from alinea.caribu.CaribuScene import CaribuScene
from alinea.caribu.sky_tools import GenSky, GetLight, Gensun, GetLightsSun, spitters_horaire
from openalea.plantgl.all import *
from openalea.plantgl.all import Scene
from alinea.caribu.plantgl_adaptor import scene_to_cscene
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
        triangle_scene = {}
        unique_shape_id = 1

        # id = plant_data["plant_id"]
        # props = plant_data["data"]

        # c_scene = props["scene"]
        
        # indexer[id] = {}

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

            # Next unique id
            unique_shape_id += 1

        # Generates CaribuScenes
        # print(stand_scene, sky, ((0, self.scene_xrange), (0, self.scene_yrange)), opt)
        c_stand_scene_sky = CaribuScene(scene=triangle_scene, light=sky, pattern=(0, 0, scene_xrange, scene_yrange), opt=opt)
        c_stand_scene_sun = CaribuScene(scene=triangle_scene, light=sun, pattern=(0, 0, scene_xrange, scene_yrange), opt=opt)
        
        return c_stand_scene_sky, c_stand_scene_sun, indexer



if __name__ == "__main__":
    # input_path = 'test/inputs/test_big_scene.bgeom'
    input_path = 'test/inputs/test_scene.bgeom'
    scene = Scene(input_path)
    c_scene = scene_to_cscene(scene)
    PARi = 600.

    c_stand_scene_sky, c_stand_scene_sun, indexer = _initialize_model_on_stand(c_scene=c_scene, 
                                                                                        energy=1,
                                                                                        diffuse_model='soc',
                                                                                        azimuts=4,
                                                                                        zenits=5,
                                                                                        DOY=10,
                                                                                        hourTU=12,
                                                                                        latitude=48.84425,
                                                                                        scene_xrange=0.15,
                                                                                        scene_yrange=0.15)

    print("caribu starts...")
    t1 = time.time()
    raw, aggregated_sky = c_stand_scene_sky.run(direct=True, infinite=True)
    print("caribu finished")
    print("regular run took :", time.time() - t1)

    Erel = aggregated_sky['par']['Eabs']  #: Erel is the relative surfacic absorbed energy per organ
    PARa = {k: v * PARi for k, v in Erel.items()}
    raw_Erel = []
    for l in raw["par"]["Eabs"].values():
         raw_Erel += l

    raw_PARa = [v * PARi for v in raw_Erel]

    print("PARa", min(raw_PARa), max(raw_PARa), "Erel", min(raw_Erel), max(raw_Erel))
    
    # Requiered before shutting down
    del c_stand_scene_sky, c_stand_scene_sun