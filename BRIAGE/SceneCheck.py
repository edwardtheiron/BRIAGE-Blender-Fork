# ##### BEGIN LICENSE BLOCK #####
#
# Copyright (C) 2024 'Juju49'(MERLE-RÉMOND Julian)
# see license notes __init__.py
#
# ##### END LICENSE BLOCK #####

import bpy # @UnresolvedImport
import os

from . Bl_data import (
	SHADERS_LIST,
	SHADERS_ENUM)

from ._datastructs.IGF import gVertexWeldNormalThreshold, MAX_EXPORTED_BONES, MAX_CHILDREN
from BRIAGE.Groups import MAX_NAME_WITHOUT_LOD


PROFILE_MODE = True

error_bias = 8 #error code above this value are counted as errors and not warnings only
	

def _checkMaterial(Config, material):
	error_flags = 0
	texslots = material.IgsMat.textures#2020
	# check properties of applied materials texture slots
	num_slot = len(texslots)
	
	if (num_slot == 0):
		mShaderName = material.IgsMat.shader_name
		if mShaderName == 'custom' or len(SHADERS_ENUM) == 1: 
			mShaderName = material.IgsMat.shader_name_string
		
		#error_flags += 0b10 #warning2
		#bpy.ops.igs_err.damned('EXEC_DEFAULT',type='INFO', message=" Material '{1}' is not using any texture with shader '{0}'.".format(mShaderName, material.name))
		
		if mShaderName in SHADERS_LIST:
			if (int(SHADERS_LIST[mShaderName][1]) != num_slot):
				error_flags += 0b10000 << error_bias#error16
				if not Config.u_test_mode:
					bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='ERROR',  # @undefinedVariable
						message=" Incorrect number of slots for shader name {0} used in material named {1}, {2} texture slots must be set in Blender; {3} found".format(mShaderName, material.name, SHADERS_LIST[mShaderName][1], num_slot))
				return error_flags
			
	for j, txslot in enumerate(texslots):
		#check shader name validity
		if j == 0:
			mShaderName = material.IgsMat.shader_name
			if mShaderName == 'custom' or len(SHADERS_ENUM) == 1: 
				mShaderName = material.IgsMat.shader_name_string
			
			if (num_slot == 0):
				error_flags += 0b10 #warning2
				bpy.ops.igs_err.damned('EXEC_DEFAULT',type='INFO', message=" Material '{1}' is not using any texture with shader '{0}'.".format(mShaderName, material.name)) # @undefinedVariable

			if mShaderName in SHADERS_LIST:
				if (int(SHADERS_LIST[mShaderName][1]) != num_slot):
					error_flags += 0b10000  << error_bias#error16
					if not Config.u_test_mode:
						bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='ERROR',  # @undefinedVariable
							message=" Incorrect number of slots for shader name {0} used in material named {1}, {2} texture slots must be set in Blender; {3} found".format(mShaderName, material.name, SHADERS_LIST[mShaderName][1], num_slot))
					return error_flags
					
			if (mShaderName.find('WeatherEffects') >= 0) and (num_slot == 1):
				name_split = material.name.split('_')
				if (len(name_split) != 2) or (name_split[0] != 'weatherglass') or not (name_split[1].isdigit()): # @undefinedVariable
					error_flags += 0b100000  << error_bias#error128
					if not Config.u_test_mode:
						bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='ERROR',  # @undefinedVariable
							message=" With shader name TrainGlassWeatherEffects.fx, material name must be weatherglass_1, weatherglass_2, etc.. ('{:s}' was found)".format(material.name))
					return error_flags
						
			del mShaderName
			
		#check textures
		
		if txslot.texture is None: #if no image assigned
			error_flags += 0b100000 << error_bias #error32
			if not Config.u_test_mode:
				bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='ERROR',  # @undefinedVariable
					message=" Missing image file in material '{0}', in texture slot '{1}'".format(material.name, j))
			return error_flags
		
		texture_file_name = txslot.texture.filepath
		tfn_test = os.path.basename(texture_file_name)
			
		if tfn_test != "":
			ext = tfn_test.rfind('.')
			if (ext == -1): #if no other texture path can be assigned
				error_flags += 0b100000 << error_bias #error32
				if not Config.u_test_mode:
					bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='ERROR',  # @undefinedVariable
						message=" Missing image file in material '{0}', in texture slot '{1}'".format(material.name, j))
				return error_flags
			
			texture_file_name = tfn_test[:ext]
		
		else: #fallback mode if os.path.basename fails to compute correctly
			ext = texture_file_name.rfind('.')
			if (ext == -1): #if no other texture path can be assigned
				error_flags += 0b100000 << error_bias #error32
				if not Config.u_test_mode:
					bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='ERROR',  # @undefinedVariable
						message=" Missing image file in material '{0}', in texture slot '{1}'".format(material.name, j))
				return error_flags
			
			base = texture_file_name.rfind('\\')
			if base != -1:
				texture_file_name = texture_file_name[base+1:ext]
		del tfn_test
		
		# Process texture file substitution   # MAJ_1_4_0b #MODIFS2016
		for strings in Config.texture_string_to_replace: #texture name replace mode
			if "#" == strings.name[0]:
				if strings.name[1:] == texture_file_name:
					texture_file_name = strings.prop1
					
		for strings in Config.texture_string_to_replace: #string replace mode
			if (strings.name in texture_file_name) and ("#" != strings.name[0]):
				texture_file_name = texture_file_name.replace(strings.name, strings.prop1)
		# =================================================convert texture_file_name to path
		
		if texture_file_name.count(".") > 0:
				error_flags += 0b100 #warning4
				bpy.ops.igs_err.damned('EXEC_DEFAULT',type='WARNING',  # @undefinedVariable
					message=f" Image filename '{texture_file_name}' contains dots '.' which will cause unexpected results in material '{material.name}', in texture slot nb'{j}'")
				
				texture_file_name += ".safe"
		
		# Add specific target:
		if txslot.use_source_tex_file_path  or (Config.target_textures_directory == ""):
			ext = (txslot.texture.filepath).rindex('.')
			texture_file_name = txslot.texture.filepath[:ext]

		# Add target textures directory:
		else:
			texture_file_name = Config.target_textures_directory + "\\" + texture_file_name
		
		#MODIFS2016 Remap paths:
		ref_path = bpy.path.abspath("//") # @undefinedVariable
		if Config.remap_to_igf:
			ref_path = os.path.dirname(bpy.path.abspath(Config.FilePath)) # @undefinedVariable
			
		try:
			texture_file_name = (bpy.path.relpath(bpy.path.abspath(texture_file_name), start=ref_path)).lstrip("/") # @undefinedVariable
		except ValueError as VE:
			p_args = (VE.args[0]).split(',')
			p_texname = bpy.path.basename(texture_file_name) # @undefinedVariable
			error_flags += 0b1000000 << error_bias #error64
			if not Config.u_test_mode:
				bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR',  # @undefinedVariable
					message="Final IGS export path {1} .  But textures {0} .  Please, export to the same drive your data are from!  Texture '{2}' not added from '{3}'".format(p_args[0], p_args[1], p_texname, texture_file_name))
				bpy.ops.igs_err.damned('EXEC_DEFAULT',type='ERROR', # @undefinedVariable
					message=" Cannot link image file in material '{0}', in texture slot '{1}'".format(material.name, txslot.texture.name))
			return error_flags
	return error_flags

def _checkMesh(Config, ob):
	""" Config, ob -> error_flags, mat_data_index
	
		Checks if ob is ready for export according to Config values"""
	error_flags = 0
	mat_data_index = set()
	should_add_test_mat = False
	
	mesh = ob.data.evaluated_get(Config.dpg) # Create mesh object
	
	#check if UVs exist
	if (len(mesh.uv_layers) == 0) and (not Config.u_test_mode):
		error_flags += 0b1 << error_bias #error1
		bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR',  # @undefinedVariable
			message=" Blender Mesh object '{:s}' has no collection of UV maps (check material assignement).".format(ob.name))
		return error_flags, mat_data_index
	
	
	#test face(s) or present
	if len(mesh.polygons) == 0:
		error_flags += 0b10 << error_bias #error2
		bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR',  # @undefinedVariable
			message=" Blender Mesh object '{:s}' has no face(s)!!".format(ob.name))
		return error_flags, mat_data_index
	
	if len(mesh.materials) == 0: #and not should_add_test_mat:
			if Config.u_test_mode:
				should_add_test_mat = True
			else:
				error_flags += 0b10000000 << error_bias #error128
				bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR',  # @undefinedVariable
					message=" Blender Mesh object '{:s}' has no materials assigned.".format(ob.name))
				return error_flags, mat_data_index
	
	#list materials applied and test face area:
	applied_set = set()
	face_area_problems_already = False
	for face in mesh.polygons:
		#check face area
		if not face_area_problems_already and not mesh.has_custom_normals and face.area < gVertexWeldNormalThreshold:
			if not Config.u_test_mode:
				error_flags += 0b11 #Warning3
				bpy.ops.igs_err.damned('EXEC_DEFAULT', type='WARNING',  # @undefinedVariable
					message=" Blender Mesh object '{:s}' face No{:d} has a ludicrous size, there is a high risk of a hole to appear in mesh.".format(ob.name, face.index))#\n\
	#If face doesn't exist, it is generated by one of your modifiers.\n\
	#to prevent this from happening, apply your modifiers then use a normal editor and weld its normals to other faces around.\n\
	#Next occurrences of this warning will not display for this object.".format(ob.name, face.index))
			face_area_problems_already = True
		
		#check if a material is assigned to each face unless in test mode
		#2020: default index is 0, check materials list directly (see up)
		# saves applied materials
		applied_set.add(face.material_index)
	
	#del msh  # @UndefinedVariable
		
	#if PROFILE_MODE:
	#	print(">>>CS: applied set: "+str(applied_set))
		
	#check if a material is present
	#11/2018 didn't check for empty mat list
	#dec2020 didn't check for slot without material
	if ((not len(ob.material_slots)) or (applied_set is set())) and not should_add_test_mat:
		if Config.u_test_mode:
			should_add_test_mat = True
		else:
			error_flags += 0b100 << error_bias #error4
			bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR', # @undefinedVariable
				message=" Blender Mesh object '{0}' has no material assigned.".format(ob.name))
			return error_flags, mat_data_index

	#assert applied_set or should_add_test_mat, "CheckScene: Invalid material diagnosis"

	#Review selected materials for export
	for i in range(len(ob.material_slots)):
		if i in applied_set:
			material = ob.material_slots[i].material
			if not material :
				0b100 << error_bias #error4
				bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR', # @undefinedVariable
					message=f" Blender Mesh object '{ob.name}' has an empty material slot.")
				return error_flags, mat_data_index
			if not material.IgsMat : #2021 invalid mat 
				0b100 << error_bias #error4
				bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR', # @undefinedVariable
					message=f" Blender Mesh object '{ob.name}' has an invalid material '{material.name}'")
				return error_flags, mat_data_index
			error_flags += _checkMaterial(Config, material)
			
			#print(material, error_flags)
			
			#re-raise error
			if error_bias < error_flags:
				if Config.u_test_mode:
					should_add_test_mat = True
					error_flags = 0
					continue
				else:
					return error_flags, mat_data_index
			else:
				#add material to our list of validated content
				mat_data_index.add(material.id_data)
			
	if Config.u_test_mode and (should_add_test_mat or not mat_data_index):
		if Config.u_test_mat == '':
			error_flags += 0b100 << error_bias #error4
			bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR',  # @undefinedVariable
				message=" Blender Mesh object '{0}' needs a valid test material".format(ob.name))
			return error_flags, mat_data_index
		
		material = bpy.data.materials[Config.u_test_mat]  # @UndefinedVariable
		error_flags += _checkMaterial(Config, material)
		#re-raise error
		if error_bias < error_flags:
#			if PROFILE_MODE:
#				print(">>> default mat is not feeling so good...")
				
			return error_flags, mat_data_index
		mat_data_index.add(material)
	
	#super error filter
# 	if PROFILE_MODE:
# 		print(ob.name, " CS exit:",error_flags, str(mat_data_index))
# 	assert (0 < error_flags < warn_bias) or mat_data_index, "SceneCheck: No data but no errors?!!"

	
	return error_flags, mat_data_index

def _unfoldLOD(obname):
	name_split = obname.split('_')
	#dec2020: if it was not properly formated int
	if name_split[0].isdigit() and name_split[1].isdigit():
		return int(name_split[0]), int(name_split[1]), name_split[2][:MAX_NAME_WITHOUT_LOD]
	else:
		return 1, 1000, obname

def _checkLOD(Config, ob, objects_list):
	err_incons_loding = False
	LOD_num, LOD_dist, LOD_name = _unfoldLOD(ob.name)
	if LOD_num >= 1:
		if LOD_num > 1:
			if (ob.parent and 
			ob.parent in objects_list):
				pLOD_num, pLOD_dist, pLOD_name = _unfoldLOD(ob.parent.name)
				
				if (pLOD_num < LOD_num and 
				pLOD_dist < LOD_dist and 
				pLOD_name == LOD_name):
					
					if (LOD_num > 2):
						#No previous LOD available or not correct
						err_incons_loding = True
						for chd in ob.parent.children:
							cLOD_num, cLOD_dist, cLOD_name = _unfoldLOD(chd.name)
							if (LOD_num-1 == cLOD_num and 
							cLOD_dist < LOD_dist and 
							cLOD_name == LOD_name):
								#Previous LOD found
								err_incons_loding = False
								#we don't check all of them since each object will check the one above himself
								break
				else:
					#LOD dist or num is not correct regarding top LOD
					err_incons_loding = True
			else:
				#parent is absent for subLOD (LOD > 1)
				err_incons_loding = True
		pass #top LOD OK
	else:
		#LOD number invalid
		err_incons_loding = True
	
	if err_incons_loding:
		bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='ERROR', # @undefinedVariable 
			message=f" Inconsistent loding at object {ob.name}!")


def checkScene(Config, objects_list):
	"""	Config, objects_list -> mat_data_index
		Checks if the objects in scene are ready for export and returns a list of materials to export"""
	mat_data_index = set()

	assert objects_list, "SceneCheck: Empty object list"

	for ob in objects_list:
		if ob.type == 'MESH':
			if len(ob.children) > MAX_CHILDREN:
					bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='ERROR',  # @undefinedVariable
						message=f" Too many children for object '{ob.name}'! : {len(ob.children)} > {MAX_CHILDREN}")
			
			_checkLOD(Config, ob, objects_list)
				
			error_flags = 0
			error_flags, mat_data_index_i = _checkMesh(Config, ob)
			if error_bias < error_flags: #=>there are errors (flags cumulative max val < warning bias)
				print("BRIAGE: CheckScene: exiting with error code: ", error_flags)
				return None
			mat_data_index.update(mat_data_index_i)
			
			#super error filter
			#print(error_flags, str(mat_data_index_i))
			assert (0 <= error_flags <= error_bias) or not mat_data_index_i, "SceneCheck: No materials but no errors?!! for object: " + ob.name
			
		elif ob.type == 'ARMATURE':
			for bone in ob.data.bones:
				if len(bone.children) > MAX_EXPORTED_BONES:
					bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='ERROR',  # @undefinedVariable
						message=f" Too many children for bone {bone.name} in armature '{ob.name}'! : {len(bone.children)} < {MAX_EXPORTED_BONES}")
				elif len(bone.children) > 3: #juillet 2023 : empirical deduction from trial and errors in TS with complex pantograph
					bpy.ops.igs_err.damned('EXEC_DEFAULT',type='WARNING',  # @undefinedVariable
						message=f" More than 3 children for bone {bone.name} in armature '{ob.name}', animations may shake when played : {len(bone.children)} < 3")

# 		if ob.dupli_type not in {'NONE', 'FRAMES'}: #duplicates obj itself
# 			ob_set = None
# 			if ob.dupli_type in {'VERTS', 'FACES'}: #duplicates childs of obj
# 				ob_set = [chd for chd in ob.children if chd not in objects_list]
# 				
# 			elif ob.dupli_group : # instance a 'GROUP'
# 				ob_set = set(chd for chd in ob.dupli_group.objects if chd not in objects_list)
# 				
# 			if ob_set:
# 				new_material_data = checkScene(Config, ob_set)
# 				if new_material_data is None:
# 					return None
# 				mat_data_index.update( set(new_material_data) )
			
	#print("checkScene: exiting loop cleanly")
	
	return list(mat_data_index)