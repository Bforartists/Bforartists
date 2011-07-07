/**
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * Contributor(s): Mitchell Stokes.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file BL_ActionManager.cpp
 *  \ingroup ketsji
 */

#ifndef __BL_ACTIONMANAGER
#define __BL_ACTIONMANAGER

#include "BL_Action.h"

#define MAX_ACTION_LAYERS 4

/**
 * BL_ActionManager is responsible for handling a KX_GameObject's actions.
 */
class BL_ActionManager
{
private:
	BL_Action* m_layers[MAX_ACTION_LAYERS];

public:
	BL_ActionManager(class KX_GameObject* obj);
	~BL_ActionManager();

	bool PlayAction(const char* name,
					float start,
					float end,
					short layer=0,
					short priority=0,
					float blendin=0.f,
					short play_mode=0,
					float layer_weight=0.f,
					short ipo_flags=0,
					float playback_speed=1.f);
	/**
	 * Gets the current frame of an action
	 */
	float GetActionFrame(short layer);

	/**
	 * Sets the current frame of an action
	 */
	void SetActionFrame(short layer, float frame);
	
	/**
	 * Gets the currently running action on the given layer
	 */
	struct bAction *GetCurrentAction(short layer);

	/**
	 * Stop playing the action on the given layer
	 */
	void StopAction(short layer);

	/**
	 * Check if an action has finished playing
	 */
	bool IsActionDone(short layer);

	/**
	 * Update any running actions
	 */
	void Update(float);

#ifdef WITH_CXX_GUARDEDALLOC
public:
	void *operator new(size_t num_bytes) { return MEM_mallocN(num_bytes, "GE:BL_ActionManager"); }
	void operator delete( void *mem ) { MEM_freeN(mem); }
#endif
};

#endif //BL_ACTIONMANAGER

