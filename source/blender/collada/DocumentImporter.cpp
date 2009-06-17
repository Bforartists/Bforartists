#include "COLLADAFWStableHeaders.h"
#include "COLLADAFWIWriter.h"
#include "COLLADAFWRoot.h"
#include "COLLADAFWNode.h"
#include "COLLADAFWVisualScene.h"
#include "COLLADAFWInstanceGeometry.h"
#include "COLLADAFWFileInfo.h"
#include "COLLADAFWRoot.h"
#include "COLLADAFWLight.h"
#include "COLLADAFWImage.h"
#include "COLLADAFWMaterial.h"
#include "COLLADAFWGeometry.h"
#include "COLLADAFWMesh.h"

#include "COLLADASaxFWLLoader.h"

extern "C" 
{
#include "BKE_main.h"
#include "BKE_mesh.h"
#include "BKE_context.h"

#include "DNA_object_types.h"

#include "ED_object.h"

#include "DocumentImporter.h"
}


/** Class that needs to be implemented by a writer. 
	IMPORTANT: The write functions are called in arbitrary order.*/
class Writer: public COLLADAFW::IWriter
{
private:
	std::string mFilename;
	
	std::vector<COLLADAFW::VisualScene> mVisualScenes;

	bContext *mContext;

	class UnitConverter
	{
	private:
		COLLADAFW::FileInfo::Unit mUnit;
		COLLADAFW::FileInfo::UpAxisType mUpAxis;
	public:
		UnitConverter(COLLADAFW::FileInfo::UpAxisType upAxis, COLLADAFW::FileInfo::Unit& unit) :
			mUpAxis(upAxis), mUnit(unit)
		{
		}

		// TODO
		// convert vector vec from COLLADA format to Blender
		void convertVec3(float *vec)
		{
		}
		
		// TODO need also for angle conversion, time conversion...
	};

public:

	/** Constructor. */
	Writer(bContext *C, const char *filename) : mContext(C), mFilename(filename) {};

	/** Destructor. */
	~Writer() {};

	bool write()
	{
		COLLADASaxFWL::Loader loader;
		COLLADAFW::Root root(&loader, this);

		// XXX report error
		if (!root.loadDocument(mFilename))
			return false;
	}

	/** This method will be called if an error in the loading process occurred and the loader cannot
		continue to to load. The writer should undo all operations that have been performed.
		@param errorMessage A message containing informations about the error that occurred.
	*/
	virtual void cancel(const COLLADAFW::String& errorMessage)
	{
	}

	/** This is the method called. The writer hast to prepare to receive data.*/
	virtual void start()
	{
	}

	/** This method is called after the last write* method. No other methods will be called after this.*/
	virtual void finish()
	{
		// using mVisualScenes, do:
		// - write <node> data to Objects: materials, transforms, etc.
	}

	/** When this method is called, the writer must write the global document asset.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeGlobalAsset ( const COLLADAFW::FileInfo* asset ) 
	{
		// XXX take up_axis, unit into account
		// COLLADAFW::FileInfo::Unit unit = asset->getUnit();
		// COLLADAFW::FileInfo::UpAxisType upAxis = asset->getUpAxisType();

		return true;
	}

	/** When this method is called, the writer must write the scene.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeScene ( const COLLADAFW::Scene* scene ) 
	{
		// XXX could store the scene id, but do nothing for now
		return true;
	}

	/** When this method is called, the writer must write the entire visual scene.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeVisualScene ( const COLLADAFW::VisualScene* visualScene ) 
	{
		// for the sake of clarity link nodes to geometries at a later stage
		mVisualScenes.push_back(*visualScene);
		return true;
	}

	/** When this method is called, the writer must handle all nodes contained in the 
		library nodes.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeLibraryNodes ( const COLLADAFW::LibraryNodes* libraryNodes ) 
	{
		return true;
	}

	/** When this method is called, the writer must write the geometry.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeGeometry ( const COLLADAFW::Geometry* geometry ) 
	{
		// - create a mesh object
		// - enter editmode getting editmesh
		// - write geometry
		// - exit editmode

		// check geometry->getType() first
		COLLADAFW::Mesh *mesh = (COLLADAFW::Mesh*)geometry;

		// create a mesh object
		Object *ob = ED_object_add_type(mContext, OB_MESH);
		Mesh *me = (Mesh*)ob->data;

		// enter editmode
		ED_object_enter_editmode(mContext, 0);

		EditMesh *em = BKE_mesh_get_editmesh(me);

		// write geometry
		// currently only support <triangles>

		BKE_mesh_end_editmesh(me, em);

		// exit editmode
		ED_object_exit_editmode(mContext, EM_FREEDATA);

		return true;
	}

	/** When this method is called, the writer must write the material.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeMaterial( const COLLADAFW::Material* material ) 
	{
		// TODO: create and store a material.
		// Let it have 0 users for now.
		return true;
	}

	/** When this method is called, the writer must write the effect.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeEffect( const COLLADAFW::Effect* effect ) 
	{
		return true;
	}

	/** When this method is called, the writer must write the camera.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeCamera( const COLLADAFW::Camera* camera ) 
	{
		return true;
	}

	/** When this method is called, the writer must write the image.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeImage( const COLLADAFW::Image* image ) 
	{
		return true;
	}

	/** When this method is called, the writer must write the light.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeLight( const COLLADAFW::Light* light ) 
	{
		return true;
	}

	/** When this method is called, the writer must write the Animation.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeAnimation( const COLLADAFW::Animation* animation ) 
	{
		return true;
	}

	/** When this method is called, the writer must write the AnimationList.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeAnimationList( const COLLADAFW::AnimationList* animationList ) 
	{
		return true;
	}

	/** When this method is called, the writer must write the skin controller data.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeSkinControllerData( const COLLADAFW::SkinControllerData* skinControllerData ) 
	{
		return true;
	}

	/** When this method is called, the writer must write the controller.
		@return The writer should return true, if writing succeeded, false otherwise.*/
	virtual bool writeController( const COLLADAFW::Controller* Controller ) 
	{
		return true;
	}
};

void DocumentImporter::import(bContext *C, const char *filename)
{
	Writer w(C, filename);
	w.write();
}
