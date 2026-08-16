# Align View to Selection

A small Blender add-on that aligns the 3D Viewport to a **best-fit plane computed from the positions of selected vertices**.

It is especially useful when Blender's normal/active-element based alignment does not give the view you want—for example with curved edge loops or disconnected point selections.

## Features

- Aligns the view to a best-fit plane from any **3 or more selected vertices**
- Works with:
  - edge loops
  - disconnected vertices
  - selected edges and faces
  - multiple mesh objects in Edit Mode
- Uses selected vertex **positions**, not topology or averaged mesh normals
- Preserves the current viewport roll as much as possible
- Preserves the current zoom level
- Smooth Blender-like view transition
- Optional automatic Transform Orientation → `View`
- Configurable keyboard shortcut
- Uses Blender's standard Keymap UI for shortcut editing
- Detects shortcut conflicts and shows a warning

## Usage

1. Enter **Mesh Edit Mode**.
2. Select **3 or more vertices**.
3. Run **Align View to Selection**.

Default shortcut:

**Alt + Numpad 7**

The command is also available in:

**3D Viewport → N sidebar → View → Align View to Selection**

## Shortcut settings

Open:

**Edit → Preferences → Add-ons / Extensions → Align View to Selection**

The shortcut is shown with Blender's standard Keymap editor UI, so you can change the key, modifiers, event type, or disable the binding exactly like other Blender shortcuts.

If another active command uses the same key combination in a relevant 3D View/Edit Mode context, the add-on shows a conflict warning so you can change or disable one of the bindings.

## View behavior

The add-on:

1. collects all selected vertex positions;
2. computes a best-fit plane using PCA;
3. uses the least-variance axis as the plane normal;
4. chooses the side already facing the viewer;
5. preserves the current screen roll as much as possible;
6. moves the view smoothly to face that plane;
7. keeps the current zoom unchanged.

The transition duration follows Blender-style angle scaling: smaller rotations complete faster than large ones.

## Auto Transform Orientation: View

This option is **off by default**. When enabled, the add-on switches Transform Orientation to `View` after alignment.

It stays in `View` while you:

- pan
- zoom
- change roll

When the actual viewing direction changes, the previous Transform Orientation is restored.

## Why not Align View to Active?

Blender's standard alignment tools generally derive an orientation from active geometry, normals, or transform orientations.

Align View to Selection instead asks:

> What plane best describes the positions of all selected points?

That difference is useful for edge loops, mildly non-planar selections, and disconnected points.

## Limitations

- At least 3 vertices are required.
- A nearly straight-line selection does not define a unique best-fit plane, so the operation is cancelled with a warning.
- Intended for Mesh Edit Mode.

## Compatibility

- Blender 4.2 or newer
- No external Python dependencies

## License

GPL-3.0-or-later.
