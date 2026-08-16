from . import preferences, operator, ui

classes = (
    preferences.ALIGNVIEWTOSELECTION_Preferences,
    operator.VIEW3D_OT_align_view_to_selection,
    ui.VIEW3D_PT_align_view_to_selection,
)


def register():
    for cls in classes:
        preferences.bpy.utils.register_class(cls)

    preferences.schedule_shortcut_registration()


def unregister():
    operator.clear_orientation_watches()
    preferences.stop_shortcut_registration()
    preferences.remove_shortcut_keymap()

    for cls in reversed(classes):
        preferences.bpy.utils.unregister_class(cls)
