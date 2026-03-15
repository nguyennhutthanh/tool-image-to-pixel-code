"""
preview_renderer.py
Displays a popup window with a scaled image preview.
"""

import customtkinter as ctk
from PIL import Image
from typing import Optional


class PreviewRenderer:
    def __init__(self, parent: ctk.CTk):
        self.parent = parent
        self._window: Optional[ctk.CTkToplevel] = None

    def show_preview(self, image: Image.Image) -> None:
        """Open (or re-open) a preview window showing the given image."""
        # Close any existing preview window
        if self._window and self._window.winfo_exists():
            self._window.destroy()

        win = ctk.CTkToplevel(self.parent)
        win.title("Image Preview")
        win.resizable(True, True)
        self._window = win

        MAX_W, MAX_H = 800, 600

        # Scale image to fit within the max display size
        display = image.copy()
        display.thumbnail((MAX_W, MAX_H), Image.LANCZOS)

        ctk_img = ctk.CTkImage(
            light_image=display,
            dark_image=display,
            size=display.size,
        )

        img_label = ctk.CTkLabel(win, image=ctk_img, text="")
        img_label.image = ctk_img  # prevent garbage collection
        img_label.pack(padx=10, pady=10)

        info = (
            f"Original: {image.width} × {image.height} px"
            + (
                f"  |  Preview: {display.width} × {display.height} px"
                if display.size != image.size
                else ""
            )
        )
        ctk.CTkLabel(win, text=info, text_color="gray").pack(pady=(0, 10))

        win.geometry(f"{display.width + 20}x{display.height + 60}")
        win.after(100, win.lift)  # bring window to front
