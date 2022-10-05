/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_context.h"

#include "ED_screen.h"
#include "ED_viewer_path.hh"

#include "WM_api.h"

/**
 * Checks if the viewer path stored in the workspace is still active and resets it if not.
 * The viewer path stored in the workspace is the ground truth for other editors, so it should be
 * updated before other editors look at it.
 */
static void validate_viewer_paths(bContext &C, WorkSpace &workspace)
{
  if (BLI_listbase_is_empty(&workspace.viewer_path.path)) {
    return;
  }

  const std::optional<blender::ed::viewer_path::ViewerPathForGeometryNodesViewer> parsed_path =
      blender::ed::viewer_path::parse_geometry_nodes_viewer(workspace.viewer_path);
  if (parsed_path.has_value() &&
      blender::ed::viewer_path::is_active_geometry_nodes_viewer(C, *parsed_path)) {
    /* The current viewer path is still valid and active. */
    return;
  }
  /* Reset inactive viewer path. */
  BKE_viewer_path_clear(&workspace.viewer_path);
  WM_event_add_notifier(&C, NC_VIEWER_PATH, nullptr);
}

void ED_workspace_do_listen(bContext *C, const wmNotifier * /*note*/)
{
  WorkSpace *workspace = CTX_wm_workspace(C);
  validate_viewer_paths(*C, *workspace);
}
