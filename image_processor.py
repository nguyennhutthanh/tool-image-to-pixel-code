"""
image_processor.py
Handles image loading, resizing, and pixel extraction.
"""

from collections import Counter
from PIL import Image, ImageFilter
from typing import List, Tuple, Optional


class ImageProcessor:
    def __init__(self):
        self.image: Optional[Image.Image] = None
        self.original_image: Optional[Image.Image] = None  # before any processing
        self.pixels: List[List[Tuple[int, int, int]]] = []
        self.width: int = 0
        self.height: int = 0
        self.filepath: str = ""

    def load_image(self, filepath: str) -> None:
        self.filepath = filepath
        try:
            self.image = Image.open(filepath).convert("RGB")
        except Exception as e:
            raise ValueError(f"Failed to load image: {e}")
        self.original_image = self.image.copy()
        self.width, self.height = self.image.size
        self.pixels = []

    def load_from_pil(self, img: Image.Image) -> None:
        """Load from a PIL Image (e.g. pasted from clipboard)."""
        self.filepath = "<clipboard>"
        self.image = img.convert("RGB")
        self.original_image = self.image.copy()
        self.width, self.height = self.image.size
        self.pixels = []

    def resize_image(self, new_width: int, new_height: int) -> None:
        if self.image is None:
            raise ValueError("No image loaded.")
        if new_width <= 0 or new_height <= 0:
            raise ValueError("Width and height must be positive integers.")
        self.image = self.image.resize((new_width, new_height), Image.LANCZOS)
        self.width, self.height = self.image.size

    def to_grayscale(self) -> None:
        if self.image is None:
            raise ValueError("No image loaded.")
        self.image = self.image.convert("L").convert("RGB")

    def detect_edges(self) -> None:
        if self.image is None:
            raise ValueError("No image loaded.")
        self.image = self.image.filter(ImageFilter.FIND_EDGES)

    def quantize_colors(self, n_colors: int, dither: bool = False) -> None:
        if self.image is None:
            raise ValueError("No image loaded.")
        n_colors = max(2, min(256, n_colors))
        dither_val = Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE
        self.image = (
            self.image
            .quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT, dither=dither_val)
            .convert("RGB")
        )

    def extract_pixels(self) -> List[List[Tuple[int, int, int]]]:
        if self.image is None:
            raise ValueError("No image loaded.")
        self.pixels = []
        for y in range(self.height):
            row: List[Tuple[int, int, int]] = []
            for x in range(self.width):
                r, g, b = self.image.getpixel((x, y))
                row.append((r, g, b))
            self.pixels.append(row)
        return self.pixels

    def get_color_stats(self):
        """Return (unique_count, [(color, count), ...] most common first)."""
        if not self.pixels:
            return 0, []
        flat = [px for row in self.pixels for px in row]
        counter = Counter(flat)
        return len(counter), counter.most_common()

    def get_image(self) -> Optional[Image.Image]:
        return self.image

    def get_original_image(self) -> Optional[Image.Image]:
        return self.original_image
