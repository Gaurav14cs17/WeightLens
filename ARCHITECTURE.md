# WeightLens — Architecture Guide

## Project Layout

```
WeightLens_new/
├── serve.py                  # Dev server (no-cache, port 8080, serves from src/)
├── README.md                 # Quick start & feature list
├── ARCHITECTURE.md           # This file — code map for developers
├── models/                   # Sample ONNX models for testing
│   ├── model_fp32.onnx
│   ├── model_fp32.onnx.data
│   ├── model_int8.onnx
│   └── model_int8.onnx.data
└── src/                      # Application source (served at http://localhost:8080)
    ├── index.html            # Entry point, welcome UI, CSS, theme toggle (716 lines)
    ├── index.js              # Module loader + path resolver
    │
    ├── core/                 # ★ WeightLens application code (9 files)
    │   ├── compare.js        # Comparison engine (charts, stats, navigation)
    │   ├── compare.css       # Comparison sidebar styles
    │   ├── view.js           # Graph view + sidebar + node interaction
    │   ├── app.js            # Electron app lifecycle (desktop only)
    │   ├── browser.js        # Browser environment + module resolver
    │   ├── grapher.js        # SVG graph renderer (nodes, edges)
    │   ├── grapher.css       # Graph node styling
    │   ├── message.js        # Message/notification system
    │   └── worker.js         # Web worker for dagre layout
    │
    ├── lib/                  # Shared libraries & utilities (18 files)
    │   ├── dagre.js          # Directed graph layout algorithm
    │   ├── base.js           # Binary streams, readers, telemetry
    │   ├── protobuf.js       # Protobuf decoder
    │   ├── flatbuffers.js    # FlatBuffers decoder
    │   ├── flexbuffers.js    # FlexBuffers decoder
    │   ├── json.js           # JSON parser
    │   ├── xml.js            # XML parser
    │   ├── zip.js            # ZIP archive handler
    │   ├── tar.js            # TAR archive handler
    │   ├── python.js         # Python execution engine + pickle
    │   ├── pickle.js         # Pickle format handler
    │   ├── numpy.js          # NumPy format handler
    │   ├── hdf5.js           # HDF5 format handler
    │   ├── text.js           # Text file utilities
    │   ├── dot.js            # DOT graph format parser
    │   ├── safetensors.js    # SafeTensors format handler
    │   ├── flax.js           # Flax/JAX format handler
    │   └── node.js           # Node.js file stream (desktop only)
    │
    ├── parsers/              # Model format parsers (147 files, rarely modified)
    │   ├── onnx.js           # ONNX parser
    │   ├── onnx-proto.js     # ONNX protobuf schema
    │   ├── onnx-metadata.json
    │   ├── pytorch.js        # PyTorch parser
    │   ├── pytorch-metadata.json
    │   ├── tf.js             # TensorFlow parser
    │   ├── tflite.js         # TFLite parser
    │   ├── keras.js, coreml.js, caffe.js, paddle.js, ...
    │   └── (100+ format parsers and metadata JSON files)
    │
    ├── assets/               # Static assets
    │   ├── favicon.ico
    │   ├── icon.png
    │   └── desktop.mjs       # Electron preload script
    │
    └── test_models/          # Demo models for welcome page
        ├── model_fp32.onnx
        ├── model_fp32.onnx.data
        ├── model_int8.onnx
        └── model_int8.onnx.data
```

## Key Files for Feature Development

| File | Purpose | When to Edit |
|------|---------|--------------|
| `src/core/compare.js` | Comparison logic, charts, navigation, grouping, health scores | Adding metrics, charts, comparison types |
| `src/index.html` | Welcome page, CSS themes, page layout | Changing UI, adding pages, theme colors |
| `src/core/view.js` | Graph rendering, sidebar, node click handling | Sidebar changes, node interactions |
| `src/index.js` | Module resolver (maps names → folders) | Adding new modules |
| `src/core/browser.js` | Browser host, file loading, asset resolution | Changing how files/models are loaded |
| `src/core/grapher.js` | Low-level SVG node/edge rendering | Changing graph node appearance |

## How It Works

### Module System

`index.js` defines `window.exports._resolve(id)` which maps module names to folder paths:
- Core modules (`compare`, `view`, `app`, `browser`, `grapher`, `message`, `worker`) → `core/`
- Library modules (`dagre`, `base`, `protobuf`, `flatbuffers`, `flexbuffers`, `json`, `xml`, `zip`, `tar`, `python`, `pickle`, `numpy`, `hdf5`, `text`, `dot`, `safetensors`, `flax`, `node`) → `lib/`
- Everything else → `parsers/`

**Adding a new module:**
1. Put the file in the correct folder (`core/`, `lib/`, or `parsers/`)
2. If it's a core or lib module, add its name to the corresponding array in `_resolve()` in `index.js`
3. Use `import * as X from '../lib/X.js'` or `'../parsers/X.js'` for cross-directory imports

### Import Conventions

- **Within the same directory:** `import * as X from './X.js'`
- **From core → lib:** `import * as X from '../lib/X.js'`
- **From parsers → lib:** `import * as X from '../lib/X.js'`
- **Dynamic imports in core:** `await import('../lib/X.js')` or `await import('../parsers/X.js')`
- **Browser.Host.require(id):** Strips `./` prefix, uses `_resolve()`, loads via `import()`
- **Asset loading (JSON metadata):** `browser.Host.asset(file)` prefixes with `parsers/`

### Boot Sequence

1. Browser loads `index.html` → `index.js` (sets up module system)
2. `index.html` loads `core/compare.js` (comparison controller)
3. `window.load` fires → `preload()` loads modules in batches:
   - Batch 1: `base`, `text`, `flatbuffers`, `flexbuffers`, `zip`, `tar`, `python`
   - Batch 2: `json`, `xml`, `protobuf`, `hdf5`, `grapher`, `browser`
   - Batch 3: `view`
4. After preload: creates `browser.Host` → `view.View` → `.start()`
5. View shows welcome page; user picks comparison type or loads model

### Comparison Flow

1. User selects type (Quantization/Pruning/etc.) → uploads models or clicks Demo
2. `compare.Controller` extracts weights from all models
3. `_groupMatchedLayers()` → groups weight+bias by parent layer
4. `_sortLayersByGraphOrder()` → reorders to match DAG execution order
5. `_computeAllHealthScores()` → quality metrics per layer
6. `_applyGraphOverlays()` → health badges on graph nodes
7. `CompareSidebar` (view.js) renders navigation + charts

### Adding a New Comparison Type

1. Add entry to `compare.COMPARE_TYPES` in `core/compare.js`
2. Add `loadDemo<Type>()` method with synthetic data
3. Add type-specific charts in `_renderSingleTensorComparison()`
4. Add card to welcome page in `index.html`

### Adding a New Chart

1. Create `_createMyChart(variants, labels, w, h)` → returns SVG string
2. Add tab button in `_renderSingleTensorComparison()`
3. Wire tab click to render your chart

### Theming

- Dark: CSS variables in `:root` (index.html line 13)
- Light: CSS variables in `html.light` (index.html line 15)
- Toggle: `.wl-theme-pill` button in top-right corner

### Graph Highlighting

- **Health badges** (permanent): `_addNodeOverlay()` → green/orange/red circles on nodes
- **Selection ring** (current layer): `_applyCurrentNodeHighlight()` → dashed blue border

## Server

```bash
python3 serve.py   # Serves src/ at http://localhost:8080 with no-cache headers
```

The server uses `SimpleHTTPRequestHandler` with `Cache-Control: no-store` for development. It `chdir`s into `src/` so all URL paths map directly to the file system.
