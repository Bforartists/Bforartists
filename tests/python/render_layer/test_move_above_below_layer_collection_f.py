# ./blender.bin --background -noaudio --python tests/python/render_layer/test_link.py -- --testdir="/data/lib/tests/"

# ############################################################
# Importing - Same For All Render Layer Tests
# ############################################################

import unittest

import os, sys
sys.path.append(os.path.dirname(__file__))

from render_layer_common import *


# ############################################################
# Testing
# ############################################################

class UnitTesting(MoveLayerCollectionTesting):
    def get_reference_scene_tree_map(self):
        reference_tree_map = [
                ['A', [
                    ['i', None],
                    ['ii', None],
                    ['iii', None],
                    ]],
                ['B', None],
                ['C', [
                    ['1', None],
                    ['3', [
                        ['dog', None],
                        ['cat', None],
                        ]],
                    ['2', None],
                    ]],
                ]
        return reference_tree_map

    def get_reference_layers_tree_map(self):
        reference_layers_map = [
                ['Layer 1', [
                    'Master Collection',
                    'C',
                    '3',
                    ]],
                ['Layer 2', [
                    'C',
                    'dog',
                    'cat',
                    ]],
                ]
        return reference_layers_map

    def test_layer_collection_move_a(self):
        """
        Test outliner operations
        """
        self.setup_tree()
        self.assertTrue(self.move_below('Layer 2.3', 'Layer 2.C.1'))
        self.compare_tree_maps()

    def test_layer_collection_move_b(self):
        """
        Test outliner operations
        """
        self.setup_tree()
        self.assertTrue(self.move_above('Layer 2.3', 'Layer 2.C.2'))
        self.compare_tree_maps()

    def test_layer_collection_move_c(self):
        """
        Test outliner operations
        """
        self.setup_tree()

        # collection that will be moved
        collection_original = self.parse_move('Layer 2.3')
        collection_original.hide = False
        collection_original.hide_select = True

        # collection that will disappear
        collection_old = self.parse_move('Layer 2.C.3')
        collection_old.hide = True
        collection_old.hide_select = False

        # move
        self.assertTrue(self.move_below('Layer 2.3', 'Layer 2.C.1'))
        self.compare_tree_maps()

        # we expect the settings to be carried along from the
        # original layer collection
        collection_new = self.parse_move('Layer 2.C.3')
        self.assertEqual(collection_new.hide, False)
        self.assertEqual(collection_new.hide_select, True)


# ############################################################
# Main - Same For All Render Layer Tests
# ############################################################

if __name__ == '__main__':
    import sys

    extra_arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    sys.argv = [__file__] + (sys.argv[sys.argv.index("--") + 2:] if "--" in sys.argv else [])

    UnitTesting._extra_arguments = extra_arguments
    unittest.main()
