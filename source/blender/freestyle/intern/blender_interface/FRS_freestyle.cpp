#include "../application/AppView.h"
#include "../application/Controller.h"
#include "../application/AppConfig.h"
#include "../application/AppCanvas.h"

#include <iostream>
#include <map>
#include <set>
using namespace std;

#ifdef __cplusplus
extern "C" {
#endif

#include "MEM_guardedalloc.h"

#include "DNA_camera_types.h"
#include "DNA_freestyle_types.h"

#include "BKE_main.h"
#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BPY_extern.h"

#include "renderpipeline.h"
#include "pixelblending.h"

#include "../../FRS_freestyle.h"
#include "../../FRS_freestyle_config.h"

	// Freestyle configuration
	static short freestyle_is_initialized = 0;
	static Config::Path *pathconfig = NULL;
	static Controller *controller = NULL;
	static AppView *view = NULL;

	// camera information
	float freestyle_viewpoint[3];
	float freestyle_mv[4][4];
	float freestyle_proj[4][4];
	int freestyle_viewport[4];
	
	// current scene
	Scene *freestyle_scene;

	string default_module_path;

	//=======================================================
	//   Initialization 
	//=======================================================

	void FRS_initialize() {
		
		if( freestyle_is_initialized )
			return;

		pathconfig = new Config::Path;
		controller = new Controller();
		view = new AppView;
		controller->setView(view);
		freestyle_scene = NULL;
			
		default_module_path = pathconfig->getProjectDir() + Config::DIR_SEP + "style_modules" + Config::DIR_SEP + "contour.py";
			
		freestyle_is_initialized = 1;
	}
	
	void FRS_set_context(bContext* C) {
		cout << "FRS_set_context: context 0x" << C << " scene 0x" << CTX_data_scene(C) << endl;
		controller->setContext(C);
	}

	void FRS_exit() {
		delete pathconfig;
		delete controller;
		delete view;
	}

	//=======================================================
	//   Rendering 
	//=======================================================

	void init_view(Render* re){
		int width = re->scene->r.xsch;
		int height = re->scene->r.ysch;
		
		freestyle_viewport[0] = freestyle_viewport[1] = 0;
		freestyle_viewport[2] = width;
		freestyle_viewport[3] = height;
		
		view->setWidth( width );
		view->setHeight( height );
	}

	void init_camera(Render* re){
		Object* maincam_obj = re->scene->camera;
		// Camera *cam = (Camera*) maincam_obj->data;
		
		freestyle_viewpoint[0] = maincam_obj->obmat[3][0];
		freestyle_viewpoint[1] = maincam_obj->obmat[3][1];
		freestyle_viewpoint[2] = maincam_obj->obmat[3][2];
		
		for( int i = 0; i < 4; i++ )
		   for( int j = 0; j < 4; j++ )
			freestyle_mv[i][j] = re->viewmat[i][j];
		
		for( int i = 0; i < 4; i++ )
		   for( int j = 0; j < 4; j++ )
			freestyle_proj[i][j] = re->winmat[i][j];

		//print_m4("mv", freestyle_mv);
		//print_m4("proj", freestyle_proj);
	}

	
	void prepare(Render* re, SceneRenderLayer* srl ) {
				
		// clear canvas
		controller->Clear();

		// load mesh
		if( controller->LoadMesh(re, srl) ) // returns if scene cannot be loaded or if empty
			return;
		
		// add style modules
		FreestyleConfig* config = &srl->freestyleConfig;
		
		cout << "\n===  Rendering options  ===" << endl;
		cout << "Modules :"<< endl;
		int layer_count = 0;
		

		for( FreestyleModuleConfig* module_conf = (FreestyleModuleConfig *)config->modules.first; module_conf; module_conf = module_conf->next ) {
			if( module_conf->is_displayed ) {
				cout << "  " << layer_count+1 << ": " << module_conf->module_path << endl;
				controller->InsertStyleModule( layer_count, module_conf->module_path );
				controller->toggleLayer(layer_count, true);
				layer_count++;
			}
		}	
		cout << endl;
		
		// set parameters
		controller->setSphereRadius( config->sphere_radius );
		controller->setComputeRidgesAndValleysFlag( (config->flags & FREESTYLE_RIDGES_AND_VALLEYS_FLAG) ? true : false);
		controller->setComputeSuggestiveContoursFlag( (config->flags & FREESTYLE_SUGGESTIVE_CONTOURS_FLAG) ? true : false);
		controller->setSuggestiveContourKrDerivativeEpsilon( config->dkr_epsilon ) ;

		cout << "Sphere radius : " << controller->getSphereRadius() << endl;
		cout << "Redges and valleys : " << (controller->getComputeRidgesAndValleysFlag() ? "enabled" : "disabled") << endl;
		cout << "Suggestive contours : " << (controller->getComputeSuggestiveContoursFlag() ? "enabled" : "disabled") << endl;
		cout << "Suggestive contour dkr epsilon : " << controller->getSuggestiveContourKrDerivativeEpsilon() << endl;

		// compute view map
		controller->ComputeViewMap();
	}
	
	void composite_result(Render* re, SceneRenderLayer* srl, Render* freestyle_render)
	{

		RenderLayer *rl;
	    float *src, *dest, *pixSrc, *pixDest;
		int x, y, rectx, recty;
		
		if( freestyle_render == NULL || freestyle_render->result == NULL )
			return;

		rl = render_get_active_layer( freestyle_render, freestyle_render->result );
	    if( !rl || rl->rectf == NULL) { cout << "Cannot find Freestyle result image" << endl; return; }
		src  = rl->rectf;
		
		rl = RE_GetRenderLayer(re->result, srl->name);
	    if( !rl || rl->rectf == NULL) { cout << "No layer to composite to" << endl; return; }
		dest  = rl->rectf;
		
		rectx = re->rectx;
		recty = re->recty;

	    for( y = 0; y < recty; y++) {
	        for( x = 0; x < rectx; x++) {

	            pixSrc = src + 4 * (rectx * y + x);
	            if( pixSrc[3] > 0.0) {
					pixDest = dest + 4 * (rectx * y + x);
					addAlphaOverFloat(pixDest, pixSrc);
	             }
	         }
	    }
		
	}
	
	int displayed_layer_count( SceneRenderLayer* srl ) {
		int count = 0;

		for( FreestyleModuleConfig* module_conf = (FreestyleModuleConfig *)srl->freestyleConfig.modules.first; module_conf; module_conf = module_conf->next ) {
			if( module_conf->is_displayed )
				count++;
		}
		return count;
	}
	
	void FRS_add_Freestyle(Render* re) {
		
		SceneRenderLayer *srl;
		Render* freestyle_render = NULL;
		
		// init
		cout << "\n#===============================================================" << endl;
		cout << "#  Freestyle" << endl;
		cout << "#===============================================================" << endl;
		
		init_view(re);
		init_camera(re);
		freestyle_scene = re->scene;
		
		for(srl= (SceneRenderLayer *)re->scene->r.layers.first; srl; srl= srl->next) {
			if( !(srl->layflag & SCE_LAY_DISABLE) &&
			 	srl->layflag & SCE_LAY_FRS &&
				displayed_layer_count(srl) > 0       )
			{
				cout << "\n----------------------------------------------------------" << endl;
				cout << "|  " << (re->scene->id.name+2) << "|" << srl->name << endl;
				cout << "----------------------------------------------------------" << endl;
				
				// prepare Freestyle:
				//   - clear canvas
				//   - load mesh
				//   - add style modules
				//   - set parameters
				//   - compute view map
				prepare(re, srl);

				// render and composite Freestyle result
				if( controller->_ViewMap ) {
					
					// render strokes					
					controller->DrawStrokes();
					freestyle_render = controller->RenderStrokes(re);
					controller->CloseFile();
					
					// composite result
					composite_result(re, srl, freestyle_render);
					
					// free resources
					RE_FreeRender(freestyle_render);
				}
			}
		}
		
		freestyle_scene = NULL;
	}

	//=======================================================
	//   Freestyle Panel Configuration
	//=======================================================

	void FRS_add_freestyle_config( SceneRenderLayer* srl )
	{		
		FreestyleConfig* config = &srl->freestyleConfig;
		
		config->modules.first = config->modules.last = NULL;
		config->flags = 0;
		config->sphere_radius = 1.0;
		config->dkr_epsilon = 0.001;
	}
	
	void FRS_free_freestyle_config( SceneRenderLayer* srl )
	{		
		BLI_freelistN( &srl->freestyleConfig.modules );
	}

	void FRS_add_module(FreestyleConfig *config)
	{
		FreestyleModuleConfig* module_conf = (FreestyleModuleConfig*) MEM_callocN( sizeof(FreestyleModuleConfig), "style module configuration");
		BLI_addtail(&config->modules, (void*) module_conf);
		
		strcpy( module_conf->module_path, default_module_path.c_str() );
		module_conf->is_displayed = 1;	
	}
	
	void FRS_delete_module(FreestyleConfig *config, FreestyleModuleConfig *module_conf)
	{
		BLI_freelinkN(&config->modules, module_conf);
	}
	
	void FRS_move_up_module(FreestyleConfig *config, FreestyleModuleConfig *module_conf)
	{
		BLI_remlink(&config->modules, module_conf);
		BLI_insertlink(&config->modules, module_conf->prev->prev, module_conf);
	}
	
	void FRS_move_down_module(FreestyleConfig *config, FreestyleModuleConfig *module_conf)
	{			
		BLI_remlink(&config->modules, module_conf);
		BLI_insertlink(&config->modules, module_conf->next, module_conf);
	}

#ifdef __cplusplus
}
#endif
