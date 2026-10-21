"""读取教学流水线的 .isp 中间文件，供生成文档图片使用。"""
import struct
import numpy as np

HEADER = struct.Struct("<8s8IQ4ff3f9fff64s96s")
assert HEADER.size == 284

CFA_NAMES = {0: "RGGB", 1: "BGGR", 2: "GRBG", 3: "GBRG", 0xFFFFFFFF: "NONE"}
CFA_TABLE = {
    0: [[0, 1], [1, 2]],
    1: [[2, 1], [1, 0]],
    2: [[1, 0], [2, 1]],
    3: [[1, 2], [0, 1]],
}


def read_isp(path):
    with open(path, "rb") as f:
        raw = f.read()
    (magic, ver, w, h, ch, cfa, dt, bits, space, data_bytes,
     b0, b1, b2, b3, white, wbr, wbg, wbb,
     m0, m1, m2, m3, m4, m5, m6, m7, m8,
     exposure, gamma, camera, note) = HEADER.unpack(raw[:HEADER.size])
    assert magic.startswith(b"ISPIMG1"), path
    dtype = "<u2" if dt == 0 else "<f4"
    arr = np.frombuffer(raw[HEADER.size:HEADER.size + data_bytes], dtype=dtype)
    arr = arr.reshape(h, w, ch).astype(np.float32)
    return {
        "path": path, "w": w, "h": h, "ch": ch, "cfa": cfa,
        "dtype": "u16" if dt == 0 else "f32",
        "bit_depth": bits, "space": space, "black": [b0, b1, b2, b3], "white": white,
        "wb": [wbr, wbg, wbb],
        "cam_to_xyz": [m0, m1, m2, m3, m4, m5, m6, m7, m8],
        "exposure": exposure, "gamma": gamma,
        "camera": camera.rstrip(b"\0").decode("utf-8", "ignore"),
        "note": note.rstrip(b"\0").decode("utf-8", "ignore"),
        "arr": arr,
    }


def auto_scale(arr, pct=99.5, target=0.95):
    v = arr.reshape(-1)
    v = v[np.isfinite(v)]
    lo = np.percentile(v, 0.5)
    hi = np.percentile(v, pct)
    if hi <= lo + 1e-9:
        hi, lo = 1.0, 0.0
    return target / (hi - lo), lo


def encode(x, gamma=2.2, srgb=False, scale=1.0, lo=0.0):
    x = np.clip((x - lo) * scale, 0, 1)
    if srgb:
        return np.where(x <= 0.0031308, 12.92 * x,
                        1.055 * np.power(x, 1 / 2.4) - 0.055)
    return np.power(x, 1.0 / gamma)


def to_u8(x):
    return (np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8)


def gray_rgb(g):
    return np.repeat(g[..., None], 3, axis=2)


def cfa_map(h, w, cfa):
    """返回 h x w 的 0/1/2 颜色图。"""
    t = np.array(CFA_TABLE.get(int(cfa), [[1, 1], [1, 1]]), dtype=np.uint8)
    yy = np.arange(h)[:, None] % 2
    xx = np.arange(w)[None, :] % 2
    return t[yy, xx]


def crop(arr, x0, y0, x1, y1):
    return arr[y0:y1, x0:x1]


def write_isp(path, arr, meta, note=None):
    """把 float32 数组写成 .isp（主要用于生成教学用的合成小图）。"""
    arr = np.asarray(arr, dtype="<f4")
    h, w = arr.shape[:2]
    ch = 1 if arr.ndim == 2 else arr.shape[2]
    if ch == 1:
        arr = arr.reshape(h, w, 1)
    cam = meta.get("camera", "synthetic").encode("utf-8")[:63]
    note_s = (note if note is not None else meta.get("note", "")).encode("utf-8")[:95]
    b = meta.get("black", [0, 0, 0, 0])
    wb = meta.get("wb", [1, 1, 1])
    m = meta.get("cam_to_xyz", [1, 0, 0, 0, 1, 0, 0, 0, 1])
    hdr = HEADER.pack(
        b"ISPIMG1", 1, w, h, ch, int(meta.get("cfa", 0)), 1, 32, 0,
        arr.nbytes, *b, float(meta.get("white", 1.0)), *wb, *m,
        float(meta.get("exposure", 1.0)), float(meta.get("gamma", 1.0)),
        cam, note_s)
    with open(path, "wb") as f:
        f.write(hdr)
        f.write(arr.tobytes())


def bin_bayer(a):
    """2x2 平均，只用于"看噪声"的可视化（去掉 CFA 棋盘格）。"""
    h, w = a.shape
    h2, w2 = h // 2 * 2, w // 2 * 2
    return a[:h2, :w2].reshape(h2 // 2, 2, w2 // 2, 2).mean(axis=(1, 3))
