#################################################################
## Family of scripts to get autosmooth normals by various authors
## adapted for bpy 2.79 by Juju49
## remade from:
# +-------------------------------------------------------------+
# | Backface Culling Script v0.2                                |
# | Vector Functions (c) 2001 Anthony C. D'Agostino             |
# | http://ourworld.compuserve.com/homepages/scorpius           |
# | scorpius@compuserve.com                                     |
# | March 27, 2001                                              |
# +-------------------------------------------------------------+
# |autosmooth.py                                                |
# |may 2004, z3r0_d (Nick Winters)                              |
# +-------------------------------------------------------------+
# |v1 by Flippyneck, July 2003                                  |
# |addition to give better normals for quads by z3r0_d may 2004 |
# +-------------------------------------------------------------+

from mathutils import Vector
import bpy
from builtins import int


##Two classes, 'MeshPlus' and 'FacePlus' allow storage of additional parameters not
## directly accessable through bpy's Python API. 

## v1 by Flippyneck, July 2003

## addition to give better normals for quads by z3r0_d may 2004
## (the method used to generate a normal from a quad is supposedly the one in blender's source)

##converted to tessfaces Juju49 may 2018
##converted to bmesh Juju49 feb 2020

class MeshPlus:
    def __init__(self, 
            original_mesh:bpy.types.Mesh, 
            apply_sm:bool=True,
            generate_sm_gp:bool=False):
        
        self.original_mesh = original_mesh    #reference to blender obj
        
        if not apply_sm:
            #if we don't update mesh why should we tesselate it twice?!
            self.original_mesh.calc_normals_split()
            
        self.original_mesh.calc_loop()
        
        #mesh.calc_normals_split()
        #vn_local = mesh.loops[loop.index].normal
        #mesh.free_normals_split()
        
        self.edgekey_list = {e.key : EdgePlus(e) for e in original_mesh.edges}
        self.faces = list(FacePlus(f) for f in original_mesh.tessfaces) #list of faces
        self.verts = original_mesh.vertices    #list of verts


        #creates a list of adjacent faces for each edge
        for f in self.faces:
            for e_key in f.edges:
                if e_key in self.edgekey_list:
                    self.edgekey_list[e_key].faces.append(f)
                else:
                    continue
                
                #make edge hard if face is not smoothed to sep sm_groups
                if not f.original_face.use_smooth:
                    self.edgekey_list[e_key].sharp = True
                   
        #write to neighbour faces list in each face
        for e in self.edgekey_list.values():
            for f in e.faces:
                f.neighbours.extend([n_f for n_f in e.faces if n_f is not f])
        
        if apply_sm:
            self.apply_autosmooth_edge_sharpness()
            
            #recalc what we have changed in mesh (use_sharp...)
            self.original_mesh.update()
            self.original_mesh.calc_normals_split()
            self.original_mesh.calc_tessface()
        
        if not generate_sm_gp:
            return

        #assign smooth groups to faces:
        poly_gp, nb_gp = self.original_mesh.calc_smooth_groups(use_bitflags=True)
        if nb_gp > 1:
            polys_ls = [set(p.vertices) for p in original_mesh.polygons]
            
            #store smoothing groups data to the right faces
            for f in self.faces:
                for i, set_poly_verts in enumerate(polys_ls):
                    if set_poly_verts.issuperset(set(f.v)):
                        f.smoothgp = poly_gp[i]
                        assert type(f.smoothgp) is int, "not int but {}".format(type(f.smoothg))
                        break

    def apply_autosmooth_edge_sharpness(self):
        """apply edge sharpness and returns smoothing groups"""
        me = self.original_mesh
        ANGLE = me.auto_smooth_angle
        c_norms = me.has_custom_normals
        for edge in self.edgekey_list.values():
            # each edge is a list of the verts it contains
            if edge.sharp:
                pass
            elif len(edge.faces) is 2:
                if not c_norms and Vector(edge.faces[0].fnorm).angle(Vector(edge.faces[1].fnorm), 3.14) > ANGLE:
                    edge.sharp = True
            else:
                edge.sharp = True
            
            me.edges[edge.index].use_edge_sharp = edge.sharp
            

class EdgePlus:
    __slots__ = ("index","key","sharp","faces",)
    
    def __init__(self, e):
        self.index = e.index
        self.key = e.key
        self.sharp = e.use_edge_sharp
        self.faces = []



class FacePlus:
    __slots__ = ("original_face", "v", "edges", "fnorm", "smoothgp", "neighbours",)
    
    def __init__(self, original_face):
        self.original_face = original_face
        self.v = original_face.vertices
        self.edges = original_face.edge_keys#self.GetEdges()        #list of vertex pairs that make face edges
        self.fnorm = self.original_face.normal    #Face normal
        self.smoothgp = 0
        self.neighbours = []            #List of faces adjacent to this one

# autosmooth.py
# may 2004, z3r0_d (Nick Winters)
# status: works, but not fully tested
#   - haven't tested meshes with many holes
#   - and haven't tested to see if autosmooth result is 
#     EXACTLY the same as blender's, and for changes in the angle value
# prerequisites:
#   load this text file (autosmooth.py) into blender's text window
#   and meshplus.py (either with or without my modifications should work)
#   and vector.py
#  they should all be included 
# usage: select your objects (meshes) and press alt+p with the cursor in the text window
# 
# 
# def calc_autosmooth_normals(mesh):
#     # progressbar?
#     me = mesh
#     # get the ANGLE!!!
#     ANGLE = me.auto_smooth_angle
#     print("    ","creating mplus")
#     mplus = MeshPlus(me)
#     # find the edges I need to make hard
#     print("    ","finding edges to make hard")
#     toBeHardEdges = []
#     beenWarned = False
#     for edge_key in mplus.edge_list:
#         edge = mplus.edge_list[edge_key]
#         # each edge is a list of the verts it contains
#         if edge.sharp:
#             toBeHardEdges.append(edge)
#             continue
#         
#         if len(edge.faces) is 2:
#             if Vector(edge.faces[0].fnorm).angle(Vector(edge.faces[1].fnorm)) > ANGLE:
#                 toBeHardEdges.append(edge)
#                 edge.sharp = True
#         else:
#             toBeHardEdges.append(edge)
#             edge.sharp = True
#             if not beenWarned and len(edge.faces) > 2:
#                 print ("    ","UNTESTED: this is a non manifold mesh!!!!")
#                 beenWarned = True
#     
#     print ("    ",len(toBeHardEdges), "edges to make hard")
#     print ("    ","making dictionary of vert's used edges")
#     
#     
#     vertEdges = {}
#     # find the verts I will need to duplicate...
#     for anEdge in toBeHardEdges:
#         # add anEdge[0] and anEdge[1] to my dictionary
#         if anEdge[0] in vertEdges:
#             vertEdges[anEdge[0]].append(anEdge)
#         else:
#             vertEdges[anEdge[0]] = [anEdge]
#         # second vertex in edge
#         if anEdge[1] in vertEdges:
#             vertEdges[anEdge[1]].append(anEdge)
#         else:
#             vertEdges[anEdge[1]] = [anEdge]
#     print ("    ","hardening edges now")
#     # payoff is coming, or the end is near
#     for vertKey in vertEdges:
#         hardEdges = vertEdges[vertKey]
#         #print vertKey
#         #print vertEdges
#         #print hardEdges
#         if len(hardEdges) > 1:
#             # reset each face's beendone value
#             # this could be made more efficent, want to prove concept first
#             for aface in mplus.faces:
#                 aface.beendone = 0
#             firstedge = 0
#             for hardEdge in hardEdges:
#                 #traverse faces..
#                 for face in mplus.edge_list[hardEdge]:
#                     #try:
#                     #    face.beendone
#                     #except AttributeError:
#                     if face.beendone == 0:
#                         newvert = vertKey # only create a new vert after the first edge?
#                         if firstedge != 0:
#                             # copy vertKey into newVert
#                             newvert = bpy.NMesh.Vert()
#                             for i in range(3):
#                                 newvert.co[i] = vertKey.co[i]
#                                 newvert.no[i] = vertKey.no[i]
#                             newvert.uvco[0] = vertKey.uvco[0]
#                             newvert.uvco[1] = vertKey.uvco[1]
#                             newvert.sel = vertKey.sel
#                             me.verts.append(newvert)
#                             #print newvert
#                         firstedge += 1
#                         # go through all faces starting with face which contain vertKey
#                         # stop if trying to go over an edge in hardEdges
#                         # don't go into faces which have been done
#                         faces = [face]
#                         face.beendone = 1
#                         while faces != []:
#                             thisface = faces.pop()
#                             #thisface.beendone = 1 # should already be the case
#                             # find edges containing vertKey
#                             # (do not try edges in hardEdges)
#                             # add contained faces that have not been done (use try)
#                             # into faces
#                             # replace vertKey with the newvert in face
#                             realindex = 0
#                             try: # is this a hack?
#                                 vkeyindex = thisface.v.index(vertKey)
#                                 realindex = 1
#                             except ValueError:
#                                 continue
#                             if realindex != 1:
#                                 print ("!!!!???")
#                             adjacent_edges = [
#                                 thisface.edges[(vkeyindex - 1) % len(thisface.edges)],
#                                 thisface.edges[vkeyindex] ]
#                             for anEdge in adjacent_edges:
#                                 try:
#                                     toBeHardEdges.index(anEdge)
#                                 except:
#                                     # anEdge isn't one I want to make hard
#                                     for prospectFace in mplus.edge_list[anEdge]:
#                                         if prospectFace.beendone == 0:
#                                             prospectFace.beendone = 1
#                                             faces.append(prospectFace)
#                             #edge_faces = list(mplus.edge_list[edge1]) 
#                             #edge_faces.extend(mplus.edge_list[edge2])
#                             #print edge1,edge2,edge_faces
#                             # MAGIC STUFF NOT IMPLEMENTED
#                             thisface.v[vkeyindex] = newvert
#         # else case: do nothing, no need to create verts on end of seam
#         # (would make seam longer than necescary)
#     # update the mesh
#     #print me, mplus.original_mesh
#     #newvert = bpy.NMesh.Vert(0,0,0)
#     #me.verts.append(newvert)
#     #me.faces.append(bpy.NMesh.Face([newvert,me.verts[0],me.verts[1]]))
#     me.update(calc_tessface=True) # will re-calculate normals
#     # ...