
#include "AppGLWidget.h"
#include "Controller.h"
#include "AppConfig.h"
#include "test_config.h"

#include <iostream>

using namespace std;

#ifdef __cplusplus
extern "C" {
#endif

	void FRS_execute() {
		cout << "Freestyle start" << endl;
	
		Config::Path pathconfig;
		Controller *c = new Controller;
		AppGLWidget *view = new AppGLWidget;
		
		c->SetView(view);
		view->setWidth(640);
		view->setHeight(640);
		
		c->Load3DSFile( TEST_3DS_FILE );
		
		c->InsertStyleModule( 0, TEST_STYLE_MODULE_FILE );
		c->toggleLayer(0, true);
		c->ComputeViewMap();
		 
		c->DrawStrokes();
		
		cout << "Freestyle end" << endl;

	}
	
#ifdef __cplusplus
}
#endif
