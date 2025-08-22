# scripts/build_sysimage.jl
using Pkg

buildenv = joinpath(@__DIR__, "src/openalea/pyRTVPL/VPLBridge/build_env")

# 1) Activate your package env and install the exact deps pinned in Manifest.toml
Pkg.activate(buildenv)
Pkg.develop(path=joinpath(@__DIR__, "src/openalea/pyRTVPL/VPLBridge"))  # adds VPLBridge to the env's
Pkg.instantiate()
Pkg.precompile()

# 2) Use PackageCompiler from a temp env (keeps your Project.toml clean)
Pkg.activate(; temp = true)
Pkg.add("PackageCompiler")
using PackageCompiler

# 3) Switch back to your project env so the right versions are used, then build
Pkg.activate(buildenv)

# Cross-platform sysimage filename
sysimg = joinpath(@__DIR__, "src/openalea/pyRTVPL/VPLBridge/vplbridge_sysimage." *
    (Sys.iswindows() ? "dll" : Sys.isapple() ? "dylib" : "so"))

create_sysimage(
    [:VPLBridge];
    sysimage_path = sysimg,
    cpu_target    = "native",
)
