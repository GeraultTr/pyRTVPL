import numpy as np
import pandas as pd
import pvlib


def build_times(start_when: str, hours: int, step_h: float, tz="Europe/Paris"):
    """
    start_when: "YYYY-MM-DD HH:MM" in local wall time of tz
    hours:      total time span to cover (e.g., 24)
    step_h:     step in hours (e.g., 1, 0.5)
    returns:    pandas.DatetimeIndex of length N
    """
    n = int(round(hours / step_h)) + 1
    freq = pd.to_timedelta(step_h, unit="h")
    return pd.date_range(start=pd.Timestamp(start_when, tz=tz), periods=n, freq=freq)


def vpl_angles_series(lat_deg: float, lon_deg: float, times, altitude_m: float = 0.0):
    """
    Convert pvlib solar position to VPL angles:
      theta_dir = zenith [radians]  (0=overhead, π/2=horizon)
      phi_dir   = azimuth [radians] math-convention (0=+X/East, CCW to +Y/North)
    pvlib azimuth is compass (0=North, 90=East, clockwise). Map with φ = (90 - az) mod 360.
    """
    sp = pvlib.solarposition.get_solarposition(times, lat_deg, lon_deg, altitude=altitude_m)
    theta = np.deg2rad(sp["zenith"].to_numpy())                             # radians
    phi   = np.deg2rad((90.0 - sp["azimuth"].to_numpy()) % 360.0)           # radians
    return theta, phi


if __name__ == '__main__':
    times = build_times('1997-12-17 12:00', hours=4716, step_h=1)
    theta, phi = vpl_angles_series(48.84425, 1.9519167, times, altitude_m=120.0)
    df = pd.DataFrame({"times": times, "theta": theta, "phi": phi})
    df.to_csv("sun_positions.csv")