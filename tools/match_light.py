# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "scipy", "pillow"]
# ///
"""Give an edited image the local lighting of the aligned original it was edited from.

Fine detail comes from the edit; brightness and colour at a coarse scale come from the original.
"""

import argparse

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter


def load_linear(path, size=None):
    image = Image.open(path).convert("RGB")
    if size:
        image = image.resize(size, Image.LANCZOS)
    return (np.asarray(image, dtype=np.float32) / 255) ** 2.2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("original")
    parser.add_argument("edited")
    parser.add_argument("output")
    parser.add_argument("--radius", type=float, default=12, help="blur radius of the lighting, in pixels")
    args = parser.parse_args()

    original = load_linear(args.original)
    edited = load_linear(args.edited, (original.shape[1], original.shape[0]))

    def smooth(image):
        return np.stack([gaussian_filter(image[..., c], args.radius) for c in range(3)], axis=-1)

    gain = (smooth(original) + 1e-3) / (smooth(edited) + 1e-3)
    result = np.clip(edited * gain, 0, 1) ** (1 / 2.2)
    Image.fromarray((result * 255).astype(np.uint8)).save(args.output)


if __name__ == "__main__":
    main()
