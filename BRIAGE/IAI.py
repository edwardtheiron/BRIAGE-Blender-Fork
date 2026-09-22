# ##### BEGIN LICENSE BLOCK #####
#
# Copyright (C) 2020 'Juju49'(MERLE-RÉMOND Julian), 'DOM107'
# see license notes __init__.py
#
# ##### END LICENSE BLOCK #####
from mathutils import Quaternion

#====================================================================INFO
"""submodule for importing IA files:  
    mthd: ImportIA(ctx, file)
    file is a filepath"""

_info = {
    "version" : (1, 0, "111")}

IAI_VERSION = 'IAI V' + '.'.join(str(i) for i in _info['version'])

#====================================================================IMPORTS
import bpy
import os

from mathutils import Vector, Matrix  # @UnresolvedImport
from math import radians

from .Utilityfcts import profiler
from ._datastructs import IAF

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

#matrix to transform vectors from TS instance local space
TS_MATRIX = Matrix((
    (1.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0),
    (0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 1.0)
    ))

# ==================================================================MAIN
@profiler(PROFILE_MODE)
def ImportIA(filepath, verbose, pgrh):
    """ str * context.window_manager
    -> str or NoneType"""
    pgrh.update(0, "Opening file") 
    
    v0 = verbose > 0
    v1 = verbose > 1
    v2 = verbose > 2
    
    
    # Open the file for reading ia data
    with open(filepath, 'rb') as file:
        file.seek(0) # start of file
        
        #FS = FSInterface(IAF.IAFHeader,
        #                 IAF.IAAnimationNode,
        #                 IAF.IAMotionController,
        #                 IAF.IAMotionSet)
        
        header = IAF.IAFHeader.load(file)
        if v0:
            header.dump_log()
        AnimationNodeCount = header.mNumAnimationNodes
        
        pgrh.update(10, "Reading Animations...") 
        
        AnimationNodes = []
        for i in range(AnimationNodeCount):
            a_node = IAF.IAAnimationNode.load(file)
            AnimationNodes.append(a_node)
            if v0:
                a_node.dump_log(i+1, AnimationNodeCount, file.tell()-len(a_node), v2)
            
        MotionControllers = []
        for a_node in AnimationNodes:
            file.seek(a_node.mMotionControllers)
            
            a_node.mMotionControllers = []
            for i in range(a_node.mNumControllers):
                mc = IAF.IAMotionController.load(file)
                a_node.mMotionControllers.append( mc )
                if v1:
                    mc.dump_log(i+1, a_node.mNumControllers, file.tell()-len(mc))
            
            MotionControllers += a_node.mMotionControllers
        
        pgrh.update(20, "Reading keyframes")
        
        for motion_ctrler in MotionControllers:
            file.seek(motion_ctrler.mKeyStream)
            
            if motion_ctrler.mControllerType == 0:
                motion_ctrler.mKeyStream = [
                    IAF.IAMotionVector4Frame.load(file) 
                    for _ in range(header.mTotalFrames)
                    ]
            else:
                motion_ctrler.mKeyStream = [
                    IAF.IAMotionQuaternionFrame.load(file)
                    for _ in range(header.mTotalFrames)
                    ]
                    
    pgrh.update(50, "Ensuring required items") 
    scene = bpy.context.scene
    
    #multiply fps to be able to render subframe-sampling
    frame_multi = scene.render.fps / header.mSampleRate
    if frame_multi != 1:
        scene.render.fps_base = frame_multi
    
    name_to_ob = {a.mName.decode(*IAF.STRING_ENCODING) : scene.objects.get(a.mName.decode(*IAF.STRING_ENCODING), None) 
                  for a in AnimationNodes}
    default_armature_name = os.path.basename(filepath)
    
    #resolve missing objects and bones
    for name, ob in name_to_ob.items():
        if ob is None:
            if "1_" == name[0:2]: #missing object
                new_obj = bpy.data.objects.new(name, None)
                scene.collection.objects.link(new_obj)
                name_to_ob[name] = new_obj
                if v1:
                    print(f"object {name} created")
                
            else: #find bone
                bone = None
                for armature in scene.objects:
                    if armature.type != 'ARMATURE':
                        continue
                    bone = armature.pose.bones.get(name, None)
                    
                    if bone:
                        name_to_ob[name] = bone
                        if v1:
                            print(f"bone {name} found")
                        break
                    
                if bone is None:#not found create new bone
                    if default_armature_name in scene.objects:
                        default_armat = scene.objects[default_armature_name]
                        
                    else:#and a new armature, since we don't already have one
                        armat = bpy.data.armatures.new(default_armature_name)
                        default_armat = bpy.data.objects.new(default_armature_name, armat)
                        scene.collection.objects.link(default_armat)
                    
                    default_armat.select_set(True)
                    bpy.context.view_layer.objects.active = default_armat
                    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                    
                    edit_bone = default_armat.data.edit_bones.new(name)
                    edit_bone.head = (0.0, 0.0, 0.0)
                    edit_bone.tail = (0.0, 0.0, 0.3)
                    
                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
                    default_armat.select_set(False)
                    
                    name_to_ob[name] = default_armat.pose.bones[name]
                    if v1:
                        print(f"bone {name} created")
                    
                 
    pgrh.update(75, "Registering keyframes")   
    
    for a_node in AnimationNodes:
        bl_posebone_or_ob = name_to_ob[a_node.mName.decode(*IAF.STRING_ENCODING)]#get obj
        #drop lods but not bones!:
        if type(ob) is bpy.types.Object and bl_posebone_or_ob.name[0] != '1':
            continue
        bl_posebone_or_ob.rotation_mode = 'QUATERNION'
        if v1:
            print(f"Adding KF {bl_posebone_or_ob.name}...")
        for mctrl in a_node.mMotionControllers:#there should only be 2...
            #get transformation to apply
            mtx = get_matrix(bl_posebone_or_ob)
            if mctrl.mControllerType == 0:
                #get transform vect
                for frame in range(1, header.mTotalFrames):
                    bl_posebone_or_ob.location = mtx @ mctrl.mKeyStream[frame].vect.xyz
                    bl_posebone_or_ob.keyframe_insert(data_path="location", frame=frame)
                    if v2:
                        print(f"  location at frame {frame}...")
                    
            else:
                #get quaternion
                mtxquat = mtx.to_quaternion()
                for frame in range(header.mTotalFrames):
                    #swizzled on load, no need to redo it here
                    bl_posebone_or_ob.rotation_quaternion = mtxquat @ mctrl.mKeyStream[frame].quater
                    #bl_posebone_or_ob.rotation_quaternion.rotate(le quater que je veux)
                    bl_posebone_or_ob.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                    if v2:
                        print(f"  rotation at frame {frame}...")
    
    pgrh.update(100, "Done!")
    
    return 'FINISHED' or None

def get_matrix(ob):
    if type(ob) is bpy.types.Object: 
        #is a regular group
        MyMatrix = Matrix.Identity(4)
        
    else: 
        #is a bone
        if ob.parent:
            MyMatrix = ob.bone.matrix_local.inverted() @ ob.id_data.matrix_world @ ob.bone.parent.matrix_local
        else:
            MyMatrix = ob.id_data.matrix_world @ ob.bone.matrix_local.inverted()
            
    return MyMatrix
