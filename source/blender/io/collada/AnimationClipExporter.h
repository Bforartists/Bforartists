/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 */

#ifndef __ANIMATIONCLIPEXPORTER_H__
#define __ANIMATIONCLIPEXPORTER_H__

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include "COLLADASWLibraryAnimationClips.h"
#include "DEG_depsgraph.h"
#include "ExportSettings.h"

class AnimationClipExporter : COLLADASW::LibraryAnimationClips {
 private:
  Depsgraph *depsgraph;
  Scene *scene;
  COLLADASW::StreamWriter *sw;
  BCExportSettings &export_settings;
  std::vector<std::vector<std::string>> anim_meta;

 public:
  AnimationClipExporter(Depsgraph *depsgraph,
                        COLLADASW::StreamWriter *sw,
                        BCExportSettings &export_settings,
                        std::vector<std::vector<std::string>> anim_meta)
      : COLLADASW::LibraryAnimationClips(sw),
        depsgraph(depsgraph),
        scene(nullptr),
        sw(sw),
        export_settings(export_settings),
        anim_meta(anim_meta)
  {
  }

  void exportAnimationClips(Scene *sce);
};

#endif /*  __ANIMATIONCLIPEXPORTER_H__ */
