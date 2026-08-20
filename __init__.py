from . import preferences, operator, ui

classes = (
    preferences.ALIGNVIEWTOSELECTION_Preferences,
    operator.VIEW3D_OT_align_view_to_selection,
    operator.VIEW3D_OT_return_to_previous_view,
    ui.VIEW3D_PT_align_view_to_selection,
)


def register():
    for cls in classes:
        preferences.bpy.utils.register_class(cls)

    preferences.register_shortcut_keymap()


def unregister():
    operator.clear_runtime_state()
    preferences.remove_shortcut_keymap()

    for cls in reversed(classes):
        preferences.bpy.utils.unregister_class(cls)
