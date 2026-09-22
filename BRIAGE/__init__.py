# ##### BEGIN LICENSE BLOCK #####
#
# Blender IGS exporter. Read/Write data from Blender to Kuju IG/IA/ACE
# format files.
# Copyright (C) 2024  'Juju49'(MERLE-RÉMOND Julian), 'DOM107'
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#   -The above copyright notice and this permission notice shall be included 
#    in all copies or substantial portions of the Software.
#	-The origin of the Software must be easily identifiable from its
#	 download description page.
#	-User-modified versions of the Software require to be marked as clearly
#	 as possible that they are different from the original version.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Contact:
#  e-mail: 			julian.merle-remond@devmares.net
#  mailing address: MERLE-RÉMOND Julian, 
#					64 avenue Henri Martin
#					94100, Saint-Maur-dès-Fossés
#					FRANCE
#	
# ##### END LICENSE BLOCK #####

#====================================================================INFO
bl_info = {
	"name": "BRIAGE - TS Intermediate scenes handler (.igs, .ia, .ace)",
	"author": "Juju49, dom107",
	"version": (3, 3, "101"),
	"blender": (4, 1, 0),
	"location": "Properties > Scene > IA/IGS export options;   Files > Import/Export;   Properties > Material",
	"description": "Export IGS/IA Models  for DTG Train Simulator Classic and import IGS/IA/ACE files",
	"warning": "",
	"tracker_url": "julian.merle-remond@devmares.net",
	"support": 'COMMUNITY', #'TESTING',
	"category": "Import-Export"}

PCKG_VERSION = 'BRIAGE V' + '.'.join(str(i) for i in bl_info['version'])

__all__ = ["Utilityfcts", "CleanAndProperSceneExport", "Groups", "IGSE", "IGSI", "IAI", "IAE", "Bl_data", "SceneCheck", "Bl_mtl280"]

#====================================================================CHECK PyVERSION
import sys
if sys.version_info[1] == 3 and sys.version_info[2] >= 7:
	raise Exception("must use python 3.7 or above")

#====================================================================RELOAD MODULES
from . import Utilityfcts
import os.path
import bpy
BINARY_PATH = Utilityfcts.get_binpath()
Utilityfcts.setup_addon_modules(BINARY_PATH, __name__, "bpy" in locals())

#====================================================================REGISTER/UNREGISTER
from . import Bl_data
from . import Bl_mtl280
def register():
	Bl_data.register()
	Utilityfcts.register()
	Bl_mtl280.register()
	
	Utilityfcts.print_pr(1)
	
def unregister():
	Bl_data.unregister()
	Utilityfcts.unregister()
	Bl_mtl280.unregister()
