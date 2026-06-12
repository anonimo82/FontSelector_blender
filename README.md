# FontSelector — Font Management for Blender

**FontSelector** is a Blender extension that brings a proper font browsing workflow to 3D text objects and VSE text strips. Instead of hunting through a file browser every time you want to try a different typeface, FontSelector scans your system font directories, groups fonts into families, and lets you preview and apply them directly from the 3D Viewport or the Video Sequence Editor.

[Watch the addon in action](https://makertube.net/w/2sxbKKHV8QWL8p5EACGn8T)

> **Note:** The `main` branch is the experimental/development branch.  
> For the latest stable release, download from the [Releases page](https://github.com/samytichadou/FontSelector_blender_addon/releases).

If FontSelector saves you time, consider [buying me a coffee](https://ko-fi.com/tonton_blender) to support continued development of free tools.

---

## Requirements

| Field | Value |
|---|---|
| Blender | 5.0.0 or later |
| License | GPL-3.0-or-later |
| Extension ID | `font_selector` |

---

## Installation

Since version 3.0, FontSelector is distributed as a **Blender Extension**.

- **Blender Extension Platform (recommended):** Search for *Font Selector* at [extensions.blender.org](https://extensions.blender.org/) and install directly from Blender's *Get Extensions* panel.
- **Manual install:** Download the `.zip` from the [Releases page](https://github.com/samytichadou/FontSelector_blender_addon/releases), then in Blender go to **Edit → Preferences → Extensions** and drag-and-drop the zip, or use *Install from Disk*.

The extension bundles the `fonttools` Python library (`fonttools-4.54.0`) as a wheel — no separate pip install is needed.

---

## Features

### Font Discovery
- **Automatic OS detection** — FontSelector detects the standard font directories for Linux, Windows, and macOS at startup. If a folder is missing from your system it is silently skipped.
- **Recursive folder scan** — All subdirectories are walked, so fonts installed in nested paths are found automatically.
- **OTF and TTF support** — Both `.otf` and `.ttf` files are recognised.
- **Family grouping** — Fonts are grouped into families (e.g. *Roboto*) with individual type variants (Regular, Bold, Italic, Bold Italic, Condensed, …). Families are sorted alphabetically; within each family the four standard Blender slots (Regular → Bold → Italic → Bold Italic) are listed first.
- **Duplicate detection** — If the same font type appears in more than one folder, only the first encountered copy is kept.

### Cache System
- Font metadata is stored in a JSON cache file (`families_datas.json`) inside the preferences folder so Blender does not re-scan all folders on every launch.
- On startup FontSelector computes the total size of all font directories. If the size has changed (fonts added or removed), the cache is automatically rebuilt.
- A manual **Reload Fonts** operator forces a full rescan regardless of the size check.

### UI Integration

FontSelector adds its panel in three places, each independently toggleable in the addon preferences:

| Location | Type | Preference toggle |
|---|---|---|
| 3D Viewport header | Popover (font icon) | *3D Viewport Popover* |
| Properties → Object Data (Font) | Side panel | *Font Properties Panel* |
| VSE header | Popover (font icon) | *Sequencer Popover* |
| Properties → Strip | Side panel | *Sequencer Properties Panel* |

A **Pop-Up Operator** (`fontselector.popup`) is also available (toggle in preferences) and accessible via the F3 search menu. It works in both the 3D Viewport and the VSE.

### Font Browsing
- **Search bar** — Filter the family list by family name. Optionally extend the search to individual font names or file paths via the toggle icons next to the search field.
- **Favourites** — Star any family with the ★ icon. Enable the *Favourites Filter* to show only starred families. The favourites list is saved to `favorite_datas.json` and persists across sessions.
- **Invert Filter** — Flip the current filter to show everything that does *not* match.
- **Live preview** — Selecting a family or changing the type variant immediately applies the font to the active text object (and all other selected text objects of the same kind).
- **Type selector** — A drop-down below the list shows all available variants for the selected family (Regular, Bold, Condensed, etc.).
- **Arrow navigation** — The ▲ / ▼ buttons step through fonts one at a time, crossing family boundaries so you can sweep through your entire font library without lifting your hands from the keyboard.
- **Multi-component icon** — Families that contain at least one of the four Blender-native font slots (Bold, Italic, Bold Italic) in addition to Regular display a ꟻ icon with a one-click *Load Font Family* operator.

### Load Font Family
Clicking the ꟻ icon (or calling `fontselector.load_font_family`) loads the Regular, Bold, Italic, and Bold Italic variants of a family into the matching slots on the active text object's data block in one operation. This is the correct workflow when you need Blender's per-character style mixing (e.g. **bold** inline with normal text).

The operator respects the *Remove Blender Type Fonts* toggle: when enabled (default), existing bold/italic/bold-italic assignments are cleared before loading the new family.

### Font Infos Panel
Expand the collapsible *Font Infos* panel to see:
- Full font name (as reported by the font file)
- Type variant
- File path, with a clickable *Reveal File* button that opens the system file manager at the font's location

### Text Decoration
A collapsible **Text Decoration** section in the panel provides typographic helpers beyond what Blender exposes natively.

#### Native (Blender)
- **Underline** — toggles `TextCurve.use_underline` (3D objects only)
- **Text Anchor** — exposes `TextCurve.align_x` (3D objects only)

#### Line Decorations (3D text only)
Helper mesh objects are created in a dedicated *FontSelector Decorations* collection:

| Decoration | Description |
|---|---|
| **Strikethrough** | A flat quad centred at ~30% of the font size above the baseline |
| **Overline** | A flat quad positioned at ~105% of the font size above the baseline |

Both lines match the text's bounding-box width and scale with `font size`. They are parented conceptually by name (`<object_name>_strikethrough` / `<object_name>_overline`).

- **Update Decorations** — Refreshes helper positions after you move or resize the text object.
- **Remove All** — Deletes both helper objects and resets the toggles.

#### Stroke (3D text only)
Duplicates the text object, converts it to a mesh, and applies a *Solidify* + *Wireframe* modifier stack to simulate a text outline/stroke. The stroke thickness is configurable. **This is a destructive, one-way operation** — the original text object is kept intact.

#### Sub / Superscript (3D text only)
A workflow helper for positioning a separate text object as a superscript or subscript relative to a main text object:

1. Create a separate text object containing the super/subscript content.
2. Select both objects, making the super/subscript the **active** object.
3. Choose *Superscript* or *Subscript* from the *Script* drop-down.
4. Adjust *Y Offset* and *Size Factor* as needed.
5. Click **Apply to This Object**.

The operator places the active object at the right edge of the main text along its local X axis and offsets it vertically along local Y. It also scales the font size by the chosen factor. The operation is undoable with Ctrl+Z.

---

## Preferences

Open **Edit → Preferences → Extensions → Font Selector** to access:

| Option | Default | Description |
|---|---|---|
| Preferences Folder | Extension user folder | Directory where JSON cache and favourites files are stored. Change this to share a font cache between machines or Blender versions. |
| Debug | Off | Prints verbose messages to the system console (useful for bug reports). |
| 3D Viewport Popover | Off | Show the font icon in the 3D Viewport header. |
| Font Properties Panel | On | Show the panel in Properties → Object Data (Font). |
| Sequencer Popover | Off | Show the font icon in the VSE header. |
| Sequencer Properties Panel | On | Show the panel in Properties → Strip. |
| Pop Up Operator | Off | Register the popup operator accessible via F3. |

---

## Operators Reference

| Operator ID | Label | Description |
|---|---|---|
| `fontselector.reload_fonts` | Reload Fonts | Force a full rescan of all font directories and rebuild the cache. |
| `fontselector.switch_font` | Switch Font | Step to the next or previous font/type, crossing family boundaries. |
| `fontselector.load_font_family` | Load/Remove Font Family | Load all four Blender-native font slots for a family onto the active object. |
| `fontselector.reveal_file` | Reveal File | Open the system file manager at the selected font's location. |
| `fontselector.apply_stroke` | Apply Stroke | Duplicate + convert text to mesh and apply a stroke (outline) modifier stack. |
| `fontselector.update_decorations` | Update Decorations | Refresh strikethrough/overline helper positions after moving or resizing text. |
| `fontselector.remove_decorations` | Remove Decorations | Delete all decoration helpers linked to the active text object. |
| `fontselector.apply_script` | Apply Script Position | Position the active object as superscript/subscript relative to a main text object. |
| `fontselector.popup` | Font Selection (popup) | Open the font selector as a floating dialog. |

---

## Data / Cache Files

All files are stored in the **Preferences Folder** (configurable in addon prefs):

| File | Contents |
|---|---|
| `families_datas.json` | Full font family / type / path database with a size checksum. |
| `favorite_datas.json` | List of favourite family names. |

---

## Supported OS Font Directories

FontSelector scans these paths by default:

**Linux**
- `/usr/share/fonts`
- `/usr/local/share/fonts`
- `/usr/X11R6/lib/X11/fonts`
- `~/.local/share/fonts`
- `~/.fonts`

**Windows**
- `C:\Windows\Fonts`
- `C:\Program Files\WindowsApps`
- `%USERPROFILE%\fonts`
- `%USERPROFILE%\Microsoft\Windows\Fonts`

**macOS**
- `~/Library/Fonts`
- `/Library/Fonts`
- `/System/Library/Fonts`
- `/System Folder/Fonts`
- `/Network/Library/Fonts`

If a directory does not exist it is silently skipped. If a font folder is missing from this list, please [open an issue](https://github.com/samytichadou/FontSelector_blender_addon/issues).

---

## Important Notes & Disclaimers

- **Regular slot only for browsing** — When you select a font family or type in the list, FontSelector writes the chosen font to the text object's *Regular* slot only. This makes the preview immediate and unambiguous. A bold font selected from the list will occupy the Regular slot.
- **Load Font Family for multi-style text** — To use Blender's per-character bold/italic mixing on a single text object, use the *Load Font Family* operator instead of browsing the list.
- **Stroke is destructive** — The *Apply Stroke* operator duplicates and converts the object; the operation cannot be undone through FontSelector itself (use Ctrl+Z in Blender immediately after).
- **Decorations are helper objects** — Strikethrough and overline lines are separate mesh objects. They do not update automatically when you edit the text. Use *Update Decorations* after any transform or content change.

---

## Known Issues

- **Windows — Reveal File** does not select the specific font file; Windows Explorer's CLI does not support per-file selection reliably. The parent folder is opened instead.
- **Popover panels + F3 search** — When popover panels are enabled, Blender's F3 search menu may display unnamed entries originating from those panels. This appears to be a Blender bug.

---

## Module Overview

| File | Purpose |
|---|---|
| `__init__.py` | Extension entry point — registers / unregisters all modules. |
| `addon_prefs.py` | Addon preferences panel and `get_addon_preferences()` helper. |
| `properties.py` | All `PropertyGroup` definitions, font-change callbacks, and font datablock helpers. |
| `load_fonts.py` | OS font discovery, JSON cache read/write, startup handler, relinking logic. |
| `ui_list_family_font.py` | `UIList` implementations for the family browser (object and strip variants). |
| `gui.py` | All panel/popover/popup UI classes and `draw_font_selector` / `draw_text_decoration` helpers. |
| `reload_operator.py` | `fontselector.reload_fonts` operator. |
| `reveal_file_operator.py` | `fontselector.reveal_file` operator and OS-specific explorer launch logic. |
| `load_font_family_operator.py` | `fontselector.load_font_family` operator. |
| `switch_font_operator.py` | `fontselector.switch_font` operator with cross-family navigation. |
| `text_decoration.py` | Strikethrough/overline mesh helpers, stroke, and sub/superscript operators. |

---

## License

FontSelector is free software distributed under the **GNU General Public License v3.0 or later**.  
See the [LICENSE](LICENSE) file for the full text.

Copyright © 2018 Samy Tichadou (tonton) — samytichadou@gmail.com
