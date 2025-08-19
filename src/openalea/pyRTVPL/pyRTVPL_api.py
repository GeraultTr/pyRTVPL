import os

n = max(1, int(0.8 * os.cpu_count()))
os.environ["JULIA_NUM_THREADS"] = str(n)
os.environ["PYTHON_JULIACALL_HANDLE_SIGNALS"] = "yes"

from juliacall import Main as jl
# input("Julia exe dir (Sys.BINDIR):", jl.seval("Sys.BINDIR"))
import numpy as np 
import os, sys


class pyRTVPL:

    tau_soil = 0.0 # no transmitance
    rho_soil = 0. # Caribu default reflectance
    # rho_soil = 0.15 # Caribu default reflectance

    nrays_dir = 100_000 # default 100_000
    # nrays_dif = 1_000_000 # default 1_000_000
    nrays_dif = 1_000_000 # default 1_000_000

    def __init__(self, scene_xrange: float=1., scene_yrange: float=1., periodise_numberx: int=2, periodise_numbery: int=2, maxiter: int = 4):
        self_path = sys.modules[self.__class__.__module__].__file__
        bridge_path = os.path.dirname(os.path.abspath(self_path))
        jl.include(os.path.join(bridge_path, "vpl_bridge.jl"))
        self.VPL = jl.VPLBridge

        self.scene_xrange = scene_xrange
        self.scene_yrange = scene_yrange
        self.periodise_numberx = periodise_numberx
        self.periodise_numbery = periodise_numbery
        self.maxiter = maxiter


    def __call__(self, triangles, tau, rho, direct_PAR: float, diffuse_PAR: float, theta_dir: float=1.4486, phi_dir: float=3.1416):
        """Run method for Virtual Plant Lab raytracer interception on provided triangles set

        Args:
            triangles (np.ndarray): (N, 3) triangle arrays
            tau (np.ndarray): (N,) transmitance, Caribu default is 0.05
            rho (np.ndarray): (N,) reflectance, Caribu default is 0.1
            direct_PAR (float): Direct PAR in µmol.m-2.s-1 . In case direct is used, 'sun_position.py' should be used to estimate input varying theta_dir and phi_dir along with PARi
            diffuse_PAR (float): Diffuse PAR in µmol.m-2.s-1
            theta_dir (float, optional): Zenith angle in radian Zenith angle (0 max intensity, above pi/2 bellow horizon). Defaults to 1.4486.
            phi_dir (float, optional): Azimuth angle (0, 2pi). Defaults to 3.1416.

        Returns:
            np.ndarray: PARa, absorbed PAR in µmol.m-2.s-1
            np.ndarray: Erel, relative absorption (adim)
        """
        
        PARa, Erel = self.VPL.trace_absorbed_incident(triangles, tau, rho, self.tau_soil, self.rho_soil, direct_PAR, diffuse_PAR, theta_dir, phi_dir, 
                                                 nx=self.periodise_numberx, ny=self.periodise_numbery, dx=self.scene_xrange, dy=self.scene_yrange, maxiter=self.maxiter, 
                                                 nrays_dir=self.nrays_dir, nrays_dif=self.nrays_dif, ntheta=5, nphi=4)
        return PARa, Erel
