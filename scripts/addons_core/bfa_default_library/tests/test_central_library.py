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
Test script for Default Library functionality.
This script can be run to verify the central library system works correctly.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from os import path as p

# Add the parent directory to the path so we can import the utility module
sys.path.insert(0, p.dirname(p.dirname(__file__)))

from utility import (
    get_central_library_path,
    read_addon_tracking,
    write_addon_tracking,
    add_addon_to_central_library,
    remove_addon_from_central_library,
    get_active_addons_count,
    cleanup_central_library,
    get_addon_identifier
)


def test_basic_functionality():
    """Test basic central library functionality with isolated temp directories."""
    print("Testing Default Library basic functionality...")
    
    # Test 1: Simple add and remove
    with tempfile.TemporaryDirectory() as temp_dir:
        test_central_path = p.join(temp_dir, "test_central_lib")
        
        test_addon_info = {'name': 'Test Addon', 'version': (1, 0, 0)}
        test_addon_path = temp_dir
        test_libraries = ['Test Library']
        
        # Create test files
        test_lib_dir = p.join(test_addon_path, 'Test Library')
        os.makedirs(test_lib_dir, exist_ok=True)
        
        with open(p.join(test_lib_dir, 'test.blend'), 'w') as f:
            f.write("# Test blend file")
        with open(p.join(test_lib_dir, 'blender_assets.cats.txt'), 'w') as f:
            f.write("# Test catalog")
        
        # Add to central library
        central_path = add_addon_to_central_library(
            test_addon_info, test_libraries, test_addon_path, test_central_path
        )

        # Check tracking
        tracking = read_addon_tracking(test_central_path)
        addon_id = get_addon_identifier(test_addon_info)
        assert addon_id in tracking
        assert tracking[addon_id]['name'] == 'Test Addon'
        print("✓ Addon successfully added to central library")

        # Check files copied
        assert p.exists(p.join(test_central_path, 'Test Library', 'test.blend'))
        assert p.exists(p.join(test_central_path, 'Test Library', 'blender_assets.cats.txt'))
        print("✓ Files successfully copied")

        # Check count
        count = get_active_addons_count(test_central_path)
        assert count == 1
        print(f"✓ Active addons count: {count}")

        # Remove addon
        remove_addon_from_central_library(test_addon_info, test_central_path)

        # Check removed
        tracking_after = read_addon_tracking(test_central_path)
        assert addon_id not in tracking_after
        print("✓ Addon successfully removed")

        # Cleanup
        cleanup_central_library(test_central_path)
        final_count = get_active_addons_count(test_central_path)
        assert final_count == 0
        print("✓ Cleanup successful")

    print("🎉 Basic functionality test passed!")


def test_multiple_addons():
    """Test multiple addons in separate central libraries."""
    print("\nTesting multiple addons...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        central_path_1 = p.join(temp_dir, "central_1")
        central_path_2 = p.join(temp_dir, "central_2")
        
        # Addon 1
        addon1_info = {'name': 'Addon One', 'version': (1, 0, 0)}
        addon1_path = p.join(temp_dir, 'addon1')
        os.makedirs(p.join(addon1_path, 'Library1'), exist_ok=True)

        with open(p.join(addon1_path, 'Library1', 'asset1.blend'), 'w') as f:
            f.write("# Addon One asset")

        add_addon_to_central_library(addon1_info, ['Library1'], addon1_path, central_path_1)

        # Addon 2
        addon2_info = {'name': 'Addon Two', 'version': (2, 0, 0)}
        addon2_path = p.join(temp_dir, 'addon2')
        os.makedirs(p.join(addon2_path, 'Library2'), exist_ok=True)

        with open(p.join(addon2_path, 'Library2', 'asset2.blend'), 'w') as f:
            f.write("# Addon Two asset")

        add_addon_to_central_library(addon2_info, ['Library2'], addon2_path, central_path_2)

        # Check they're isolated
        count1 = get_active_addons_count(central_path_1)
        count2 = get_active_addons_count(central_path_2)

        assert count1 == 1, f"Expected 1 addon in central_path_1, got {count1}"
        assert count2 == 1, f"Expected 1 addon in central_path_2, got {count2}"

        print("✓ Multiple addons work in isolation")

        # Remove addon 1
        remove_addon_from_central_library(addon1_info, central_path_1)
        count1_after = get_active_addons_count(central_path_1)
        assert count1_after == 0, f"Expected 0 addons after removal, got {count1_after}"

        # Addon 2 should still be there
        count2_after = get_active_addons_count(central_path_2)
        assert count2_after == 1, f"Expected addon 2 to remain, count: {count2_after}"

        print("✓ Addon removal works correctly")
    
    print("🎉 Multiple addons test passed!")


if __name__ == "__main__":
    test_basic_functionality()
    test_multiple_addons()
    
    print("\n" + "="*50)
    print("All central library tests completed successfully!")
    print("The system is ready for use with multiple BFA library addons.")
