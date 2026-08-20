import bpy
import rna_keymap_ui

ALIGN_OPERATOR_IDNAME = "view3d.align_view_to_selection"
RETURN_OPERATOR_IDNAME = "view3d.return_to_previous_aligned_view"
KEYMAP_NAME = "3D View"

_addon_keymaps = []


def get_preferences(context=None):
    context = context or bpy.context
    addon = context.preferences.addons.get(__package__)
    return addon.preferences if addon else None


def register_shortcut_keymap(context=None):
    """Register both shortcuts in Blender's built-in 3D View keymap."""
    context = context or bpy.context
    wm = context.window_manager
    keyconfig = wm.keyconfigs.addon
    if keyconfig is None:
        return

    keymap = keyconfig.keymaps.new(
        name=KEYMAP_NAME,
        space_type='VIEW_3D',
    )

    align_item = keymap.keymap_items.new(
        ALIGN_OPERATOR_IDNAME,
        type='NUMPAD_7',
        value='PRESS',
        alt=True,
    )
    _addon_keymaps.append((keymap, align_item))

    return_item = keymap.keymap_items.new(
        RETURN_OPERATOR_IDNAME,
        type='NUMPAD_7',
        value='PRESS',
        alt=True,
        shift=True,
    )
    _addon_keymaps.append((keymap, return_item))


def remove_shortcut_keymap():
    for keymap, item in reversed(_addon_keymaps):
        try:
            keymap.keymap_items.remove(item)
        except Exception:
            pass
    _addon_keymaps.clear()


def get_editable_shortcut(context, operator_idname):
    """Return the user-edited KeyMapItem when available, otherwise add-on default."""
    wm = context.window_manager

    user_keyconfig = wm.keyconfigs.user
    if user_keyconfig is not None:
        keymap = user_keyconfig.keymaps.get(KEYMAP_NAME)
        if keymap is not None:
            for item in keymap.keymap_items:
                if item.idname == operator_idname:
                    return user_keyconfig, keymap, item

    addon_keyconfig = wm.keyconfigs.addon
    if addon_keyconfig is not None:
        for keymap, item in _addon_keymaps:
            if item.idname == operator_idname:
                return addon_keyconfig, keymap, item

    return None, None, None


def shortcut_label(item):
    if item is None:
        return "Not registered"

    parts = []
    if item.ctrl:
        parts.append("Ctrl")
    if item.shift:
        parts.append("Shift")
    if item.alt:
        parts.append("Alt")
    if item.oskey:
        parts.append("OSKey")

    key_name = (
        item.type
        .replace("NUMPAD_", "Numpad ")
        .replace("_", " ")
        .title()
    )
    parts.append(key_name)
    return " + ".join(parts)


def _same_event(a, b):
    return (
        a.type == b.type
        and a.value == b.value
        and bool(a.ctrl) == bool(b.ctrl)
        and bool(a.shift) == bool(b.shift)
        and bool(a.alt) == bool(b.alt)
        and bool(a.oskey) == bool(b.oskey)
        and a.key_modifier == b.key_modifier
    )


def find_shortcut_conflicts(context, target_item):
    if target_item is None or not target_item.active:
        return []

    active_keyconfig = context.window_manager.keyconfigs.active
    if active_keyconfig is None:
        return []

    conflicts = []
    seen = set()
    relevant_names = {KEYMAP_NAME, '3D View Generic', 'Window'}

    for keymap in active_keyconfig.keymaps:
        if (
            keymap.name not in relevant_names
            and keymap.space_type not in {'EMPTY', 'VIEW_3D'}
        ):
            continue

        for item in keymap.keymap_items:
            if not item.active:
                continue
            if item.idname in {ALIGN_OPERATOR_IDNAME, RETURN_OPERATOR_IDNAME}:
                continue
            if not _same_event(item, target_item):
                continue

            identity = (keymap.name, item.idname, item.name)
            if identity in seen:
                continue

            seen.add(identity)
            conflicts.append((keymap.name, item.name or item.idname))

    return conflicts


def draw_shortcut(layout, context, label, operator_idname):
    layout.label(text=label)
    keyconfig, keymap, item = get_editable_shortcut(context, operator_idname)

    if keyconfig is None or keymap is None or item is None:
        layout.label(text="Shortcut is not available.", icon='ERROR')
        return

    row = layout.row()
    row.context_pointer_set("keymap", keymap)
    rna_keymap_ui.draw_kmi(
        ["ADDON", "USER", "DEFAULT"],
        keyconfig,
        keymap,
        item,
        row,
        0,
    )

    conflicts = find_shortcut_conflicts(context, item)
    if conflicts:
        warning = layout.box()
        warning.alert = True
        warning.label(
            text=f"Shortcut conflict: {shortcut_label(item)}",
            icon='ERROR',
        )
        for keymap_name, name in conflicts[:4]:
            warning.label(text=f"{keymap_name}: {name}")
        if len(conflicts) > 4:
            warning.label(text=f"...and {len(conflicts) - 4} more")
        warning.label(text="Change or disable one of the bindings.")


class ALIGNVIEWTOSELECTION_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    auto_view_orientation: bpy.props.BoolProperty(
        name="Auto Transform Orientation: View",
        description=(
            "Switch Transform Orientation to View after alignment, then restore "
            "the previous orientation when the viewing direction changes"
        ),
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "auto_view_orientation")
        layout.separator()

        draw_shortcut(
            layout,
            context,
            "Align View to Selection",
            ALIGN_OPERATOR_IDNAME,
        )

        layout.separator()

        draw_shortcut(
            layout,
            context,
            "Return to Last Aligned View",
            RETURN_OPERATOR_IDNAME,
        )
