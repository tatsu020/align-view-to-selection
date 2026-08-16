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
from .preferences import DEFAULT_TRANSITION_MS, get_preferences


_orientation_watch_tokens = {}
_token_counter = 0


def clear_orientation_watches():
    _orientation_watch_tokens.clear()


def smoothstep_blender_like(t):
    """Cubic smoothstep, matching Blender's smooth-view easing shape."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def next_token():
    global _token_counter
    _token_counter += 1
    return _token_counter


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

        # A manual orientation change wins immediately.
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

        # Compare direction only: roll, pan, and zoom do not restore it.
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


class VIEW3D_OT_align_view_to_selection(bpy.types.Operator):
    bl_idname = "view3d.align_view_to_selection"
    bl_label = "Align View to Selection"
    bl_description = (
        "Fit a plane to all selected vertex positions and align the view "
        "perpendicular to it"
    )
    bl_options = {'REGISTER'}

    _timer = None

    @classmethod
    def poll(cls, context):
        return (
            context.area is not None
            and context.area.type == 'VIEW_3D'
            and context.mode == 'EDIT_MESH'
        )

    def _cancel_timer(self, context):
        if self._timer is None:
            return
        try:
            context.window_manager.event_timer_remove(self._timer)
        except Exception:
            pass
        self._timer = None

    def _restore_orientation_on_cancel(self):
        if not getattr(self, "_auto_view", False):
            return
        try:
            slot = self._scene.transform_orientation_slots[0]
            if slot.type == 'VIEW':
                slot.type = self._previous_orientation
        except Exception:
            pass

    def _finish(self, context):
        try:
            self._rv3d.view_rotation = self._target_rotation
            self._rv3d.view_location = self._target_location
            self._rv3d.view_distance = self._fixed_distance
            self._area.tag_redraw()
        except ReferenceError:
            self._cancel_timer(context)
            return {'CANCELLED'}

        self._cancel_timer(context)

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

        self._rv3d = rv3d
        self._area = context.area
        self._scene = context.scene
        self._start_rotation = rv3d.view_rotation.copy()
        self._target_rotation = rotation_preserve_roll(rv3d, normal)
        self._start_location = rv3d.view_location.copy()
        self._target_location = center.copy()
        self._fixed_distance = rv3d.view_distance

        prefs = get_preferences(context)
        base_ms = prefs.transition_ms if prefs else DEFAULT_TRANSITION_MS
        self._auto_view = prefs.auto_view_orientation if prefs else True

        quat_dot = abs(max(
            -1.0,
            min(1.0, self._start_rotation.dot(self._target_rotation)),
        ))
        rotation_angle = 2.0 * math.acos(quat_dot)

        # Blender-like timing: 180° uses the base duration, smaller turns less.
        self._duration = (base_ms / 1000.0) * (rotation_angle / math.pi)
        self._start_time = time.perf_counter()

        self._previous_orientation = (
            context.scene.transform_orientation_slots[0].type
        )
        if self._auto_view:
            context.scene.transform_orientation_slots[0].type = 'VIEW'

        self._timer = context.window_manager.event_timer_add(
            0.01,
            window=context.window,
        )
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        return self._start(context)

    def execute(self, context):
        return self._start(context)

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
                self._restore_orientation_on_cancel()
                return {'CANCELLED'}

            return {'PASS_THROUGH'}

        elapsed = time.perf_counter() - self._start_time
        if self._duration <= 1.0e-6:
            return self._finish(context)

        raw_t = elapsed / self._duration
        if raw_t >= 1.0:
            return self._finish(context)

        t = smoothstep_blender_like(raw_t)

        try:
            self._rv3d.view_rotation = self._start_rotation.slerp(
                self._target_rotation,
                t,
            )
            self._rv3d.view_location = self._start_location.lerp(
                self._target_location,
                t,
            )
            self._rv3d.view_distance = self._fixed_distance
            self._area.tag_redraw()
        except ReferenceError:
            self._cancel_timer(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}
