/*
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 * NetworkSceneManagement generic class
 */
#ifndef __NG_NETWORKSCENE_H
#define __NG_NETWORKSCENE_H

#include "GEN_Map.h"
#include "STR_HashedString.h"
#include <vector>
class NG_NetworkDeviceInterface;

class NG_NetworkScene
{
	class NG_NetworkDeviceInterface *m_networkdevice;	
	GEN_Map<STR_HashedString, class NG_NetworkObject *> m_networkObjects;

	// GEN_Maps used as a 'Bloom' filter
	typedef GEN_Map<STR_HashedString, std::vector<class NG_NetworkMessage*>* > TMessageMap;
	TMessageMap m_messagesByDestinationName;
	TMessageMap m_messagesBySenderName;
	TMessageMap m_messagesBySubject;

public:	
	NG_NetworkScene(NG_NetworkDeviceInterface *nic);
	~NG_NetworkScene();

	/**
	 * progress one frame, handle all network traffic
	 */
	void proceed(double curtime, double deltatime);

	/**
	 * add a networkobject to the scene
	 */
	void AddObject(NG_NetworkObject* object);

	/**
	 * remove a networkobject to the scene
	 */
	void RemoveObject(NG_NetworkObject* object);

	/**
	 * remove all objects at once
	 */
	void RemoveAllObjects();

	/**
	 *	send a message (ascii text) over the network
	 */
	void SendMessage(const STR_String& to,const STR_String& from,const STR_String& subject,const STR_String& message);

	/**
	 * find an object by name
	 */
	NG_NetworkObject* FindNetworkObject(const STR_String& objname);

	bool	ConstraintsAreValid(const STR_String& from,const STR_String& subject,class NG_NetworkMessage* message);
	vector<NG_NetworkMessage*> FindMessages(const STR_String& to,const STR_String& from,const STR_String& subject,bool spamallowed);

protected:
	/**
	 * Releases messages in message map members.
	 */
	void ClearAllMessageMaps(void);

	/**
	 * Releases messages for the given message map.
	 * @param map	Message map with messages.
	 */
	void ClearMessageMap(TMessageMap& map);	
};

#endif //__NG_NETWORKSCENE_H
