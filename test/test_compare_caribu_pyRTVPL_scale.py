# public packages
import math
import numpy as np
import time
import os
import pandas as pd

# OA packages
from openalea.caribu.CaribuScene import CaribuScene
from openalea.caribu.sky_tools import GenSky, GetLight, Gensun, GetLightsSun, spitters_horaire
from openalea.plantgl.all import *
from openalea.plantgl.all import Scene
from openalea.caribu.plantgl_adaptor import scene_to_cscene
from openalea.pyRTVPL import pyRTVPL
import time


def _initialize_model_on_stand(c_scene, energy, diffuse_model, azimuts, zenits, DOY, hourTU, latitude, scene_xrange, scene_yrange):
        """
        Initialize the inputs of the model from the MTG shared

        :param float energy: The incident PAR above the canopy (�mol m-2 s-1)
        :param string diffuse_model: The kind of diffuse model, either 'soc' or 'uoc'.
        :param int azimuts: The number of azimutal positions.
        :param int zenits: The number of zenital positions.
        :param int DOY: Day Of the Year to be used for solar sources
        :param int hourTU: Hour to be used for solar sources (Universal Time)
        :param float latitude: latitude to be used for solar sources (�)
        :param bool heterogeneous_canopy: Whether to create a duplicated heterogeneous canopy from the initial mtg.

        :return: A tuple of Caribu scenes instantiated for sky and sun sources, respectively, and two dictionaries with Erel value per vertex id and per primitive.
        :rtype: (CaribuScene, CaribuScene, dict, dict)
        """
        c_stand_scene_sky, c_stand_scene_sun = None, None

        #: Diffuse light sources : Get the energy and positions of the source for each sector as a string
        sky_string = GetLight.GetLight(GenSky.GenSky()(energy, diffuse_model, azimuts, zenits))  #: (Energy, soc/uoc, azimuts, zenits)

        # Convert string to list in order to be compatible with CaribuScene input format
        sky = []
        for string in sky_string.split('\n'):
            if len(string) != 0:
                string_split = string.split(' ')
                t = tuple((float(string_split[0]), tuple((float(string_split[1]), float(string_split[2]), float(string_split[3])))))
                sky.append(t)

        #: Direct light sources (sun positions)
        sun = Gensun.Gensun()(energy, DOY, hourTU, latitude)
        sun = GetLightsSun.GetLightsSun(sun)
        sun_str_split = sun.split(' ')
        sun = [tuple((float(sun_str_split[0]), tuple((float(sun_str_split[1]), float(sun_str_split[2]), float(sun_str_split[3])))))]

        #: Optical properties
        opt = {'par': {}}
        
        # Create a unified scene of all mtgs provided as input
        indexer = {}
        per_triangle_indexer = []
        triangle_scene = {}
        unique_shape_id = 1

        for vid in c_scene:
            # indexer[id][unique_shape_id] = vid
            triangle_scene[unique_shape_id] = c_scene[vid]

            # retreive optical properties and assign using the mapping
            opt['par'][unique_shape_id] = (0.10, 0.05) # NOTE : Since we don't have access to mtg properties in this test, we assign leaf properties everywhere

            # Move the plants position in the stand
            for i, triple in enumerate(triangle_scene[unique_shape_id]):
                translated_triangle = []
                for x, y, z in triple:
                    # xr, yr, znr = rotate_point_z((x, y, z), rotation)
                    # translated_triangle.append((xr + pos[0], yr + pos[1], znr + pos[2]))
                    translated_triangle.append((x, y, z))
                triangle_scene[unique_shape_id][i] = translated_triangle
                per_triangle_indexer.append(unique_shape_id)

            # Next unique id
            unique_shape_id += 1

        # Generates CaribuScenes
        # print(stand_scene, sky, ((0, self.scene_xrange), (0, self.scene_yrange)), opt)
        c_stand_scene_sky = CaribuScene(scene=triangle_scene, light=sky, pattern=(0, 0, scene_xrange, scene_yrange), opt=opt)
        c_stand_scene_sun = CaribuScene(scene=triangle_scene, light=sun, pattern=(0, 0, scene_xrange, scene_yrange), opt=opt)
        
        return c_stand_scene_sky, c_stand_scene_sun, per_triangle_indexer

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



if __name__ == "__main__":

    # Path to folder containing the scenes
    scenes_folder = r"test\inputs\test_scaled_scenes"

    scenes_paths = []

    for root, dirs, files in os.walk(scenes_folder):
        for file in files:
            if "scene_light_plantgl" in file:
                file_path = os.path.join(root, file)
                if os.path.getsize(file_path) > 10 * 1024:  # 10KB in bytes
                    scenes_paths.append(file_path)

    #Julia VPL Raytracer parameters
    scene_xrange, scene_yrange = 0.56, 0.56 #specific to this set of scenes
    generate_soil = False

    # Dataframe to store results
    results_df = pd.DataFrame()
    time_df = pd.DataFrame()

    #Compilation of the VPL Raytracer
    print("Importing VPL RayTracer from Julia...")
    rt = pyRTVPL(scene_xrange=scene_xrange, scene_yrange=scene_yrange, periodize=True, maxiter=1, generate_soil=generate_soil)

    for input_path in scenes_paths:
        
        scene_index = scenes_paths.index(input_path)
        scene = Scene(input_path)
        c_scene = scene_to_cscene(scene)
        PARi = 600.

        print("Loading scene ", scene_index + 1, " / ", len(scenes_paths), ": ", input_path)

        # ---------- CARIBU ----------
        c_stand_scene_sky, c_stand_scene_sun, indexer = _initialize_model_on_stand(c_scene=c_scene, 
                                                                                            energy=1,
                                                                                            diffuse_model='soc',
                                                                                            azimuts=4,
                                                                                            zenits=5,
                                                                                            DOY=100,
                                                                                            hourTU=12,
                                                                                            latitude=48.84425,
                                                                                            scene_xrange=scene_xrange,
                                                                                            scene_yrange=scene_yrange)

        print("caribu starts...")
        t1 = time.time()
        raw, aggregated_sky = c_stand_scene_sky.run(direct=True, infinite=True)
        print("caribu finished")
        caribu_time = time.time() - t1
        print("Caribu regular run took :", caribu_time, "s")

        Erel = aggregated_sky['par']['Eabs']  #: Erel is the relative surfacic absorbed energy per organ
        PARa = {k: v * PARi for k, v in Erel.items()}
        raw_Erel = []
        for l in raw["par"]["Eabs"].values():
            raw_Erel += l

        raw_PARa = [v * PARi for v in raw_Erel]

        caribu_PARa = np.array(raw_PARa)
        
        # Requiered before shutting down
        del c_stand_scene_sky, c_stand_scene_sun



        # ---------- PYRTVPL ----------
        t_scene, tau, rho = triangle_scene_conversion(c_scene)
        flat_triangle_scene = []
        per_triangle_indexer = []
        for shape_id, triangles in t_scene.items():
            flat_triangle_scene += triangles
            per_triangle_indexer += [shape_id for _ in range(len(triangles))]
        
        triangle_scene_np = np.array(flat_triangle_scene)
        triangle_n = triangle_scene_np.shape[0]

        tau_np = np.array([0.05 for _ in range(triangle_n)])
        rho_np = np.array([0.1 for _ in range(triangle_n)])

        direct_PAR = 0.
        diffuse_PAR = PARi

        t1 = time.time()
        print("Initial compile...")
        rt(triangle_scene_np, tau_np, rho_np, direct_PAR=direct_PAR, diffuse_PAR=diffuse_PAR)
        compile_time = time.time() - t1
        print("Finished compile in ", compile_time, "s")

        t1 = time.time()
        PARa, Erel, areas = rt(triangle_scene_np, tau_np, rho_np, direct_PAR=direct_PAR, diffuse_PAR=diffuse_PAR)
        VPL_time = time.time() - t1
        print("VPL regular run took :", VPL_time, "s")

        vpl_PARa = np.array(PARa)
        if generate_soil:
            areas = areas[:-2] # Remove the two soil triangles

        #print("Difference PARa (% PARi)", 100 * (caribu_PARa - vpl_PARa) / PARi)
        print("Caribu absorbed (µmol.s-1)", (caribu_PARa * areas).sum())
        print("pyRTVPL absorbed (µmol.s-1)", (vpl_PARa * areas).sum())
        #print("Caribu absorbed per triangle (µmol.s-1)", (caribu_PARa * areas))
        #print("Differences in absorbed energy per triangle (µmol.s-1)", (caribu_PARa - vpl_PARa) * areas)
        #print("corresponding shape index", indexer)

        #Store time
        time_df = pd.concat([time_df, pd.DataFrame([{
            "scene": input_path,
            "n_triangles": len(c_scene),
            "caribu_time": caribu_time,
            "pyrtvpl_time": VPL_time
        }])], ignore_index=True)

        #Store results

        results_df = pd.concat([results_df, pd.DataFrame({
            'indexer': indexer,
            'caribu_PARa': caribu_PARa,
            'vpl_PARa': vpl_PARa,
            'areas': areas,
            'PARi': PARi,
            'input_path': input_path,
            'n_triangles': len(c_scene)
        })], ignore_index=True)


# Save results to a file
    #get the path of the working directory
    results_file = os.path.join(os.getcwd(), "results_caribu_vs_pyrtvpl.csv")
    time_file = os.path.join(os.getcwd(), "time_results_caribu_vs_pyrtvpl.csv")

    results_df.to_csv(results_file, index=False)
    time_df.to_csv(time_file, index=False)

    print("Results saved to", results_file)
    print("Time results saved to", time_file)
    print("--------------------------------------------------")
    
