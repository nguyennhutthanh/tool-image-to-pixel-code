"""
main.py
Entry point — supports GUI mode and CLI mode.

CLI usage:
  python main.py image.png --mode SVG --width 64 --height 64 --output out.svg
  python main.py image.png --mode Pygame --colors 16 --grayscale
"""

import sys
from pathlib import Path


def run_cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Image → Pixel Code Generator (CLI)",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("input", help="Input image file")
    parser.add_argument(
        "--mode", "-m", default="Python",
        choices=["Python", "JavaScript Canvas", "CSS Pixel Art", "ASCII Art",
                 "SVG", "Pygame", "Unity C#", "p5.js", "Minecraft"],
        help="Output code mode (default: Python)",
    )
    parser.add_argument("--width",  "-W", type=int, default=64, help="Resize width  (default: 64)")
    parser.add_argument("--height", "-H", type=int, default=64, help="Resize height (default: 64)")
    parser.add_argument("--no-resize", action="store_true", help="Skip resize step")
    parser.add_argument("--colors", "-c", type=int, default=0,
                        help="Quantize to N colors (0 = disabled)")
    parser.add_argument("--dither", action="store_true", help="Use Floyd-Steinberg dithering with --colors")
    parser.add_argument("--grayscale", "-g", action="store_true", help="Convert to grayscale")
    parser.add_argument("--edges",    "-e", action="store_true", help="Apply edge detection")
    parser.add_argument("--output",   "-o", help="Output file (default: print to stdout)")
    args = parser.parse_args()

    from image_processor import ImageProcessor
    from code_generator import CodeGenerator

    proc = ImageProcessor()
    gen  = CodeGenerator()

    print(f"Loading {args.input} …")
    proc.load_image(args.input)

    if not args.no_resize:
        print(f"Resizing to {args.width}×{args.height} …")
        proc.resize_image(args.width, args.height)

    if args.grayscale:
        proc.to_grayscale()
    if args.edges:
        proc.detect_edges()
    if args.colors > 0:
        print(f"Quantizing to {args.colors} colors …")
        proc.quantize_colors(args.colors, dither=args.dither)

    print("Extracting pixels …")
    pixels = proc.extract_pixels()

    print(f"Generating {args.mode} code …")
    code = gen.generate(pixels, args.mode)

    if args.output:
        Path(args.output).write_text(code, encoding="utf-8")
        print(f"Saved to {args.output}  ({len(code):,} bytes)")
    else:
        print(code)


def run_gui() -> None:
    import customtkinter as ctk

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Try to enable Drag-and-Drop via tkinterdnd2
    try:
        from tkinterdnd2 import TkinterDnD

        class _DnDCTk(ctk.CTk, TkinterDnD.DnDWrapper):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.TkdndVersion = TkinterDnD._require(self)

        root = _DnDCTk()
    except Exception:
        root = ctk.CTk()

    from ui import App
    App(root)
    root.mainloop()


if __name__ == "__main__":
    # If the first argument looks like a file, run CLI mode
    if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
        run_cli()
    else:
        run_gui()
