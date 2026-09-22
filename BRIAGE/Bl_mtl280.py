# ##### BEGIN LICENSE BLOCK #####
# 
# Copyright (C) 2024  'Juju49'(MERLE-RÉMOND Julian)
# see license notes __init__.py
# 
# ##### END  LICENSE  BLOCK #####

#Further improvements to do:
#TODO: -scrolling UVs
#TODO: -viewfacing
#-do more shaders


##====================================================================IMPORTS
#import bpy
import bpy.props
import bpy.app

#from bpy.types import Panel, UIList  # @UnresolvedImport
#from bl_ui.properties_material import MaterialButtonsPanel  # @UnresolvedImport

from bpy.app.handlers import persistent
import bpy_extras.node_shader_utils as nsu  # @UnresolvedImport
from . import Bl_data
#from bpy.types import NodeTree, NodeSocket, ShaderNode # @UnresolvedImport
#from nodeitems_utils import NodeItem # @UnresolvedImport
#from nodeitems_builtins import ShaderNodeCategory # @UnresolvedImport

#import sys

IMPORTED_GROUPS = dict()
PROCESSED_MATERIALS = dict()

__all__ = ('PREVIEW_OT_IGSMatPreview', 'IMPORTED_GROUPS', 'bind_mat', 'unbind_material')

#faster to use than operator
def bind_mat(scene, material):
    scene.eevee.use_ssr = True
    scene.eevee.use_ssr_refraction = True
    
    material.use_nodes = True
    material.use_screen_refraction = True
    material.show_transparent_back = False
    
    if material.name in PROCESSED_MATERIALS:
        mt = PROCESSED_MATERIALS[material.name]
        #dec2020: sometimes it doesn't find it because reference expired somehow
        try:
            mt.update()
        except ReferenceError:
            mt = TSGroupWrapper(material, is_readonly=False)
            PROCESSED_MATERIALS[material.name] = mt
            mt.update()
            
    else:
        mt = TSGroupWrapper(material, is_readonly=False)
        PROCESSED_MATERIALS[material.name] = mt
        mt.update()
    inputs = mt.node_TS.inputs
    
    add_driver_color(inputs['diffuse_color'], material, "default_value", "IgsMat.diffuse_color")
    add_driver_color(inputs['specular_color'], material, "default_value", "IgsMat.specular_color")
    
    add_driver(inputs['spec_power'], material, "default_value", "IgsMat.specular_power")
    add_driver_color(inputs['emissive_color'], material, "default_value", "IgsMat.emissive_color")
    
    add_driver(inputs['emissive_power'], material, "default_value", "IgsMat.emissive_power")
    
    add_driver(inputs['arg1'], material, "default_value", "IgsMat.uv_param_1")
    add_driver(inputs['arg2'], material, "default_value", "IgsMat.uv_param_2")
    add_driver(inputs['arg3'], material, "default_value", "IgsMat.uv_param_3")
    add_driver(inputs['arg4'], material, "default_value", "IgsMat.uv_param_4")
    add_driver(inputs['arg5'], material, "default_value", "IgsMat.uv_param_5")
    add_driver(inputs['arg6'], material, "default_value", "IgsMat.uv_param_6")
    
    material.IgsMat.preview_active = True

def unbind_material(material):
    if material.name in PROCESSED_MATERIALS:
        mt = PROCESSED_MATERIALS[material.name]
    else:
        mt = TSGroupWrapper(material, is_readonly=False)
        PROCESSED_MATERIALS[material.name] = mt
    inputs = mt.node_TS.inputs
    
    inputs['diffuse_color'].driver_remove("default_value")
    inputs['specular_color'].driver_remove("default_value")
    
    inputs['spec_power'].driver_remove("default_value")
    inputs['emissive_color'].driver_remove("default_value")
    
    inputs['emissive_power'].driver_remove("default_value")
    
    inputs['arg1'].driver_remove("default_value")
    inputs['arg2'].driver_remove("default_value")
    inputs['arg3'].driver_remove("default_value")
    inputs['arg4'].driver_remove("default_value")
    inputs['arg5'].driver_remove("default_value")
    inputs['arg6'].driver_remove("default_value")
    
    material.node_tree.links.remove(mt.node_TS.outputs[0].links[0])
    
    material.IgsMat.preview_active = False

class PREVIEW_OT_IGSMatPreview(bpy.types.Operator):
    """Toggles preview function of IGS material"""
    bl_idname = "igs.preview"
    bl_label = "Preview IGS material"
    #
    bind: bpy.props.BoolProperty(default=True)
    invoked: bpy.props.BoolProperty(default=False)
    #
    def execute(self, context):
        """un/binds IGS data to material"""
        global PROCESSED_MATERIALS
        material = context.object.active_material
        if material is None:
            return {'CANCELLED'}
        
        if self.bind:
            bind_mat(context.scene, material)
            self.report({'INFO'}, "IGS material bound")
            
        else:#unbinds drivers
            unbind_material(material)
            self.report({'INFO'}, "IGS material unbound")
            
        return {'FINISHED'}
        #else:
        #    return {'CANCELLED'}
    #
    def invoke(self, context, event):
        """writes message according to its type to console and log file and pops up a window display"""
        mt = context.object.active_material
        if mt is None:
            return {'CANCELLED'}
        if mt.use_nodes and len(mt.node_tree.links) > 1 and not context.object.active_material.IgsMat.preview_active:
            wm = context.window_manager
            return wm.invoke_props_dialog(self)
        else:
            return self.execute(context)
    #
    def draw(self, context):
        """window display layout"""
        #
        row = self.layout.split(factor=0.1)
        row.label(text='', icon='QUESTION')
        col = row.column()
        #col.alert = True
        col.label(text="Current node setting will be overridden")
        self.layout.label(text="Are you sure?")

##====================================================================UTILS



@persistent
def Ensure_TS_node_groups_on_load(dummy):
    global IMPORTED_GROUPS
    #reset on new file to enable us to check for this file
    #when needed
    IMPORTED_GROUPS.clear()
    
    #add missing entries to old materials:
    for mat in bpy.data.materials:
        igmat = mat.IgsMat
        if not len(igmat.textures):
            Bl_data.UpdateShName(igmat, None)

def Import_TS_node_groups():
    global IMPORTED_GROUPS
    if 'TS_base' in IMPORTED_GROUPS:
        try:
            # Проверяем, жива ли ссылка в памяти Blender
            _ = IMPORTED_GROUPS['TS_base'].name
            return
        except ReferenceError:
            # Если Blender удалил объект, чистим мертвый кэш
            IMPORTED_GROUPS.clear()

    from BRIAGE import BINARY_PATH
    filepath = BINARY_PATH+r"\TS_material_lib.blend"
    
    #append object from .blend file
    with bpy.data.libraries.load(filepath) as (data_from, data_to):  # @UndefinedVariable
        data_to.node_groups = [ng for ng in data_from.node_groups if ng not in bpy.data.node_groups]
        
    IMPORTED_GROUPS = {ng.name : ng for ng in bpy.data.node_groups}

    #print("Groups imported, from "+filepath)
    #print(IMPORTED_GROUPS)

def add_driver(
    #from https://blender.stackexchange.com/questions/39127/how-to-put-together-a-driver-with-python
        source, target, prop, dataPath,
        index = -1, negative = False, func = ''
    ):
    ''' Add driver to source prop (at index), driven by target dataPath '''

    if index != -1:
        d = source.driver_add( prop, index ).driver
    else:
        d = source.driver_add( prop ).driver

    v = d.variables.new()
    v.name = prop
    v.type = 'SINGLE_PROP'
    v.targets[0].id_type   = 'MATERIAL' if target.name in bpy.data.materials else 'OBJECT'
    v.targets[0].id        = target
    v.targets[0].data_path = dataPath

    d.expression = func + "(" + v.name + ")" if func else v.name
    d.expression = d.expression if not negative else "-1 * " + d.expression
    
    #example of use:
    #cube  = bpy.context.scene.objects['Cube']
    #empty = bpy.context.scene.objects['Empty']
    #add_driver( cube, empty, 'scale', 'scale.z', 2 )
    
def add_driver_color(
        source, target, prop, dataPath, negative = False, func = ''
    ):
    add_driver(source, target, prop, dataPath+'[0]', 0, negative, func)
    add_driver(source, target, prop, dataPath+'[1]', 1, negative, func)
    add_driver(source, target, prop, dataPath+'[2]', 2, negative, func)
    add_driver(source, target, prop, dataPath+'[3]', 3, negative, func)
        

##====================================================================NODE WRAPPERS
    
class TSGroupWrapper(nsu.ShaderWrapper):
    """
    Hard coded shader setup, based on Node Groups for TS preview. Modified from PrincipledBSDF in node_shader_utils.
    """
    NODES_LIST = (
        "node_out",
        "node_TS",

        "_node_normalmap",
        "_node_texcoords",
        "_node_TS_paletteUV"
    )

    __slots__ = (
        "is_readonly",
        "material",
        *NODES_LIST,
    )

    NODES_LIST = nsu.ShaderWrapper.NODES_LIST + NODES_LIST

    def __init__(self, material, is_readonly=True, use_nodes=True):
        super().__init__(material, is_readonly, use_nodes)
        self._node_TS_paletteUV = None


    def update(self):
        super().update()
       
        if not self.use_nodes:
            return

        tree = self.material.node_tree

        nodes = tree.nodes
        links = tree.links

        # --------------------------------------------------------------------
        # Main output and shader.
        node_out = None
        node_TS = None
        for n in nodes:
            if n.bl_idname == 'ShaderNodeOutputMaterial':
                node_out = n
                if n.inputs[0].is_linked:
                    is_node_ts = n.inputs[0].links[0].from_node
                    if is_node_ts.bl_idname == 'ShaderNodeGroup' and "TS_" in is_node_ts.node_tree.name:
                        node_TS = is_node_ts
            elif (
                    n.bl_idname == 'ShaderNodeGroup' and
                    n.node_tree and
                    "TS_" in n.node_tree.name
                ):
                node_TS = n
                if n.outputs[0].is_linked:
                    for lnk in n.outputs[0].links:
                        node_out = lnk.to_node
                        if node_out.bl_idname == 'ShaderNodeOutputMaterial':
                            break
                        else:
                            node_out = None
            if (
                    node_out is not None and node_TS is not None and
                    (node_out.inputs[0].is_linked and
                    node_TS.outputs[0].is_linked and
                    node_out.inputs[0].links[0].from_node == node_TS)
            ):
                break
            #node_out = node_TS = None  # Could not find a valid pair

        if node_out is not None:
            self._grid_to_location(0, 0, ref_node=node_out)
        elif not self.is_readonly:
            node_out = nodes.new(type='ShaderNodeOutputMaterial')
            node_out.label = "Material Out"
            node_out.target = 'ALL'
            self._grid_to_location(1, 1, dst_node=node_out)
        self.node_out = node_out

        if node_TS is not None:
            self._grid_to_location(0, 0, ref_node=node_TS)
        elif not self.is_readonly:
            node_TS = nodes.new(type='ShaderNodeGroup')
            node_TS.label = "TS Material"
            self._grid_to_location(0, 1, dst_node=node_TS)

        self.node_TS = node_TS
            
        if node_TS is not None:
            #find appropriate shader
            shader = self.material.IgsMat.shader_name
            if shader != 'custom':
                self._find_node_tree(shader)
            else:
                self._find_node_tree(self.material.IgsMat.shader_name_string)
                
            # Link
            links.new(node_TS.outputs["BSDF"], self.node_out.inputs["Surface"])
            
            m_textures = self.material.IgsMat.textures
            t = []
            for i in range(8):
                if i < len(m_textures):
                    tex = m_textures[i]
                    t.append(self.texture_set(i, tex.texture, tex.uv_layer))
                else:
                    self.texture_set(i, None, "")
                    
            if "Palette" in shader or "Pallete" in shader or "Pallette" in shader: #connect uv for palettes
                TS_paletteUV = self._node_TS_paletteUV
                if TS_paletteUV is None:
                    for n in nodes:
                        if (n.bl_idname == 'ShaderNodeGroup' and "TS_paletteUV" == n.node_tree.name):
                            TS_paletteUV = n
                            break
                
                if TS_paletteUV is not None:
                    self._grid_to_location(0, 0, ref_node=TS_paletteUV)
                elif not self.is_readonly:
                    global IMPORTED_GROUPS
                    TS_paletteUV = nodes.new(type='ShaderNodeGroup')
                    TS_paletteUV.node_tree = IMPORTED_GROUPS["TS_paletteUV"]
                    TS_paletteUV.label = "TS Material pUV"
                    self._grid_to_location(-3, -2, dst_node=TS_paletteUV)
                    
                links.new(t[0].node_image.outputs["Color"], TS_paletteUV.inputs["t1"])
                links.new(TS_paletteUV.outputs["p1uv"], t[1].node_image.inputs["Vector"])
                nodes.remove(t[1].node_uv)
                if "2" in shader:
                    links.new(TS_paletteUV.outputs["p2uv"], t[2].node_image.inputs["Vector"])
                    nodes.remove(t[2].node_uv)
                self._node_TS_paletteUV = TS_paletteUV
            elif self._node_TS_paletteUV:
                for n in nodes:
                    if (n.bl_idname == 'ShaderNodeGroup' and "TS_paletteUV" == n.node_tree.name):
                        nodes.remove(n)
        
    def update_texture(self, i):
        tex = self.material.IgsMat.textures.m_textures[i]
        self.texture_set(i, tex.texture, tex.uv_layer)
        
        
    def _find_node_tree(self, shader_name):
        #check lib has been imported
        Import_TS_node_groups()
        
        #Assign group corresponding to shader or default to a more
        #generic one.
        group_looked_for = "TS_"+shader_name
        global IMPORTED_GROUPS
        data_n_gp = IMPORTED_GROUPS
        #print(data_n_gp)
        if group_looked_for in data_n_gp:
            #print(group_looked_for+" found")
            self.node_TS.node_tree = data_n_gp[group_looked_for]
        elif 'Glass' in group_looked_for:
            #print(group_looked_for+" not found -> TS_TrainGlass.fx")
            self.node_TS.node_tree = data_n_gp['TS_TrainGlass.fx']
        #elif 'View' in group_looked_for:
        #    self.node_TS.node_tree = data_n_gp['TS_ViewFacingFlora.fx']
        else:
            #print(group_looked_for+" not found -> TS_base")
            self.node_TS.node_tree = data_n_gp['TS_base']
        
    def texture_set(self, i, image, uv_name):
        if not self.use_nodes or self.node_TS is None:
            return None
        
        shader = self.node_TS.node_tree.name
        slot = "t"+str(i+1)
        
        if i > 0: #only the first image is diffuse
            t = ShaderUVImageTextureWrapper(
                self, self.node_TS,
                self.node_TS.inputs[slot],
                grid_row_diff=-i,
                colorspace_name='Non-Color'
            )
        else:
            t = ShaderUVImageTextureWrapper(
                self, self.node_TS,
                self.node_TS.inputs[slot],
                grid_row_diff=-i,
                colorspace_name='sRGB'
            )
        t.image = image
        t.uv = uv_name
        if "Palette" in shader or "Pallete" in shader or "Palete" in shader:
            t.node_uv
        t.node_image.label = slot
        if (
            self.node_TS.inputs[slot+"a"].is_linked and 
            self.node_TS.inputs[slot+"a"].links[0].from_node.label == slot
        ):
            pass #already connected to our alpha input
        else:
            socket_dst = self.node_TS.inputs[slot+"a"]
            socket_src = t.node_image.outputs[1]
            
            self.material.node_tree.links.new(socket_src, socket_dst)
            

#         if "Palette" in shader or "Pallete" in shader or "Palete" in shader:
#             palette1 = ("1" in shader) and (i == 1)
#             palette2 = ("2" in shader) and (i == 1 or i == 2)
#             
#             if ((palette1 or palette2) and not self.node_TS.outputs["p1uv"].is_linked):
#                 socket_dst = t.node_image.inputs[0]
#                 socket_src = self.node_TS.outputs["p1uv"]
#                 self.material.node_tree.links.new(socket_src, socket_dst)
#                 
#             if (palette2 and not self.node_TS.outputs["p2uv"].is_linked):
#                 socket_dst = t.node_image.inputs[0]
#                 socket_src = self.node_TS.outputs["p2uv"]
#                 self.material.node_tree.links.new(socket_src, socket_dst)
#         
        return t

class ShaderUVImageTextureWrapper(nsu.ShaderImageTextureWrapper):
    NODES_LIST = (
        "_node_uv",
    )

    __slots__ = (
        "_node_uv",
    )
    
    def __init__(self, owner_shader: nsu.ShaderWrapper, node_dst, socket_dst, grid_row_diff=0,
                 use_alpha=False, colorspace_is_data=..., colorspace_name=...):
        super().__init__(owner_shader, node_dst, socket_dst, grid_row_diff,
                 use_alpha, colorspace_is_data, colorspace_name)
        
        self._node_uv = ...
    
    
    def image_get(self):
        return self.node_image.image if self.node_image is not None else None
    
    def image_set(self, image):
        if image is None: 
            if self.node_image is not None:
                self.node_image.image = image
            return
            
        if self.colorspace_is_data is not ...:
            if image.colorspace_settings.is_data != self.colorspace_is_data and image.users >= 1:
                image = image.copy()
            image.colorspace_settings.is_data = self.colorspace_is_data
        if self.colorspace_name is not ...:
            if image.colorspace_settings.is_data != self.colorspace_is_data and image.users >= 1:
                image = image.copy()
            image.colorspace_settings.name = self.colorspace_name
        self.node_image.image = image
            
    image = property(image_get, image_set)
    
    
    
    def has_uv_node(self):
        return self._node_uv not in {None, ...}
    
    def node_uv_get(self):
        if self._node_uv is ...:
            # Running only once, trying to find a valid uv node.
            if self.node_image is None:
                return None
            if self.node_image.inputs["Vector"].is_linked:
                node_uv = self.node_image.inputs["Vector"].links[0].from_node
                if node_uv.bl_idname == 'ShaderNodeUVMap':
                    self._node_uv = node_uv
                    self.owner_shader._grid_to_location(0, 0 + self.grid_row_diff, ref_node=node_uv)
            if self._node_uv is ...:
                self._node_uv = None
                
        if self._node_uv is None and not self.is_readonly:
            # Find potential existing link into image's Vector input.
            socket_dst = self.node_image.inputs["Vector"]

            tree = self.owner_shader.material.node_tree
            node_uv = tree.nodes.new(type='ShaderNodeUVMap')
            node_uv.label = "UV Coords"
            self.owner_shader._grid_to_location(-1, 0, dst_node=node_uv, ref_node=self.node_image)

            # Link uv -> image node.
            tree.links.new(node_uv.outputs[0], socket_dst)

            self._node_uv = node_uv
        return self._node_uv
    
    node_uv = property(node_uv_get)
    
    def uv_get(self):
        return self.node_uv.uv_map

    @nsu._set_check
    def uv_set(self, uv_map):
        if uv_map is None:
            self.owner_shader.material.node_tree.remove(self._node_uv)
            return
        self.node_uv.uv_map = uv_map

    uv = property(uv_get, uv_set)
    
classes = (
    PREVIEW_OT_IGSMatPreview,
)

def register():
    from bpy.utils import register_class# @UnresolvedImport
    for cls in classes:
        register_class(cls)
        
    bpy.app.handlers.load_post.append(Ensure_TS_node_groups_on_load)
    
#     import nodeitems_utils# @UnresolvedImport
#     nodeitems_utils.register_node_categories('CUSTOM_NODES', node_categories)
#
 
def unregister():
#     import nodeitems_utils# @UnresolvedImport
#     nodeitems_utils.unregister_node_categories('CUSTOM_NODES')
# 
    from bpy.utils import unregister_class# @UnresolvedImport
    
    bpy.app.handlers.load_post.remove(Ensure_TS_node_groups_on_load) 
    
    for cls in reversed(classes):
        unregister_class(cls)
