# Blender Copilot Instructions

This codebase is **Bforartists** (a Blender fork), a large-scale 3D graphics application written in C/C++ with Python bindings for the interface and user API.

## Architecture Overview

### Core Layer Structure
- **`source/blender/makesdna/`** - Data structure definitions (DNA) that define Blender's serializable file format
  - All `DNA_*.h` files define core data structures persisted in `.blend` files
  - Changes to DNA require version bumping and forward compatibility handling
- **`source/blender/blenkernel/`** - Core kernel functions operating on DNA data structures
- **`source/blender/blenlib/`** - Low-level utility library (math, memory, data structures)
- **`source/blender/editors/`** - User interface and editor code
- **`source/blender/windowmanager/`** - Event handling and window management
- **`source/blender/modifiers/`** - Procedural modifiers (deform, generate, etc.)
- **`source/blender/render/`** - Rendering engine (Cycles, Eevee, Hydra backends)
- **`source/blender/python/`** - Python API (RNA) bindings to expose C code
- **`source/blender/nodes/`** - Node system for shaders, geometry, compositing
- **`source/blender/compositor/`** - Compositing pipeline
- **`source/blender/depsgraph/`** - Dependency graph for scheduling computation

### Build System
- **CMake-based** - Primary build tool (not Make or Scons)
- **Out-of-source builds required** - Never build in source directory; creates parallel `build_*` directories
- **Convenience targets via GNUmakefile** - `make debug`, `make release`, `make ninja`, `make full`, `make lite`
- **Library organization** - Precompiled libs in `lib/{platform}_{arch}/`, e.g., `lib/windows_x64/`

## Developer Notes (Bforartists-Specific)
Bforartists mostly modifies interface code and uses marker comments to track changes:
```
# BFA           (Python comment)
#bfa            (Python comment, lowercase)
/*bfa*/         (C/C++ comment)
/* bfa*/        (C/C++ comment with space)
```
These comments indicate changes made to the source code. It is important that changes are tracked and updated when syncing with upstream Blender merges.

**When making significant changes**, always add a BFA comment with an explanation of why the change was made. This helps:
- Document the rationale for divergence from upstream Blender
- Enable future developers to understand design decisions
- Facilitate merging and rebasing with upstream Blender updates
- Track change history without external documentation

**UI Checkbox Convention**: Both interface code in Python and C++ must have checkboxes always float left in layout code. This ensures consistent UI alignment across the codebase.

## Key Developer Workflows

### Building Blender
```bash
# Initialize build environment (fetch libraries)
python build_files/utils/make_update.py

# Configure and build (uses GNUmakefile convenience targets)
make                    # Standard build for development
make release            # Standard release build
make debug              # Standard debug build
make ninja              # Fast incremental build
make ninja release      # Fast incremental release build
make ninja debug        # Fast incremental debug build
make release ccache     # Full release with ccache speedup
make full               # All features enabled
make lite               # Minimal build for testing

# Or direct CMake (out-of-source)
mkdir build_linux_x64
cd build_linux_x64
cmake ../
make -j$(nproc)
```

### Code Organization Conventions
- **Module naming** - `BKE_*` (kernel), `BLI_*` (library), `UI_*` (interface), `WM_*` (window manager)
- **Header structure** - Public API in `.h`, internal in `intern/`
- **Source layout** - Each module in `source/blender/{module}/` with `CMakeLists.txt`, `intern/`, and public headers
- **Namespace usage** - C++ code uses `blender::` namespace (see `MOD_ocean.cc` example)

## Critical Patterns and Conventions

### DNA Data Structures (Core Persistence)
- All persistable data defined in `DNA_*.h` files
- Structures are binary-serialized to `.blend` files
- **Backward compatibility required** - Old files must load in newer versions
- When modifying DNA: version bump needed in blend file loader
- Example: `DNA_modifier_types.h` defines `OceanModifierData`

### Modifiers (Common Extension Point)
- Located in `source/blender/modifiers/intern/`
- Standard pattern: `MOD_*.cc` files implement modifier callbacks
- Required callbacks: `init_data()`, `free_data()`, `copy_data()`, `deform_verts_EM()`, `deform_verts()`, `modify_mesh()`
- Conditional compilation with `#ifdef WITH_FEATURE` for optional dependencies
- Example: `MOD_ocean.cc` shows ocean simulation modifier with ocean library integration

### Python API (RNA)
- Auto-generated Python API from C structures
- `RNA_access.hh`, `RNA_prototypes.hh` for C++ side
- Python modules in `scripts/modules/` and `scripts/addons_core/`
- Blender Python API exposed as `bpy` module (C extensions compiled with `pybind11` or custom wrappers)

### Rendering Pipeline
- **Cycles** - GPU/CPU ray tracer (C++, CUDA/HIP/OptiX support in `intern/cycles/`)
- **Eevee** - Real-time rasterizer using OpenGL/Vulkan
- **Hydra** - Open-source renderer abstraction (in `source/blender/render/hydra/`)
- Render engines accessed via `RenderEngine` interface

### Dependency Management
- External libraries vendored in `extern/` (Bullet, Audaspace, OpenVDB, etc.)
- Precompiled libs downloaded to `lib/{platform}_{arch}/` via SVN
- Features behind CMake toggles: `WITH_CYCLES`, `WITH_OCEANSIM`, `WITH_PYTHON`, etc.

## Important File Patterns and Locations

- **Build configuration** - `build_files/cmake/` (macros, platform-specific rules)
- **Test suite** - `tests/` with CMake integration
- **Scripts and tools** - `scripts/` for Python tools, `tools/` for build utilities
- **Data files** - `release/datafiles/` (textures, fonts, startup scripts)
- **License and attribution** - `AUTHORS` (Git-generated contributor list), `COPYING` (GPL-2.0-or-later)

## Code Style and Conventions

- **Header guards** - Use SPDX license identifier in first line: `/* SPDX-License-Identifier: GPL-2.0-or-later */`
- **Python formatting** - `autopep8` configured in `pyproject.toml` with aggressive=2
- **Naming** - Snake_case for functions/variables, PascalCase for types/classes
- **C++ usage** - Mix of C and C++ (C++ preferred in newer code), namespace `blender::` for C++ features
- **Macro names** - ALL_CAPS for compile-time constants, prefixed with module (e.g., `BKE_`, `BLI_`)

## Common Integration Points

- **Depsgraph** - Update scheduling system; modify `depsgraph/` for new dependency types
- **Attribute system** - `BKE_attribute.h` for generic mesh/geometry attributes
- **Task system** - `BLI_task.h` for threading (parallel loops, job scheduling)
- **File I/O** - `blenloader/` handles `.blend` file serialization; format is backward-compatible binary

## Testing and Debugging

- **Unit tests** - `tests/gtests/` (GoogleTest C++ tests)
- **Python tests** - `tests/python/`
- **Debugging** - GDB scripts in `tools/debug/gdb/`
- **Build types** - `Debug`, `Release`, `RelWithDebInfo` via CMake `CMAKE_BUILD_TYPE`

## Platform-Specific Notes

- **Windows** - Prebuilt libraries in `lib/windows_x64/`, uses MSVC
- **macOS** - `lib/macos_arm64/` for Apple Silicon, `lib/macos_x64/` for Intel
- **Linux** - Requires dev packages; build environment setup in `build_files/build_environment/linux/`

## Key References

- **Rendering**: `source/blender/render/`, `intern/cycles/`
- **UI/Viewport**: `source/blender/editors/`, `source/blender/gpu/` (graphics)
- **Geometry**: `source/blender/bmesh/` (mesh primitives), `source/blender/geometry/` (procedural)
- **Animation**: `source/blender/animrig/` (animation system)
- **Compositor**: `source/blender/compositor/` (node-based image processing)

---

For in-depth architecture questions, consult the DNA definitions (`makesdna/DNA_*.h`) and kernel implementations (`blenkernel/`). When working with modifiers, use `MOD_*.cc` files as templates.
