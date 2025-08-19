
# public packages
import math
import numpy as np

# OA dependancies
from openalea.plantgl.all import *
from openalea.plantgl.all import Scene
from alinea.caribu.plantgl_adaptor import scene_to_cscene
from openalea.pyRTVPL import pyRTVPL

def rotate_point_z(point, angle_deg):
    """
    Rotate a single 3D point around the vertical (z) axis by angle_deg (degrees).
    Axis passes through (x,y) = (0,0).
    """
    x, y, z = point
    t = math.radians(angle_deg)
    c, s = math.cos(t), math.sin(t)
    xr = c * x - s * y
    yr = s * x + c * y
    return (xr, yr, z)

def triangle_scene_conversion(c_scene):
    #: Optical properties
    # opt = {}
    tau = {}
    rho = {}

    # Create a unified scene of all mtgs provided as input
    triangle_scene = {}
    unique_shape_id = 1

    indexer = {}
    pos = (0, 0, 0)
    rotation = 0

    for vid in c_scene:
        indexer[unique_shape_id] = vid
        triangle_scene[unique_shape_id] = c_scene[vid]
        tau[unique_shape_id] = 0.05
        rho[unique_shape_id] = 0.10

        # retreive optical properties and assign using the mapping
        # class_name = props["class_name"][vid]
        # if class_name in ('LeafElement1', 'LeafElement'):
        #     # opt[unique_shape_id] = (0.10, 0.05)  #: (reflectance, transmittance) of the adaxial side of the leaves
        #     tau[unique_shape_id] = 0.05
        #     rho[unique_shape_id] = 0.10
        # elif class_name == 'StemElement':
        #     # opt[unique_shape_id] = (0.10,)  #: (reflectance,) of the stems
        #     tau[unique_shape_id] = 0.
        #     rho[unique_shape_id] = 0.10
        # else:
        #     print('Warning: unknown element type')

        # Move the plants position in the stand
        # for i, triple in enumerate(triangle_scene[unique_shape_id]):
        #     translated_triangle = []
        #     for x, y, z in triple:
        #         xr, yr, znr = rotate_point_z((x, y, z), rotation)
        #         translated_triangle.append((xr + pos[0], yr + pos[1], znr + pos[2]))
        #     triangle_scene[unique_shape_id][i] = translated_triangle

        # Next unique id
        unique_shape_id += 1
    return triangle_scene, tau, rho

# @note main
if __name__ == "__main__":
    input_path = 'test/inputs/test_scene.bgeom'
    scene = Scene(input_path)
    c_scene = scene_to_cscene(scene)
    # print(c_scene)

    t_scene, tau, rho = triangle_scene_conversion(c_scene)
    flat_triangle_scene = []
    for triangles in t_scene.values():
        flat_triangle_scene += triangles
    
    triangle_scene_np = np.array(flat_triangle_scene)
    triangle_n = triangle_scene_np.shape[0]

    tau_np = np.array([0.05 for _ in range(triangle_n)])
    rho_np = np.array([0.1 for _ in range(triangle_n)])
    print(tau_np.shape)

    rt = pyRTVPL(scene_xrange=1., scene_yrange=1., periodise_numberx=2, periodise_numbery=2)
    print("first")
    rt(triangle_scene_np, tau_np, rho_np, direct_PAR=600., diffuse_PAR=0.)

    for _ in range(10):
        rt(t_scene, tau, rho, direct_PAR=600., diffuse_PAR=0.)
