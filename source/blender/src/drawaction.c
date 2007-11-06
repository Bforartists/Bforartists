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
 * Contributor(s): Joshua Leung
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 * Drawing routines for the Action window type
 */

/* System includes ----------------------------------------------------- */

#include <math.h>
#include <stdlib.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "MEM_guardedalloc.h"

#include "BMF_Api.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

/* Types --------------------------------------------------------------- */
#include "DNA_listBase.h"
#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_curve_types.h"
#include "DNA_ipo_types.h"
#include "DNA_object_types.h"
#include "DNA_screen_types.h"
#include "DNA_scene_types.h"
#include "DNA_space_types.h"
#include "DNA_constraint_types.h"
#include "DNA_key_types.h"

#include "BKE_action.h"
#include "BKE_depsgraph.h"
#include "BKE_ipo.h"
#include "BKE_key.h"
#include "BKE_global.h"
#include "BKE_utildefines.h"

/* Everything from source (BIF, BDR, BSE) ------------------------------ */ 

#include "BIF_editaction.h"
#include "BIF_editkey.h"
#include "BIF_editnla.h"
#include "BIF_interface.h"
#include "BIF_interface_icons.h"
#include "BIF_gl.h"
#include "BIF_glutil.h"
#include "BIF_resources.h"
#include "BIF_screen.h"
#include "BIF_mywindow.h"
#include "BIF_space.h"

#include "BDR_drawaction.h"
#include "BDR_editcurve.h"

#include "BSE_drawnla.h"
#include "BSE_drawipo.h"
#include "BSE_editaction_types.h"
#include "BSE_editipo.h"
#include "BSE_time.h"
#include "BSE_view.h"

/* 'old' stuff": defines and types, and own include -------------------- */

#include "blendef.h"
#include "mydevice.h"

/********************************** Slider Stuff **************************** */

/* sliders for shapekeys */
static void meshactionbuts(SpaceAction *saction, Object *ob, Key *key)
{
	int           i;
	char          str[64];
	float	      x, y;
	uiBlock       *block;
	uiBut 		  *but;

#define XIC 20
#define YIC 20

	/* lets make the rvk sliders */

	/* reset the damn myortho2 or the sliders won't draw/redraw
	 * correctly *grumble*
	 */
	mywinset(curarea->win);
	myortho2(-0.375, curarea->winx-0.375, G.v2d->cur.ymin, G.v2d->cur.ymax);

    sprintf(str, "actionbuttonswin %d", curarea->win);
    block= uiNewBlock (&curarea->uiblocks, str, UI_EMBOSS, UI_HELV, curarea->win);

	x = NAMEWIDTH + 1;
    y = 0.0f;

	/* make the little 'open the sliders' widget */
	// should eventually be removed
    BIF_ThemeColor(TH_FACE); // this slot was open... (???... Aligorith)
	glRects(2,            y + 2*CHANNELHEIGHT - 2, ACTWIDTH - 2, y + CHANNELHEIGHT + 2);
	glColor3ub(0, 0, 0);
	glRasterPos2f(4, y + CHANNELHEIGHT + 6);
	BMF_DrawString(G.font, "Sliders");

	uiBlockSetEmboss(block, UI_EMBOSSN);

	if (!(G.saction->flag & SACTION_SLIDERS)) {
		ACTWIDTH = NAMEWIDTH;
		but=uiDefIconButBitS(block, TOG, SACTION_SLIDERS, B_REDR, 
					  ICON_DISCLOSURE_TRI_RIGHT,
					  NAMEWIDTH - XIC - 5, y + CHANNELHEIGHT,
					  XIC,YIC-2,
					  &(G.saction->flag), 0, 0, 0, 0, 
					  "Show action window sliders");
		/* no hilite, the winmatrix is not correct later on... */
		uiButSetFlag(but, UI_NO_HILITE);

	}
	else {
		but= uiDefIconButBitS(block, TOG, SACTION_SLIDERS, B_REDR, 
					  ICON_DISCLOSURE_TRI_DOWN,
					  NAMEWIDTH - XIC - 5, y + CHANNELHEIGHT,
					  XIC,YIC-2,
					  &(G.saction->flag), 0, 0, 0, 0, 
					  "Hide action window sliders");
		/* no hilite, the winmatrix is not correct later on... */
		uiButSetFlag(but, UI_NO_HILITE);
					  
		ACTWIDTH = NAMEWIDTH + SLIDERWIDTH;

		/* sliders are open so draw them */
		BIF_ThemeColor(TH_FACE); 

		glRects(NAMEWIDTH,  0,  NAMEWIDTH+SLIDERWIDTH,  curarea->winy);
		uiBlockSetEmboss(block, UI_EMBOSS);
		for (i=1; i < key->totkey; i++) {
			make_rvk_slider(block, ob, i, 
							x, y, SLIDERWIDTH-2, CHANNELHEIGHT-1, "Slider to control Shape Keys");

			y-=CHANNELHEIGHT+CHANNELSKIP;
			
			/* see sliderval array in editkey.c */
			if(i >= 255) break;
		}
	}
	uiDrawBlock(block);

}

static void icu_slider_func(void *voidicu, void *voidignore) 
{
	/* the callback for the icu sliders ... copies the
	 * value from the icu->curval into a bezier at the
	 * right frame on the right ipo curve (creating both the
	 * ipo curve and the bezier if needed).
	 */
	IpoCurve  *icu= voidicu;
	BezTriple *bezt=NULL;
	float cfra, icuval;

	cfra = frame_to_float(CFRA);
	if (G.saction->pin==0 && OBACT)
		cfra= get_action_frame(OBACT, cfra);
	
	/* if the ipocurve exists, try to get a bezier
	 * for this frame
	 */
	bezt = get_bezt_icu_time(icu, &cfra, &icuval);

	/* create the bezier triple if one doesn't exist,
	 * otherwise modify it's value
	 */
	if (bezt == NULL) {
		insert_vert_icu(icu, cfra, icu->curval, 0);
	}
	else {
		bezt->vec[1][1] = icu->curval;
	}

	/* make sure the Ipo's are properly processed and
	 * redraw as necessary
	 */
	sort_time_ipocurve(icu);
	testhandles_ipocurve(icu);
	
	/* nla-update (in case this affects anything) */
	synchronize_action_strips();
	
	/* do redraw pushes, and also the depsgraph flushes */
	if (OBACT->pose || ob_get_key(OBACT))
		DAG_object_flush_update(G.scene, OBACT, OB_RECALC);
	else
		DAG_object_flush_update(G.scene, OBACT, OB_RECALC_OB);
	
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWACTION, 0);
	allqueue(REDRAWNLA, 0);
	allqueue(REDRAWIPO, 0);
	allspace(REMAKEIPO, 0);
	allqueue(REDRAWBUTSALL, 0);
}

static void make_icu_slider(uiBlock *block, IpoCurve *icu,
					 int x, int y, int w, int h, char *tip)
{
	/* create a slider for the ipo-curve*/
	uiBut *but;
	
	if(icu==NULL) return;
	
	if (IS_EQ(icu->slide_max, icu->slide_min)) {
		if (IS_EQ(icu->ymax, icu->ymin)) {
			if (ELEM(icu->blocktype, ID_CO, ID_KE)) {
				/* hack for constraints and shapekeys (and maybe a few others) */
				icu->slide_min= 0.0;
				icu->slide_max= 1.0;
			}
			else {
				icu->slide_min= -100;
				icu->slide_max= 100;
			}
		}
		else {
			icu->slide_min= icu->ymin;
			icu->slide_max= icu->ymax;
		}
	}
	if (icu->slide_min >= icu->slide_max) {
		SWAP(float, icu->slide_min, icu->slide_max);
	}

	but=uiDefButF(block, NUMSLI, REDRAWVIEW3D, "",
				  x, y , w, h,
				  &(icu->curval), icu->slide_min, icu->slide_max, 
				  10, 2, tip);
	
	uiButSetFunc(but, icu_slider_func, icu, NULL);
	
	// no hilite, the winmatrix is not correct later on...
	uiButSetFlag(but, UI_NO_HILITE);
}

/* sliders for ipo-curves of active action-channel */
static void action_icu_buts(SpaceAction *saction)
{
	bAction *act= saction->action;
	bActionChannel *achan;
	bConstraintChannel *conchan;
	IpoCurve *icu;
	char          str[64];
	float	        x, y;
	uiBlock       *block;

	/* lets make the action sliders */

	/* reset the damn myortho2 or the sliders won't draw/redraw
	 * correctly *grumble*
	 */
	mywinset(curarea->win);
	myortho2(-0.375, curarea->winx-0.375, G.v2d->cur.ymin, G.v2d->cur.ymax);
	
    sprintf(str, "actionbuttonswin %d", curarea->win);
    block= uiNewBlock (&curarea->uiblocks, str, 
                       UI_EMBOSS, UI_HELV, curarea->win);

	x = NAMEWIDTH + 1;
    y = 0.0f;
	
	uiBlockSetEmboss(block, UI_EMBOSSN);

	if (G.saction->flag & SACTION_SLIDERS) {
		/* sliders are open so draw them */
		
		/* draw backdrop first */
		BIF_ThemeColor(TH_FACE); // change this color... it's ugly
		glRects(NAMEWIDTH,  G.v2d->cur.ymin,  NAMEWIDTH+SLIDERWIDTH,  G.v2d->cur.ymax);
		
		uiBlockSetEmboss(block, UI_EMBOSS);
		for (achan=act->chanbase.first; achan; achan= achan->next) {
			if(VISIBLE_ACHAN(achan)) {
				y-=CHANNELHEIGHT+CHANNELSKIP;
				
				if (EXPANDED_ACHAN(achan)) {					
					if (achan->ipo) {
						y-=CHANNELHEIGHT+CHANNELSKIP;
						
						if (FILTER_IPO_ACHAN(achan)) {
							for (icu= achan->ipo->curve.first; icu; icu=icu->next) {
								if (achan->flag & ACHAN_HILIGHTED) {
									make_icu_slider(block, icu,
													x, y, SLIDERWIDTH-2, CHANNELHEIGHT-2, 
													"Slider to control current value of IPO-Curve");
								}
								
								y-=CHANNELHEIGHT+CHANNELSKIP;
							}
						}
					}
					
					if (achan->constraintChannels.first) {
						y-=CHANNELHEIGHT+CHANNELSKIP;
						
						if (FILTER_CON_ACHAN(achan)) {
							for (conchan= achan->constraintChannels.first; conchan; conchan=conchan->next) {
								if ((achan->flag & ACHAN_HILIGHTED) && EDITABLE_CONCHAN(conchan)) {
									icu= (IpoCurve *)conchan->ipo->curve.first;
									make_icu_slider(block, icu,
													x, y, SLIDERWIDTH-2, CHANNELHEIGHT-2, 
													"Slider to control current value of Constraint Channel");
								}
								
								y-=CHANNELHEIGHT+CHANNELSKIP;
							}
						}
					}
				}
			}
		}
	}
	uiDrawBlock(block);
}

/********************************** Current Frame **************************** */

void draw_cfra_action (void)
{
	Object *ob;
	float vec[2];
	
	/* Draw a light green line to indicate current frame */
	vec[0]= (G.scene->r.cfra);
	vec[0]*= G.scene->r.framelen;
	
	vec[1]= G.v2d->cur.ymin;
	glColor3ub(0x60, 0xc0, 0x40);
	glLineWidth(2.0);
	
	glBegin(GL_LINE_STRIP);
	glVertex2fv(vec);
	vec[1]= G.v2d->cur.ymax;
	glVertex2fv(vec);
	glEnd();
	
	/* Draw dark green line if slow-parenting/time-offset is enabled */
	ob= (G.scene->basact) ? (G.scene->basact->object) : 0;
	if(ob && ob->sf!=0.0 && (ob->ipoflag & OB_OFFS_OB) ) {
		vec[0]-= ob->sf;
		
		glColor3ub(0x10, 0x60, 0);
		
		glBegin(GL_LINE_STRIP);
		glVertex2fv(vec);
		vec[1]= G.v2d->cur.ymin;
		glVertex2fv(vec);
		glEnd();
	}
	
	glLineWidth(1.0);
}

/********************************** Left-Hand Panel + Generics **************************** */

/* left hand part */
static void draw_channel_names(void) 
{
	ListBase act_data = {NULL, NULL};
	bActListElem *ale;
	int filter;
	void *data;
	short datatype;
	short ofsx = 0, ofsy = 0; 
	float x= 0.0f, y= 0.0f;
	
	/* determine what type of data we are operating on */
	data = get_action_context(&datatype);
	if (data == NULL) return;
	
	/* Clip to the scrollable area */
	if(curarea->winx>SCROLLB+10 && curarea->winy>SCROLLH+10) {
		if(G.v2d->scroll) {	
			ofsx= curarea->winrct.xmin;	
			ofsy= curarea->winrct.ymin;
			glViewport(ofsx,  ofsy+G.v2d->mask.ymin, NAMEWIDTH, 
					   (ofsy+G.v2d->mask.ymax) -
					   (ofsy+G.v2d->mask.ymin)); 
			glScissor(ofsx,	 ofsy+G.v2d->mask.ymin, NAMEWIDTH, 
					  (ofsy+G.v2d->mask.ymax) -
					  (ofsy+G.v2d->mask.ymin));
		}
	}
	
	/* prepare scaling for LHS panel */
	myortho2(0,	NAMEWIDTH, G.v2d->cur.ymin, G.v2d->cur.ymax);
	
	/* set default color back to black */
	glColor3ub(0x00, 0x00, 0x00);
	
	/* build list of channels to draw */
	filter= (ACTFILTER_FORDRAWING|ACTFILTER_VISIBLE|ACTFILTER_CHANNELS);
	actdata_filter(&act_data, filter, data, datatype);
		
	/* loop through channels, and set up drawing depending on their type  */
	glEnable(GL_BLEND);
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
	
	for (ale= act_data.first; ale; ale= ale->next) {
		short indent= 0, offset= 0, sel= 0;
		int expand= -1, protect = -1, special= -1, mute = -1;
		char name[32];
		
		/* determine what needs to be drawn */
		switch (ale->type) {
			case ACTTYPE_ACHAN: /* action channel */
			{
				bActionChannel *achan= (bActionChannel *)ale->data;
				
				indent = 0;
				special = -1;
				
				if (EXPANDED_ACHAN(achan))
					expand = ICON_TRIA_DOWN;
				else
					expand = ICON_TRIA_RIGHT;
					
				if (EDITABLE_ACHAN(achan))
					protect = ICON_UNLOCKED;
				else
					protect = ICON_LOCKED;
					
				if (achan->ipo) {
					if (achan->ipo->muteipo)
						mute = ICON_MUTE_IPO_ON;
					else
						mute = ICON_MUTE_IPO_OFF;
				}
				
				sel = SEL_ACHAN(achan);
				sprintf(name, achan->name);
			}
				break;
			case ACTTYPE_CONCHAN: /* constraint channel */
			{
				bConstraintChannel *conchan = (bConstraintChannel *)ale->data;
				
				indent = 2;
				
				if (EDITABLE_CONCHAN(conchan))
					protect = ICON_UNLOCKED;
				else
					protect = ICON_LOCKED;
					
				if (conchan->ipo) {
					if (conchan->ipo->muteipo)
						mute = ICON_MUTE_IPO_ON;
					else
						mute = ICON_MUTE_IPO_OFF;
				}
				
				sel = SEL_CONCHAN(conchan);
				sprintf(name, conchan->name);
			}
				break;
			case ACTTYPE_ICU: /* ipo-curve channel */
			{
				IpoCurve *icu = (IpoCurve *)ale->data;
				
				indent = 2;
				protect = -1; // for now, until this can be supported by others
				
				if (icu->flag & IPO_MUTE)
					mute = ICON_MUTE_IPO_ON;
				else	
					mute = ICON_MUTE_IPO_OFF;
				
				sel = SEL_ICU(icu);
				if (G.saction->pin)
					sprintf(name, getname_ipocurve(icu, NULL));
				else
					sprintf(name, getname_ipocurve(icu, OBACT));
			}
				break;
			case ACTTYPE_SHAPEKEY: /* shapekey channel */
			{
				KeyBlock *kb = (KeyBlock *)ale->data;
				
				indent = 0;
				special = -1;
				
				if (kb->name[0] == '\0')
					sprintf(name, "Key %d", ale->index);
				else
					sprintf(name, kb->name);
			}
				break;
			case ACTTYPE_FILLIPO: /* ipo expand widget */
			{
				bActionChannel *achan = (bActionChannel *)ale->data;
				
				indent = 1;
				special = geticon_ipo_blocktype(achan->ipo->blocktype);
				
				if (FILTER_IPO_ACHAN(achan))	
					expand = ICON_TRIA_DOWN;
				else
					expand = ICON_TRIA_RIGHT;
				
				sel = SEL_ACHAN(achan);
				sprintf(name, "IPO Curves");
			}
				break;
			case ACTTYPE_FILLCON: /* constraint expand widget */
			{
				bActionChannel *achan = (bActionChannel *)ale->data;
				
				indent = 1;
				special = ICON_CONSTRAINT;
				
				if (FILTER_CON_ACHAN(achan))	
					expand = ICON_TRIA_DOWN;
				else
					expand = ICON_TRIA_RIGHT;
					
				sel = SEL_ACHAN(achan);
				sprintf(name, "Constraint");
			}
				break;
		}	

		/* now, start drawing based on this information */
		/* draw backing strip behind channel name */
		BIF_ThemeColorShade(TH_HEADER, ((indent==0)?20: (indent==1)?-20: -40));
		offset = 7 * indent;
		glRectf(x+offset,  y-CHANNELHEIGHT/2,  (float)NAMEWIDTH,  y+CHANNELHEIGHT/2);
		
		/* draw expand/collapse triangle */
		if (expand > 0) {
			BIF_icon_draw(x+offset, y-CHANNELHEIGHT/2, expand);
			offset += 17;
		}
		
		/* draw special icon indicating type of ipo-blocktype? 
		 * 	only for expand widgets for Ipo and Constraint Channels 
		 */
		if (special > 0) {
			offset = 24;
			BIF_icon_draw(x+offset, y-CHANNELHEIGHT/2, special);
			offset += 17;
		}
			
		/* draw name */
		if (sel)
			BIF_ThemeColor(TH_TEXT_HI);
		else
			BIF_ThemeColor(TH_TEXT);
		offset += 3;
		glRasterPos2f(x+offset, y-4);
		BMF_DrawString(G.font, name);
		
		/* reset offset - for RHS of panel */
		offset = 0;
		
		/* draw protect 'lock' */
		if (protect > 0) {
			offset = 16;
			BIF_icon_draw(NAMEWIDTH-offset, y-CHANNELHEIGHT/2, protect);
		}
		
		/* draw mute 'eye' */
		if (mute > 0) {
			offset += 16;
			BIF_icon_draw(NAMEWIDTH-offset, y-CHANNELHEIGHT/2, mute);
		}
		
		/* adjust y-position for next one */
		y-=CHANNELHEIGHT+CHANNELSKIP;
	}
	
	/* free tempolary channels */
	BLI_freelistN(&act_data);
	
	/* re-adjust view matrices for correct scaling */
    myortho2(0,	NAMEWIDTH, 0, (ofsy+G.v2d->mask.ymax) - (ofsy+G.v2d->mask.ymin));	//	Scaling
}

/* sets or clears hidden flags */
void check_action_context(SpaceAction *saction)
{
	bActionChannel *achan;
	
	if(saction->action==NULL) return;
	
	for (achan=saction->action->chanbase.first; achan; achan=achan->next)
		achan->flag &= ~ACHAN_HIDDEN;
	
	if (G.saction->pin==0 && OBACT) {
		Object *ob= OBACT;
		bPoseChannel *pchan;
		bArmature *arm= ob->data;
		
		for (achan=saction->action->chanbase.first; achan; achan=achan->next) {
			pchan= get_pose_channel(ob->pose, achan->name);
			if (pchan) {
				if ((pchan->bone->layer & arm->layer)==0)
					achan->flag |= ACHAN_HIDDEN;
				else if (pchan->bone->flag & BONE_HIDDEN_P)
					achan->flag |= ACHAN_HIDDEN;
			}
		}
	}
}

static void draw_channel_strips(void)
{
	ListBase act_data = {NULL, NULL};
	bActListElem *ale;
	int filter;
	void *data;
	short datatype;
	
	rcti scr_rct;
	gla2DDrawInfo *di;
	float y, sta, end;
	int act_start, act_end, dummy;
	char col1[3], col2[3];
	
	BIF_GetThemeColor3ubv(TH_SHADE2, col2);
	BIF_GetThemeColor3ubv(TH_HILITE, col1);

	/* get editor data */
	data= get_action_context(&datatype);
	if (data == NULL) return;

	scr_rct.xmin= G.saction->area->winrct.xmin + G.saction->v2d.mask.xmin;
	scr_rct.ymin= G.saction->area->winrct.ymin + G.saction->v2d.mask.ymin;
	scr_rct.xmax= G.saction->area->winrct.xmin + G.saction->v2d.hor.xmax;
	scr_rct.ymax= G.saction->area->winrct.ymin + G.saction->v2d.mask.ymax; 
	di= glaBegin2DDraw(&scr_rct, &G.v2d->cur);

	/* if in NLA there's a strip active, map the view */
	if (datatype == ACTCONT_ACTION) {
		if (NLA_ACTION_SCALED)
			map_active_strip(di, OBACT, 0);
		
		/* start and end of action itself */
		calc_action_range(data, &sta, &end, 0);
		gla2DDrawTranslatePt(di, sta, 0.0f, &act_start, &dummy);
		gla2DDrawTranslatePt(di, end, 0.0f, &act_end, &dummy);
		
		if (NLA_ACTION_SCALED)
			map_active_strip(di, OBACT, 1);
	}
	
	/* build list of channels to draw */
	filter= (ACTFILTER_FORDRAWING|ACTFILTER_VISIBLE|ACTFILTER_CHANNELS);
	actdata_filter(&act_data, filter, data, datatype);
	
	/* first backdrop strips */
	y = 0.0;
	glEnable(GL_BLEND);
	for (ale= act_data.first; ale; ale= ale->next) {
		int frame1_x, channel_y, sel=0;
		
		/* determine if any need to draw channel */
		if (ale->datatype != ALE_NONE) {
			/* determine if channel is selected */
			switch (ale->type) {
				case ACTTYPE_ACHAN:
				{
					bActionChannel *achan = (bActionChannel *)ale->data;
					sel = SEL_ACHAN(achan);
				}
					break;
				case ACTTYPE_CONCHAN:
				{
					bConstraintChannel *conchan = (bConstraintChannel *)ale->data;
					sel = SEL_CONCHAN(conchan);
				}
					break;
				case ACTTYPE_ICU:
				{
					IpoCurve *icu = (IpoCurve *)ale->data;
					sel = SEL_ICU(icu);
				}
					break;
			}
			
			if (datatype == ACTCONT_ACTION) {
				gla2DDrawTranslatePt(di, G.v2d->cur.xmin, y, &frame1_x, &channel_y);
				
				if (sel) glColor4ub(col1[0], col1[1], col1[2], 0x22);
				else glColor4ub(col2[0], col2[1], col2[2], 0x22);
				glRectf(frame1_x,  channel_y-CHANNELHEIGHT/2,  G.v2d->hor.xmax,  channel_y+CHANNELHEIGHT/2);
				
				if (sel) glColor4ub(col1[0], col1[1], col1[2], 0x22);
				else glColor4ub(col2[0], col2[1], col2[2], 0x22);
				glRectf(act_start,  channel_y-CHANNELHEIGHT/2,  act_end,  channel_y+CHANNELHEIGHT/2);
			}
			else if (datatype == ACTCONT_SHAPEKEY) {
				gla2DDrawTranslatePt(di, 1, y, &frame1_x, &channel_y);
				
				/* all frames that have a frame number less than one
				 * get a desaturated orange background
				 */
				glColor4ub(col2[0], col2[1], col2[2], 0x22);
				glRectf(0, channel_y-CHANNELHEIGHT/2, frame1_x, channel_y+CHANNELHEIGHT/2);
				
				/* frames one and higher get a saturated orange background */
				glColor4ub(col2[0], col2[1], col2[2], 0x44);
				glRectf(frame1_x, channel_y-CHANNELHEIGHT/2, G.v2d->hor.xmax,  channel_y+CHANNELHEIGHT/2);
			}
		}
		
		/*	Increment the step */
		y-=CHANNELHEIGHT+CHANNELSKIP;
	}		
	glDisable(GL_BLEND);
	
	if (NLA_ACTION_SCALED)
		map_active_strip(di, OBACT, 0);
	
	/* draw keyframes */
	y = 0.0;
	for (ale= act_data.first; ale; ale= ale->next) {
		switch (ale->datatype) {
			case ALE_IPO:
				draw_ipo_channel(di, ale->key_data, y);
				break;
			case ALE_ICU:
				draw_icu_channel(di, ale->key_data, y);
				break;
		}
		
		y-=CHANNELHEIGHT+CHANNELSKIP;
	}
	
	/* free tempolary channels used for drawing */
	BLI_freelistN(&act_data);

	/* black line marking 'current frame' for Time-Slide transform mode */
	if (G.saction->flag & SACTION_MOVING) {
		int frame1_x, channel_y;
		
		gla2DDrawTranslatePt(di, G.saction->timeslide, 0, &frame1_x, &channel_y);
		cpack(0x0);
		
		glBegin(GL_LINES);
		glVertex2f(frame1_x, G.v2d->mask.ymin - 100);
		glVertex2f(frame1_x, G.v2d->mask.ymax);
		glEnd();
	}
	
	glaEnd2DDraw(di);
}

/* ********* action panel *********** */


void do_actionbuts(unsigned short event)
{
	switch(event) {
	case REDRAWVIEW3D:
		allqueue(REDRAWVIEW3D, 0);
		break;
	case B_REDR:
		allqueue(REDRAWACTION, 0);
		break;
	}
}


static void action_panel_properties(short cntrl)	// ACTION_HANDLER_PROPERTIES
{
	uiBlock *block;

	block= uiNewBlock(&curarea->uiblocks, "action_panel_properties", UI_EMBOSS, UI_HELV, curarea->win);
	uiPanelControl(UI_PNL_SOLID | UI_PNL_CLOSE | cntrl);
	uiSetPanelHandler(ACTION_HANDLER_PROPERTIES);  // for close and esc
	if(uiNewPanel(curarea, block, "Transform Properties", "Action", 10, 230, 318, 204)==0) return;

	uiDefBut(block, LABEL, 0, "test text",		10,180,300,19, 0, 0, 0, 0, 0, "");

}

static void action_blockhandlers(ScrArea *sa)
{
	SpaceAction *sact= sa->spacedata.first;
	short a;
	
	for(a=0; a<SPACE_MAXHANDLER; a+=2) {
		switch(sact->blockhandler[a]) {

		case ACTION_HANDLER_PROPERTIES:
			action_panel_properties(sact->blockhandler[a+1]);
			break;
		
		}
		/* clear action value for event */
		sact->blockhandler[a+1]= 0;
	}
	uiDrawBlocksPanels(sa, 0);
}

/* ************************* Action Editor Space ***************************** */

void drawactionspace(ScrArea *sa, void *spacedata)
{
	bAction *act = NULL;
	Key *key = NULL;
	void *data;
	short datatype;
	
	short ofsx = 0, ofsy = 0;
	float col[3];

	/* this is unlikely to occur, but it may */
	if (G.saction == NULL)
		return;

	/* warning: blocks need to be freed each time, handlers dont remove  */
	uiFreeBlocksWin(&sa->uiblocks, sa->win);

	/* only try to refresh action that's displayed if not pinned */
	if (G.saction->pin==0) {
		/* TODO: allow more than one active action sometime? */
		if (OBACT)
			G.saction->action = OBACT->action;
		else
			G.saction->action= NULL;
	}
	
	/* get data */
	data = get_action_context(&datatype);
	if (datatype == ACTCONT_ACTION)
		act = data;
	else if (datatype == ACTCONT_SHAPEKEY)
		key = data;
	
	/* Lets make sure the width of the left hand of the screen
	 * is set to an appropriate value based on whether sliders
	 * are showing of not
	 */
	if ((data) && (G.saction->flag & SACTION_SLIDERS)) 
		ACTWIDTH = NAMEWIDTH + SLIDERWIDTH;
	else 
		ACTWIDTH = NAMEWIDTH;

	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

	calc_scrollrcts(sa, G.v2d, curarea->winx, curarea->winy);

	/* background color for entire window (used in lefthand part though) */
	BIF_GetThemeColor3fv(TH_HEADER, col);
	glClearColor(col[0], col[1], col[2], 0.0); 
	glClear(GL_COLOR_BUFFER_BIT);
	
	if(curarea->winx>SCROLLB+10 && curarea->winy>SCROLLH+10) {
		if(G.v2d->scroll) {	
			ofsx= curarea->winrct.xmin;	
			ofsy= curarea->winrct.ymin;
			glViewport(ofsx+G.v2d->mask.xmin,  ofsy+G.v2d->mask.ymin, 
					   ( ofsx+G.v2d->mask.xmax-1)-(ofsx+G.v2d->mask.xmin)+1, 
					   ( ofsy+G.v2d->mask.ymax-1)-( ofsy+G.v2d->mask.ymin)+1); 
			glScissor(ofsx+G.v2d->mask.xmin,  ofsy+G.v2d->mask.ymin, 
					  ( ofsx+G.v2d->mask.xmax-1)-(ofsx+G.v2d->mask.xmin)+1, 
					  ( ofsy+G.v2d->mask.ymax-1)-( ofsy+G.v2d->mask.ymin)+1);
		}
	}

	BIF_GetThemeColor3fv(TH_BACK, col);
	glClearColor(col[0], col[1], col[2], 0.0);
	glClear(GL_COLOR_BUFFER_BIT);

	myortho2(G.v2d->cur.xmin, G.v2d->cur.xmax, G.v2d->cur.ymin, G.v2d->cur.ymax);
	bwin_clear_viewmat(sa->win);	/* clear buttons view */
	glLoadIdentity();

	/*	Draw backdrop */
	calc_ipogrid();	
	draw_ipogrid();

	check_action_context(G.saction);
	
	/* Draw channel strips */
	draw_channel_strips();
	
	/* reset matrices for stuff to be drawn on top of keys*/
	glViewport(ofsx+G.v2d->mask.xmin,  
             ofsy+G.v2d->mask.ymin, 
             ( ofsx+G.v2d->mask.xmax-1)-(ofsx+G.v2d->mask.xmin)+1, 
             ( ofsy+G.v2d->mask.ymax-1)-( ofsy+G.v2d->mask.ymin)+1); 
	glScissor(ofsx+G.v2d->mask.xmin,  
            ofsy+G.v2d->mask.ymin, 
            ( ofsx+G.v2d->mask.xmax-1)-(ofsx+G.v2d->mask.xmin)+1, 
            ( ofsy+G.v2d->mask.ymax-1)-( ofsy+G.v2d->mask.ymin)+1);
	myortho2(G.v2d->cur.xmin, G.v2d->cur.xmax,  G.v2d->cur.ymin, G.v2d->cur.ymax);
	
	/* Draw current frame */
	draw_cfra_action();
	
	/* Draw markers */
	draw_markers_timespace(0);
	
	/* Draw 'curtains' for preview */
	draw_anim_preview_timespace();

	/* Draw scroll */
	mywinset(curarea->win);	// reset scissor too
	if (curarea->winx>SCROLLB+10 && curarea->winy>SCROLLH+10) {
		myortho2(-0.375, curarea->winx-0.375, -0.375, curarea->winy-0.375);
		if (G.v2d->scroll) drawscroll(0);
	}

	/* Draw Left-Hand Panel if enough space in window */
	if (G.v2d->mask.xmin!=0) {
		/* Draw channel names */
		draw_channel_names();
		
		if(sa->winx > 50 + NAMEWIDTH + SLIDERWIDTH) {
			if (act) {
				/* if there is an action, draw sliders for its
				 * ipo-curve channels in the action window
				 */
				action_icu_buts(G.saction);
			}
			else if (key) {
				/* if there is a mesh with rvk's selected,
				 * then draw the key frames in the action window
				 */
				meshactionbuts(G.saction, OBACT, key);
			}
		}
	}
	
	mywinset(curarea->win);	// reset scissor too
	myortho2(-0.375, curarea->winx-0.375, -0.375, curarea->winy-0.375);
	draw_area_emboss(sa);

	/* it is important to end a view in a transform compatible with buttons */
	bwin_scalematrix(sa->win, G.saction->blockscale, G.saction->blockscale, G.saction->blockscale);
	action_blockhandlers(sa);

	curarea->win_swap= WIN_BACK_OK;
}

/* *************************** Keyframe Drawing *************************** */

static void add_bezt_to_keycolumnslist(ListBase *keys, BezTriple *bezt)
{
	/* The equivilant of add_to_cfra_elem except this version 
	 * makes ActKeyColumns - one of the two datatypes required
	 * for action editor drawing.
	 */
	ActKeyColumn *ak, *akn;
	
	if (!(keys) || !(bezt)) return;
	
	/* try to find a keyblock that starts on the previous beztriple */
	for (ak= keys->first; ak; ak= ak->next) {
		/* do because of double keys */
		if (ak->cfra == bezt->vec[1][0]) {			
			/* set selection status and 'touched' status */
			if (BEZSELECTED(bezt)) ak->sel = SELECT;
			ak->modified += 1;
			
			return;
		}
		else if (ak->cfra > bezt->vec[1][0]) break;
	}
	
	/* add new block */
	akn= MEM_callocN(sizeof(ActKeyColumn), "ActKeyColumn");
	if (ak) BLI_insertlinkbefore(keys, ak, akn);
	else BLI_addtail(keys, akn);
	
	akn->cfra= bezt->vec[1][0];
	akn->modified += 1;
	
	// TODO: handle type = bezt->h1 or bezt->h2
	akn->handle_type= 0; 
	
	if (BEZSELECTED(bezt))
		akn->sel = SELECT;
	else
		akn->sel = 0;
}

static void add_bezt_to_keyblockslist(ListBase *blocks, IpoCurve *icu, int index)
{
	/* The equivilant of add_to_cfra_elem except this version 
	 * makes ActKeyBlocks - one of the two datatypes required
	 * for action editor drawing.
	 */
	ActKeyBlock *ab, *abn;
	BezTriple *beztn=NULL, *prev=NULL;
	BezTriple *bezt;
	int v;
	
	/* get beztriples */
	beztn= (icu->bezt + index);
	
	for (v=0, bezt=icu->bezt; v<icu->totvert; v++, bezt++) {
		/* skip if beztriple is current */
		if (v != index) {
			/* check if beztriple is immediately before */
			if (beztn->vec[1][0] > bezt->vec[1][0]) {
				/* check if closer than previous was */
				if (prev) {
					if (prev->vec[1][0] < bezt->vec[1][0])
						prev= bezt;
				}
				else {
					prev= bezt;
				}
			}
		}
	}
	
	/* check if block needed - same value? */
	if ((!prev) || (!beztn))
		return;
	if (beztn->vec[1][1] != prev->vec[1][1])
		return;
	
	/* try to find a keyblock that starts on the previous beztriple */
	for (ab= blocks->first; ab; ab= ab->next) {
		/* check if alter existing block or add new block */
		if (ab->start == prev->vec[1][0]) {			
			/* set selection status and 'touched' status */
			if (BEZSELECTED(beztn)) ab->sel = SELECT;
			ab->modified += 1;
			
			return;
		}
		else if (ab->start > prev->vec[1][0]) break;
	}
	
	/* add new block */
	abn= MEM_callocN(sizeof(ActKeyBlock), "ActKeyBlock");
	if (ab) BLI_insertlinkbefore(blocks, ab, abn);
	else BLI_addtail(blocks, abn);
	
	abn->start= prev->vec[1][0];
	abn->end= beztn->vec[1][0];
	abn->val= beztn->vec[1][1];
	
	if (BEZSELECTED(prev) || BEZSELECTED(beztn))
		abn->sel = SELECT;
	else
		abn->sel = 0;
	abn->modified = 1;
}

/* helper function - find actkeycolumn that occurs on cframe */
static ActKeyColumn *cfra_find_actkeycolumn (ListBase *keys, float cframe)
{
	ActKeyColumn *ak;
	
	if (keys==NULL) 
		return NULL;
	 
	for (ak= keys->first; ak; ak= ak->next) {
		if (ak->cfra == cframe)
			return ak;
	}
	
	return NULL;
}

static void draw_keylist(gla2DDrawInfo *di, ListBase *keys, ListBase *blocks, float ypos)
{
	ActKeyColumn *ak;
	ActKeyBlock *ab;
	
	glEnable(GL_BLEND);
	
	/* draw keyblocks */
	if (blocks) {
		for (ab= blocks->first; ab; ab= ab->next) {
			short startCurves, endCurves, totCurves;
			
			/* find out how many curves occur at each keyframe */
			ak= cfra_find_actkeycolumn(keys, ab->start);
			startCurves = (ak)? ak->totcurve: 0;
			
			ak= cfra_find_actkeycolumn(keys, ab->end);
			endCurves = (ak)? ak->totcurve: 0;
			
			/* only draw keyblock if it appears in at all of the keyframes at lowest end */
			if (!startCurves && !endCurves) 
				continue;
			else
				totCurves = (startCurves>endCurves)? endCurves: startCurves;
				
			if (ab->totcurve >= totCurves) {
				int sc_xa, sc_ya;
				int sc_xb, sc_yb;
				
				/* get co-ordinates of block */
				gla2DDrawTranslatePt(di, ab->start, ypos, &sc_xa, &sc_ya);
				gla2DDrawTranslatePt(di, ab->end, ypos, &sc_xb, &sc_yb);
				
				/* draw block */
				if (ab->sel)
					BIF_ThemeColor4(TH_STRIP_SELECT);
				else
					BIF_ThemeColor4(TH_STRIP);
				glRectf(sc_xa,  sc_ya-3,  sc_xb,  sc_yb+5);
			}
		}
	}
	
	/* draw keys */
	if (keys) {
		for (ak= keys->first; ak; ak= ak->next) {
			int sc_x, sc_y;
			
			/* get co-ordinate to draw at */
			gla2DDrawTranslatePt(di, ak->cfra, ypos, &sc_x, &sc_y);
			
			if(ak->sel & 1) BIF_icon_draw_aspect(sc_x-7, sc_y-6, ICON_SPACE2, 1.0f);
			else BIF_icon_draw_aspect(sc_x-7, sc_y-6, ICON_SPACE3, 1.0f);
		}	
	}
	
	glDisable(GL_BLEND);
}

void draw_object_channel(gla2DDrawInfo *di, Object *ob, float ypos)
{
	ListBase keys = {0, 0};
	ListBase blocks = {0, 0};

	ob_to_keylist(ob, &keys, &blocks);
	draw_keylist(di, &keys, &blocks, ypos);
	
	BLI_freelistN(&keys);
	BLI_freelistN(&blocks);
}

void draw_ipo_channel(gla2DDrawInfo *di, Ipo *ipo, float ypos)
{
	ListBase keys = {0, 0};
	ListBase blocks = {0, 0};

	ipo_to_keylist(ipo, &keys, &blocks);
	draw_keylist(di, &keys, &blocks, ypos);
	
	BLI_freelistN(&keys);
	BLI_freelistN(&blocks);
}

void draw_icu_channel(gla2DDrawInfo *di, IpoCurve *icu, float ypos)
{
	ListBase keys = {0, 0};
	ListBase blocks = {0, 0};

	icu_to_keylist(icu, &keys, &blocks);
	draw_keylist(di, &keys, &blocks, ypos);
	
	BLI_freelistN(&keys);
	BLI_freelistN(&blocks);
}

void draw_action_channel(gla2DDrawInfo *di, bAction *act, float ypos)
{
	ListBase keys = {0, 0};

	action_to_keylist(act, &keys, NULL);
	draw_keylist(di, &keys, NULL, ypos);
	BLI_freelistN(&keys);
}

/* --------------- Conversion: data -> keyframe list ------------------ */

void ob_to_keylist(Object *ob, ListBase *keys, ListBase *blocks)
{
	bConstraintChannel *conchan;

	if (ob) {
		/* Add object keyframes */
		if (ob->ipo)
			ipo_to_keylist(ob->ipo, keys, blocks);
		
		/* Add constraint keyframes */
		for (conchan=ob->constraintChannels.first; conchan; conchan=conchan->next){
			if(conchan->ipo)
				ipo_to_keylist(conchan->ipo, keys, blocks);		
		}
			
		/* Add object data keyframes */
		// 		TODO??
	}
}

void icu_to_keylist(IpoCurve *icu, ListBase *keys, ListBase *blocks)
{
	BezTriple *bezt;
	ActKeyColumn *ak;
	ActKeyBlock *ab;
	int v;
	
	if (icu && icu->totvert) {
		/* loop through beztriples, making ActKeys and ActKeyBlocks */
		bezt= icu->bezt;
		
		for (v=0; v<icu->totvert; v++, bezt++) {
			add_bezt_to_keycolumnslist(keys, bezt);
			if (blocks) add_bezt_to_keyblockslist(blocks, icu, v);
		}
		
		/* update the number of curves that elements have appeared in  */
		if (keys) {
			for (ak= keys->first; ak; ak= ak->next) {
				if (ak->modified) {
					ak->modified = 0;
					ak->totcurve += 1;
				}
			}
		}
		if (blocks) {
			for (ab= blocks->first; ab; ab= ab->next) {
				if (ab->modified) {
					ab->modified = 0;
					ab->totcurve += 1;
				}
			}
		}
	}
}

void ipo_to_keylist(Ipo *ipo, ListBase *keys, ListBase *blocks)
{
	IpoCurve *icu;
	
	if (ipo) {
		for (icu= ipo->curve.first; icu; icu= icu->next)
			icu_to_keylist(icu, keys, blocks);
	}
}

void action_to_keylist(bAction *act, ListBase *keys, ListBase *blocks)
{
	bActionChannel *achan;
	bConstraintChannel *conchan;

	if (act) {
		/* loop through action channels */
		for (achan= act->chanbase.first; achan; achan= achan->next) {
			/* firstly, add keys from action channel's ipo block */
			if (achan->ipo)
				ipo_to_keylist(achan->ipo, keys, blocks);
			
			/* then, add keys from constraint channels */
			for (conchan= achan->constraintChannels.first; conchan; conchan= conchan->next) {
				if (conchan->ipo)
					ipo_to_keylist(achan->ipo, keys, blocks);
			}
		}
	}
}

