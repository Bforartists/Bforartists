# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""
Test script to verify file copying functionality.
This tests the actual file operations that should happen during registration.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from os import path as p

# Add the parent directory to the path so we can import the utility module
sys.path.insert(0, p.dirname(p.dirname(__file__)))

from utility import add_addon_to_central_library

def test_file_copying():
    """Test that files are properly copied from addon to central library."""
    print("Testing file copying functionality...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test central library
        test_central_path = p.join(temp_dir, "central_test")
        
        # Create mock addon structure
        addon_path = p.join(temp_dir, "mock_addon")
        
        # Create library directories with blend files
        library_dirs = ['Default Library', 'Geometry Nodes Library']
        
        for lib_dir in library_dirs:
            lib_path = p.join(addon_path, lib_dir)
            os.makedirs(lib_path, exist_ok=True)
            
            # Create mock blend file
            blend_file = p.join(lib_path, f"{lib_dir.replace(' ', '_')}.blend")
            with open(blend_file, 'w') as f:
                f.write(f"# Mock blend file for {lib_dir}")
            
            # Create catalog file
            catalog_file = p.join(lib_path, "blender_assets.cats.txt")
            with open(catalog_file, 'w') as f:
                f.write(f"# Catalog for {lib_dir}")
            
            print(f"Created mock files in: {lib_path}")
        
        # Test addon info
        test_addon_info = {
            'name': 'Test Asset Library',
            'version': (1, 0, 0)
        }
        
        # Copy to central library
        central_path = add_addon_to_central_library(
            test_addon_info, library_dirs, addon_path, test_central_path
        )
        
        # Verify files were copied
        all_files_copied = True
        for lib_dir in library_dirs:
            central_lib_path = p.join(central_path, lib_dir)
            
            # Check blend file
            expected_blend = p.join(central_lib_path, f"{lib_dir.replace(' ', '_')}.blend")
            if not p.exists(expected_blend):
                print(f"❌ Blend file not copied: {expected_blend}")
                all_files_copied = False
            else:
                print(f"✓ Blend file copied: {expected_blend}")
            
            # Check catalog file
            expected_catalog = p.join(central_lib_path, "blender_assets.cats.txt")
            if not p.exists(expected_catalog):
                print(f"❌ Catalog file not copied: {expected_catalog}")
                all_files_copied = False
            else:
                print(f"✓ Catalog file copied: {expected_catalog}")
        
        # Verify central directory structure
        if p.exists(test_central_path):
            print(f"✓ Central library directory created: {test_central_path}")
            
            # List contents
            items = os.listdir(test_central_path)
            print(f"Central library contents: {items}")
            
            # Check tracking file
            tracking_file = p.join(test_central_path, ".addon_tracking.json")
            if p.exists(tracking_file):
                print(f"✓ Tracking file created: {tracking_file}")
            else:
                print(f"❌ Tracking file missing: {tracking_file}")
                all_files_copied = False
        else:
            print(f"❌ Central library directory not created: {test_central_path}")
            all_files_copied = False
        
        if all_files_copied:
            print("🎉 All files copied successfully!")
            return True
        else:
            print("❌ Some files failed to copy!")
            return False

if __name__ == "__main__":
    success = test_file_copying()
    sys.exit(0 if success else 1)
