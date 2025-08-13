# DO NOT USE CONDA

```
Official website : curl -fsSL https://install.julialang.org | sh
Manual install from master is safer to ensure compatibility and avoid old versions
]add VirtualPlantLab#master
import Pkg
Pkg.add(url="https://github.com/VirtualPlantLab/PlantGeomPrimitives.jl", rev = "master")
Pkg.add(url="https://github.com/VirtualPlantLab/PlantRayTracer.jl", rev = "master")
Pkg.add(url = "https://github.com/VirtualPlantLab/SkyDomes.jl", rev = "master")
```