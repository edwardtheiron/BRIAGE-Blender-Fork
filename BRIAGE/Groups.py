3# ##### BEGIN LICENSE BLOCK #####
#
# Copyright (C) 2024 'Juju49'(MERLE-RÉMOND Julian)
# see license notes __init__.py
#
# ##### END LICENSE BLOCK #####

#====================================================================INFO

#====================================================================IMPORTS
import bpy

from . Bl_data import (
    RESERVED_OBJECT_NAMES,
    RESERVED_OBJECT_NAMES_NB)

#====================================================================GLOBALS
END_OK = 0
END_ERROR = -1
END_WARNING = -2

KEYWORD_OTHER = 0
KEYWORD_CUSTOM = 1

MAX_NAME_WITH_LOD = 31
MAX_NAME_WITHOUT_LOD = 24
SIZE_DISTANCE_DIGITS = 4

#====================================================================PRIVATE

# Return reserved name found in an object name
#MODIF2016: -->autoLOD to implement
def _has_reserved_name(name, custom_keywords):
    
    #it has to match longest and not the first found
    longest_name_found = ""
    kw_type = None
    for reserved_name in custom_keywords:
        if name.find(reserved_name) >= 0:
            if len(reserved_name) >= len(longest_name_found):
                longest_name_found, kw_type = reserved_name, KEYWORD_CUSTOM
        
    for reserved_name in RESERVED_OBJECT_NAMES:
        if name.find(reserved_name) >= 0:
            if len(reserved_name) >= len(longest_name_found):
                longest_name_found, kw_type = reserved_name, KEYWORD_OTHER

    import re
    # Check for wh after bo?? (bo??wh??)
    matched_name = re.match(r'.+\w(_bo\d+wh\d+).*', name)
    if matched_name:
        reserved_name = matched_name.group(1)
        if len(reserved_name) >= len(longest_name_found):
            longest_name_found, kw_type = reserved_name, KEYWORD_OTHER
                
    for reserved_name in RESERVED_OBJECT_NAMES_NB:
        matched_name = re.match(r'.+\w('+reserved_name+r'\d+).*', name)
        if matched_name:
            reserved_name = matched_name.group(1)
            if len(reserved_name) >= len(longest_name_found):
                longest_name_found, kw_type = reserved_name, KEYWORD_OTHER
        #i = name.find(reserved_name)
        #print(" 0>> ", name, len(name), i, len(name) - len(reserved_name) - i)
        #if i != -1:
            # A keyword was found
#            if len(name) - len(reserved_name) - i >= 2 and reserved_name not in RESERVED_OBJECT_NAMES_1NB:
                #print(" 1>> ", name, len(name), i, name[i + len(reserved_name)], name[i + 1 + len(reserved_name)])
#                 if  i >= 0 and \
#                 name[i + len(reserved_name)].isdigit() and name[i + 1 + len(reserved_name)].isdigit():
                    # Check for wh after bo?? (bo??wh??)
#                     k = name.find('_bo')
#                     if k >= 0:
#                         l = name.find('wh', k + len('_bo') + 2, k + len('_bo') + 4)
#                     if  k >= 0 and l >=0 and \
#                     name[l + 2].isdigit() and name[l + 3].isdigit() and len(name)-k >= 9: # 1_0100_bo01wh01, 1_0100_bo01wh01G, ...
#                         # bo??wh??
#                         return name[k:l+4], KEYWORD_OTHER
#                     else:
#                         if len(name)- i == len(reserved_name) + 2:
#                         # bo??, for example (then, bo01 or bo02, ... is returned)
#                             return name[i:i + 2 + len(reserved_name)], KEYWORD_OTHER
#                     return reserved_name, KEYWORD_OTHER
#             else:
#                 for reserved_name in RESERVED_OBJECT_NAMES_1NB: # MAJ_1_4_1
#                     i = name.find(reserved_name)
#                     #print(" 3>> ", reserved_name, name, len(name), i, len(name)- i, len(reserved_name) + 1)
#                     # keyword with 1 or 2 digits? (then, for example, _primarydigits_ followed by the digit is returned)
#                     # Ex: 1_0032_primarydigits_3 or 1_0032_primarydigits_10 or 1_0032_primarydigits_3.001 or 1_0032_primarydigits_10.001
#                     if ( ((len(name) == i + len(reserved_name) + 1) and name[i + len(reserved_name)].isdigit()) or \
#                          ((len(name) > i + len(reserved_name) + 1) and name[i + len(reserved_name)].isdigit() and not name[i + len(reserved_name) + 1].isdigit()) ):
#                         return name[i:i + 1 + len(reserved_name)], KEYWORD_OTHER
#                     else:
#                         if ( ((len(name) == i + len(reserved_name) + 2) and name[i + len(reserved_name)].isdigit() and name[i + len(reserved_name) + 1].isdigit()) or \
#                              ((len(name) > i + len(reserved_name) + 2) and name[i + len(reserved_name)].isdigit() and name[i + len(reserved_name) + 1].isdigit() and not name[i + len(reserved_name) + 2].isdigit()) ):
#                             return name[i:i + 2 + len(reserved_name)], KEYWORD_OTHER
                        
                        
    return None if longest_name_found == "" else longest_name_found, kw_type

def getLOD(object_string_to_replace, Name):
    '''List of elements e, with e.name and e.prop1 two string * String -> String
    Get a LOD compliant name for a group: like 1_0100_name
    A LOD compliant name is 
    a digit (level), an underscore, 4 digits (visible distance), 
    and underscore and the name, 
    and the total length is <= 31 (24 for the name)'''
    
    #MODIFS2016: replace objects names if special strings found in them
    if object_string_to_replace:
        Name_old = Name
        for elem in object_string_to_replace:
            if elem.name in Name:
                Name = Name.replace(elem.name, elem.prop1)
        if Name_old is not Name:
            bpy.ops.igs_err.damned('EXEC_DEFAULT', type='INFO', message=f" Object '{Name_old}' had his name changed to '{Name}'")  # @UndefinedVariable
                
    #MODIF2016: moved to top :
    #dec2020: factorise and treat more cases
    LODlevel = '1'
    LODdist = '1000'
    name_split = Name.split('_')
    if len(name_split) >= 2:
        if name_split[0].isdigit() and name_split[1].isdigit():
        # LOD mode:
            if len(name_split[0]) == 1 and len(name_split[1]) == SIZE_DISTANCE_DIGITS:
                LODlevel = name_split[0]
                LODdist = name_split[1]
                if len(Name) > MAX_NAME_WITH_LOD:
                    NewName = Name[:MAX_NAME_WITH_LOD]
                    bpy.ops.igs_err.damned('EXEC_DEFAULT', type='WARNING', message=f" Object '{Name}' processed as '{NewName}' to comply with LOD naming rule: names of max {MAX_NAME_WITH_LOD} characters.") # @UndefinedVariable
                
                    return int(LODlevel), int(LODdist), NewName
                else:
                    return int(LODlevel), int(LODdist), Name
            else:
                if len(name_split[0]) == 1: # LODlevel
                    LODlevel = name_split[0]
                    LODdist = name_split[1]
                    
                    if len(name_split[1]) >= SIZE_DISTANCE_DIGITS: # LODdist
                    # Truncate
                        NewName = ("_".join([LODlevel, LODdist[:SIZE_DISTANCE_DIGITS], name_split[2]]))[:MAX_NAME_WITH_LOD]
                        LODdist = LODdist[:SIZE_DISTANCE_DIGITS]
                        
                    else:
                    # Pad
                        NewName = ("_".join([LODlevel, LODdist.ljust(SIZE_DISTANCE_DIGITS,'0'), name_split[2]]))[:MAX_NAME_WITH_LOD]
                        LODdist = LODdist.ljust(SIZE_DISTANCE_DIGITS,'0')
                        
                    bpy.ops.igs_err.damned('EXEC_DEFAULT', type='WARNING', message=f" Object '{Name}' processed as '{NewName}' to comply with LOD naming rule: {SIZE_DISTANCE_DIGITS} distance digits.") # @UndefinedVariable
                    return int(LODlevel), int(LODdist), NewName
                    
    #default alternative:
    NewName = "_".join([LODlevel, LODdist, Name[:MAX_NAME_WITHOUT_LOD]])
    bpy.ops.igs_err.damned('EXEC_DEFAULT', type='WARNING', message=f" Object '{Name}' processed as '{NewName}' to comply with LOD naming rule.") # @UndefinedVariable
                
    return int(LODlevel), int(LODdist), NewName # (LODlevel + '_' + LODdist + '_' + Name)

class group_wrapper(object):
    '''Class to group objects along criteria in order to merge them into a single object'''

    __slots__ = ("LODlevel", "LODdist", 
                "keyword", "parent_group", 
                "name", "objects_list", 
                "child_groups_list", 
                "IGinstance_id", "IGinstance",
                "type_o")

    def __init__(self, LODlevel=1, LODdist=0, keyword=None, parent_group=None, name="", type_o='MSH'):
        self.LODlevel = int(LODlevel)
        self.LODdist = int(LODdist)
        self.keyword = keyword
        self.parent_group = parent_group
        self.name = name
        self.type_o = type_o #str in {'MSH', 'SPT'} (Mesh, snap point)
        self.objects_list = []
        self.child_groups_list = []
        self.IGinstance_id = 0 # Id of the related IGinstance
        self.IGinstance = None # Related IGinstance

    def __eq__(self, other):
        if self.type_o != other.type_o:
            return False
        
        if (self.LODlevel is not other.LODlevel) or (self.LODdist is not other.LODdist):
            return False
    
        if (other.LODlevel > 1) or (other.LODdist is not self.LODdist): # MAJ_1_4_1 / 1.4.4
            if other.parent_group is not self.parent_group:
                # They must be siblings
                return False
            #else:
            #    print(" >> (obj_parent == current_group.objects_list[0].parent) ", obj_parent)
    
        if self.keyword is not other.keyword:
            return False
        
        return True

def _register_group(groups_list, new_group):
    if new_group.parent_group:
        new_group.parent_group.child_groups_list.append(new_group) # Store child group wrapper reference in parent group wrapper
        #if new_group.keyword:
        #    new_group.parent_group.keyword = new_group.keyword
    
    groups_list.append(new_group)
    

#MODIF2016: add snap points :
def _add_to_group(Config, mObjects_list, obj, parent_group, groups_list, processed_objects_list):
    """Sort objects in groups according to LOD, keyword,... : group_wrapper objects are created with parent group wrapper and a list of children group_wrapper."""
    #print(" add_group name={:s} // parent_object_keyword={:s}".format(obj.name, parent_object_keyword))
    hierarchy_processing = Config.hierarchy_processing
    #custom_keywords = [kword.name for kword in Config.KeywordsListItem if kword.prop1] #moved were it is used lower
    keyword, keyword_type = None, None
    
    if obj in processed_objects_list:
            return
        
    if obj.type == 'EMPTY' and not len(obj.children):
        #MODIF: snap points :
        name_split = obj.name.split('_')
        if ("#s" == name_split[0]) and len(name_split[0]) == 3:
            obj_group = group_wrapper(0, 0, keyword, parent_group, obj.name, 'SPT')
            obj_group.objects_list.append(obj)
            
            _register_group(groups_list, obj_group)
            
            
            bpy.ops.igs_err.damned('EXEC_DEFAULT',type='INFO', message=" object '{0}' has been processed as Snap Point".format(obj.name)) # @UndefinedVariable
                
    
    
    
    elif obj.type == 'MESH': #MODIFS2016: auto nodes
        obj_group = None
        LODlevel, LODdist, group_name = getLOD(Config.object_string_to_replace, obj.name) # MAJ3
        keyword, keyword_type = _has_reserved_name(group_name, [kword.name for kword in Config.KeywordsListItem if kword.prop1])
        new_gp = group_wrapper(LODlevel, LODdist, keyword, parent_group, group_name, 'MSH')
        
        if hierarchy_processing and not (obj.animation_data or obj.constraints):
            
            if parent_group and parent_group == new_gp:
                #
                obj_group = parent_group

            elif new_gp.keyword is None and len(obj.children) == 0:
                # LODlevel == LODlevel_parent and LODdist != LODdist_parent and parent_object_keyword != None (example: 1_0100_Parent with 2 children 1_0030_Child1 and |_1_0030_Child2, then 1_0030_Child* are merged)
                if (parent_group and 
                keyword_type == KEYWORD_CUSTOM and 
                LODlevel == parent_group.LODlevel and 
                LODdist != parent_group.LODdist): # 1.4.4 #2020 reorder
                    
                    for current_group in groups_list:
                        if current_group == new_gp:
                            obj_group = current_group
                            break
                    #else:
                        #nothing found to add itself to
                    #    pass
                        
        if obj_group is None:
        # Create a new group and store it to the common list
            obj_group = new_gp
            
            _register_group(groups_list, obj_group)
            
            parent_group = obj_group
        #
        #add object to selected group
        obj_group.objects_list.append(obj)
    
    #elif obj.type == 'ARMATURE':
    #    obj_group = group_wrapper(0, 0, None, parent_group, obj.name, 'ARM')
    #    _register_group(groups_list, obj_group)
        
    else:
        #print(" not mesh or empty: {:s}".format(obj.name))
        #parent_group = None # Example: no parent for children of LATTICE or ARMATURE
        pass
        
    processed_objects_list.append(obj)
    #bpy.ops.igs_err.damned('EXEC_DEFAULT',type='INFO', message=" object '{}' has been processed in a group".format(obj.name))
    
    if not (parent_group and parent_group.type_o == 'SPT') and (obj in mObjects_list): #do not search through children for snap points and duplis
        #to avoid searching through all groups and just cut away from list groups
        #which are not involved for sure. To do this, we save postion of parent group in list and
        # all groups after this and before duplis computation are sure to be its children.
            
        for obj_children in obj.children:
            if obj_children in mObjects_list: #only use validated children from CleanAndProperSceneExport() :
                _add_to_group(Config, mObjects_list, obj_children, parent_group, groups_list, processed_objects_list)

def _group_wrapper_dump(groups_list):
    print("\n ------------------ Groups list -----------------\n+--- {:d} groups ---\n|".format(len(groups_list)))
    def recursive_dump(gp,lvl):
        print("|  "*lvl+"+--> {:s} (kw: {:s})".format(gp.name, gp.keyword or "None"))
        print("|  "*lvl+"|         type: {:s}".format(gp.type_o))
        if len(gp.objects_list):
            print("|  "*lvl+"|  [ included objects:                ]")
        for ob in gp.objects_list:
            print("|  "*lvl+"|  [ {:<32} ]".format(ob.name))
            
        for chd in gp.child_groups_list:
            print("|  "*(lvl+2))
            recursive_dump(chd, lvl+1)
        print("|  "*(lvl+1))
        
    
    for grp in groups_list:
        if grp.parent_group is None:
            recursive_dump(grp, 0)
            print("|")

#====================================================================PUBLIC

def make_groups(Config, objects_list, dump_grps=True):
    """"Sort objects in groups"""
    
    groups_list = []
    processed_objects_list = []
    
    for obj in objects_list:
        if not (obj.parent in objects_list): # don't process a child before its parent
            _add_to_group(Config, objects_list, obj, None, groups_list, processed_objects_list)
    
    assert len(groups_list) > 0, "No Groups found!"
    
    #dec2020: check doubled names due to shortening or renaming for example
    name_set = set()
    duplicate_flag = False #True when duplicate names found
    duplicate_string = " Duplicated group renamed:\n"
    shortened_flag = False #True when a shortened/modified object name has already been found and needs to be reported back to the user
    shortened_objects_string = " Objects processed to comply with LOD naming rule:\n"
    
    for gp1 in groups_list:
        if gp1.LODlevel <= 1: #only check top lod because other levels are modified accordingly
            gp_main_ob_name = gp1.objects_list[0].name
                
            #check duplicates
            if gp1.name in name_set:
                #duplicated group names
                duplicate_flag = True
                new_name_no_lod = "obhash_" + str(hash(gp_main_ob_name))
                #modify name for all LODs of this object
                for gp in [gp1] + [g for g in gp1.child_groups_list if g.LODlevel > 1]:
                    new_name = gp.name[:SIZE_DISTANCE_DIGITS+3] + new_name_no_lod #cut after underscore following LOD to replace name with hashed value of object name
                    duplicate_string += f"  - {gp_main_ob_name}\n      as {new_name}\n"
                    gp.name = new_name
                    
            #check shortened/modified
            if gp1.name != gp_main_ob_name:
                shortened_objects_string += f"  - {gp_main_ob_name}\n      as {gp1.name}\n"
                shortened_flag = True
                
            name_set.add(gp1.name)
        elif gp1.LODlevel > 1:
            #check no group with lod>1 on top
            if not gp1.parent_group: 
                gp1.name[0] = "1"
                shortened_objects_string += f"  - {gp1.objects_list[0].name} [wrong top LOD]\n      as {gp1.name} \n"
                shortened_flag = True
            
            else:
                #wrong lod order
                if gp1.parent_group.LODlevel >= gp1.LODlevel: 
                    gp1.LODlevel = gp1.parent_group.LODlevel+1
                    gp1.name[0] = str(gp1.LODlevel)
                    shortened_objects_string += f"  - {gp1.objects_list[0].name} [wrong LOD order]\n      as {gp1.name} \n"
                    shortened_flag = True
                    
                #wrong lod dist order
                if gp1.parent_group.LODdist >= gp1.LODdist: 
                    gp1.LODdist = gp1.parent_group.LODdist+1
                    gp1.name[2] = str((gp1.LODdist // 1000) % 10)
                    gp1.name[3] = str((gp1.LODdist // 100) % 10)
                    gp1.name[4] = str((gp1.LODdist // 10) % 10)
                    gp1.name[5] = str(gp1.LODdist % 10)
                    shortened_objects_string += f"  - {gp1.objects_list[0].name} [wrong LOD dist]\n      as {gp1.name} \n"
                    shortened_flag = True
                
            
    assert len(set(gp.name for gp in groups_list)) == len(groups_list), "Group names not unique!"
    
    #print the warnings
    if shortened_flag:
        shortened_objects_string+=" -> can't see why? read the log!"
        bpy.ops.igs_err.damned('EXEC_DEFAULT', type='WARNING', message=shortened_objects_string) # @UndefinedVariable

    if duplicate_flag:
        duplicate_string+=f" -> try renaming them to something unique and shorter than {MAX_NAME_WITHOUT_LOD} characters (LOD excluded)"
        bpy.ops.igs_err.damned('EXEC_DEFAULT', type='WARNING', message=duplicate_string) # @UndefinedVariable

    if duplicate_flag or shortened_flag:
        #no full list because of Blender formating making it horrible and I'm to lazy to make another UI_List for logs! TODO: make logs a UI_List in interface
        bpy.ops.igs_err.damned('INVOKE_DEFAULT', type='WARNING', message=" Some object names have been modified to comply with lod naming rules. Please look at the log to see which.") # @UndefinedVariable
 
    #print groups to be exported
    if dump_grps:
        _group_wrapper_dump(groups_list)
        
    return groups_list

