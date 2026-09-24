## 3.3.102 — Blender 4.2 compatibility fork

This is the first release of the independently maintained BRIAGE-Fork.

Based on the original BRIAGE 3.3.101 release.

### Blender 4.2 compatibility

- Replaced the legacy mesh auto-smoothing setup in `IGSI.py` with the
  current Blender mesh smoothing approach.
- Added `BLENDER_EEVEE_NEXT` to the supported material engines.
- Added handling for custom-normal and vertex-count mismatches.

### IGS import fixes

- Reworked BMesh quad reconstruction to use a batch
  `bmesh.ops.dissolve_edges()` operation, avoiding invalidated BMesh
  references during topology changes.
- Fixed stale node-group references in the material library import cache.

### Improvements

- Added IGS export options to the file-save dialog.
- `Trim animation` is enabled by default.

### Compatibility

- Tested with Blender 4.2.x.
- This release is not currently claimed to support other Blender versions.