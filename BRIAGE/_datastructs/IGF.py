# ##### BEGIN LICENSE BLOCK #####
#
# Copyright (C) 2024  'DOM107', 'Juju49'(MERLE-RÉMOND Julian)
# see license notes __init__.py
#
# ##### END LICENSE BLOCK #####

import struct
from mathutils import Matrix

#from enum import Enum, IntEnum

#====================================================================IGF data structures

"""class containing data for IGS"""

#thresholds:
gVertexWeldNormalThreshold = 0.00002
gVertexWeldColourThreshold = 0.0039
gVertexWeldUVThreshold     = 0.00002

#lengths:
MAX_RENDER_STAGES = 8
MAX_LEGACY_TEXTURE_NAME = 32
MAX_SHADER_NAME = 128
MAX_SURF_TYPE_NAME = 128
MAX_MATERIAL_COMMENT = 256
MAX_MATERIAL_NAME = 128
MAX_EFFECT_NAME = 32
MAX_LIGHTGLOW_TYPE = 32
MAX_SEQUENCE_MODE = 32
MAX_OBJECT_NAME = 32
MAX_EXPORTED_BONES = 8
MAX_HEADER_COMMENT = 64
MAX_HEADER_DESCRIPTOR = 16
MAX_CHILDREN = 24
MAX_FACE_TAG_DESCS = 256 				# Each tag is of size MAX_OBJECT_NAME

#Flags:
#	light flags
LIGHT_FLAG_NEAR_ATTENUATION	=   0b1		# if near attenuation enabled
LIGHT_FLAG_FAR_ATTENUATION	=  0b10		# if far attenuation enabled
LIGHT_FLAG_RECTANGULAR_SPOT	= 0b100		# otherwise spotlight defaults to cone
#	hidden edges
EDGE_V0_V1_HIDDEN =   0b1
EDGE_V1_V2_HIDDEN =  0b10
EDGE_V2_V3_HIDDEN = 0b100

#Enums:
#	eIGLightType
LIGHT_OMNIDIRECTIONAL = 0
LIGHT_SPOTLIGHT = 1
# var = NUM_LIGHT_TYPES

#	eIGLightAttenuation
LIGHT_ATTENUATION_LINEAR = 0
LIGHT_ATTENUATION_INVERSE = 1
LIGHT_ATTENUATION_INVERSE_SQUARED = 2
# var = NUM_LIGHT_ATTENUATIONS

#	eIGUVOperation:
UV_OP_INVALID = -1
UV_OP_COPY = 0
UV_OP_REFLECTMAP = 1
UV_OP_REFLECTMAPFULL = 2
UV_OP_REFLECTMAP_VERTICAL = 3
# var = NUM_UV_OPERATIONS

#	eIGUVWrapMode
UVWRAP_INVALID = -1
UVWRAP_TILE = 0
UVWRAP_CLAMP = 1

#	eIGViewFacing
VF_NONE = 0
VF_FACING = 1
VF_UPRIGHT = 2
# var = NUM_VF_MODES

#	eIGPulseGlowMode
PG_PULSE = 0
PG_RANDOM = 1
PG_SEQUENCED = 2
# var = NUM_PULSE_GLOW_MODES

#	eIGDataBlockID
BLOCK_INVALID = 0
BLOCK_FACE_TAG_DESCS = 1
BLOCK_TEXTURE_NAMES = 2
# var = NUM_BLOCK_IDS

gIGDescriptors = {b"SHAPE", b"LEVEL"}

gIGTags = {b'IG_TAG_NONE',
	b'IG_TAG_HEAD' , b'IG_TAG_HEAD_STUMP' , b'IG_TAG_HEAD_STUMP_REPL' ,
	b'IG_TAG_ARM_L', b'IG_TAG_ARM_L_STUMP', b'IG_TAG_ARM_L_STUMP_REPL',
	b'IG_TAG_ARM_R', b'IG_TAG_ARM_R_STUMP', b'IG_TAG_ARM_R_STUMP_REPL',
	b'IG_TAG_LEG_L', b'IG_TAG_LEG_L_STUMP', b'IG_TAG_LEG_L_STUMP_REPL',
	b'IG_TAG_LEG_R', b'IG_TAG_LEG_R_STUMP', b'IG_TAG_LEG_R_STUMP_REPL'}

gCollisionTypes = {
	b"Unknown" ,
	b"METAL" ,
	b"METAL_HOLLOW" ,
	b"DIRT" ,
	b"WOOD" ,
	b"STONE" ,
	b"BRICK" ,
	b"CONCRETE" ,
	b"GLASS" ,
	b"PLASTIC" ,
	b"BLOOD" ,
	b"SLIME" ,
	b"GRILL" ,
	b"OPAQUE_GLASS" ,
	b"SNOW" ,
	b"ICE" ,
	b"SILENT"}


gIGCommentFieldToggles = { 
	b":forceprelit",
	b":pointlit",
	b":pre-dpp",
	b":unfog",
	b":animdelay",
	b":animmaxframe",
	b":fpsfraction",
	b":fadedist",
	b":noclip",
	b":startinvisible",
	b":startnocollide",
	b":nocompress",
	b":forceunder",
	b":fullalphasort",
	b":occlude",
	b":alternode", #alterable node...
	b":shatter",
	b":objectstick" }
	
#size:
HEADER_SIZE = 216
MATERIAL_SIZE = 1788
VERTEX_SIZE = 240
TRIANGLE_SIZE = 92
GEOM_SIZE = 100
GEOMLOD_SIZE = 56
INSTANCE_SIZE = 260
DATABLOCK_SIZE = 44
BONE_SIZE = 252 		#MODIFS2016: bones
GSCITEMS_SIZE = 220 	#MODIFS2016: gscitems

SIZE_OF_INT = 4
#SIZE_OF_BOOL = 4
#SIZE_OF_FLOAT = 4

STRING_ENCODING = ("ascii", "ignore") #2020: decode errors

#uid generation:
# class IGUuid():
# 	"""start: int #to be used as a first id when incrementing
# 	-> int
# 	
# 	Used for generating unique ids either by incrementing or by slicing uuids (safe mode).
# 	This is a singleton!"""
# 	#
# 	class __IGUuid():
# 		__slots__ = ( "counter", )
# 		#
# 		def __init__(self, start_number):
# 			self.counter = start_number
# 			#
# 		def __str__(self):
# 			return repr(self) + self.counter
# 		#
# 		def __iter__ (self):
# 			return self
# 		#
# 		def __next__ (self):
# 			self.counter += 1
# 			return self.counter
# 		#
# 	__slots__ = ( "instance", )
# 	
# 	instance = None
# 	#
# 	def __init__(self, start=None):
# 		if not IGUuid.instance:
# 			if not start:
# 				start = 0
# 			IGUuid.instance = IGUuid.__IGUuid(start)
# 	#
# 	def __getattr__(self, name):
# 		return getattr(IGUuid.instance, name)
# 	def __setattr__(self, name, val):
# 		return setattr(IGUuid.instance, name, val)
# 	#
# 	def generate_safe_uid(self):
# 		import uuid
# 		return uuid.uuid4().fields[1].format( (2**32-1) )
# 	#
# 	def __iter__ (self):
# 		return IGUuid
# 	#
# 	def __next__ (self):
# 		if not IGUuid.instance:
# 			IGUuid()
# 		#
# 		return next(IGUuid.instance)

class LengthMetaclass(type):
	"""metaclass used to make classmethod __len__ working"""
	def __len__(self):
		return self.__len__()

# abstract class for auto __init__ and dumps
class _MetaIGClass(object):
	"""Metaclass of all IGobjects built to standardize specs across classes
	
	"block_format" is included and must be a tuple of struct formating types
	except for IGobjects where a tuple must be provided space splits number of occurrences from type
	name the corresponding __slot__ object is"""
	
	__slots__ = ("block_type",) #block_format is a dict of "var_name" : type
	
	def __init__(self, **kwargs):
		"""
		Defines init procedurally from kwargs.
		types are given through annotations to child func __init__ methods.
		
		May raise AttributeError if not defined correctly:
			len(args) == len(self.__slots__) and kwargs.keys() in self.__slots__
		"""
		#store type in block format for later io ops, must be dict of var names and there classes
		self.block_type = self.__init__.__annotations__
			
		for key, value in kwargs.items():
			if not key in self.block_type:
				continue
			setattr(self, key, value)
		

	def _get_format_str(self):
		""" -> list[str or tuple[type, int]]
		
		Returns the block_format corresponding to self.
		contains also entities subclass of _MetaIGClass
		
		/!\ this is a generator!
		
		Notice for the tuples:
			t[0] contains type
			t[1] contains number of occurrences
			t[2] contains the length of an occurrence 
			 relative to the smallest size available (only useful for str)
			 but not all tuple have it, will defaults to 1 if not found"""
		
		#alias:
		bt = self.block_type
		
		def _get_format_char(var_name):
			"""type or tuple(str, int) -> str, int or type, int
			
			Returns the struct block_format corresponding to this entity
			or the corresponding entity if type is _MetaIGClass
			
			Notice for the tuples:
				t[0] contains type
				t[1] contains number of occurrences
				t[2] contains the length of an occurrence 
				 relative to the smallest size available (only useful for str)
				 but not all tuple have it, will defaults to 1 if not found"""
			#default case where there is just a type entered
			type_to_find = bt[var_name]
			num_occurences = 1
			len_occurence  = 1
			
			if type_to_find is tuple:
				#0 contains type
				type_to_find   = type_to_find[0]
				#1 contains number of occurrences
				num_occurences = type_to_find[1]
				#2 contains the length of an occurrence 
				# relative to the smallest size available (only useful for str)
				#but not all tuple have it, so we default if not found:
				len_occurence  = type_to_find[2] if len(type_to_find) == 3 else len_occurence
				
			if type_to_find is int:
				return "I", num_occurences, len_occurence
			if type_to_find is float:
				return "f", num_occurences, len_occurence
			if type_to_find is str:
				return "s", num_occurences, len_occurence
			if isinstance(type_to_find, _MetaIGClass):
				return type_to_find, num_occurences, len_occurence
			raise TypeError("type to write not in {int, float, str, _MetaIGClass}")
		

		
		#list of str for struct module, 
		#types of other instance included as their own types
		#format_list = []
		
		for declared_vars in self.__slots__:
			#get struct compatible format string for object or something to filter after:
			format_type, format_num_occ, occ_length = _get_format_char(declared_vars)
			#if format_num_occ > 1, then its a subscriptable list! bear that in mind!!

			
			#appends a format str char or a tuple(type, list_len) => useful for filtering later
			#or used here as a generator to save up memory...

			if type(format_type) is not str:
				#Here format_type is a class so we want to do ops on type for this
				#(like get length or stuff).
				yield (format_type(), format_num_occ, occ_length)
				#format_list.append((getattr(self, declared_vars), format_num_occ))
			
			#type(format_type) is str here
			else: 
				yield (str(format_num_occ) + str(format_type), format_num_occ)
				#format_list.append((format_num_occ + format_type, format_num_occ))

		#return format_list
		raise StopIteration

	def __len__(self):
		""" -> int
		Return the size of this datablock.
		
		It is computed from "block_format" types and missing parts are gotten 
		recursively from vars which are children of MetaIGClass.
		It is advised to redefine this method for each child class for improved speed.
		"""
		size = 0
		format_str = "<"

		for formats in self._get_format_str():
			if formats[0] is not str:
				#get size and multiply by number of occurrences here
				size += formats[0].__len__() * formats[1]
			else:
				#get usual size later from struct
				format_str += formats * formats[1]
				
		size += struct.calcsize(format_str)
		
		return size
	
	def write(self, file):
		"""FileObject -> NoneType
		Writes this class and its children to file."""
		#aliases
		fw = file.write
		sp = struct.pack
		empty_bytes = sp("<x")
		
		prop_list = zip([getattr(self, var) for var in self.__slots__], self._get_format_str())
		#tuples of (prop,(type, num_occurrences)) or tuples of (prop, format_str))
		
		for attr , fmt in prop_list: #cycle tuples of (var, type)
		#objects export themselves else, 
		# we pack according to our type instructions
		
			#do we write a regular type down? special _MetaIGClass child if not:
			is_str = type(fmt[0]) is str
			
			#struct for regular types:
			if is_str:
				local_struct_p = struct.Struct("<" + str(fmt[0])).pack
			
			#is it a list of elements?
			if fmt[1] > 1: #number of occurrence in fmt[1]		
				if is_str:			
					empty_block = empty_bytes * local_struct_p.size #length of empty class
				else:
					empty_block = empty_bytes * len(fmt[0]) #length of empty class
					
				for i in range(fmt[1]): 
					if i >= len(attr): #filling blank space
						fw(empty_block * fmt[2])
						
					elif is_str: #it's a regular object
						fw(local_struct_p(attr[i]))
						
					else:#it's a special object
						attr[i].write(file)
			
			#it's an object alone
			elif is_str: 
				#it's regular
				fw(local_struct_p(attr))
			
			else: 
				#it's special
				attr.write(file)
	
	def load(self, file):
		"""FileObject -> type(self)
		returns a new object of its type (and its children into it)
		from loaded data"""
		#alias
		fr = file.read
		
		new_obj_args = []

		prop_list = zip(self.__slots__, self._get_format_str())
		#tuples of (prop,(type, num_occurrences)) or tuples of (prop, format_str))
		
		for attr_name , fmt in prop_list: #cycle tuples of (var, type)
		#objects export themselves else, 
		# we pack according to our type instructions
		
			#do we write a regular type down? special _MetaIGClass child if not:
			is_str = type(fmt[0]) is str
			
			#struct for regular types:
			if is_str:
				local_struct = struct.Struct("<" + str(fmt[2]) + str(fmt[0]))
				sunp = local_struct.unpack
			else:
				IGClass = globals()[attr_name]
			
			#is it a list of elements?
			if fmt[1] > 1: #number of occurrence in fmt[1]					
				attr = [] #new list of objects
			
				for i in range(fmt[1]): 
					if is_str: #it's a regular object
						attr[i] = sunp(fr(local_struct.size))
						
					else:#it's a special object
						attr[i] = IGClass.load(file)
			
			#it's an object alone
			elif is_str: 
				#it's regular
				attr = sunp(fr(local_struct.size))
			
			else: 
				#it's special
				attr = IGClass.load(file)
				
			new_obj_args.append(attr)

		return self.__class__(*new_obj_args)


	def dump(self):
		"""-> NoneType
		prints this class content to stdout"""
		print("{=:<20} :".format(self.__class__.__name__))
		for var in self.__slots__:
			print("    {:<16} : {}".format(str(var), str(getattr(self, var))))
		else:
			print("    ::end vars")

	def dump_log(self):
		"""-> NoneType
		prints this class content to stdout for logging purposes"""
		self.dump()
	
	

class IGDataBlockContainer(_MetaIGClass, metaclass=LengthMetaclass):
	''' Container that details extra data blocks attached to an IG structure
		most major structures in the IG format have a data block container
	'''
	__slots__ = ("NumBlocks", "offsetBlocks", "pad0", "pad1")

	def __init__(self, 
				NumBlocks:int=0,
				offsetBlocks:int=0,
				pad0:(str, 1, MAX_OBJECT_NAME)=b'',
				pad1:(int, 2)=[0,0]):
		pad0 = pad0
		
		var_dict_to_pass_over = locals()
		del var_dict_to_pass_over["self"]
		super().__init__(**var_dict_to_pass_over)
	
	@classmethod
	def __len__(self):
		return 48 #MAX_OBJECT_NAME + 4 * SIZE_OF_INT

	def write(self, file):
		if (0, 0, b'', [0,0]) == (self.NumBlocks, self.offsetBlocks, self.pad0, self.pad1):
			file.write(b'\x00'*48) #faster shortcut
			
		else:
			file.write(struct.pack("<II{:d}s2I".format(MAX_OBJECT_NAME), self.NumBlocks, 
							self.offsetBlocks, self.pad0, 
							self.pad1[0], self.pad1[1]))
	
	@classmethod
	def load(cls, file):
		new_dblc = cls()
		buffer = file.read(len(cls))
		
		new_dblc.NumBlocks, new_dblc.offsetBlocks, \
		new_dblc.pad0, new_dblc.pad1[0], new_dblc.pad1[1] \
		= struct.unpack("<II{:d}s2I".format(MAX_OBJECT_NAME), buffer)
		
		return new_dblc

	def dump(self):
		print(" IGDataBlockContainer NumBlocks= ", self.NumBlocks, " offsetBlocks=", self.offsetBlocks, \
		"  Pad0='", self.pad0.decode(*STRING_ENCODING), "' Pad1= [", self.pad1[0], ", ", self.pad1[1],"]")

	def dump_log(self):
		if (0, 0, b'', [0,0]) == (self.NumBlocks, self.offsetBlocks, self.pad0, self.pad1):
			print("ExtraData ------------------ NULL")
		else:
			print("ExtraData ----------------------. ")
			print("  DataBlockCount                : {:d}".format(self.NumBlocks))
			print("  DataBlockStartOffset          : {:d}".format(self.offsetBlocks)) # (--)
			print("  Pad0                          : '{:s}'".format(self.pad0.decode(*STRING_ENCODING)))
			print("  Pad1                          : [", self.pad1[0], ", ", self.pad1[1],"]")

class IGsColour(_MetaIGClass, metaclass=LengthMetaclass):
# 16 bytes / r, g, b, alpha
	__slots__ = ("r", "g", "b", "a")

	def __init__(self, r:float=1.0, g:float=1.0, b:float=1.0, a:float=1.0):
		self.r, self.g, self.b, self.a = r,g,b,a
		#var_dict_to_pass_over = locals()
		#del var_dict_to_pass_over["self"]
		#super().__init__(**var_dict_to_pass_over)
	
	def __eq__(self, other):
		#same type
		if not isinstance(other, self.__class__):
			return False
		
		# weld colour
		if (abs(other.r - self.r) >= gVertexWeldColourThreshold):
			return False
		if (abs(other.g - self.g) >= gVertexWeldColourThreshold):
			return False
		if (abs(other.b - self.b) >= gVertexWeldColourThreshold):
			return False
		if (abs(other.a - self.a) >= gVertexWeldColourThreshold):
			return False
		
		return True
	
	def __hash__(self):
		return hash(self.__slots__) + self.r*1000 + self.g*100 + self.b*10 + self.a
	
	def __iter__(self):
		return iter((self.r, self.g, self.b, self.a))
	
	@classmethod
	def __len__(cls):
		return 16 #struct.calcsize("<4f")

	def write(self, file):
		#return super().write(file)
		file.write(struct.pack("<4f", self.r, self.g, self.b, self.a))
	
	@classmethod	
	def load(cls, file):
		#return super().load(file)
		buffer = file.read(len(cls))
		new_obj_args = struct.unpack("<4f", buffer)
		return cls(*new_obj_args)

	def dump(self):
		return '{Colour: {:f}, {:f}, {:f}, {:f}}'.format(self.r, self.g, self.b, self.a)

	def dump_log(self):
		print("    Red                           : {:f}".format(self.r))
		print("    Green                         : {:f}".format(self.g))
		print("    Blue                          : {:f}".format(self.b))
		print("    Alpha                         : {:f}".format(self.a))

class IGsVector4(_MetaIGClass, metaclass=LengthMetaclass):
	__slots__ = ("x", "y", "z", "w")

	def __init__(self, x:float=0.0, y:float=0.0, z:float=0.0, w:float=1.0):
# 		var_dict_to_pass_over = locals()
# 		del var_dict_to_pass_over["self"]
# 		super().__init__(**var_dict_to_pass_over)
		
		self.x = x
		self.y = y
		self.z = z
		self.w = w
	
	def __eq__(self, other):
		return (self.x == other.x and self.y == other.y and self.z == other.z 
			and self.w == other.w)
		
	def __iter__(self):
		return iter((self.x, self.y, self.z, self.w))
	
	@classmethod
	def __len__(self):
		return 16 #struct.calcsize("<4f")

	def write(self, file):
		file.write(struct.pack("<4f", self.x, self.y, self.z, self.w))
	
	@classmethod	
	def load(cls, file):
		buffer = file.read(len(cls))
		new_obj_args = struct.unpack("<4f", buffer)
		return cls(*new_obj_args) 

	def dump(self):
		print(f'   {self.x:f}, {self.y:f}, {self.z:f}, {self.w:f}')

	def dump_log(self):
		self.dump()
# 		print("  X                             : {:f}".format(self.x))
# 		print("  Y                             : {:f}".format(self.y))
# 		print("  Z                             : {:f}".format(self.z))
# 		print("  Weight                        : {:f}".format(self.w))      

class IGsMatrix4x4(_MetaIGClass, metaclass=LengthMetaclass):
	__slots__ = ("M",)

	def __init__(self, 	a:float=1.0,b:float=0.0,c:float=0.0,d:float=0.0,
						e:float=0.0,f:float=1.0,g:float=0.0,h:float=0.0,
						i:float=0.0,j:float=0.0,k:float=1.0,l:float=0.0,
						m:float=0.0,n:float=0.0,o:float=0.0,p:float=1.0):
		self.M = Matrix((	(a,b,c,d),
							(e,f,g,h),
							(i,j,k,l),
							(m,n,o,p)))
	
	@classmethod
	def new_to_TS_screenspace(self, matrix):
		""" matrix: mathutils.Matrix or nested tupples/lists
			return a new IGsMatrix4x4 after swapping Y and Z from input 4x4 matrix"""
		return IGsMatrix4x4(matrix[0][0], matrix[2][0], matrix[1][0], matrix[3][0],
							matrix[0][2], matrix[2][2], matrix[1][2], matrix[3][2],
							matrix[0][1], matrix[2][1], matrix[1][1], matrix[3][1],
							matrix[0][3], matrix[2][3], matrix[1][3], matrix[3][3])

	def get_matrix(self):
		return self.M

	def update_from_parent(self, matrix):
		self.M = matrix.inverted() * self.M
		
	def get_translation(self):
		return self.M[3][0], self.M[3][1], self.M[3][2]
	
	@classmethod
	def __len__(self):
		return 64 #struct.calcsize('<16f')

	def write(self, file):
		file.write(struct.pack('<16f', 
			self.M[0][0], self.M[0][1],self.M[0][2],self.M[0][3], 
			self.M[1][0], self.M[1][1],self.M[1][2],self.M[1][3], 
			self.M[2][0], self.M[2][1],self.M[2][2],self.M[2][3],
			self.M[3][0], self.M[3][1],self.M[3][2],self.M[3][3])
			)
	
	@classmethod
	def load(cls, file):
		new_obj = cls()
		new_obj.M[0][0], new_obj.M[0][1],new_obj.M[0][2],new_obj.M[0][3],\
		new_obj.M[1][0], new_obj.M[1][1],new_obj.M[1][2],new_obj.M[1][3],\
		new_obj.M[2][0], new_obj.M[2][1],new_obj.M[2][2],new_obj.M[2][3],\
		new_obj.M[3][0], new_obj.M[3][1],new_obj.M[3][2],new_obj.M[3][3] \
		= struct.unpack('<16f', file.read(len(cls)))
		return new_obj
		
		
	def dump_log(self):
		print("TM -----------------------------.")
		for row in range (4):
			print ('    {0:10f} {1:10f} {2:10f} {3:10f}'.format(self.M[row][0], self.M[row][1], self.M[row][2], self.M[row][3]))

class IGsBoundingBox(_MetaIGClass, metaclass=LengthMetaclass):
	__slots__ = ("mini", "maxi")

	def __init__(self, 
				mini:IGsVector4=IGsVector4(), 
				maxi:IGsVector4=IGsVector4()):
		var_dict_to_pass_over = locals()
		del var_dict_to_pass_over["self"]
		super().__init__(**var_dict_to_pass_over)

	def upgrade(self, point:IGsVector4):
		"""IGsVector4 or Vector -> NoneType
		enlarges this bbox to fit point
		point = (x, y, z)"""
		m = self.mini
		M = self.maxi
		
		m.x = min(m.x, point.x)
		m.y = min(m.y, point.y)
		m.z = min(m.z, point.z)
		
		M.x = max(M.x, point.x)
		M.y = max(M.y, point.y)
		M.z = max(M.z, point.z)
	
	@classmethod	
	def __len__(self):
		return 32 #len(self.mini.get_size()) + len(self.maxi.get_size())

	def write(self, file):
		self.mini.write(file)
		self.maxi.write(file)
	
	@classmethod	
	def load(cls, file):
		new_obj = cls()
		new_obj.mini = IGsVector4.load(file)
		new_obj.maxi = IGsVector4.load(file)
		return new_obj

	def dump(self):
		self.mini.dump()
		self.maxi.dump()

	def dump_log(self):
		print("BoundingBox --------------------.")
		print("  LowerLeftPointX               : {:f}".format(self.mini.x))
		print("  LowerLeftPointY               : {:f}".format(self.mini.y))
		print("  LowerLeftPointZ               : {:f}".format(self.mini.z))
		print("  LowerLeftPointScale           : {:f}".format(self.mini.w))       
		print("  UpperRightPointX              : {:f}".format(self.maxi.x))
		print("  UpperRightPointY              : {:f}".format(self.maxi.y))
		print("  UpperRightPointZ              : {:f}".format(self.maxi.z))
		print("  UpperRightPointScale          : {:f}".format(self.maxi.w))      

class IGsUV(_MetaIGClass, metaclass=LengthMetaclass):
	__slots__ = ("u", "v")

	def __init__(self, u:float=0.0, v:float=0.0):
# 		var_dict_to_pass_over = locals()
# 		del var_dict_to_pass_over["self"]
# 		super().__init__(**var_dict_to_pass_over)
		
		self.u = u
		self.v = v
	
	@classmethod	
	def __len__(self):
		return 8 #struct.calcsize('<2f')

	def write(self, file):
		file.write(struct.pack('<2f', self.u, self.v))
	
	@classmethod
	def load(cls, file):
		buffer = file.read(len(cls))
		new_obj_args = struct.unpack('<2f', buffer)
		return cls(*new_obj_args)
		
	def dump(self):
		return '{Vector2: {:f}, {:f}}'.format(self.u, self.v)        

	def dump_log(self):
		print("  U                             :", self.u)
		print("  V                             :", self.v)

class IGHeader(_MetaIGClass, metaclass=LengthMetaclass):
# Main file header, always written first in the IG file stream
	__slots__ = ("block_format", "mMagic", "mVersion", "mIGDescriptor", "mCommentField", "mDataStart", "mNumInstances", "mInstances", "mNumGeometry", "mGeometry", "mNumBones", \
	"mBones", "mNumMaterials", "mMaterials", "mNumLights", "mLights", "mAmbientColour", "mNumSplines", "mSplines", "mNumGenericItems", "mGenericItems", \
	"mExtraDataNumBlocks", "mExtraOffsetBlocks", "mExtraDataPad0", "mExtraDataPad1", "DataPtr")

	def __init__(self, 
		mIGDescriptor:(str,1, MAX_HEADER_DESCRIPTOR)=b"SHAPE", 
		mCommentField:(str,1, MAX_HEADER_COMMENT)="Blender IGF - this shouldn't be readable", 
		mDataStart:int=0, 
		mNumInstances:int=0, 
		mInstances:int=0, 
		mNumGeometry:int=0, 
		mGeometry:int=0, 
		mNumBones:int=0, 
		mBones:int=0, 
		mNumMaterials:int=0, 
		mMaterials:int=0, 
		mNumLights:int=0, 
		mLights:int=0,
		mAmbientColour:IGsColour=IGsColour(), 
		mNumSplines:int=0, 
		mSplines:int=0, 
		mNumGenericItems:int=0, 
		mGenericItems:int=0, 
		mExtraDataNumBlocks:int=0, 
		mExtraOffsetBlocks:int=0, 
		DataPtr:int=0
		):
		self.block_format = f"<4sI{MAX_HEADER_DESCRIPTOR}s{MAX_HEADER_COMMENT}s11I4f6I{MAX_OBJECT_NAME}s3I"

		self.mMagic = b'KIGF' # must be == gIGFMagicCode or not a valid IGF format file
		self.mVersion = 151 # current version of IGF file
		# generic comment / description field
		# comment can be anything, descriptor describes IG purpose (eg. 'shape', 'level', etc)
		assert mIGDescriptor in gIGDescriptors
		self.mIGDescriptor = mIGDescriptor
		self.mCommentField = mCommentField
		self.mDataStart = mDataStart # tags beginning of file data
		self.mNumInstances = mNumInstances # number of object instances
		self.mInstances = mInstances # number of object instances
		self.mNumGeometry = mNumGeometry # number of geometry items (meshes)
		self.mGeometry = mGeometry # Start of list of geometry items
		self.mNumBones = mNumBones # Number of bones present
		self.mBones = mBones # List of bones
		self.mNumMaterials = mNumMaterials # Number of materials
		self.mMaterials = mMaterials # Start of list of materials
		self.mNumLights = mNumLights # Number of lights
		self.mLights = mLights # Start of list of lights
		self.mAmbientColour = mAmbientColour
		self.mNumSplines = mNumSplines # Number of splines
		self.mSplines = mSplines # Start of list of splines
		self.mNumGenericItems = mNumGenericItems # Number of list of generic items
		self.mGenericItems = mGenericItems # Start of list of generic items
		self.mExtraDataNumBlocks = mExtraDataNumBlocks
		self.mExtraOffsetBlocks = mExtraOffsetBlocks # 'Face tag descriptions' in IGfDataBlocks
		self.mExtraDataPad0 = b''
		self.mExtraDataPad1 = 0, 0
		self.DataPtr = DataPtr # Custom data blocks
	
	@classmethod	
	def __len__(self):
		return HEADER_SIZE #struct.calcsize(self.block_format)

	def write(self, file):
		file.write(struct.pack(self.block_format, 
			self.mMagic, self.mVersion, self.mIGDescriptor, 
			self.mCommentField, self.mDataStart, 
			self.mNumInstances, self.mInstances, 
			self.mNumGeometry, self.mGeometry, 
			self.mNumBones, self.mBones, 
			self.mNumMaterials, self.mMaterials, 
			self.mNumLights, self.mLights, 
			self.mAmbientColour.r, self.mAmbientColour.g,self.mAmbientColour.b,self.mAmbientColour.a, 
			self.mNumSplines, self.mSplines, 
			self.mNumGenericItems, self.mGenericItems, 
			self.mExtraDataNumBlocks, self.mExtraOffsetBlocks, 
			self.mExtraDataPad0, self.mExtraDataPad1[0], self.mExtraDataPad1[1], 
			self.DataPtr)
			)
		
	@classmethod
	def load(cls, file):
		new_header = cls()
		buffer = file.read(HEADER_SIZE)
		new_header.mMagic, new_header.mVersion, new_header.mIGDescriptor, \
		new_header.mCommentField, new_header.mDataStart, \
		new_header.mNumInstances, new_header.mInstances, \
		new_header.mNumGeometry, new_header.mGeometry, \
		new_header.mNumBones, new_header.mBones, \
		new_header.mNumMaterials, new_header.mMaterials, \
		new_header.mNumLights, new_header.mLights, \
		new_header.mAmbientColour.r, new_header.mAmbientColour.g,new_header.mAmbientColour.b,new_header.mAmbientColour.a, \
		new_header.mNumSplines, new_header.mSplines, \
		new_header.mNumGenericItems, new_header.mGenericItems, \
		new_header.mExtraDataNumBlocks, new_header.mExtraOffsetBlocks, \
		new_header.mExtraDataPad0, pad1, pad2, \
		new_header.DataPtr \
		= struct.unpack(new_header.block_format, buffer)
		new_header.mExtraDataPad1 = (pad1, pad2)
		return new_header

	def dump_log(self, verbose):
		print("================================================================================")
		print("IG file header information (0)")
		print("--------------------------------------------------------------------------------")
		if verbose:
			print("MagicId                       : '{:s}'".format(self.mMagic.decode(*STRING_ENCODING)))
			print("Version                       : {:d}".format(self.mVersion))
			print("Descriptor                    : '{:s}'".format(self.mIGDescriptor.decode(*STRING_ENCODING)))
		print("CommentField                  : '{:s}'".format(self.mCommentField.decode(*STRING_ENCODING)))
		if verbose: print("DataStart                     : {:d}".format(self.mDataStart)) # (--)
		print("ObjectCount                   : {:d}".format(self.mNumInstances))
		if verbose: print("ObjectListStartOffset         : {:d}".format(self.mInstances)) # (--)
		print("MeshCount                     : {:d}".format(self.mNumGeometry))
		if verbose: print("MeshListStartOffset           : {:d}".format(self.mGeometry)) # (--)
		print("BoneCount                     : {:d}".format(self.mNumBones))
		if verbose:
			if self.mBones == 0: print("BoneListStartOffset           : 0 NULL ==> None")
			else: print("BoneListStartOffset           : {:d}".format(self.mBones))
		print("MaterialCount                 : {:d}".format(self.mNumMaterials))
		if verbose:
			print("MaterialListStartOffset       : {:d}".format(self.mMaterials)) # (--)
		print("LightCount                    : {:d}".format(self.mNumLights))
		if verbose:
			if self.mLights == 0:
				print("LightListStartOffset          : 0 NULL ==> None")
			else:
				print("LightListStartOffset          : {:d}".format(self.mLights))
			print("AmbientColor -------------------.")
			print("  Red                           : {:f}".format(self.mAmbientColour.r))
			print("  Green                         : {:f}".format(self.mAmbientColour.g))
			print("  Blue                          : {:f}".format(self.mAmbientColour.b))
			print("  Alpha                         : {:f}".format(self.mAmbientColour.a))
		print("SplineCount                   : {:d}".format(self.mNumSplines))
		if verbose:
			if self.mSplines == 0: print("SplineListStartOffset         : 0 NULL ==> None")
			else: print("SplineListStartOffset         : {:d}".format(self.mSplines))
		print("GenericItemCount              : {:d}".format(self.mNumGenericItems))
		if verbose:
			if self.mGenericItems == 0: print("GenericItemListStartOffset    : 0 NULL ==> None")
			else: print("GenericItemListStartOffset    : {:d}".format(self.mGenericItems))
			print("ExtraData ----------------------. ")
			print("  DataBlockCount                : {:d}".format(self.mExtraDataNumBlocks))
			print("  DataBlockStartOffset          : {:d}".format(self.mExtraOffsetBlocks)) # (--)
			print("  Pad0                          : '{:s}'".format(self.mExtraDataPad0.decode(*STRING_ENCODING)))
			print("  Pad1                          : [", self.mExtraDataPad1[0], ", ", self.mExtraDataPad1[1],"]")
			print("ExtraDataBlockListStartOffset : {:d}".format(self.DataPtr)) # (--) 'Face tag descriptions'


class IGBone(_MetaIGClass, metaclass=LengthMetaclass): #MODIFS2016
	'''Defines a non-mesh object, a bone used in the scene during skinning operations
		similar in form to a cIGInstance'''
	
	__slots__ = ("mName", "mNameUID", "mTM", "mParent", "mNumChildren", "mChildren", "mExtraData")

	def __init__(self, 
				mName:(str, 1, MAX_OBJECT_NAME)=b"emptybone", 
				mNameUID:int=0, 
				mTM:IGsMatrix4x4=IGsMatrix4x4(), 
				mParent:int=0, 
				mChildren:(int, MAX_EXPORTED_BONES)=[], 
				mExtraData:IGDataBlockContainer=IGDataBlockContainer()):
		mName = mName
		mNameUID = mNameUID or id(self) # unique ID for this object name, used for fast matching or hashing (UInt32)
		#mNumChildren = len(mChildren)
		
		var_dict_to_pass_over = locals()
		del var_dict_to_pass_over["self"]
		super().__init__(**var_dict_to_pass_over)
	
	@classmethod
	def __len__(self):
		return BONE_SIZE #MAX_OBJECT_NAME + 12 + 4*MAX_CHILDREN + self.mExtraData.get_size()

	def write(self, file):
		block_format = "<{:d}sI".format(MAX_OBJECT_NAME)
		file.write(struct.pack(block_format, self.mName, self.mNameUID))
		self.mTM.write(file)
		if not self.mParent:
			file.write(b'\x00\x00\x00\x00')
		else: 
			file.write(struct.pack('<I',self.mParent))
		file.write(struct.pack('<I',len(self.mChildren)))
		for i in range(0, MAX_CHILDREN):
			if i < len(self.mChildren) and i < MAX_EXPORTED_BONES:
				file.write(struct.pack('<I', self.mChildren[i]))
			else:
				file.write(b'\x00\x00\x00\x00')
		self.mExtraData.write(file)
	
	@classmethod
	def load(cls, file):
		block_format = f"<{MAX_OBJECT_NAME}sI"
		new_IGBone = cls()
		
		buffer = file.read(struct.calcsize(block_format))
		new_IGBone.mName, new_IGBone.mNameUID = struct.unpack(block_format, buffer)
		new_IGBone.mName = new_IGBone.mName.strip(b'\x00')
		
		new_IGBone.mTM = IGsMatrix4x4.load(file)
		
		buffer = file.read(8)
		new_IGBone.mParent, mNumChildren = struct.unpack("<II", buffer)
		buffer = file.read(4*MAX_CHILDREN)
		new_IGBone.mChildren = (struct.unpack(f"<{MAX_CHILDREN}I", buffer))[:int(mNumChildren)]
		
		new_IGBone.mExtraData = IGDataBlockContainer.load(file)
		
		return new_IGBone

	def dump_log(self, num_bone, bones_count, bone_offset):
		print("--------------------------------------------------------------------------------")
		print("IGfBone [ {:d} / {:d} ] ({:d})".format(num_bone, bones_count, bone_offset))
		print("------------------------------.")
		print("Name                          : '{:s}'".format(self.mName.decode(*STRING_ENCODING)))
		print("NameUniqueID                  : {:d}".format(self.mNameUID))
		self.mTM.dump_log()
		if self.mParent: print("ParentStartOffset             : {:d}".format(self.mParent))
		else: print("ParentStartOffset             : NULL")
		print("ChildrenCount                 : {:d}".format(len(self.mChildren)))
		for i in range(0, MAX_EXPORTED_BONES):
			if i < len(self.mChildren):
				if self.mChildren[i] == 0:
					print("ChildStartOffset{:02d}            : NULL".format(i))
				else:
					print("ChildStartOffset{:02d}            : {:d}".format(i, self.mChildren[i]))
#			else:
#				print("ChildStartOffset{:02d}            : 0 NULL ==> None".format(i))
		self.mExtraData.dump_log()

class IGVertexBoneBinding(_MetaIGClass, metaclass=LengthMetaclass):
	'''Defines a single skinning influence on a vertex, defined as a pointer
		back to a bone matrix and a weight that determines how much that bone 
		influences the vertex final position'''
	__slots__ = ("block_format", "mBone", "mWeight")

	def __init__(self, mBone=0, mWeight=0.0):
		self.block_format = "<If"
		
		self.mBone = mBone
		self.mWeight = mWeight
	
	@classmethod	
	def __len__(self):
		return 8 #struct.calcsize(self.block_format)

	def write(self, file):
		file.write(struct.pack(self.block_format, self.mBone, self.mWeight))
	
	@classmethod
	def load(cls, file):
		data = struct.unpack("<If", file.read(8))
		return cls(*data)
		
	def dump(self):
		return '{IGVertexBoneBinding: {:d}, {:f}}'.format(self.mBone, self.mWeight)

	def dump_log(self):
		if self.mBone == 0:        
			print("  BoneListStartOffset           : 0 NULL ==> None")
		else:
			print("  BoneListStartOffset           :", self.mBone)
		print("  Weight                        :", self.mWeight)
		

class IGRenderStage(_MetaIGClass, metaclass=LengthMetaclass):
	__slots__ = ("self", 
	"mTextureName", "mPadding", 
	"mUVChannelIndex", "mFilterMode", 
	"mUVOperation", "mUVWrapU",
	"mUVWrapV", "mMipLODBias", 
	"mAnimateUVs", "mNumFrames", 
	"mFPS", "mScrollUVs", 
	"mScrollU", "mScrollV", "mArguments")
	
	def __init__(self, 
			mTextureName:int=0, 
			mPadding:(str, 1, MAX_LEGACY_TEXTURE_NAME-4)=b'', 
			mUVChannelIndex:int=0, 
			mFilterMode:int=1, 
			mUVOperation:int=UV_OP_COPY, 
			mUVWrapU:int=UVWRAP_TILE,
			mUVWrapV:int=UVWRAP_TILE, 
			mMipLODBias:float=0.0,
			mAnimateUVs:int=0, 
			mNumFrames:int=0, 
			mFPS:int=0, 
			mScrollUVs:int=0, 
			mScrollU:float=0.0, 
			mScrollV:float=0.0, 
			mArguments:(float,6)=(0.0,0.0,0.0,0.0,0.0,0.0)
		):
		# texture name index for this stage
		self.mTextureName = mTextureName
		# padding to remain compatible with original format:
		# this space normally would have the texture name directly in it
		self.mPadding = mPadding
		self.mUVChannelIndex = mUVChannelIndex # which UV channel to use
		# UV engine-side operations
		self.mFilterMode = mFilterMode
		self.mUVOperation = mUVOperation #enum in UV_OP
		self.mUVWrapU = mUVWrapU
		self.mUVWrapV = mUVWrapV
		self.mMipLODBias = mMipLODBias
		# UV page animation
		self.mAnimateUVs = mAnimateUVs
		self.mNumFrames = mNumFrames # number of frames on texture page
		self.mFPS = mFPS
		# UV scrolling per-stage setup
		self.mScrollUVs = mScrollUVs
		self.mScrollU = mScrollU # rate to scroll per second
		self.mScrollV = mScrollV                
		# arbitary arguments setup in UI
		# purpose dependant on shader and operation mode
		self.mArguments = mArguments
		
	@classmethod
	def __len__(self):
		return 104
	
	def write(self, file):
		file.write(struct.pack("<I{:d}sII3If4I".format(MAX_LEGACY_TEXTURE_NAME-4), 
			self.mTextureName, self.mPadding, self.mUVChannelIndex, 
			self.mFilterMode, 
			self.mUVOperation, self.mUVWrapU, self.mUVWrapV, 
			self.mMipLODBias, self.mAnimateUVs, self.mNumFrames, 
			self.mFPS, self.mScrollUVs))
		file.write(struct.pack('<ff6f', 
			self.mScrollU, self.mScrollV, *self.mArguments))
	
	@classmethod
	def load(cls, file):
		ncls = cls()
		ncls.mTextureName, \
		ncls.mPadding, \
		ncls.mUVChannelIndex, \
		ncls.mFilterMode, \
		ncls.mUVOperation, \
		ncls.mUVWrapU, \
		ncls.mUVWrapV, \
		ncls.mMipLODBias, \
		ncls.mAnimateUVs, \
		ncls.mNumFrames, \
		ncls.mFPS, \
		ncls.mScrollUVs, \
		ncls.mScrollU, \
		ncls.mScrollV \
		= struct.unpack("<I{:d}sII3If4Iff".format(MAX_LEGACY_TEXTURE_NAME-4), file.read(80))
		
		ncls.mArguments = struct.unpack("<6f", file.read(24))
		return ncls
	
	def dump_log(self, verbose, rs_num):
		print("RenderStage{:d} -------------------.".format(rs_num))
		print("  TextureNameStartOffset        : {:d}".format(self.mTextureName))
		print("  Padding                       : '{:s}'".format(self.mPadding.decode(*STRING_ENCODING)))
		if verbose:
			pass
			
		print("  UVChannelIndex                : {:d}".format(self.mUVChannelIndex))
		if verbose:
			print("  FilterMode                    : {:d}".format(self.mFilterMode))
			print("  UVOperation                   : {:d}".format(self.mUVOperation))
			print("  UVWrapU                       : {:d}".format(self.mUVWrapU))
			print("  UVWrapV                       : {:d}".format(self.mUVWrapV))
			print("  MipLODBias                    : {:f}".format(self.mMipLODBias))
			print("  AnimateUVs                    : {:d}".format(self.mAnimateUVs))
			print("  NumFrames                     : {:d}".format(self.mNumFrames))
			print("  FPS                           : {:d}".format(self.mFPS))
			print("  ScrollUVs                     : {:d}".format(self.mScrollUVs))
			print("  ScrollU                       : {:f}".format(self.mScrollU))
			print("  ScrollV                       : {:f}".format(self.mScrollV))
		print("  UVArguments                   : [{:f},{:f},{:f},{:f},{:f},{:f}]".format(*self.mArguments))
				
class IGPulseGlowCfg(_MetaIGClass, metaclass=LengthMetaclass):
	__slots__ = ("mTargCol", "mMode", "mPhase", 
		"mPeriod", "mAmplitude", "mRptTimeMin",
		"mRptTimeMax", "mExeTimeMin", "mExeTimeMax", 
		"mActivationTime", "mSeqMode", "mVertexModify"
	)
	
	def __init__(self,
			mTargCol:IGsColour=IGsColour(), 
			mMode:int=PG_PULSE, 
			mPhase:float=0.0, 
			mPeriod:float=0, 
			mAmplitude:float=0, 
			mRptTimeMin:float=0,
			mRptTimeMax:float=0, 
			mExeTimeMin:float=0,
			mExeTimeMax:float=0, 
			mActivationTime:float=0, 
			mSeqMode:(bytes, 1, MAX_SEQUENCE_MODE)=b'', 
			mVertexModify:int=0
		):
		self.mTargCol = mTargCol
		self.mMode = mMode
		# if in pulse mode...
		self.mPhase = mPhase
		self.mPeriod = mPeriod
		self.mAmplitude = mAmplitude
		# if in random mode...
		self.mRptTimeMin = mRptTimeMin
		self.mRptTimeMax = mRptTimeMax
		self.mExeTimeMin = mExeTimeMin
		self.mExeTimeMax = mExeTimeMax
		self.mActivationTime = mActivationTime
		# if in sequenced mode...
		self.mSeqMode = mSeqMode
		self.mVertexModify = mVertexModify # if false, texture modify
	
	@classmethod
	def __len__(self):
		return MAX_SEQUENCE_MODE + 14 * SIZE_OF_INT
	
	def write(self, file):
		self.mTargCol.write(file)
		file.write(struct.pack(f"<I8f{MAX_SEQUENCE_MODE}sI", 
			self.mMode, self.mPhase, self.mPeriod, 
			self.mAmplitude, self.mRptTimeMin, self.mRptTimeMax, 
			self.mExeTimeMin, self.mExeTimeMax, self.mActivationTime,
			self.mSeqMode, self.mVertexModify))
		
	@classmethod
	def load(cls, file):
		colour = IGsColour.load(file)
		data = struct.unpack(f'<I8f{MAX_SEQUENCE_MODE}sI', file.read(MAX_SEQUENCE_MODE + 10 * SIZE_OF_INT))
		
		return cls(colour, *data)
		
	def dump_log(self):
		print("PulseGlowConfig ----------------.")
		print("  TargColor ----------------------.")
		self.mTargCol.dump_log()
		print("  Mode						  : ", self.mMode)
		print("  Phase						 : ", self.mPhase)
		print("  Period						: ", self.mPeriod)
		print("  Amplitude					 : ", self.mAmplitude)
		print("  RptTimeMin					: ", self.mRptTimeMin)
		print("  RptTimeMax					: ", self.mRptTimeMax)
		print("  ExeTimeMin					: ", self.mExeTimeMin)
		print("  ExeTimeMax					:", self.mExeTimeMax)
		print("  ActivationTime				:", self.mActivationTime)
		print("  SeqMode					   :", self.mSeqMode.decode(*STRING_ENCODING))
		print("  VertexModify				  :", self.mVertexModify)
		
class IGMaterials(_MetaIGClass, metaclass=LengthMetaclass):
# Defines all properties that can be assigned to a surface in a polygon mesh
	__slots__ = ("self", 
		"mName", "mShaderName", "mNumRenderStages",
		"IGRenderS", "mNeverOcclude", "mSortPriority", 
		"mZBias", "mAlphaTestMode", "mAdditiveAlphaStrength", 
		"mZBufferMode", "mBackfaceCull", "mTwoSided", 
		"mViewFacing", "mVisMod", "mSurfaceType", 
		"mUseLightGlow", "mUsePulseGlow", "mLightGlowType",
		"mIGPulseGlowCfg", "mUnfoggable", "mForce32Bit", 
		"mAmbient", "mDiffuse", "mEmissive",
		"mEmissiveStrength", "mSpecular", "mSpecularPower", 
		"mLMCastShadows", "mLMGenerateShadows", "mLMKeepVertexColours", 
		"mLMTexelsPerMetre", "mComment", "mExtraData")

	def __init__(self, 
			mName:(str, 1, MAX_MATERIAL_NAME)=b"nullMaterial", 
			mShaderName:(str, 1, MAX_SHADER_NAME)=b"invisible", 
			mNumRenderStages:int=0,
			IGRenderS:(IGRenderStage, MAX_RENDER_STAGES)=[],
			mNeverOcclude:int=0, 
			mSortPriority:int=0, 
			mZBias:int=0, 
			mAlphaTestMode:int=0, 
			mAdditiveAlphaStrength:int=0, 
			mZBufferMode:int=0,
			mBackfaceCull:int=0, 
			mTwoSided:int=0, 
			mViewFacing:int=VF_NONE, 
			mVisMod:int=0, 
			mSurfaceType:(str, 1, MAX_SURF_TYPE_NAME)=b'', 
			mUseLightGlow:int=0, 
			mUsePulseGlow:int=0, 
			mLightGlowType:(str, 1, MAX_LIGHTGLOW_TYPE)=b'',
			mIGPulseGlowCfg:IGPulseGlowCfg=IGPulseGlowCfg(),
			mUnfoggable:int=0, 
			mForce32Bit:int=0, 
			mAmbient:IGsColour=IGsColour(), 
			mDiffuse:IGsColour=IGsColour(), 
			mEmissive:IGsColour=IGsColour(),
			mEmissiveStrength:int=0, 
			mSpecular:IGsColour=IGsColour(), 
			mSpecularPower:int=0, 
			mLMCastShadows:int=0, 
			mLMGenerateShadows:int=0, 
			mLMKeepVertexColours:int=0, 
			mLMTexelsPerMetre:int=4, 
			mComment:(str, 1, MAX_MATERIAL_COMMENT)=b'', 
			mExtraData:IGDataBlockContainer=IGDataBlockContainer()
		):

		self.mName = mName # original name of material from editor UI
		self.mShaderName = mShaderName # name of active shader
		# set of multipass rendering stages
		self.mNumRenderStages = mNumRenderStages
		self.IGRenderS = IGRenderS
		# engine behavior setup
		self.mNeverOcclude = mNeverOcclude
		self.mSortPriority = mSortPriority
		self.mZBias = mZBias
		self.mAlphaTestMode = mAlphaTestMode
		self.mAdditiveAlphaStrength = mAdditiveAlphaStrength
		self.mZBufferMode = mZBufferMode
		self.mBackfaceCull = mBackfaceCull
		self.mTwoSided = mTwoSided
		self.mViewFacing = mViewFacing
		self.mVisMod = mVisMod # visible distance mod for this surface
		self.mSurfaceType = mSurfaceType # string description of surface type
		# special effects behaviors
		self.mUseLightGlow = mUseLightGlow
		self.mUsePulseGlow = mUsePulseGlow
		self.mLightGlowType = mLightGlowType
		self.mIGPulseGlowCfg = mIGPulseGlowCfg
		# behaviors promoted from comment field toggles
		self.mUnfoggable = mUnfoggable
		self.mForce32Bit = mForce32Bit
		# colouring and behavior of material surface
		self.mAmbient = mAmbient
		self.mDiffuse = mDiffuse
		self.mEmissive = mEmissive
		self.mEmissiveStrength = mEmissiveStrength
		self.mSpecular = mSpecular
		self.mSpecularPower = mSpecularPower
		# lightmap generation support
		self.mLMCastShadows = mLMCastShadows
		self.mLMGenerateShadows = mLMGenerateShadows
		self.mLMKeepVertexColours = mLMKeepVertexColours
		self.mLMTexelsPerMetre = mLMTexelsPerMetre
		self.mComment = mComment # generic 'comment' string
		self.mExtraData = mExtraData
	
	@classmethod
	def __len__(self):
		return MATERIAL_SIZE

	def write(self, file):
		file.write(struct.pack("<{:d}s".format(MAX_MATERIAL_NAME), 
			self.mName))
		file.write(struct.pack("<{:d}s".format(MAX_SHADER_NAME), 
			self.mShaderName))
		
		file.write(struct.pack('<I', self.mNumRenderStages))
		for rs in self.IGRenderS:  # total size of cIGRenderStage = MAX_RENDER_STAGES * 104 bytes
			rs.write(file)
		for _ in range(self.mNumRenderStages, MAX_RENDER_STAGES): #pad unused renderStages
			file.write(b'\x00' * len(IGRenderStage)) # 104 null bytes
			
		file.write(struct.pack("<6I", 
			self.mNeverOcclude ,self.mSortPriority, self.mZBias, 
			self.mAlphaTestMode, self.mAdditiveAlphaStrength, self.mZBufferMode))
		file.write(struct.pack("<4I{:d}s2I{:d}s".format(MAX_SURF_TYPE_NAME, MAX_LIGHTGLOW_TYPE), 
			self.mBackfaceCull, self.mTwoSided, self.mViewFacing, 
			self.mVisMod, self.mSurfaceType, self.mUseLightGlow,
			self.mUsePulseGlow, self.mLightGlowType))
		self.mIGPulseGlowCfg.write(file)
		file.write(struct.pack("<2I", 
			self.mUnfoggable, self.mForce32Bit))
		self.mAmbient.write(file)
		self.mDiffuse.write(file)
		self.mEmissive.write(file)
		file.write(struct.pack("<f", 
			self.mEmissiveStrength))
		self.mSpecular.write(file)
		file.write(struct.pack("<f3If{:d}s".format(MAX_MATERIAL_COMMENT), 
			self.mSpecularPower, self.mLMCastShadows, self.mLMGenerateShadows, 
			self.mLMKeepVertexColours, self.mLMTexelsPerMetre, self.mComment))
		self.mExtraData.write(file)
		
	@classmethod
	def load(cls, file):
		data = []
		data.extend(struct.unpack("<{:d}s{:d}sI".format(MAX_MATERIAL_NAME, MAX_SHADER_NAME), 
			file.read(MAX_MATERIAL_NAME + MAX_SHADER_NAME + SIZE_OF_INT)) )
		
		NumRenderStages = data[2]
		rs = []
		for _ in range(NumRenderStages):  # total size of cIGRenderStage = MAX_RENDER_STAGES * 104 bytes
			rs.append( IGRenderStage.load(file) )
		#jump unused renderStages
		file.seek(
			len(IGRenderStage) * (MAX_RENDER_STAGES - NumRenderStages), 
			1
			) # 104 null bytes
		data.append(rs)
		
		data.extend( struct.unpack("<6I", file.read(6*SIZE_OF_INT)) )
		data.extend( struct.unpack("<4I{:d}s2I{:d}s".format(MAX_SURF_TYPE_NAME, MAX_LIGHTGLOW_TYPE), 
			file.read(MAX_SURF_TYPE_NAME + MAX_LIGHTGLOW_TYPE + 6*SIZE_OF_INT)) )
		data.append( IGPulseGlowCfg.load(file) )
		data.extend( struct.unpack("<2I", 
			file.read(SIZE_OF_INT + SIZE_OF_INT)) )
		data.append( IGsColour.load(file) ) #ambiant
		data.append( IGsColour.load(file) ) #diffuse
		data.append( IGsColour.load(file) ) #emissive
		data.extend( struct.unpack("<f", 
			file.read(SIZE_OF_INT)) )
		data.append( IGsColour.load(file) ) #specular
		data.extend( struct.unpack("<f3If{:d}s".format(MAX_MATERIAL_COMMENT), 
			file.read(MAX_MATERIAL_COMMENT + 5*SIZE_OF_INT)) )
		data.append( IGDataBlockContainer.load(file) )
		data[0] = data[0].strip(b'\x00')
		data[1] = data[1].strip(b'\x00') #allows shader list matching
		return cls(*data)
		
	def dump_log(self, num_mat, nb_mat, mat_offset, verbose):
		print("--------------------------------------------------------------------------------")
		if verbose:
			print("IGfMaterials [ {:d} / {:d} ] ({:d}) : '{:s}'".format(num_mat, nb_mat, mat_offset, self.mName.decode(*STRING_ENCODING)))
		else:
			print("Material main parameters [ {:d} / {:d} ] : '{:s}'".format(num_mat, nb_mat, self.mName.decode(*STRING_ENCODING)))
		print("------------------------------.")
		print("Name                          : '{:s}'".format(self.mName.decode(*STRING_ENCODING)))
		print("ShaderName                    : '{:s}'".format(self.mShaderName.decode(*STRING_ENCODING)))
		print("RenderStageCount              : {:d}".format(self.mNumRenderStages))
		for i, rs in enumerate(self.IGRenderS):
			rs.dump_log(verbose, i)
		if verbose: 
			print("NeverOccludeFlag              : {:d}".format(self.mNeverOcclude))
			print("SortPriority                  : {:d}".format(self.mSortPriority))
			print("ZBias                         : {:d}".format(self.mZBias))
			print("AlphaTestMode                 : {:d}".format(self.mAlphaTestMode))
			print("AdditiveAlphaStrength         : {:d}".format(self.mAdditiveAlphaStrength))
			print("ZBufferMode                   : {:d}".format(self.mZBufferMode))
			print("BackfaceCull                  : {:d}".format(self.mBackfaceCull))
			print("TwoSided                      : {:d}".format(self.mTwoSided))
			print("ViewFacing                  : {:d}".format(self.mViewFacing))
		if verbose:
			print("VisibleDistanceMod            : {:d}".format(self.mVisMod))
			print("SurfaceTypeName               : '{:s}'".format(self.mSurfaceType.decode(*STRING_ENCODING)))
			print("UseLightGlowFlag              : {:d}".format(self.mUseLightGlow))
			print("UsePulseGlowFlag              : {:d}".format(self.mUsePulseGlow))
			print("LightGlowTypeName             : '{:s}'".format(self.mLightGlowType.decode(*STRING_ENCODING)))
			self.mIGPulseGlowCfg.dump_log()
			print("UnfoggableFlag                : {:d}".format(self.mUnfoggable))
			print("Force32BitFlag                : {:d}".format(self.mForce32Bit))
			print("AmbientColor -------------------.")
			self.mAmbient.dump_log()
			print("DiffuseColor -------------------.")
			self.mDiffuse.dump_log()
			print("EmissiveColor -------------------.")
			self.mEmissive.dump_log()
			print("EmissiveStrength              :  {:f}".format(self.mEmissiveStrength))
			print("SpecularColor ------------------.")
			self.mSpecular.dump_log()
			print("SpecularPower                 : {:f}".format(self.mSpecularPower))
		if verbose:
			print("LightMapCastShadows           : {:d}".format(self.mLMCastShadows))
			print("LightMapGenerateShadows       : {:d}".format(self.mLMGenerateShadows))
			print("LightMapKeepVertexColours     : {:d}".format(self.mLMKeepVertexColours))
			print("LightMapTexelsPerMetre        : {:f}".format(self.mLMTexelsPerMetre))
			print("MaterialComment               : '{:s}'".format(self.mComment.decode(*STRING_ENCODING)))
		if verbose:
			self.mExtraData.dump_log()

class IGVertex(_MetaIGClass, metaclass=LengthMetaclass):
# Defines single vertex in a polygon mesh
	__slots__ = ("mPoint", "mNormal", "mNumValidUVs", "mUV", "mColour", "mMaterial", 
				"mNumBones", "mBoneBinding", "mReserved", "mExtraData")

	def __init__(self, 
				mPoint:IGsVector4=IGsVector4(), 
				mNormal:IGsVector4=IGsVector4(), 
				mNumValidUVs:int=0, 
				mUV:(IGsUV, MAX_RENDER_STAGES)=[], 
				mColour:IGsColour=IGsColour(), 
				mMaterial:int=0, 
				mNumBones:int=0, 
				mBoneBinding:(IGVertexBoneBinding, MAX_EXPORTED_BONES)=[], 
				mReserved:int=0 , 
				mExtraData:IGDataBlockContainer=IGDataBlockContainer()):
		
# 		var_dict_to_pass_over = locals()
# 		del var_dict_to_pass_over["self"]
# 		super().__init__(**var_dict_to_pass_over)
		
		self.mPoint = mPoint #IGsVector4
		self.mNormal = mNormal #IGsVector4
		self.mNumValidUVs = mNumValidUVs #int
		self.mUV = mUV #list[IGsUV]
		self.mColour = mColour #IGsColour
		self.mMaterial = mMaterial #int (offset)
		self.mNumBones = mNumBones #int (count boneBindings)
		self.mBoneBinding = mBoneBinding #list[IGVertexBoneBinding]
		self.mReserved = mReserved #int #global vertex index in MAX
		self.mExtraData = mExtraData #
	
	@classmethod	
	def __len__(self):
		return VERTEX_SIZE

	def __eq__(self, other):
		# check positional absolute
		if (self.mPoint != other.mPoint):
			return False
		
		if (self.mNumValidUVs != other.mNumValidUVs):
			return False
		if (self.mNumBones != other.mNumBones):
			return False
	
		if (self.mMaterial != other.mMaterial):
			return False
	
		# weld normal
		if (abs(other.mNormal.x - self.mNormal.x) >= gVertexWeldNormalThreshold):
			return False
		if (abs(other.mNormal.y - self.mNormal.y) >= gVertexWeldNormalThreshold):
			return False
		if (abs(other.mNormal.z - self.mNormal.z) >= gVertexWeldNormalThreshold):
			return False
	
		# weld colour
		if other.mColour != self.mColour:
			return False
	
		# check UVs for all uv maps
		for UV1, UV2 in zip(other.mUV, self.mUV):  # MAJ_1_4_0
			if (abs(UV1.u - UV2.u) >= gVertexWeldUVThreshold):
				return False
			if (abs(UV1.v - UV2.v) >= gVertexWeldUVThreshold):
				return False
		
		return True

	def write(self, file):
		self.mPoint.write(file)
		self.mNormal.write(file)
		file.write(struct.pack('I', self.mNumValidUVs))
		for i in range(MAX_RENDER_STAGES):
			if i < self.mNumValidUVs:
				self.mUV[i].write(file)
			else:
				file.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')
		self.mColour.write(file)
		file.write(struct.pack("<2I", self.mMaterial, self.mNumBones))
		for i in range(MAX_EXPORTED_BONES): # cIGVertexBoneBinding
			if i < self.mNumBones:
				self.mBoneBinding[i].write(file)
			else:
				file.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')
		file.write(struct.pack("<I", self.mReserved))
		self.mExtraData.write(file)

	@classmethod
	def load(cls, file):
		#return super().load(file)
		ncls = cls()
		
		ncls.mPoint = IGsVector4.load(file)
		ncls.mNormal = IGsVector4.load(file)
		ncls.mNumValidUVs, = struct.unpack('I', file.read(SIZE_OF_INT))#',' to turn tuple to int
		ncls.mUV = [
			IGsUV.load(file) for _ in range(MAX_RENDER_STAGES)
			][:ncls.mNumValidUVs]
		ncls.mColour = IGsColour.load(file)
		ncls.mMaterial, ncls.mNumBones = struct.unpack("<2I", file.read(2*SIZE_OF_INT))
		ncls.mBoneBinding = [
			IGVertexBoneBinding.load(file) for _ in range(MAX_EXPORTED_BONES)
			][:ncls.mNumBones]
		ncls.mReserved, = struct.unpack("<I", file.read(SIZE_OF_INT))
		ncls.mExtraData = IGDataBlockContainer.load(file)
		
		return ncls
		
	def dump_log(self, num_vert, nb_vert, vert_offset):
		print("--------------------------------------------------------------------------------")
		print("IGfVerts [ {:d} / {:d} ] ({:d})".format(num_vert, nb_vert, vert_offset))
		print("------------------------------.")
		print("Point --------------------------.")
		self.mPoint.dump_log()
		print("Normal -------------------------.")
		self.mNormal.dump_log()
		print("ValidUVsCount                 : {:d}".format(self.mNumValidUVs))
		for i, uv in enumerate(self.mUV):
			print(f"UV0{i} ---------------------------.")
			uv.dump_log()
		print("Color --------------------------.")
		self.mColour.dump_log()
		print("MaterialStartOffset           : {:d}".format(self.mMaterial))
		print("BoneCount                     : {:d}".format(self.mNumBones))
		for i, bb in enumerate(self.mBoneBinding):
			print(f"BoneBinding0{i} ------------------.")
			bb.dump_log()
		print(f"Reserved                      : {self.mReserved}")
		self.mExtraData.dump_log()

class IGTriangle(_MetaIGClass, metaclass=LengthMetaclass):
# Defines a triangle representing a face in a polygon mesh
	__slots__ = ("self", 
				"mVertices", 
				"mNormal", 
				"mHiddenEdges", 
				"mMaterial", 
				"mSMGroup", 
				"mTagId", 
				"mExtraData", "vertices_count_start"
			)
	def __init__(self, 
				mVertices:(int, 3)=(0,0,0), 
				mNormal:IGsVector4=IGsVector4(), 
				mHiddenEdges:int=0, 
				mMaterial:int=0, 
				mSMGroup:int=0, 
				mTagId:int=0, 
				mExtraData:IGDataBlockContainer=IGDataBlockContainer(), 
				vertices_count_start:int=0): # three vertices making up this triangle
		self.mVertices = [
			mVertices[0] + vertices_count_start, 
			mVertices[1] + vertices_count_start, 
			mVertices[2] + vertices_count_start] # Vertex position in object space
		self.mNormal = mNormal # face normal
		self.mHiddenEdges = mHiddenEdges # edge visibility flags (EDGE_V0_V1_HIDDEN, etc)
		self.mMaterial = mMaterial # assigned material
		self.mSMGroup = mSMGroup # smoothing group ID from editor (if applicable - eg. MAX)
		self.mTagId = mTagId # per-face tag
		self.mExtraData = mExtraData # per-face extra data        
	
	@classmethod	
	def __len__(self):
		return TRIANGLE_SIZE

	def write(self, file):
		file.write(struct.pack('<3I', self.mVertices[0], self.mVertices[1], self.mVertices[2]))
		self.mNormal.write(file)
		file.write(struct.pack('<4I', self.mHiddenEdges, self.mMaterial, self.mSMGroup, self.mTagId))
		self.mExtraData.write(file)

	@classmethod
	def load(cls, file):
		ncls = cls()
		
		ncls.mVertices = struct.unpack('<3I', file.read(3*SIZE_OF_INT))
		ncls.mNormal = IGsVector4.load(file)
		ncls.mHiddenEdges, ncls.mMaterial, ncls.mSMGroup, ncls.mTagId \
		= struct.unpack('<4I', file.read( 4 * SIZE_OF_INT ))
		ncls.mExtraData = IGDataBlockContainer.load(file)
		
		return ncls
	
	def dump_log(self, num_tri, nb_tri, tri_offset):
		print("--------------------------------------------------------------------------------")
		print("IGfTriangles [ {:d} / {:d} ] ({:d})".format(num_tri, nb_tri, tri_offset))
		print("------------------------------.")
		print("Vertex0                       : {:d}".format(self.mVertices[0])) # (--)
		print("Vertex1                       : {:d}".format(self.mVertices[1])) # (--)
		print("Vertex2                       : {:d}".format(self.mVertices[2])) # (--)
		print("Normal -------------------------.")
		self.mNormal.dump_log()
		if   self.mHiddenEdges == EDGE_V0_V1_HIDDEN:
			print("HiddenEdges                   : V0 V1")
		elif self.mHiddenEdges == EDGE_V1_V2_HIDDEN:
			print("HiddenEdges                   : V1 V2")
		elif self.mHiddenEdges == EDGE_V2_V3_HIDDEN:
			print("HiddenEdges                   : V2 V0")
		else:
			print("HiddenEdges                   : {:d}".format(self.mHiddenEdges))
		print("MaterialStartOffset           : {:d}".format(self.mMaterial)) # (--)
		print("SMGroup                       : {:d}".format(self.mSMGroup))
		print("TagID                         : {:d}".format(self.mTagId))
		self.mExtraData.dump_log()

class IGGeom(_MetaIGClass, metaclass=LengthMetaclass):
# a geometry node encapsulates all data required to define a complete polygon mesh
# note that this data may be referenced and shared amongst various instances in the scene
	__slots__ = (
			"self", 
			"mIsSkinned", 
			"mNumVertices", "mVertices", 
			"mNumTriangles", "mTriangles", 
			"mBoundingBox", 
			"mExtraData"
		)

	def __init__(self, 
				mIsSkinned:int=0, 
				mNumVertices:int=0, 
				mVertices:int=0, 
				mNumTriangles:int=0, 
				mTriangles:int=0, 
				mBoundingBox:IGsBoundingBox=IGsBoundingBox(), 
				mExtraData:IGDataBlockContainer=IGDataBlockContainer()
			):
		self.mIsSkinned = mIsSkinned # has skinning information in the vertices  
		self.mNumVertices = mNumVertices # number of vertices in mVertexList  
		self.mVertices = mVertices # array of vertices used by this node  
		self.mNumTriangles = mNumTriangles # number of triangles in mTriangleList  
		self.mTriangles = mTriangles # triangles forming the surface of this mesh  
		self.mBoundingBox = mBoundingBox # bounding volume for all node verts  
		self.mExtraData = mExtraData # per-node extra data  
	
	@classmethod	
	def __len__(self):
		return GEOM_SIZE

	def write(self, file):
		file.write(struct.pack('<5I', self.mIsSkinned, self.mNumVertices, self.mVertices, self.mNumTriangles, self.mTriangles))
		self.mBoundingBox.write(file)
		self.mExtraData.write(file)

	@classmethod
	def load(cls, file):
		return cls(
			*struct.unpack('<5I', file.read(20)),
			IGsBoundingBox.load(file),
			IGDataBlockContainer.load(file)
			)

	def dump_log(self, num_geom, nb_geom, geom_offset):
		print("--------------------------------------------------------------------------------")
		print("IGfMeshes [ {:d} / {:d} ] ({:d})".format(num_geom, nb_geom, geom_offset))
		print("------------------------------.")
		print("IsSkinned                     : {:d}".format(self.mIsSkinned))
		print("VerticesCount                 : {:d}".format(self.mNumVertices))
		print("VerticesStartOffset           : {:d}".format(self.mVertices)) # (--)
		print("TrianglesCount                : {:d}".format(self.mNumTriangles))
		print("TrianglesStartOffset          : {:d}".format(self.mTriangles)) # (--)
		self.mBoundingBox.dump_log()
		self.mExtraData.dump_log()

class IGGeometryLOD(_MetaIGClass, metaclass=LengthMetaclass):

	__slots__ = ("self", "VisibleDistance", "pGeometry", "mExtraData")

	def __init__(self, 
				VisibleDistance:float=1000.0, 
				pGeometry:int=0, 
				mExtraData:IGDataBlockContainer=IGDataBlockContainer()
			):
		self.VisibleDistance = VisibleDistance # distance that LOD is visible
		self.pGeometry = pGeometry # mesh
		self.mExtraData = mExtraData # lod-level extra data
		
	@classmethod
	def __len__(self):
		return GEOMLOD_SIZE

	def write(self, file):
		file.write(struct.pack('<fI', float(self.VisibleDistance),self.pGeometry))
		self.mExtraData.write(file)
		
	@classmethod
	def load(cls, file):
		return cls(
			*struct.unpack('<fI', file.read(8)),
			IGDataBlockContainer.load(file)
			)
		
	def dump_log(self, num_geomLOD, nb_geomLOD, geomLOD_offset):
		print("--------------------------------------------------------------------------------")
		print("IGfMeshLODs [ {:d} / {:d} ] ({:d})".format(num_geomLOD, nb_geomLOD, geomLOD_offset))
		print("------------------------------.")
		print("VisibleDistance               : {:f}".format(float(self.VisibleDistance)))
		print("MeshListStartOffset           : {:d}".format(self.pGeometry)) # (--)
		self.mExtraData.dump_log()

class IGInstance(_MetaIGClass, metaclass=LengthMetaclass):
	"""an instance binds translational information to a polygon mesh / IGfObject"""
	
	__slots__ = "self", "mName", "mNameUID", "mNumLODs", "mGeometry", "mTM", "mParent", "mNumChildren", "mChildren", \
	"mExtraData", "mInitialTM", "parent_group", "child_groups_list"

	def __init__(self, 
				mName:(str, 1, MAX_OBJECT_NAME)=b'null',
				mNameUID:int=1234, 
				mNumLODs:int=1, 
				mGeometry:int=0, 
				mTM:IGsMatrix4x4=IGsMatrix4x4(), 
				mParent:int=0, 
				mNumChildren:int=0, 
				mChildren:(int, MAX_CHILDREN)=[],
				mExtraData:int=0, 
				mInitialTM:IGsMatrix4x4=IGsMatrix4x4(), 
				parent_group:int=None, 
				child_groups_list:(int, MAX_CHILDREN)=None
			):
		self.mName = mName  # original name of object in editor 
		self.mNameUID = mNameUID # unique ID for this object name, used for fast matching or hashing 
		self.mNumLODs = mNumLODs # number of LODs stored in mGeometry 
		self.mGeometry = mGeometry # pointers back to geometryLODs 
		self.mTM = mTM  # transformation (Matrix 4 x 4) for igs object
		# hierarchy management  
		self.mParent = mParent # parent node, None if root of hierarchy 
		self.mNumChildren = mNumChildren # number of children in mChildren list 
		self.mChildren = mChildren  # 1 or more children instances 
		self.mExtraData = mExtraData # per-instance extra data
		#
		# (initial) transformation (Matrix 4 x 4)
		self.mInitialTM = mInitialTM
		self.parent_group = parent_group # None if root of hierarchy (from group_wrapper)
		self.child_groups_list = child_groups_list  # 1 or more children instances (from group_wrapper)
		
	@classmethod
	def __len__(self):
		return INSTANCE_SIZE

	def write(self, file):
		block_format = "<{:d}s".format(MAX_OBJECT_NAME)
		file.write(struct.pack(block_format, self.mName))
		file.write(struct.pack('<3I', self.mNameUID, self.mNumLODs, self.mGeometry))
		self.mTM.write(file)
		file.write(struct.pack('<2I', self.mParent, self.mNumChildren))
		for i in range(0, MAX_CHILDREN):
			if i < len(self.mChildren):
				file.write(struct.pack('<I', self.mChildren[i]))
			else:
				file.write(b'\x00\x00\x00\x00')
		self.mExtraData.write(file)
	
	@classmethod
	def load(self, file):
		n_cls = self()
		
		n_cls.mName, \
		n_cls.mNameUID,\
		n_cls.mNumLODs,\
		n_cls.mGeometry \
		= struct.unpack("<{:d}s3I".format(MAX_OBJECT_NAME), file.read(MAX_OBJECT_NAME + 12))#3*SIZE_OF_INT))
		
		n_cls.mTM = IGsMatrix4x4.load(file)
		
		n_cls.mParent, n_cls.mNumChildren = struct.unpack('<2I', file.read(8))
		n_cls.mChildren = [ 
			( struct.unpack('<I', file.read(4)) )[0] 
			for _ in range(MAX_CHILDREN) 
			][:int(n_cls.mNumChildren)]
			
		n_cls.mExtraData = IGDataBlockContainer.load(file)
		
		return n_cls
		
	def dump_log(self, num_Obj, nb_Obj, Obj_offset):
		print("--------------------------------------------------------------------------------")
		print("IGfObjects [ {:d} / {:d} ] ({:d})".format(num_Obj, nb_Obj, Obj_offset))
		print("------------------------------.")
		print("Name                          : '{:s}'".format(self.mName.decode(*STRING_ENCODING)))
		print("NameUniqueID                  : {:d}".format(self.mNameUID))
		print("MeshLODCount                  : {:d}".format(self.mNumLODs))
		print("MeshLODListStartOffset        : {:d}".format(self.mGeometry)) # (--)
		self.mTM.dump_log()
		print("ParentStartOffset             : {:d}".format(self.mParent)) # (--)
		print("ChildrenCount                 : {:d}".format(self.mNumChildren))
		for i in range(0, MAX_CHILDREN):
			if i < len(self.mChildren):
				if self.mChildren[i] == 0:
					print("ChildStartOffset{:02d}            : NULL".format(i))
				else:
					print("ChildStartOffset{:02d}            : {:d}".format(i, self.mChildren[i]))
#			else:
#				print("ChildStartOffset{:02d}            : 0 NULL ==> None".format(i))
		self.mExtraData.dump_log()

class IGLight(): #MODIFS2016
	"""defines a physical light exported from the editor"""
	
	__slots__ = "self", "mName", "mPoint", "mDirection", "mColour", "mIntensity", "mCastShadows", "mType", \
	"mAttenuation", "mFlags", "mEffectName", "mNearAttenuationStart", "mNearAttenuationEnd", \
	"mFarAttenuationStart", "mFarAttenuationEnd", "mDecayStart", "mConeHotSpotAngle", "mConeFallOffAngle", \
	"mIsAreaLight", "mAreaLightRadius", "mExtraData"
	
	def __init__(self, mName, mPoint, mDirection, mColour, mIntensity, mCastShadows, mType, \
	mAttenuation, mFlags, mEffectName, mNearAttenuationStart, mNearAttenuationEnd, \
	mFarAttenuationStart, mFarAttenuationEnd, mDecayStart, mConeHotSpotAngle, mConeFallOffAngle, \
	mIsAreaLight, mAreaLightRadius, mExtraData):
		self.mName = mName[:MAX_OBJECT_NAME]	#original name of object in editor {Char8}
		
		self.mPoint = mPoint								#light origin {Vector4}
		self.mDirection = mDirection						#directional vector {Vector4}
		self.mColour = mColour								#colour of light emitted {IGColour}
		self.mIntensity = mIntensity						#multiplier for colour emitted {Float32}
		
		self.mCastShadows = int(mCastShadows)				#obvious {IGBool=UInt32}
		
		self.mType = mType									#type of light {IGLightType=UInt32}
		self.mAttenuation = mAttenuation					#type of attenuation {IGLightAttenuation=UInt32}
		self.mFlags = int(mFlags)							#any light flags used (LIGHT_FLAG_... etc) {UInt32}
		
		self.mEffectName = mEffectName[:MAX_EFFECT_NAME]#named light effect {Char8}
		
		#parameters describing falloff				; in metres
		#(only applicable to linear attenuation)
		self.mNearAttenuationStart = mNearAttenuationStart	# {Float32}
		self.mNearAttenuationEnd = mNearAttenuationEnd		# {Float32}
		self.mFarAttenuationStart = mFarAttenuationStart	# {Float32}
		self.mFarAttenuationEnd = mFarAttenuationEnd		# {Float32}
		
		#parameter describing where decay starts	; in metres
		#(only applicable to inverse/inverse squared attenuation)
		self.mDecayStart = mDecayStart 						#{Float32}
		
		#parameters describing size of cone			; in radians
		#(for spot light)
		self.mConeHotSpotAngle = mConeHotSpotAngle			#angle from axis to hot spot edge {Float32}
		self.mConeFallOffAngle = mConeFallOffAngle			#angle from axis to cone edge {Float32}
		
		#area lighting support
		#(spherical)
		self.mIsAreaLight = int(mIsAreaLight)				#needs to operate as area light {IGBool=UInt32}
		self.mAreaLightRadius = mAreaLightRadius			#radius of area light {Float32}
		
		self.mExtraData = mExtraData						#per-light extra data {IGDataBlockContainer}

	def get_size(self):
		return 228 #120 + 4*16 + 44
		
	def write(self, file):
		block_format = "<{:d}s".format(MAX_OBJECT_NAME)
		file.write(struct.pack(block_format, self.mName))
		self.mPoint.write(file)
		self.mDirection.write(file)
		self.mColour.write(file)
		file.write(struct.pack('<f4I', self.mIntensity, self.mCastShadows, self.mType, self.mAttenuation, self.mFlags))
		block_format = "<{:d}s".format(MAX_EFFECT_NAME)
		file.write(struct.pack(block_format, self.mEffectName))
		file.write(struct.pack('<4f', self.mNearAttenuationStart, self.mNearAttenuationEnd, self.mFarAttenuationStart, self.mFarAttenuationEnd))
		file.write(struct.pack('<3f', self.mDecayStart, self.mConeHotSpotAngle, self.mConeFallOffAngle))
		file.write(struct.pack('<If', self.mIsAreaLight, self.mAreaLightRadius))
		self.mExtraData.write(file)
		
	def dump_log(self, num_Light, nb_Light, Light_offset):
		print("--------------------------------------------------------------------------------")
		print("IGLight [ {:d} / {:d} ] ({:d})".format(num_Light, nb_Light, Light_offset))
		print("------------------------------.")
		print("Name                          : '{:s}'".format(self.mName.decode(*STRING_ENCODING)))
		print("Point                         :")
		self.mPoint.dump_log()
		print("Direction                     :")
		self.mDirection.dump_log()
		print("Colour                        :")
		self.mColour.dump_log()
		print("Intensity                     :", self.mIntensity)
		print("CastShadows                   :", self.mCastShadows)
		print("-----")
		print("Type                          :", self.mType)
		print("Attenuation                   :", self.mAttenuation)
		print("mFlags                        :", self.mFlags)
		print("mEffectName                   :", self.mEffectName.decode(*STRING_ENCODING))
		print("-----")
		print("NearAttenuationStart          :", self.mNearAttenuationStart)
		print("NearAttenuationEnd            :", self.mNearAttenuationEnd)
		print("FarAttenuationStart           :", self.mFarAttenuationStart)
		print("FarAttenuationEnd             :", self.mFarAttenuationEnd)
		print("-----")
		print("DecayStart                    :", self.mDecayStart)
		print("-----")
		print("ConeHotSpotAngle              :", self.mConeHotSpotAngle)
		print("ConeFallOffAngle              :", self.mConeFallOffAngle)
		print("-----")
		print("IsAreaLight                   :", self.mIsAreaLight)
		print("AreaLightRadius               :", self.mAreaLightRadius)
		self.mExtraData.dump_log()
		print("--------------------------------------------------------------------------------")

class IGSplineKnot(_MetaIGClass, metaclass=LengthMetaclass): #MODIFS2016
	"""defines a single spline knot plus its two vector handles"""
	__slots__ = "self", "mPoint", "mInVec", "mOutVec"

	def __init__(self, 
				mPoint:IGsVector4=IGsVector4(), 
				mInVec:IGsVector4=IGsVector4(), 
				mOutVec:IGsVector4=IGsVector4()
				):
		self.mPoint = mPoint	# in splinespace (object space) 
		self.mInVec = mInVec	# also in splinespace, *not* relative to knot mPoint
		self.mOutVec = mOutVec	# also in splinespace, *not* relative to knot mPoint
		
	@classmethod
	def __len__(self):
		return 48

	def write(self, file):
		self.mPoint.write(file)
		self.mInVec.write(file)
		self.mOutVec.write(file)
		
	@classmethod
	def load(cls, file):
		data = (
			IGsVector4.load(file),
			IGsVector4.load(file),
			IGsVector4.load(file)
			)
		return cls(*data)
		
	def dump_log(self, num_SplineKnot, nb_SplineKnot, SplineKnot_offset):
		print("--------------------------------------------------------------------------------")
		print("IGfSplineKnot [ {:d} / {:d} ] ({:d})".format(num_SplineKnot, nb_SplineKnot, SplineKnot_offset))
		print("------------------------------.")
		print("Point                         :")
		self.mPoint.dump_log()
		print("InVec                         :")
		self.mInVec.dump_log()
		print("OutVec                        :")
		self.mOutVec.dump_log()
		print("--------------------------------------------------------------------------------")	

class IGSpline(): #MODIFS2016
	"""a basic representation of a bezier spline"""
	
	__slots__ = "self", "mName", "mNameUID", "mNumKnots", "mKnots", "mTM", "mIsClosed", "mExtraData"

	def __init__(self, mName, mNameUID, mNumKnots, mKnots, mTM, mIsClosed, mExtraData):
		self.mName = mName	# original name of object in editor {Char8}
		self.mNameUID = mNameUID		# unique ID for this object name, used for fast matching or hashing {UInt32}
		self.mNumKnots = mNumKnots		# number of knots present {UInt32}
		self.mKnots = mKnots			# pointers to list of knot data {ArrayPointer=UInt32}
		self.mTM = mTM 					# transformation {Matrix4x4}
		self.mIsClosed = mIsClosed		# is spline a closed loop? {IGBool=UInt32}
		self.mExtraData = mExtraData	# per-instance extra data {UInt32}
		
	def get_size(self):
		return 160 #64 + 48 + 48 bytes

	def write(self, file):
		block_format = "<{:d}s".format(MAX_OBJECT_NAME)
		file.write(struct.pack(block_format, self.mName))
		file.write(struct.pack('<3I', self.mNameUID, self.mNumKnots, self.mKnots))
		self.mTM.write(file)
		file.write(struct.pack('<I', self.mIsClosed))
		self.mExtraData.write(file)

	def dump_log(self, num_Spl, nb_Spl, Spl_offset):
		print("--------------------------------------------------------------------------------")
		print("IGfSplines [ {:d} / {:d} ] ({:d})".format(num_Spl, nb_Spl, Spl_offset))
		print("------------------------------.")
		print("Name                          : '{:s}'".format(self.mName.decode(*STRING_ENCODING)))
		print("NameUniqueID                  : {:d}".format(self.mNameUID))
		print("Num Knots                  : {:d}".format(self.mNumKnots))
		print("Knots array        : {:d}".format(self.mKnots)) # (--)
		self.mTM.dump_log()
		print("Is Closed             : {:d}".format(self.mIsClosed)) # (--)
		self.mExtraData.dump_log()

class IGDataBlock(_MetaIGClass, metaclass=LengthMetaclass):

	__slots__ = ("mName", "mID", "mData", "mSize")

	def __init__(self, 
				mName:(str, 1, MAX_OBJECT_NAME)=b"invalid", 
				mID:int=BLOCK_INVALID, 
				mData:int=0, 
				mSize:int=0):
		self.mName = mName  # name of data block
		self.mID = mID  # unique id for this type (id(self) if mID eval to <false>)
		self.mData = mData  # pointer to arbitrary data
		self.mSize = mSize  # size of data
	
	@classmethod
	def __len__(self):
		return DATABLOCK_SIZE

	def write(self, file):
		file.write(struct.pack("<{:d}s3I".format(MAX_OBJECT_NAME), 
                               self.mName, self.mID, self.mData, self.mSize))
	
	@classmethod
	def load(cls, file):
		buffer = file.read(len(cls))
		new_obj_args = struct.unpack("<{:d}s3I".format(MAX_OBJECT_NAME), buffer)
		return cls(*new_obj_args)
	
	def dump_log(self, num_dataBlock, nb_dataBlock, dataBlock_offset):
		print("--------------------------------------------------------------------------------")
		print("IGfDataBlocks [ {:d} / {:d} ] ({:d})".format(num_dataBlock, nb_dataBlock, dataBlock_offset))
		print("------------------------------.")
		print("Name                          : '{:s}'".format(self.mName.decode(*STRING_ENCODING)))
		print("UniqueID                      : {:d}".format(self.mID))
		print("DataStartOffset               : {:d}".format(self.mData)) # (--)
		print("DataSize                      : {:d}".format(self.mSize))
		print("--------------------------------------------------------------------------------")

class IGGenericSceneData(_MetaIGClass, metaclass=LengthMetaclass): #MODIFS2016
	'''Data stored in a cIGGenericSceneItem, returned from an interface call via
		gIGDataGenericDataInterfaceID (see top of header)'''
	
	__slots__ = "self", "mType", "mICustomParam", "mFCustomParam", "mExtraData"

	def __init__(self, 
				mType:int=0, 
				mICustomParam:(int,4)=(0,0,0,0), 
				mFCustomParam:(float, 4)=(0.0,0.0,0.0,0.0), 
				mExtraData:IGDataBlockContainer=IGDataBlockContainer()
				):
		self.mType = mType  # some numerical ID for item (Int32)
		self.mICustomParam = mICustomParam  # int configurable parameter (Int32)
		self.mFCustomParam = mFCustomParam  # float configurable parameter (Float32)
		self.mExtraData = mExtraData  # per-node extra data  (IGDataBlockContainer)
	
	@classmethod	
	def __len__(self):
		return 72

	def write(self, file):
		file.write(struct.pack('<I', self.mType))
		for j in range(4):
			file.write(struct.pack('<I', self.mICustomParam[j]))
		for j in range(4):
			file.write(struct.pack('<f', self.mFCustomParam[j]))
		self.mExtraData.write(file)
		
	@classmethod
	def load(cls, file):
		ncls = cls()
		data = struct.unpack('<5I4f', file.read(36))
		ncls.mType = data[0]
		ncls.mICustomParam = tuple(data[1:4])
		ncls.mFCustomParam = tuple(data[5:8])
		ncls.mExtraData = IGDataBlockContainer.load(file)
		return ncls
		
	def dump_log(self, GenericSceneData_offset):
		print("--------------------------------------------------------------------------------")
		print("IGGenericSceneData ({:d})".format( GenericSceneData_offset))
		print("------------------------------.")
		print("Type                          : '{0}'".format(self.mType))
		print("mICustomParam                 : {0}".format(self.mICustomParam))
		print("mFCustomParam                 : {0}".format(self.mFCustomParam))
		self.mExtraData.dump_log()
		print("--------------------------------------------------------------------------------")

class IGGenericSceneItem(_MetaIGClass, metaclass=LengthMetaclass): #MODIFS2016
	'''A simple area / point definition item that can be used to add simple triggers
		or tags to the IG file without having to change the format'''
	
	__slots__ = ("self", "mName", "mNameUID", "mTM", "mBoundingBox", "mParent", "mData")

	def __init__(self, 
				mName:(str, 1, MAX_OBJECT_NAME)='null',
				mNameUID:int=1234,
				mTM:IGsMatrix4x4=IGsMatrix4x4(),
				mBoundingBox:IGsBoundingBox=IGsBoundingBox(),
				mParent:int=0,
				mData:IGGenericSceneData=IGGenericSceneData(),
			):
		self.mName = mName  # original name of object in editor (Char8)
		self.mNameUID = mNameUID # unique ID for this object name, used for fast matching or hashing (UInt32)
		self.mTM = mTM  # transformation matrix (4 x 4)
		self.mBoundingBox = mBoundingBox # Bounding volume, if applicable (igs_bounding_box)
		self.mParent = mParent # parent node, NULL if none (offset de IGInstance)
		self.mData = mData # actual item data (offset de IGGenericSceneData)
	
	@classmethod	
	def __len__(self):
		return GSCITEMS_SIZE

	def write(self, file):
		block_format = "<{:d}s".format(MAX_OBJECT_NAME)
		file.write(struct.pack(block_format, self.mName))
		file.write(struct.pack('<I', self.mNameUID))
		self.mTM.write(file)
		self.mBoundingBox.write(file)
		file.write(struct.pack('<I', self.mParent))
		self.mData.write(file)
	
	@classmethod
	def load(cls, file):
		ncls = cls()
		
		ncls.mName, ncls.mNameUID \
		= struct.unpack(f"<{MAX_OBJECT_NAME}sI", 
			file.read(MAX_OBJECT_NAME + SIZE_OF_INT))
		ncls.mName = ncls.mName.strip(b'\x00')
		
		ncls.mTM = IGsMatrix4x4.load(file)
		ncls.mBoundingBox = IGsBoundingBox.load(file)
		
		ncls.mParent, = struct.unpack('<I', file.read(SIZE_OF_INT))
		
		ncls.mData = IGGenericSceneData.load(file)
		
		return ncls
	
	def dump_log(self, num_GenericSceneItem, nb_GenericSceneItem, GenericSceneItem_offset):
		print("--------------------------------------------------------------------------------")
		print("IGfGenericSceneItem [ {:d} / {:d} ] ({:d})".format(num_GenericSceneItem, nb_GenericSceneItem, GenericSceneItem_offset))
		print("------------------------------.")
		print("Name                          : '{:s}'".format(self.mName.decode(*STRING_ENCODING)))
		print("NameUniqueID                  : {:d}".format(self.mNameUID))
		self.mTM.dump_log()
		self.mBoundingBox.dump_log()
		print("Parent                        : {:d}".format(self.mParent))
		self.mData.dump_log(GenericSceneItem_offset - 72)

class IGFaceTagDescription(_MetaIGClass, metaclass=LengthMetaclass):

	__slots__ = ("FaceTagDescription",)

	def __init__(self, 
		ListOfTags:(str, MAX_FACE_TAG_DESCS, MAX_OBJECT_NAME)=[]
		):
		assert type(ListOfTags) is list, "Tags list is not a list!"
		#var_dict_to_pass_over = locals()
		#del var_dict_to_pass_over["self"]
		#super().__init__(**var_dict_to_pass_over)
		self.FaceTagDescription = ListOfTags
		
	@classmethod	
	def __len__(self):
		return MAX_FACE_TAG_DESCS * MAX_OBJECT_NAME

	def write(self, file):
		#super().write(file)
		block_format = f"<{MAX_OBJECT_NAME}s"
		for i in range(len(self.FaceTagDescription)):
			file.write(struct.pack(block_format, self.FaceTagDescription[i]))
		file.write(b'\x00'*(MAX_OBJECT_NAME * (MAX_FACE_TAG_DESCS - len(self.FaceTagDescription))) )
	@classmethod
	def load(cls, file):
		#return super().load(file)
		
		block_format = "<"+f"{MAX_OBJECT_NAME}s"*MAX_FACE_TAG_DESCS
		return cls(
			list(struct.unpack(block_format, file.read(MAX_OBJECT_NAME * MAX_FACE_TAG_DESCS)))
			)
			
	
	def dump_log(self, dataBlock_offset):
		print('IGfFaceTagDescriptions        : [ 1 ]')
		print('--------------------------------------------------------------------------------')
		print("IGfFaceTagDescriptions [ 1 / 1 ] ({:d})".format(dataBlock_offset))
		print('------------------------------.')
		print('FaceTagDescriptionList ---------.') 
		for i in range(0, len(self.FaceTagDescription)):
			print("  FaceTagDescription[{:d}]        : '{:s}'".format((i+1), self.FaceTagDescription[i].decode(*STRING_ENCODING)))
		for i in range(len(self.FaceTagDescription), MAX_FACE_TAG_DESCS):
			print("  FaceTagDescription[{:d}]        :".format(i+1))
		
class IGTextureNames(_MetaIGClass, metaclass=LengthMetaclass):
	''' Container for texture names with no length limit (namespaced)
	'''
	__slots__ = ("SizeStringtable", "mNumStrings", "ListOfStrings", "TextureNameStartOffset")

	def __init__(self, ListOfStrings:(str, 1)=[]):
		self.SizeStringtable = 0 # total length of string table
		self.mNumStrings = len(ListOfStrings) # num of strings in string table
		# Compute indices into string table (TextureNameStartOffset)
		self.TextureNameStartOffset = []
		
		#super().__init__(**vars())
		
		for i in range(self.mNumStrings):
			self.TextureNameStartOffset.append(self.SizeStringtable)
			self.SizeStringtable += len(ListOfStrings[i]) + 1

		# Strings table begins after indices
		self.ListOfStrings = ListOfStrings

	def append(self, tex_name):
		self.ListOfStrings.append(tex_name)
		self.TextureNameStartOffset.append(self.SizeStringtable)
		self.mNumStrings += 1
		self.SizeStringtable += len(tex_name) + 1
	
	@classmethod
	def __len__(self):
		return self.SizeStringtable 

	def write(self, file):
		file.write(struct.pack('<II', self.SizeStringtable, self.mNumStrings))
		for i in range(self.mNumStrings):
			file.write(struct.pack('<I', self.TextureNameStartOffset[i]))
		for i in range(self.mNumStrings):
			block_format = "<{:d}sx".format(len(self.ListOfStrings[i]))
			file.write(struct.pack(block_format, str.encode(self.ListOfStrings[i])))
		
	@classmethod
	def load(cls, file):
		new_TL = cls()
		
		buffer = file.read(2 * SIZE_OF_INT)
		new_TL.SizeStringtable, new_TL.mNumStrings = struct.unpack('2I', buffer)

		#TextureNameStartOffset
		buffer = file.read(new_TL.mNumStrings * SIZE_OF_INT)
		new_TL.TextureNameStartOffset = struct.unpack(f'<{new_TL.mNumStrings}I', buffer)
		
		assert new_TL.mNumStrings == len(new_TL.TextureNameStartOffset)
		
		#ListOfStrings
		buffer = file.read(new_TL.SizeStringtable)
		data, = struct.unpack(f"{new_TL.SizeStringtable}s", buffer)
		
		ListOfStrings = []
		for offset_start in new_TL.TextureNameStartOffset:
			offset_next = data.index(b'\0', offset_start) #C like end of string
			ListOfStrings.append( data[offset_start:offset_next] )
			
		new_TL.ListOfStrings = ListOfStrings
		return new_TL
		
	def dump_log(self, textureNames_offset):
		print("IGfTextureNames [ 1 ] ({:d})".format(textureNames_offset))
		print("------------------------------.")
		print("TextureNameListLength         : {:d}".format(self.SizeStringtable))
		print("TextureNameCount              : {:d}".format(self.mNumStrings))
		print("--------------------------------------------------------------------------------")
		print("TextureNameStartOffsetList -----.")
		for i in range(0, self.mNumStrings):
			print(f"  TextureNameStartOffset[{i+1}] : {self.TextureNameStartOffset[i]}")
		print("TextureNameList ----------------.")
		for i in range(0, len(self.ListOfStrings)):
			print(f"  TextureName[{i+1}]  : '{self.ListOfStrings[i]}'")
		
	def get_texture_name(self, i):
		return self.ListOfStrings[i]


