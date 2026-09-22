# ##### BEGIN LICENSE BLOCK #####
#
# Copyright (C) 2020  'Juju49'(MERLE-RÉMOND Julian)
# see license notes __init__.py
#
# ##### END LICENSE BLOCK #####

#====================================================================INFO
"""class containing data for SimisACE image format"""

#====================================================================IMPORTS
import struct
from math import log, ceil

#====================================================================GLOBALS
#Version
SACE_VERSION_0 = 0 #Version zero (WIP use)
SACE_VERSION_1 = 1 #Version one (Daedalus release one)
SACE_VERSION_2 = 2 #Version two (16-bit textures and alpha palette support)

#Format
SACE_FMT_UNKNOWN                = 0
SACE_FMT_1BIT_RGBPAL            = 1
SACE_FMT_2BIT_RGBPAL            = 2
SACE_FMT_4BIT_RGBPAL            = 3 #TS supported #TODO: implement SACE_FMT_4BIT_RGBPAL format
SACE_FMT_8BIT_RGBPAL            = 4
SACE_FMT_1BIT_INTENSITY         = 5
SACE_FMT_2BIT_INTENSITY         = 6
SACE_FMT_4BIT_INTENSITY         = 7
SACE_FMT_8BIT_INTENSITY         = 8
SACE_FMT_1BIT_RGBPAL_TMASK      = 9
SACE_FMT_2BIT_RGBPAL_TMASK      = 10
SACE_FMT_4BIT_RGBPAL_TMASK      = 11
SACE_FMT_8BIT_RGBPAL_TMASK      = 12
SACE_FMT_8BIT_UVBUMP            = 13
SACE_FMT_8BIT_RGB               = 14 #MSTS supported
SACE_FMT_8BIT_INTENSITY_UVBUMP  = 15
SACE_FMT_8BIT_RGBT              = 16 #MSTS supported
SACE_FMT_8BIT_RGBTA             = 17 #MSTS supported
SACE_FMT_DXT1                   = 18 #MSTS supported
SACE_FMT_DXT2                   = 19
SACE_FMT_DXT3                   = 20 #MSTS supported
SACE_FMT_DXT4                   = 21
SACE_FMT_DXT5                   = 22 #MSTS supported
SACE_FMT_16BIT_RGBT_5551        = 30
SACE_FMT_8BIT_RGBA              = 31 #TS supported
SACE_FMT_24BIT_IPU_COMPRESSED   = 32

#ID for channels and palettes
SACE_ID_UNKNOWN                 = 0
SACE_ID_PALETTE_INDEX           = 1 # Channel entries index palette
SACE_ID_TRANSPARENCY            = 2 # Transparency mask
SACE_ID_RED                     = 3
SACE_ID_GREEN                   = 4
SACE_ID_BLUE                    = 5
SACE_ID_ALPHA                   = 6
SACE_ID_RGB                     = 7
SACE_ID_RGBA                    = 8
SACE_ID_INTENSITY               = 9
SACE_ID_UBUMP                   = 10
SACE_ID_VBUMP                   = 11
SACE_ID_RGB16_5551              = 12 #Red,Green,Blue,Trans combined components (16-bit)

#Flags
SACE_FLAGS_MIPMAPPED       = 0x01
SACE_FLAGS_HINTDYNAMIC     = 0x02 # Surface will be locked frequently
SACE_FLAGS_HINTSTATIC      = 0x04 # Surface will be locked infrequently
SACE_FLAGS_HINTOPAQUE      = 0x08 # Surface will never be locked
SACE_FLAGS_FLAT_PACKED     = 0x10 # Surface is compressed and is accessed as a line per mip
SACE_FLAGS_VRAM_LOCKED     = 0x20 # Surface is uploaded to vram and not kept in system memory
SACE_FLAGS_MMAPS_GAUSSBLUR = 0x40 # V3: if surface contains mipmaps, then mipmaps will be gaussian blurred

class Header:
    def __init__(
        self, 
        version=SACE_VERSION_2, 
        flags=0,
        width=8,
        height=8,
        sformat=SACE_FMT_8BIT_RGBTA,
        nchannels=4,
        npalettes=0,
        author=b'anon',
        desc=b'my ace file',
        cdp=0,
        qp=0,
        mp=0,
        rp=0,
        res_size=16,
        ps_res_size=0,
        mip_dist=1,
        uncompresssed_format=SACE_FMT_UNKNOWN,
        compressed_format=SACE_FMT_UNKNOWN,
        gauss_factor=1.0,
        gauss_mip_multiplier=1.0,
        reserved=b'\x00'*12
        ):
        self.version = version               # Version id (see AACE_VERSION_xxx above)
        self.flags = flags                   # Flags (see AACE_FLAGS_xxx above)
        self.width = int(width)              # Surface width
        self.height = int(height)            # Surface height
        self.format = sformat                # Surface format id (see AACE_FMT_xxx above)
        self.nchannels = nchannels           # Number of surface channels
        self.npalettes = npalettes           # Number of surface palettes
        self.author = author[:16]            # Author sting
        self.desc = desc[:64]                # Description string
        self.colour_depth_priority = cdp     # Priority that colour depth be 24(hi 4bits) 16(lo 4bits)
        self.quality_priority = qp           # Priority that texture be rendered at high quality
        self.mipmap_priority = mp            # Priority that higher mipmaps be used (not dropped)
        self.reserved_priority = rp          # Unused, reserved for further quality extensions
        self.resource_size = res_size        # Size (bytes) of extra resources appended to ACE file
        self.ps_resource_size = ps_res_size  # Size (bytes) of Photoshop resources appended to extra resources
        self.mip_dist = mip_dist             # Max mip distance (world space) for the first mip
        
        #because decompressed aces have two formats, the stored and the displayed,
        # for operations like dropping mips, it is vital to know what both are.
        # this pair allows us to represent these. when we decompress, we generate
        # the lowest two mips out of the uncompresssed_format, as we cant represent
        # them compressed.
        self.uncompresssed_format = uncompresssed_format
        self.compressed_format = compressed_format
        # new scalar for gaussian blurring mipmaps
        self.gauss_factor = gauss_factor                 # for mip-maps, the intensity of gaussian blurring applied
        self.gauss_mip_multiplier = gauss_mip_multiplier # for mip-maps, the multiplier for gausisan intensity on lower level mips
        # gauss_factor has taken 6 bytes away from the reserved bytes.
        #    was... byte        reserved [20]            # Reserved field
        self.reserved = reserved # Reserved field 12 bytes
        # Dynamic members
    
        # Channel table (nchannels array)
        self.channel_table = None
    
        # Palettes (npalettes array)
        self.palettes = None
    
        # regular ace files: SACE_FLAGS_MIPMAPPED flagged ACE files contain log2(width)
        # offset tables, otherwise a single table
        # flat packed ace files: SACE_FLAGS_MIPMAPPED flagged ACE files contain log2(width)
        # mips, otherwise a single value
        self.offset_table = None
        
    @classmethod
    def load(cls, file):
        #static header
        self = cls(*struct.unpack('<7I16s64s4B2If4I12s', file.read(152))) #overloadin' XD
        
        mips_included = self.flags & SACE_FLAGS_MIPMAPPED
        flat = self.flags & SACE_FLAGS_FLAT_PACKED
        
        if mips_included:
            #only in MSTS but not in TS:
            #if self.height != self.width:
            #    raise RuntimeError(f"SACE: non square texture with mips! {self.height}x{self.width}")
            if self.width & (self.width - 1):
                raise RuntimeError(f"SACE: width is not a power of 2 with mips! {self.width}")
            if self.height & (self.height - 1):
                raise RuntimeError(f"SACE: width is not a power of 2 with mips! {self.height}")
            
        if not flat:
            if self.format not in {#MSTS supported formats
                SACE_FMT_8BIT_RGB,
                SACE_FMT_8BIT_RGBT,
                SACE_FMT_8BIT_RGBTA,
                #Unsupported for now, but later maybe!
                #SACE_FMT_DXT1,
                #SACE_FMT_DXT3,
                #SACE_FMT_DXT5,
                #SACE_FMT_4BIT_RGBPAL,
                SACE_FMT_8BIT_RGBA,
                }:
                if self.format in {
                    SACE_FMT_DXT1,
                    SACE_FMT_DXT3,
                    SACE_FMT_DXT5
                    }:
                    raise NotImplementedError(f"SACE: DXT compression not implemented!" )
                raise NotImplementedError(f"SACE: format {self.format} not implemented!" )
        
        # Dynamic members
        
        # Channel table (nchannels array)
        channel_table = []
        for _ in range(self.nchannels):
            channel_table.append(Channel.load(file))
            
        self.channel_table = channel_table
    
        # Palettes (npalettes array)
        palettes = []
        for _ in range(self.npalettes):
            palettes = Palette.load(file)
        for palette in palettes:
            palette.load_entries(file)
        self.palettes = palettes
    
        # regular ace files: SACE_FLAGS_MIPMAPPED flagged ACE files contain log2(width)
        # offset tables, otherwise a single table
        # flat packed ace files: SACE_FLAGS_MIPMAPPED flagged ACE files contain log2(width)
        # mips, otherwise a single value
        nMips = int(1+log(self.width, 2) if mips_included else 1)
        Mips = []
        #read offset table
        real_offset_table = []
        for i in range(nMips):
            if flat:
                num_scanlines = 1
            else:
                num_scanlines = self.height >> i
            real_offset_table.append( struct.unpack(f'<{num_scanlines}I', 
                file.read( 4 * num_scanlines )
                ) )
        #read lines
        if flat:
            #iterate on images directly
            for i in range(nMips):
                size = self.width >> i * self.height >> i
                Mips.append( struct.unpack(f"{size}I", file.read(size)) )
                #flat ARGB8
        else:
            #iterate on images
            for i in range(nMips):
                mip_width  = self.width >> i
                mip_height = self.height >> i
                r=[]
                g=[]
                b=[]
                a=[]
                if self.format is SACE_FMT_8BIT_RGB:
                    #pad alpha with opaque because no channel
                    a = mip_width * mip_height * [255]
                #iterate on each lines' pixels
                # SACEs are stored as RRRGGGBBBAAA arrays per line
                for y in range(mip_height):
                    #iterate on what this row part might be:
                    for ch in self.channel_table:
                        expected_length = ceil(mip_width * ch.byte_len)
                        buffer = file.read(expected_length)
                        #print(f"mip {i}, "
                        #      f"ln {y}, "
                        #      f"id {ch.id}, "
                        #      f"size {len(buffer)}")
                        
                        #read it according to nbits len
                        if   ch.nbits is 32: #Uint
                            channel_pixels = struct.unpack(
                                    f"{mip_width}I", buffer)
                        elif ch.nbits is 16: #Ushort
                            channel_pixels = struct.unpack(
                                    f"{mip_width}H", buffer)
                        elif ch.nbits is 8: #Uchar
                            channel_pixels = struct.unpack(
                                    f"{mip_width}B", buffer)
                        else:
                            #We will need to create an "x" to navigate
                            #on the row to slice bytes according
                            #to ch.nbits
                            color_bytes = struct.unpack(
                                    f"{expected_length}B", buffer)
                            if   ch.nbits is 4:
                                #mask original byte by packets of 4
                                channel_pixels = ( px >> x & 15 for px in color_bytes 
                                                  for x in range(2) )
                            elif ch.nbits is 2:
                                #mask original byte by packets of 2
                                channel_pixels = ( px >> x & 3 for px in color_bytes
                                                  for x in range(4) )
                            elif ch.nbits is 1:
                                #mask original byte by packets of 1
                                channel_pixels = ( px >> x & 1 for px in color_bytes
                                                  for x in range(8) )
                            else:
                                raise NotImplemented(f"SACE: channel nBits {ch.nbits}")
                            
                        #first, reorder lines. Blender needs to read from bottom to top:
                        channel_pixels = reversed(channel_pixels)
                        
                        #Save RRRGGGBBBAAA colors obtained 
                        # for later RGBARGBARGBA reordering
                        if   ch.id is SACE_ID_RED:
                            r.extend(channel_pixels)
                        elif ch.id is SACE_ID_GREEN:
                            g.extend(channel_pixels)
                        elif ch.id is SACE_ID_BLUE:
                            b.extend(channel_pixels)
                        elif ch.id is SACE_ID_ALPHA \
                        or   ch.id is SACE_ID_TRANSPARENCY :
                            a.extend(channel_pixels)
                        else:
                            raise NotImplemented(f"SACE: channel id {ch.id}")
                        
                #Build image from it RBGA data:
                
                #then, reorder columns. Blender needs to read from right to left:
                r.reverse()
                g.reverse()
                b.reverse()
                a.reverse()
                
                #We reorder this with a zip beacause blender only accepts flat
                #RGBARGBARGBA list of ints
                image = [ px[i] / 255 for px in zip(r, g, b, a) for i in range(4)]
                
                #This one is not flat but migght be usefull another day:
                #image = [ px for px in zip(r, g, b, a)]
                
                Mips.append( image )
        self.offset_table = Mips
    
        return self
    
    def get_mip_width(self, i):
        """int -> int
        returns height of mip if existing,
        else raises RuntimeError. NOTA: all mips are squares!"""
        if self.flag & SACE_FLAGS_MIPMAPPED:
            return self.width >> i
        elif i is 0:
            return self.width
        else:
            raise RuntimeError("SACE: cannot request size of non(existing mip!")
        
    def dump_log(self, verbose):
        if verbose <= 1:
            print(
             "\n==::SimisACE file::==================================================\n"
            f"  version :{self.version}\n"
            f"  flags   :{self.flags}\n"
            f"  width   :{self.width}\n"
            f"  height  :{self.height}\n"
            f"  format  :{self.format}\n"
            f"  num channels :{self.nchannels}\n"
            f"  num palettes :{self.npalettes}\n"
            f"  author  :{self.author.decode('ascii','ignore')}\n"
            f"  desc    :{self.desc.decode('ascii','ignore')}\n"
            f"  num Mips: {len(self.offset_table)}"
            )
            return 
        print(
            "\n===:: SimisACE file ::===::===::===::===::===::===::===::===\n"
            "Header ============================="
            f"  version :{self.version}\n"
            f"  flags   :{self.flags}\n"
            f"  width   :{self.width}\n"
            f"  height  :{self.height}\n"
            f"  format  :{self.format}\n"
            f"  num channels :{self.nchannels}\n"
            f"  num palettes :{self.npalettes}\n"
            f"  author  :{self.author}\n"
            f"  desc    :{self.desc}\n"
             "  priorities --------\n"
            f"    colour depth   :{self.colour_depth_priority}\n"
            f"    hq render      :{self.quality_priority}\n"
            f"    use high mips  :{self.mipmap_priority}\n"
            f"    reserved       :{self.reserved_priority}\n"
             "  extra resources ----\n"
            f"    general size   :{self.resource_size}\n"
            f"    photoshop size :{self.ps_resource_size}\n"
            f"  max top MIP dist     :{self.mip_dist}\n"
            f"  uncompresssed format :{self.uncompresssed_format}\n"
            f"  compressed format    :{self.compressed_format}\n"
            f"  gauss factor         :{self.gauss_factor}\n"
            f"  gauss mip multiplier :{self.gauss_mip_multiplier}\n"
            f"  reserved             :{self.reserved}\n"
            )
        
        print("Channels =========================")
        if self.channel_table:
            for i, channel in enumerate(self.channel_table):
                channel.dump_log(len(self.channel_table), i)
        else:
            print(
                "  No channel"
                )
            
        print("Palettes =========================")
        if self.palettes:
            for i, palette in enumerate(self.palettes):
                palette.dump_log(len(self.palettes), i)
        else:
            print(
                "  No palettes"
                )
            
        print("Image data =======================")
        if not self.offset_table:
            print(
                "  No texture data!!"
                )
            return
        for i, mip in enumerate(self.offset_table):
            print( f"Image data [{i}/{len(self.offset_table)}] "
                   f"{len(mip)} bytes"
                   )
        print("===:: EOD file ::===::===::===::===::===::===::===::===")
        
class Channel:
    __slots__ = ('nbits', 'byte_len', 'palette', 'id', 'reserved')

    def __init__(self, 
         nbits=8, 
         palette=0, 
         sid=SACE_ID_UNKNOWN, 
         reserved=0
         ):
        self.nbits = nbits      # Bits per channel ( 1, 2, 4, 8, 16, 32 )
        self.byte_len = nbits / 8
        self.palette = palette  # Palette (0-none, else palette number)
        self.id = sid           # Identification (0-unknown), used to index sace_id_string table / SACE_ID_xxx
        self.reserved = reserved
    
    @classmethod
    def load(cls, file):
        data = struct.unpack('<4I', file.read(16))
        #ncls = cls(*data)
        #print("raw channel", data)
        ncls = cls(nbits=data[0], palette=data[1], sid=data[2], reserved=data[3])
        return ncls
    
    def dump_log(self, numchannel, i):
        print(
            f"Channel [{i}/{numchannel}]----.\n"
            f"  nbits      : {self.nbits}\n"
            f"  palette    : {self.palette}\n"
            f"  id         : {self.id}\n"
            f"  reserved   : {self.reserved}"
            )
    
class Palette:
    __slots__ = ('nentries', 'entry_size', 'id', 'entries')
    def __init__(self, 
         nentries=0, 
         entry_size=0, 
         sid=SACE_ID_UNKNOWN, 
         entries=0#becomes a list upon loading
         ):
        self.nentries = nentries     # Number of palette entries
        self.entry_size = entry_size # Size of palette entries (bytes)
        self.id = sid                # Identification (0-unknown), used
            # to index sace_id_string table / SACE_ID_xxx
        self.entries = entries       # nentries * entry_size palette
    
    @classmethod
    def load(cls, file):
        ncls = cls(*struct.unpack('<3Ic', file.read(13)))
        return ncls
    
    def load_entries(self, file):
        self.entries = list( struct.unpack(f'<{self.entry_size}s', file.read(self.nentries * self.entry_size)) )
    
    def dump_log(self, numpalettes, i):
        print(
            f"Palette [{i}/{numpalettes}]----.\n"
            f"  nentries   : {self.nentries}\n"
            f"  entry_size : {self.entry_size}\n"
            f"  id         : {self.id}"
            )
        if type(self.entries) is list:
            print(
                "  entries    : "
                )
            for e in self.entries:
                print(
                f"    :{e}"
                )
        else:
            print(
                f"  entries    : {self.entries}"
                )
        
    