# StickerPipeline System Architecture

This document presents the detailed architectural design and technical specifications of the **StickerPipeline** microservice.

---

## 1. System Components

The microservice consists of four decoupled internal modules:

```
[ FastAPI App (src/main.py) ]
       │
       ├─────► [ Interceptor Router (src/api/interceptor.py) ]
       │              │
       │              ▼
       ├─────► [ Image Engine (src/engine/processor.py) ]
       │              │
       │              ├─────► rembg ONNX Engine (Alpha Extraction)
       │              ├─────► Contour Engine (src/engine/contour.py)
       │              └─────► Sheet Builder (src/engine/sheet.py)
       │
       └─────► [ Storage Manager (NFS Mount: /drives/nfs/stickers) ]
```

### Module Descriptions
- **`src.main`**: FastAPI application entry point, lifecycle hooks, CORS middleware, and route registrations.
- **`src.config`**: Central Pydantic settings loading environment configuration.
- **`src.api.interceptor`**: OpenAI API specification proxy handler. Forwards payloads to upstream LiteLLM endpoints, inspects completion text and prompt metadata, and triggers async processing worker threads.
- **`src.engine.contour`**: Pure OpenCV algorithm executing binary kernel dilation, Gaussian edge smoothing, alpha mask synthesis, and solid background offset construction.
- **`src.engine.processor`**: Coordinates `rembg` session invocation, memory transfers between PIL Images and NumPy matrices, and metadata logging.
- **`src.engine.sheet`**: ReportLab / Pillow high-DPI page composition module placing processed sticker elements onto grid layouts.

---

## 2. Image Processing Algorithm (OpenCV & rembg)

### Background Removal
`rembg` uses the `u2net` ONNX vision network executed via `onnxruntime.InferenceSession`. 
- **Input**: 3-channel RGB or 4-channel RGBA NumPy matrix `(H, W, 3/4)`.
- **Output**: 4-channel RGBA NumPy matrix with extracted alpha channel `(H, W, 4)`.

### Die-Cut Offset Contour Construction
To build a white sticker border:
1. Extract alpha channel mask $A \in [0, 255]^{H \times W}$.
2. Binarize alpha mask: $M_{binary} = (A > 10) \cdot 255$.
3. Compute morphological dilation kernel $K$ of radius $r = \text{border\_offset\_px}$:
   $$K = \text{cv2.getStructuringElement}(\text{cv2.MORPH\_ELLIPSE}, (2r+1, 2r+1))$$
4. Dilate alpha mask:
   $$M_{dilated} = \text{cv2.dilate}(M_{binary}, K)$$
5. Apply Gaussian blur to soften corners:
   $$M_{smooth} = \text{cv2.GaussianBlur}(M_{dilated}, (5, 5), 0)$$
6. Re-threshold to crisp binary edge:
   $$M_{final} = (M_{smooth} > 128) \cdot 255$$
7. Composite: Create a solid white canvas of dimension $(H, W, 3)$ masked by $M_{final}$, overlaying the original transparent subject image in the center.

---

## 3. Storage Hierarchy

The persistent volume is mounted to `/drives/nfs/stickers`:

```
/drives/nfs/stickers/
├── raw/
│   └── 20260726_010000_a1b2c3d4.png
├── processed/
│   ├── 20260726_010000_a1b2c3d4_nobg.png
│   └── 20260726_010000_a1b2c3d4_bordered.png
├── sheets/
│   ├── sheet_20260726_010500.png
│   └── sheet_20260726_010500.pdf
└── metadata/
    └── 20260726_010000_a1b2c3d4.json
```

---

## 4. Semantic Versioning & Release Strategy

The repository strictly enforces **Semantic Versioning (`vMAJOR.MINOR.PATCH`)**:
- **MAJOR**: Breaking API path or pipeline interface changes.
- **MINOR**: New processing algorithms, sheet paper formats, or endpoint additions.
- **PATCH**: Bug fixes, performance optimizations, or documentation updates.

GitHub Actions validates formatting, executes pytest suites on pull requests to `main`, and publishes Docker tags upon git version tag pushes.
