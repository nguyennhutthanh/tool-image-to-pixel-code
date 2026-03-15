"""
ui.py
Main application window — full feature set.
"""

import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from collections import Counter

import customtkinter as ctk
from PIL import Image, ImageDraw

from image_processor import ImageProcessor
from code_generator import CodeGenerator
from preview_renderer import PreviewRenderer

try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

EXPORT_EXTENSIONS = {
    "Python":            ".py",
    "JavaScript Canvas": ".js",
    "CSS Pixel Art":     ".css",
    "ASCII Art":         ".txt",
    "SVG":               ".svg",
    "Pygame":            ".py",
    "Unity C#":          ".cs",
    "p5.js":             ".js",
    "Minecraft":         ".txt",
}
OUTPUT_MODES = list(EXPORT_EXTENSIONS.keys())


# ── Pixel Canvas ──────────────────────────────────────────────────────────────

class PixelCanvas:
    """Zoomable, scrollable tk.Canvas with grid overlay and pixel hover info."""

    def __init__(self, parent):
        self._base_img: Image.Image | None = None
        self._zoom = 8
        self._grid_on = False
        self._photo = None

        self.frame = tk.Frame(parent, bg="#1c1c1c")

        hbar = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL)
        vbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL)
        self.canvas = tk.Canvas(
            self.frame, bg="#1a1a1a",
            xscrollcommand=hbar.set, yscrollcommand=vbar.set,
            cursor="crosshair", highlightthickness=0,
        )
        hbar.config(command=self.canvas.xview)
        vbar.config(command=self.canvas.yview)

        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar.pack(side=tk.RIGHT,  fill=tk.Y)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._info_var = tk.StringVar(value="Generate code to see the pixel preview")
        tk.Label(
            self.frame, textvariable=self._info_var,
            bg="#1c1c1c", fg="#888888", font=("Consolas", 10), anchor="w", pady=3,
        ).pack(side=tk.BOTTOM, fill=tk.X, padx=8)

        self.canvas.bind("<Motion>",     self._on_motion)
        self.canvas.bind("<MouseWheel>", self._on_wheel)

    def set_image(self, img: Image.Image, zoom: int = 8):
        self._base_img = img
        self._zoom = max(1, zoom)
        self._render()

    def set_zoom(self, value: float):
        self._zoom = max(1, min(32, int(value)))
        self._render()

    def toggle_grid(self, on: bool):
        self._grid_on = on
        self._render()

    def clear(self):
        self._base_img = None
        self.canvas.delete("all")
        self._info_var.set("Generate code to see the pixel preview")

    def _render(self):
        if self._base_img is None:
            return
        from PIL import ImageTk
        w, h = self._base_img.size
        z = self._zoom
        sw, sh = w * z, h * z
        scaled = self._base_img.resize((sw, sh), Image.NEAREST)
        if self._grid_on and z >= 4:
            draw = ImageDraw.Draw(scaled)
            gc = (45, 45, 45)
            for x in range(0, sw, z):
                draw.line([(x, 0), (x, sh)], fill=gc)
            for y in range(0, sh, z):
                draw.line([(0, y), (sw, y)], fill=gc)
        self._photo = ImageTk.PhotoImage(scaled)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self._photo)
        self.canvas.configure(scrollregion=(0, 0, sw, sh))

    def _on_motion(self, event):
        if self._base_img is None:
            return
        x = int(self.canvas.canvasx(event.x) / self._zoom)
        y = int(self.canvas.canvasy(event.y) / self._zoom)
        iw, ih = self._base_img.size
        if 0 <= x < iw and 0 <= y < ih:
            r, g, b = self._base_img.getpixel((x, y))
            self._info_var.set(
                f"  ({x}, {y})   │   RGB({r}, {g}, {b})   │   #{r:02x}{g:02x}{b:02x}"
            )
        else:
            self._info_var.set("")

    def _on_wheel(self, event):
        self.set_zoom(self._zoom + (1 if event.delta > 0 else -1))


# ── App ───────────────────────────────────────────────────────────────────────

class App:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("Image → Pixel Code Generator")
        self.root.geometry("1320x780")
        self.root.minsize(1050, 660)

        self.processor = ImageProcessor()
        self.generator = CodeGenerator()
        self.renderer  = PreviewRenderer(root)

        self.generated_code = ""
        self._compare_refs: list = []        # keep CTkImage refs alive
        self._batch_files: list[str] = []
        self._batch_folder: str = ""
        self._original_clipboard_image: Image.Image | None = None

        self._build_ui()

    # ══ Build UI ══════════════════════════════════════════════════════════════

    def _build_ui(self):
        # Left panel
        left = ctk.CTkFrame(self.root, width=315, corner_radius=10)
        left.pack(side="left", fill="y", padx=10, pady=10)
        left.pack_propagate(False)

        ctk.CTkLabel(left, text="Image → Code",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(18, 3))
        ctk.CTkLabel(left, text="Pixel Code Generator",
                     text_color="gray", font=ctk.CTkFont(size=11)).pack(pady=(0, 10))

        self._build_upload_section(left)
        self._build_processing_section(left)
        self._build_resize_section(left)
        self._build_mode_section(left)
        self._build_action_buttons(left)
        self._build_status_bar(left)

        # Right panel
        right = ctk.CTkFrame(self.root, corner_radius=10)
        right.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)

        hdr = ctk.CTkFrame(right, fg_color="transparent")
        hdr.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(hdr, text="Output",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        self.info_label = ctk.CTkLabel(hdr, text="", text_color="gray")
        self.info_label.pack(side="right")

        self.tabs = ctk.CTkTabview(right)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        for name in ("Code", "Preview", "Compare", "Stats", "Batch"):
            self.tabs.add(name)

        self._build_code_tab()
        self._build_preview_tab()
        self._build_compare_tab()
        self._build_stats_tab()
        self._build_batch_tab()

    # ── Left panel sections ───────────────────────────────────────────────────

    def _build_upload_section(self, p):
        ctk.CTkLabel(p, text="1. Upload Image",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=14, pady=(8, 2))

        self.file_label = ctk.CTkLabel(
            p, text="No file selected", wraplength=280,
            text_color="gray", font=ctk.CTkFont(size=11),
        )
        self.file_label.pack(anchor="w", padx=14)

        btn_row = ctk.CTkFrame(p, fg_color="transparent")
        btn_row.pack(padx=14, pady=(4, 2), fill="x")
        ctk.CTkButton(btn_row, text="Browse", command=self._browse_image,
                      width=118).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_row, text="Paste (Ctrl+V)", command=self._paste_clipboard,
                      width=130, fg_color="gray40", hover_color="gray25").pack(side="left")

        if DND_AVAILABLE:
            drop = ctk.CTkLabel(
                p, text="⬇  Drop image here",
                height=36, corner_radius=8,
                fg_color="#2a2a3a", text_color="#8888cc",
                font=ctk.CTkFont(size=11),
            )
            drop.pack(padx=14, pady=(2, 4), fill="x")
            drop.drop_target_register(DND_FILES)
            drop.dnd_bind("<<Drop>>", self._on_drop)

        self.root.bind("<Control-v>", lambda _e: self._paste_clipboard())

    def _build_processing_section(self, p):
        ctk.CTkLabel(p, text="2. Image Processing",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=14, pady=(10, 2))

        self.gray_var    = ctk.BooleanVar(value=False)
        self.edge_var    = ctk.BooleanVar(value=False)
        self.quantize_var = ctk.BooleanVar(value=False)
        self.dither_var  = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(p, text="Grayscale",      variable=self.gray_var ).pack(anchor="w", padx=14, pady=2)
        ctk.CTkCheckBox(p, text="Edge Detection", variable=self.edge_var ).pack(anchor="w", padx=14, pady=2)

        qrow = ctk.CTkFrame(p, fg_color="transparent")
        qrow.pack(anchor="w", padx=14, pady=2, fill="x")
        ctk.CTkCheckBox(qrow, text="Color Quantize", variable=self.quantize_var,
                        command=self._toggle_quantize).pack(side="left")
        self.colors_entry = ctk.CTkEntry(qrow, width=50, state="disabled")
        self.colors_entry.insert(0, "16")
        self.colors_entry.pack(side="left", padx=(8, 2))
        ctk.CTkLabel(qrow, text="colors", text_color="gray").pack(side="left")

        ctk.CTkCheckBox(p, text="Dithering (with quantize)",
                        variable=self.dither_var).pack(anchor="w", padx=14, pady=2)

    def _build_resize_section(self, p):
        ctk.CTkLabel(p, text="3. Resize",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=14, pady=(10, 2))

        self.resize_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(p, text="Resize before processing", variable=self.resize_var,
                        command=self._toggle_resize).pack(anchor="w", padx=14, pady=2)

        f = ctk.CTkFrame(p)
        f.pack(padx=14, pady=4, fill="x")
        for i, (lbl, default) in enumerate([("Width:", "64"), ("Height:", "64")]):
            ctk.CTkLabel(f, text=lbl, width=54).grid(row=i, column=0, padx=6, pady=3, sticky="w")
            e = ctk.CTkEntry(f, width=72)
            e.insert(0, default)
            e.grid(row=i, column=1, padx=6, pady=3)
            ctk.CTkLabel(f, text="px", text_color="gray").grid(row=i, column=2, padx=2)
            setattr(self, "width_entry" if i == 0 else "height_entry", e)

    def _build_mode_section(self, p):
        ctk.CTkLabel(p, text="4. Output Mode",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=14, pady=(10, 2))
        self.mode_var = ctk.StringVar(value="Python")
        ctk.CTkOptionMenu(p, values=OUTPUT_MODES, variable=self.mode_var,
                          ).pack(padx=14, pady=4, fill="x")

    def _build_action_buttons(self, p):
        ctk.CTkLabel(p, text="5. Actions",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=14, pady=(10, 2))
        for text, cmd, fg, hv in [
            ("Generate Code",  self._generate_code,  "#2e7d32", "#1b5e20"),
            ("Preview Popup",  self._preview_popup,  None,      None),
            ("Export Code",    self._export_code,    None,      None),
            ("Clear",          self._clear,          "gray40",  "gray25"),
        ]:
            kw = {"text": text, "command": cmd}
            if fg: kw["fg_color"]    = fg
            if hv: kw["hover_color"] = hv
            ctk.CTkButton(p, **kw).pack(padx=14, pady=3, fill="x")

    def _build_status_bar(self, p):
        self.status_label = ctk.CTkLabel(p, text="Ready", text_color="gray",
                                         font=ctk.CTkFont(size=11))
        self.status_label.pack(pady=(8, 3))
        self.progress = ctk.CTkProgressBar(p)
        self.progress.set(0)
        self.progress.pack(padx=14, fill="x", pady=(0, 12))

    # ── Tabs ─────────────────────────────────────────────────────────────────

    def _build_code_tab(self):
        tab = self.tabs.tab("Code")
        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 4))
        ctk.CTkButton(toolbar, text="Copy Code", width=110,
                      command=self._copy_code).pack(side="right")
        self.code_text = ctk.CTkTextbox(
            tab, font=ctk.CTkFont(family="Courier New", size=12), wrap="none")
        self.code_text.pack(fill="both", expand=True)

    def _build_preview_tab(self):
        tab = self.tabs.tab("Preview")

        bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(bar, text="Zoom:").pack(side="left", padx=(0, 4))
        self._zoom_label = ctk.CTkLabel(bar, text="8×", width=34)
        self._zoom_label.pack(side="left")
        self._zoom_slider = ctk.CTkSlider(
            bar, from_=1, to=24, number_of_steps=23,
            command=self._on_zoom_change, width=160)
        self._zoom_slider.set(8)
        self._zoom_slider.pack(side="left", padx=6)

        self._grid_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(bar, text="Grid", variable=self._grid_var,
                        command=lambda: self._pixel_canvas.toggle_grid(self._grid_var.get())
                        ).pack(side="left", padx=10)

        ctk.CTkButton(bar, text="Save PNG", width=90,
                      command=self._save_preview_png).pack(side="right")

        self._pixel_canvas = PixelCanvas(tab)
        self._pixel_canvas.frame.pack(fill="both", expand=True)

    def _build_compare_tab(self):
        tab = self.tabs.tab("Compare")
        self._compare_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self._compare_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self._compare_frame,
                     text="Generate code to see before/after comparison.",
                     text_color="gray").pack(expand=True)

    def _build_stats_tab(self):
        tab = self.tabs.tab("Stats")
        self._stats_frame = ctk.CTkScrollableFrame(tab)
        self._stats_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self._stats_frame,
                     text="Generate code to see color statistics.",
                     text_color="gray").pack(pady=40)

    def _build_batch_tab(self):
        tab = self.tabs.tab("Batch")

        list_frame = ctk.CTkFrame(tab)
        list_frame.pack(fill="both", expand=True, pady=(0, 6))
        ctk.CTkLabel(list_frame, text="Files to process:",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=8, pady=(6, 2))

        self._batch_listbox = tk.Listbox(
            list_frame, selectmode=tk.EXTENDED,
            bg="#2b2b2b", fg="#dddddd", selectbackground="#1f6aa5",
            borderwidth=0, highlightthickness=0, font=("Consolas", 10),
        )
        sb = tk.Scrollbar(list_frame, command=self._batch_listbox.yview)
        self._batch_listbox.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._batch_listbox.pack(fill="both", expand=True, padx=8, pady=4)

        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.pack(fill="x", pady=4)
        ctk.CTkButton(btn_row, text="Add Files", width=100,
                      command=self._batch_add_files).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Remove Selected", width=130,
                      command=self._batch_remove,
                      fg_color="gray40", hover_color="gray25").pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Clear All", width=88,
                      command=self._batch_clear,
                      fg_color="gray40", hover_color="gray25").pack(side="left", padx=4)

        out_row = ctk.CTkFrame(tab, fg_color="transparent")
        out_row.pack(fill="x", pady=4)
        ctk.CTkLabel(out_row, text="Output folder:").pack(side="left", padx=4)
        self._batch_folder_label = ctk.CTkLabel(out_row, text="<same as input>", text_color="gray")
        self._batch_folder_label.pack(side="left", padx=4)
        ctk.CTkButton(out_row, text="Choose Folder", width=120,
                      command=self._batch_choose_folder).pack(side="right", padx=4)

        run_row = ctk.CTkFrame(tab, fg_color="transparent")
        run_row.pack(fill="x", pady=4)
        ctk.CTkButton(run_row, text="▶  Run Batch", command=self._run_batch,
                      fg_color="#2e7d32", hover_color="#1b5e20", width=120).pack(side="left", padx=4)
        self._batch_progress = ctk.CTkProgressBar(run_row)
        self._batch_progress.set(0)
        self._batch_progress.pack(side="left", fill="x", expand=True, padx=8)

        self._batch_log = ctk.CTkTextbox(tab, height=130,
                                         font=ctk.CTkFont(family="Courier New", size=11))
        self._batch_log.pack(fill="x", pady=(4, 0))

    # ══ Toggles ══════════════════════════════════════════════════════════════

    def _toggle_resize(self):
        s = "normal" if self.resize_var.get() else "disabled"
        self.width_entry.configure(state=s)
        self.height_entry.configure(state=s)

    def _toggle_quantize(self):
        self.colors_entry.configure(state="normal" if self.quantize_var.get() else "disabled")

    def _on_zoom_change(self, value):
        z = max(1, int(value))
        self._zoom_label.configure(text=f"{z}×")
        self._pixel_canvas.set_zoom(z)

    # ══ Image Loading ═════════════════════════════════════════════════════════

    def _browse_image(self):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
                       ("All files", "*.*")],
        )
        if path:
            self._load_image_file(path)

    def _on_drop(self, event):
        data = event.data.strip()
        path = data[1:data.index("}")] if data.startswith("{") else data.split()[0]
        self._load_image_file(path)

    def _paste_clipboard(self):
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img is None:
                messagebox.showinfo("Clipboard", "No image found in clipboard.\nCopy an image first.")
                return
            self._original_clipboard_image = img.convert("RGB")
            self.processor.load_from_pil(img)
            self.file_label.configure(
                text=f"<clipboard>  {self.processor.width}×{self.processor.height} px",
                text_color="white",
            )
            self._set_status("Loaded from clipboard")
        except Exception as e:
            messagebox.showerror("Clipboard Error", str(e))

    def _load_image_file(self, path: str):
        try:
            self.processor.load_image(path)
            fname = Path(path).name
            self.file_label.configure(
                text=f"{fname}\n{self.processor.width}×{self.processor.height} px",
                text_color="white",
            )
            self._set_status(f"Loaded: {fname}")
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    # ══ Generation ════════════════════════════════════════════════════════════

    def _generate_code(self):
        if self.processor.image is None:
            messagebox.showwarning("No Image", "Please upload an image first.")
            return
        # Capture UI values on main thread before launching background thread
        settings = {
            "filepath":  self.processor.filepath,
            "resize":    self.resize_var.get(),
            "width":     self.width_entry.get(),
            "height":    self.height_entry.get(),
            "grayscale": self.gray_var.get(),
            "edges":     self.edge_var.get(),
            "quantize":  self.quantize_var.get(),
            "colors":    self.colors_entry.get(),
            "dither":    self.dither_var.get(),
            "mode":      self.mode_var.get(),
        }
        threading.Thread(target=self._run_generation, args=(settings,), daemon=True).start()

    def _run_generation(self, s: dict):
        try:
            self._set_status("Loading…")
            self.progress.set(0.05)

            proc = ImageProcessor()
            if s["filepath"] == "<clipboard>" and self._original_clipboard_image:
                proc.load_from_pil(self._original_clipboard_image)
            else:
                proc.load_image(s["filepath"])
            original_img = proc.get_original_image().copy()
            self.progress.set(0.15)

            if s["resize"]:
                try:
                    w, h = int(s["width"]), int(s["height"])
                except ValueError:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Invalid Size", "Width and height must be integers."))
                    return
                self._set_status(f"Resizing to {w}×{h}…")
                proc.resize_image(w, h)
            self.progress.set(0.25)

            if s["grayscale"]:
                proc.to_grayscale()
            if s["edges"]:
                proc.detect_edges()
            if s["quantize"]:
                try:    n = int(s["colors"])
                except: n = 16
                self._set_status(f"Quantizing to {n} colors…")
                proc.quantize_colors(n, dither=s["dither"])
            self.progress.set(0.45)

            self._set_status("Extracting pixels…")
            pixels = proc.extract_pixels()
            processed_img = proc.get_image().copy()
            self.progress.set(0.60)

            mode = s["mode"]
            self._set_status(f"Generating {mode} code…")
            code = self.generator.generate(pixels, mode)
            self.generated_code = code
            # also expose processor for preview popup / clear
            self.processor = proc
            self.progress.set(0.85)

            self._set_status("Rendering…")
            self.root.after(0, lambda: self._update_all(code, pixels, processed_img, original_img, mode))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, lambda: self._set_status("Error"))
            self.root.after(0, lambda: self.progress.set(0))

    def _update_all(self, code, pixels, processed_img, original_img, mode):
        # Code tab
        self.code_text.delete("1.0", "end")
        self.code_text.insert("1.0", code)
        w, h = self.processor.width, self.processor.height
        self.info_label.configure(
            text=f"{code.count(chr(10))+1:,} lines · {len(code):,} chars · {w}×{h} px"
        )

        # Preview tab
        self._pixel_canvas.set_image(processed_img, zoom=int(self._zoom_slider.get()))

        # Compare tab
        self._update_compare(original_img, processed_img)

        # Stats tab
        self._update_stats(pixels)

        self._set_status("Done!")
        self.progress.set(1.0)
        self.tabs.set("Preview")

    # ── Compare tab ──────────────────────────────────────────────────────────

    def _update_compare(self, original: Image.Image, processed: Image.Image):
        for w in self._compare_frame.winfo_children():
            w.destroy()
        self._compare_refs = []

        for img, label_text in [(original, "Original"), (processed, "Processed (pixel)")]:
            col = ctk.CTkFrame(self._compare_frame)
            col.pack(side="left", fill="both", expand=True, padx=6, pady=6)
            ctk.CTkLabel(col, text=label_text,
                         font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(8, 4))
            disp = img.copy()
            disp.thumbnail((400, 400), Image.LANCZOS)
            ci = ctk.CTkImage(light_image=disp, dark_image=disp, size=disp.size)
            self._compare_refs.append(ci)
            ctk.CTkLabel(col, image=ci, text="").pack(pady=4)
            ctk.CTkLabel(col, text=f"{img.width}×{img.height} px",
                         text_color="gray").pack(pady=(0, 8))

    # ── Stats tab ─────────────────────────────────────────────────────────────

    def _update_stats(self, pixels):
        for w in self._stats_frame.winfo_children():
            w.destroy()

        flat   = [px for row in pixels for px in row]
        total  = len(flat)
        cnt    = Counter(flat)
        unique = len(cnt)
        top    = cnt.most_common(64)

        ctk.CTkLabel(
            self._stats_frame,
            text=(f"Total pixels: {total:,}   │   Unique colors: {unique:,}   │   "
                  f"Est. code size: ~{max(1, len(self.generated_code)//1024)} KB"),
            font=ctk.CTkFont(size=12),
        ).pack(pady=(12, 6), anchor="w")

        ctk.CTkLabel(self._stats_frame,
                     text=f"Color Palette  (top {len(top)} colors, 8 per row):",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=4)

        palette_frame = ctk.CTkFrame(self._stats_frame, fg_color="transparent")
        palette_frame.pack(fill="x", padx=4, pady=6)

        for i, ((r, g, b), count) in enumerate(top):
            hex_c = f"#{r:02x}{g:02x}{b:02x}"
            pct   = count / total * 100
            cell  = tk.Frame(palette_frame, bg="#1c1c1c")
            cell.grid(row=i // 8, column=i % 8, padx=4, pady=4)
            tk.Frame(cell, bg=hex_c, width=40, height=40).pack()
            tk.Label(cell, text=hex_c,   bg="#1c1c1c", fg="#aaaaaa", font=("Consolas", 8)).pack()
            tk.Label(cell, text=f"{pct:.1f}%", bg="#1c1c1c", fg="#777777", font=("Consolas", 8)).pack()

    # ══ Actions ══════════════════════════════════════════════════════════════

    def _copy_code(self):
        if not self.generated_code:
            messagebox.showwarning("No Code", "Generate code first.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.generated_code)
        self._set_status("Code copied to clipboard!")

    def _export_code(self):
        if not self.generated_code:
            messagebox.showwarning("No Code", "Generate code first.")
            return
        mode = self.mode_var.get()
        ext  = EXPORT_EXTENSIONS.get(mode, ".txt")
        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[(f"{mode} file", f"*{ext}"), ("All files", "*.*")],
            title="Export Generated Code",
        )
        if path:
            try:
                Path(path).write_text(self.generated_code, encoding="utf-8")
                self._set_status(f"Exported: {Path(path).name}")
                messagebox.showinfo("Exported", f"Saved to:\n{path}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))

    def _save_preview_png(self):
        if self._pixel_canvas._base_img is None:
            messagebox.showwarning("No Preview", "Generate code first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
            title="Save Preview as PNG",
        )
        if path:
            try:
                self._pixel_canvas._base_img.save(path)
                self._set_status(f"Saved: {Path(path).name}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))

    def _preview_popup(self):
        if self.processor.image is None:
            messagebox.showwarning("No Image", "Upload an image first.")
            return
        self.renderer.show_preview(self.processor.image)

    def _clear(self):
        self.processor  = ImageProcessor()
        self.generated_code = ""
        self._compare_refs  = []
        self._original_clipboard_image = None

        self.file_label.configure(text="No file selected", text_color="gray")
        self.code_text.delete("1.0", "end")
        self.info_label.configure(text="")
        self.progress.set(0)
        self._pixel_canvas.clear()
        self._set_status("Ready")

        for w in self._compare_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._compare_frame,
                     text="Generate code to see before/after comparison.",
                     text_color="gray").pack(expand=True)

        for w in self._stats_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._stats_frame,
                     text="Generate code to see color statistics.",
                     text_color="gray").pack(pady=40)

        self.tabs.set("Code")

    # ══ Batch ════════════════════════════════════════════════════════════════

    def _batch_add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
                       ("All files", "*.*")],
        )
        for p in paths:
            if p not in self._batch_files:
                self._batch_files.append(p)
                self._batch_listbox.insert(tk.END, Path(p).name)

    def _batch_remove(self):
        for i in reversed(self._batch_listbox.curselection()):
            self._batch_listbox.delete(i)
            self._batch_files.pop(i)

    def _batch_clear(self):
        self._batch_listbox.delete(0, tk.END)
        self._batch_files.clear()

    def _batch_choose_folder(self):
        folder = filedialog.askdirectory(title="Choose Output Folder")
        if folder:
            self._batch_folder = folder
            self._batch_folder_label.configure(text=folder, text_color="white")

    def _run_batch(self):
        if not self._batch_files:
            messagebox.showwarning("No Files", "Add files to the batch list first.")
            return
        # Capture settings on main thread
        settings = {
            "mode":     self.mode_var.get(),
            "resize":   self.resize_var.get(),
            "width":    self.width_entry.get(),
            "height":   self.height_entry.get(),
            "grayscale":self.gray_var.get(),
            "edges":    self.edge_var.get(),
            "quantize": self.quantize_var.get(),
            "colors":   self.colors_entry.get(),
            "dither":   self.dither_var.get(),
            "out_folder": self._batch_folder,
            "files":    self._batch_files.copy(),
        }
        threading.Thread(target=self._batch_worker, args=(settings,), daemon=True).start()

    def _batch_worker(self, s: dict):
        files  = s["files"]
        mode   = s["mode"]
        ext    = EXPORT_EXTENSIONS.get(mode, ".txt")
        total  = len(files)
        self._blog_clear()
        self._blog_write(f"Batch: {total} files  │  mode={mode}\n{'─'*44}\n")

        for i, filepath in enumerate(files):
            try:
                proc = ImageProcessor()
                proc.load_image(filepath)
                if s["resize"]:
                    proc.resize_image(int(s["width"]), int(s["height"]))
                if s["grayscale"]:
                    proc.to_grayscale()
                if s["edges"]:
                    proc.detect_edges()
                if s["quantize"]:
                    try: n = int(s["colors"])
                    except: n = 16
                    proc.quantize_colors(n, dither=s["dither"])
                pixels = proc.extract_pixels()
                code   = self.generator.generate(pixels, mode)

                out_dir  = Path(s["out_folder"]) if s["out_folder"] else Path(filepath).parent
                out_path = out_dir / (Path(filepath).stem + ext)
                out_path.write_text(code, encoding="utf-8")
                self._blog_write(f"✓ {Path(filepath).name}  →  {out_path.name}\n")
            except Exception as e:
                self._blog_write(f"✗ {Path(filepath).name}: {e}\n")

            self.root.after(0, lambda v=(i + 1) / total: self._batch_progress.set(v))

        self._blog_write(f"\nDone! {total} file(s) processed.\n")
        self.root.after(0, lambda: self._set_status("Batch complete!"))

    def _blog_clear(self):
        self.root.after(0, lambda: self._batch_log.delete("1.0", "end"))

    def _blog_write(self, text: str):
        self.root.after(0, lambda t=text: self._batch_log.insert("end", t))

    # ══ Utility ══════════════════════════════════════════════════════════════

    def _set_status(self, text: str):
        self.root.after(0, lambda: self.status_label.configure(text=text))
