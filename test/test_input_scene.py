
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

        # Next unique id
        unique_shape_id += 1
    return triangle_scene, tau, rho

# @note main
if __name__ == "__main__":
    input_path = 'test/inputs/test_scene.bgeom'
    scene = Scene(input_path)
    c_scene = scene_to_cscene(scene)

    t_scene, tau, rho = triangle_scene_conversion(c_scene)
    flat_triangle_scene = []
    for triangles in t_scene.values():
        flat_triangle_scene += triangles
    
    triangle_scene_np = np.array(flat_triangle_scene)
    triangle_n = triangle_scene_np.shape[0]

    tau_np = np.array([0.05 for _ in range(triangle_n)])
    rho_np = np.array([0.1 for _ in range(triangle_n)])

    direct_PAR = 0.
    diffuse_PAR = 600.

    rt = pyRTVPL(scene_xrange=1., scene_yrange=1., periodise_numberx=2, periodise_numbery=2, maxiter=1)
    print("First compile...")
    rt(triangle_scene_np, tau_np, rho_np, direct_PAR=direct_PAR, diffuse_PAR=diffuse_PAR)
    print("Finished")

    for _ in range(10):
        PARa, Erel = rt(triangle_scene_np, tau_np, rho_np, direct_PAR=direct_PAR, diffuse_PAR=diffuse_PAR)

    print(PARa, Erel)
