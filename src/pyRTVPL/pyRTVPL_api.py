

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
tau = np.array([0.05, 0.05])  # 5 % transmittance NOTE : when built for Stem elements, should be 0.
rho = np.array([0.1, 0.1])  # 10 % reflectance
tau_soil = 0.0
rho_soil = 0.15 # Caribu default

for _ in range(3):
    t1 = time.time()
    # Proper unit
    direct_par = 600. # µmol.m-2.s-1
    diffuse_par = 0.
    nrays_dir = 100_000 if direct_par > 0 else 0 # default 100_000
    nrays_dif = 1_000_000 if diffuse_par > 0 else 0 # default 1_000_000
    maxiter = 4 # 4 default, # 1 is equivalent to caribu's default
    # NOTE : In case direct is used, 'sun_position.py' should be used to input varying theta_dir and phi_dir along with PARi
    theta_dir= np.deg2rad(83) # Zenith angle (0, pi/2 / 90°)
    phi_dir = np.deg2rad(180) # Azimuth angle (0, 2pi)

    PARa, Erel = VPL.trace_absorbed_incident(tris, tau, rho, tau_soil, rho_soil, direct_par, diffuse_par, theta_dir, phi_dir, 
                                                 nx=2, ny=2, dx=1., dy=1., maxiter=maxiter, nrays_dir=nrays_dir, nrays_dif=nrays_dif)
    t2 = time.time()
    print(t2 - t1)
    print(PARa, Erel)
