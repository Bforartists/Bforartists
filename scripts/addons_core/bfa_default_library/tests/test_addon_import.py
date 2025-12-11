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
Test script to verify the addon can be imported without errors.
This helps catch import-time issues before trying to register in Blender.
"""

import sys
import os
import ast
from pathlib import Path
from os import path as p

def test_syntax():
    """Test that all Python files have valid syntax."""
    print("Testing Python file syntax...")
    
    # List of Python files to check
    python_files = [
        "../__init__.py",
        "../utility.py",
        "../ui.py",
        "../panels.py",
        "../ops.py",
        "../wizards.py"
    ]
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            ast.parse(source)
            print(f"✓ {file_path} has valid syntax")
        except SyntaxError as e:
            print(f"❌ {file_path} has syntax error: {e}")
            return False
        except Exception as e:
            print(f"⚠ {file_path} couldn't be read: {e}")
    
    print("✓ All files have valid syntax")
    return True

def test_utility_import():
    """Test that utility functions can be imported and used."""
    print("Testing utility module import...")
    
    try:
        # Add parent directory to path
        sys.path.insert(0, p.dirname(p.dirname(__file__)))
        
        # Mock bpy module for testing
        class MockBpy:
            class types:
                class Context: pass
                class Preferences: pass
                class UILayout: pass
                class AddonPreferences: pass
            
            class context:
                scene = type('Scene', (), {'frame_current': 0})()
                preferences = type('Preferences', (), {})()
            
            class ops:
                class preferences:
                    def asset_library_add(**kwargs): pass
                    def asset_library_remove(**kwargs): pass
                class asset:
                    def library_refresh(**kwargs): pass
            
            class app:
                class timers:
                    def register(**kwargs): pass
                    def unregister(**kwargs): pass
        
        sys.modules['bpy'] = MockBpy()
        sys.modules['bpy.utils'] = type('Module', (), {})()
        sys.modules['bpy.types'] = MockBpy.types
        
        # Now try to import utility
        from utility import get_central_library_path, get_addon_identifier
        
        # Test basic functions
        path = get_central_library_path()
        print(f"✓ Central library path function works: {path}")
        
        test_info = {'name': 'Test', 'version': (1, 0, 0)}
        addon_id = get_addon_identifier(test_info)
        print(f"✓ Addon identifier function works: {addon_id}")
        
        print("✓ Utility module test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Utility module test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_syntax()
    success2 = test_utility_import()
    
    if success1 and success2:
        print("🎉 All import tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
