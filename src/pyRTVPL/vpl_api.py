

from juliacall import Main as jl
# input("Julia exe dir (Sys.BINDIR):", jl.seval("Sys.BINDIR"))
import numpy as np
import os
import time


jl.include("src/pyRTVPL/vpl_bridge.jl")
print("imported")
VPL = jl.VPLBridge
print(VPL)

# Suppose you have triangles (m) and optical properties (τ, ρ) from your model
tris = np.array([  # (ntri,3,3)
    [[0.,0.,1.],[1.,0.,1.],[0.,1.,1.]],
    [[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]],
], dtype=float)
tau = np.array([0.10, 0.10])  # 10 % transmittance
rho = np.array([0.05, 0.05])  # 5 % reflectance

for _ in range(3):
    t1 = time.time()
    direct_par = 600.
    diffuse_par = 0.
    nrays_dir = 100_000 if direct_par > 0 else 0
    nrays_dif = 1_000_000 if diffuse_par > 0 else 0
    theta_dir=np.pi/2 # Zenith angle (0, pi/2)
    phi_dir = np.pi # Azimuth angle (0, 2pi)
    results = VPL.trace_absorbed_incident(tris, tau, rho, direct_par, diffuse_par, theta_dir, phi_dir, nx=2, ny=2, dx=0.15, dy=0.15, nrays_dir=nrays_dir, nrays_dif=nrays_dif)
    t2 = time.time()
    print(t2 - t1)
    absorbed, incident = results
    print(absorbed, incident)
