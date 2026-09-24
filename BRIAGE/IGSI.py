# ##### BEGIN LICENSE BLOCK #####
#
# Copyright (C) 2024 'Juju49'(MERLE-RÉMOND Julian)
# see license notes __init__.py
#
# ##### END LICENSE BLOCK #####

#====================================================================INFO
"""submodule for importing IGS files:  
    mthd: ImportIGS(ctx, file)
    file is a filepath"""

_info = {
    "version" : (1, 1, "201dev")} #add "dev" to the last version number to trigger verbose and profiler, example "dev123"

IGSI_VERSION = 'IGSI V' + '.'.join(str(i) for i in _info['version'])

#====================================================================IMPORTS
import bpy
import bmesh
import os
from .Utilityfcts import profiler

from mathutils import Vector, Euler
from math import radians

from ._datastructs.IGF import *  # @UnusedWildImport

#====================================================================GLOBALS
PROFILE_MODE = "dev" in _info['version'][2]

EXTENSIONS = ('.dds', '', '.png', '.jpg', '.jpeg', '.tga', '.bmp', '.ace')

#matrix to transform vectors from TS instance local space
TS_MATRIX = Matrix((
    (1.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0),
    (0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 1.0)
    ))


# ==================================================================TOOLS

class OffsetJump():
    def __init__(self, file, jump_to):
        self.file = file
        self.jump_to = jump_to
        self.jump_from = 0
        
    def __enter__(self):
        self.jump_from = self.file.tell()
        self.file.seek(self.jump_to)
        return self.jump_to
    
    def __exit__(self, e_type, e_value, e_traceback):  # @UnusedVariable
        self.file.seek(self.jump_from)
    

# ==================================================================MAIN
@profiler(PROFILE_MODE)
def ImportIGS(filepath, verbose, pgrh):
    """ str * int * context.window_manager
    -> str or NoneType"""

    pgrh.update(0, "Reading file") 
    assert os.path.isfile(filepath), "not a file!"
    # Current  directory name
    current_directory = os.path.dirname(filepath)
    # Current file name
    current_file_name = os.path.basename(filepath)
    # Name without suffix
    filename_strip = os.path.splitext(current_file_name)[0]
    
    with open(filepath, 'rb') as file:
        try:
            if verbose > 3:
                from contextlib import redirect_stdout
                with open(filepath+".importlog", 'w') as log:
                    with redirect_stdout(log):
                        offsetIG = file_to_dict(file, verbose)
                
                
            else:
                offsetIG = file_to_dict(file, verbose)
            
        except struct.error as se:
            bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR', # @UndefinedVariable
                message=f" Invalid data"
                )
            import traceback
            print(se, traceback.format_exc())
            return 'ERROR'
        
        except RuntimeError as r:
            bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR', # @UndefinedVariable
                message=f" Not an IGS file: '{r}'"
                )
            return 'ERROR'
    
    if verbose > 3:
        pgrh.update(100, "Done!")
        return 'FINISHED'
    
    offsetBlenderPtr = dict()
    
    #order of importation:
    #materials
    #armatures
    #instances and follow indirections to complete objects
    #GSCItems
    #stop there since the rest is unused
    
    header = offsetIG[0]
    
    if b'Exported by 3DCrafter' in header.mCommentField:
        bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='WARNING', # @UndefinedVariable
            message=" This file was made by 3DCrafter: integrity of materials and quads will be compromised. Proceed with caution."
            )
    else:
        bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='PROPERTY', # @UndefinedVariable
            message=" File comment: '"+header.mCommentField.decode(*STRING_ENCODING)+"'"
            )
    
    pgrh.update(25, "Importing materials")
    #allows reduction of the "for" block to improve readability
    where_data_is = (
        header.mMaterials, 
        header.mMaterials + header.mNumMaterials * MATERIAL_SIZE, 
        MATERIAL_SIZE
        )
    #search only in this export frame and not on whole blender scene.
    #This allows to re import aces if they changed for example.
    already_imported_textures = dict()
    for o in range(*where_data_is):
        offsetBlenderPtr[o] = create_BLmtl(offsetIG, o, already_imported_textures, current_directory)
    
    pgrh.update(40, "Importing bones")
    if header.mNumBones:
        offsetBlenderPtr["bones"] = create_BLbones(offsetIG, offsetBlenderPtr, filename_strip)
    
    pgrh.update(55, "Importing Objects")
    where_data_is = (
        header.mInstances, 
        header.mInstances + header.mNumInstances * INSTANCE_SIZE, 
        INSTANCE_SIZE
        )
    #only top lods with no parents
    instances_left_to_process = {
        IGinst for IGinst in range(*where_data_is) 
        if not offsetIG[IGinst].mParent}
    ressolve_lods = set()
    ob_imported = set()
    while instances_left_to_process:
        IGinst_offset = instances_left_to_process.pop()
        
        new_ob, child_IGinst = create_BLobject_geometry_instances(
            offsetIG, 
            offsetBlenderPtr, 
            IGinst_offset
            )
        instances_left_to_process |= child_IGinst
        offsetBlenderPtr[IGinst_offset] = new_ob
        ob_imported.add(new_ob)
        if new_ob.name[0] != '1':
            ressolve_lods.add(new_ob)
    
    #resolve old lod hierarchies
    for new_ob in ressolve_lods:
        lod, dist, name = new_ob.name.split('_', maxsplit=2)  # @UnusedVariable
        if (not new_ob.parent):
            for parent_lod in bpy.data.objects:
                if (parent_lod.name[0] == "1" and 
                    parent_lod.name.endswith(name)
                    ):
                    new_ob.parent = parent_lod
                    new_ob.matrix_world @= new_ob.parent.matrix_world.inverted()
                    #new_ob.matrix_parent_inverse = new_ob.parent.matrix_world.inverted()
                    break
        #top lod is child of another node (the same as us)
        elif new_ob.parent and not new_ob.parent.name.endswith(name):
            for parent_lod in new_ob.parent.children:
                if (parent_lod.name[0] == "1" and 
                    parent_lod.name.endswith(name)
                    ):
                    new_ob.parent = parent_lod
                    new_ob.matrix_world @= new_ob.parent.matrix_world.inverted()
                    #new_ob.matrix_parent_inverse = new_ob.parent.matrix_world.inverted()
                    break
                
    pgrh.update(90, "Importing Snap points")
    if header.mNumGenericItems:
        where_data_is = (
            header.mGenericItems, 
            header.mGenericItems + header.mNumGenericItems * GSCITEMS_SIZE, 
            GSCITEMS_SIZE
            )
        for IGgsc in range(*where_data_is):
            offsetBlenderPtr[IGgsc] = create_BLobject_GSC(offsetIG, offsetBlenderPtr, IGgsc)
    
    #update materials:
    scene = bpy.context.scene
    from .Bl_mtl280 import bind_mat
    for ob in ob_imported:
        for mat in ob.material_slots:
            bind_mat(scene, mat.material)
    
    #needs to be done after material else, if a name is the same as a removed material,
    #it crashes with a RefError
    bpy.context.view_layer.update()
    
    #clean data
    for ob in offsetIG:
        del ob
        
    del offsetIG
    del offsetBlenderPtr
    del header
    
    pgrh.update(100, "Done!")
    return 'FINISHED'

# ==================================================================FILE
def file_to_dict(file, verbose=-1):
    """file -> dict
        returns the content of IGS file as dict of offsets
        containing IGclasses
    """
    final_datablocks_count = 0

    offset_ctn = dict()
    offset = 0
    
    header = IGHeader.load(file)
    
    if header.mMagic != b'KIGF':
        raise RuntimeError("Invalid Magic code")
    if header.mVersion != 151:
        raise RuntimeError(f"Incorrect version {header.mVersion}, should be 151")
    
    offset_ctn[0] = header
    offset += HEADER_SIZE
    
    final_datablocks_count += header.mExtraDataNumBlocks
    EDBl_start_offset = header.DataPtr
    
    #verbosity levels:
    v0 = verbose > 0
    v1 = verbose > 1
    v2 = verbose > 2
    
    if v0:
        header.dump_log(v1)
    
    #order of importation:
    #materials
    #armatures
    #instances and follow indirections to complete objects
    #GSCItems
    #stop there since the rest is unused
    
    
    
    if header.mNumMaterials:
        file.seek(header.mMaterials)
        offset = header.mMaterials
        
        for i in range(header.mNumMaterials):
            #print(f"material {offset}")
            mtl = IGMaterials.load(file)
            if v0:
                mtl.dump_log(i+1, header.mNumMaterials, offset, v1)
            offset_ctn[offset] = mtl
            offset += MATERIAL_SIZE

            final_datablocks_count += mtl.mExtraData.NumBlocks
    
    if header.mNumBones:
        file.seek(header.mBones)
        offset = header.mBones

        for i in range(header.mNumBones):
            #print(f"bone {offset}")
            bone = IGBone.load(file)
            if v1:
                bone.dump_log(i+1, header.mNumBones, offset)
            offset_ctn[offset] = bone
            offset += BONE_SIZE
            
            final_datablocks_count += bone.mExtraData.NumBlocks
    
    if header.mNumInstances:
        file.seek(header.mInstances)
        offset = header.mInstances
        
        LOD_count = 0
        
        for i in range(header.mNumInstances):
            #print(f"instance {offset}")
            new_IGInstance = IGInstance.load(file)
            if v1:
                new_IGInstance.dump_log(i+1, header.mNumInstances, offset)
            offset_ctn[offset] = new_IGInstance
            offset += INSTANCE_SIZE
            
            final_datablocks_count += new_IGInstance.mExtraData.NumBlocks
            LOD_count += new_IGInstance.mNumLODs

    if header.mNumGeometry:
        file.seek(header.mGeometry)
        offset = header.mGeometry

        for i in range(header.mNumGeometry):
            #print(f"mesh {offset}")
            new_geometry = IGGeom.load(file)
            if v1:
                new_geometry.dump_log(i+1, header.mNumGeometry, offset)
            offset_ctn[offset] = new_geometry
            offset += GEOM_SIZE

            final_datablocks_count += new_geometry.mExtraData.NumBlocks

            #seek its vertices
            vertices_count = new_geometry.mNumVertices
            with OffsetJump(file, new_geometry.mVertices) as j_offset:
                for j in range(vertices_count):
                    #print(f" vertex {j_offset}")
                    if not j_offset in offset_ctn:
                        vertex = IGVertex.load(file)
                        if v2:
                            vertex.dump_log(j+1, vertices_count, j_offset)
                        offset_ctn[j_offset] = vertex
                        final_datablocks_count += vertex.mExtraData.NumBlocks
                    else:
                        #print(f"   >skipped")
                        file.seek(VERTEX_SIZE, 1)
                    j_offset += VERTEX_SIZE
            
            #seek its triangles
            triangles_count = new_geometry.mNumTriangles
            assert triangles_count > 0, "no triangles?! wtf!"
            with OffsetJump(file, new_geometry.mTriangles) as j_offset:
                for j in range(triangles_count):
                    #print(f" triangle {j_offset}")
                    if not j_offset in offset_ctn:
                        tris = IGTriangle.load(file)
                        if v2:
                            tris.dump_log(j+1, triangles_count, j_offset)
                        offset_ctn[j_offset] = tris
                        final_datablocks_count += tris.mExtraData.NumBlocks
                    else:
                        #print(f"   >skipped")
                        file.seek(TRIANGLE_SIZE, 1)
                    j_offset += TRIANGLE_SIZE
        
        #after meshes, we find meshLODs
        for i in range(LOD_count):
            new_LOD = IGGeometryLOD.load(file)
            if v2:
                new_LOD.dump_log(i+1, LOD_count, offset)
            offset_ctn[offset] = new_LOD
            offset += GEOMLOD_SIZE 

            final_datablocks_count +=  new_LOD.mExtraData.NumBlocks
                

    if header.mNumGenericItems:
        file.seek(header.mGenericItems)
        offset = header.mGenericItems
        
        for i in range(header.mNumGenericItems):
            GSCItem = IGGenericSceneItem.load(file)
            if v1:
                GSCItem.dump_log(i+1, header.mNumGenericItems, offset)
            offset_ctn[offset] = GSCItem
            offset += GSCITEMS_SIZE
            
            final_datablocks_count += GSCItem.mData.mExtraData.NumBlocks

    
    #there always are for textures a least
    file.seek(EDBl_start_offset)
    offset = EDBl_start_offset
    
    for i in range(final_datablocks_count):
        #print(f"datablock {offset}")
        dbl = IGDataBlock.load(file)
        if v1:
            dbl.dump_log(i+1, final_datablocks_count, offset)
        offset_ctn[offset] = dbl
        offset += DATABLOCK_SIZE
        
        with OffsetJump(file, dbl.mData + EDBl_start_offset) as j_offset:
            #print(f" data {j_offset}")
            if dbl.mID == BLOCK_FACE_TAG_DESCS: 
                offset_ctn[j_offset] = IGFaceTagDescription.load(file)
                if v1:
                    offset_ctn[j_offset].dump_log(j_offset)
                
            elif dbl.mID == BLOCK_TEXTURE_NAMES:
                textures = IGTextureNames.load(file)
                offset_ctn[j_offset] = textures
                offset_ctn['textures'] = textures #for easy finding later on
                if v0:
                    textures.dump_log(j_offset)
    
    return offset_ctn


def create_image_from_ace(filepath, verbose=-1, save=False):
    """str * int -> bpy.types.Image
    Import an ACE texture to blender
    filepath is assumed valid"""
    from ._datastructs import SACE
    
    #specs from OR project
    
    #open ACE texture
    with open(filepath, 'rb') as file:
        buffer = file.read(16)
        data1 = struct.unpack("<8sI4s", buffer)
        data2 = struct.unpack("<8s8s", buffer)
        import io
        if data1[0] == b"SIMISA@F" and data1[2] == b"@@@@":
            buffer = file.read(2)
            data, = struct.unpack("<H", buffer) #Uint16 (a short)
            if data & 0x20FF != 0x0078:
                raise RuntimeError(f"SACE: Invalid compression {data1[1]} at {filepath}")
            
            import zlib
            with io.BytesIO(zlib.decompress(file.read(data1[1]), -15)) as deflated:
                ace_file = SACE.Header.load(deflated)
            
        elif data2[0] == b"SIMISA@@" and data2[1] == b"@@@@@@@@":
            with io.BytesIO( file.read() ) as data:
                ace_file = SACE.Header.load(data)
        else:
            raise RuntimeError(f"SACE: Invalid signature {data2[0]}{data2[1]} at {filepath}")
        
    #debug option
    print(f"SACE: Imported {filepath}")
    if verbose > 0:
        ace_file.dump_log(verbose)
        
    #create BL image
    img = bpy.data.images.new(
        os.path.basename(filepath), 
        width=ace_file.width, 
        height=ace_file.height,
        alpha=True,
        )
    #img.source = 'FILE' #must not be set or Bl tries to reload.. and it will fail obviously
    img.filepath_raw = filepath[:-3]+"png" #for easy unpack
    img.file_format = 'PNG'
    
    img.pixels = ace_file.offset_table[0]
    
    if save:
        img.save() #save outside immediately for batch conversions
    else:
        img.pack() #save in blend file
    
    return img

# ==================================================================DATA TRANSFERT
def create_BLmtl(
        offsetIG:dict, 
        offset:int, 
        already_imported_textures:dict, 
        current_directory:str
        ):
    """dict * int * str -> Material
    Creates and populates Blender material from IG data"""
    
    IGcls = offsetIG[offset]
    
    bl_mtl = bpy.data.materials.new(name=IGcls.mName.decode(*STRING_ENCODING))
    bl_igs = bl_mtl.IgsMat

    #set shader
    from . Bl_data import SHADERS_LIST
    shader = IGcls.mShaderName.decode(*STRING_ENCODING)
    is_regular_shader = shader in SHADERS_LIST
    
    #print(shader, is_regular_shader)
    #print(SHADERS_LIST)
    
    if is_regular_shader:
        bl_igs.shader_name = shader
    else:
        bl_igs.shader_name = 'custom'
        bl_igs.shader_name_string = shader
        
    bl_igs.ambient_color = *IGcls.mAmbient, #',' to tuple values
    bl_igs.diffuse_color = *IGcls.mDiffuse, #',' to tuple values
    bl_igs.emissive_color = *IGcls.mEmissive, #',' to tuple values
    bl_igs.specular_color = *IGcls.mSpecular, #',' to tuple values
    bl_igs.specular_power = IGcls.mSpecularPower
    bl_igs.emissive_power = IGcls.mEmissiveStrength
    
    bl_igs.alpha_test_mode = bool(IGcls.mAlphaTestMode)
    bl_igs.z_buffer_mode = str(IGcls.mZBufferMode) #str() because this is an enum!
    bl_igs.back_face_cull = bool(IGcls.mBackfaceCull)
    bl_igs.two_sided = bool(IGcls.mTwoSided)
    bl_igs.vis_mod = IGcls.mVisMod
    bl_igs.z_bias = IGcls.mZBias
    bl_igs.use_cast_shadows = bool(IGcls.mLMCastShadows)
    bl_igs.unlit = bool(IGcls.mLMKeepVertexColours)
    bl_igs.comment_field = IGcls.mComment.decode(*STRING_ENCODING)
    
    bl_igs['view_facing'] = IGcls.mViewFacing #[]: this is an enum!
    #print(f"{bl_mtl.name}:")
    
    #print("mNumRenderStages: ",  IGcls.mNumRenderStages)
    #print("numSlots:", len(bl_igs.textures))
    for i,rs in enumerate(IGcls.IGRenderS):
        #rs.dump_log(True, i)
        #texture_num = rs.mTextureName
        #TS never reads it and just proceeds happily...
        texture_path_from_igs = offsetIG['textures'].ListOfStrings.pop(0).decode(*STRING_ENCODING)
        texture_from_blend = current_directory + '\\' + texture_path_from_igs
        #print(f"  [{i}] = {texture_path_from_igs}")
        
        if ('WeatherEffects' in shader) and (i == 1):
            continue #skip it, it is auto-set in blender export and is therefore not present
        #mask if invisible
        if is_regular_shader and SHADERS_LIST[shader][1] == 0:
            texture_path_from_igs = ''
        
        if len(texture_path_from_igs) : #fake path for invisible materials
            #try for each extension possible as they are not stored in IGS files
            for ext in EXTENSIONS:
                if os.path.isfile(texture_from_blend+ext):
                    texture_from_blend += ext
                    tex_name = os.path.basename(texture_from_blend)
                    #test if it already exists
                    if tex_name in already_imported_textures:
                        new_img = already_imported_textures[tex_name]
                    #if its an ace file, we create it
                    elif ext == '.ace':
                        #add try to pass butchered up SACE files
                        try:
                            new_img = create_image_from_ace(texture_from_blend)
                            already_imported_textures[tex_name] = new_img
                        except (RuntimeError, NotImplementedError) as e:
                            print(f"SACE: Import failed {texture_from_blend}")
                            if PROFILE_MODE:
                                import traceback
                                print(e, traceback.format_exc())
                            else:
                                print(e)
                            continue #as ACE is last format, it will trigger the "else" statement
                    #in other cases, blender can manage
                    else:
                        new_img = bpy.data.images.load(texture_from_blend, check_existing=True)
                        already_imported_textures[tex_name] = new_img
                    break
            else:#Nothing was found
                #import dummy texture, or the same if used elsewhere in IGS
                tex_name = os.path.basename(texture_path_from_igs)
                if tex_name in already_imported_textures:
                    new_img = already_imported_textures[tex_name]
                else:
                    # but keep filepath for user to know where to search
                    new_img = bpy.data.images.new(texture_path_from_igs, width=8, height=8)
                    already_imported_textures[tex_name] = new_img
            
            #textures must be added manually for non listed shaders:
            if not is_regular_shader:
                bl_igs.textures.add() #FIXED: Some bug at Oystein's here
            if ('WeatherEffects' in shader) and (i > 1):
                i -= 1
                
            #dec2020: clamp max i to max shader texture length. Wrong results come from 3DC were the first texture may be duplicated for some reason
            if i >= len(bl_igs.textures):
                i = len(bl_igs.textures)-1
                
            #fill in texture settings
            bl_igs.textures[i].texture = new_img
            bl_igs.textures[i].uv_layer= str(rs.mUVChannelIndex)
            #Set this to avoid complex re-export when to much textures
            # have been used:
            bl_igs.textures[i].use_source_tex_file_path = True
        
        #BRIAGE only cares for first pass mostly. so intel is found
        # in the 1rst slot to populate material attributes:
        if i == 0:
            bl_igs.uv_param_1, bl_igs.uv_param_2, bl_igs.uv_param_3, \
            bl_igs.uv_param_4, bl_igs.uv_param_5, bl_igs.uv_param_6  \
            = rs.mArguments
            
            bl_igs.animate_uv = bool(rs.mAnimateUVs)
            bl_igs.num_frames = rs.mNumFrames
            bl_igs.f_p_s = rs.mFPS
            
            bl_igs.uv_scroll = bool(rs.mScrollUVs)
            bl_igs.scroll_u = rs.mScrollU
            bl_igs.scroll_v = rs.mScrollV
            
            try:
                bl_igs.filter_mode = str(rs.mFilterMode) #str: this is an enum!
            except:
                bl_igs.filter_mode = "1"
            bl_igs.mip_lod_bias = rs.mMipLODBias
    
    #do things "Update" functions of properties can't do due to lack of context:
    fxShader = '.fx' in shader
    if fxShader:
        bl_mtl.use_backface_culling = not bl_igs.two_sided
    else:
        bl_mtl.use_backface_culling = bl_igs.back_face_cull
    bl_mtl.blend_method = 'BLEND'
    
    return bl_mtl

def create_BLbones(offsetIG:dict, offsetBlenderPtr:dict, default_armature_name:str):
    scene = bpy.context.scene
    armat = bpy.data.armatures.new(default_armature_name)
    default_armat = bpy.data.objects.new(default_armature_name, armat)
    scene.collection.objects.link(default_armat)
    
    default_armat.select_set(True)
    bpy.context.view_layer.objects.active = default_armat
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    edit_bones = default_armat.data.edit_bones
    
    base_bone_tail_direction = Vector((0.0, 0.1, 0.0))
    def create_a_bone(IG_bone, parent_bl_bone=None):
        bone_name = IG_bone.mName.decode(*STRING_ENCODING)
        
        new_edit_bone = edit_bones.new( bone_name )
        
        #new_edit_bone.layers[0] = True
        new_edit_bone.use_deform = True
        new_edit_bone.use_inherit_rotation = True
        new_edit_bone.use_local_location = True
        
        new_edit_bone.tail = base_bone_tail_direction #if not set, shits on matrix..
        new_edit_bone.parent = parent_bl_bone
        
        #TODO: ? max armatures have to be local_x+90° rotated to match... apply it at the risk of 
        # breaking re-exporting to IA files?
        
        my_matrix = (TS_MATRIX @ IG_bone.mTM.M @ TS_MATRIX).transposed()# @ Matrix.Rotation(radians(-90.0), 4, 'Z')
        if parent_bl_bone:
            pmatrix = parent_bl_bone.matrix
            new_edit_bone.matrix =  pmatrix @ my_matrix # pmatrix @ Matrix.Rotation(radians(90.0), 4, 'Z') @ my_matrix
        else:
            new_edit_bone.matrix = my_matrix
            
        #print(new_edit_bone.name)
        #print(new_edit_bone.matrix)

        #only pull tail to first child
        tail_pulled = False
        for b_child in IG_bone.mChildren: #register children
            #skip invalid bone (if any exists)
            if not isinstance(offsetIG[b_child], IGBone):
                bpy.ops.igs_err.damned('EXEC_DEFAULT', type='ERROR', # @UndefinedVariable
                    message=" Bone child is not a bone! Bone '{0}' looking for '{1}'".format(IG_bone.mName.decode(*STRING_ENCODING), b_child)
                    ) 
                continue
            child = offsetIG[b_child]
            #save it there to find it back from boneBindings
            offsetBlenderPtr[b_child] = (
                child.mName.decode(*STRING_ENCODING), #name separated because stored name generates UTF errors...
                create_a_bone(child, new_edit_bone),
                )
            
            if not tail_pulled:
                #new_edit_bone.tail = offsetBlenderPtr[b_child][1].head
                #we just want to extend it as mush as possible:
                l = (new_edit_bone.head - offsetBlenderPtr[b_child][1].head).length
                new_edit_bone.length = abs(l)
                #above op return the len of "=":  armat_origin------->chd_head======>my_head
                tail_pulled = True
                
        return new_edit_bone
    
    for o in range( offsetIG[0].mBones, 
                    offsetIG[0].mBones + offsetIG[0].mNumBones * len(IGBone), 
                    len(IGBone) 
                    ):
        bone = offsetIG[o]
        if (not bone.mParent) or not isinstance(offsetIG[bone.mParent], IGBone):
            #parent is none or not a bone
            offsetBlenderPtr[o] = (
                bone.mName.decode(*STRING_ENCODING),
                create_a_bone(bone),
                )
            if bone.mParent and not isinstance(offsetIG[bone.mParent], IGBone):
                bpy.ops.igs_err.damned('EXEC_DEFAULT', type='ERROR', # @UndefinedVariable
                    message=" Bone parent is not a bone! Bone '{0}' looking for '{1}'".format(bone.mName.decode(*STRING_ENCODING), bone.mParent)
                    )
    
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    default_armat.select_set(False)
    
    return default_armat


def create_BLmesh(offsetIG:dict, offsetBlenderPtr:dict, IG_mesh_ptr:int, world_tm:Matrix):
    if IG_mesh_ptr in offsetBlenderPtr:
        return offsetBlenderPtr[IG_mesh_ptr]
    #IGGeom instance from offset
    IG_mesh = offsetIG[IG_mesh_ptr]
    
    #init mesh
    bl_mesh = bpy.data.meshes.new(str(IG_mesh_ptr))

    # Set smooth shading and initialize custom vertex normals
    bl_mesh.normals_split_custom_set_from_vertices([(0,0,1)] * len(bl_mesh.vertices))

    bl_mesh.shade_smooth()
    
    #create arrays:
    bm = bmesh.new()
    layers = bm.loops.layers
    vertice_normal = []
    
    #init deform if needed
    skinning_actived = bool (IG_mesh.mIsSkinned )
    if skinning_actived:
        bm.verts.layers.deform.verify()
        vg = bm.verts.layers.deform.active
        vg_indexes = dict()
        for i, bone in enumerate( offsetBlenderPtr["bones"].data.bones ):
            vg_indexes[bone.name] = i
    v_c = layers.color.new("vCol")
    
    most_uv_encountered = 1 #count uvs to generate right uv layers number
    local_vertices_offsets = dict()
    for o in range(
        IG_mesh.mVertices, 
        IG_mesh.mVertices + IG_mesh.mNumVertices * len(IGVertex), 
        len(IGVertex) 
        ):
        #get IG instance and create Bl instance
        Vert = offsetIG[o]
        bl_v = bm.verts.new( (Vert.mPoint.x, Vert.mPoint.y, Vert.mPoint.z) )
        #Vert.dump_log(Vert.mReserved,-1,o)
        
        #count UVs for later layer creation
        if Vert.mNumValidUVs > most_uv_encountered:
            most_uv_encountered = Vert.mNumValidUVs
            
        #get weights for bones
        if skinning_actived and Vert.mNumBones:  
            for bone_binding in Vert.mBoneBinding:
                bone_name = offsetBlenderPtr[bone_binding.mBone][0]
                if bone_binding.mWeight: #jump 0.0 ones (why even added?!)
                    try:
                        bl_v[vg][vg_indexes[bone_name]] = bone_binding.mWeight
                    except KeyError as r:
                        print("vg_indexes : "+ repr(vg_indexes))
                        raise(r)
            
        local_vertices_offsets[o] = bl_v
        
        #save as split normal to avoid overriding by blender
        nm = Vert.mNormal
        bl_v.normal = (nm.x, nm.z, nm.y)
        #since this will be applied after TS_MATRIX, we must swizzle
        #right away to avoid weird stuff
        vertice_normal.append( (nm.x, nm.z, nm.y) )
    uv = [layers.uv.new(str(i)) for i in range(most_uv_encountered) ]
    
    local_tris_vertice_keys = dict()
    for o in range(
        IG_mesh.mTriangles, 
        IG_mesh.mTriangles + IG_mesh.mNumTriangles * len(IGTriangle), 
        len(IGTriangle) 
        ):
        #get IG triangle
        IGtri = offsetIG[o]
        v_list = [local_vertices_offsets[o] for o in IGtri.mVertices]
        
        
        vertice_key = frozenset( v_list )
        #filter invalid tris:
        if len(vertice_key) != 3:
            continue
        #filter duplicate faces:
        if vertice_key in local_tris_vertice_keys:
            continue
        
        
        
        #create bl face:
        tri = bm.faces.new( v_list ) #don't use vertice_key, else loops not aligned
        local_tris_vertice_keys[vertice_key] = tri
        loops = tri.loops
        
        #assign material
        #get id for material of face
        bl_mtl = offsetBlenderPtr[IGtri.mMaterial]
        bl_mtl_idx = bl_mesh.materials.find(bl_mtl.name)
        if bl_mtl_idx == -1:
            #append new material to the end of material array
            bl_mtl_idx = len(bl_mesh.materials)
            bl_mesh.materials.append(bl_mtl)
        tri.material_index = bl_mtl_idx
        
        #deal with normal
        trinorm = IGtri.mNormal
        tri.normal = (trinorm.x, trinorm.y, trinorm.z)
        tri.smooth = True
        
        
        #tag hidden edges for dissolution:
        hide_edges = IGtri.mHiddenEdges
        #check if edge is hidden and edge is manifold for fusion
        #dec2020: edges could have been tagged from some other operation, 
        # it also un-tags edges marked from only one side on some occasions, quite useful...
        if hide_edges & EDGE_V0_V1_HIDDEN and len(loops[0].edge.link_faces) == 2:
            loops[0].edge.tag = True
        else:
            loops[0].edge.tag = False
        if hide_edges & EDGE_V1_V2_HIDDEN and len(loops[1].edge.link_faces) == 2:
            loops[1].edge.tag = True
        else:
            loops[1].edge.tag = False
        if hide_edges & EDGE_V2_V3_HIDDEN and len(loops[2].edge.link_faces) == 2:
            loops[2].edge.tag = True
        else:
            loops[2].edge.tag = False
        
        for cur_loop, v_idx in zip( loops, IGtri.mVertices ):
            Vert = offsetIG[v_idx]
            #Get UVs
            for i, IGuv in enumerate(Vert.mUV):
                cur_loop[uv[i]].uv = (IGuv.u, 1 - IGuv.v)
            
            #Get Vertex colours
            cur_loop[v_c] = *Vert.mColour,
            
        # Reconstruct quads by dissolving hidden diagonal edges in a single batch operation.
    #find quads from hidden edges as quads:
    # Batch-dissolve hidden diagonal edges to reconstruct quads.
    edges_to_dissolve = [e for e in bm.edges if e.tag and len(e.link_faces) == 2]
    if edges_to_dissolve:
        bmesh.ops.dissolve_edges(bm, edges=edges_to_dissolve, use_verts=False)
    
    matrix = (TS_MATRIX @ world_tm).inverted()
    bm.transform( matrix )
    
    bm.to_mesh(bl_mesh)
    bm.free()
    
    try:
        # Limit the custom normal array to the actual number of vertices.
        bl_mesh.normals_split_custom_set_from_vertices(vertice_normal[:len(bl_mesh.vertices)])
    except RuntimeError:
        print(f"Warning: Custom normals skipped for {bl_mesh.name} due to vertex/normal count mismatch")  
    
    bl_mesh.update()
    return bl_mesh, bool( IG_mesh.mIsSkinned )


def create_BLobject_geometry_instances(offsetIG:dict, offsetBlenderPtr:dict, instance_offset:int ):
    IG_instance = offsetIG[instance_offset]
    
    data, add_armature_modifier = create_BLmesh(
        offsetIG,
        offsetBlenderPtr, 
        offsetIG[IG_instance.mGeometry].pGeometry, 
        Matrix())
        #IG_instance.mTM.M)
    
    new_ob = bpy.data.objects.new(IG_instance.mName.decode(*STRING_ENCODING), data)
    #print(new_ob.name, IG_instance.mParent)
    
    if IG_instance.mParent:
        new_ob.parent = offsetBlenderPtr[IG_instance.mParent]
        
    my_matrix = (TS_MATRIX @ IG_instance.mTM.M @ TS_MATRIX).transposed()
    new_ob.matrix_local = my_matrix
    if new_ob.parent:
        new_ob.matrix_parent_inverse = new_ob.parent.matrix_world.inverted()
    
    #add armature modifier for vertex groups
    if add_armature_modifier:
        for bone in offsetBlenderPtr["bones"].data.bones:
            #will iterate in same order than mesh as of python 3.6
            new_ob.vertex_groups.new(name=bone.name)
        mod = new_ob.modifiers.new('Armature deform', 'ARMATURE')
        mod.object = offsetBlenderPtr["bones"]
        mod.use_vertex_groups = True
    
    child_to_process_later = set()
    for b_child in IG_instance.mChildren: #register children
        #skip invalid GSC inside (if any exists)
        if not isinstance(offsetIG[b_child], IGInstance):
            bpy.ops.igs_err.damned('EXEC_DEFAULT', type='ERROR', # @UndefinedVariable
                message=" Instance child is not an instance! Object '{0}' looking for '{1}'".format(IG_instance.mName.decode(*STRING_ENCODING), b_child)
                ) 
            continue
        
        child_to_process_later.add( b_child )
    
    bpy.context.collection.objects.link(new_ob)
    
    return new_ob, child_to_process_later

def create_BLobject_GSC(offsetIG:dict, offsetBlenderPtr:dict, instance_offset:int ):
    IG_GSCitem = offsetIG[instance_offset]
    
    new_ob = bpy.data.objects.new('#'+IG_GSCitem.mName.decode(*STRING_ENCODING), None)
    if IG_GSCitem.mParent:
        new_ob.parent = offsetBlenderPtr[IG_GSCitem.mParent]
        
    new_ob.matrix_local = (TS_MATRIX @ IG_GSCitem.mTM.M @ TS_MATRIX).transposed()
    
    new_ob.empty_display_size = 0.5
    new_ob.empty_display_type = 'ARROWS'
    
    bpy.context.collection.objects.link(new_ob)
    
    return new_ob