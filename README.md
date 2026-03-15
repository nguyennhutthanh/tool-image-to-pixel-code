# Image → Pixel Code Generator

Công cụ desktop chuyển đổi ảnh bất kỳ thành **code pixel art** với nhiều ngôn ngữ/định dạng khác nhau. Hỗ trợ preview trực quan, xử lý ảnh nâng cao, batch conversion và CLI mode.

---

## Tính năng

### Upload ảnh
- **Browse** — chọn file từ máy
- **Drag & Drop** — kéo thả ảnh vào cửa sổ app
- **Paste (Ctrl+V)** — dán ảnh thẳng từ clipboard

### Xử lý ảnh
| Tùy chọn | Mô tả |
|----------|-------|
| Resize | Thay đổi kích thước trước khi xử lý (mặc định 64×64) |
| Grayscale | Chuyển ảnh sang đen trắng |
| Edge Detection | Phát hiện cạnh (viền đối tượng) |
| Color Quantize | Giảm số màu xuống N màu (tiết kiệm code) |
| Dithering | Floyd-Steinberg dithering khi quantize |

### 9 Output Modes
| Mode | File | Mô tả |
|------|------|-------|
| **Python** | `.py` | Tkinter Canvas — chạy được ngay |
| **JavaScript Canvas** | `.js` | HTML5 Canvas — nhúng vào web |
| **CSS Pixel Art** | `.css` | `box-shadow` pixel art |
| **ASCII Art** | `.txt` | Ảnh bằng ký tự ASCII |
| **SVG** | `.svg` | Vector `<rect>` — scale vô hạn không vỡ |
| **Pygame** | `.py` | Standalone Pygame script |
| **Unity C#** | `.cs` | `Texture2D.SetPixel()` — dùng trong Unity |
| **p5.js** | `.js` | Processing / p5.js sketch |
| **Minecraft** | `.txt` | `/setblock` commands — pixel art trong Minecraft |

### Preview nâng cao (tab Preview)
- **Zoom slider** (1×–24×) + scroll chuột để zoom
- **Grid overlay** — bật lưới khi zoom ≥ 4×
- **Hover info** — di chuột → hiện tọa độ `(x, y)`, `RGB(r,g,b)`, `#hex`
- **Save PNG** — lưu preview ra file ảnh

### Tab Compare
So sánh ảnh gốc và ảnh sau xử lý cạnh nhau.

### Tab Stats
- Tổng số pixel, số màu unique
- Ước tính kích thước code
- Bảng màu (top 64 màu) với % sử dụng

### Tab Batch
- Thêm nhiều file cùng lúc
- Chọn output folder
- Chạy batch với cùng cài đặt, xem log kết quả từng file

### CLI Mode
Chạy không cần giao diện đồ họa:
```bash
python main.py <input_image> [options]
```

---

## Cài đặt

### Yêu cầu
- Python **3.10+**

### Bước 1 — Clone hoặc tải về
```bash
git clone <repo-url>
cd tool-image_to_pixel_code
```

### Bước 2 — Cài thư viện
```bash
pip install -r requirements.txt
```

Các thư viện cần thiết:
```
customtkinter>=5.2.0   # Giao diện hiện đại
Pillow>=10.0.0         # Xử lý ảnh
tkinterdnd2>=0.3.0     # Drag & Drop support
```

---

## Cách chạy

### GUI Mode (giao diện đồ họa)
```bash
python main.py
```

### CLI Mode (dòng lệnh)
```bash
# Cơ bản
python main.py anh.png

# Chọn mode và kích thước
python main.py anh.png --mode SVG --width 64 --height 64 --output out.svg

# Quantize màu + dithering
python main.py anh.png --mode Python --colors 16 --dither --output pixel.py

# Grayscale + edge detection
python main.py anh.png --mode ASCII Art --grayscale --edges

# Không resize
python main.py anh.png --mode Pygame --no-resize --output game.py
```

#### Tất cả CLI options:
```
positional:
  input                   File ảnh đầu vào

optional:
  --mode, -m MODE         Output mode (mặc định: Python)
                          Choices: Python | JavaScript Canvas | CSS Pixel Art |
                                   ASCII Art | SVG | Pygame | Unity C# | p5.js | Minecraft
  --width,  -W N          Resize width  (mặc định: 64)
  --height, -H N          Resize height (mặc định: 64)
  --no-resize             Bỏ qua bước resize
  --colors, -c N          Quantize xuống N màu (0 = tắt)
  --dither                Dùng Floyd-Steinberg dithering (cần --colors)
  --grayscale, -g         Chuyển sang grayscale
  --edges, -e             Áp dụng edge detection
  --output, -o FILE       Lưu ra file (mặc định: in ra stdout)
```

---

## Cấu trúc dự án

```
tool-image_to_pixel_code/
├── main.py               # Entry point — GUI + CLI
├── ui.py                 # Giao diện chính (App + PixelCanvas)
├── image_processor.py    # Load, resize, grayscale, edge, quantize
├── code_generator.py     # 9 output mode generators
├── preview_renderer.py   # Preview popup window
├── requirements.txt      # Dependencies
└── README.md
```

---

## Ví dụ output

### SVG (64×64)
```xml
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" shape-rendering="crispEdges">
  <rect x="0" y="0" width="1" height="1" fill="#1a2b3c"/>
  ...
</svg>
```

### Minecraft
```
/setblock 0 64 0 minecraft:white_concrete
/setblock 1 64 0 minecraft:light_blue_concrete
...
```

### Unity C#
```csharp
Texture2D tex = new Texture2D(64, 64);
tex.SetPixel(0, 63, new Color(0.1f, 0.17f, 0.24f));
...
tex.Apply();
GetComponent<Renderer>().material.mainTexture = tex;
```

---

## License

MIT License — free to use and modify.
