# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "scipy", "pillow"]
# ///
"""Composite rain running down the outside of backlit stained glass, seen from inside.

The painted layer stays sharp; the water only modulates the light passing through
the glass: drop cores focus light (brighter), drop rims refract it away (darker).
"""

import argparse

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, laplace


def stamp(height, x, y, rx, ry, peak):
    h, w = height.shape
    x0, x1 = int(max(0, x - rx - 1)), int(min(w, x + rx + 2))
    y0, y1 = int(max(0, y - ry - 1)), int(min(h, y + ry + 2))
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = ((xx - x) / rx) ** 2 + ((yy - y) / ry) ** 2
    dome = np.sqrt(np.clip(1 - d, 0, None)) * peak
    np.maximum(height[y0:y1, x0:x1], dome, out=height[y0:y1, x0:x1])


def static_drops(height, rng, count, scale):
    h, w = height.shape
    radii = np.clip(rng.lognormal(np.log(8.0), 0.55, count), 3, 36) * scale
    for r, x, y in zip(radii, rng.uniform(0, w, count), rng.uniform(0, h, count)):
        stamp(height, x, y, r, r * rng.uniform(1.0, 1.3), r * 0.5)


def rivulets(height, rng, count, scale):
    h, w = height.shape
    for _ in range(count):
        x, y = rng.uniform(0, w), rng.uniform(-0.2 * h, 0.5 * h)
        head = rng.uniform(16, 32) * scale
        length = rng.uniform(0.4, 1.4) * h
        vx, travelled = 0.0, 0.0
        while travelled < length and y < h + head:
            vx = 0.93 * vx + rng.normal(0, 0.18)
            x += vx * scale
            y += 1.5 * scale
            travelled += 1.5 * scale
            trail = head * rng.uniform(0.32, 0.48)
            if rng.random() > 0.015:
                stamp(height, x, y, trail, trail, trail * 0.45)
            if rng.random() < 0.01:
                bead = trail * rng.uniform(1.1, 1.8)
                stamp(height, x + rng.normal(0, 2), y, bead, bead * 1.2, bead * 0.5)
        stamp(height, x, y, head, head * 1.25, head * 0.55)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--drops", type=int, default=900)
    parser.add_argument("--rivulets", type=int, default=22)
    parser.add_argument("--scale", type=float, default=1.0, help="size of the water relative to a face close-up")
    parser.add_argument("--wet", type=float, default=0.8, help="brightening of glass under water")
    parser.add_argument("--glow", type=float, default=1.6, help="brightening of drop cores")
    parser.add_argument("--rim", type=float, default=0.9, help="darkening of drop rims")
    parser.add_argument("--blur", type=float, default=2.0, help="softness of the water behind the paint")
    parser.add_argument("--debug", help="save the light map to this path")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    image = np.asarray(Image.open(args.input).convert("RGB"), dtype=np.float32) / 255
    height = np.zeros(image.shape[:2], dtype=np.float32)

    static_drops(height, rng, args.drops, args.scale)
    rivulets(height, rng, args.rivulets, args.scale)
    height = gaussian_filter(height, 1.0)

    gy, gx = np.gradient(height)
    slope = np.tanh(np.hypot(gx, gy) * 1.2)
    focus = np.clip(-laplace(gaussian_filter(height, 3.0 * args.scale)), 0, None)
    focus /= np.percentile(focus[focus > 0], 99) or 1
    wet = np.clip(height / (3 * args.scale), 0, 1)
    light = 1 + args.wet * wet + args.glow * np.clip(focus, 0, 1.5) - args.rim * slope
    light = gaussian_filter(np.clip(light, 0.15, None), args.blur * args.scale)
    if args.debug:
        Image.fromarray(np.clip(light * 100, 0, 255).astype(np.uint8)).save(args.debug)

    linear = image**2.2 * light[..., None]
    result = np.clip(linear, 0, 1) ** (1 / 2.2)
    Image.fromarray((result * 255).astype(np.uint8)).save(args.output, quality=95)


if __name__ == "__main__":
    main()
