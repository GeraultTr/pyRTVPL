from openalea.pyRTVPL import pyRTVPL
import numpy as np


def test_simple_triangles():
    # Suppose you have triangles (m) and optical properties (τ, ρ) from your model
    tris = np.array([  # (ntri,3,3)
        [[0.,0.,1.],[1.,0.,1.],[0.,1.,1.]],
        [[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]],
    ], dtype=float)
    tau = np.array([0.05, 0.05])  # 5 % transmittance NOTE : when built for Stem elements, should be 0.
    rho = np.array([0.1, 0.1])  # 10 % reflectance

    rt = pyRTVPL(scene_xrange=1., scene_yrange=1., periodise_numberx=2, periodise_numbery=2)
    for _ in range(3):
        rt(tris, tau, rho, direct_PAR=600., diffuse_PAR=0.)

if __name__ == "__main__":
    test_simple_triangles()