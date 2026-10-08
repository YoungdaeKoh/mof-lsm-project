# Shared helpers for the snow diagnostics: model grids and fine-to-model-grid area averaging.
import numpy as np, xarray as xr

D = "/Volumes/data02/MOF_LSM_model_results/snowdiag/"
MINVALID = 0.5

def model_grid(name):
    """Model cell centres after lon%360 + ascending sort (see check_model_snow.py)."""
    if name == "JULES":  # CDO r360x180, lon centres on integers
        return np.arange(-89.5, 90, 1.0), np.arange(0.0, 360, 1.0)
    f = {"LM4p": "lm4p", "CLM5": "clm5", "NoahMP": "noahmp"}[name]
    ds = xr.open_dataset(D + f"{f}_snow_2001_2023.nc")
    return np.sort(ds.lat.values), np.sort(ds.lon.values % 360)

class Binner:
    """Map a fine (lat, lon) grid onto a model grid once; then average any field quickly.
    Each fine pixel goes to the model cell containing its centre; cos(lat)-weighted mean;
    NaN where the valid weight share is below `minvalid`."""
    def __init__(self, flat, flon, mlat, mlon):
        self.shape = (mlat.size, mlon.size)
        le = np.concatenate([[mlat[0] - (mlat[1] - mlat[0]) / 2], (mlat[:-1] + mlat[1:]) / 2,
                             [mlat[-1] + (mlat[-1] - mlat[-2]) / 2]])
        iy = np.searchsorted(le, flat, side="right") - 1
        dlon = mlon[1] - mlon[0]
        assert np.allclose(np.diff(mlon), dlon), "model lon not uniform"
        ix = np.floor(((flon - (mlon[0] - dlon / 2)) % 360) / dlon).astype(np.int64)
        ix = np.minimum(ix, mlon.size - 1)
        oky = (iy >= 0) & (iy < mlat.size)
        idx = np.where(oky[:, None], iy[:, None] * mlon.size + ix[None, :], -1)
        self.idx = idx.ravel().astype(np.int64)
        self.w = np.broadcast_to(np.cos(np.deg2rad(flat))[:, None], idx.shape).ravel().astype(np.float64)
        keep = self.idx >= 0
        self.idx_all, self.w_all = self.idx[keep], self.w[keep]
        self.n = mlat.size * mlon.size
        self.wtot = np.bincount(self.idx_all, self.w_all, minlength=self.n)

    def __call__(self, field, minvalid=MINVALID):
        v = np.asarray(field, np.float64).ravel()
        ok = np.isfinite(v) & (self.idx >= 0)
        sw = np.bincount(self.idx[ok], self.w[ok], minlength=self.n)
        sv = np.bincount(self.idx[ok], self.w[ok] * v[ok], minlength=self.n)
        with np.errstate(invalid="ignore", divide="ignore"):
            m = sv / sw
            m[(sw / self.wtot < minvalid) | (self.wtot == 0)] = np.nan
        return m.reshape(self.shape)
