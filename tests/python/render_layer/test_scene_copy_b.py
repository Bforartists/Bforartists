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

class UnitTesting(RenderLayerTesting):
    def test_scene_collections_link(self):
        """
        See if scene copying 'LINK_OBJECTS' is working for scene collections
        """
        import os
        ROOT = self.get_root()

        # note: nothing should change, so using `layers_simple.json`
        filepath_layers_json_copy = os.path.join(ROOT, 'layers_simple.json')
        self.do_scene_copy(
                filepath_layers_json_copy,
                'LINK_OBJECTS',
                (get_scene_collections,))


# ############################################################
# Main - Same For All Render Layer Tests
# ############################################################

if __name__ == '__main__':
    import sys

    extra_arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    sys.argv = [__file__] + (sys.argv[sys.argv.index("--") + 2:] if "--" in sys.argv else [])

    UnitTesting._extra_arguments = extra_arguments
    unittest.main()
