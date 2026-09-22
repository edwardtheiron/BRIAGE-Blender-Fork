# ##### BEGIN GPL LICENSE BLOCK #####
#
# Copyright (C) 2023  'Juju49'(MERLE-RÉMOND Julian)
# see license notes __init__.py
#
# ##### END GPL LICENSE BLOCK #####

import sys
import bpy
from bpy.props import FloatProperty, StringProperty  # @UnresolvedImport


#===============================================================MISC FUNCS

import time
import math

def register():
	pass

def unregister():
	pass
	
class ProgressReporterHack():
	"""Reports progress to info spaces"""
	
	def __init__(self, context):
		from os import devnull
		
		self.context = context
		self.redraws = ( area for area in self.context.window.screen.areas
			if area.type == 'STATUSBAR')
		
		self.last_time = time.perf_counter() - 0.51 # to enable first update

		self._fake_output = open(devnull, 'w')
	
	def __enter__(self):
		self.context.workspace.status_text_set(f"0% : starting")
		return self
	
	def __exit__(self, e_type, e_value, e_traceback):
		self.context.workspace.status_text_set(None)
		
		self._fake_output.close()
		
		return isinstance(e_type, Exception)
		
	def update(self, progress, msg=""):
		self.context.workspace.status_text_set(f"{progress}% : {msg:<100}")
		
		# see https://docs.blender.org/api/current/info_gotcha.html
		new_time = time.perf_counter()
		if new_time >= self.last_time + 0.51:
			self.last_time = new_time
			
			for area in self.redraws:
				area.tag_redraw()
			
			self._original_stdout = sys.stdout
			sys.stdout = self._fake_output
			
			bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
			
			sys.stdout = self._original_stdout

from mathutils import Vector, Matrix, Euler

def get_matrix_world(dup_instance):
	if dup_instance.is_instance:  # @UndefinedVariable
		return dup_instance.matrix_world.copy()
	else:
		return dup_instance.matrix_world
	
	
def center_main_object(Config, objects_list):
	"""Center Main Object"""
	
	center_main_object = Config.center_main_object
	center_main_object_N = Config.center_main_object_N
	current_position = objects_list[0].matrix_world.to_translation()
	applied_translation = Vector((0.0, 0.0, 0.0))
	for num_axis in range(3):
		if center_main_object_N[num_axis]:
			applied_translation[num_axis] = float(center_main_object[num_axis]) - current_position[num_axis]
	#		
	rot_mat = Euler(Config.center_main_object_rot[:], 'XYZ').to_matrix().to_4x4()
	#bpy.ops.igs_err.damned('EXEC_DEFAULT',  # @UndefinedVariable
	#    type='INFO',
	#    message=" CenterMainObject: exported model moved by X={:f} Y={:f} Z={:f} (Blender axis)\n".format(applied_translation.x, applied_translation.y, applied_translation.z))  # @UndefinedVariable
	#  
	return Matrix.Translation(applied_translation).to_4x4() @ rot_mat

#===============================================================GET SCRIPT PATH
def get_binpath():
	"""	-> str
		returns dirname of this addon"""
	#import bpy
	import os.path
	BINARY_PATH = os.path.dirname(__file__)
	return BINARY_PATH


def print_pr(seq, data=[]):
	"""	-> None
		seq: str ; name of the segment we want to print from strings.pr
		data: list ; prints list item [i] at $DATAi
	
	Prints predefined strings from file to console or log or wherever you rerouted sys.out
	If $VERSION is found, prints BRIAGE full version number
	"""
	from .IAE  import IAE_VERSION
	from .     import PCKG_VERSION, BINARY_PATH
	from .IGSE import IGSE_VERSION
	from .IGSI import IGSI_VERSION
	from .IAI  import IAI_VERSION
	
	seq_found = False
	with open(BINARY_PATH + "\\strings.pr", mode='r', encoding='utf-8', errors='ignore') as file:
		for line in file:
			if seq_found and r"$END" in line:
				return 'END_OK'
			elif seq_found and r"$VERSIONS" in line:
				print(f"{PCKG_VERSION}\n  {IGSE_VERSION} - {IAE_VERSION}\n  {IGSI_VERSION} - {IAI_VERSION} ")
			elif seq_found and r"$DATA" in line:
				datum_index = int("".join([s for s in line if s.isdigit()]))
				print(data[datum_index])
			elif not seq_found and r"$START" + str(seq) in line:
				seq_found = True
			elif not seq_found:
				continue
			else: print(line, end="")


def setup_addon_modules(path, package_name, reload = False):
# from animation nodes:
# 	Created by Jacques Lucke
#	Copyright (C) 2014 Jacques Lucke
#	license GPL 3
	import os
	import pkgutil
	import importlib
	
	"""
	Imports and reloads all modules in this add-on. 
	
	path -- __path__ from __init__.py
	package_name -- __name__ from __init__.py
	"""
	def get_submodule_names(path = path[0], root = ""):
		module_names = []
		for _, module_name, is_package in pkgutil.iter_modules([path]):
			if is_package:
				sub_path = os.path.join(path, module_name)
				sub_root = root + module_name + "."
				module_names.extend(get_submodule_names(sub_path, sub_root))
			else: 
				module_names.append(root + module_name)
		return module_names 

	def import_submodules(names):
		modules = []
		for name in names:
			modules.append(importlib.import_module("." + name, package_name))
		return modules
		
	def reload_modules(modules):
		for module in modules:
			importlib.reload(module)
	
	names = get_submodule_names()
	modules = import_submodules(names)        
	if reload: 
		reload_modules(modules) 
	return modules

def profiler(pmode):
	def decorator(f):
		def wrapper(*args, **kwargs):
			if pmode:
				import cProfile, pstats, io, os
				pr = cProfile.Profile()
				s = io.StringIO()
				print("BRIAGE: PROFILE MODE")
				saveout, sys.stdout = sys.stdout, s
				
				pr.enable()
			
			ret = f(*args, **kwargs)
			
			if pmode:
				pr.disable()
				sortby = 'tottime'
				pstats.Stats(pr, stream=s).sort_stats(sortby).print_stats(20)
				sortby = 'cumtime'
				pstats.Stats(pr, stream=s).sort_stats(sortby).print_stats(20)
				#print(s.getvalue())
				sys.stdout = saveout
				try:
					with open("BRIAGE_Import.log", "w", encoding='utf-8') as logfile:
						logfile.write(s.getvalue())
					print( os.path.abspath("BRIAGE_Import.log") )
				except:
					print("BRIAGE: Cannot print profile log to file, redirect to stdout :")
					print(s.getvalue())
				s.close()
			return ret or None
		return wrapper
	return decorator

#===========================================================COMMON FS INTERFACE
#I was gonna use this to be able to modify already packaged IGS files 
#but, it ended up being useless with some more optimizations elsewhere in the program
#perhaps, need of this will appear again later...
#from collections import namedtuple

class FSINode():
	"""wraps IG classes and computes missing values on creation"""
	__slots__ = ("IGPayload", "offset", "index")
	
	def __init__(self, IGPayload: object, 
			offset: int = None, index: int = None):
		
		assert (offset != None) or (index != None), "invalid node: references are empty!"
		
		self.IGPayload = IGPayload
		self.offset = offset
		self.index = index
	
	@property
	def inner_type(self):
		return type(self.IGPayload)
	
	def __len__(self):
		return len(self.IGPayload)
	
	def __eq__(self, other):
		return (type(self) == type(other)) and \
			(self.IGPayload == other.IGPayload) and \
			(self.offset == other.offset) and \
			(self.index == other.index)
			
		
	

class FSInterface():
	
	__slots__ = ("class_order", "_index_dict", "_offset_dict", "_inclusion_set")
	
	def __init__(self, *class_order):
		super().__init__()
		self.class_order = tuple(class_order) #order of data-classes in file
		self._index_dict = dict() #dict of classes to store
		self._offset_dict = dict() #access by offset
		self._inclusion_set = set() #quick __contains__
	
	
	def __contains__(self, item):
		return item in self._inclusion_set
	
	def _iter_node(self, 
				start_cls:"cls of class_order"=None, 
				end_cls:"same"=None, 
				start_index:"internal dict index"=0):
		c_o = self.class_order
		
		s1 = c_o.index(start_cls) if start_cls != None else 0
		s2 = c_o.index(end_cls) if end_cls != None else len(c_o)-1
		
		for curr_cls in c_o[s1:s2]:
			#freeze it before iterating to avoid re-affectation mistakes
			frozen_node_dict = self._index_dict[curr_cls].copy()
			for i in range(start_index, len(frozen_node_dict)): 
				yield frozen_node_dict[i]
	
	def __iter__(self):
		for item in self._iter_node():
			yield item.IGPayload
	
	def _get_node(self, key): #__getitem__ key
		#key type: tuple for access by index and int for access by offset
		if type(key) == tuple:
			assert len(key) == 2, "FSI: Invalid key, wrong length"
			#check key args type....
			category_type, internal_index = key
			assert type(internal_index) == int, "FSI: Invalid key, wrong second member"
			
			#check if the category exists, else, warn user by reraising
			try:
				i_dict = self._index_dict[category_type]
			except KeyError as E:
				raise E
			return i_dict[internal_index] #FSINode
		
		elif type(key) == int:
			return self._offset_dict[key] #FSINode
		
		else:
			raise AssertionError("FSI: Invalid key, invalid key type")
		
	def __recalc_offsets_from_indexes(self,
				start_cls:"cls of class_order"=None, 
				start_index:"internal dict index"=0):
		"""recalculate offsets from indexes of nodes from 
		dict[start_cls][start_index] and onward"""
		
		o_d = self._offset_dict
		
		#print("upd offsets")
		
		#unpack values here
		first_turn = True
		for node in self._iter_node(start_cls=start_cls, start_index=start_index):
			if first_turn:
				total_offset = node.offset
				first_turn = False
		
			node.offset = total_offset
			o_d[total_offset] = node
			#print("upd offsets: {} {}".format(str(node.inner_type), str(total_offset)))
			total_offset += len(node)
			
	def __fix_indexes(self,
					cls:"cls of class_order"=None,
					start_index:"internal dict index"=0):
		"""suppress holes in index sequence by moving references"""
		node_dict = self._index_dict[cls]
		len_dict = len(node_dict)
		move_offsets_of_x_backwards = 0
		#nodes are moved backwards if a hole is found. Each hole adds itself.
		#it also checks that the hole != actually the end of the list.
		for i in range(start_index, len_dict):
			#print("fixing id {}".format(str(i)))
			is_fixed_now = False
			while not is_fixed_now:
				#print("  move_offsets_of_x_backwards: " + str(move_offsets_of_x_backwards))
				try:
					if i + move_offsets_of_x_backwards < len_dict:
						node_dict[i + move_offsets_of_x_backwards]
						#print("  testing...")
				except KeyError:
					move_offsets_of_x_backwards += 1
				else:
					node_dict[i] = node_dict[i + move_offsets_of_x_backwards]
					node_dict[i].index = i
					is_fixed_now = True
					#print("  profit")
		#self._recalc_offsets_from_node(node) should be called here to avoid confusion
			
	def _recalc_offsets_from_node(self, node):
		self.__recalc_offsets_from_indexes(
			start_cls=node.inner_type, 
			start_index=(node.index-1 if node.index>0 else 0))
		
	def __getitem__(self, key):
		"""
		returns IGPayloads from keys (type, int) or (int)"""
		return self._get_node(key).IGPayload
	
	def __setitem__(self, key, value):
		"""(type, int) * alpha or int * alpha -> NoneType
		allows modification to node items from (type, index) or (offset)
		and allows creation of new items from (type, index)"""
		
		#important values that must be declared to avoid confusion later:
		offset = None
		category_type = None
		internal_index = None
		
		#does it already exists?
		try:
			node = self._get_node(key)
		except KeyError:
			#raises AssertionError if key is invalid in _get_node(k)
			if type(key) == int:
				raise NotImplementedError("FSI: Cannot set new offsets from this method, see append(item)")
			node = None
			
		
		#if nothing has changed, exit:
		if node.IGPayload == value: return
		
		#check if the category exists, else, create it
		try:
			i_dict = self._index_dict[category_type]
		except KeyError:
			#assigns the same reference to both = easy work:
			i_dict = self._index_dict[category_type] = {} 
		
		
		#key type: tuple for access by index and int for access by offset
		if (type(key) == tuple) and (node == None):
			category_type, internal_index = key
			
			new_node = FSINode(IGPayload=value, 
							offset=offset, 
							index=internal_index)
			
			#register node
			self._offset_dict[offset] = new_node
			i_dict[internal_index] = new_node
			
			self._recalc_offsets_from_node(new_node)
				

		else: #here: (type(key) == int) or (node != None)
		#we replace the old value since its hard to create a new one from here
			assert type(value) == node.inner_type, "FSI: type doesn't match"
			
			#remove old item from set
			self._inclusion_set.remove(node.IGPayload)
			
			node.IGPayload = value
			
			#add item to inclusion set for fast matching
			self._inclusion_set.add(value)
	
	def __delitem__(self, key):
		#we can only remove it if we have it:
		try:
			node = self._get_node(key)
		except KeyError as E:
			raise E

		print("deleting {}".format(str(key)))
		#take it out of everything we have
		del self._index_dict[node.inner_type][node.index]
		del self._offset_dict[node.offset]
		self._inclusion_set.remove(node.IGPayload)
		
		#recalc offsets from next node because this item might have been in the middle
		self.__fix_indexes(node.inner_type, node.index)
		#transfer my offset to the one who replaced me:
		self._index_dict[node.inner_type][node.index].offset = node.offset
		#calc offsets of the following nodes 
		self._recalc_offsets_from_node(node)
		
		#assign invalid values to indicate that, this is no longer 
		#a valid container if it is referenced elsewhere:
		node.offset = None
		node.index = None
		
		#del our reference:
		del node
	
	def __len__(self):
		return len(self._inclusion_set)
	
	def __length_hint__(self):
		return self.__len__()
	
	def __add__(self, other):
		raise NotImplementedError
		return
	
	def append(self, item):
		"""appends item at the end its class indexes"""
		category_type = type(item)
		#check if the category exists, else, create it
		try:
			i_dict = self._index_dict[category_type]
		except KeyError:
			#assigns the same reference to both = easy work:
			i_dict = self._index_dict[category_type] = {} 
			
		internal_index = len(i_dict)

		if internal_index > 0:
			previous_elem = i_dict[internal_index-1]
			offset = previous_elem.offset + len(previous_elem)
		else:
			c_o = self.class_order
			class_index = c_o.index(category_type)
			if class_index > 0:
				try:
					previous_dict = self._index_dict[c_o[class_index-1]]
				except KeyError:
					previous_dict = self._index_dict[c_o[class_index-1]] = {}
				prev_item = previous_dict[len(previous_dict)-1]
				
				offset = prev_item.offset + len(prev_item)
			else:
				offset = 0
		
		new_node = FSINode(IGPayload=item, 
							offset=offset, 
							index=internal_index)
		
		#register node
		self._offset_dict[offset] = new_node
		i_dict[internal_index] = new_node
		
		#add item to inclusion set for fast matching
		self._inclusion_set.add(item)
		
		#recalc offsets because this item might have been inserted
		self._recalc_offsets_from_node(new_node)
	
	def dump_structure(self, out):
		raise NotImplementedError
	
	def extend(self, other):
		raise NotImplementedError 
	
	def write(self, file):
		for containers in self:
			containers.write(file)
	
	def open(self, file):
		raise NotImplementedError
