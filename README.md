# Description
 TODO

# Installation
## Julia Intallation

Do not use conda, rather manual installation for julia and VPL dependancies

```
Official website for julia installation, example for linux : curl -fsSL https://install.julialang.org | sh
Manual install from master is safer to ensure compatibility and avoid old versions
]add VirtualPlantLab#master
import Pkg
Pkg.add(url="https://github.com/VirtualPlantLab/PlantGeomPrimitives.jl", rev = "master")
Pkg.add(url="https://github.com/VirtualPlantLab/PlantRayTracer.jl", rev = "master")
Pkg.add(url = "https://github.com/VirtualPlantLab/SkyDomes.jl", rev = "master")
```

## Python installation

In your conda environment install the following

```
mamba install -c conda-forge -c openalea3 python numpy juliacall openalea.mtg alinea.caribu
```

PyRTVPL dev install
```
pip install -e .
```