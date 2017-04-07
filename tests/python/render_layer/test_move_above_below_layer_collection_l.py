# ############################################################
# Importing - Same For All Render Layer Tests
# ############################################################

import unittest
import os
import sys

from render_layer_common import *


# ############################################################
# Testing
# ############################################################

class UnitTesting(MoveLayerCollectionTesting):
    def get_reference_scene_tree_map(self):
        # original tree, no changes
        return self.get_initial_scene_tree_map()

    def get_reference_layers_tree_map(self):
        reference_layers_map = [
                ['Layer 1', [
                    'Master Collection',
                    'C',
                    '3',
                    ]],
                ['Layer 2', [
                    'C',
                    'cat',
                    '3',
                    'dog',
                    ]],
                ]
        return reference_layers_map

    def test_layer_collection_move_a(self):
        """
        Test outliner operations
        """
        self.setup_tree()
        self.assertTrue(self.move_below('Layer 2.cat', 'Layer 2.C'))
        self.compare_tree_maps()

    def test_layer_collection_move_b(self):
        """
        Test outliner operations
        """
        self.setup_tree()
        self.assertTrue(self.move_above('Layer 2.cat', 'Layer 2.3'))
        self.compare_tree_maps()


# ############################################################
# Main - Same For All Render Layer Tests
# ############################################################

if __name__ == '__main__':
    import sys

    extra_arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    sys.argv = [__file__] + (sys.argv[sys.argv.index("--") + 2:] if "--" in sys.argv else [])

    UnitTesting._extra_arguments = extra_arguments
    unittest.main()
