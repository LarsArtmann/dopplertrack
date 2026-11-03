"""Ground elevation from AWS Terrain Tiles (Terrarium encoding), cached on disk."""
from __future__ import annotations

import io
import os
from pathlib import Path

import numpy as np
import requests
from PIL import Image

_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"


class Terrain:
    def __init__(self, zoom: int = 12, cache_dir: str | Path | None = None):
        self.z = zoom
        self.cache = Path(cache_dir or os.environ.get("DOPPLERTRACK_CACHE", Path.home() / ".cache" / "dopplertrack")) / "terrarium" / str(zoom)
        self.cache.mkdir(parents=True, exist_ok=True)
        self._mem: dict[tuple[int, int], np.ndarray] = {}

    def _tile(self, x: int, y: int) -> np.ndarray:
        k = (x, y)
        if k in self._mem:
            return self._mem[k]
        p = self.cache / f"{x}_{y}.png"
        if not p.exists():
            r = requests.get(_URL.format(z=self.z, x=x, y=y), timeout=60)
            r.raise_for_status()
            p.write_bytes(r.content)
        img = np.asarray(Image.open(p).convert("RGB"), dtype=np.float64)
        elev = img[..., 0] * 256 + img[..., 1] + img[..., 2] / 256 - 32768
        self._mem[k] = elev
        return elev

    def elevation(self, lat, lon) -> np.ndarray:
        """Elevation in metres (MSL) for arrays of lat/lon. Nearest pixel."""
        lat = np.atleast_1d(np.asarray(lat, float)); lon = np.atleast_1d(np.asarray(lon, float))
        n = 2 ** self.z
        xf = (lon + 180.0) / 360.0 * n
        latr = np.radians(lat)
        yf = (1 - np.log(np.tan(latr) + 1 / np.cos(latr)) / np.pi) / 2 * n
        xt = np.floor(xf).astype(int); yt = np.floor(yf).astype(int)
        px = np.clip(((xf - xt) * 256).astype(int), 0, 255); py = np.clip(((yf - yt) * 256).astype(int), 0, 255)
        out = np.zeros(lat.shape)
        for (tx, ty) in set(zip(xt.tolist(), yt.tolist())):
            m = (xt == tx) & (yt == ty)
            out[m] = self._tile(tx, ty)[py[m], px[m]]
        return out
