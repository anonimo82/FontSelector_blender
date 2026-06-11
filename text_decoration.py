import bpy
import bmesh

from .addon_prefs import get_addon_preferences


# --- Constants ---

STRIKETHROUGH_SUFFIX = "_strikethrough"
OVERLINE_SUFFIX = "_overline"
COLLECTION_NAME = "FontSelector Decorations"

STRIKETHROUGH_Y_FACTOR = 0.3   # Relative to font size, from baseline
OVERLINE_Y_FACTOR = 1.05        # Relative to font size, from baseline
LINE_THICKNESS = 0.04           # Relative to font size


# --- Helpers ---

def get_decoration_collection(context):
    """Get or create the decoration collection."""
    col = bpy.data.collections.get(COLLECTION_NAME)
    if col is None:
        col = bpy.data.collections.new(COLLECTION_NAME)
        context.scene.collection.children.link(col)
    return col


def get_text_dimensions(obj):
    """Return approximate width and height of a text object via its bounding box."""
    if obj.type != 'FONT':
        return 0.0, 0.0
    # Bounding box in local space
    bb = obj.bound_box  # 8 corners
    xs = [v[0] for v in bb]
    ys = [v[1] for v in bb]
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    return width, height


def get_text_bounds(obj):
    """Return (min_x, max_x, min_y, max_y) of the text bounding box in local space."""
    bb = obj.bound_box
    xs = [v[0] for v in bb]
    ys = [v[1] for v in bb]
    return min(xs), max(xs), min(ys), max(ys)


def create_line_mesh(name, width, y_pos, thickness):
    """Create (or update) a flat quad mesh representing a horizontal line."""
    mesh = bpy.data.meshes.get(name)
    if mesh is not None:
        bpy.data.meshes.remove(mesh)

    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    half_t = thickness / 2.0
    # Four corners: bottom-left, bottom-right, top-right, top-left
    verts = [
        bm.verts.new((0.0,        y_pos - half_t, 0.0)),
        bm.verts.new((width,      y_pos - half_t, 0.0)),
        bm.verts.new((width,      y_pos + half_t, 0.0)),
        bm.verts.new((0.0,        y_pos + half_t, 0.0)),
    ]
    bm.faces.new(verts)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def place_line_object(context, obj, suffix, y_factor, thickness_factor):
    """
    Create or update a mesh helper object that draws a horizontal line
    across the text object.

    y_factor      — vertical position relative to font size (from baseline)
    thickness_factor — line thickness relative to font size
    """
    debug = get_addon_preferences().debug

    font_size = obj.data.size
    min_x, max_x, min_y, max_y = get_text_bounds(obj)
    width = max_x - min_x

    y_pos = font_size * y_factor
    thickness = font_size * thickness_factor

    helper_name = obj.name + suffix
    mesh = create_line_mesh(helper_name + "_mesh", width, y_pos, thickness)

    # Reuse existing object if possible
    helper = bpy.data.objects.get(helper_name)
    if helper is None:
        helper = bpy.data.objects.new(helper_name, mesh)
        col = get_decoration_collection(context)
        col.objects.link(helper)
        if debug:
            print(f"FONTSELECTOR --- Created helper : {helper_name}")
    else:
        helper.data = mesh
        if debug:
            print(f"FONTSELECTOR --- Updated helper : {helper_name}")

    # Align helper to text object
    helper.matrix_world = obj.matrix_world.copy()
    # Offset X to match text left edge (bounding box min_x is in local space)
    helper.location.x += min_x * obj.scale.x

    # Tag helper so we can find it later
    helper["fontselector_decoration"] = True
    helper["fontselector_parent"] = obj.name

    return helper


def remove_line_object(obj, suffix, debug):
    """Remove a decoration helper object if it exists."""
    helper_name = obj.name + suffix
    helper = bpy.data.objects.get(helper_name)
    if helper is not None:
        mesh = helper.data
        bpy.data.objects.remove(helper)
        if mesh and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        if debug:
            print(f"FONTSELECTOR --- Removed helper : {helper_name}")


# --- Callbacks ---

def strikethrough_update(self, context):
    debug = get_addon_preferences().debug
    obj = context.active_object
    if obj is None or obj.type != 'FONT':
        return
    if self.use_strikethrough:
        place_line_object(
            context, obj,
            STRIKETHROUGH_SUFFIX,
            STRIKETHROUGH_Y_FACTOR,
            LINE_THICKNESS,
        )
    else:
        remove_line_object(obj, STRIKETHROUGH_SUFFIX, debug)


def overline_update(self, context):
    debug = get_addon_preferences().debug
    obj = context.active_object
    if obj is None or obj.type != 'FONT':
        return
    if self.use_overline:
        place_line_object(
            context, obj,
            OVERLINE_SUFFIX,
            OVERLINE_Y_FACTOR,
            LINE_THICKNESS,
        )
    else:
        remove_line_object(obj, OVERLINE_SUFFIX, debug)


# --- Operators ---

class FONTSELECTOR_OT_apply_stroke(bpy.types.Operator):
    """Convert text to mesh and apply Solidify modifier to simulate stroke (outline only)"""
    bl_idname = "fontselector.apply_stroke"
    bl_label = "Apply Stroke"
    bl_options = {'UNDO'}

    thickness: bpy.props.FloatProperty(
        name="Stroke Thickness",
        default=0.02,
        min=0.001,
        max=1.0,
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'FONT'

    def invoke(self, context, event):
        obj = context.active_object
        props = obj.data.fontselector_object_properties
        self.thickness = props.stroke_thickness
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "thickness")

    def execute(self, context):
        debug = get_addon_preferences().debug
        obj = context.active_object

        # Duplicate object — keep original intact
        bpy.ops.object.duplicate()
        stroke_obj = context.active_object
        stroke_obj.name = obj.name + "_stroke"

        # Convert to mesh
        bpy.ops.object.convert(target='MESH')

        # Add Solidify modifier
        mod = stroke_obj.modifiers.new(name="Stroke", type='SOLIDIFY')
        mod.thickness = self.thickness
        mod.offset = 0.0
        mod.use_rim = False
        mod.use_flip_normals = True

        # Add Wireframe modifier to keep only the border
        wf = stroke_obj.modifiers.new(name="Wireframe", type='WIREFRAME')
        wf.thickness = self.thickness * 0.5
        wf.use_boundary = True
        wf.use_even_offset = True

        if debug:
            print(f"FONTSELECTOR --- Stroke applied to : {stroke_obj.name}")

        self.report({'INFO'}, f"Stroke applied to {stroke_obj.name}")
        return {'FINISHED'}


class FONTSELECTOR_OT_update_decorations(bpy.types.Operator):
    """Refresh strikethrough / overline helper positions (use after moving or resizing the text)"""
    bl_idname = "fontselector.update_decorations"
    bl_label = "Update Decorations"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'FONT'

    def execute(self, context):
        obj = context.active_object
        props = obj.data.fontselector_object_properties

        if props.use_strikethrough:
            place_line_object(
                context, obj,
                STRIKETHROUGH_SUFFIX,
                STRIKETHROUGH_Y_FACTOR,
                LINE_THICKNESS,
            )
        if props.use_overline:
            place_line_object(
                context, obj,
                OVERLINE_SUFFIX,
                OVERLINE_Y_FACTOR,
                LINE_THICKNESS,
            )

        self.report({'INFO'}, "Decorations updated")
        return {'FINISHED'}


class FONTSELECTOR_OT_remove_decorations(bpy.types.Operator):
    """Remove all decoration helper objects linked to this text object"""
    bl_idname = "fontselector.remove_decorations"
    bl_label = "Remove Decorations"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'FONT'

    def execute(self, context):
        debug = get_addon_preferences().debug
        obj = context.active_object
        props = obj.data.fontselector_object_properties

        remove_line_object(obj, STRIKETHROUGH_SUFFIX, debug)
        remove_line_object(obj, OVERLINE_SUFFIX, debug)

        props.use_strikethrough = False
        props.use_overline = False

        self.report({'INFO'}, "Decorations removed")
        return {'FINISHED'}


class FONTSELECTOR_OT_apply_script(bpy.types.Operator):
    """Apply superscript or subscript: set font size and Z offset on the active object.
    Select the sub/superscript text object before running this — the operator
    reads offset and size factor from its own fontselector properties."""
    bl_idname = "fontselector.apply_script"
    bl_label = "Apply Script Position"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is None or obj.type != 'FONT':
            return False
        props = obj.data.fontselector_object_properties
        return props.script_type != 'NONE'

    def execute(self, context):
        debug = get_addon_preferences().debug

        obj = context.active_object
        props = obj.data.fontselector_object_properties

        offset_y = props.script_offset_y
        size_factor = props.script_size_factor
        script_type = props.script_type

        # --- Apply Z offset ---
        # Superscript: move up (+Z), Subscript: move down (-Z)
        sign = 1.0 if script_type == 'SUPERSCRIPT' else -1.0
        obj.location.z += sign * offset_y

        # --- Apply font size ---
        current_size = obj.data.size
        obj.data.size = current_size * size_factor

        if debug:
            print(
                f"FONTSELECTOR --- Script applied: type={script_type}, "
                f"offset={sign * offset_y:.3f}, size={obj.data.size:.3f}"
            )

        label = "Superscript" if script_type == 'SUPERSCRIPT' else "Subscript"
        self.report({'INFO'}, f"{label} applied — size {obj.data.size:.3f}, offset {sign * offset_y:+.3f} Z")
        return {'FINISHED'}


### REGISTER ---
def register():
    bpy.utils.register_class(FONTSELECTOR_OT_apply_stroke)
    bpy.utils.register_class(FONTSELECTOR_OT_update_decorations)
    bpy.utils.register_class(FONTSELECTOR_OT_remove_decorations)
    bpy.utils.register_class(FONTSELECTOR_OT_apply_script)

def unregister():
    bpy.utils.unregister_class(FONTSELECTOR_OT_apply_stroke)
    bpy.utils.unregister_class(FONTSELECTOR_OT_update_decorations)
    bpy.utils.unregister_class(FONTSELECTOR_OT_remove_decorations)
    bpy.utils.unregister_class(FONTSELECTOR_OT_apply_script)
