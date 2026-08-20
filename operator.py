import bpy
import math
import time
from mathutils import Vector

from .geometry import (
    best_fit_plane,
    choose_normal_side,
    rotation_preserve_roll,
    selected_world_points,
)
from .preferences import get_preferences


BASE_TRANSITION_MS = 200

_orientation_watch_tokens = {}
_token_counter = 0

# One saved last-aligned view for each 3D View area.
_last_aligned_views = {}


def clear_runtime_state():
    _orientation_watch_tokens.clear()
    _last_aligned_views.clear()


def smoothstep_blender_like(t):
    """Cubic smoothstep, matching Blender's smooth-view easing shape."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def next_token():
    global _token_counter
    _token_counter += 1
    return _token_counter


def capture_view_state(rv3d):
    state = {
        "rotation": rv3d.view_rotation.copy(),
        "location": rv3d.view_location.copy(),
        "perspective": rv3d.view_perspective,
    }

    # Camera offset affects framing rather than zoom, so it is kept.
    if hasattr(rv3d, "view_camera_offset"):
        state["camera_offset"] = tuple(rv3d.view_camera_offset)

    return state


def restore_non_interpolated_view_state(rv3d, state):
    try:
        rv3d.view_perspective = state["perspective"]
    except Exception:
        pass

    if "camera_offset" in state:
        try:
            rv3d.view_camera_offset = state["camera_offset"]
        except Exception:
            pass


def start_orientation_watch(
    scene,
    rv3d,
    area,
    target_direction,
    previous_orientation,
):
    if previous_orientation == 'VIEW':
        return

    area_pointer = area.as_pointer()
    token = next_token()
    _orientation_watch_tokens[area_pointer] = token

    target_direction = target_direction.normalized()
    threshold = math.cos(math.radians(0.35))

    def watcher():
        if _orientation_watch_tokens.get(area_pointer) != token:
            return None

        try:
            slot = scene.transform_orientation_slots[0]
        except ReferenceError:
            _orientation_watch_tokens.pop(area_pointer, None)
            return None

        if slot.type != 'VIEW':
            _orientation_watch_tokens.pop(area_pointer, None)
            return None

        try:
            current_direction = (
                rv3d.view_rotation @ Vector((0.0, 0.0, 1.0))
            ).normalized()
        except ReferenceError:
            _orientation_watch_tokens.pop(area_pointer, None)
            return None

        dot = max(-1.0, min(1.0, target_direction.dot(current_direction)))
        if dot < threshold:
            try:
                slot.type = previous_orientation
            except Exception:
                try:
                    slot.type = 'GLOBAL'
                except Exception:
                    pass

            _orientation_watch_tokens.pop(area_pointer, None)
            return None

        return 0.10

    bpy.app.timers.register(watcher, first_interval=0.10)


class _SmoothViewOperator:
    _timer = None

    def _cancel_timer(self, context):
        if self._timer is None:
            return
        try:
            context.window_manager.event_timer_remove(self._timer)
        except Exception:
            pass
        self._timer = None

    def _begin_smooth_view(
        self,
        context,
        target_rotation,
        target_location,
        target_distance,
        target_state=None,
    ):
        self._rv3d = context.space_data.region_3d
        self._area = context.area

        self._start_rotation = self._rv3d.view_rotation.copy()
        self._target_rotation = target_rotation.copy()
        self._start_location = self._rv3d.view_location.copy()
        self._target_location = target_location.copy()
        self._start_distance = float(self._rv3d.view_distance)
        self._target_distance = float(target_distance)
        self._target_state = target_state

        quat_dot = abs(max(
            -1.0,
            min(1.0, self._start_rotation.dot(self._target_rotation)),
        ))
        rotation_angle = 2.0 * math.acos(quat_dot)

        rotation_factor = rotation_angle / math.pi
        location_delta = (self._target_location - self._start_location).length
        distance_delta = abs(self._target_distance - self._start_distance)

        if rotation_factor < 1.0e-5 and (
            location_delta > 1.0e-7 or distance_delta > 1.0e-7
        ):
            rotation_factor = 0.35

        self._duration = (BASE_TRANSITION_MS / 1000.0) * rotation_factor
        self._start_time = time.perf_counter()

        self._timer = context.window_manager.event_timer_add(
            0.01,
            window=context.window,
        )
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _apply_interpolated_view(self, t):
        self._rv3d.view_rotation = self._start_rotation.slerp(
            self._target_rotation,
            t,
        )
        self._rv3d.view_location = self._start_location.lerp(
            self._target_location,
            t,
        )
        self._rv3d.view_distance = (
            self._start_distance
            + (self._target_distance - self._start_distance) * t
        )
        self._area.tag_redraw()

    def _finish_smooth_view(self, context):
        try:
            self._rv3d.view_rotation = self._target_rotation
            self._rv3d.view_location = self._target_location
            self._rv3d.view_distance = self._target_distance

            if self._target_state is not None:
                restore_non_interpolated_view_state(
                    self._rv3d,
                    self._target_state,
                )

            self._area.tag_redraw()
        except ReferenceError:
            self._cancel_timer(context)
            return {'CANCELLED'}

        self._cancel_timer(context)
        return self.on_smooth_view_finished(context)

    def on_smooth_view_finished(self, context):
        return {'FINISHED'}

    def modal(self, context, event):
        if event.type != 'TIMER':
            if (
                event.type in {
                    'MIDDLEMOUSE',
                    'NDOF_MOTION',
                    'TRACKPADPAN',
                    'TRACKPADZOOM',
                    'TRACKPADROTATE',
                }
                and event.value == 'PRESS'
            ):
                self._cancel_timer(context)
                return self.on_smooth_view_cancelled(context)

            return {'PASS_THROUGH'}

        elapsed = time.perf_counter() - self._start_time
        if self._duration <= 1.0e-6:
            return self._finish_smooth_view(context)

        raw_t = elapsed / self._duration
        if raw_t >= 1.0:
            return self._finish_smooth_view(context)

        t = smoothstep_blender_like(raw_t)

        try:
            self._apply_interpolated_view(t)
        except ReferenceError:
            self._cancel_timer(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def on_smooth_view_cancelled(self, context):
        return {'CANCELLED'}


class VIEW3D_OT_align_view_to_selection(
    _SmoothViewOperator,
    bpy.types.Operator,
):
    bl_idname = "view3d.align_view_to_selection"
    bl_label = "Align View to Selection"
    bl_description = (
        "Fit a plane to all selected vertex positions and align the view "
        "perpendicular to it"
    )
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return (
            context.area is not None
            and context.area.type == 'VIEW_3D'
            and context.mode == 'EDIT_MESH'
        )

    def _restore_orientation_on_cancel(self):
        if not getattr(self, "_auto_view", False):
            return

        try:
            slot = self._scene.transform_orientation_slots[0]
            if slot.type == 'VIEW':
                slot.type = self._previous_orientation
        except Exception:
            pass

    def _start(self, context):
        points = selected_world_points(context)
        center, normal, error = best_fit_plane(points)
        if error:
            self.report({'WARNING'}, error)
            return {'CANCELLED'}

        rv3d = context.space_data.region_3d
        if rv3d is None:
            self.report({'WARNING'}, "3D view data was not found.")
            return {'CANCELLED'}

        normal = choose_normal_side(rv3d, normal)

        self._scene = context.scene

        prefs = get_preferences(context)
        self._auto_view = prefs.auto_view_orientation if prefs else False
        self._previous_orientation = (
            context.scene.transform_orientation_slots[0].type
        )

        if self._auto_view:
            context.scene.transform_orientation_slots[0].type = 'VIEW'

        target_rotation = rotation_preserve_roll(rv3d, normal)

        # Align keeps the current zoom, matching the existing behavior.
        return self._begin_smooth_view(
            context,
            target_rotation=target_rotation,
            target_location=center,
            target_distance=rv3d.view_distance,
        )

    def invoke(self, context, event):
        return self._start(context)

    def execute(self, context):
        return self._start(context)

    def on_smooth_view_finished(self, context):
        area_pointer = self._area.as_pointer()

        # Save the aligned orientation and center. Zoom is intentionally not
        # part of the stored state so Return never changes the current zoom.
        _last_aligned_views[area_pointer] = capture_view_state(self._rv3d)

        if self._auto_view:
            target_direction = (
                self._target_rotation @ Vector((0.0, 0.0, 1.0))
            ).normalized()

            start_orientation_watch(
                self._scene,
                self._rv3d,
                self._area,
                target_direction,
                self._previous_orientation,
            )

        return {'FINISHED'}

    def on_smooth_view_cancelled(self, context):
        self._restore_orientation_on_cancel()
        return {'CANCELLED'}


class VIEW3D_OT_return_to_previous_view(
    _SmoothViewOperator,
    bpy.types.Operator,
):
    bl_idname = "view3d.return_to_previous_aligned_view"
    bl_label = "Return to Previous View"
    bl_description = (
        "Return to the most recent view created by "
        "Align View to Selection in this 3D View"
    )
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return (
            context.area is not None
            and context.area.type == 'VIEW_3D'
        )

    def _start(self, context):
        rv3d = context.space_data.region_3d
        if rv3d is None:
            self.report({'WARNING'}, "3D view data was not found.")
            return {'CANCELLED'}

        area_pointer = context.area.as_pointer()
        state = _last_aligned_views.get(area_pointer)

        if state is None:
            self.report({
                'WARNING'
            }, "No Align View to Selection view is stored yet.")
            return {'CANCELLED'}

        # Return orientation/center only. Keep whatever zoom the user currently
        # has when invoking this operator.
        return self._begin_smooth_view(
            context,
            target_rotation=state["rotation"],
            target_location=state["location"],
            target_distance=rv3d.view_distance,
            target_state=state,
        )

    def invoke(self, context, event):
        return self._start(context)

    def execute(self, context):
        return self._start(context)
