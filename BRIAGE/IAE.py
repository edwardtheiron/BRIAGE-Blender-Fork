# ##### BEGIN LICENSE BLOCK #####
#
# Copyright (C) 2024  'Juju49'(MERLE-RÉMOND Julian), 'DOM107'
# see license notes __init__.py
#
# ##### END LICENSE BLOCK #####

#====================================================================INFO
_info = {
	"version" : (3, 2, "201")}

IAE_VERSION = 'IAE V' + '.'.join(str(i) for i in _info['version'])

#====================================================================IMPORTS
import bpy  # @UnresolvedImport
import os

from mathutils import Matrix  # @UnresolvedImport

from ._datastructs import IAF
from . Utilityfcts import (
	print_pr, 
	center_main_object,
	profiler)
from . Groups import make_groups
from . CleanAndProperSceneExport import CleanAndProperSceneExport

#====================================================================GLOBALS
MAXFRAMERATEMULTPLIER = 10
PROFILE_MODE = "dev" in _info['version'][2]
NO_MAKE_COMPATIBLE = bpy.app.version[0] == 2 and bpy.app.version[1] < 82  # @UndefinedVariable
if NO_MAKE_COMPATIBLE:
	from math import atan2
#====================================================================EXPORT FCTS

class object_wrapper(object):
	'''Class to gather animation ia objects for a Blender object'''

	__slots__ = ("name", "animation_node", "motion_controller", "motion_vector", "motion_quaternion", "persistent_id")

	def __init__(self, name, animation_node, motion_controller, motion_vector, motion_quaternion):
		self.name = name
		self.animation_node = animation_node # 1 animation node
		self.motion_controller = motion_controller # 2 motion controllers
		self.motion_vector = motion_vector
		self.motion_quaternion = motion_quaternion

	def dump(self):
		print("--- object_wrapper --- {:s}".format(self.name))
		self.animation_node.dump_log2()
		for mc in self.motion_controller:
			mc.dump_log2()


def has_animation_in_hierachy(IActn, Object):
# Has animation or has animation as parent
	if Object.animation_data or Object.constraints:
		return True
	if not IActn.relative_export and (Object.parent is not None):
		return has_animation_in_hierachy(IActn, Object.parent)
# 	for obj_children in Object.children:
# 		if obj_children.animation_data or obj_children.constraints:
# 			return True
	return False


def is_moving_during_anim(ia_obj):
	'''fonction qui dit si une suite de controller d'anim ne bouge pas relativement'''
	for i in range(len(ia_obj.motion_vector)):
		if  ia_obj.motion_vector[i]     != ia_obj.motion_vector[i-1]    or \
			ia_obj.motion_quaternion[i] != ia_obj.motion_quaternion[i-1]:
			return True
	return False

class IAArray():
	def __init__(self):
		self.FrameRateMultiplier = 7 #prevents jump on 360 anims
		self.KeyframeCount = 0
		
		self.global_transform_matrix = Matrix()
		self.relative_export = True
		self.ia_objects_list = []
		self.animation_node_index = 0
		self.motion_controller_index = 0

class IAObjectGen():
	def __init__(self, ob, IActn, o_type):
		self.ob = ob
		self.o_type = o_type
		
		self.vector_frame_list      = []
		self.quaternion_frame_list  = []
		
		self.trim_start = 0
		self.trim_end = 0
		self.prev_position = None
		self.prev_rotation = None
		
		self.IActn = IActn
		
		if o_type == 'MSH':
			bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message=" Instance '{}' was added to export".format(ob.name))
		else:
			bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message=" Bone     '{}' was added to export".format(ob.name))
		
	def _getMatrix(self, main_ob=None):
		
		if self.o_type == 'MSH': #is a regular group
			if not main_ob:
				main_ob = self.ob.objects_list[0]
			
			if self.ob.parent_group:
				MyMatrix = self.ob.parent_group.objects_list[0].matrix_world.inverted() @ main_ob.matrix_world

			elif self.IActn.relative_export and main_ob.parent: #parent not processed in selection, Duplis cannot enter here
				MyMatrix = main_ob.parent.matrix_world.inverted() @ self.IActn.global_transform_matrix @ main_ob.matrix_world

			else:
				MyMatrix = self.IActn.global_transform_matrix @ main_ob.matrix_world
				
				
		else: #is a bone
			main_ob = self.ob
			
			if self.ob.parent:
				MyMatrix = self.ob.parent.matrix.inverted() @ main_ob.matrix
			else:
				MyMatrix = self.IActn.global_transform_matrix @ main_ob.id_data.matrix_world @ main_ob.matrix
				
		
				
		return MyMatrix
	
	if NO_MAKE_COMPATIBLE:
		#fix <180° rotations by finding correct quaternion to pick in 4D space
		@staticmethod
		def getClosestQuaternion(p_qtn, qtn, n_qtn):
			if (p_qtn is None) or (n_qtn is None):
				return qtn
			
			qtn_i = qtn.inverted()
			closest_mid_qtn = p_qtn.slerp(n_qtn, 0.5)
			
			qe1 = closest_mid_qtn.rotation_difference( qtn )
			qe2 = closest_mid_qtn.rotation_difference(qtn_i)
			
			#retourner l'opposé lorsque l'on atteint 180°
			aqe2 = abs(2 * atan2(len(qe2.axis), qe2.w)) #acos(2 * qtn_i.dot(closest_mid_qtn)**2 - 1)
			aqe1 = abs(2 * atan2(len(qe1.axis), qe1.w)) #acos(2 * qtn.dot(closest_mid_qtn)**2 - 1)
			
			if aqe1 < aqe2:
				return qtn
			return qtn_i
		
		
	def addFrame(self):
		MyMatrix = self._getMatrix()
		
		Rotation = MyMatrix.to_quaternion()
		if self.prev_rotation and not NO_MAKE_COMPATIBLE:
			Rotation.make_compatible(self.prev_rotation) #2020 try to prevent TS weird 180° errors
		Position = MyMatrix.to_translation()
		
		new_quaternion = IAF.IAMotionQuaternionFrame(Rotation)
		new_vector = IAF.IAMotionVector4Frame(Position)

		if self.prev_position is not None: #not frame0
			FrameRateMultiplier = self.IActn.FrameRateMultiplier
			# Add intermediary frames for smoothness
			for i in range(1, FrameRateMultiplier):
				inter_vector = IAF.IAMotionVector4Frame(self.prev_position.lerp(Position, i/FrameRateMultiplier))
				inter_quaternion = IAF.IAMotionQuaternionFrame(self.prev_rotation.slerp(Rotation, i/FrameRateMultiplier))
				
				self.vector_frame_list.append(inter_vector)
				self.quaternion_frame_list.append(inter_quaternion)
		
			if self.prev_position == Position and self.prev_rotation == Rotation:
				if self.trim_start == self.trim_end:
					self.trim_start += FrameRateMultiplier
					self.trim_end += FrameRateMultiplier
			else:
				self.trim_end = len(self.quaternion_frame_list)+2
				#no '+=' to cover cases of stop then restart after skipping frames
				#+1 because one vector is added later
				#+1 because we want to capture it with a slice later in code
					
		self.vector_frame_list.append(new_vector)
		self.prev_position = Position
		self.quaternion_frame_list.append(new_quaternion)
		self.prev_rotation = Rotation
		
	def packageIAObject(self):
		# mControllerType, mKeySize, mKeyStream
		motion_controller_list = []
		motion_controller_list.append(IAF.IAMotionController(0, 16, self.IActn.motion_controller_index))
		motion_controller_list.append(IAF.IAMotionController(1, 16, self.IActn.motion_controller_index + 1))
		
		animation_node = IAF.IAAnimationNode(
			mName=self.ob.name.encode(), 
			mNumControllers=2,
			mMotionControllers=self.IActn.motion_controller_index
			)
		
		if NO_MAKE_COMPATIBLE:
			#check rotation continuity
			for i in range(1, len(self.quaternion_frame_list)-1):
				self.quaternion_frame_list[i].quater = self.getClosestQuaternion(self.quaternion_frame_list[i-1].quater, self.quaternion_frame_list[i].quater, self.quaternion_frame_list[i+1].quater)
			#if PROFILE_MODE and 106 <= i <= 110:
			#	print("quater frame ",i ,self.quaternion_frame_list[i].quater)
		
		#print(" wrapper_name, animation_node_index, motion_controller_index ", wrapper_name, animation_node_index, motion_controller_index)
	
		ia_obj = object_wrapper(self.ob.name, animation_node, 
			motion_controller_list, self.vector_frame_list, self.quaternion_frame_list)
				
		# control if animating nothing	
		#bpy.context.scene.frame_set(0)
		
		MyMatrix = self._getMatrix()
			
		start_pos = MyMatrix.to_quaternion()
		start_rot = MyMatrix.to_translation()
			
		if  start_pos == self.vector_frame_list[0] and \
			start_rot == self.quaternion_frame_list[0]:
			if not is_moving_during_anim(ia_obj):
				bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message=" Group    '{}' has been filtered out".format(ia_obj.name))
				return
		
		self.IActn.animation_node_index += 1
		self.IActn.motion_controller_index += 2
		self.IActn.ia_objects_list.append(ia_obj)


#====================================================================EXPORT MAIN
@profiler(PROFILE_MODE)
def ExportIA(Config, pgrh):
	""" Bl_data.IGSExporterSettings(bpy.types.PropertyGroup) * context.window_manager
	-> str or NoneType
	wrapper for the real exporter, protects users scenes  """
	
	pgrh.update(0, "Cleaning Scene...")
	wrapper = CleanAndProperSceneExport(Config)
	with wrapper as objects_list:
		if not objects_list:
			raise RuntimeError("BRIAGE: Empty object list! check Blender console or log file") from None
	
		export_errors = _internal_ExportIA(wrapper.Config, pgrh, objects_list)
		pgrh.update(100, "Reverting Scene...")
		
	return export_errors or None


def _internal_ExportIA(Config, pgrh, objects_list):         
	
	# Current  model directory name
	model_directory = os.path.dirname(Config.FilePath)
	# Current model file name
	model_name = os.path.basename(Config.FilePath)
	# Name without suffix
	filename_strip = os.path.splitext(model_name)[0]
	
	#basic container to pass values around without a hassle
	IActn = IAArray()
	IActn.relative_export = Config.relative_export
	IActn.TrimAnimation = Config.TrimAnimation
	
	IActn.FrameRateMultiplier = Config.FrameRateMultiplier
	if IActn.FrameRateMultiplier > MAXFRAMERATEMULTPLIER:
		print(" ERROR: Frame rate multiplier greater than {:d}. FrameRateMultiplier reset to 1.".format(MAXFRAMERATEMULTPLIER))
		IActn.FrameRateMultiplier = 1

	RemoveLastFrame = Config.RemoveLastFrame

	# ------------------------------------------------------------------------------------------
	# Read Model specific file for Blender IGS exporter
	context = Config.context
	scene = context.scene
	
	igs_config = scene.IgsOpt
	igs_config.context = context
	
	#Center Main Object
	IActn.global_transform_matrix = center_main_object(igs_config, objects_list)
	pgrh.update(20, "Generating groups...") 
	# Sort objects in groups
	try:
		groups_list = make_groups(igs_config, objects_list, False)
	except AssertionError:
		groups_list = []
	# ------------------------------------------------------------------------------------------

	# Start of export

	bpy.ops.object.mode_set(mode='OBJECT')

	#'''--------------------------------------------------'''
	#'''Save the selected Blender objects into ia objects.'''
	#'''--------------------------------------------------'''
	
	IActn.KeyframeCount = Config.context.scene.frame_end - Config.context.scene.frame_start + 1
	print('\n\n')
	bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', 
		message=" Keyframes count = {:d} (frame start={:d} / frame end={:d})\n Frame count multiplier = {}".format(
			IActn.KeyframeCount, Config.context.scene.frame_start, Config.context.scene.frame_end, IActn.FrameRateMultiplier))
	
	if IActn.KeyframeCount == 0:
		print("")
		bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR', message=" No animation found (key frame count = 0): Export stopped")
		return {'FINISHED with error'}


	anim_objects_list = []
	
	pgrh.update(30, "Looking for animated content...")
	
	#sort armatures out and process bones:
	if igs_config.process_bones:
		for armature in [obj for obj in objects_list if obj.type == 'ARMATURE']:
			if has_animation_in_hierachy(IActn, armature):
				#Go to pose mode to track selections
				#bpy.ops.object.mode_set({'selected_objects':[armature], 'active_object':armature}, mode='POSE')
				#armature.data.pose_position = 'POSE'
				#no duplicator check for armatures because they should not be duplicated alone
				for bone in armature.pose.bones:
					if (not igs_config.use_selection) \
					or (bone.bone.select and igs_config.use_selection):
						anim_objects_list.append(IAObjectGen(bone, IActn, 'BONE')) #juillet 2023:modif select bones bl3.6
				#bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message=" Processing ARMATURE '{0}'".format(armature.name))
				#return to object mode to track positions
				#bpy.ops.object.mode_set({'selected_objects':[armature], 'active_object':armature}, mode='OBJECT')
	for gp in groups_list:
		ob = gp.objects_list[0]
		if (gp.type_o == 'MSH') and ((ob.animation_data or ob.constraints) or (not gp.parent_group and has_animation_in_hierachy(IActn, ob))):
			anim_objects_list.append(IAObjectGen(gp, IActn, 'MSH'))


	if not anim_objects_list:
		bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR', message=" No animation found (no suitable group): Export stopped")
		return {'FINISHED with error'}
	
	#save current frame
	current_frame = scene.frame_current 
	pgr_bar = 40
	pgrh.update(pgr_bar, "Tracking motion on {} frames...".format(IActn.KeyframeCount))
	
	#roll frames and save selected groups
	for frame in range(IActn.KeyframeCount):
		scene.frame_set(frame + scene.frame_start)

		for anim_ob in anim_objects_list:
			anim_ob.addFrame()
	else:
		#stop execution
		bpy.context.scene.frame_set(0) #compare with first frame  # @UndefinedVariable

		if IActn.TrimAnimation: #if trimming enabled
			trim_start = anim_objects_list[0].trim_start
			trim_end = 0
			for anim_ob in anim_objects_list:
				trim_start = anim_ob.trim_start if trim_start > anim_ob.trim_start else trim_start #get cut at begining
				trim_end = anim_ob.trim_end if trim_end < anim_ob.trim_end else trim_end #get cut at end
				#print(anim_ob.ob.name,  "trim:", anim_ob.trim_start, anim_ob.trim_end) 
				
			for anim_ob in anim_objects_list: #trim each list before compiling
				anim_ob.vector_frame_list = anim_ob.vector_frame_list[trim_start:trim_end]
				anim_ob.quaternion_frame_list = anim_ob.quaternion_frame_list[trim_start:trim_end]
				anim_ob.packageIAObject()
		
			IActn.KeyframeCount = trim_end - trim_start
			#print("trim:", trim_start, trim_end) 
		
		else:
			for anim_ob in anim_objects_list:
				anim_ob.packageIAObject()
		
	# Reset object to initial frame position
	scene.frame_set(current_frame)
	
	pgrh.update(70, "Updating offsets...") 
	
	#print(' animation_node_index = / motion_controller_index = ', animation_node_index, motion_controller_index)
	if IActn.animation_node_index == 0:
		bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR', message=" No animation found (no animation nodes): Export stopped")
		return {'FINISHED with error'}
	
	# Update data to deal with actual offsets in the future IA file
	if IActn.TrimAnimation: #if trimming enabled, kf count obtained differently
		total_frames_count = IActn.KeyframeCount - 1
	else:
		total_frames_count = (IActn.KeyframeCount-1) * IActn.FrameRateMultiplier + 1
		
	if RemoveLastFrame:
		total_frames_count -= 1
	
	start_animation_node_offset = IAF.HEADER_SIZE 
	start_motion_controller_offset = IAF.HEADER_SIZE + IActn.animation_node_index * IAF.ANIMATIONNODE_SIZE 
	start_motion_set_offset = start_motion_controller_offset + IActn.motion_controller_index * IAF.MOTIONCONTROLLER_SIZE 
	for ia_obj in IActn.ia_objects_list:
		ia_obj.animation_node.mMotionControllers = start_motion_controller_offset + ia_obj.animation_node.mMotionControllers * IAF.MOTIONCONTROLLER_SIZE
		ia_obj.motion_controller[0].mKeyStream = start_motion_set_offset + ia_obj.motion_controller[0].mKeyStream * IAF.MOTIONSET_SIZE * total_frames_count
		ia_obj.motion_controller[1].mKeyStream = start_motion_set_offset + ia_obj.motion_controller[1].mKeyStream * IAF.MOTIONSET_SIZE * total_frames_count
		
	# Initialize Header structure
	blender_version = ".".join(str(i) for i in bpy.app.version)  # @UndefinedVariable
	exporter_version = IAE_VERSION
	myComment = 'Blender ' + blender_version + ' - ' + exporter_version
	mTriggersTimeline = IAF.IATriggerTimeline(0, 0)
	# mCommentField, mDataStart, mTotalFrames, mSampleRate, mTriggersTimeline, mNumAnimationNodes, mAnimationNodes, mDataEnd
	myHeader = IAF.IAFHeader(myComment.encode(), 0,
		total_frames_count, IActn.FrameRateMultiplier * int(Config.context.scene.render.fps / Config.context.scene.render.fps_base),
		mTriggersTimeline, IActn.animation_node_index,
		start_animation_node_offset, 0)
	
	pgrh.update(80, "Writing to file...")
	# Open the file for writing ia data
	with open(model_directory + '\\' + filename_strip + '.ia', 'wb') as file:
		
		myHeader.write(file)
		
		print_pr(2)
		if Config.Verbose:
			myHeader.dump_log()
	
		if Config.Verbose:
			print('================================================================================')
			print('IAfAnimationNodes             : [ {:d} ]'.format(IActn.animation_node_index))
		else:
			print('\n==========================')
			print(' --- Included objects in the animation: ---')
		for i in range(IActn.animation_node_index):
			IActn.ia_objects_list[i].animation_node.write(file)
			IActn.ia_objects_list[i].animation_node.dump_log(i+1, IActn.animation_node_index, start_animation_node_offset + i * IAF.ANIMATIONNODE_SIZE, Config.Verbose)
	
		if Config.Verbose:
			print('================================================================================')
			print('IAfMotionControllers          : [ {:d} ]'.format(IActn.motion_controller_index))
		for i in range(IActn.animation_node_index):
			IActn.ia_objects_list[i].motion_controller[0].write(file)
			IActn.ia_objects_list[i].motion_controller[1].write(file)
			if Config.Verbose:
				IActn.ia_objects_list[i].motion_controller[0].dump_log(2*i+1, IActn.motion_controller_index, start_motion_controller_offset + 2*i * IAF.MOTIONCONTROLLER_SIZE )
				IActn.ia_objects_list[i].motion_controller[1].dump_log(2*i+2, IActn.motion_controller_index, start_motion_controller_offset + (2*i+1) * IAF.MOTIONCONTROLLER_SIZE )
		
		pgrh.update(85, "Writing to file...")
		if Config.Verbose:
			print('================================================================================')
			print('IAfMotionSets                 : [ {:d} ]'.format(IActn.motion_controller_index))
		for i in range(IActn.animation_node_index):
			offset = IActn.ia_objects_list[i].motion_controller[0].mKeyStream
			if Config.Verbose:
				print('--------------------------------------------------------------------------------')
				print('IAfMotionSets [ {:d}  /  {:d}  ] ({:d}) :'.format(2*i+1, IActn.motion_controller_index, offset))
				print('------------------------------.')
			for frame_num in range(total_frames_count):
				IActn.ia_objects_list[i].motion_vector[frame_num].write(file)
				if Config.Verbose:
					IActn.ia_objects_list[i].motion_vector[frame_num].dump_log(frame_num)
			offset = IActn.ia_objects_list[i].motion_controller[1].mKeyStream
			if Config.Verbose:
				print('--------------------------------------------------------------------------------')
				print('IAfMotionSets [ {:d}  /  {:d}  ] ({:d}) :'.format(2*(i+1), IActn.motion_controller_index, offset))
				print('------------------------------.')
			#for frame_num in range((KeyframeCount - 1) * FrameRateMultiplier):
			for frame_num in range(total_frames_count):
				IActn.ia_objects_list[i].motion_quaternion[frame_num].write(file)
				if Config.Verbose:
					IActn.ia_objects_list[i].motion_quaternion[frame_num].dump_log(frame_num)
				
		# Close the file

#---------------------------

	return {'FINISHED'}
