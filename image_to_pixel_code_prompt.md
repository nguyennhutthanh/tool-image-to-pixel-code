# AI Project Prompt: Image ? Pixel Code Generator Tool

## 1. Project Overview

Build a **Python desktop application** that converts an image into code that recreates the image pixel-by-pixel.

The application should:

* Take an **image file as input**
* Read **pixel color values**
* Convert those pixels into **code instructions**
* Output **code that redraws the image**

This means every pixel of the image becomes a **code instruction**.

Example concept:

Input image ? pixel data ? generated drawing code.

---

# 2. Goal of the Tool

Create a **developer tool** that transforms images into code.

Input:

Image file (.png, .jpg, .jpeg)

Output:

Code that recreates the image pixel-by-pixel.

The generated code should draw the image when executed.

---

# 3. Technology Stack

Use **Python**.

Recommended libraries:

Image processing:

* Pillow

GUI:

* Tkinter
  or
* PyQt6
  or
* CustomTkinter (preferred for modern UI)

Optional:

* NumPy (for pixel processing)

---

# 4. Functional Requirements

The tool must:

1. Allow user to **upload an image**
2. Read image dimensions
3. Extract **RGB color values of every pixel**
4. Convert pixel data into code
5. Display generated code
6. Allow exporting the code to a file

---

# 5. Input / Output

Input:

User uploads an image file.

Example:

image.png

Output:

Generated code instructions like:

```
draw_pixel(0,0,(255,0,0))
draw_pixel(1,0,(255,0,0))
draw_pixel(2,0,(255,255,255))
```

Each line represents a pixel.

---

# 6. Supported Code Output Modes

The user should be able to choose different output formats.

Modes:

### Python Drawing Code

Example:

```
canvas.create_rectangle(x,y,x+1,y+1, fill=color)
```

### JavaScript Canvas

Example:

```
ctx.fillStyle = "rgb(255,0,0)"
ctx.fillRect(x,y,1,1)
```

### CSS Pixel Art

Example:

```
box-shadow:
1px 1px red,
2px 1px blue,
3px 1px white;
```

### ASCII Art

Example:

```
@@@
@..
...
```

---

# 7. User Interface Requirements

The application must include a GUI.

UI layout example:

---

Image ? Code Generator

Upload Image Button

[ Browse Image ]

Output Mode:

Dropdown:

* Python
* JavaScript Canvas
* CSS Pixel Art
* ASCII

Buttons:

Generate Code

Preview Image

Export Code

---

Generated Code Window

---

---

# 8. Image Processing Workflow

1. User selects image
2. Program loads image
3. Image may be resized (optional)
4. Program reads pixel values
5. Pixels converted to drawing instructions
6. Code displayed in UI
7. User exports code

Pipeline:

Upload Image
?
Resize Image
?
Read Pixel Data
?
Generate Code
?
Preview
?
Export Code

---

# 9. Performance Optimization

Large images create very large code output.

Add an optional feature:

Resize image before processing.

Example:

Original image:

1920 × 1080

Resize to:

64 × 64

This reduces generated code size.

---

# 10. Additional Features (Optional)

Add the following advanced features if possible:

• Pixel preview
• Live preview rendering
• Code syntax highlighting
• Export as .py / .js / .txt
• Batch image conversion
• Dark mode UI
• Drag and drop image upload

---

# 11. Project Structure

Example structure:

project/

main.py

ui.py

image_processor.py

code_generator.py

preview_renderer.py

requirements.txt

---

# 12. Code Quality Requirements

The generated project must:

• be modular
• include comments
• follow clean architecture
• separate UI from logic
• include error handling

---

# 13. Output Required

Generate:

1. Full Python source code
2. Project folder structure
3. requirements.txt
4. Instructions to run the tool
5. Example generated output

---

# 14. Expected Result

After running the program:

User uploads an image.

The tool converts the image into code that redraws the image pixel-by-pixel.
