#ifndef  BLENDERSTROKERENDERER_H
# define BLENDERSTROKERENDERER_H

# include "../system/FreestyleConfig.h"
# include "StrokeRenderer.h"

#ifdef __cplusplus
extern "C" {
#endif

#include "DNA_material_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "render_types.h"

#ifdef __cplusplus
}
#endif



class LIB_STROKE_EXPORT BlenderStrokeRenderer : public StrokeRenderer
{
public:
  BlenderStrokeRenderer();
  virtual ~BlenderStrokeRenderer();

  /*! Renders a stroke rep */
  virtual void RenderStrokeRep(StrokeRep *iStrokeRep) const;
  virtual void RenderStrokeRepBasic(StrokeRep *iStrokeRep) const;

	Render* RenderScene(Render *re);
	void Close();

protected:
	Scene* scene;
	Scene* old_scene;
	
	Object* object_camera;
	Material* material;

};

#endif // BLENDERSTROKERENDERER_H

