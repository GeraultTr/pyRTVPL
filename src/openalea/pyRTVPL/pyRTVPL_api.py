import os

n = max(1, int(0.8 * os.cpu_count()))
os.environ["JULIA_NUM_THREADS"] = str(n)
os.environ["PYTHON_JULIACALL_HANDLE_SIGNALS"] = "yes"

from juliacall import Main as jl
# input("Julia exe dir (Sys.BINDIR):", jl.seval("Sys.BINDIR"))
import numpy as np 
import os, sys


class pyRTVPL:

    tau_soil = 0.0 # 0.0 # no transmitance
    rho_soil = 0.15 # 0.15 # Caribu default soil reflectance

    nrays_dir = 100_000 # default 100_000
    nrays_dif = 1_000_000 # default 1_000_000

    minimal_zenith = np.deg2rad(9.23) # Lower zenit of Caribu 46 sky

    def __init__(self, scene_xrange: float=1., scene_yrange: float=1., periodize: bool = True, maxiter: int = 4, ntheta: int = 8, nphi: int = 6):
        """_summary_

        Args:
            scene_xrange (float, optional): _description_. Defaults to 1..
            scene_yrange (float, optional): _description_. Defaults to 1..
            periodize (bool, optional): _description_. Defaults to True.
            maxiter (int, optional): _description_. Defaults to 4.
            ntheta (int, optional): _description_. Defaults to 8, to near Caribu's 46 sky dome.
            nphi (int, optional): _description_. Defaults to 6, to near Caribu's 46 sky dome.
        """
        self_path = sys.modules[self.__class__.__module__].__file__
        bridge_path = os.path.dirname(os.path.abspath(self_path))
        jl.include(os.path.join(bridge_path, "vpl_bridge.jl"))
        self.VPL = jl.VPLBridge

        self.scene_xrange = scene_xrange
        self.scene_yrange = scene_yrange
        self.periodize = periodize
        self.maxiter = maxiter
        self.ntheta = ntheta
        self.nphi = nphi


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
        canopy_height = triangles[:, :, 2].max()
        periodise_numberx = self.n_replications(canopy_height, self.minimal_zenith, self.scene_xrange) if self.periodize else 0
        periodise_numbery = self.n_replications(canopy_height, self.minimal_zenith, self.scene_yrange) if self.periodize else 0
        
        out = self.VPL.trace_absorbed_incident(triangles, tau, rho, self.tau_soil, self.rho_soil, direct_PAR, diffuse_PAR, theta_dir, phi_dir, 
                                                 nx=periodise_numberx, ny=periodise_numbery, dx=self.scene_xrange, dy=self.scene_yrange, maxiter=self.maxiter, 
                                                 nrays_dir=self.nrays_dir if direct_PAR > 0 else 0, nrays_dif=self.nrays_dif if diffuse_PAR > 0 else 0, ntheta=self.ntheta, nphi=self.nphi)
        return out
    

    def n_replications(self, canopy_height, lower_plane_zenith, scene_range):
        projected_length = canopy_height / np.tan(lower_plane_zenith)
        return int(np.ceil(projected_length / scene_range))