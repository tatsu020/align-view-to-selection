import bpy

from .operator import (
    VIEW3D_OT_align_view_to_selection,
    VIEW3D_OT_return_to_previous_view,
)
from .preferences import (
    ALIGN_OPERATOR_IDNAME,
    RETURN_OPERATOR_IDNAME,
    get_editable_shortcut,
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

        layout.operator(
            VIEW3D_OT_align_view_to_selection.bl_idname,
            text="Align View to Selection",
            icon='ORIENTATION_VIEW',
        )

        _, _, align_item = get_editable_shortcut(
            context,
            ALIGN_OPERATOR_IDNAME,
        )
        if align_item is not None and align_item.active:
            layout.label(text=f"Shortcut: {shortcut_label(align_item)}")
        else:
            layout.label(text="Shortcut: Disabled")

        layout.separator()

        layout.operator(
            VIEW3D_OT_return_to_previous_view.bl_idname,
            text="Return to Last Aligned View",
            icon='LOOP_BACK',
        )

        _, _, return_item = get_editable_shortcut(
            context,
            RETURN_OPERATOR_IDNAME,
        )
        if return_item is not None and return_item.active:
            layout.label(text=f"Shortcut: {shortcut_label(return_item)}")
        else:
            layout.label(text="Shortcut: Disabled")
