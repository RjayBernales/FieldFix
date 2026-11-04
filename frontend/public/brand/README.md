# FieldFix brand assets

- `fieldfix-logo-v1.png`: approved horizontal logo, 2172 × 724 pixels. The supplied PNG is preserved unchanged.
- `fieldfix-mark-v1.png`: matching symbol-only favicon, 1254 × 1254 pixels, prepared from the approved logo with the built-in image-generation tool.

Both files are transparent RGBA PNGs. They are raster assets, not SVG files. Use them on the application's white or pale surfaces, keep their natural aspect ratios, and retain the built-in clear space. Do not stretch, apply filters, or put the dark wordmark on a dark background.

The shared `Brand` component in `frontend/src/main.tsx` provides the home link, image alternative text, intrinsic dimensions, and consistent responsive sizing. The horizontal logo is used in the dashboard header and demo entry screen; the symbol is referenced by `frontend/index.html` for browser tabs. Keep the original assets available when adding future versions.
