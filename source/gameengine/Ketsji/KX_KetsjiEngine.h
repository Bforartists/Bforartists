/*
 * $Id$
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 *
 */
#ifndef __KX_KETSJI_ENGINE
#define __KX_KETSJI_ENGINE

#include "MT_CmMatrix4x4.h"
#include "MT_Matrix4x4.h"
#include "STR_String.h"
#include "KX_ISystem.h"
#include "KX_Scene.h"
#include "KX_Python.h"
#include "KX_WorldInfo.h"
#include <vector>
#include <set>

class KX_TimeCategoryLogger;

#define LEFT_EYE  1
#define RIGHT_EYE 2

enum KX_ExitRequestMode
{
	KX_EXIT_REQUEST_NO_REQUEST = 0,
	KX_EXIT_REQUEST_QUIT_GAME,
	KX_EXIT_REQUEST_RESTART_GAME,
	KX_EXIT_REQUEST_START_OTHER_GAME,
	KX_EXIT_REQUEST_NO_SCENES_LEFT,
	KX_EXIT_REQUEST_BLENDER_ESC,
	KX_EXIT_REQUEST_OUTSIDE,
	KX_EXIT_REQUEST_MAX
};

/**
 * KX_KetsjiEngine is the core game engine class.
 */
class KX_KetsjiEngine
{

private:
	class RAS_ICanvas*				m_canvas; // 2D Canvas (2D Rendering Device Context)
	class RAS_IRasterizer*				m_rasterizer;  // 3D Rasterizer (3D Rendering)
	class KX_ISystem*				m_kxsystem;
	class RAS_IRenderTools*				m_rendertools;
	class KX_ISceneConverter*			m_sceneconverter;
	class NG_NetworkDeviceInterface*		m_networkdevice;
	PyObject*					m_pythondictionary;
	class SCA_IInputDevice*				m_keyboarddevice;
	class SCA_IInputDevice*				m_mousedevice;
	class KX_Dome*						m_dome; // dome stereo mode

	/** Lists of scenes scheduled to be removed at the end of the frame. */
	std::set<STR_String> m_removingScenes;
	/** Lists of overley scenes scheduled to be added at the end of the frame. */
	std::set<STR_String> m_addingOverlayScenes;
	/** Lists of background scenes scheduled to be added at the end of the frame. */
	std::set<STR_String> m_addingBackgroundScenes;
	/** Lists of scenes scheduled to be replaced at the end of the frame. */
	std::set<std::pair<STR_String,STR_String> >	m_replace_scenes;

	/* The current list of scenes. */
	KX_SceneList		m_scenes;
	/* State variable recording the presence of object debug info in the current scene list. */
	bool				m_propertiesPresent;	

	bool				m_bInitialized;
	int					m_activecam;
	bool				m_bFixedTime;
	
	
	bool				m_firstframe;
	int					m_currentFrame;

	double				m_frameTime;//discrete timestamp of the 'game logic frame'
	double				m_clockTime;//current time
	double				m_previousClockTime;//previous clock time
	double				m_remainingTime;

	static int				m_maxLogicFrame;	/* maximum number of consecutive logic frame */
	static int				m_maxPhysicsFrame;	/* maximum number of consecutive physics frame */
	static double			m_ticrate;
	static double			m_anim_framerate; /* for animation playback only - ipo and action */

	static double			m_suspendedtime;
	static double			m_suspendeddelta;

	int					m_exitcode;
	STR_String			m_exitstring;
		/**
		 * Some drawing parameters, the drawing mode
		 * (wire/flat/texture), and the camera zoom
		 * factor.
		 */
	int				m_drawingmode;
	float			m_cameraZoom;
	
	bool			m_overrideCam;	
	STR_String		m_overrideSceneName;
	
	bool			m_overrideCamUseOrtho;
	MT_CmMatrix4x4	m_overrideCamProjMat;
	MT_CmMatrix4x4	m_overrideCamViewMat;
	float			m_overrideCamNear;
	float			m_overrideCamFar;
	float			m_overrideCamLens;

	bool m_stereo;
	int m_curreye;

	/** Categories for profiling display. */
	typedef enum
	{
		tc_first = 0,
		tc_physics = 0,
		tc_logic,
		tc_network,
		tc_scenegraph,
		tc_sound,
		tc_rasterizer,
		tc_services,	// time spend in miscelaneous activities
		tc_overhead,	// profile info drawing overhead
		tc_outside,		// time spend outside main loop
		tc_numCategories
	} KX_TimeCategory;

	/** Time logger. */
	KX_TimeCategoryLogger*	m_logger;
	
	/** Labels for profiling display. */
	static const char		m_profileLabels[tc_numCategories][15];
	/** Last estimated framerate */
	static double			m_average_framerate;
	/** Show the framerate on the game display? */
	bool					m_show_framerate;
	/** Show profiling info on the game display? */
	bool					m_show_profile;
	/** Show any debug (scene) object properties on the game display? */
	bool					m_showProperties;
	/** Show background behind text for readability? */
	bool					m_showBackground;

	bool					m_show_debug_properties;

	/** record physics into keyframes */
	bool					m_game2ipo;

	/** Hide cursor every frame? */
	bool					m_hideCursor;

	/** Override framing bars color? */
	bool					m_overrideFrameColor;
	/** Red component of framing bar color. */
	float					m_overrideFrameColorR;
	/** Green component of framing bar color. */
	float					m_overrideFrameColorG;
	/** Blue component of framing bar color. */
	float					m_overrideFrameColorB;

	void					RenderFrame(KX_Scene* scene, KX_Camera* cam);
	void					PostRenderFrame();
	void					RenderDebugProperties();
	void					RenderShadowBuffers(KX_Scene *scene);
	void					SetBackGround(KX_WorldInfo* worldinfo);
	void					DoSound(KX_Scene* scene);

public:

	KX_KetsjiEngine(class KX_ISystem* system);
	virtual ~KX_KetsjiEngine();

	// set the devices and stuff. the client must take care of creating these
	void			SetWorldSettings(KX_WorldInfo* worldinfo);
	void			SetKeyboardDevice(SCA_IInputDevice* keyboarddevice);
	void			SetMouseDevice(SCA_IInputDevice* mousedevice);
	void			SetNetworkDevice(NG_NetworkDeviceInterface* networkdevice);
	void			SetCanvas(RAS_ICanvas* canvas);
	void			SetRenderTools(RAS_IRenderTools* rendertools);
	void			SetRasterizer(RAS_IRasterizer* rasterizer);
	void			SetPythonDictionary(PyObject* pythondictionary);
	void			SetSceneConverter(KX_ISceneConverter* sceneconverter);
	void			SetGame2IpoMode(bool game2ipo,int startFrame);

	RAS_IRasterizer*		GetRasterizer(){return m_rasterizer;};
	RAS_ICanvas*		    GetCanvas(){return m_canvas;};
	RAS_IRenderTools*	    GetRenderTools(){return m_rendertools;};

	/// Dome functions
	void			InitDome(short res, short mode, short angle, float resbuf, short tilt, struct Text* text); 
	void			EndDome();
	void			RenderDome();
	bool			m_usedome;

	///returns true if an update happened to indicate -> Render
	bool			NextFrame();
	void			Render();
	
	void			StartEngine(bool clearIpo);
	void			StopEngine();
	void			Export(const STR_String& filename);

	void			RequestExit(int exitrequestmode);
	void			SetNameNextGame(const STR_String& nextgame);
	int				GetExitCode();
	const STR_String&	GetExitString();

	KX_SceneList*	CurrentScenes();
	KX_Scene*       FindScene(const STR_String& scenename);
	void			AddScene(class KX_Scene* scene);
	void			ConvertAndAddScene(const STR_String& scenename,bool overlay);

	void			RemoveScene(const STR_String& scenename);
	void			ReplaceScene(const STR_String& oldscene,const STR_String& newscene);
	void			SuspendScene(const STR_String& scenename);
	void			ResumeScene(const STR_String& scenename);

	void			GetSceneViewport(KX_Scene* scene, KX_Camera* cam, RAS_Rect& area, RAS_Rect& viewport);

	void SetDrawType(int drawingtype);
	int  GetDrawType(){return m_drawingmode;};

	void SetCameraZoom(float camzoom);
	
	void EnableCameraOverride(const STR_String& forscene);
	
	void SetCameraOverrideUseOrtho(bool useOrtho);
	void SetCameraOverrideProjectionMatrix(const MT_CmMatrix4x4& mat);
	void SetCameraOverrideViewMatrix(const MT_CmMatrix4x4& mat);
	void SetCameraOverrideClipping(float near, float far);
	void SetCameraOverrideLens(float lens);
	
	/**
	 * Sets display of all frames.
	 * @param bUseFixedTime	New setting for display all frames.
	 */ 
	void SetUseFixedTime(bool bUseFixedTime);

	/**
	 * Returns display of all frames.
	 * @return Current setting for display all frames.
	 */ 
	bool GetUseFixedTime(void) const;

	/**
	 * Returns current render frame clock time
	 */
	double GetClockTime(void) const;

	double GetRealTime(void) const;
	/**
	 * Returns the difference between the local time of the scene (when it
	 * was running and not suspended) and the "curtime"
	 */
	static double GetSuspendedDelta();

	/**
	 * Gets the number of logic updates per second.
	 */
	static double GetTicRate();
	/**
	 * Sets the number of logic updates per second.
	 */
	static void SetTicRate(double ticrate);
	/**
	 * Gets the maximum number of logic frame before render frame
	 */
	static int GetMaxLogicFrame();
	/**
	 * Sets the maximum number of logic frame before render frame
	 */
	static void SetMaxLogicFrame(int frame);
	/**
	 * Gets the maximum number of physics frame before render frame
	 */
	static int GetMaxPhysicsFrame();
	/**
	 * Sets the maximum number of physics frame before render frame
	 */
	static void SetMaxPhysicsFrame(int frame);

	/**
	 * Gets the framerate for playing animations. (actions and ipos)
	 */
	static double GetAnimFrameRate();
	/**
	 * Sets the framerate for playing animations. (actions and ipos)
	 */
	static void SetAnimFrameRate(double framerate);

	/**
	 * Gets the last estimated average framerate
	 */
	static double GetAverageFrameRate();

	/**
	 * Activates or deactivates timing information display.
	 * @param frameRate		Display for frame rate on or off.
	 * @param profile		Display for individual components on or off.
	 * @param properties	Display of scene object debug properties on or off.
	 */ 
	void SetTimingDisplay(bool frameRate, bool profile, bool properties);

	/**
	 * Returns status of timing information display.
	 * @param frameRate		Display for frame rate on or off.
	 * @param profile		Display for individual components on or off.
	 * @param properties	Display of scene object debug properties on or off.
	 */ 
	void GetTimingDisplay(bool& frameRate, bool& profile, bool& properties) const;

	/** 
	 * Sets cursor hiding on every frame.
	 * @param hideCursor Turns hiding on or off.
	 */
	void SetHideCursor(bool hideCursor);

	/** 
	 * Returns the current setting for cursor hiding.
	 * @return The current setting for cursor hiding.
	 */
	bool GetHideCursor(void) const;

	/** 
	 * Enables/disables the use of the framing bar color of the Blender file's scenes.
	 * @param overrideFrameColor The new setting.
	 */
	void SetUseOverrideFrameColor(bool overrideFrameColor);

	/** 
	 * Enables/disables the use of the framing bar color of the Blender file's scenes.
	 * @param useSceneFrameColor The new setting.
	 */
	bool GetUseOverrideFrameColor(void) const; 

	/** 
	 * Set the color used for framing bar color instead of the one in the Blender file's scenes.
	 * @param r Red component of the override color.
	 * @param g Green component of the override color.
	 * @param b Blue component of the override color.
	 */
	void SetOverrideFrameColor(float r, float g, float b);

	/** 
	 * Returns the color used for framing bar color instead of the one in the Blender file's scenes.
	 * @param r Red component of the override color.
	 * @param g Green component of the override color.
	 * @param b Blue component of the override color.
	 */
	void GetOverrideFrameColor(float& r, float& g, float& b) const;
	
protected:
	/**
	 * Processes all scheduled scene activity.
	 * At the end, if the scene lists have changed,
	 * SceneListsChanged(void) is called.
	 * @see SceneListsChanged(void).
	 */
	void			ProcessScheduledScenes(void);

	/**
	 * This method is invoked when the scene lists have changed.
	 */
	void			SceneListsChanged(void);

	void			RemoveScheduledScenes(void);
	void			AddScheduledScenes(void);
	void			ReplaceScheduledScenes(void);
	void			PostProcessScene(class KX_Scene* scene);
	KX_Scene*		CreateScene(const STR_String& scenename);
	
	bool			BeginFrame();
	void			ClearFrame();
	void			EndFrame();
};

#endif //__KX_KETSJI_ENGINE


