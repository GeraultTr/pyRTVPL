# Description
Python interface class for VirtualPlantLab's RayTracer.

# Installation
## Julia Intallation

Do not use conda, rather manual installation for julia and VPL dependancies
```
Official website for julia installation, example for linux : curl -fsSL https://install.julialang.org | sh
```

Then use the julia system image build script at the root of this repo with the following
```
julia --project -e 'include("build_sysimage.jl")'
```


Note for developpers : To build the package VPLBridge dependancies we used :
- In the package folder we created the environment with 
```
cd to/cloned/folder/src/openalea/pyRTVPL
julia
import Pkg
Pkg.generate("VPLBridge")
# Copied source in empty julia file at the name of the module
Pkg.activate("VPLBridge")
# Manual install from master is safer to ensure compatibility and avoid old versions
Pkg.add(url="https://github.com/VirtualPlantLab/VirtualPlantLab.jl", rev = "master")
Pkg.add(url="https://github.com/VirtualPlantLab/PlantGeomPrimitives.jl", rev = "master")
Pkg.add(url="https://github.com/VirtualPlantLab/PlantRayTracer.jl", rev = "master")
Pkg.add(url = "https://github.com/VirtualPlantLab/SkyDomes.jl", rev = "master")
Pkg.add(["PrecompileTools"])
```
It is normal if you get warnings about VPLBridge not compiling

These installations filled a proper Project.toml that can be used to build the systemimage with the 'build_sysimage.jl' script at the root of this repo. See instructions above to launch it.


## Python installation

In your conda environment install the following

```
mamba install -c conda-forge -c openalea3 python numpy openalea.mtg openalea.caribu

pip install juliacall
```

PyRTVPL dev install
```
pip install -e .
```