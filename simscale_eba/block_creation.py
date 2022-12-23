import numpy as np
from stl import mesh

import pathlib

class block():
    
    def __init__(self, 
                 origin=np.array([0,0,0]), 
                 dimensions=np.array([1, 1, 1]),
                 rotation_angle=0):
        
        self.origin = origin
        self.dimensions = dimensions
        self.rotation_angle = rotation_angle
        
        self.vertices = np.array([\
                                 [-0.5, -0.5, -0],#0
                                 [+0.5, -0.5, -0],#1
                                 [+0.5, +0.5, -0],#2
                                 [-0.5, +0.5, -0],#3
                                 [-0.5, -0.5, +1],#4
                                 [+0.5, -0.5, +1],#5
                                 [+0.5, +0.5, +1],#6
                                 [-0.5, +0.5, +1]])#7
            
        self.faces = np.array([\
                              #Bottom
                              [0,3,1],
                              [1,3,2],
                              #Side 1
                              [0,4,7],
                              [0,7,3],
                              #Top
                              [4,5,6],
                              [4,6,7],
                              #Side 2
                              [5,1,2],
                              [5,2,6],
                              #Back
                              [2,3,6],
                              [3,7,6],
                              #Front
                              [0,1,5],
                              [0,5,4]])
        
        self.block = None
        self._scale(self.dimensions)
        self._translate(self.origin)
        self._rotate(self.rotation_angle)
        self._create_block()
        
    def _rotate(self, angle):
        
        angle = np.radians(angle)
        ox, oy, oz = self.origin
        px, py, pz = np.hsplit(self.vertices, 3)
    
        qx = ox + np.cos(angle) * (px - ox) - np.sin(angle) * (py - oy)
        qy = oy + np.sin(angle) * (px - ox) + np.cos(angle) * (py - oy)
        
        self.vertices = np.concatenate([qx, qy, pz], axis=1)
    
    def _scale(self, dimensions):
        self.vertices = self.vertices*dimensions
    
    def _translate(self, translation):
        self.vertices = self.vertices + translation
        
    def _create_block(self):
        self.block = mesh.Mesh(np.zeros(self.faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(self.faces):
            for j in range(3):
                self.block.vectors[i][j] = self.vertices[f[j],:]
                
class spire():
    
    def __init__(self, 
                 origin=np.array([0,0,0]), 
                 dimensions=np.array([1, 1, 1]),
                 rotation_angle=0):
        
        self.origin = origin
        self.dimensions = dimensions
        self.rotation_angle = rotation_angle
        
        #Base first from low to high xy, clockwise
        self.vertices = np.array([\
                                 [-0.5, -0.5, -0],#0
                                 [+0.5, -0.5, -0],#1
                                 [+0.5, +0.5, -0],#2
                                 [-0.5, +0.5, -0],#3
                                 [0, -0.5, +1],#4
                                 [0, +0.5, +1]])#5
            
        self.faces = np.array([\
                              #Bottom
                              [0,3,1],
                              [1,3,2],
                              #Side 1
                              [0,3,5],
                              [0,5,2],
                              #Side 2
                              [1,2,5],
                              [1,5,4],
                              #Front
                              [0,1,4],
                              #Back
                              [2,3,5]])
        
        self.block = None
        self._scale(self.dimensions)
        self._translate(self.origin)
        self._rotate(self.rotation_angle)
        self._create_block()
        
    def _rotate(self, angle):
        
        angle = np.radians(angle)
        ox, oy, oz = self.origin
        px, py, pz = np.hsplit(self.vertices, 3)
    
        qx = ox + np.cos(angle) * (px - ox) - np.sin(angle) * (py - oy)
        qy = oy + np.sin(angle) * (px - ox) + np.cos(angle) * (py - oy)
        
        self.vertices = np.concatenate([qx, qy, pz], axis=1)
    
    def _scale(self, dimensions):
        self.vertices = self.vertices*dimensions
    
    def _translate(self, translation):
        self.vertices = self.vertices + translation
        
    def _create_block(self):
        self.block = mesh.Mesh(np.zeros(self.faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(self.faces):
            for j in range(3):
                self.block.vectors[i][j] = self.vertices[f[j],:]
        
                
class ring():
    
    def __init__(self,
                 radius, 
                 index=0,
                 origin=np.array([0, 0, 0]),
                 dimensions=np.array([20, 20, 20]),
                 height_stdev=0.1,
                 spacing=2):
        
        self.index=index
        self.is_even=is_odd(self.index)
        self.origin = origin
        self.radius = radius
        self.height_stdev=height_stdev
        self.dimensions = dimensions
        self.spacing = spacing
        
        self.no_blocks = int((2*np.pi*self.radius)
                             /(self.dimensions[1]+self.dimensions[1]*self.spacing))
        self.blocks = []
        self.data = []
        self._mesh = None
        
        self._create_blocks()
        
    def _create_blocks(self):
        angles = np.arange(0, 360, 360/self.no_blocks)
        if self.is_even:
            angles += (360/self.no_blocks)/2
            
        angles -= 180
        angles += np.random.normal(0, 1, angles.shape)
        X = self.radius*np.cos(np.radians(angles)) + self.origin[0]
        Y = self.radius*np.sin(np.radians(angles)) + self.origin[1]
        Z = (self.origin[2]*np.ones(len(X)) 
             + self.origin[2])
        
        origins = np.column_stack((X,Y,Z))
        
        for i in range(0, len(X)):
            block = self._block(origins[i], angles[i])
            self.blocks.append(block.block)
            self.data.append(block.block.data)
        self._mesh = mesh.Mesh(np.concatenate(self.data))
        
    def _block(self, origin, angle):
        return block(
            origin=origin,
            dimensions=self.dimensions+np.array([
            0, 0, np.random.normal(0, self.height_stdev)[0]]),
            rotation_angle=angle
            )
    
class roughness_blocks():
    
    def __init__(self, 
                 origin=np.array([0, 0, 0]),
                 dimensions=np.array([20, 20, 20]),
                 height_stdev=0,
                 inner_ring_radius=300,
                 outer_ring_radius=800,
                 ring_spacing_factor=2,
                 building_spacing_factor=2):
        
        self.origin = origin
        self.inner_ring_radius = inner_ring_radius
        self.outer_ring_radius = outer_ring_radius
        self.dimensions = dimensions
        self.height_stdev=height_stdev,
        self.ring_spacing_factor = ring_spacing_factor
        self.building_spacing_factor = building_spacing_factor
        
        self.ring_radii = np.arange(inner_ring_radius + self.ring_spacing_factor*self.dimensions[0], 
                                    outer_ring_radius, 
                                    dimensions[0]+dimensions[0]*ring_spacing_factor)
        
        self.ring_index = range(len(self.ring_radii))
        self.rings = []
        self.data = None
        self._mesh = None
        
        self._create_rings()
        
        
    def _create_rings(self):
        for radius, i in zip(self.ring_radii, self.ring_index):
            _ring = ring(
                         index=i,
                         radius=radius, 
                         origin=self.origin,
                         dimensions=self.dimensions,
                         height_stdev=self.height_stdev,
                         spacing=self.building_spacing_factor
                         )
            
            self.rings = self.rings +_ring.data
        self._mesh = mesh.Mesh(np.concatenate(self.rings))
    
    def _create_centre_block(self, dimensions, angle):
        _block = block(origin=self.origin,
                      dimensions=dimensions,
                      rotation_angle=angle
                      )
        self.rings.append(_block.block.data)
        
    def _create_mesh(self):
        self._mesh = mesh.Mesh(np.concatenate(self.rings))
    
    def export(self, path=pathlib.Path.cwd()):
        mesh = self._mesh
        path = path / "surrounding_blocks.stl"
        mesh.save(path)
        
def is_odd(num):
    return num & 0x1
