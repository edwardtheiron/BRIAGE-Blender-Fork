# ##### BEGIN LICENSE BLOCK #####
# 
# Copyright (C) 2024  'Juju49'(MERLE-RÉMOND Julian)
# see license notes __init__.py
# 
# ##### END  LICENSE  BLOCK #####

SHORT_SHADER_NAME_DIC = {
	"Shadow":'StencilShadow.fx',
	"TrDiff":'TrainBasicObjectDiffuse.fx',
	"TrGlass":'TrainGlass.fx',
	"TrSpec":'TrainBasicObjectSpecular.fx',
	"TrSpecEM":'TrainSpecEnvMask.fx',
	"TrBumpSpec":'TrainBumpSpec.fx',
	"TrBumpSpecEM":'TrainBumpSpecEnvMask.fx',
	"TrGlassWeather":'TrainGlassWeatherEffects.fx',
	"TrLightMap":'TrainLightMapWithDiffuse.fx',
	"TrEnv":'TrainEnv.fx',
	"TrFlora":'TrainFlora.fx',
	"TrVFaceFlora":'TrainViewFacingFlora.fx',
	"TrUpVFaceFlora":'TrainUprightViewFacingFlora.fx',
	"LoftTexDiff":'LoftTexDiff.fx',
	"LoftTexDiffTr":'LoftTexDiffTrans.fx',
	"Skin":'SkinDiffuse.fx',
	"Water":'WaterCubeMap.fx',
	"WaterScenery":'WaterScenery.fx',
	"Sky":'TrainSkyDome.fx' }

RESERVED_OBJECT_NAMES = ['_day', '_night', '_locomotive', '_tender', '_coach', '_vehicle', '_wagon', '_carriage', '_coal', '_fuel_level_', '_freight', '_bulk', \
	'_lights_fwdhead', '_lights_revhead', '_lights_fwdtail', '_lights_revtail', '_light_fwdhead', '_light_revhead', '_light_fwdtail', '_light_revtail']
RESERVED_OBJECT_NAMES_NB = ['_door', '_step', '_wh', '_bo', '_panto', '_wiper', '_primarydigits_', '_secondarydigits_'] # Reserved names followed by 1 or 2 digits
RESERVED_OBJECT_NAMES_1NB = [] # Reserved names followed by 1 digit (any keyword in RESERVED_OBJECT_NAMES_1NB must be also in RESERVED_OBJECT_NAMES_NB)

#MODIFS2016: use xml tools to import from TS/dev/shaders:
#MODIFS2016: shader dic.
#SHADERS_LIST['shader_name'][0] == expected number of slots for TS
#SHADERS_LIST['shader_name'][1] == related number of slots for Blender
#SHADERS_LIST['shader_name'][2] == shader description
SHADERS_LIST = {}
SHADERS_ENUM = []

#List of objects created by exporter to destroy when it ends:
exp_duplicates = []

#====================================================================IMPORTS
import bpy
import bpy.path

from bpy_extras.io_utils import ImportHelper #,ExportHelper 
from bpy.types import Panel, UIList  # @UnresolvedImport
from bl_ui.properties_material import MaterialButtonsPanel  # @UnresolvedImport
from bl_ui.properties_scene import SceneButtonsPanel  # @UnresolvedImport
from bpy.props import BoolVectorProperty, BoolProperty, StringProperty, FloatProperty, IntProperty, FloatVectorProperty, PointerProperty, EnumProperty, CollectionProperty  # @UnresolvedImport
from . Bl_mtl280 import PREVIEW_OT_IGSMatPreview

import sys

#====================================================================REPORT HANDLER

#MODIF2016 new reports handler: implemented everywhere
#method ref: bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message="")
#type (enum set in {"DEBUG", "INFO", "OPERATOR", "PROPERTY", "WARNING", "ERROR", "ERROR_INVALID_INPUT", "ERROR_INVALID_CONTEXT", "ERROR_OUT_OF_MEMORY"}) <<<--- operator self.report(type, msg) like
#INVOKE_DEFAULT for Popup
class REPORTER_OT_OhlalalaLa_LaCata(bpy.types.Operator):
	"""mini reporter for igs exporter functions"""
	bl_idname = "igs_err.damned"
	bl_label = "Exporter's messages to user"
	#
	invoked: BoolProperty(default=False)
	type: StringProperty()
	message: StringProperty()
	#
	def execute(self, context):
		"""writes message according to its type to console and log file"""
		if not self.invoked:
			print("BRIAGE:: '" + self.type + "': "+ self.message)
			if sys.stdout != sys.__stdout__:
				saveout_temp = sys.stdout
				sys.stdout = sys.__stdout__
				#if not self.invoked:
					#if self.type == 'ERROR': self.report({'WARNING'}, self.message)
					#else: self.report({self.type}, self.message)
				print("BRIAGE:: '" + self.type + "': "+ self.message)
				sys.stdout = saveout_temp
		return {'FINISHED'}
	#
	def invoke(self, context, event):
		"""writes message according to its type to console and log file and pops up a window display"""
		print("BRIAGE:: '" + self.type + "': "+ self.message)
		if sys.stdout != sys.__stdout__:
			saveout_temp = sys.stdout
			sys.stdout = sys.__stdout__
			print("BRIAGE:: '" + self.type + "': "+ self.message)
			sys.stdout = saveout_temp
		message = self.message
		msgwd = message.split()
		msgwd.reverse()
		message2 = ""
		while msgwd > []:
			msg_line = ""
			while (len(msg_line) < 60) and (msgwd > []):
				msg_line += msgwd.pop()
				msg_line += " "
			msg_line += " \n"
			message2 += msg_line
		self.message2 = message2
		wm = context.window_manager
		return wm.invoke_popup(self, width=510)
	#
	def draw(self, context):
		"""window display layout"""
		if self.type in ['INFO','DEBUG',]: custom_icon = 'INFO'
		elif self.type == 'WARNING': custom_icon = 'ERROR'
		elif self.type in ['ERROR','ERROR_INVALID_INPUT','ERROR_INVALID_CONTEXT','ERROR_OUT_OF_MEMORY']: custom_icon = 'CANCEL'
		elif self.type in ['OPERATOR','PROPERTY']: custom_icon = 'SCRIPT'
		else: custom_icon = None
		row = self.layout
		row.alignment = 'CENTER'
		row.label(text=">-~-~ IGS Exporter ~-~-<")
		#
		#https://www.blender.org/api/blender_python_api_2_75_3/bpy.utils.previews.html will be dev for Bl_2.79.0 version & upwards with funny pics or something else fun
		#row = layout.row()
		#row.alignement = 'CENTER'
		#row.label(text="", icon_value='')
		#
		row = self.layout.split(factor=0.25)
		row.label(text=self.type, icon=custom_icon)
		col = row.column()
		msg = self.message2
		msg = msg.splitlines()
		for line in msg:
			col.label(text=line)
		#
		row = self.layout.split(factor=0.60)
		row.separator()
		row.operator_context = 'EXEC_DEFAULT'
		row.operator("igs_err.damned", text="OK (or press 'enter')", icon='FILE_TICK').invoked = True


#====================================================================PROPS
	#collections
class KeywordsListItem(bpy.types.PropertyGroup):
	""" Group of custom keyword """
	# http://www.sinestesia.co/tutorials/making-uilists-in-blender/
	name: StringProperty(
		name="keyword",
		description="A keyword for exporter to group objects together. Write full name to exclude",
		default="_newKword")
	prop1: BoolProperty(
		name="keyword used for export",
		description="enables keyword's processing during next IGS export",
		default=True)

class TextureStringsListItem(bpy.types.PropertyGroup):
	""" Group of custom tex strings """
	# http://www.sinestesia.co/tutorials/making-uilists-in-blender/
	name: StringProperty(
		name="old string",
		description="",
		default="OldString")
	prop1: StringProperty(
		name="new string",
		description="",
		default="NewString")

class ObjectStringListItem(bpy.types.PropertyGroup):
	""" Group of custom obj strings """
	# http://www.sinestesia.co/tutorials/making-uilists-in-blender/
	name: StringProperty(
		name="old string",
		description="",
		default="OldString")
	prop1: StringProperty(
		name="new string",
		description="",
		default="NewString")
		
	# Lists manager:
class LISTBUILDER_UL_BODY(UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		# http://www.sinestesia.co/tutorials/making-uilists-in-blender/
		layout.use_property_decorate = False #No anim
		custom_icon = 'TEXT'
		if self.layout_type in {'DEFAULT', 'COMPACT'}:
			layout.prop(item, "name", emboss=False, text="")
			layout.emboss='NORMAL'
			layout.prop(item, "prop1",text="")
		#
		elif self.layout_type in {'GRID'}:
			layout.alignment = 'CENTER'
			layout.label(text="", icon = custom_icon)

class LISTBUILDER_OT_NewItem(bpy.types.Operator):
	""" Add a new keyword to KeywordsListItem """
	# http://www.sinestesia.co/tutorials/making-uilists-in-blender/
	bl_idname = "listbuilder.new_item"
	bl_label = "Add an item"
	ilist: IntProperty()
	def execute(self, context):
		ilist = self.ilist
		if ilist == 0:
			f_list = context.scene.IgsOpt.KeywordsListItem.add()
		elif ilist == 1:
			f_list = context.scene.IgsOpt.texture_string_to_replace.add()
		elif ilist == 2:
			f_list = context.scene.IgsOpt.object_string_to_replace.add()
		elif ilist == 3:
			if len(context.material.IgsMat.textures) < 8:
				f_list = context.material.IgsMat.textures.add()
		return{'FINISHED'}

class LISTBUILDER_OT_DeleteItem(bpy.types.Operator):
	""" Delete the selected keyword from KeywordsListItem """
	# http://www.sinestesia.co/tutorials/making-uilists-in-blender/
	bl_idname = "listbuilder.delete_item"
	bl_label = "Deletes an item"
	#
	ilist: IntProperty()
	#
	#@classmethod
	# def poll(self, context):
		# """ Enable if there's something in the list """
		# list = self.list
		# if list == 0:
			# return context.scene.IgsOpt.KeywordsListItem > 0
		# elif list == 1:
			# return context.scene.IgsOpt.texture_string_to_replace > 0
		# else:
			# return False
		# --> marche pas!
	#
	def execute(self, context):
		ilist = self.ilist
		if ilist == 0:
			context.scene.IgsOpt.KeywordsListItem.remove(context.scene.IgsOpt.KeywordsListIndex)
			if context.scene.IgsOpt.KeywordsListIndex > 0:
				context.scene.IgsOpt.KeywordsListIndex -= 1
		elif ilist == 1:
			context.scene.IgsOpt.texture_string_to_replace.remove(context.scene.IgsOpt.texture_string_to_replace_index)
			if context.scene.IgsOpt.texture_string_to_replace_index > 0:
				context.scene.IgsOpt.texture_string_to_replace_index -= 1
		elif ilist == 2:
			context.scene.IgsOpt.object_string_to_replace.remove(context.scene.IgsOpt.object_string_to_replace_index)
			if context.scene.IgsOpt.object_string_to_replace_index > 0:
				context.scene.IgsOpt.object_string_to_replace_index -= 1
		elif ilist == 3:
			context.material.IgsMat.textures.remove(len(context.material.IgsMat.textures)-1)
		return{'FINISHED'}


# Global options:
def potentialMainObj(self, context):
	mainObj_enum_items = sorted(
		[(obj.name, obj.name, '') for obj in list(bpy.context.scene.objects)])
	
	mainObj_enum_items.insert(0, ('actObj', 'active object', ''))
	return mainObj_enum_items

class IGSExporterSettings(bpy.types.PropertyGroup):
	def __init__(self, context):
		self.context = context
	
	FilePath: StringProperty(description="Igs file destination; can be set after pushing EXPORT button too",
		subtype='FILE_PATH')
	use_selection: BoolProperty(name="use selection",
		description="export selected object and their children. active is main object if none is set",
		default=True)
	visible_children: BoolProperty(name="visible children",
		description="export only visible objects' childrens")
	Verbose: BoolProperty(name="Verbose",
		description="extended debug feature; prints a log file")
	
	u_test_mode: BoolProperty(name="Early tests mode",
		description="bypasses securities and generates missing infos /n Made for you to be able to preview your work quicker")
	u_test_mat: StringProperty(name="Standard test material",  #items=potentialTestmat, 
		description="select a standard material for IGS test exports")
	
	target_textures_directory: StringProperty(description="main texture directory relative filepath",
		default="//Textures",
		subtype='FILE_PATH')
	
	texture_string_to_replace: CollectionProperty(type=TextureStringsListItem)
	texture_string_to_replace_index: IntProperty(name="Index for texture_string_to_replace", default=0)
	object_string_to_replace: CollectionProperty(type=ObjectStringListItem)
	object_string_to_replace_index: IntProperty(name="Index for object_string_to_replace", default=0)
	hierarchy_processing: BoolProperty(name="hierarchy processing",
		description="Allows the exporter to change the scene's hierarchy",
		default=True)
	KeywordsListItem: CollectionProperty(type=KeywordsListItem)
	KeywordsListIndex: IntProperty(name="Index for KeywordsListItem", default=0)
	
	center_main_object_N: BoolVectorProperty(name="Main object centering enabled axis",
		description="enables CMO axis")
	center_main_object: FloatVectorProperty(name="Main object center",
		description="re-centers main object origin on this coordinates",
		subtype='XYZ',
		unit='LENGTH',
		size=3)
	center_main_object_rot: FloatVectorProperty(name="Main object rotate",
		description="rotates main object origin",
		subtype='EULER',
		unit='ROTATION',
		size=3)
	s_main_object: EnumProperty(items=potentialMainObj, name="main Object", 
		description="select a main object for IGS export")
	
	process_bones: BoolProperty(name="export skinned geometry",
		description="Export bones and vertex weights /n make sure all IGS objects are skinned!",
		default=False)
	
	remap_to_igf: BoolProperty(name="remap textures' paths",
		description="Remap paths from *.blend file path to *.igs file path / Map paths as if the *.igs file was in the same directory as the *.blend file",
		default=True)

class IAExporterSettings(bpy.types.PropertyGroup):
	FilePath: StringProperty(description="IA file destination",
		subtype='FILE_PATH')
	export_selected_hierarchy: BoolProperty(
		name="Selected hierarchy",
		description="Export children too?",
		default=False)
	relative_export: BoolProperty(
		name="relative export",
		description="Animation taking into account non-exported parents?",
		default=True)
	#
	Verbose: BoolProperty(
		name="Verbose",
		description="Detailed log file.",
		default=False)
	FrameRateMultiplier: IntProperty(name="Frame rate Multiplier",
		description="raises animation sample rate",
		default=7,
		min=1,
		max=10)
	RemoveLastFrame: BoolProperty(name="Remove last frame",
		description="export only visible objects' and their children's animations")
	TrimAnimation: BoolProperty(name="Trim animation",
        description="Trim unused time before first keyframe and after last one",
        default=True)
	#
	def __init__(self,
				 context,
				 FilePath):
		self.context = context
		self.FilePath = FilePath

	# Materials options:
	
def is_TSmaterial_tex(self, inst):
	return inst.source == "FILE"

def UpdateTexture(self, context):
	if not context.object or not context.object.active_material:
		return 
	if context.object.active_material.IgsMat.preview_active:
		bpy.ops.igs.preview('EXEC_DEFAULT', bind=True, invoked=True) # @UndefinedVariable
	
class IgsTex(bpy.types.PropertyGroup):
	texture: PointerProperty(name="Texture", 
		description="Texture pass for TS Material", 
		type=bpy.types.Image, 
		poll=is_TSmaterial_tex, 
		update=UpdateTexture)
	uv_layer: StringProperty(name="UV layer", 
		description="UV pass for TS Material", 
		update=UpdateTexture)
	
	use_source_tex_file_path: BoolProperty(name="Cancel 'Textures directory' setting",
 		description="disables 'Textures directory' setting on this texture")
	
def UpdateShName(self, context):
	if self.shader_name.find("ViewFacing") >= 0:
		self.view_facing = 'AUTO'
	if self.shader_name.find("FacingFlora") >= 0:
		self.mip_lod_bias = -2.0
	if self.shader_name.find("Spec") >= 0:
		self.mip_lod_bias = -1.0
	if self.shader_name == "AddATex":
		self.mip_lod_bias = -1.0
		self.filter_mode = "5";
	
	#2020: autoset texture number
	if self.shader_name != 'custom':
		global SHADERS_LIST
		num_tex = SHADERS_LIST[self.shader_name][1]
		while num_tex > len(self.textures):
			self.textures.add()
		while num_tex < len(self.textures):
			self.textures.remove(len(self.textures)-1)
			
	if self.preview_active:
		bpy.ops.igs.preview('EXEC_DEFAULT', bind=True, invoked=True) # @UndefinedVariable
	return None

def ShItems(self, context):
	global SHADERS_ENUM
	return SHADERS_ENUM

def UpdateBackFaceCullAndAlpha(self, context):
	shader = self.shader_name if self.shader_name != "custom" else self.shader_name_string
	fxShader = '.fx' in shader
	
	if not context.object or not context.object.active_material:
		return 
	
	mat = context.object.active_material
	
	mat.use_backface_culling = \
		(fxShader and self.two_sided) or (not fxShader and self.back_face_cull)

	if fxShader:
		if self.alpha_test_mode:
			mat.blend_method = "CLIP"
		else:
			mat.blend_method = "OPAQUE"
	else:
		if self.z_buffer_mode == "3":
			mat.blend_method = "BLEND"
		else:
			mat.blend_method = "OPAQUE"
			
class IgsMatPropGp(bpy.types.PropertyGroup):
	#trouver un moyen de faire update le shader à la création du matériel
	def __init__(self):
		if not self.is_property_set("textures"):
			self.textures.add()
		
	preview_active: BoolProperty(name="Preview active", 
		default=False)
	
	
	shader_name_string: StringProperty(name="Custom shader name",
		description="custom shader name to use")
	shader_name: EnumProperty(items=ShItems,
		name="Shader name",
		description="Name of the TS20XX shader to use",
		default=None,
		update=UpdateShName)
	
	textures: CollectionProperty(type=IgsTex)
	#textures_index: IntProperty(name="Index for textures", default=0)
	
	
	ambient_color: FloatVectorProperty(name="Ambiant colour",
		description="Ambiant colour used in TS",
		min=0.0,
		max=1.0,
		subtype='COLOR',
		size=4,
		default=(0.0,0.0,0.0,1.0))
	
	diffuse_color: FloatVectorProperty(name="Diffuse colour",
		description="Diffuse colour used in TS",
		min=0.0,
		max=1.0,
		subtype='COLOR',
		size=4,
		default=(1.0,1.0,1.0,1.0))
	
	specular_color: FloatVectorProperty(name="Specular colour",
		description="Specular colour used in TS",
		min=0.0,
		max=1.0,
		subtype='COLOR',
		size=4,
		default=(1.0,1.0,1.0,1.0))
	
	specular_power: FloatProperty(name="Specular power",
		description="Power of specular colour used in TS",
		min=0.0,
		max=8.0, 
		subtype='UNSIGNED',
		default=3.0)
	
	emissive_color: FloatVectorProperty(name="Emissive colour",
		description="Emissive colour used in TS",
		min=0.0,
		max=1.0,
		subtype='COLOR',
		size=4,
		default=(0.0,0.0,0.0,1.0))
	emissive_power: FloatProperty(name="Emissive power",
		description="Power of emissive colour used in TS",
		min=0.0,
		soft_min=0.0,
		soft_max=3.0,
		subtype='FACTOR')
	
	uv_param_1: FloatProperty(name="arg1", description="UV arg1, param for 1rst pass [glossiness]",
		min=0.0, max=255.0, default=32)
	uv_param_2: FloatProperty(name="arg2", description="UV arg2, param for 1rst pass",
		min=0.0, max=255.0)
	uv_param_3: FloatProperty(name="arg3", description="UV arg3, param for 1rst pass",
		min=0.0, max=255.0)
	uv_param_4: FloatProperty(name="arg4", description="UV arg4, param for 1rst pass",
		min=0.0, max=255.0)
	uv_param_5: FloatProperty(name="arg5", description="UV arg5, param for 1rst pass",
		min=0.0, max=255.0)
	uv_param_6: FloatProperty(name="arg6", description="UV arg6, param for 1rst pass",
		min=0.0, max=255.0)
	
	alpha_test_mode: BoolProperty(name="Transparency",
		description="(AlphaTestMode) renders 1 bit Alpha transparency",
		update=UpdateBackFaceCullAndAlpha)
	
	animate_uv: BoolProperty(name="Animate UVs",
		description="allows use of animated textures")
	num_frames: IntProperty(name="#Frames",
		description="number of frames anim texture has",
		min=1,
		default=1)
	f_p_s: IntProperty(name="FPS",
		description="texture animation speed - set to 0 to use blender scene's anim speed",
		min=0)
	
	uv_scroll: BoolProperty(name="scroll UVs",
		description="allows scrolling UVs on a texture")
	scroll_u: FloatProperty(name="scroll U",
		description="proportion of the image scrolled horizontally",
		step=10,
		precision=3)
	scroll_v: FloatProperty(name="scroll V",
		description="proportion of the image scrolled vertically",
		step=10,
		precision=3)
	
	fmItems = [
		("1", "Point", "1", 1),
		("2", "Bilinear", "2", 2),
		("3", "Trilinear", "3", 3),
		("5", "MipMap", "5 allows smooth mip maps transition with AddATex", 5)]
	filter_mode: EnumProperty(items=fmItems,
		name="FilterMode",
		description="Dx9 texture filter mode",
		default='3')
	mip_lod_bias: FloatProperty(name="MipLODBias",
		description="The higher, the closer you see smaller Mips. lower it to see the top Mip longer.",
		soft_min=-2.0,
		soft_max=2.0)
	
	back_face_cull: BoolProperty(name="BackFaceCull",
		description="enables back face culling on non-fx shaders",
		update=UpdateBackFaceCullAndAlpha)
	two_sided: BoolProperty(name="Two sided",
		description="disables back face culling on fx shaders",
		update=UpdateBackFaceCullAndAlpha)
	
	vfItems = [
		("NO", "No", "", 0),
		("VF", "ViewFacing", "", 1),
		("UVF", "UprightViewFacing", "", 2),
		("AUTO", "Auto", "use infos in shader's name", 3)]
	view_facing: EnumProperty(items=vfItems,
		name="Viewer Facing Options",
		description="enables viewer facing options for this material",
		default='AUTO')
	vis_mod: IntProperty(name="Visible distance",
		description="max distance the material can be observed from (0 is infinite)",
		min=0)
	
	zbItems = [
		("0", "None", "0", 0),
		("1", "Normal", "1 - default", 1),
		("2", "Write Only", "2", 2),
		("3", "Test Only", "3 - allows 8bit alpha transparency with some shaders", 3)]
	z_buffer_mode: EnumProperty(items=zbItems,
		name="ZBufferMode",
		description="3 for transparency",
		default='1',
		update=UpdateBackFaceCullAndAlpha)
	z_bias: IntProperty(name="Z Offset",
		description="use as a mean to solve z-fighting",
		default=0)
	
	comment_field: StringProperty(name="comment",
		description="field used for comment driven shader behaviours, look at possible flags")
	unlit: BoolProperty(name="Unlit",
		description="No dynamic lightning applied")
	preDPP: BoolProperty(name="Pre-DPP",
		description="process before Deferred Post-Production effects")
	use_cast_shadows: BoolProperty(name="Cast shadows",
		default=True,
		description="This material casts shadows")
	
	
	
	# Textures options:
	
# class IgsTexPropGp(bpy.types.PropertyGroup):
# 	final_tex_file_path: StringProperty(name="Export texture path",
# 		description="texture path used on IGS export instead of Blender's one.",
# 		subtype='FILE_PATH')
# 	use_source_tex_file_path: BoolProperty(name="Cancel 'Textures directory' setting",
# 		description="disables 'Textures directory' setting on this texture")


#====================================================================EXPORT OPS
class IO_OT_IGSExporter(bpy.types.Operator):
	"""Export to the IGS model format (.igs) for Railworks"""
	bl_idname = "export_scene.igs"
	bl_label = "Export IGS"
	#
	filepath: StringProperty(description="Igs file destination", subtype='FILE_PATH')
	
	# ExportHelper mixin class uses this
	filename_ext = ".igs"

	filter_glob: StringProperty(
		default="*.igs",
		options={'HIDDEN'},
		maxlen=255,  # Max internal buffer length, longer would be clamped.
	)
	
	def __init__(self):
		Config = bpy.context.scene.IgsOpt  # @UndefinedVariable
		self.filepath2 = Config.FilePath
	#
	def execute(self, context):
		# Append .igs
		Config = bpy.context.scene.IgsOpt  # @UndefinedVariable
		#
		filepath = bpy.path.ensure_ext(self.filepath, ".igs")
		Config.FilePath = filepath
		Config.context = context
		Config.dpg = context.evaluated_depsgraph_get()
		#
		from .IGSE import ExportIGS
		from .Utilityfcts import ProgressReporterHack
		
		with ProgressReporterHack(context) as pgrh:
			error = ExportIGS(Config, pgrh)
		#
		if error == "FINISHED":
			self.report({'INFO'}, "IGS file successfully created")
			return {'FINISHED'}
		else:
			self.report({'ERROR'}, "IGS exporter failed -- Check Blender's system console or logs")
			return {"FINISHED"}
	#
	def invoke(self, context, event):
		#if not self.filepath:
		if self.filepath2:
			self.filepath = bpy.path.ensure_ext(self.filepath2, ".igs")
		else:
			self.filepath = bpy.path.ensure_ext(bpy.data.filepath[-6:], ".igs")
		wm = context.window_manager
		wm.fileselect_add(self)
		return {"RUNNING_MODAL"}
        

	# Additional options for export interface

	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		scn = context.scene.IgsOpt
		
		col = layout.column()
		col.label(text="Export options:")
		
		but1 = col.row()
		but1.emboss = 'PULLDOWN_MENU'
		if scn.use_selection:
			but1.prop(scn, "use_selection", text="Export Selected", icon='RESTRICT_SELECT_OFF')
		else:
			but1.prop(scn, "use_selection", text="Export Visible", icon='RESTRICT_VIEW_OFF')
			
		col.prop(scn, "visible_children")        
        
		
class IO_OT_IAExporter(bpy.types.Operator):
	"""Export to the IA animation format (.ia) for Railworks"""
	
	bl_idname = "export_scene.ia"
	bl_label = "Export IA"
	
	filepath: StringProperty(subtype='FILE_PATH')
	
	# ExportHelper mixin class uses this
	filename_ext = ".ia"

	filter_glob: StringProperty(
		default="*.ia",
		options={'HIDDEN'},
		maxlen=255,  # Max internal buffer length, longer would be clamped.
	)
	
	def __init__(self):
		Config = bpy.context.scene.IaOpt  # @UndefinedVariable
		self.filepath2 = Config.FilePath
		
	def execute(self, context):
		# Append .ia
		FilePath = bpy.path.ensure_ext(self.filepath, ".ia")
		#
		Config = bpy.context.scene.IaOpt  # @UndefinedVariable
		Config.context = context
		Config.FilePath = FilePath
		Config.dpg = context.evaluated_depsgraph_get()
		#
		from .IAE import ExportIA
		from .Utilityfcts import ProgressReporterHack
		
		with ProgressReporterHack(context) as pgrh:
			errors = ExportIA(Config, pgrh)
			
		if 'FINISHED with error' in errors:
			self.report({'ERROR'}, "IA exporter failed -- Check Blender's system console or logs")
		else:
			self.report({'INFO'}, "IA file successfully created")
		return {"FINISHED"}

	def invoke(self, context, event):
		if not self.filepath:
			if self.filepath2:
				self.filepath = bpy.path.ensure_ext(self.filepath2, ".ia")
			else:
				self.filepath = bpy.path.ensure_ext(bpy.data.filepath, ".ia")
		WM = context.window_manager
		WM.fileselect_add(self)
		return {"RUNNING_MODAL"}

	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		scn = context.scene.IaOpt
		#
		col = layout.column()
		col.label(text="export options:")
		col2 = layout.column()
		col2.prop(scn, "Verbose")
		col.separator()
		#
		col = layout.column()
		col.prop(scn, "FrameRateMultiplier")
		col.prop(scn, "RemoveLastFrame")

#
#

class IO_OT_IGSImporter(bpy.types.Operator, ImportHelper):
	"""Import from the IGS model format (.igs) for Railworks"""
	bl_idname = "import_scene.igs"
	bl_label = "Import IGS"
	#
	# ImportHelper mixin class uses this
	filename_ext = ".igs"
	
	filter_glob : StringProperty(
        default="*.igs;",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
        )
	
	from .IGSI import PROFILE_MODE
	verbose_lv: IntProperty(
		name="Verbose", 
		description="Logging verbosity",
		default=0, 
		options={'HIDDEN'} if not PROFILE_MODE else set(),
		min=0, max=4)
	
	def execute(self, context):
		from .IGSI import ImportIGS
		from .Utilityfcts import ProgressReporterHack
		
		with ProgressReporterHack(context) as pgrh:
			error = ImportIGS(self.filepath, self.verbose_lv, pgrh)
		#
		if error == "FINISHED":
			self.report({'INFO'}, "IGS file successfully imported")
			return {'FINISHED'}
		else:
			self.report({'ERROR'}, "IGS importer failed -- Check Blender's system console or logs")
			return {"FINISHED"}

class IO_OT_IAImporter(bpy.types.Operator, ImportHelper):
	"""Import from the IA animation format (.ia) for Railworks"""
	
	bl_idname = "import_scene.ia"
	bl_label = "Import IA"
	
	# ImportHelper mixin class uses this
	filename_ext = ".ia"
	
	filter_glob : StringProperty(
        default="*.ia;",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
        )
	
	from .IAI import PROFILE_MODE
	verbose_lv: IntProperty(
		name="Verbose", 
		description="Logging verbosity",
		default=0, 
		options={'HIDDEN'} if not PROFILE_MODE else set(),
		min=0, max=3)
	
	def execute(self, context):
		from .IAI import ImportIA
		from .Utilityfcts import ProgressReporterHack
		
		with ProgressReporterHack(context) as pgrh:
			errors = ImportIA(self.filepath, self.verbose_lv, pgrh)
			
		if 'FINISHED with error' in errors:
			self.report({'ERROR'}, "IA importer failed -- Check Blender's system console or logs")
		else:
			self.report({'INFO'}, "IA file successfully imported")
		return {"FINISHED"}
	
class IO_OT_SACEImporter(bpy.types.Operator, ImportHelper):
	"""Loads image from Simis ACE V2 texture format (.ace) files
in memory for you to use or save as png"""
	
	bl_idname = "import_scene.sace"
	bl_label = "Import SACE"
	
	from .IGSI import PROFILE_MODE
	pmode = PROFILE_MODE
	
	# ImportHelper mixin class uses this
	filename_ext = ".ace"
	filter_glob : StringProperty(
        default="*.ace;",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
        )
	
	directory: StringProperty()
	
	files: CollectionProperty(
            name="File Path",
            type=bpy.types.OperatorFileListElement,
            )
	
	to_png: BoolProperty(
		name="save png", 
		description="saves files as png in same directory",
		default=False)
	
	to_dds: BoolProperty(
		name="save dds", 
		description="saves files as dds in same directory",
		default=False)
	
	verbose_lv: IntProperty(
		name="Verbose", 
		description="Logging verbosity",
		default=0, 
		options={'HIDDEN'} if not pmode else set(),
		min=0, max=3)
	
	def execute(self, context):
		from .IGSI import create_image_from_ace
		import os, traceback
		
		if self.files:
			ret = {'CANCELLED'}
			dirname = os.path.dirname(self.filepath)
			num_valid_files = 0
			for file in self.files:
				path = os.path.join(dirname, file.name)
				try:
					image = create_image_from_ace(path, self.verbose_lv, self.to_png or self.to_dds)  # @UnusedVariable
					num_valid_files += 1
					ret = {'FINISHED'}
					
				except (RuntimeError, NotImplementedError) as e:
					self.report({'ERROR'}, f"SACE import failed, {e}")
					if self.pmode:
						print(traceback.format_exc())
					ret = {'CANCELLED'}
					break
					
			if (num_valid_files > 0) and ('CANCELLED' not in ret):
				self.report({'INFO'}, f"{num_valid_files} SACE files available in image list!")
				
				if self.to_dds:
					#to dds with gimp
					gimp_py_cmd = r'"G:\\Program Files\\GIMP 2\\bin\\gimp-console-2.10.exe" -idcf --batch-interpreter=python-fu-eval --batch="'
					for file in self.files:
						path = os.path.join(dirname, file.name[:-3])
						gimp_py_cmd += f'image = pdb.file_png_load(r\\\"{path}png\\\", r\\\"{file.name[:-3]}png\\\", run_mode=1); drawable = image.active_layer; pdb.file_dds_save(image, drawable, r\\\"{path}dds\\\", r\\\"{file.name[:-3]}dds\\\", 0, 1, 0, 2, -1, 7, 2, 0, 1, 0.0, 1, 1, 0.5);gimp.delete(image);'
					gimp_py_cmd += '" --batch="pdb.gimp_quit(1)"'
					
					import subprocess
					#print(gimp_py_cmd)
					proc = subprocess.run(gimp_py_cmd,
										#cwd=gimp_path,
										stdout=subprocess.PIPE,
										stderr=subprocess.STDOUT)
					print(proc.stdout.decode('windows-1252'))
					
				if self.to_dds and not self.to_png:
					#delete pngs
					print("SACE to DDS: deleting pngs")
					for file in self.files:
						path = os.path.join(dirname, file.name[:-3]+'png')
						os.remove(path)
				
			return ret
		else:
			try:
				image = create_image_from_ace(self.filepath, self.verbose_lv)  # @UnusedVariable
			except (RuntimeError, NotImplementedError) as e:
				self.report({'ERROR'}, f"SACE import failed, {e}")
				if self.pmode:
					print(traceback.format_exc())
	
				return {"CANCELLED"}
			
			self.report({'INFO'}, "SACE file available in image list!")
			return {"FINISHED"}
		
		

#====================================================================UTILITY FCTS
#

def get_TS_Path_From_WinReg():
	import winreg
	import os.path
	TS_path = ""
	def keypathval(path):
		path = path.split("\\")
		main_key = eval(path[0],{},dict(HKEY_LOCAL_MACHINE=winreg.HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER=winreg.HKEY_CURRENT_USER, HKEY_CURRENT_CONFIG=winreg.HKEY_CURRENT_CONFIG))
		with winreg.OpenKey(main_key, path[1], reserved=0, access=winreg.KEY_READ) as key:
			#print("mainkey:", path[0])
			#print("key:", path[1])
			for i in range(2, len(path)-1):
				key = winreg.OpenKey(key, path[i], reserved=0, access=winreg.KEY_READ)
				#print("key:", path[i])
			val_tpl = ("","","")
			index = 0
			while path[len(path)-1] != val_tpl[0]:
				val_tpl = winreg.EnumValue(key, index)
				#print("val tuple:", val_tpl)
				index += 1
		return val_tpl[1]
	
	def vdflibtspathval(vdf_file):
		from . libs import vdf
		lib_f = (vdf.load(vdf_file))["LibraryFolders"]
		for i in range(1, len(lib_f)-2):
			lib_path = lib_f[str(i)]
			yield lib_path
		
	try:
		key_dir = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\RailWorks\Path"
		TS_path = os.path.normpath(keypathval(key_dir))
	except:
		try:
			key_dir = r"HKEY_CURRENT_USER\Software\Valve\Steam\SteamPath"
			steam_path = os.path.normpath(keypathval(key_dir))
			#print("Steam path:", steam_path)
			if os.path.isfile(steam_path + r"\SteamApps\appmanifest_24010.acf"):
				TS_path = steam_path + r"\SteamApps\common\railworks"
			else:
				with open(steam_path + r"\SteamApps\libraryfolders.vdf", encoding='utf-8') as vreg:
					#print("libraryfolders reg at:", steam_path + r"\SteamApps\libraryfolders.vdf")
					for ipath in vdflibtspathval(vreg):
						#print("Steam lib path:", ipath)
						if os.path.isfile(ipath + r"\SteamApps\appmanifest_24010.acf"):
							TS_path = ipath + r"\SteamApps\common\railworks"
							#print("TS found at:", TS_path)
							break
		except OSError as E:
			print("BRIAGE :: TS path not found in Windows' registry -- [WinError n°{0}] \"{1}\"".format(E.errno, E.strerror))
			return ""
		except:
			print("BRIAGE :: TS path not found in Windows' registry -- unknown error")
			return ""
		
	print("BRIAGE :: TS path gotten from Windows' registry")
	return TS_path

def get_shader_names():
	import xml.etree.ElementTree as ET
	def saveS(temp_shader_enum, index=0, temp_shader_list=None, include_custom=True):
		if include_custom:
			temp_shader_enum.append(("custom","\\custom shader\\","use a shader not listed here", index + 1))
			index += 1
		#save results:
		global SHADERS_ENUM
		SHADERS_ENUM = temp_shader_enum
		if temp_shader_list:
			global SHADERS_LIST
			SHADERS_LIST = temp_shader_list
			try:
				bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='INFO', message=" Shader list built!")  # @UndefinedVariable
			except:
				print("BRIAGE :: Shader list built")
		return	
	
	#retrieve TS path from user prefs:
	
	addon_prefs = bpy.context.preferences.addons[__package__].preferences
	temp_shader_enum = []
	
	if (addon_prefs.ts_install_path != ""):
		path = addon_prefs.ts_install_path
		try:
			bpy.path.abspath(path)
		except:
			try:
				bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='WARNING', message=" Cannot retrieve shader list! - Invalid path")  # @UndefinedVariable
			except:
				print("BRIAGE :: Cannot retrieve shader list! - Invalid path")
			saveS(temp_shader_enum)
			
	else:#retrieve TS path from Windows:
		path = get_TS_Path_From_WinReg()
		if path == "":
			try:
				bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='WARNING', message=" Cannot retrieve shader list! - No Windows registry entry")  # @UndefinedVariable
			except:
				print("BRIAGE :: Cannot retrieve shader list! - No Windows registry entry")
			saveS(temp_shader_enum)
			return
		addon_prefs.ts_install_path = path
	
	#assign data from UI
	print(path)
	shader_path = bpy.path.abspath(path) + '\\dev\\Shaders\\Shaders.xml'
	chars_per_line = addon_prefs.chars_per_line
	
	#read XML in TS data:
	try:
		tree = ET.parse(shader_path)
		root = tree.getroot()
	except:
		try:
			bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='WARNING', message=" Cannot retrieve shader list! - Wrong path")  # @UndefinedVariable
		except:
			print("BRIAGE :: Cannot retrieve shader list! - Wrong path")
		finally:
			saveS(temp_shader_enum)
		return
	if root.tag != 'NamedShaders':
		try:
			bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='WARNING', message=" Cannot retrieve shader list! - Wrong file")  # @UndefinedVariable
		except:
			print("BRIAGE :: Cannot retrieve shader list! - Wrong file")
		finally:
			saveS(temp_shader_enum)
		return

	#building shader list
	temp_shader_list = {} #dict for processing shaders
	for child in root:
		#put newlines in descriptions every ~50 chars to ease reading in Blender UI
		txt = child[0].text
		if txt == None: txt = "\\ desc unavailable in shader dict \\"
		txtwd = txt.split()
		txtwd.reverse()
		decription = ""
		while txtwd > []:
			desc_line = ""
			while (len(desc_line) < chars_per_line) and (txtwd > []):
				desc_line += txtwd.pop()
				desc_line += " "
			desc_line += " \n"
			decription += desc_line
		#remember slots:
		sNum_Slots = int(child.attrib['numSlots'])
		#dump infos in dict
		temp_shader_list[child.attrib['name']] = [sNum_Slots, sNum_Slots, decription]

	temp_shader_list['TrainGlassWeatherEffects.fx'][1] = 3 #Blender numslot not the same as in MAX for this shader
	#print(temp_shader_list)
	#create enum:
	temp_shader_enum = []
	index = 0
	for k, _ in sorted(temp_shader_list.items()):
		temp_shader_enum.append((k, k, "", index))
		index += 1
	
	#2022 Summer : fix for custom included after customshaders xml
	temp_shader_enum.append(("custom","\\custom shader\\","use a shader not listed here", index + 1))
	index += 1
	
	#2022: Jachym's custom shader insertion test
	custom_shader_path = bpy.path.abspath(path) + '\\dev\\Shaders\\CustomShaders.xml'
	try:
		tree = ET.parse(custom_shader_path)
		root = tree.getroot()
		if root.tag == 'NamedShaders':
			for child in root:
				#put newlines in descriptions every ~50 chars to ease reading in Blender UI
				txt = child[0].text
				if txt == None: txt = "\\ desc unavailable in shader dict \\"
				txtwd = txt.split()
				txtwd.reverse()
				decription = ""
				while txtwd > []:
					desc_line = ""
					while (len(desc_line) < chars_per_line) and (txtwd > []):
						desc_line += txtwd.pop()
						desc_line += " "
					desc_line += " \n"
					decription += desc_line
				#remember slots:
				sNum_Slots = int(child.attrib['numSlots'])
				#dump infos in dict
				name = child.attrib['name']
				temp_shader_list[name] = [sNum_Slots, sNum_Slots, decription]
				temp_shader_enum.append((name, name, "", index))
				index += 1
	except:
		try:
			bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='INFO', message=" No or invalid "+custom_shader_path)  # @UndefinedVariable
		except:
			print("BRIAGE :: No or invalid "+custom_shader_path)
	finally:
		saveS(temp_shader_enum, index, temp_shader_list, False)
	return

def update_shader_names(self, context):
	get_shader_names()
	return
#

#====================================================================UI OPS
#
class BRIAGE_OT_Briage_CopyMaterial(bpy.types.Operator) :
	def execute(self, context):
		return {'FINISHED'}
	#TODO: Faire un op de copie de matériel à matériel
	

class BRIAGE_OT_TxtHlp_Root() : #methods for drop-down help menus from lists
	def execute(self, context):
		return {'FINISHED'}
	#
	title = "//empty//"
	paragraph = []
	#
	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_popup(self, width=200)
	#
	def draw(self, context):
		self.layout.use_property_split = True
		col = self.layout.column()
		col.label(text=(self.title+" :"))
		col = col.split(factor=0.1)
		col.label(text="")
		col2 = col. column()
		for line in self.paragraph:
			col2.label(text=line)

class BRIAGE_OT_TxtHlp_CfToggles(bpy.types.Operator, BRIAGE_OT_TxtHlp_Root) : 
	bl_idname = "briage.txthlp_cftoggles"
	bl_label = "Description"  
	bl_options = {"REGISTER"} 
	#
	title = "Comment field toggles"
	paragraph = [ 
	":forceprelit",
	":pointlit",
	":pre-dpp",
	":unfog",
	":animdelay",
	":animmaxframe",
	":fpsfraction",
	":fadedist",
	":noclip",
	":startinvisible",
	":startnocollide",
	":nocompress",
	":forceunder",
	":fullalphasort",
	":occlude",
	":alternode", #alterable node... for clothes?!
	":shatter",
	":objectstick", ]#Gridifiying ?!!

class BRIAGE_OT_TxtHlp_BuildInKwd(bpy.types.Operator, BRIAGE_OT_TxtHlp_Root) : 
	bl_idname = "briage.txthlp_buildinkwd"  
	bl_label = "Description"  
	bl_options = {"REGISTER"} 
	#
	title = "Build-in Keywords"
	paragraph = ["   Object names:"]+RESERVED_OBJECT_NAMES + \
				["   Followed by a number:"]+RESERVED_OBJECT_NAMES_NB
	


#====================================================================UI PANELS
#
class SCENE_PT_igs(SceneButtonsPanel, Panel):
	"""Igs config panel"""
	bl_idname = "SCENE_PT_igs"
	bl_label = "IGS export config"
	bl_options = {'DEFAULT_CLOSED'}
	#
	def draw_header(self, context):
		self.layout.operator(IO_OT_IGSExporter.bl_idname, text="EXPORT", icon='FILE_TICK')
	
	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		layout.use_property_decorate = False #No anim
		
		scn = context.scene.IgsOpt
		#
		#confuses users but func stays in code and still useful
		#in file selector:
		#col = layout.column()
		#col.label(text="IGS target filepath:")
		#col.prop(scn, "FilePath", text="", icon='FILE')
		
		#col.separator()
		#
		col = layout.column()
		col.label(text="export options:")
		col2 = layout.split(factor=0.5)
		col1 = col2.column()
		but1 = col1.row()
		but1.emboss='PULLDOWN_MENU'
		if scn.use_selection:
			but1.prop(scn, "use_selection", text="export selected", icon='RESTRICT_SELECT_OFF')
		else:
			but1.prop(scn, "use_selection", text="export visible", icon='RESTRICT_VIEW_OFF')
		col1.prop(scn, "visible_children")
		col2 = col2.column()
		col2.prop(scn, "Verbose")
		col = col1.column()
		col.prop(scn, "hierarchy_processing")
		col = col1.column()
		#col.enabled = False
		col.prop(scn, "process_bones")
		col.separator()
		#
		col = layout.column()
		col.separator()
		col.prop(scn, "s_main_object", text="main object")
		col = layout.column()
		#col.label(text="")
		spl = col.row().split(factor=0.9)
		spl.prop(scn, "center_main_object")
		spl.prop(scn, "center_main_object_N", text="")
		spl = col.row().split(factor=0.9)
		spl.prop(scn, "center_main_object_rot")
		spl.label(text="")
		col.separator()
		#
		col = layout.column()
		col.label(text="Textures path mapping:")
		if scn.remap_to_igf:
			col.prop(scn, "remap_to_igf", text="write from *.IGS destination", icon="FILE_BLANK")
		else:
			col.prop(scn, "remap_to_igf", text="write from *.blend location", icon="FILE_BLEND")
		col.label(text="Textures directory:")
		col.prop(scn, "target_textures_directory", text="", icon='IMAGE_DATA')
		col.label(text="to change path individually go to texture's tab,")
		col.label(text="individual parameters overrides the main")
		col.label(text="texture directory.")
		col.separator()
		#
		col = layout.column()
		box = col.box()
		box.prop(scn, "u_test_mode")
		col_in = box.column()
		col_in.active = scn.u_test_mode
		#col_in.label("Test material:")
		if len(bpy.data.materials):  # @UndefinedVariable
			col_in.label(text="Standard test material:")
			col_in.prop_search(scn, "u_test_mat", bpy.data, "materials", text="", icon="MATERIAL_DATA")
		else:
			col_in.label(text="No materials in blend!", icon="MATERIAL_DATA")
		if scn.u_test_mode:
			box.label(text="UV and material checks are bypassed", icon='INFO')
		col.label(text="")
		col.separator()
		#
		# http://www.sinestesia.co/tutorials/making-uilists-in-blender/
		col = layout.column()
		col.label(text="Texture strings to replace:", icon='TEXTURE_DATA')
		col.template_list("LISTBUILDER_UL_BODY", "old string -> new string", scn, "texture_string_to_replace", scn, "texture_string_to_replace_index" )
		row = col.row(align=True)
		row.operator('listbuilder.new_item', text='NEW', icon='ADD').ilist=1
		row.operator('listbuilder.delete_item', text='REMOVE', icon='REMOVE').ilist=1
		col.separator()
		#
		colg = col.split(factor=0.9)
		colg.label(text="Custom keywords:", icon='XRAY')
		colg.operator(BRIAGE_OT_TxtHlp_BuildInKwd.bl_idname, text="", icon='QUESTION', emboss=True)
		col.template_list("LISTBUILDER_UL_BODY", "custom keywords", scn, "KeywordsListItem", scn, "KeywordsListIndex" )
		row = col.row(align=True)
		row.operator('listbuilder.new_item', text='NEW', icon='ADD').ilist=0
		row.operator('listbuilder.delete_item', text='REMOVE', icon='REMOVE').ilist=0
		col.separator()
		#
		col.label(text="Object Name strings to replace: (!!BONES and SNAP POINTS parenting will fail!!)", icon='OBJECT_DATA')
		col.template_list("LISTBUILDER_UL_BODY", "old name string -> new full name", scn, "object_string_to_replace", scn, "object_string_to_replace_index" )
		row = col.row(align=True)
		row.operator('listbuilder.new_item', text='NEW', icon='ADD').ilist=2
		row.operator('listbuilder.delete_item', text='REMOVE', icon='REMOVE').ilist=2
		col.separator()
		#
		layout.operator(IO_OT_IGSExporter.bl_idname, text="EXPORT", icon='FILE_TICK')

class SCENE_PT_ia(SceneButtonsPanel, Panel):
	"""Igs config panel"""
	bl_idname = "SCENE_PT_ia"
	bl_label = "IA export config"
	bl_options = {'DEFAULT_CLOSED'}
	#
	def draw_header(self, context):
		self.layout.operator(IO_OT_IAExporter.bl_idname, text="EXPORT", icon='ANIM')
	
	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		layout.use_property_decorate = False #No anim
		
		scn = context.scene.IaOpt
		scn2 = context.scene.IgsOpt
		#
		#col = layout.column()
		#col.label(text="IA target filepath:")
		#col.prop(scn, "FilePath", text="", icon='FILE')
		#col.separator()
		#
		col = layout.column()
		col.label(text="export options:")
		col2 = col.split(factor=0.5)
		col1 = col2.column()
		but1 = col1.row()
		but1.emboss='PULLDOWN_MENU'
		if scn2.use_selection:
			but1.prop(scn2, "use_selection", text="Selected", icon='RESTRICT_SELECT_OFF')
			col1.prop(scn, "export_selected_hierarchy")
		else:
			but1.prop(scn2, "use_selection", text="Visible ", icon='RESTRICT_VIEW_OFF')
			col1.label(text="")
		col1.prop(scn2, "visible_children")
		col1.prop(scn, "relative_export")
		col1.separator()
		col1.prop(scn2, "process_bones")
		col2 = col2.column()
		col2.label(text="")
		col2.prop(scn, "Verbose")
		col2.separator
		col2.prop(scn, "FrameRateMultiplier")
		col2.prop(scn, "RemoveLastFrame")
		col2.prop(scn, "TrimAnimation")

class MATERIAL_PT_igs(MaterialButtonsPanel, Panel):
	"""igs per material config"""
	bl_idname = "MATERIAL_PT_igs"
	bl_label = "IGS options"
	bl_options = set()
	bl_order = 1
	# bl_space_type = 'PROPERTIES'
	# bl_region_type = 'WINDOW'
	# bl_context = "material"
	COMPAT_ENGINES = {'CYCLES', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'BLENDER_WORKBENCH'}
	#
	# @classmethod
	# def poll(self, context):
		# return context.material 
	#
	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		layout.use_property_decorate = False #No anim
		
		mat = context.material.IgsMat
		#bmat = context.material
		#
		col = layout.column()
		col.operator(PREVIEW_OT_IGSMatPreview.bl_idname, text=("Unbind" if mat.preview_active else "Bind"), icon='INFO').bind=(not mat.preview_active)
		col.label(text="Shader name:")
		if len(SHADERS_ENUM) > 1:
			col.prop(mat, "shader_name", text="")
		#
		if len(SHADERS_ENUM) == 1:
			col.prop(mat, "shader_name_string", text="")
			abox = col.box()
			abox = abox.split(factor=0.1)
			abox1 = abox.row()
			abox1.label(text="", icon='CANCEL')
			abox1.label(text="", icon='UNLINKED')
			abox = abox.column()
			abox.label(text="Shaders' list not generated!")
			abox.label(text="Please enter the path to your TS directory in:")
			abox.label(text="File>User pref>Add-ons>IGS Model Format (.igs)")
			fxShader = ('.fx' in mat.shader_name_string)
		elif mat.shader_name == 'custom':
			col.label(text="Custom shader name:")
			col.prop(mat, "shader_name_string", text="")
			fxShader = ('.fx' in mat.shader_name_string)
		else:
			fxShader = ('.fx' in mat.shader_name)
			col.label(text="Shader description:")
			col3 = col.split(factor=0.1)
			col3.label(text="")
			bol = col3.column().box().column()
			try:
				txt = SHADERS_LIST[mat.shader_name][2]
			except:
				bol.label(text="unavailable")
			else:
				txt = txt.splitlines()
				for line in txt:
					bol.label(text=line)
				#2020 autoset number of texture: this info is redundant
				#bolr = bol.row()
				#bolr.label(text="")
				#num_tex = SHADERS_LIST[mat.shader_name][1]
				#bolr.label(text="slots needed: " + str(num_tex), icon='TEXTURE')
		#
			
		#2020 Textures
		col = layout.column()
		col.label(text="Textures:", icon='TEXTURE_DATA')
		if mat.shader_name == 'custom': 
			#2020: choose what you need
			#col.template_list("LISTBUILDER_UL_BODY", "", mat, "textures", mat, "textures_index" )
			row = col.row(align=True)
			if len(mat.textures) < 8:
				row.operator('listbuilder.new_item', text='NEW', icon='ADD').ilist=3
			else:
				row.label(text="Max render stages!", icon='INFO')
			if len(mat.textures) < 1:
				row.label(text="")
			else:
				row.operator('listbuilder.delete_item', text='REMOVE', icon='REMOVE').ilist=3
		texturebox = col.box()
		if len(mat.textures):
			for texture in mat.textures:
				tbox = texturebox.box().column()
				line1 = tbox.row()
				line1.emboss='PULLDOWN_MENU'
				line1.template_ID(texture, "texture", open="image.open", unlink="", live_icon=True)
				line2 = tbox.row().split(factor=0.7)
				line2.prop_search(texture, "uv_layer", context.object.data, "uv_layers", text="", icon="UV")
				line2.prop(texture, "use_source_tex_file_path", text="raw path")
		else:
			if not mat.is_property_set('shader_name'):
				texturebox.alert = True
				texturebox.label(text="Select a shader to update")
			else:
				texturebox.label(text="No textures")
		col.separator()
		#
		col = layout.column()
		#
		grid = col.grid_flow(columns=2)
		grid.label(text="Ambiant")
		grid.prop(mat, "ambient_color", text="color")
		grid.label(text="Emissive")
		grid.prop(mat, "emissive_color", text="color")
		grid.prop(mat, "emissive_power", text="power")
		grid.label(text="Diffuse")
		grid.prop(mat, "diffuse_color", text="color")
		grid.label(text="Specular")
		grid.prop(mat, "specular_color", text="color")
		grid.prop(mat, "specular_power", text="power")
		
		col.separator()
		#
		col = layout.column()
		box = col.box()
		box.label(text="UV Arguments")
		grid = box.grid_flow(columns=3,row_major=True)
		grid.prop(mat, "uv_param_1")
		grid.prop(mat, "uv_param_2")
		grid.prop(mat, "uv_param_3")
		grid.prop(mat, "uv_param_4")
		grid.prop(mat, "uv_param_5")
		grid.prop(mat, "uv_param_6")
		
		col.separator()
		#
		box = col.box()
		box.label(text="Animation / UV Special effects:")
		rbox = box.split()
		lbox = rbox.column()
		lbox.active = not fxShader
		lbox.prop(mat, "uv_scroll")
		sub = lbox.column()
		sub.enabled = mat.uv_scroll
		sub = sub.column(align=True)
		sub.prop(mat, "scroll_u", text="u")
		sub.prop(mat, "scroll_v", text="v")
		rbox = rbox.column()
		rbox.prop(mat, "animate_uv")
		sub = rbox.column(align=True)
		sub.enabled = mat.animate_uv
		sub.prop(mat, "num_frames")
		sub.prop(mat, "f_p_s")
		
		col2 = col.split()
		col1 = col2.column()
		#
		col1.label(text="Transparency:")
		col1.prop(mat, "z_buffer_mode")
		col1.prop(mat, "alpha_test_mode")
		col1.separator()
		#
		col1.label(text="Display:")
		col1.prop(mat, "z_bias")
		col1.prop(mat, "vis_mod")
		col1.prop(mat, "mip_lod_bias")
		col1.prop(mat, "filter_mode")
		col1.separator()
		#
		col1.label(text="Miscellaneous:")
		col1.prop(mat, "unlit")
		col1.prop(mat, "preDPP")
		col1.prop(mat, "use_cast_shadows")
		col1.separator()
		#
		col2 = col2.column()
		#
		col2.label(text="View facing:")
		#col2sub.enabled = not ('ViewFacing' in mat.shader_name) #not such a good idea finally...
		col2.prop_tabs_enum(mat, "view_facing")
		col2.separator()
		#
		col2.label(text="Double siding:")
		line = col2.row()
		line.active = not fxShader
		line.prop(mat, "back_face_cull")
		line = col2.row()
		line.active = fxShader
		line.prop(mat, "two_sided")
		col2.separator()
		#
		col = layout.column()
		col.label(text="Comment field:")
		colg = col.split(factor=0.1)
		colg.operator(BRIAGE_OT_TxtHlp_CfToggles.bl_idname, text="", icon='QUESTION', emboss=True)
		colg.prop(mat, "comment_field", text="")

class AddOn_Prefs_igs(bpy.types.AddonPreferences):
	bl_idname = __package__
	#
	ts_install_path: StringProperty(name="TS install directory",
		description="TS20XX install path",
		default="",
		update=update_shader_names,
		subtype='FILE_PATH')
	chars_per_line: IntProperty(name="line length for shader descriptions",
		description="number on chars per line in the description",
		min=25,
		default=45)
	#
	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		layout.prop(self, "ts_install_path")
		layout.prop(self, "chars_per_line")


#MENUS
def menu_func_exp(self, context):
	self.layout.operator(IO_OT_IGSExporter.bl_idname, text="TS shape (.igs)")
	self.layout.operator(IO_OT_IAExporter.bl_idname , text="TS animation (.ia)")
	
def menu_func_imp(self, context):
	self.layout.operator(IO_OT_IGSImporter.bl_idname , text="TS shape (.igs)")
	self.layout.operator(IO_OT_IAImporter.bl_idname  , text="TS animation (.ia)")
	self.layout.operator(IO_OT_SACEImporter.bl_idname, text="Simis ACE image (.ace)")

#====================================================================REGISTER
classes = (
	REPORTER_OT_OhlalalaLa_LaCata,
	KeywordsListItem,
	TextureStringsListItem,
	ObjectStringListItem,
	LISTBUILDER_UL_BODY,
	LISTBUILDER_OT_NewItem,
	LISTBUILDER_OT_DeleteItem,
	IGSExporterSettings,
	IAExporterSettings,
	IgsTex,
	IgsMatPropGp,
	IO_OT_IGSExporter,
	IO_OT_IAExporter,
	IO_OT_IGSImporter,
	IO_OT_IAImporter,
	IO_OT_SACEImporter,
	BRIAGE_OT_TxtHlp_CfToggles,
	BRIAGE_OT_TxtHlp_BuildInKwd,
	SCENE_PT_igs,
	SCENE_PT_ia,
	MATERIAL_PT_igs,
	AddOn_Prefs_igs)

from bpy.utils import register_classes_factory  # @UnresolvedImport
register_cls, unregister_cls = register_classes_factory(classes)

def register():
	register_cls()
	
	bpy.types.TOPBAR_MT_file_export.append(menu_func_exp)
	bpy.types.TOPBAR_MT_file_import.append(menu_func_imp)
	
	bpy.types.Scene.IgsOpt = PointerProperty(type=IGSExporterSettings,name="IGS Options",
		description="Options for IGS exporter")
	bpy.types.Scene.IaOpt = PointerProperty(type=IAExporterSettings, name="IA Options",
		description="Options for IA exporter")
	bpy.types.Material.IgsMat = PointerProperty(type=IgsMatPropGp,name="IGS properties",
		description="properties for IGS export")

	get_shader_names()

def unregister():
	bpy.types.TOPBAR_MT_file_export.remove(menu_func_exp)
	bpy.types.TOPBAR_MT_file_import.remove(menu_func_imp)
	
	unregister_cls()
	
	del bpy.types.Scene.IgsOpt
	del bpy.types.Scene.IaOpt
	del bpy.types.Material.IgsMat
