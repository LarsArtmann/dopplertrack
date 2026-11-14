"""Terrain tile decoding and caching against a mocked tile server: the Terrarium decode,
the slippy-tile projection, the disk+memory cache, prefetch, and damaged-tile recovery.
The network is never touched."""

import io

import numpy as np
import pytest
from PIL import Image

from dopplertrack.terrain import Terrain


def _tile_png(elev):
    """Encode an elevation array (metres) as a Terrarium RGB PNG."""
    h = np.asarray(elev) + 32768
    rgb = np.zeros((*h.shape, 3), dtype=np.uint8)
    rgb[..., 0] = (h // 256).astype(np.uint8)
    rgb[..., 1] = (h % 256).astype(np.uint8)
    rgb[..., 2] = ((h % 1) * 256).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(rgb, "RGB").save(buf, format="PNG")
    return buf.getvalue()


class _Resp:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


@pytest.fixture
def server(monkeypatch, tmp_path):
    """A fake S3 serving one ramp tile (pixel row == elevation/16 m) and counting calls."""
    calls = []
    body = _tile_png(np.full((256, 256), 2048.0))

    def fake_get(url, timeout=0):
        calls.append(url)
        return _Resp(body)

    monkeypatch.setattr("dopplertrack.terrain.requests.get", fake_get)
    return calls


def test_elevation_decodes_terrarium_encoding(server, tmp_path):
    t = Terrain(zoom=10, cache_dir=tmp_path)
    got = t.elevation([0.0], [15.0])
    assert got.shape == (1,)
    assert got[0] == pytest.approx(2048.0)


def test_tile_projection_hits_expected_tiles(server, tmp_path):
    t = Terrain(zoom=4, cache_dir=tmp_path)
    t.elevation([0.0, 0.0], [0.0, 90.0])
    assert any("/4/8/8.png" in c for c in server)  # lat 0, lon 0
    assert any("/4/12/8.png" in c for c in server)  # lat 0, lon 90
    assert all("/4/" in c for c in server)


def test_disk_cache_serves_second_instance_without_http(server, tmp_path):
    Terrain(zoom=10, cache_dir=tmp_path).elevation([0.0], [15.0])
    assert server, "first instance must download"
    n = len(server)
    Terrain(zoom=10, cache_dir=tmp_path).elevation([0.0], [15.0])
    assert len(server) == n, "second instance must read from disk only"


def test_memory_cache_serves_repeated_queries(server, tmp_path):
    t = Terrain(zoom=10, cache_dir=tmp_path)
    t.elevation([0.0], [15.0])
    n = len(server)
    t.elevation([0.0], [15.001])
    assert len(server) == n


def test_prefetch_downloads_missing_and_skips_cached(server, tmp_path):
    t = Terrain(zoom=10, cache_dir=tmp_path)
    t.prefetch([(522, 335), (523, 335)])
    n = len(server)
    t.prefetch([(522, 335), (523, 335)])
    assert len(server) == n == 2


def test_damaged_cached_tile_is_refetched_once(server, tmp_path):
    t = Terrain(zoom=10, cache_dir=tmp_path)
    p = t._path(522, 335)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"not a png")
    got = t.elevation([0.0], [15.0])
    assert got[0] == pytest.approx(2048.0)
    assert len(server) == 1  # one refetch replaced the damaged file
