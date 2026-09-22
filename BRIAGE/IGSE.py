# ##### BEGIN LICENSE BLOCK #####
#
# Copyright (C) 2024 'Juju49'(MERLE-RÉMOND Julian), 'DOM107'
# see license notes __init__.py
#
# ##### END LICENSE BLOCK #####
from BRIAGE.SceneCheck import _checkLOD

#====================================================================INFO
__doc__ = ( # @ReservedAssignment
"""submodule for exporting IGS files:  
	mthd: ExportIGS(Config)
	Config is a class containing 'IgsOpt' and 'context = bpy.context'""")

_info = {
	"version" : (3, 2, "101")}

IGSE_VERSION = 'IGSE V' + '.'.join(str(i) for i in _info['version'])

#====================================================================IMPORTS
import bpy # @UnresolvedImport
import bmesh # @UnresolvedImport
import os

from mathutils import Vector, Matrix   # @UnresolvedImport

from ._datastructs import IGF
from . Utilityfcts import print_pr, center_main_object
from . Groups import make_groups
from . Bl_data import (
	SHADERS_ENUM)
from . SceneCheck import checkScene
from . CleanAndProperSceneExport import CleanAndProperSceneExport


#====================================================================GLOBALS
PROFILE_MODE = "dev" in _info['version'][2]

END_OK = 0
END_ERROR = -1
END_WARNING = -2

KEYWORD_OTHER = 0
KEYWORD_CUSTOM = 1

MAX_NAME_WITH_LOD = 31
MAX_NAME_WITHOUT_LOD = 24
SIZE_DISTANCE_DIGITS = 4
	
VNULL3D = Vector((0.0, 0.0, 0.0))

#matrix to transform vectors into TS instance local space
TS_MATRIX = Matrix(((1.0, 0.0, 0.0, 0.0),
			        (0.0, 0.0, 1.0, 0.0),
			        (0.0, 1.0, 0.0, 0.0),
			        (0.0, 0.0, 0.0, 1.0)))
#====================================================================EXPORT FCTS

#======================================MATERIALS

# Add a texture file name to the textures list
#MODIFS2016: custom texture paths implementation
def add_texture_to_list(textures_list, Config, texture_data): # MAJ_1_4_0b
	"""list[str] * Config * TextureData -> int
	Register a new texture and/or returns its index+1 in texture_list"""
	#MODIFS2016: specific dir and reroute to props
	# error struct for ref: bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message="")
	
	# MODIFS2016 final specific folder
	# dec2020 canceled and implemented in a more robust way below
	#final_tex_file_path	= texture_data.texture.filepath

	# MODIFS2016 texture path
	texture_file_name = texture_data.texture.filepath
	#f_ext = texture_file_name.rfind('.')
	tfn_test = os.path.basename(texture_file_name)
	if tfn_test != "":
		ext = tfn_test.rfind('.')
		#replaced by a global SceneCheck# if (ext == -1) and (f_ext == -1): #if no other texture path can be assigned
		#replaced by a global SceneCheck# 	return -2
		
		texture_file_name = tfn_test[:ext]
	
	else: #fallback mode if os.path.basename fails to compute correctly
		ext = texture_file_name.rfind('.')
		#replaced by a global SceneCheck# if (ext == -1) and (f_ext == -1): #if no other texture path can be assigned
		#replaced by a global SceneCheck# 	return -2
		
		base = texture_file_name.rfind('\\')
		# dec2020: if base == -1 we don't trim in the beginning but want to trim the end in this manner: [1-1:ext]
		texture_file_name = texture_file_name[base+1:ext]
	del tfn_test
	
	# Process texture file substitution   # MAJ_1_4_0b #MODIFS2016
	for strings in Config.texture_string_to_replace: 
		if "#" == strings.name[0]: #texture name replace mode
			if strings.name[1:] == texture_file_name:
				texture_file_name = strings.prop1
				
		elif (strings.name in texture_file_name): #string replace mode
			texture_file_name = texture_file_name.replace(strings.name, strings.prop1)

	# =================================================convert texture_file_name to path
	

	
	# Add specific target:
	if texture_data.use_source_tex_file_path or (Config.target_textures_directory == ""):
		ext = (texture_data.texture.filepath).rindex('.')
		texture_file_name = texture_data.texture.filepath[:ext]
	
	#elif f_ext != -1: #replaced by dot count on line 119
	#	texture_file_name = texture_file_name[:f_ext]
	
	# Add target textures directory:
	else:
		texture_file_name = Config.target_textures_directory + "\\" + texture_file_name
	
	if (os.path.basename(texture_file_name)).count(".") > 0:
		texture_file_name += ".safe"
	
	#MODIFS2016 Remap paths:
	if Config.remap_to_igf:
		ref_path = os.path.dirname(bpy.path.abspath(Config.FilePath))  # @UndefinedVariable
	else:
		ref_path = bpy.path.abspath("//")  # @UndefinedVariable
		
		#replaced by a global SceneCheck# try:
	texture_file_name = (bpy.path.relpath(bpy.path.abspath(texture_file_name), start=ref_path)).lstrip("/")  # @UndefinedVariable
		#replaced by a global SceneCheck# except ValueError as VE:
		#replaced by a global SceneCheck# 	p_args = (VE.args[0]).split(',')
		#replaced by a global SceneCheck# 	p_texname = bpy.path.basename(texture_file_name)
		#replaced by a global SceneCheck# 	bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR', message="Final IGS export path {1} .  But textures {0} .  Please, export to the same drive your data are from!  Texture '{2}' not added".format(p_args[0], p_args[1], p_texname))
		#replaced by a global SceneCheck# 	return -1
	#else:
	#	texture_file_name = (bpy.path.relpath(bpy.path.abspath(texture_file_name), start=ref_path)).lstrip("/")
	
	#DOESN'T WORK with TS because ConvertToGeo checks number of textures references and is
	#unhappy with this little spared size	
	#if not texture_file_name in set(textures_list):
	#	textures_list.append(texture_file_name)
	textures_list.append(texture_file_name)
	#optimisation possible: nombre de clefs complet
	#mais nombre de valeurs optimisé (pointeurs)
	return len(textures_list)

#MODIF2016: new props pointers, TrUberSh.fx implementation, UV scrolling
def add_igs_material(material, Config, textures_list):
	'''Add an igs material description out of a blender material.'''

	material_found = False
	add_face_tag_description = False
	IGmat = material.IgsMat
	#
	#Material Config:
	mShaderName = IGmat.shader_name
	if mShaderName == 'custom' or len(SHADERS_ENUM) == 1: mShaderName = IGmat.shader_name_string
	#
	mNeverOcclude = 0
	mSortPriority = 0
	#            
	mAlphaTestMode = IGmat.alpha_test_mode
	mZBias = int(IGmat.z_bias)
	mZBufferMode = int(IGmat.z_buffer_mode)
	mVisMod = IGmat.vis_mod
	mTwoSided = IGmat.two_sided
	mBackfaceCull = IGmat.back_face_cull	
	#
	mAdditiveAlphaStrength = 0#128
	#
	#MODIFS2016: VF enum AUTO opt:
	mViewFacing = IGF.VF_NONE
	if mShaderName.find('ViewFacing') >= 0:
		if mShaderName.find('Upright') >= 0:
			mViewFacing = IGF.VF_UPRIGHT
		else:
			mViewFacing = IGF.VF_FACING
	if IGmat.view_facing != 'AUTO':
		mViewFacing = IGmat['view_facing']
	
	mAmbient = IGF.IGsColour(*IGmat.ambient_color)
	mDiffuse = IGF.IGsColour(*IGmat.diffuse_color)
	mSpecular = IGF.IGsColour(*IGmat.specular_color)
	mSpecularPower = IGmat.specular_power
	mEmissive = IGF.IGsColour(*IGmat.emissive_color)
	mEmissiveStrength = IGmat.emissive_power
	
	mSurfaceType = b''#NO COLLIDE'
	
	mUseLightGlow = 0
	mUsePulseGlow = 0
	mLightGlowType = b''#HEADLAMP'
	
	IGGlow = IGF.IGPulseGlowCfg(
		mTargCol = IGF.IGsColour(0.78,0.78,1.0,1.0),
		
		mMode = IGF.PG_PULSE,
		mPhase = 0.0,
		mPeriod = 5,
		mAmplitude = 1,
		
		mRptTimeMin = 1.0,
		mRptTimeMax = 5.0,
		mExeTimeMin = 1.0,
		mExeTimeMax = 5.0,
		mActivationTime = 0.0,
		
		mSeqMode = b'',#b'TRAFFIC'
		mVertexModify = 0,
		)
	
	mUnfoggable = 0
	mForce32Bit = 0
	
	mLMCastShadows = 0
	mLMKeepVertexColours = 0
	mLMGenerateShadows = 1
	mLMTexelsPerMetre = 0
	
	mComment = IGmat.comment_field
	mExtraData = IGF.IGDataBlockContainer()
	#MODIFS2016: some toggles...
	if IGmat.use_cast_shadows:
		mLMCastShadows = 1
	if IGmat.preDPP:
		mComment += ' :pre-dpp'
	if IGmat.unlit:
		mLMKeepVertexColours = 1
	#
	#Render Stages:
	IGRenderS = []
	for num_s, s in enumerate(IGmat.textures):
		if num_s == 0:
			# FilterMode, AnimateUVs, NumFrames, FPS
			mFilterMode = int(IGmat.filter_mode)
			mAnimateUVs = IGmat.animate_uv
			mNumFrames = IGmat.num_frames
			mFPS = IGmat.f_p_s
			#
			#UV scrolling:
			mScrollUVs = IGmat.uv_scroll
			mScrollU = IGmat.scroll_u
			mScrollV = IGmat.scroll_v
			
			if mAnimateUVs: #animated textures
				mAdditiveAlphaStrength = 0
				
				mSurfaceType = b''
				mUseLightGlow = 0
				mUsePulseGlow = 0
				mLightGlowType = b''
				IGGlow = IGF.IGPulseGlowCfg()
				
				mUnfoggable = 0
				mForce32Bit = 0
				mAmbient = IGF.IGsColour(0.0,0.0,0.0,0.0)
				mEmissive = IGF.IGsColour(IGmat.emissive_color[0],IGmat.emissive_color[1],IGmat.emissive_color[2],0.0)
				
				mLMGenerateShadows = 0
				mLMTexelsPerMetre = 0
		#
		# Material data for the slot
		rs = IGF.IGRenderStage(
			mTextureName=add_texture_to_list(textures_list, Config, s), #len_texlist saved

			mUVChannelIndex=num_s,
			mFilterMode=mFilterMode,
			mFPS=mFPS,
			
			mAnimateUVs = mAnimateUVs,
			mNumFrames = mNumFrames,
			
			mScrollUVs=mScrollUVs,
			mScrollU=mScrollU,
			mScrollV=mScrollV
			)
		if num_s == 0:
			rs.mMipLODBias = IGmat.mip_lod_bias
			#
			args = (IGmat.uv_param_1, IGmat.uv_param_2, IGmat.uv_param_3, IGmat.uv_param_4, IGmat.uv_param_5, IGmat.uv_param_6)
			
			rs.mArguments = args
		#
		elif num_s == 1:
			if mShaderName.find('BumpSpecEnv') >= 0:
				rs.mMipLODBias = -1.0
			#else: default setting:
			#	rs.mMipLODBias = 0.0
		#elif ('WeatherEffects' in mShaderName) and num_s == 3: default setting:
		#	rs.mMipLODBias = 0.0
		#elif num_s > 1: default setting:
		#	rs.mMipLODBias = 0.0
			
		#if num_s != 0: default setting:
		#	rs.mArguments = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
			
		if mFPS == 0:
			# Use model setting
			rs.mFPS = int(Config.context.scene.render.fps / Config.context.scene.render.fps_base)
		#else: FPS was set in configuration file
		
		IGRenderS.append(rs)
		#
		if ('WeatherEffects' in mShaderName) and (num_s == 1):
			IGRenderS.append(IGF.IGRenderStage(
				mTextureName=add_texture_to_list(textures_list, Config, s),
				mFilterMode=3,
				mMipLODBias=-1.0,
				mFPS=int(Config.context.scene.render.fps / Config.context.scene.render.fps_base)
			))
			#print(" >>> mNumRenderStages 2 {:d}".format(mNumRenderStages))
		#MODIF2016: support for TrainUberShader.fx
		elif mShaderName == "TrainUberShader.fx":
			mSurfaceType = b'METAL'
			mUseLightGlow = 1
		#MODIF2023: support for addATex mipmaps and stuff from a 3DS file from AP
		elif mShaderName == "TrainGlass.fx":
			mSurfaceType = b'GLASS'
		#
		material_found = True
		#
	if not material_found:
		textures_list.append("")
		IGRenderS.append(IGF.IGRenderStage(
			mTextureName=len(textures_list) 
			))

	new_material = IGF.IGMaterials(material.name.encode(), mShaderName.encode(), len(IGRenderS), \
	IGRenderS, \
	mNeverOcclude, mSortPriority, mZBias, mAlphaTestMode, mAdditiveAlphaStrength, mZBufferMode, \
	mBackfaceCull, mTwoSided, mViewFacing, mVisMod, mSurfaceType, mUseLightGlow, mUsePulseGlow, mLightGlowType, \
	IGGlow, \
	mUnfoggable, mForce32Bit, mAmbient, mDiffuse, mEmissive, \
	mEmissiveStrength, mSpecular, mSpecularPower, mLMCastShadows, mLMGenerateShadows, mLMKeepVertexColours, mLMTexelsPerMetre, mComment.encode(), mExtraData)

	return new_material, len(IGRenderS), add_face_tag_description

def create_materials_igs(Config, IGctn):
	'''Export all materials and make them easily accessible from geometry'''
	
	#sort set into list to put test_mat forward. needed to compute faces and verts
	#efficiently later
	if Config.u_test_mode:
		test_mat = bpy.data.materials[Config.u_test_mat]  # @UndefinedVariable
		if test_mat in IGctn.mat_data_index:
			IGctn.mat_data_index = [test_mat]+[m for m in IGctn.mat_data_index if m != test_mat]
	
	#export materials
	for mat in IGctn.mat_data_index:
		material_IGMaterials, nb_slots, add_face_tag_description_mat = add_igs_material(mat, Config, IGctn.textures_list)
		
		IGctn.add_face_tag_description = add_face_tag_description_mat or IGctn.add_face_tag_description
		
		#build helpers for storage and fast matching respectively 
		IGctn.materials_list.append([material_IGMaterials, nb_slots])
		IGctn.materials_sdict[mat.name] = len(IGctn.materials_list) - 1
	
	IGctn.materials_count = len(IGctn.mat_data_index)


#======================================GEOMETRY

def update_bounding_box(Vmin_bounding_box, Vmax_bounding_box, new_vector):

	m = Vmin_bounding_box
	M = Vmax_bounding_box

	m.x = min(m.x, new_vector.x)
	m.y = min(m.x, new_vector.y)
	m.z = min(m.x, new_vector.z)
	
	M.x = max(M.x, new_vector.x)
	M.y = max(M.x, new_vector.y)
	M.z = max(M.x, new_vector.z)


def getMaterialFromFace(bm, eval_mesh, face, u_test_mode, materials_list, materials_sdict, mat_data_index):
	
	data_mat_available = len(eval_mesh.materials) > 0
	uv_unavailable = len(eval_mesh.uv_layers) == 0
	uv_layers = bm.loops.layers.uv
	
	mat_index = 0 #u-test-mat here!!
	if (not u_test_mode) or data_mat_available :
		if u_test_mode and data_mat_available:
			#the materials may have been incompatible and hence suppressed. watch out and do this:
			mat_name = eval_mesh.materials[face.material_index].name
			if mat_name in materials_sdict:
				mat_index = materials_sdict[mat_name]
				
		else:
			mat_index = materials_sdict[eval_mesh.materials[face.material_index].name] 
				
	#IGmat = materials_list[mat_index][0]
	BLmat = mat_data_index[mat_index]
	f_mat_nb_slots = materials_list[mat_index][1]
	#print(" >>>> f_mat_nb_slots {:d} f_mat.name {:s} face.material_index {:d} ".format(f_mat_nb_slots, f_mat_name, face.material_index))
	
	mat_igs_offset = IGF.HEADER_SIZE + mat_index * IGF.MATERIAL_SIZE
	
	# In a given mesh, a slot may have a specific UV mapping (MAJ_1_4_0)
	f_uv_list = []
	active_uv_layer = uv_layers.active #texture_1
	
	if u_test_mode and uv_unavailable:
		f_uv_list = [active_uv_layer for i in range(f_mat_nb_slots)]
		
	else:
		#print(" >>> UVMaps for obj {}; face n°{}".format(obj.name, face_num))
		for tex_slot in BLmat.IgsMat.textures:
			#print("IMAGE found")
			if (tex_slot.uv_layer in uv_layers): #name found in UVmaps list
				f_uv_list.append(uv_layers[tex_slot.uv_layer])
				#print(" >>> added {}".format(tex_slot.uv_layer))
				
			else: # name == "" or name == invalid
				f_uv_list.append(active_uv_layer)
				#print(" >>> added {}".format(data.tessface_uv_textures[0].name))
		
		if b"WeatherEffects" in materials_list[mat_index][0].mShaderName:
			# name == "" or name == invalid
			f_uv_list.append(active_uv_layer)
			#print(" >>> added {} for WeatherEffects".format(data.tessface_uv_textures[0].name))
		
		if not len(BLmat.IgsMat.textures):
			#for Invisible shaders and stuff like this
			f_uv_list.append(active_uv_layer)
			
		assert (f_mat_nb_slots == len(f_uv_list)), f"{eval_mesh.materials[face.material_index].name}: Slots and UVmaps number do not match: {f_mat_nb_slots} | {len(f_uv_list)}"
	
	return materials_list[mat_index][0], mat_igs_offset, f_uv_list

#MODIF2016: Vertex color, Bone Binding, is_skinned adapt
def process_mesh_geometry(
		Config,
		IGctn,
		obj,
		first_obj_matrix,
        g_transform,
		Vmin_bounding_box, 
		Vmax_bounding_box, 
		object_triangles_list, 
		object_vertices_list, 
		vertices_count, 
		vertices_count_start, 
		triangles_count,
		object_vertices_params_list,
		remote_is_skinned
		):
	
	bones_list = IGctn.bones_list
	materials_list = IGctn.materials_list
	materials_sdict = IGctn.materials_sdict
	mat_data_index = IGctn.mat_data_index
	mExtraData = IGctn.mExtraData
			
	if not obj.is_evaluated:
		obj = obj.evaluated_get(Config.dpg)
	bm = bmesh.new()
	mesh = obj.to_mesh(preserve_all_data_layers=True, depsgraph=Config.dpg)
	
	#mesh.corner_normals() #06/2024: must be removed for Blender 4.1+
	bm.from_mesh(mesh) # Create a BMesh datablock with modifiers applied
	#print(" >>> preview", obj.name)
	
	#MODIFS2016: is blender parent an armature?
	is_skinned = False
	if Config.process_bones and len(obj.vertex_groups) != 0:
		for mod in obj.modifiers:
			if mod.type == 'ARMATURE' and mod.use_vertex_groups:
				is_skinned = True
				break
	
	#associate available vertex groups with offsets exported earlier for data-matching with bone bindings of verts:
	if is_skinned or remote_is_skinned:
		all_bones_names = {bone.mName : i for i, bone in enumerate(bones_list)}
		if is_skinned:
			all_group_indices = {vGroup.index : all_bones_names[vGroup.name.encode()] for vGroup in obj.vertex_groups if vGroup.name.encode() in all_bones_names}
		
		MAX_EXPORTED_BONES = IGF.MAX_EXPORTED_BONES if PROFILE_MODE else 4 #it supports up to 8 in IGS but if there are more than 4, vertices are distorted in game...
		gVertexWeightThreshold = IGF.gVertexWeldNormalThreshold
	
	bm.verts.ensure_lookup_table()
	bm.edges.ensure_lookup_table()
	bm.faces.ensure_lookup_table()
	
	#generate smooth-groups
	bm.faces.layers.int.new('smooth-group')
	smthgp_key = bm.faces.layers.int['smooth-group']
	
	#assign smooth groups to faces:
	poly_gp, nb_gp = mesh.calc_smooth_groups(use_bitflags=True)  # @UnusedVariable
	for f, smg in zip(bm.faces, poly_gp):
		f[smthgp_key] = smg
	
	vg_key = bm.verts.layers.deform.verify()
	#for k, v in bm.loops.layers.color.items():
	#	print("vcol names :", repr(k), repr(v))
		
	vc_key = bm.loops.layers.color.verify()
	
	uv_layers = bm.loops.layers.uv
	uv_layers.verify()
	
	# Change of coordinates system
	common_transform = TS_MATRIX @ \
        first_obj_matrix.inverted() @ \
        g_transform @ obj.matrix_world

	for tri in bm.calc_loop_triangles():
		triangle_vertices_indices_list = []
		
		face = tri[0].face
		
		#Normals
		face_normal_rot = common_transform @ face.normal
		face_normal = IGF.IGsVector4(*face_normal_rot, 1.0)
		
		#determine used material for this face
		IG_mat, mat_igs_offset, f_uv_list = getMaterialFromFace(bm, mesh, face, Config.u_test_mode, materials_list, materials_sdict, mat_data_index)

			
		for vert_num in range(0,3):
			cur_loop = tri[vert_num]
			
			#vertex colours 2020
			new_colour = IGF.IGsColour(*cur_loop[vc_key])
				
			# convert local object coordinates -> world - > local coordinates of first object -> axis change
			local_vertex = common_transform @ cur_loop.vert.co
			
			#2020 get normals with autosmooth or split normals or edge sharp
			new_normal_rot = common_transform @ mesh.loops[cur_loop.index].normal
			#del local_split_normal
				
			# Update bounding box in world coordinates
			update_bounding_box(Vmin_bounding_box, Vmax_bounding_box, local_vertex)
			
			#get UVs used
			new_UV0 = tuple(IGF.IGsUV(cur_loop[i_uv_key].uv[0], 1 - cur_loop[i_uv_key].uv[1]) for i_uv_key in f_uv_list)
# 			# if u_test_mode and not data.tessface_uv_textures:
# 			# pad with zero or stuff, nobody cares about zeroes!
# 			if uv_unavailable:
# 				new_UV0 = tuple(
# 					IGF.IGsUV(
# 						(1 if vert_num >= 2 else 0), 
# 						(1 if ((0 < vert_num <= 2) and (vert_num != 0)) else 0) )
# 					for i in range(nb_uvMaps))
# 				#gives:
# 				# v0 --> (0,0)
# 				# v1 --> (0,1)
# 				# v2 --> (1,1)
# 				# v3 --> (1,0)
			
			#MODIFS2016: export vertex bindings and weights:
			vertex_bone_binding = []
			if is_skinned:
				#compute values which must add up to 1.0 (using mean)
				bl_v_weights = [v_wgt for v_wgt in cur_loop.vert[vg_key].items()] if PROFILE_MODE else [v_wgt for v_wgt in cur_loop.vert[vg_key].items() if v_wgt[1] > 0.0]
				total_bl_v_wgt = sum(w for _ , w in bl_v_weights)
				
				if len(bl_v_weights) == 1:
					#only one bone put 0.0 as MAX does
					if bl_v_weights[0][0] in all_group_indices:
						vertex_bone_binding.append(IGF.IGVertexBoneBinding(all_group_indices[bl_v_weights[0][0]], 1.0)) #weights always adds up to 1.0
				else:
					#sort out too small bone influences
					adjusted_vert_weights = not PROFILE_MODE
					while not adjusted_vert_weights:
						
						adjusted_vert_weights = True #put to False if a non matching elem is found
						
						for idx, (v_g_idx, v_wgt) in enumerate(bl_v_weights):							
							if ((v_wgt / total_bl_v_wgt) < gVertexWeightThreshold) or (v_g_idx not in all_group_indices): #pass bones with not enough influence on export
								
								total_bl_v_wgt -= v_wgt #take them away from calcs
								del bl_v_weights[idx]
								
								adjusted_vert_weights = False
								break
							
					#trim at max bones
					if not PROFILE_MODE:
						bl_v_weights.sort(key=lambda weight_tuple: weight_tuple[1], reverse=True)
					bl_v_weights = bl_v_weights[:MAX_EXPORTED_BONES]
				
					#look for our bones in our pre-sorted list all_group_names giving bone indices
					for v_g_idx, v_wgt in bl_v_weights:
						#if v_g_idx in all_group_indices:
							#print(bone_name, "found")
						vertex_bone_binding.append(IGF.IGVertexBoneBinding(all_group_indices[v_g_idx], v_wgt / total_bl_v_wgt)) #weights always adds up to 1.0
						#else: #we didn't found something
						#	bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='WARNING', 
						#		message=" VertexBoneBinding processing error: cannot find bone: '{}'".format(obj.vertex_groups[v_g_idx].name))
							#return
						
				if not len(vertex_bone_binding):
					vertex_bone_binding.append(IGF.IGVertexBoneBinding(all_group_indices[0], 1.0)) #this should be a root bone
					
			elif remote_is_skinned: #enters here if not skinned in Blender only
				vertex_bone_binding.append(IGF.IGVertexBoneBinding(0, 0.0))
				#this should be a root bone. anyway, this kind of merge should not happen...
					
			#weld vertices together if possible for performances in TS
			new_vertex = None
			vertex_index = -1
			f_lv = local_vertex.freeze()
			
			looking_for_this = IGF.IGVertex(
				IGF.IGsVector4(*local_vertex, 1.0), 
				IGF.IGsVector4(*new_normal_rot,1.0), 
				len(f_uv_list), 
				new_UV0, 
				new_colour, 
				mat_igs_offset,
				len(vertex_bone_binding),
				vertex_bone_binding,
				0,
				mExtraData)
			
			if (f_lv, len(f_uv_list), mat_igs_offset) in object_vertices_params_list:
				vertex_index_set = object_vertices_params_list[f_lv, len(f_uv_list), mat_igs_offset]

				for vi in vertex_index_set:
					if object_vertices_list[vi] == looking_for_this:
						vertex_index, new_vertex = vi, object_vertices_list[vi]
						del looking_for_this
						break
				
			else:
				#used for fast matching vertices
				object_vertices_params_list[f_lv, len(f_uv_list), mat_igs_offset] = set()
				#assures there is a set to receive our future vertex
				
			if new_vertex:
				triangle_vertices_indices_list.append(vertex_index)
				#print(' >>>??? vertex_index ', vertex_index)
			else:  # None
				new_vertex = looking_for_this
				
				object_vertices_list.append(new_vertex)
				object_vertices_params_list[f_lv, len(f_uv_list), mat_igs_offset].add(len(object_vertices_list)-1)
				
				triangle_vertices_indices_list.append(vertices_count)
				vertices_count += 1
			#triangle_vertices_list.append(new_vertex)
			
		
		#MODIFS2020: hide edge if it is in the middle of the face (triangle breaks continuity of loops)
		hidden_edge = 0
		if tri[0].link_loop_next != tri[1]: 
			hidden_edge += IGF.EDGE_V0_V1_HIDDEN
		if tri[1].link_loop_next != tri[2]: 
			hidden_edge += IGF.EDGE_V1_V2_HIDDEN
		if tri[2].link_loop_next != tri[0]: 
			hidden_edge += IGF.EDGE_V2_V3_HIDDEN
			
		if IG_mat.mViewFacing > IGF.VF_NONE:
			hidden_edge = 0
		
		# mVertices, mNormal, mHiddenEdges, mMaterial, mSMGroup, mTagId, mExtraData, vertices_list
		# Fill mVertices with vertex index before future update to offset value for the final igs file.
		
		new_triangle = IGF.IGTriangle(
			triangle_vertices_indices_list, 
			face_normal, 
			hidden_edge, 
			mat_igs_offset, 
			face[smthgp_key], 
			0, 
			mExtraData, 
			vertices_count_start
			) # MAJ
		
		object_triangles_list.append(new_triangle)
		triangles_count += 1

	bm.free()
	obj.to_mesh_clear()
		
	return END_OK, (is_skinned or remote_is_skinned), vertices_count, triangles_count, Vmin_bounding_box, Vmax_bounding_box

def process_mesh_group(Config, skinned_igs, IGctn, grp):
		
	local_transform_matrix = (IGctn.global_transform_matrix if grp.LODlevel == 1 else Matrix())

	scale_m = Matrix() #nullify scale
	first_obj_matrix = local_transform_matrix @ grp.objects_list[0].matrix_world
	
	scale_m[0][0], scale_m[1][1], scale_m[2][2] = grp.objects_list[0].scale
	first_obj_matrix @= scale_m.to_4x4().inverted()
		
	Vmin_bounding_box = VNULL3D.copy()
	Vmax_bounding_box = VNULL3D.copy()
	object_triangles_count = 0
	object_triangles_list = [] # At group level = at igs mesh level
	grp_vertices_count = 0
	triangles_count_start = IGctn.triangles_count # At group level
	vertices_count_start = IGctn.vertices_count # At group level
	object_vertices_count_start = IGctn.vertices_count # At object level
	is_skinned = skinned_igs #we register it here to avoid zero bone error in TS when we merge objects
	
	for obj in grp.objects_list:
		# Process objects
		object_vertices_count = 0
		object_vertices_list = [] # At object level
		object_vertices_params_list = dict() # used to find vertices quickly
		
		return_code,  \
		is_skinned,  \
		object_vertices_count, \
		object_triangles_count,  \
		Vmin_bounding_box, Vmax_bounding_box, \
		= process_mesh_geometry(
			Config,
			IGctn,
			obj,
			first_obj_matrix,
            local_transform_matrix,
			Vmin_bounding_box,
			Vmax_bounding_box,
			object_triangles_list,
			object_vertices_list,
			object_vertices_count,
			object_vertices_count_start,
			object_triangles_count,
			object_vertices_params_list, skinned_igs)
	
		if (return_code != END_OK) or (object_vertices_count == 0):
				# return_code == END_ERROR: #if there is no verts, its an error for TS anyway
				raise RuntimeError("IGSE: invalid geometry conversion for object (or dupli) {:s}!".format(obj.name)) from None

		object_vertices_count_start += object_vertices_count # At object level
		IGctn.vertices_list.extend(object_vertices_list) # At object level
		
		grp_vertices_count += object_vertices_count
		#
		#pgr_bar += pgr_b3
		#wm.progress_update(pgr_bar)
		#
	IGctn.triangles_list.extend(object_triangles_list)  # At group level
	IGctn.vertices_count = IGctn.vertices_count + grp_vertices_count
	#
	# Create mesh related items
	new_IGMesh, new_geomLOD, new_instance = create_mesh_igs(grp, first_obj_matrix, IGctn.current_id, is_skinned, grp_vertices_count, object_triangles_count, \
	triangles_count_start, vertices_count_start, Vmin_bounding_box, Vmax_bounding_box, IGctn.mExtraData)
	if new_instance is None:
		raise RuntimeError("IGSE: invalid geometry encoding!") from None
	
	grp.IGinstance_id = int(IGctn.current_id)
	IGctn.current_id += 1
	if grp_vertices_count: # Mesh
		IGctn.meshes_count += 1
		IGctn.meshes_list.append(new_IGMesh)
		IGctn.meshesLODs_list.append(new_geomLOD)
		IGctn.triangles_count += object_triangles_count
	IGctn.instances_list.append(new_instance)
	
def create_mesh_igs(
	grp, 
	matrix, 
	current_id, 
	is_skinned, 
	vertices_count, 
	triangles_count, 
	triangles_count_start, 
	vertices_count_start,
	Vmin_bounding_box, 
	Vmax_bounding_box, 
	mExtraData): #MODIFS2016: is_skinned adapt
#MODIF2016: err handling implem
# error struct ref: bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message="")
	children_count = len(grp.child_groups_list)
	if children_count > IGF.MAX_CHILDREN:
		bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR', message=" more than {:d} children (max children) for object {:s} (check groups list above)".format(IGF.MAX_CHILDREN, grp.name))  # @UndefinedVariable
		return None, None, None
	
	if vertices_count == 0: # Empty alone in a group (should not occur as empty's are dropped when scanning the model to build groups)
		new_IGMesh, new_geomLOD = None, None
		mNumLODs = 0
		mGeometry = 0
	else: # Mesh
		# Update bounding box in world coordinates to avoid disappearing object when near camera
		update_bounding_box(Vmin_bounding_box, Vmax_bounding_box, matrix.to_translation())
		
		MyPointMin = IGF.IGsVector4(Vmin_bounding_box.x, Vmin_bounding_box.y, Vmin_bounding_box.z, 1.0)
		MyPointMax = IGF.IGsVector4(Vmax_bounding_box.x, Vmax_bounding_box.y, Vmax_bounding_box.z, 1.0)
		bounding_box = IGF.IGsBoundingBox(MyPointMin, MyPointMax)
		
		# mIsSkinned, mNumVertices, mVertices, mNumTriangles, mTriangles, mBoundingBox, mExtraData
		new_IGMesh = IGF.IGGeom(is_skinned, 
							vertices_count, vertices_count_start, 
							triangles_count, triangles_count_start, 
							bounding_box, 
							mExtraData)
		
		# VisibleDistance, pGeometry, mExtraData
		new_geomLOD = IGF.IGGeometryLOD(grp.LODdist, current_id, mExtraData)
		
		mNumLODs = 1
		mGeometry = current_id
	if grp.parent_group:
		matrix_w = grp.parent_group.objects_list[0].matrix_world.inverted() @ grp.objects_list[0].matrix_world
	else:
		matrix_w = matrix
	myMatrix  = IGF.IGsMatrix4x4.new_to_TS_screenspace(matrix_w)
	myMatrix2 = IGF.IGsMatrix4x4.new_to_TS_screenspace(matrix_w) #used as initial TM to resolve parenting later on export
	
	# mName, mNameUID, mNumLODs, mGeometry, mTM, mParent, mNumChildren, mChildren, ExtraData, parent_group, child_groups_list
	new_instance = IGF.IGInstance(grp.name.encode(), current_id, mNumLODs, mGeometry, myMatrix, 0, children_count, [], \
	mExtraData, myMatrix2, grp.parent_group, grp.child_groups_list)
	grp.IGinstance = new_instance
	
	return new_IGMesh, new_geomLOD, new_instance


#======================================ARMATURES

def create_bones_igs(IGctn, armat): #MODIFS2016: Bones
	
	def create_a_bone(current_bone, root_mtrx=Matrix.Identity(4)):
		b_name = current_bone.name
		b_uid = IGctn.bones_count + 1 #bones_count is used as UID
		
		matrix = root_mtrx @ current_bone.matrix_local
		b_TM = IGF.IGsMatrix4x4.new_to_TS_screenspace(matrix)
		
		try: 
			b_parent = current_bone.parent.name.encode()
		except AttributeError: 
			b_parent = None
	
		b_children = []
		for b_child in current_bone.children: #register children
			b_children.append(b_child.name.encode())
		
		new_bone = IGF.IGBone(b_name.encode(), b_uid, b_TM, b_parent, b_children, IGctn.mExtraData)
		
		return new_bone
	
	bak_pose_position = armat.data.pose_position
	armat.data.pose_position = 'REST'
	b_error = False
	for i, bone in enumerate(armat.data.bones):
		if bone.parent is None:
			rt_mtrx = IGctn.global_transform_matrix @ armat.matrix_world
			new_bone = create_a_bone(bone, rt_mtrx)
		else:
			rt_mtrx = bone.parent.matrix_local.inverted()
			new_bone = create_a_bone(bone, rt_mtrx)
		IGctn.bones_list.append(new_bone)
		IGctn.bones_count += 1
		
	#end creation, now link parents
	else:
		armat.data.pose_position = bak_pose_position #restore previous armature state
		#update relationship names to offsets:
		for bone in IGctn.bones_list[:]:
			#update parent:
			if bone.mParent:
				mPBoneName = bone.mParent
				for num_bone, bone2 in enumerate(IGctn.bones_list):
					if bone2.mName == mPBoneName:
						bone.mParent = num_bone + 1 #Else it's impossible to know if there is no parent or parent is first of list
						break
				else:
					bpy.ops.igs_err.damned('EXEC_DEFAULT', type='WARNING', message=" Bone parent not found. Bone '{0}' looking for '{1}'".format(bone.mName.decode(), bone.mParent))  # @UndefinedVariable
					b_error = True
			#update children:
			if bone.mChildren:
				for j, b_child in enumerate(bone.mChildren[:]):
					mCBoneName = b_child
					for num_bone, bone2 in enumerate(IGctn.bones_list):
						if bone2.mName == mCBoneName:
							bone.mChildren[j] = num_bone
							break
					else:
						bpy.ops.igs_err.damned('EXEC_DEFAULT', type='WARNING', message=" Bone child not found. Bone '{0}' looking for '{1}'".format(bone.mName.decode(), mCBoneName))  # @UndefinedVariable
						b_error = True
		if b_error:
			#error safety
			bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR', message=" Bone offset processing error. See log")  # @UndefinedVariable
			return None, None
		return
	#error safety
	armat.data.pose_position = bak_pose_position #restore previous armature state
	bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR', message=" Unknown error with bones generation happened!!")  # @UndefinedVariable
	return

	
#======================================SNAP POINTS

def create_snapp_igs(IGctn, grp): #MODIFS2016: Snap points
	obj = grp.objects_list[0]
	
	if obj.empty_display_type == 'ARROWS' and len(obj.children) == 0:
		name_split = grp.name.split('_')
		if ('#s' in name_split[0]) and (len(name_split[0]) == 3):
			if len(obj.name) > IGF.MAX_OBJECT_NAME:
				s_name = grp.name[:IGF.MAX_OBJECT_NAME]
				bpy.ops.igs_err.damned('EXEC_DEFAULT',type='WARNING', message=" Snap Point '{:s}' processed using a truncated name at {:d} characters: '{:s}' (to comply with naming rule).".format(grp.name, MAX_NAME_WITH_LOD, s_name))  # @UndefinedVariable
			else:
				s_name = grp.name
				
			s_name = s_name[1:] #stripping "#"
			
			matrix = IGctn.global_transform_matrix @ obj.matrix_world
			s_TM = IGF.IGsMatrix4x4.new_to_TS_screenspace(matrix)
			
			s_BoundingBox = IGF.IGsBoundingBox()
			
			s_Parent = 0
			if obj.parent:
				for i, instance in enumerate(IGctn.instances_list):
					if instance.mName.decode() == obj.parent.name:
						s_Parent = i + 1
			
			s_Data = IGF.IGGenericSceneData()
			new_snap_point = IGF.IGGenericSceneItem(s_name.encode(), IGctn.gscitems_count, s_TM, s_BoundingBox, s_Parent, s_Data)
			
			IGctn.gscitems_list.append(new_snap_point)
			IGctn.gscitems_count += 1
			bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message=" '{0}' computed as snap point: '{1}'".format(obj.name, s_name))  # @UndefinedVariable
			

#====================================================================EXPORT
#MODIFS2016: progress bar implementation, is_skinned adapt, bone adapt

class IGArrays():
	"""Container for IGS offsets and lists
	for easier transformations"""
	
	def __init__(self):
		self.global_transform_matrix = Matrix()
		
		self.materials_list = []
		self.materials_sdict = dict()
		self.mat_data_index = None
		
		self.meshes_list = []
		self.meshesLODs_list = []
		self.instances_list = []
		self.triangles_list = []
		self.vertices_list = []
		self.textures_list = []
		self.lights_list = []
		self.splines_list = []
		self.bones_list = []
		self.gscitems_list = []
		
		self.add_face_tag_description = False
		#
		self.current_id = 0
		self.triangles_count = 0
		self.vertices_count = 0
		self.meshes_count = 0
		self.materials_count = 0
		self.bones_count = 0
		self.gscitems_count = 0
		
		self.mExtraData = IGF.IGDataBlockContainer()

def ExportIGS(Config, pgrh):
	""" Bl_data.IGSExporterSettings(bpy.types.PropertyGroup) * context.window_manager
	-> str or NoneType
	wrapper for the real exporter, protects users scenes  """
	
	if PROFILE_MODE:
		import cProfile, pstats, io
		pr = cProfile.Profile()
		s = io.StringIO()
		pr.enable()
	
	
	pgrh.update(0, "Cleaning Scene...")
	wrapper = CleanAndProperSceneExport(Config)
	with wrapper as objects_list:
		if not objects_list:
			raise RuntimeError("BRIAGE: Empty object list! check Blender console or log file") from None
		
		export_errors = _internal_ExportIGS(wrapper.Config, pgrh, objects_list)
		
	if PROFILE_MODE:
		pr.disable()
		sortby = 'tottime'
		pstats.Stats(pr, stream=s).sort_stats(sortby).print_stats(20)
		sortby = 'cumtime'
		pstats.Stats(pr, stream=s).sort_stats(sortby).print_stats(20)
		#print(s.getvalue())
		try:
			with open("ExportIGS.log", "w") as f:
				f.write(s.getvalue())
			print( os.path.abspath("ExportIGS.log") )
		except:
			print("BRIAGE: Cannot print profile log, turn off Profiling mode")
			
	return export_errors or None

def _internal_ExportIGS(Config, pgrh, objects_list):
# error struct ref: bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message="")
	# Current  model directory name
	model_directory = os.path.dirname(bpy.path.abspath(Config.FilePath))  # @UndefinedVariable
	# Current model file name
	model_name = os.path.basename(Config.FilePath)
	# Name without suffix
	filename_strip = os.path.splitext(model_name)[0]
	#
	IGctn = IGArrays()
	#
	pgrh.update(5, "Resolving materials and checking consistency...")
	#
	#
	#Check scene for errors
	IGctn.mat_data_index = checkScene(Config, objects_list)
# 	if PROFILE_MODE:
# 		print("--> " + str(IGctn.mat_data_index))
	if not IGctn.mat_data_index: 
		# print("IGSE: empty id material list!")
		return
	#bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message=" The scene is clean and ready for export")  # @UndefinedVariable
	#
	#Center Main Object
	IGctn.global_transform_matrix = center_main_object(Config, objects_list)
	
	pgrh.update(15, "Generating groups...")
	#
	#print(" Main object selected = {:s}".format(main_obj.name))
	bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message=" Generating groups...")  # @UndefinedVariable
	#
	# Sort objects in groups
	groups_list = make_groups(Config, objects_list)
	
	#LODerror = False
	#for gp in groups_list:
	#	LODerror = _checkLOD(Config, gp, objects_list) #useless because already done
	#if LODerror:
	#	return
	#
	pgrh.update(25, "Converting bones & armatures...")
	#
	#'''-----------------------------------------------'''
	#'''Save the sorted Blender scene into igs objects.'''
	#'''-----------------------------------------------'''
	#
	#
	add_face_tag_description = False
	#
	bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message=" Converting bones & armatures...")  # @UndefinedVariable
	#sort armatures out and process bones:
	skinned_igs = False
	if Config.process_bones:
		for armature in [obj for obj in objects_list if obj.type == 'ARMATURE']:
			if Config.Verbose or PROFILE_MODE:
				bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message="   +> "+armature.name)  # @UndefinedVariable
			create_bones_igs(IGctn, armat=armature)
			skinned_igs = True
	#
	pgr_bar = 30
	try: pgr_b2 = abs(40 / len(groups_list))
	except: pgr_b2 = 1
	#
	bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message=" Converting Materials...")  # @UndefinedVariable
	#Process materials
	create_materials_igs(Config, IGctn)
	#
	bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message=" Converting Meshes and items...")  # @UndefinedVariable
	
	for grp in groups_list:
		#if Config.Verbose or PROFILE_MODE:
		#	bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message="   +> "+grp.name)
			
		assert grp.type_o in {'MSH', 'SPT'} , "IGSE: Invalid group, see previous error(s) in Blender Console"
		
		if grp.type_o == 'MSH':
			#2022: remove non-mesh children from stack
			grp.child_groups_list = list( filter( lambda g: g.type_o == 'MSH', grp.child_groups_list) )
			#process instance, mesh and meshLOD
			process_mesh_group(Config, skinned_igs, IGctn, grp)
		
		elif grp.type_o == 'SPT':
			#process snap points:
			create_snapp_igs(IGctn, grp)
		#
		pgr_bar += pgr_b2
		pgrh.update(pgr_bar, grp.name)
	#
	assert IGctn.materials_count > 0 , "IGSE: No material found: Export stopped, see previous error(s) in Blender Console"
	assert IGctn.vertices_count > 0 , "IGSE: No vertex found: Export stopped, see previous error(s) in Blender Console"
	assert IGctn.triangles_count > 0 , "IGSE: No triangle found: Export stopped, see previous error(s) in Blender Console"
	assert IGctn.meshes_count > 0 , "IGSE: No mesh found: Export stopped, see previous error(s) in Blender Console"
	#
	#
	pgr_bar = 70
	pgrh.update(pgr_bar, "Generating header and offsets...")
	#
	# Update data to deal with actual offsets in the future IGS file
	datablocks_count = 1
	if add_face_tag_description:
		datablocks_count = 2
	#
	objects_count = IGctn.meshes_count
	start_materials_offset = IGF.HEADER_SIZE 
	start_vertices_offset = IGF.HEADER_SIZE + IGctn.materials_count * IGF.MATERIAL_SIZE 
	start_triangles_offset = start_vertices_offset + IGctn.vertices_count * IGF.VERTEX_SIZE 
	start_geom_offset = start_triangles_offset + IGctn.triangles_count * IGF.TRIANGLE_SIZE 
	start_geomLOD_offset = start_geom_offset + IGctn.meshes_count * IGF.GEOM_SIZE 
	start_instance_offset = start_geomLOD_offset + IGctn.meshes_count * IGF.GEOMLOD_SIZE 
	start_bones_offset = start_instance_offset + IGctn.meshes_count * IGF.INSTANCE_SIZE #MODIFS2016: bones
	start_gscitems_offset = start_bones_offset + IGctn.bones_count * IGF.BONE_SIZE #MODIFS2016: gscitems
	start_datablocks_offset = start_gscitems_offset + IGctn.gscitems_count * IGF.GSCITEMS_SIZE
	
	if IGctn.bones_count == 0: start_bones_offset = 0
	if IGctn.gscitems_count == 0: start_gscitems_offset = 0
	if datablocks_count == 0: start_datablocks_offset = 0
	#
	if add_face_tag_description:
		#face_tag_description_start = start_datablocks_offset + (datablocks_count * IGF.DATABLOCK_SIZE)
		#absolute_texture_name_start = face_tag_description_start + IGF.MAX_FACE_TAG_DESCS * IGF.MAX_OBJECT_NAME
		start_face_tag_description_offset = datablocks_count * IGF.DATABLOCK_SIZE # Relative to start of datablocks
		start_texturenames_offset = (datablocks_count * IGF.DATABLOCK_SIZE) + (IGF.MAX_FACE_TAG_DESCS * IGF.MAX_OBJECT_NAME) # start_texturenames_offset is relative to start of datablocks
	else:
		#absolute_texture_name_start = start_datablocks_offset + (datablocks_count * IGF.DATABLOCK_SIZE)
		start_texturenames_offset = datablocks_count * IGF.DATABLOCK_SIZE # start_texturenames_offset is relative to start of datablocks
	#
	bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message=" Converting textures...")  # @UndefinedVariable
	# Texture file names
	texture_names = IGF.IGTextureNames(IGctn.textures_list)
	#
	if add_face_tag_description:
		# mName, mID, mData, mSize / UniqueID = 1
		face_tag_description_data_block = IGF.IGDataBlock(b'Face tag descriptions', IGF.BLOCK_FACE_TAG_DESCS, start_face_tag_description_offset, 0)
		list_of_tags = [b'IG_TAG_NONE', \
		b'IG_TAG_HEAD' , b'IG_TAG_HEAD_STUMP' , b'IG_TAG_HEAD_STUMP_REPL' , \
		b'IG_TAG_ARM_L', b'IG_TAG_ARM_L_STUMP', b'IG_TAG_ARM_L_STUMP_REPL', \
		b'IG_TAG_ARM_R', b'IG_TAG_ARM_R_STUMP', b'IG_TAG_ARM_R_STUMP_REPL', \
		b'IG_TAG_LEG_L', b'IG_TAG_LEG_L_STUMP', b'IG_TAG_LEG_L_STUMP_REPL', \
		b'IG_TAG_LEG_R', b'IG_TAG_LEG_R_STUMP', b'IG_TAG_LEG_R_STUMP_REPL']
		face_tag_description = IGF.IGFaceTagDescription(list_of_tags)
	#
	# mName, mID, mData, mSize / UniqueID = 2
	textures_data_block = IGF.IGDataBlock(b'Texture name table', IGF.BLOCK_TEXTURE_NAMES, start_texturenames_offset, 0)
	#
	bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message=" Writing header...")  # @UndefinedVariable
	# Initialize Header structure
	#MODIFS2016: object color from main object:
	IGobject_color = IGF.IGsColour(objects_list[0].color[0],objects_list[0].color[1],objects_list[0].color[2],objects_list[0].color[3]) #MODIFS2016: object color = main obj color
	blender_version = ".".join(str(i) for i in bpy.app.version)  # @UndefinedVariable
	exporter_version = IGSE_VERSION
	IGDescriptor = b"SHAPE"
	myComment = ('Blender ' + blender_version + ' - ' + exporter_version)
	myHeader = IGF.IGHeader(IGDescriptor,
		myComment[:IGF.MAX_HEADER_COMMENT].encode(), 0, 
		objects_count, start_instance_offset, 
		IGctn.meshes_count, start_geom_offset, 
		IGctn.bones_count, start_bones_offset, 
		IGctn.materials_count, start_materials_offset, 
		0, 0, #lights
		IGobject_color,  #ambient color...
		0, 0, #splines
		IGctn.gscitems_count, start_gscitems_offset, 
		datablocks_count, 0, 
		start_datablocks_offset) #MODIFS2016: bones, gscitems
	#
	bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message=" Updating offsets...")  # @UndefinedVariable
	# Update offset values
	# --------------------
	#
	for i, vertex in enumerate(IGctn.vertices_list):
		for b_binding in vertex.mBoneBinding:
			b_binding.mBone = start_bones_offset + b_binding.mBone * IGF.BONE_SIZE
		vertex.mReserved = i
	#
	for triangles in IGctn.triangles_list:
		for i in range(3):
			#print(' >>>??? triangles.mVertices[i]', triangles.mVertices[i])
			triangles.mVertices[i] = start_vertices_offset + triangles.mVertices[i] * IGF.VERTEX_SIZE
	#
	for mesh in IGctn.meshes_list:
		# mIsSkinned, mNumVertices, mVertices, mNumTriangles, mTriangles, mBoundingBox, mExtraData
		mesh.mVertices = start_vertices_offset + mesh.mVertices * IGF.VERTEX_SIZE
		mesh.mTriangles = start_triangles_offset + mesh.mTriangles * IGF.TRIANGLE_SIZE
	#
	for meshLOD in IGctn.meshesLODs_list:
		# VisibleDistance, pGeometry, mExtraData
		meshLOD.pGeometry = start_geom_offset + meshLOD.pGeometry * IGF.GEOM_SIZE
	#
	for instance in IGctn.instances_list:
		instance.mGeometry = start_geomLOD_offset + instance.mGeometry * IGF.GEOMLOD_SIZE

	# Update gscitems for parent offset
	# ---------------------------------------------
	#
	for snapp in IGctn.gscitems_list:
		# Parent offset
		if snapp.mParent:
			snapp.mParent = start_instance_offset + (snapp.mParent - 1) * IGF.INSTANCE_SIZE
		
	# Update bones for parent / children offset
	# ---------------------------------------------
	#
	for bone in IGctn.bones_list:
		# Parent offset
		if bone.mParent:
			bone.mParent = start_bones_offset + (bone.mParent - 1) * IGF.BONE_SIZE
		# Children offset
		for b_child_num in range(0, len(bone.mChildren)):
			bone.mChildren[b_child_num] = start_bones_offset + bone.mChildren[b_child_num] * IGF.BONE_SIZE
	
	# Update instances for parent / children offset
	# ---------------------------------------------
	#
	for instance in IGctn.instances_list:
		# Parent offset
		if instance.parent_group is None:
			instance.mParent = 0
			# Update matrix to take hierarchy into account
			# (igs rotation and translation in a child object are relative to its parent)
			#update_matrix(instance)
		else:
			instance.mParent = start_instance_offset + instance.parent_group.IGinstance_id * IGF.INSTANCE_SIZE
		# Children offset
		#print(' >>>> ', instance.mName, len(instance.child_groups_list))
		for child in instance.child_groups_list:
			# child_groups_list is a list of 'group_wrapper' / mChildren was initialized to empty list
			instance.mChildren.append(start_instance_offset + child.IGinstance_id * IGF.INSTANCE_SIZE)
	#
	#	
	#	
	pgr_bar = 75
	pgrh.update(pgr_bar, "Writing to file...")
	#
	bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message=" Writing to materials file...")  # @UndefinedVariable
	#
	# Open the file for writing igs data
	with open(model_directory + '\\' + filename_strip + '.igs', 'wb') as file:
		#
		myHeader.write(file)
		print_pr(2)
		myHeader.dump_log(Config.Verbose)
		#
		print('================================================================================')
		#
		if Config.Verbose:
			print('IGfMaterials                  : [ {:d} ]'.format(IGctn.materials_count))
		for i in range(IGctn.materials_count):
			IGctn.materials_list[i][0].write(file)
			if Config.Verbose:
				IGctn.materials_list[i][0].dump_log(i+1, IGctn.materials_count, start_materials_offset + i * IGF.MATERIAL_SIZE, Config.Verbose)
		#
		pgr_bar = 80
		pgrh.update(pgr_bar, "Writing verts to file...")
		if Config.Verbose:
			print('================================================================================')
			print('IGfVerts                      : [ {:d} ]'.format(IGctn.vertices_count))
		vl = IGctn.vertices_list
		for i in range(IGctn.vertices_count):
			vl[i].write(file)
			if Config.Verbose:
				vl[i].dump_log(i+1, IGctn.vertices_count, start_vertices_offset + i * IGF.VERTEX_SIZE )
		#
		pgr_bar = 85
		pgrh.update(pgr_bar, "Writing tris to file...")
		if Config.Verbose:
			print('================================================================================')
			print('IGfTriangles                  : [ {:d} ]'.format(IGctn.triangles_count))
		tl = IGctn.triangles_list
		for i in range(IGctn.triangles_count):
			tl[i].write(file)
			if Config.Verbose:
				tl[i].dump_log(i+1, IGctn.triangles_count, start_triangles_offset + i * IGF.TRIANGLE_SIZE )
		#
		pgr_bar = 90
		pgrh.update(pgr_bar, "Writing instances to file...")
		#
		if Config.Verbose:
			print('================================================================================')
			print('IGfMeshes                     : [ {:d} ]'.format(IGctn.meshes_count))
		for i in range(IGctn.meshes_count):
			IGctn.meshes_list[i].write(file)
			if Config.Verbose:
				IGctn.meshes_list[i].dump_log(i+1, IGctn.meshes_count, start_geom_offset + i * IGF.GEOM_SIZE)
				#
		if Config.Verbose:
			print('================================================================================')
			print('IGfMeshLODs                   : [ {:d} ]'.format(IGctn.meshes_count))
		for i in range(IGctn.meshes_count):
			IGctn.meshesLODs_list[i].write(file)
			if Config.Verbose:
				IGctn.meshesLODs_list[i].dump_log(i+1, IGctn.meshes_count, start_geomLOD_offset + i * IGF.GEOMLOD_SIZE)
		#
		if Config.Verbose:
			print('================================================================================')
			print('IGfObjects                    : [ {:d} ]'.format(IGctn.meshes_count))
		for i in range(IGctn.meshes_count):
			IGctn.instances_list[i].write(file)
			if Config.Verbose:
				IGctn.instances_list[i].dump_log(i+1, IGctn.meshes_count, start_instance_offset + i * IGF.INSTANCE_SIZE)
		#
		#MODIFS2016: bones
		if Config.Verbose:
			print('================================================================================')
			print('IGfBones                    : [ {:d} ]'.format(IGctn.bones_count))
		for i in range(IGctn.bones_count):
			IGctn.bones_list[i].write(file)
			if Config.Verbose:
				IGctn.bones_list[i].dump_log(i+1, IGctn.bones_count, start_bones_offset + i * IGF.BONE_SIZE)
		#
		#MODIFS2016: snap points
		if Config.Verbose:
			print('================================================================================')
			print('IGfGenericSceneItem           : [ {:d} ]'.format(IGctn.gscitems_count))
		for i in range(IGctn.gscitems_count):
			IGctn.gscitems_list[i].write(file)
			if Config.Verbose:
				IGctn.gscitems_list[i].dump_log(i+1, IGctn.gscitems_count, start_gscitems_offset + i * IGF.GSCITEMS_SIZE)
		#
		if Config.Verbose:
			print('================================================================================')
			print('IGfDataBlocks                 : [ {:d} ]'.format(datablocks_count))
			num_block = 1
			if add_face_tag_description:
				face_tag_description_data_block.dump_log(1, datablocks_count, start_datablocks_offset)
				num_block = 2
			textures_data_block.dump_log(num_block, datablocks_count, start_datablocks_offset + (num_block - 1) * IGF.DATABLOCK_SIZE)
		if add_face_tag_description:
			face_tag_description_data_block.write(file)
		textures_data_block.write(file)
		if add_face_tag_description:
			if Config.Verbose:
				face_tag_description.dump_log(start_datablocks_offset + 2 * IGF.DATABLOCK_SIZE)
			face_tag_description.write(file)
		texture_names.write(file)
		#
		print('================================================================================')
		texture_names.dump_log(start_texturenames_offset)
	#file closed
	
	del IGctn
	#
	pgr_bar = 100
	pgrh.update(pgr_bar, "Reverting Scene...")
	#
	return 'FINISHED'
