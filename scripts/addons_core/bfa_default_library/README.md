# BFA Central Asset Library System

## Overview

This addon implements a central asset library system that allows multiple Bforartists based library addons to share a single, unified asset library in Blender/Bforartists' user preferences, preventing duplication and providing smart management and modular installation through various addons.

## Key Features

### 🎯 For Users
- **Single Library Registration**: One "BFA Central Asset Library" instead of multiple duplicates
- **Automatic Management**: Assets are automatically copied and tracked
- **Smart Cleanup**: Central library is cleaned up when the last addon is uninstalled

### 🛠️ For Developers
- **Easy Integration**: Simple API for other addons to use the central system
- **Conflict Avoidance**: Multiple addons can coexist without issues
- **Comprehensive Tracking**: Detailed tracking of which addons contribute which files

## File Structure

```
bfa_central_asset_library/                  # Central library location (auto-created)
├── Default Library/                        # Assets from various addons
├── Geometry Nodes Library/
├── Shader Nodes Library/
├── Compositor Nodes Library/
├── .addon_tracking.json                   # JSON tracking of active addons & files
└── child_addon_tracking.json              # Tracks parent addons using child functionality

bfa_default_library/                       # Parent addon package
├── __init__.py                            # Main addon entry, library management
├── ui.py                                  # Preferences panel & UI operators
├── utility.py                             # Central library management core
├── child_addon/                           # Child addon (functional components)
│   ├── __init__.py
│   ├── operators/                         # Node operators (geometry, shader, compositor)
│   ├── panels.py                          # UI panels
│   ├── wizards.py                         # Asset wizards
│   ├── wizard_handlers.py
│   └── wizard_operators.py
├── Default Library/                       # Original assets (copied to central)
├── Geometry Nodes Library/
├── Shader Nodes Library/
├── Compositor Nodes Library/
└── tests/                                # Comprehensive test suite
```

## Architecture

The addon uses a **parent/child architecture**:

- **Parent Addon** (`__init__.py`, `ui.py`, `utility.py`): Manages asset libraries, registration, and preferences
- **Child Addon** (`child_addon/`): Contains functional components (operators, panels, wizards) that are loaded dynamically

This separation allows multiple parent addons to share the same child functionality without conflicts.

## Benefits

- 🧹 **Clean User Experience**: Single library interface
- 🔧 **Flexible Management**: Independent addon installation/removal
- 🤖 **Automatic Cleanup**: Smart removal of unused assets
- 🔍 **Transparent Operation**: Detailed tracking and debug output built in

## Implementation Summary

## How It Works

### Registration Process
1. **Asset Copying**: Addon copies its assets to central location on registration
2. **File Tracking**: System tracks exactly which files each addon contributes
3. **Library Registration**: Central library is registered in preferences
4. **Single Instance**: Only one library appears in user preferences

### Unregistration Process
1. **Tracking Removal**: Addon removes itself from tracking file
2. **Smart File Cleanup**: Files used only by this addon are removed
3. **Catalog Preservation**: Catalog files are kept to maintain structure
4. **Library Cleanup**: Entire central library removed when 0 addons remain

## Configuration

Edit these variables in `__init__.py` for each addon instance:

```python
# CONFIGURATION - Edit these for each addon instance
ADDON_UNIQUE_ID = "your_addon_name_1_0_0"    # MUST BE UNIQUE
ADDON_DISPLAY_NAME = "Your Addon Name"       # Display name
ADDON_VERSION = (1, 0, 0)                    # Version tuple

# Only include libraries that exist in your packaged addon
CENTRAL_LIB_SUBFOLDERS = ["Your Addon Sub Folders"]  # Your libraries here
```

## Usage for Other Addons

To integrate another addon with the central system:

1. **Copy the addon**: to a new folder
2. **Configure uniquely**: Set unique ID and library folders
3. **Make the extension**: to pack and ship

## Testing

Run the comprehensive test suite:

```bash
cd tests
python test_central_library.py      # Multi-addon scenarios
python test_file_copying.py         # File operations
python test_actual_structure.py     # Real path testing
```

## Debugging & Troubleshooting

### Common Issues

**Registration fails with "bl_info not defined"**
```python
# Use this safe access pattern:
import sys
current_module = sys.modules[__name__]
addon_info = getattr(current_module, 'bl_info', None)
```

**Assets not copying**
- Check source directories exist
- Make sure you have read/write access to the user folder or where you registered the addon
- Verify central library path resolution
- Enable debug output in console

**Library not appearing in preferences**
- Check `bpy.context.preferences` availability
- Verify timer/load_post registration

### Debug Output
Uncomment print statements, with debugging built in.

Abnd/or add these to track registration:
```python
def register():
    print("=== Registration Started ===")
    # Your code
    print("=== Registration Completed ===")
```


### Emergency Recovery

If registration fails completely:
1. Remove addon from Blender/Bforartists
2. Delete `../bfa_central_asset_library/` directory
3. Reinstall addon



## Technical Notes

- Central library location: `../bfa_central_asset_library/` relative to addons folder
- File tracking: JSON-based with detailed file-level tracking
- Supported files: `.blend`, `.blend?`, `blender_assets.cats.txt`
- Catalog files are preserved to maintain category structure
- Empty directories are automatically cleaned up

