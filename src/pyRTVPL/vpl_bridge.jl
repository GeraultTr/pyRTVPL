module VPLBridge

using VirtualPlantLab
using PlantGeomPrimitives
using PlantRayTracer
using SkyDomes

export mesh_from_numpy, accelerate_for_sky,
       sky_sources_for, sky_sources_from_PAR,
       trace_absorbed, trace_absorbed_incident

       
# ---------- 1) Build mesh AND return materials ----------
function mesh_from_numpy(tris::AbstractArray{<:Real,3},
                         τ::AbstractVector{<:Real},
                         ρ::AbstractVector{<:Real})
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

    # Try normals if your PGP needs them
    mesh = let m = nothing
        try
            # Compute one unit normal per triangle
            normals = Vector{V}(undef, ntri)
            @inbounds for i in 1:ntri
                a,b,c = verts[3i-2], verts[3i-1], verts[3i]
                ux,uy,uz = b[1]-a[1], b[2]-a[2], b[3]-a[3]
                vx,vy,vz = c[1]-a[1], c[2]-a[2], c[3]-a[3]
                nx = uy*vz - uz*vy; ny = uz*vx - ux*vz; nz = ux*vy - uy*vx
                L = sqrt(nx*nx + ny*ny + nz*nz)
                normals[i] = L==0 ? V(0.0,0.0,1.0) : V(nx/L, ny/L, nz/L)
            end
            PlantGeomPrimitives.Mesh(verts, normals)
        catch
            PlantGeomPrimitives.Mesh(verts)
        end
    end

    # One Lambertian per triangle (band 1 = PAR)
    mats = [PlantRayTracer.Lambertian(τ=Float64(τ[i]), ρ=Float64(ρ[i])) for i in 1:ntri]

    # Attach materials using the function in your PGP
    PlantGeomPrimitives.add_property!(mesh, :materials, mats)

    return mesh, mats
end


# ---------- 2) Accelerate (creates grid cloner) ----------
function accelerate_for_sky(mesh; nx=5, ny=5, dx=0.0, dy=0.0,
                            parallel=true, maxiter=4, pkill=0.9)
    settings = PlantRayTracer.RTSettings(nx=nx, ny=ny, dx=dx, dy=dy,
                                         parallel=parallel, maxiter=maxiter, pkill=pkill)
    acc_mesh = PlantRayTracer.accelerate(mesh; settings=settings,
                                         acceleration=PlantRayTracer.BVH,
                                         rule=PlantRayTracer.SAH{3}(1,5))
    return acc_mesh, settings
end


# ---------- 3a) Clear-sky sources (Julia computes PAR) ----------
function sky_sources_for(acc_mesh, ; lat_deg=48.7, DOY=182, f=0.5, TL=3.0,
                         nrays_dir=100_000, nrays_dif=1_000_000,
                         ntheta=9, nphi=12)
    cs = SkyDomes.clear_sky(lat=deg2rad(lat_deg), DOY=DOY, f=f, TL=TL)
    f_dir = SkyDomes.waveband_conversion(Itype=:direct,  waveband=:PAR, mode=:flux)
    f_dif = SkyDomes.waveband_conversion(Itype=:diffuse, waveband=:PAR, mode=:flux)
    return SkyDomes.sky(acc_mesh;
        Idir=cs.Idir*f_dir, nrays_dir=nrays_dir, theta_dir=cs.theta, phi_dir=cs.phi,
        Idif=cs.Idif*f_dif,  nrays_dif=nrays_dif,
        sky_model=SkyDomes.StandardSky, dome_method=SkyDomes.equal_solid_angles,
        ntheta=ntheta, nphi=nphi
    )
end


# ---------- 3b) Your own PAR + angles ----------
function sky_sources_from_PAR(acc_mesh, ; direct_PAR::Real, diffuse_PAR::Real,
                              theta_dir::Real, phi_dir::Real,
                              nrays_dir=100_000, nrays_dif=1_000_000,
                              ntheta=9, nphi=12, angles_in_degrees::Bool=false)
    θ = angles_in_degrees ? deg2rad(theta_dir) : theta_dir
    ϕ = angles_in_degrees ? deg2rad(phi_dir)   : phi_dir
    return SkyDomes.sky(acc_mesh;
        Idir=direct_PAR, nrays_dir=nrays_dir, theta_dir=θ, phi_dir=ϕ,
        Idif=diffuse_PAR, nrays_dif=nrays_dif,
        sky_model=SkyDomes.StandardSky, dome_method=SkyDomes.equal_solid_angles,
        ntheta=ntheta, nphi=nphi
    )
end

# ---------- 4) Trace (read power from the mats you built) ----------
function trace_absorbed(acc_mesh, mats, settings, sources)
    rt = PlantRayTracer.RayTracer(acc_mesh, sources; settings=settings)
    PlantRayTracer.trace!(rt)
    return [PlantRayTracer.power(m)[1] for m in mats]  # absorbed PAR per triangle
end

# ---------- 5) One-shot: you pass PAR & angles from Python ----------
function trace_absorbed_incident(tris, τ, ρ, direct_PAR, diffuse_PAR, theta_dir, phi_dir;
                                 nx=5, ny=5, dx=0.0, dy=0.0,
                                 parallel=true, maxiter=4, pkill=0.9,
                                 nrays_dir=100_000, nrays_dif=1_000_000,
                                 ntheta=9, nphi=12, angles_in_degrees::Bool=false)
    mesh, mats = mesh_from_numpy(tris, τ, ρ)
    acc_mesh, settings = accelerate_for_sky(mesh; nx=nx, ny=ny, dx=dx, dy=dy,
                                            parallel=parallel, maxiter=maxiter, pkill=pkill)
    sources = sky_sources_from_PAR(acc_mesh;
        direct_PAR=direct_PAR, diffuse_PAR=diffuse_PAR,
        theta_dir=theta_dir, phi_dir=phi_dir, nrays_dir=nrays_dir, nrays_dif=nrays_dif,
        ntheta=ntheta, nphi=nphi, angles_in_degrees=angles_in_degrees
    )
    absorbed = trace_absorbed(acc_mesh, mats, settings, sources)
    incident = similar(absorbed)
    @inbounds for i in eachindex(absorbed)
        incident[i] = absorbed[i] / (1 - (Float64(ρ[i]) + Float64(τ[i])))
    end
    return (absorbed=absorbed, incident=incident)
end

end # module
