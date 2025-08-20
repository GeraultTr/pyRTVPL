module VPLBridge

using VirtualPlantLab
using PlantGeomPrimitives
using PlantRayTracer
using SkyDomes

export mesh_from_numpy, accelerate_for_sky,
       sky_sources_from_PAR,
       trace_absorbed, trace_absorbed_incident

       
# 1) Build mesh from triangles, build soil and return materials
function mesh_from_numpy(tris::AbstractArray{<:Real,3},
                         τ::AbstractVector{<:Real},
                         ρ::AbstractVector{<:Real},
                         tau_soil, rho_soil; dx=1.0, dy=1.0)
    ntri = size(tris,1)
    @assert size(tris,2)==3 && size(tris,3)==3 "tris must be (ntri,3,3)"
    @assert length(τ)==ntri && length(ρ)==ntri "τ, ρ must have length ntri"

    V = typeof(PlantGeomPrimitives.Vec(0.0,0.0,0.0))
    verts = Vector{V}(undef, 3*ntri)
    k = 1
    @inbounds for i in 1:ntri
        verts[k] = V(Float64(tris[i,1,1]), Float64(tris[i,1,2]), Float64(tris[i,1,3])); k+=1
        verts[k] = V(Float64(tris[i,2,1]), Float64(tris[i,2,2]), Float64(tris[i,2,3])); k+=1
        verts[k] = V(Float64(tris[i,3,1]), Float64(tris[i,3,2]), Float64(tris[i,3,3])); k+=1
    end

    mesh = PlantGeomPrimitives.Mesh(verts)

    # One Lambertian per triangle (band 1 = PAR)
    mats = [PlantRayTracer.Lambertian(τ=Float64(τ[i]), ρ=Float64(ρ[i])) for i in 1:ntri]

    # Attach materials using the function in your PGP
    PlantGeomPrimitives.add_property!(mesh, :materials, mats)

    soil = PlantGeomPrimitives.Rectangle(length = dx, width = dy) ## Vertical plane initialized in x = 0, centered in y = 0, upward in z
    PlantGeomPrimitives.rotatey!(soil, π/2) ## Rotate in the xy plane
    PlantGeomPrimitives.translate!(soil, Vec(0.0, dy/2, 0.0)) ## Corner at (0, 0, 0)
    soil_material = PlantRayTracer.Lambertian(τ = tau_soil, ρ = rho_soil)
    PlantGeomPrimitives.add!(mesh, soil, materials = soil_material)

    return mesh, mats
end


# 2) Accelerate (creates grid cloner = periodize)
function accelerate_for_sky(mesh; nx=5, ny=5, dx=0.0, dy=0.0,
                            parallel=true, maxiter=4, pkill=0.9)
    settings = PlantRayTracer.RTSettings(nx=nx, ny=ny, dx=dx, dy=dy,
                                         parallel=parallel, maxiter=maxiter, pkill=pkill)
    acc_mesh = PlantRayTracer.accelerate(mesh; settings=settings,
                                         acceleration=PlantRayTracer.BVH,
                                         rule=PlantRayTracer.SAH{3}(1,5))
    return acc_mesh, settings
end


# 3) build the sky dome
function sky_sources_from_PAR(acc_mesh, ; direct_PAR::Real, diffuse_PAR::Real,
                              theta_dir::Real, phi_dir::Real,
                              nrays_dir=100_000, nrays_dif=1_000_000,
                              ntheta=9, nphi=12)
    
    return SkyDomes.sky(acc_mesh;
        Idir=direct_PAR, nrays_dir=nrays_dir, theta_dir=theta_dir, phi_dir=phi_dir,
        Idif=diffuse_PAR, nrays_dif=nrays_dif,
        sky_model=SkyDomes.StandardSky, dome_method=SkyDomes.equal_solid_angles,
        ntheta=ntheta, nphi=nphi
    )
end


# 4) Trace and read power from the materials
function trace_absorbed(acc_mesh, mats, settings, sources)
    rt = PlantRayTracer.RayTracer(acc_mesh, sources; settings=settings)
    PlantRayTracer.trace!(rt)
    return [PlantRayTracer.power(m)[1] for m in mats]  # absorbed PAR per triangle
end

# 5) Assembly function to get inputs from Python and send results to Python
function trace_absorbed_incident(tris, τ, ρ, tau_soil, rho_soil, direct_PAR, diffuse_PAR, theta_dir, phi_dir;
                                 nx=5, ny=5, dx=1.0, dy=1.0,
                                 parallel=true, maxiter=4, pkill=0.9,
                                 nrays_dir=100_000, nrays_dif=1_000_000,
                                 ntheta=9, nphi=12)
    total_PAR = direct_PAR + diffuse_PAR
    mesh, mats = mesh_from_numpy(tris, τ, ρ, tau_soil, rho_soil, dx=dx, dy=dy)
    areas = PlantGeomPrimitives.areas(mesh)
    acc_mesh, settings = accelerate_for_sky(mesh; nx=nx, ny=ny, dx=dx, dy=dy,
                                            parallel=parallel, maxiter=maxiter, pkill=pkill)
    sources = sky_sources_from_PAR(acc_mesh;
        direct_PAR=direct_PAR, diffuse_PAR=diffuse_PAR,
        theta_dir=theta_dir, phi_dir=phi_dir, nrays_dir=nrays_dir, nrays_dif=nrays_dif,
        ntheta=ntheta, nphi=nphi)
    absorbed = trace_absorbed(acc_mesh, mats, settings, sources)
    Erel = similar(absorbed)
    PARa = similar(absorbed)
    @inbounds for i in eachindex(absorbed)
        Erel[i] = (absorbed[i] / areas[i]) / total_PAR
        PARa[i] = absorbed[i] / areas[i]
    end
    return (PARa=PARa, Erel=Erel, areas=areas)
end

end # module
