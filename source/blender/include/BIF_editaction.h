/**
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
 */

#ifndef BIF_EDITACTION_H
#define BIF_EDITACTION_H

#define SET_IPO_POPUP    0
#define SET_IPO_CONSTANT 1
#define SET_IPO_LINEAR   2
#define SET_IPO_BEZIER   3

#define SET_EXTEND_POPUP    0
#define SET_EXTEND_CONSTANT 1
#define SET_EXTEND_EXTRAPOLATION  2
#define SET_EXTEND_CYCLIC   3
#define SET_EXTEND_CYCLICEXTRAPOLATION   4

#define	CHANNELHEIGHT	16
#define	CHANNELSKIP		2
#define NAMEWIDTH      128
#define SLIDERWIDTH    125

#define CHANNEL_FILTER_LOC		0x00000001	/* Show location keys */
#define CHANNEL_FILTER_ROT		0x00000002	/* Show rotation keys */
#define CHANNEL_FILTER_SIZE		0x00000004	/* Show size keys */
#define CHANNEL_FILTER_CON		0x00000008	/* Show constraint keys */
#define CHANNEL_FILTER_RGB		0x00000010	/* Show object color keys */

#define CHANNEL_FILTER_CU		0x00010000	/* Show curve keys */
#define CHANNEL_FILTER_ME		0x00020000	/* Show mesh keys */
#define CHANNEL_FILTER_LA		0x00040000	/* Show lamp keys */


struct bAction;
struct bActionChannel;
struct bPoseChannel;
struct Object;
struct Ipo;
struct BWinEvent;
struct Key;
struct ListBase;

/* Key operations */
void delete_meshchannel_keys(struct Key *key);
void delete_actionchannel_keys(void);
void duplicate_meshchannel_keys(struct Key *key);
void duplicate_actionchannel_keys(void);
void transform_actionchannel_keys(int mode, int dummy);
void transform_meshchannel_keys(char mode, struct Key *key);
struct Key *get_action_mesh_key(void);
int get_nearest_key_num(struct Key *key, short *mval, float *x);
void snap_keys_to_frame(void);
void clean_shapekeys(struct Key *key);
void clean_actionchannels(struct bAction *act);

/* Marker Operations */
struct ListBase *get_saction_markers(struct SpaceAction *saction);
struct TimeMarker *find_nearest_saction_marker(struct ListBase *markers);
void add_saction_marker(struct ListBase *markers, int frame);
void duplicate_saction_markers(struct ListBase *markers);
void remove_saction_markers(struct ListBase *markers);
void rename_saction_markers(struct ListBase *markers);
void transform_saction_markers(int mode, int smode);
void deselect_saction_markers(struct ListBase *markers, int test, int sel);
void borderselect_saction_markers(struct ListBase *markers, float xmin, float xmax, int selectmode);
void selectkeyscolumns_saction_markers(struct ListBase *markers);
void selectkeysbetween_saction_markers(struct ListBase *markers);

/* channel/strip operations */
void up_sel_action(void);
void down_sel_action(void);
void top_sel_action(void);
void bottom_sel_action(void);

/* Handles */
void sethandles_meshchannel_keys(int code, struct Key *key);
void sethandles_actionchannel_keys(int code);

/* Ipo type */ 
void set_ipotype_actionchannels(int ipotype);
void set_exprap_action(int mode);
void set_extendtype_actionchannels(int extendtype);

/* Select */
void borderselect_mesh(struct Key *key);
void borderselect_action(void);
void deselect_actionchannel_keys(struct bAction *act, int test);
void deselect_actionchannels (struct bAction *act, int test);
void deselect_meshchannel_keys (struct Key *key, int test);
int select_channel(struct bAction *act, struct bActionChannel *chan, int selectmode);
void select_actionchannel_by_name (struct bAction *act, char *name, int select);


/* Action */
struct bActionChannel* get_hilighted_action_channel(struct bAction* action);
struct bAction *add_empty_action(int blocktype);

void winqreadactionspace(struct ScrArea *sa, void *spacedata, struct BWinEvent *evt);
struct bAction *bake_action_with_client (struct bAction *act, struct Object *arm, float tolerance);

/* contextual get action */
struct bAction *ob_get_action(struct Object *ob);

void remake_action_ipos(struct bAction *act);

/* this needs review badly! (ton) */
void world2bonespace(float boneSpaceMat[][4], float worldSpace[][4], float restPos[][4], float armPos[][4]);

#endif

