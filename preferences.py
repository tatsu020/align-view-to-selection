import bpy

DEFAULT_TRANSITION_MS = 200
OPERATOR_IDNAME = "view3d.align_view_to_selection"

_addon_keymaps = []
_shortcut_status = {"registered": False, "conflicts": []}


SHORTCUT_KEY_ITEMS = [
    *[(f"NUMPAD_{i}", f"Numpad {i}", "") for i in range(10)],
    *[(f"F{i}", f"F{i}", "") for i in range(5, 13)],
    *[(letter, letter, "") for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"],
]


def get_preferences(context=None):
    context = context or bpy.context
    addon = context.preferences.addons.get(__package__)
    return addon.preferences if addon else None


def shortcut_label(prefs):
    parts = []
    if prefs.shortcut_ctrl:
        parts.append("Ctrl")
    if prefs.shortcut_shift:
        parts.append("Shift")
    if prefs.shortcut_alt:
        parts.append("Alt")

    labels = {identifier: label for identifier, label, _ in SHORTCUT_KEY_ITEMS}
    parts.append(labels.get(prefs.shortcut_key, prefs.shortcut_key))
    return " + ".join(parts)


def shortcut_matches_kmi(kmi, prefs):
    return (
        kmi.type == prefs.shortcut_key
        and kmi.value == 'PRESS'
        and bool(kmi.ctrl) == bool(prefs.shortcut_ctrl)
        and bool(kmi.shift) == bool(prefs.shortcut_shift)
        and bool(kmi.alt) == bool(prefs.shortcut_alt)
        and not bool(kmi.oskey)
        and kmi.key_modifier == 'NONE'
    )


def find_shortcut_conflicts(context, prefs):
    """Find active bindings that can compete in the 3D View/Edit Mesh context."""
    wm = context.window_manager
    conflicts = []
    seen = set()
    relevant_names = {'Mesh', '3D View', '3D View Generic', 'Window'}

    # The active keyconfig already represents the effective user configuration.
    keyconfig = getattr(wm.keyconfigs, 'active', None)
    if keyconfig is None:
        return conflicts

    for keymap in keyconfig.keymaps:
        if (
            keymap.name not in relevant_names
            and keymap.space_type not in {'EMPTY', 'VIEW_3D'}
        ):
            continue

        for item in keymap.keymap_items:
            if not item.active or item.idname == OPERATOR_IDNAME:
                continue
            if not shortcut_matches_kmi(item, prefs):
                continue

            identity = (keymap.name, item.idname, item.name)
            if identity in seen:
                continue
            seen.add(identity)
            conflicts.append({
                "keymap": keymap.name,
                "operator": item.idname,
                "name": item.name or item.idname,
            })

    return conflicts


def remove_shortcut_keymap():
    for keymap, item in reversed(_addon_keymaps):
        try:
            keymap.keymap_items.remove(item)
        except Exception:
            pass

    _addon_keymaps.clear()
    _shortcut_status["registered"] = False


def refresh_shortcut_keymap(context=None):
    context = context or bpy.context
    remove_shortcut_keymap()

    prefs = get_preferences(context)
    if prefs is None or not prefs.shortcut_enabled:
        _shortcut_status["conflicts"] = []
        return

    conflicts = find_shortcut_conflicts(context, prefs)
    _shortcut_status["conflicts"] = conflicts

    # Safe default: never silently steal an existing binding.
    if conflicts and not prefs.allow_conflicting_shortcut:
        return

    keyconfig = context.window_manager.keyconfigs.addon
    if keyconfig is None:
        return

    keymap = keyconfig.keymaps.new(name='Mesh', space_type='EMPTY')
    item = keymap.keymap_items.new(
        OPERATOR_IDNAME,
        type=prefs.shortcut_key,
        value='PRESS',
        ctrl=prefs.shortcut_ctrl,
        shift=prefs.shortcut_shift,
        alt=prefs.shortcut_alt,
    )
    _addon_keymaps.append((keymap, item))
    _shortcut_status["registered"] = True


def schedule_shortcut_refresh(self=None, context=None):
    def refresh():
        try:
            refresh_shortcut_keymap()
        except Exception:
            pass
        return None

    bpy.app.timers.register(refresh, first_interval=0.0)


class ALIGNVIEWTOSELECTION_OT_reset_shortcut(bpy.types.Operator):
    bl_idname = "preferences.align_view_to_selection_reset_shortcut"
    bl_label = "Reset Shortcut"
    bl_description = "Reset the shortcut to Alt + Numpad 7"

    def execute(self, context):
        prefs = get_preferences(context)
        if prefs is None:
            return {'CANCELLED'}

        prefs.shortcut_key = 'NUMPAD_7'
        prefs.shortcut_ctrl = False
        prefs.shortcut_shift = False
        prefs.shortcut_alt = True
        prefs.allow_conflicting_shortcut = False
        prefs.shortcut_enabled = True
        refresh_shortcut_keymap(context)
        return {'FINISHED'}


class ALIGNVIEWTOSELECTION_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    transition_ms: bpy.props.IntProperty(
        name="Base Transition",
        description=(
            "Base transition duration for a 180-degree turn; "
            "smaller view changes automatically finish faster"
        ),
        default=DEFAULT_TRANSITION_MS,
        min=50,
        max=1500,
        soft_min=100,
        soft_max=500,
        subtype='TIME',
    )

    auto_view_orientation: bpy.props.BoolProperty(
        name="Auto Transform Orientation: View",
        description=(
            "Switch Transform Orientation to View after alignment, then restore "
            "the previous orientation when the viewing direction changes"
        ),
        default=True,
    )

    shortcut_enabled: bpy.props.BoolProperty(
        name="Enable Shortcut",
        default=True,
        update=schedule_shortcut_refresh,
    )
    shortcut_key: bpy.props.EnumProperty(
        name="Key",
        items=SHORTCUT_KEY_ITEMS,
        default='NUMPAD_7',
        update=schedule_shortcut_refresh,
    )
    shortcut_ctrl: bpy.props.BoolProperty(
        name="Ctrl", default=False, update=schedule_shortcut_refresh
    )
    shortcut_shift: bpy.props.BoolProperty(
        name="Shift", default=False, update=schedule_shortcut_refresh
    )
    shortcut_alt: bpy.props.BoolProperty(
        name="Alt", default=True, update=schedule_shortcut_refresh
    )
    allow_conflicting_shortcut: bpy.props.BoolProperty(
        name="Allow Conflicting Shortcut",
        description=(
            "Register this shortcut even if another active Blender command "
            "uses the same key combination"
        ),
        default=False,
        update=schedule_shortcut_refresh,
    )

    def draw(self, context):
        layout = self.layout

        behavior = layout.box()
        behavior.label(text="View Alignment")
        behavior.prop(self, "transition_ms")
        behavior.prop(self, "auto_view_orientation")

        shortcut = layout.box()
        shortcut.label(text="Shortcut")
        shortcut.prop(self, "shortcut_enabled")

        col = shortcut.column()
        col.enabled = self.shortcut_enabled

        row = col.row(align=True)
        row.prop(self, "shortcut_key", text="")
        row.prop(self, "shortcut_ctrl", toggle=True)
        row.prop(self, "shortcut_shift", toggle=True)
        row.prop(self, "shortcut_alt", toggle=True)

        col.operator(
            ALIGNVIEWTOSELECTION_OT_reset_shortcut.bl_idname,
            icon='LOOP_BACK',
        )

        conflicts = (
            find_shortcut_conflicts(context, self)
            if self.shortcut_enabled else []
        )
        _shortcut_status["conflicts"] = conflicts

        if conflicts:
            warning = col.box()
            warning.alert = True
            warning.label(
                text=f"Shortcut conflict: {shortcut_label(self)}",
                icon='ERROR',
            )
            for conflict in conflicts[:4]:
                warning.label(
                    text=f"{conflict['keymap']}: {conflict['name']}"
                )
            if len(conflicts) > 4:
                warning.label(text=f"...and {len(conflicts) - 4} more")

            warning.prop(self, "allow_conflicting_shortcut")
            if not self.allow_conflicting_shortcut:
                warning.label(
                    text="The add-on shortcut stays disabled until resolved."
                )
        elif self.shortcut_enabled:
            col.label(text=f"Active: {shortcut_label(self)}", icon='CHECKMARK')

        info = layout.box()
        info.label(text="Mesh Edit Mode")
        info.label(text="Select any 3+ vertices")
