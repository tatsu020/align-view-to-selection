import bpy

from .operator import VIEW3D_OT_align_view_to_selection
from .preferences import (
    _shortcut_status,
    get_preferences,
    shortcut_label,
)


class VIEW3D_PT_align_view_to_selection(bpy.types.Panel):
    bl_label = "Align View to Selection"
    bl_idname = "VIEW3D_PT_align_view_to_selection"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"

    def draw(self, context):
        layout = self.layout
        prefs = get_preferences(context)

        layout.operator(
            VIEW3D_OT_align_view_to_selection.bl_idname,
            text="Align View to Selection",
            icon='ORIENTATION_VIEW',
        )

        if prefs is not None and prefs.shortcut_enabled:
            layout.label(text=f"Shortcut: {shortcut_label(prefs)}")
            if (
                _shortcut_status["conflicts"]
                and not prefs.allow_conflicting_shortcut
            ):
                warning = layout.box()
                warning.alert = True
                warning.label(
                    text="Shortcut disabled due to a conflict",
                    icon='ERROR',
                )
                warning.label(text="Change it in Add-on Preferences")
        else:
            layout.label(text="Shortcut: Disabled")

        layout.separator()
        info = layout.box()
        info.label(text="Select any 3+ vertices")
        info.label(text="Edge loops / disconnected points work")
