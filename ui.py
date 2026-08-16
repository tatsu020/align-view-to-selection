import bpy

from .operator import VIEW3D_OT_align_view_to_selection
from .preferences import get_editable_shortcut, shortcut_label


class VIEW3D_PT_align_view_to_selection(bpy.types.Panel):
    bl_label = "Align View to Selection"
    bl_idname = "VIEW3D_PT_align_view_to_selection"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "View"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            VIEW3D_OT_align_view_to_selection.bl_idname,
            text="Align View to Selection",
            icon='ORIENTATION_VIEW',
        )

        _, _, item = get_editable_shortcut(context)
        if item is not None and item.active:
            layout.label(text=f"Shortcut: {shortcut_label(item)}")
        else:
            layout.label(text="Shortcut: Disabled")

        layout.separator()
        info = layout.box()
        info.label(text="Select any 3+ vertices")
        info.label(text="Edge loops / disconnected points work")
