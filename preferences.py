import bpy
import rna_keymap_ui

OPERATOR_IDNAME = "view3d.align_view_to_selection"
KEYMAP_NAME = "Mesh"

_addon_keymaps = []
_shortcut_registration_active = False
_shortcut_registration_attempts = 0


def get_preferences(context=None):
    context = context or bpy.context
    addon = context.preferences.addons.get(__package__)
    return addon.preferences if addon else None


def register_shortcut_keymap(context=None):
    """Register the add-on shortcut once Blender's add-on keyconfig is ready."""
    context = context or bpy.context
    wm = getattr(context, "window_manager", None)
    if wm is None:
        return False

    keyconfig = wm.keyconfigs.addon
    if keyconfig is None:
        return False

    # Avoid duplicates after reloads or delayed registration retries.
    keymap = keyconfig.keymaps.get(KEYMAP_NAME)
    if keymap is not None:
        stale_items = [
            item for item in keymap.keymap_items
            if item.idname == OPERATOR_IDNAME
        ]
        for item in stale_items:
            try:
                keymap.keymap_items.remove(item)
            except Exception:
                pass

    keymap = keyconfig.keymaps.new(name=KEYMAP_NAME, space_type='EMPTY')
    item = keymap.keymap_items.new(
        OPERATOR_IDNAME,
        type='NUMPAD_7',
        value='PRESS',
        alt=True,
    )
    _addon_keymaps.append((keymap, item))
    return True


def schedule_shortcut_registration():
    """
    Register the shortcut after add-on startup.

    During extension/add-on registration Blender may not have the add-on
    keyconfig ready yet. Retry briefly instead of silently losing the shortcut.
    """
    global _shortcut_registration_active, _shortcut_registration_attempts

    _shortcut_registration_active = True
    _shortcut_registration_attempts = 0

    def try_register():
        global _shortcut_registration_attempts

        if not _shortcut_registration_active:
            return None

        if register_shortcut_keymap():
            return None

        _shortcut_registration_attempts += 1
        if _shortcut_registration_attempts >= 20:
            return None

        return 0.10

    bpy.app.timers.register(try_register, first_interval=0.0)


def stop_shortcut_registration():
    global _shortcut_registration_active
    _shortcut_registration_active = False


def remove_shortcut_keymap():
    for keymap, item in reversed(_addon_keymaps):
        try:
            keymap.keymap_items.remove(item)
        except Exception:
            pass
    _addon_keymaps.clear()


def get_editable_shortcut(context):
    wm = context.window_manager
    user_keyconfig = wm.keyconfigs.user

    if user_keyconfig is not None:
        keymap = user_keyconfig.keymaps.get(KEYMAP_NAME)
        if keymap is not None:
            for item in keymap.keymap_items:
                if item.idname == OPERATOR_IDNAME:
                    return user_keyconfig, keymap, item

    addon_keyconfig = wm.keyconfigs.addon
    if addon_keyconfig is not None and _addon_keymaps:
        keymap, item = _addon_keymaps[0]
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

    parts.append(item.type.replace("NUMPAD_", "Numpad ").replace("_", " ").title())
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
    relevant_names = {KEYMAP_NAME, '3D View', '3D View Generic', 'Window'}

    for keymap in active_keyconfig.keymaps:
        if (
            keymap.name not in relevant_names
            and keymap.space_type not in {'EMPTY', 'VIEW_3D'}
        ):
            continue

        for item in keymap.keymap_items:
            if not item.active or item.idname == OPERATOR_IDNAME:
                continue
            if not _same_event(item, target_item):
                continue

            identity = (keymap.name, item.idname, item.name)
            if identity in seen:
                continue
            seen.add(identity)
            conflicts.append((keymap.name, item.name or item.idname))

    return conflicts


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

        layout.label(text="Shortcut")
        keyconfig, keymap, item = get_editable_shortcut(context)

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
