# ##### BEGIN LICENSE BLOCK #####
#
# Copyright (C) 2016  'DOM107', 'Juju49'(MERLE-RÉMOND Julian)
# see license notes __init__.py
#
# ##### END LICENSE BLOCK #####

import struct
from mathutils import Vector, Quaternion

#====================================================================IAF data structures

#lengths:
MAX_ANIMTRACK_NAME       = 32
MAX_HEADER_COMMENT       = 64
MAX_TRIGGER_DATA_NAME    = 32

#size:
HEADER_SIZE = 104
ANIMATIONNODE_SIZE = 44
MOTIONCONTROLLER_SIZE = 12
MOTIONSET_SIZE = 16

STRING_ENCODING = ("ascii", "ignore") #2020: decode errors

class IAMotionController():
	'''Defines a set of keys creating motion over time - this may be for rotation,
		position, or whatever. '''
	__slots__ = "mControllerType", "mKeySize", "mKeyStream"

	def __init__(self, mControllerType=0, mKeySize=MOTIONCONTROLLER_SIZE, mKeyStream=0):
		self.mControllerType = mControllerType # Type of data to expect in the key stream
		# 0: MotionVector4Frame / 1: MotionQuaternionFrame
		# List of keys, whatever they may be (defined by mControllerType)
		self.mKeySize = int(mKeySize) # Size, in bytes, per key item (eg, 16 for svector4)
		self.mKeyStream = mKeyStream

	def __eq__(self, other):
		return self.mKeyStream == other.mKeyStream and self.mKeySize == other.mKeySize

	def __len__(self):
		return MOTIONCONTROLLER_SIZE
	
	def write(self, file):
		file.write(struct.pack('<2I', self.mControllerType, self.mKeySize))
		file.write(struct.pack('<I', self.mKeyStream))

	@classmethod
	def load(cls, file):
		data = struct.unpack('<3I', file.read(MOTIONCONTROLLER_SIZE))
		return cls(*data)
	
	def dump_log(self, motion_controller_num, MotionControllerCount, offset):
		print('--------------------------------------------------------------------------------')
		print('IAfMotionControllers [ {:d}  /  {:d}  ] ({:d}) :'.format(motion_controller_num, MotionControllerCount, offset))
		print('------------------------------.')
		print("MotionControllerType          : {:d}".format(self.mControllerType))
		print("KeySize                       : {:d}".format(self.mKeySize))
		print("KeyStreamObjectStartOffset    : {:d}".format(self.mKeyStream))

	def dump_log2(self):
		print('------------------------------.')
		print("MotionControllerType          : {:d}".format(self.mControllerType))
		print("KeySize                       : {:d}".format(self.mKeySize))
		print("KeyStreamObjectStartOffset    : {:d}".format(self.mKeyStream))

class IAAnimationNode():
	'''Defines grouped controllers of animation for a single node in a shape 
		hierarchy - each node will have a corresponding IAAnimationNode (with matching name)
		that defines the animation result over the total animation time'''
	__slots__ = "mName", "mNumControllers", "mMotionControllers", "mFlags"

	def __init__(self, mName='', mNumControllers=0, mMotionControllers=None, mFlags=0):
		# name of track, will be matched to node to be animated by this data
		self.mName = mName
		# number of controllers present (2, usually, for pos + rot)
		self.mNumControllers = int(mNumControllers)
		# list of controllers in use
		self.mMotionControllers = mMotionControllers
		# generic flag field
		self.mFlags = int(mFlags)
		
	def __eq__(self, other):
		return self.mNumControllers == other.mNumControllers and self.mMotionControllers == other.mMotionControllers and self.mFlags == other.mFlags
		
	def __len__(self):
		return ANIMATIONNODE_SIZE
	
	def get_size(self):
		return ANIMATIONNODE_SIZE

	def write(self, file):
		block_format = '<{:d}s2I'.format(MAX_ANIMTRACK_NAME)
		file.write(struct.pack(block_format, self.mName, self.mNumControllers, self.mMotionControllers))
		file.write(struct.pack('<I', self.mFlags))

	@classmethod
	def load(cls, file):
		data = struct.unpack(
			f'<{MAX_ANIMTRACK_NAME}s3I', 
			file.read(ANIMATIONNODE_SIZE))
		return cls(*data)
	def dump_log(self, anim_node_num, AnimationNodeCount, offset, verbose):
		if verbose:
			print('--------------------------------------------------------------------------------')
			print('IAfAnimationNodes [ {:d}  /  {:d}  ] ({:d}) :'.format(anim_node_num, AnimationNodeCount, offset))
			print('------------------------------.')
			print("Name                          : {:s}".format(self.mName.decode()))
			print("MotionControllerCount         : {:d}".format(self.mNumControllers))
			print("MotionControllerListStartOffset : {:d}".format(self.mMotionControllers))
			print("Flags                         : {:d}".format(self.mFlags))
		else:
			print("  {:s}".format(self.mName.decode()))

	def dump_log2(self):
		print('------------------------------.')
		print("Name                          : {:s}".format(self.mName.decode()))
		print("MotionControllerCount         : {:d}".format(self.mNumControllers))
		print("MotionControllerListStartOffset : {:d}".format(self.mMotionControllers))
		print("Flags                         : {:d}".format(self.mFlags))

class IATrigger():
	'''Defines an trigger event at a given time (in seconds) e.g. audio playback.'''
	__slots__ = "mFrameTime", "mTriggerData"

	def __init__(self, mFrameTime=0, mTriggerData=""):
		# Time (in seconds) that this trigger is locked to
		self.mFrameTime = mFrameTime
		# Trigger data.
		# This relates to externally defined events such as descriptor names,
		# sound effect names special effect names etc.
		self.mTriggerData = mTriggerData

	def write(self, file):
		block_format = '<I{:d}s'.format(MAX_TRIGGER_DATA_NAME)
		file.write(struct.pack(block_format, self.mFrameTime, self.mTriggerData))
	
	def dump_log(self):
		print("  X                             : {:d}".format(self.mFrameTime))
		print("  X                             : {:s}".format(self.mTriggerData))

class IAMotionSet():
	def __len__(self):
		return MOTIONSET_SIZE
	
	@classmethod
	def load(cls, file):
		data = struct.unpack('<4f', file.read(MOTIONSET_SIZE))
		return cls(*data)

class IAMotionVector4Frame(IAMotionSet):
	__slots__ = "vect"

	def __init__(self, vect=Vector.Fill(4)):
		assert type(vect) is Vector
		self.vect = vect.to_4d().xzyw #swizzling to TS format

	def __eq__(self, other):
		return self.vect == other.vect

	def write(self, file):
		file.write(struct.pack('<4f', self.vect.x, self.vect.y, self.vect.z, self.vect.w))

	@classmethod
	def load(cls, file):
		data = struct.unpack('<4f', file.read(MOTIONSET_SIZE))
		return cls(Vector(data))
	
	def dump_log(self, frame_num):
		print("MotionVector4Frame{:03d} ----------.".format(frame_num))
		print("  X                         : {:f}".format(self.vect.x))
		print("  Y                         : {:f}".format(self.vect.y))
		print("  Z                         : {:f}".format(self.vect.z))
		print("  Weight                    : {:f}".format(self.vect.w))       

class IAMotionQuaternionFrame(IAMotionSet):
	__slots__ = "quater"

	def __init__(self, quater=Quaternion()):
		assert type(quater) is Quaternion
		self.quater = quater

	def __eq__(self, other):
		return self.quater == other.quater

	def write(self, file):
		file.write(struct.pack('<4f', self.quater.x, self.quater.z, self.quater.y, self.quater.w))

	@classmethod
	def load(cls, file):
		data = struct.unpack('<4f', file.read(MOTIONSET_SIZE))
		#swizzling on load
		return cls(Quaternion((data[3], data[0], data[2], data[1])))
	
	def dump_log(self, frame_num):
		print("MotionQuaternionFrame{:03d} -------.".format(frame_num))
		print("  w                         : {:f}".format(self.quater.w))
		print("  x                         : {:f}".format(self.quater.x))
		print("  y                         : {:f}".format(self.quater.z))
		print("  z                         : {:f}".format(self.quater.y))

class IATriggerTimeline():
	'''Defines a global trigger timeline, used to tag when in the animation
		that triggers should be fired.
		Triggers include sounds, special effects etc.'''
	__slots__ = ("mNumKeys", "mTriggerList")

	def __init__(self, mNumKeys=1, mTriggerList=0):
		# number of triggers present
		self.mNumKeys = mNumKeys
		# list of triggers, mNumKeys long
		self.mTriggerList = mTriggerList

	def write(self, file):
		file.write(struct.pack('<I', self.mNumKeys))
		file.write(struct.pack('<I', self.mTriggerList))
		
	@classmethod
	def load(cls, file):
		pass #done by header loading
		
	def dump_log(self):
		print("TriggerTimeline ----------------.")
		print("  TriggerKeyCount               : {:d}".format(self.mNumKeys))
		print("  TriggerListStartOffset        : {:d}".format(self.mTriggerList))

class IAFHeader():
	'''main file header, always written first in the IA file stream'''
	__slots__ = "mMagic", "mVersion", "mCommentField", "mDataStart", "mTotalFrames", "mSampleRate", "mTriggersTimeline", "mNumAnimationNodes", "mAnimationNodes", "mDataEnd"

	def __init__(self, mCommentField='', mDataStart=0, mTotalFrames=2, 
				mSampleRate=300, mTriggersTimeline=None, mNumAnimationNodes=2, 
				mAnimationNodes=None, mDataEnd=HEADER_SIZE):
		self.mMagic = b'KIAF'
		self.mVersion = 100 # current version of IA file
		# generic comment / description field
		self.mCommentField = mCommentField
		self.mDataStart = mDataStart # tags beginning of file data
		# animation setup
		self.mTotalFrames = mTotalFrames # total frames in the whole animation
		self.mSampleRate = mSampleRate # sample rate in Hz used to get data from controllers (default 300)
		# Stream of trigger data (e.g. audio triggers).
		self.mTriggersTimeline = mTriggersTimeline # class IATriggerTimeline
		# animation tracks for all shapes represented by this IA file
		self.mNumAnimationNodes = mNumAnimationNodes # eg, num shapes dumped
		self.mAnimationNodes = mAnimationNodes
		self.mDataEnd = mDataEnd
	
	def __len__(self):
		return HEADER_SIZE
	
	def write(self, file):
		file.write(struct.pack('<4sI', self.mMagic, self.mVersion))
		block_format = "<{:d}sI".format(MAX_HEADER_COMMENT)
		file.write(struct.pack(block_format, self.mCommentField, self.mDataStart))
		file.write(struct.pack('2I', self.mTotalFrames, self.mSampleRate))
		self.mTriggersTimeline.write(file)
		file.write(struct.pack('I', self.mNumAnimationNodes))
		file.write(struct.pack('I', self.mAnimationNodes))
		file.write(struct.pack('I', self.mDataEnd))
	
	@classmethod
	def load(cls, file):
		data = struct.unpack(f'<4sI{MAX_HEADER_COMMENT}s8I', file.read(HEADER_SIZE))
		new_cls = cls(*data[2:6], None, *data[8:11])
		new_cls.mTriggersTimeline = IATriggerTimeline(data[6], data[7])
		return new_cls
		
	def dump_log(self):
		print("================================================================================")
		print("IAfHeaders                    : [ 1 ]")
		print("--------------------------------------------------------------------------------")
		print("IAfHeaders [ 1  /  1  ] (0)  ")
		print("------------------------------.")
		print("MagicId                       : '{:s}'".format(self.mMagic.decode()))
		print("Version                       : {:d}".format(self.mVersion))
		print("CommentField                  : '{:s}'".format(self.mCommentField.decode(*STRING_ENCODING)))
		print("DataStart                     : {:d}".format(self.mDataStart)) # A changer        
		print("TotalFrames                   : {:d}".format(self.mTotalFrames))
		print("SampleRate                    : {:d}".format(self.mSampleRate))
		self.mTriggersTimeline.dump_log()
		print("AnimationNodeCount            : {:d}".format(self.mNumAnimationNodes))
		print("AnimationNodeListStartOffset  : {:d}".format(self.mAnimationNodes))
		print("DataEnd                       : {:d}".format(self.mDataEnd))

