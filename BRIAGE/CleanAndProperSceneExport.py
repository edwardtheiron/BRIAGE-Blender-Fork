# ##### BEGIN LICENSE BLOCK #####
#
# Copyright (C) 2020 'Juju49'(MERLE-RÉMOND Julian)
# see license notes __init__.py
#
# ##### END LICENSE BLOCK #####

#====================================================================INFO
__doc__ = """submodule for building object list and managing context:
    mthd: CleanAndProperSceneExport(Config)
    Config == a class containing 'IgsOpt' or 'IaOpt' and 'context = bpy.context'
    implements context manager"""

#====================================================================IMPORTS
import bpy
import os
import sys
import time

from . Groups import getLOD
from . Bl_data import IAExporterSettings


#====================================================================CONTEXT MANAGER
#MODIFS2017: ensures scene == clean and always returned as ==

class CleanAndProperSceneExport():
    
    def __init__(self, Config=None):
        
        self.is_ia = type(Config) == IAExporterSettings
        self.Config = Config
        
        self._exp_duplicates = []
        self._selection_save = set(bpy.context.selected_objects)  # @UndefinedVariable
        self._outfile = sys.stdout
        self._saveout = sys.stdout
        
        # Start of export
        self.time1 = time.time()
        
    ## export parts ##
    
    def _new_std_out(self):
        ##prepare log file
        if self.Config.Verbose:
            # Current  model directory name
            model_directory = os.path.dirname(bpy.path.abspath(self.Config.FilePath))
            # Current model file name
            model_name = os.path.basename(self.Config.FilePath)
            # Name without suffix
            filename_strip = os.path.splitext(model_name)[0]
            # log filename
            if self.is_ia:
                myLogfile = model_directory + '\\' + filename_strip + '.ia.log'
            else:
                myLogfile = model_directory + '\\' + filename_strip + '.igs.log'
            
            try:
                _outfile = open(myLogfile, 'w', encoding='utf-8', errors='ignore')
            except:
                _outfile = sys.stdout
                bpy.ops.igs_err.damned('EXEC_DEFAULT',type='ERROR', message=" Cannot create log here!")
            else:
                self._saveout, sys.stdout = sys.stdout, _outfile
            
            self._outfile = _outfile
            self._myLogfile = myLogfile
    
    def _restore_std_out(self):
        # restore stdout

        if (self._outfile != self._saveout) and (self.Config.Verbose):
            try:
                self._outfile.flush()
                self._outfile.flush()
                self._outfile.close()
                sys.stdout = self._saveout
            except:
                pass
        
            bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='INFO', 
                message=" Log file created at '{0}'".format(self._myLogfile))


    def _to_exportable(self, ob, tag): #MODIFS2016: macro to export fonts, curves, sufaces, meta without too much problems
        """macro to transform objects in an exportable version if they were not"""
        context = self.Config.context
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True)
        context.view_layer.objects.active = ob
        bpy.ops.object.convert(keep_original=True) #convert to mesh
        ob_mod = context.active_object #remember temp gizmo
        ob_mod.name = "_".join((ob.name, "conv", tag)) #rename
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY') #center origin
        bpy.ops.object.transform_apply(rotation=True, scale=True) #apply rotation and scale
        ob_mod.data.uv_layers.new(name="foobar") #add UV map
        self._exp_duplicates.append(ob_mod.name) #list as temp object
        bpy.ops.igs_err.damned('EXEC_DEFAULT',type='INFO', message=f" object '{ob.name}' has been meshed in obj named: '{ob_mod.name}'!")
        return ob_mod
    
    def _make_dupli(self, dpg, duplicator):
        if (duplicator.instance_type == 'NONE'):
            return []#we care about duplis, others will just crash our stuff!
        
        context = self.Config.context
        
        duplicator.select_set(True)
        duplicator.hide_select = False
        context.view_layer.objects.active = duplicator
        
        instance_type = str(duplicator.instance_type)
        instance_collection = duplicator.instance_collection
        
        
        bpy.ops.object.duplicates_make_real(use_base_parent=True, use_hierarchy=True)
        objects_list = [ob.evaluated_get(dpg) for ob in context.selected_objects if ob != context.active_object]
        #objects_list = [ob for ob in context.selected_objects if ob != context.active_object]
        
        
        if instance_type == 'COLLECTION' and instance_collection:
            #compute prefixes and suffixes
            prefix = ""
            suffix = ""
            d_name = duplicator.name
            offset_to_get_name = 0
            
            print("collection duplicator")
            
            if duplicator.type == 'MESH':
                _, _, d_name = getLOD([], duplicator.name)
                offset_to_get_name = 7 #size of "1_1000_" at the begining of msh obj
                
            if duplicator.name[-1] == '*': #star at the end
                suffix = d_name[offset_to_get_name:-1]
                
            else: #parent_group.name[offset_to_get_name] == '*': #star at the beginning #just do it to avoid confusion
                prefix = d_name[offset_to_get_name:]
                    
#             def _duplicated_list(ob):
#                 dup_objs = set(ob.instance_collection.objects)
#                 for dupli_ob in ob.instance_collection.objects:
#                     if dupli_ob.instance_type == 'COLLECTION' and dupli_ob.instance_collection:
#                         dup_objs.update(_duplicated_list(dupli_ob))
#                 return dup_objs
#             duplicated_objects = _duplicated_list(duplicator)
            #print(duplicated_objects)
            
            #for original in dpg.object_instances:
            for dup in objects_list: #:
                if dup.is_from_instancer and dup.parent == duplicator:  # Real dupli instance
                    original = dup.instance_object
                    print("dupe ", dup)
                    #mat = dup.matrix_world.copy()
                    for dupli in (ob for ob in objects_list if ob.data == original.data):
                        _, _, dupli_name = getLOD(None, dupli.name)
                            
                        #add prefixes and suffixes
                        if dupli.type == 'MESH':
                            dupli_name = dupli_name[:7] + prefix + dupli_name[7:-4] + suffix
                        elif dupli_name[0] == "#":
                            dupli_name = dupli_name[:4] + prefix + dupli_name[4:-4] + suffix
                        else:
                            dupli_name = prefix + dupli_name[:-4] + suffix
                                
                        if dupli.type == 'ARMATURE':
                            for bone in original.data.bones:
                                bone.name =  prefix + bone.name + suffix
                                
                        print("dupe renamed to:", dupli_name)
                                
                        original.name = dupli_name
                        if original.animation_data:
                            print("create anim data...")
                            dupli.animation_data_create()
                            dupli.animation_data.action = original.animation_data.action
                        #bpy.ops.igs_err.damned('EXEC_DEFAULT',type='INFO', 
                        #message=" Dupli '{0}' has been added: '{1}'!".format(dupli.name, duplicator.name))

                
        elif instance_type in {'VERTS', 'FACES'}: #duplicate children
            def __return_children(ob):
                children = []
                for chd in ob.children:
                    children.extend([chd]+__return_children(chd))
                return children

            for original in __return_children(duplicator):
                if original.animation_data:
                    for dupli in (ob for ob in objects_list if dupli.data == original.data):
                        dupli.animation_data_create()
                        dupli.animation_data.action = original.animation_data.action
        
        
        
        self._exp_duplicates.extend([dupli.name for dupli in objects_list])
        duplicator.instance_type = instance_type
        duplicator.instance_collection = instance_collection
        bpy.ops.object.select_all(action='DESELECT')
        return objects_list
    
    
    def _make_object_list(self):
        context = self.Config.context
        
        Config = self.Config
        dpg = Config.dpg
        
        if self.is_ia:
            Config = self.Config.context.scene.IgsOpt
            
        main_object_found = False
        main_obj = None
        main_obj_name = ""
        #
        #creating objects list:
        if Config.use_selection: 
            objects_list = [ob for ob in context.selected_objects]
        else:
            objects_list = [ob for ob in context.visible_objects]
        
        if not objects_list:
            bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='ERROR', message=" No mesh or empty objects found. Export stopped")
            return
        
        vc = Config.visible_children
        sco = set(context.scene.collection.all_objects)
        #add missing children to objects list:
        def _recursive_chd_add(parent, ob_list):
            #recursively search for unselected children to add
            for obj in parent.children:
                if ((obj not in ob_list) and 
                ( not vc or (vc and obj.visible_get(view_layer=context.view_layer)) )
                and obj in sco):
                    #all children OR visible_children and visible in current scene
                    ob_list.append(obj)
                    _recursive_chd_add(obj, ob_list)
                    #visible_children but not visible! => do nothing
            return
        
        if not (self.is_ia and Config.use_selection) or (self.is_ia and self.Config.export_selected_hierarchy) :
            for obj in objects_list[:]:
                _recursive_chd_add(obj, objects_list)
        
        #integrate armatures from modifiers
        if Config.process_bones:
            one_armature_found = False
            for ob in objects_list[:]:
                if ob.type == 'MESH' and len(ob.vertex_groups) != 0:
                    for mod in ob.modifiers:
                        if mod.type == 'ARMATURE' and mod.use_vertex_groups and mod.object and mod.object not in objects_list:
                            if one_armature_found: #there are multiple armatures to be exported, prefix bones
                                #armat = mod.object
                                #for bone in armat.data.bones:
                                #    bone.name = armat.name + "." + bone.name
                                pass
                            objects_list.append(mod.object)
                            one_armature_found = True
        
        #integrate duplis:
        bpy.ops.object.select_all(action='DESELECT')
        for ob in objects_list[:]:
            if ob.instance_type != 'NONE':
                objects_list.extend(self._make_dupli(dpg, ob))

        
        #
        #select main obj:
        if Config.s_main_object == 'actObj':
            if not context.active_object:
                context.view_layer.objects.active = objects_list[0]
                bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='WARNING', message=" No active object selected as main object.")
            main_obj_name = context.active_object.name # Pick active empty or mesh
        else:
            main_obj_name = Config.s_main_object
        
        #MODIFS2016: convert things to meshes if possible (except empties):
        for i, ob in enumerate(objects_list[:]):
            #check objects are meshes except empties:
            if ob.type in {'CURVE', 'FONT', 'SURFACE', 'META'}:
                #convert macro:
                objects_list.remove(ob) #pull out from list
                ob_mod = self._to_exportable(ob, "")
                objects_list.insert(i, ob_mod)#put back in list
        bpy.ops.object.select_all(action='DESELECT')
        #Look for main object:
        bpy.ops.igs_err.damned('EXEC_DEFAULT', type='PROPERTY', message="MainObject to find = {:s}".format(main_obj_name))
        if main_obj_name != "":
            for ob in objects_list:
                if ob.name == main_obj_name:
                    main_object_found = True
                    if ob.type in {'MESH'}:
                        # Put main object at the head of the objects list
                        objects_list.remove(ob)
                        objects_list.insert(0, ob)
                        bpy.ops.igs_err.damned('EXEC_DEFAULT',type='PROPERTY', message=" MainObject found = {:s}".format(ob.name))
                        #print(" MainObject found = {:s}".format(ob.name))
                        main_obj = objects_list[0]
                        break
                    else:
                        bpy.ops.igs_err.damned('EXEC_DEFAULT',type='WARNING', message=" MainObject found = {:s} but it's not a mesh: ignored".format(ob.name))
    
        #
        if main_obj == None:
            if main_obj_name == "":
                bpy.ops.igs_err.damned('EXEC_DEFAULT',type='WARNING', message=" Main object not specified")
            else:
                if not main_object_found:
                    try:
                        bpy.ops.igs_err.damned('EXEC_DEFAULT',type='WARNING', message=" Main object {:s} not found or not visible".format(main_obj_name))
                    except TypeError:
                        bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='WARNING', message=" Main object property enum failure!! Main object not specified")
            for ob in objects_list:
                if ob.type in {'MESH'}:
                    # Take first mesh object found
                    objects_list.remove(ob)
                    objects_list.insert(0, ob)
                    bpy.ops.igs_err.damned('EXEC_DEFAULT',type='PROPERTY', message=" Main object selected = {:s}".format(ob.name))
                    main_obj = objects_list[0]
                    break
#         if main_obj == None and not self.is_ia:
#             bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='ERROR', message=" No mesh or empty objects found. Export stopped")
#             return
        return objects_list
    
    
    
    ##context manager parts##
    
    def __enter__(self):
        self.Config.context.window.cursor_modal_set('WAIT')
        
        #out redirect if logfile
        self._new_std_out()
        
        # check poll() to avoid exception -> Go into object mode to be able to select faces
        if bpy.ops.object.mode_set.poll():  # @UndefinedVariable
            bpy.ops.object.mode_set(mode='OBJECT') 
        
        # Reset objects to start position for any animation
        sc = self.Config.context.scene
        self._current_frame = sc.frame_current
        if not self.is_ia:
            sc.frame_set(0)
        
        ob_l = self._make_object_list()
                
        #check correct ob list
        if ob_l == None:
            self._restore_std_out()
            return
        
        if len(ob_l) == 0:
            bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='ERROR', message=' Nothing was selected or visible')
            self._restore_std_out()
            return
        
        return ob_l
        
    def __exit__(self, e_type, e_value, e_traceback):  # @UnusedVariable
        self.Config.context.window.cursor_modal_restore()
        error_happened_inside = isinstance(e_type, Exception)
        
        self._restore_std_out()
        
        sc = self.Config.context.scene
        if sc: sc.frame_set(self._current_frame) 
        
        #deselect all objects even if they are not visible (bug correct to avoid unwanted deletions)
        #28/10/2018
        for ob in bpy.data.objects:# @UndefinedVariable
            ob.select_set(False)
        
        for ob_name in self._exp_duplicates:
            try:
                bpy.data.objects[ob_name].select_set(True)
            except KeyError:
                continue
            bpy.ops.object.delete()
        self._exp_duplicates = []
        
        if not error_happened_inside:
            # End of export
            if self.is_ia:
                bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='INFO', 
                message=" IA export time: {:.02f}".format(time.time() - self.time1))
            else:
                bpy.ops.igs_err.damned('INVOKE_DEFAULT',type='INFO', 
                message=" IGS export time: {:.02f}".format(time.time() - self.time1))
            
        for ob in bpy.data.objects:  # @UndefinedVariable
            if ob in self._selection_save:
                ob.select_set(True)
            else:
                ob.select_set(False)
        return error_happened_inside
        
    