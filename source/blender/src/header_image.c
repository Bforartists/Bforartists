/**
 * header_image.c oct-2003
 *
 * Functions to draw the "UV/Image Editor" window header
 * and handle user events sent to it.
 * 
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA	02111-1307, USA.
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

#include <stdlib.h>
#include <string.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifdef WIN32
#include "BLI_winstuff.h"
#endif

#include "BMF_Api.h"
#include "BIF_language.h"
#ifdef INTERNATIONAL
#include "FTF_Api.h"
#endif

#include "DNA_ID.h"
#include "DNA_image_types.h"
#include "DNA_mesh_types.h"
#include "DNA_packedFile_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_userdef_types.h"

#include "BDR_drawmesh.h"
#include "BDR_unwrapper.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_main.h"
#include "BKE_packedFile.h"

#include "BLI_blenlib.h"
#include "BIF_drawimage.h"
#include "BIF_editsima.h"
#include "BIF_interface.h"
#include "BIF_resources.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_toets.h"
#include "BIF_toolbox.h"
#include "BIF_writeimage.h"

#include "BSE_filesel.h"
#include "BSE_headerbuttons.h"

#include "BPY_extern.h"
#include "BPY_menus.h"

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "blendef.h"
#include "mydevice.h"

#include "TPT_DependKludge.h"

void load_space_image(char *str)	/* called from fileselect */
{
	Image *ima=0;
 
	if(G.obedit) {
		error("Can't perfom this in editmode");
		return;
	}

	ima= add_image(str);
	if(ima) {

		G.sima->image= ima;

		free_image_buffers(ima);	/* force read again */
		ima->ok= 1;
		image_changed(G.sima, 0);

	}

	allqueue(REDRAWIMAGE, 0);
}

void image_replace(Image *old, Image *new)
{
	TFace *tface;
	Mesh *me;
	int a, rep=0;

	new->tpageflag= old->tpageflag;
	new->twsta= old->twsta;
	new->twend= old->twend;
	new->xrep= old->xrep;
	new->yrep= old->yrep;
 
	me= G.main->mesh.first;
	while(me) {

		if(me->tface) {
			tface= me->tface;
			a= me->totface;
			while(a--) {
				if(tface->tpage==old) {
					tface->tpage= new;
					rep++;
				}
				tface++;
			}
		}
		me= me->id.next;
 
	}
	if(rep) {
		if(new->id.us==0) new->id.us= 1;
	}
	else error("Nothing replaced");
}

void replace_space_image(char *str)		/* called from fileselect */
{
	Image *ima=0;

	if(G.obedit) {
		error("Can't perfom this in editmode");
		return;
	}

	ima= add_image(str);
	if(ima) {
 
		if(G.sima->image && G.sima->image != ima) {
			image_replace(G.sima->image, ima);
		}
 
		G.sima->image= ima;

		free_image_buffers(ima);	/* force read again */
		ima->ok= 1;
		/* replace also assigns: */
		image_changed(G.sima, 0);

	}
	allqueue(REDRAWIMAGE, 0);
}

void save_paint(char *name)
{
	char str[FILE_MAXDIR+FILE_MAXFILE];
	Image *ima = G.sima->image;
	ImBuf *ibuf;

	if (ima  && ima->ibuf) {
		BLI_strncpy(str, name, sizeof(str));

		BLI_convertstringcode(str, G.sce, G.scene->r.cfra);

		if (saveover(str)) {
			ibuf = IMB_dupImBuf(ima->ibuf);

			if (ibuf) {
				if (BIF_write_ibuf(ibuf, str)) {
					BLI_strncpy(ima->name, name, sizeof(ima->name));
					ima->ibuf->userflags &= ~IB_BITMAPDIRTY;
					allqueue(REDRAWHEADERS, 0);
					allqueue(REDRAWBUTSSHADING, 0);
				} else {
					error("Couldn't write image: %s", str);
				}

				IMB_freeImBuf(ibuf);
			}
		}
	}
}

void do_image_buttons(unsigned short event)
{
	Image *ima;
	ID *id, *idtest;
	int nr;
	char name[256];

	if(curarea->win==0) return;

	switch(event) {
	case B_SIMAGEHOME:
		image_home();
		break;

	case B_SIMABROWSE:	
		if(G.sima->imanr== -2) {
			activate_databrowse((ID *)G.sima->image, ID_IM, 0, B_SIMABROWSE,
											&G.sima->imanr, do_image_buttons);
			return;
		}
		if(G.sima->imanr < 0) break;
	
		nr= 1;
		id= (ID *)G.sima->image;

		idtest= G.main->image.first;
		while(idtest) {
			if(nr==G.sima->imanr) {
				break;
			}
			nr++;
			idtest= idtest->next;
		}
		if(idtest==0) { /* no new */
			return;
		}
	
		if(idtest!=id) {
			G.sima->image= (Image *)idtest;
			if(idtest->us==0) idtest->us= 1;
			allqueue(REDRAWIMAGE, 0);
		}
		/* also when image is the same: assign! 0==no tileflag: */
		image_changed(G.sima, 0);

		break;
	case B_SIMAGELOAD:
		
		if(G.sima->image) strcpy(name, G.sima->image->name);
		else strcpy(name, U.textudir);
		
		if(G.qual==LR_CTRLKEY)
			activate_imageselect(FILE_SPECIAL, "SELECT IMAGE", name, load_space_image);
		else
			activate_fileselect(FILE_SPECIAL, "SELECT IMAGE", name, load_space_image);
		break;
		
	case B_SIMAGEREPLACE:
		
		if(G.sima->image) strcpy(name, G.sima->image->name);
		else strcpy(name, U.textudir);
		
		if(G.qual==LR_CTRLKEY)
			activate_imageselect(FILE_SPECIAL, "REPLACE IMAGE", name, replace_space_image);
		else
			activate_fileselect(FILE_SPECIAL, "REPLACE IMAGE", name, replace_space_image);
		break;
		
	case B_SIMAGEDRAW:
		
		if(G.f & G_FACESELECT) {
			make_repbind(G.sima->image);
			image_changed(G.sima, 1);
		}
		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWIMAGE, 0);
		break;

	case B_SIMAGEDRAW1:
		image_changed(G.sima, 2);		/* 2: only tileflag */
		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWIMAGE, 0);
		break;
		
	case B_TWINANIM:
		ima = G.sima->image;
		if (ima) {
			if(ima->flag & IMA_TWINANIM) {
				nr= ima->xrep*ima->yrep;
				if(ima->twsta>=nr) ima->twsta= 1;
				if(ima->twend>=nr) ima->twend= nr-1;
				if(ima->twsta>ima->twend) ima->twsta= 1;
				allqueue(REDRAWIMAGE, 0);
			}
		}
		break;

	case B_CLIP_UV:
		tface_do_clip();
		allqueue(REDRAWIMAGE, 0);
		allqueue(REDRAWVIEW3D, 0);
		break;

	case B_SIMAGEPAINTTOOL:
		// check for packed file here
		allqueue(REDRAWIMAGE, 0);
		allqueue(REDRAWVIEW3D, 0);
		break;
	case B_SIMAPACKIMA:
		ima = G.sima->image;
		if (ima) {
			if (ima->packedfile) {
				if (G.fileflags & G_AUTOPACK) {
					if (okee("Disable AutoPack ?")) {
						G.fileflags &= ~G_AUTOPACK;
					}
				}
				
				if ((G.fileflags & G_AUTOPACK) == 0) {
					unpackImage(ima, PF_ASK);
				}
			} else {
				if (ima->ibuf && (ima->ibuf->userflags & IB_BITMAPDIRTY)) {
					error("Can't pack painted image. Save image first.");
				} else {
					ima->packedfile = newPackedFile(ima->name);
				}
			}
			allqueue(REDRAWBUTSSHADING, 0);
			allqueue(REDRAWHEADERS, 0);
		}
		break;
	case B_SIMAGESAVE:
		ima = G.sima->image;
		if (ima) {
			strcpy(name, ima->name);
			if (ima->ibuf) {
				char str[32];	// sufficient for message
				save_image_filesel_str(str);
				activate_fileselect(FILE_SPECIAL, str, name, save_paint);
			}
		}
		break;
	}
}

static void do_image_viewmenu(void *arg, int event)
{

	switch(event) {
	case 0: /* Update Automatically */
		if(G.sima->lock) G.sima->lock = 0;
		else G.sima->lock = 1;
		break;
	case 1: /* View All */
		do_image_buttons(B_SIMAGEHOME);
		break;
	case 2: /* Maximize Window */
		/* using event B_FULL */
		break;
	case 5: /* Draw Shadow Mesh */
		if(G.sima->flag & SI_DRAWSHADOW)
			G.sima->flag &= ~SI_DRAWSHADOW;
		else
			G.sima->flag |= SI_DRAWSHADOW;
		allqueue(REDRAWIMAGE, 0);
		break;
	case 6: /* Draw Faces */
		if(G.f & G_DRAWFACES)
			G.f &= ~G_DRAWFACES;
		else
			G.f |= G_DRAWFACES;
		allqueue(REDRAWIMAGE, 0);
		break;
	case 7: /* Properties  Panel */
		add_blockhandler(curarea, IMAGE_HANDLER_PROPERTIES, UI_PNL_UNSTOW);
		break;
	case 8: /* Paint Panel... */
		add_blockhandler(curarea, IMAGE_HANDLER_PAINT, UI_PNL_UNSTOW);
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
}

static uiBlock *image_viewmenu(void *arg_unused)
{
/*	static short tog=0; */
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiNewBlock(&curarea->uiblocks, "image_viewmenu", UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_image_viewmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "View Properties...",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 7, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "View Paint Tool...",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 8, "");

	
	if(G.f & G_DRAWFACES) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Draw Faces", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 6, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Draw Faces|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 6, "");
	if(G.sima->flag & SI_DRAWSHADOW) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Draw Shadow Mesh", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 5, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Draw Shadow Mesh|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 5, "");
	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	if(G.sima->lock) {
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Update Automatically|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	} else {
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Update Automatically|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	}

	uiDefBut(block, SEPR, 0, "",					0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "View All|Home", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
		
	if(!curarea->full) uiDefIconTextBut(block, BUTM, B_FULL, ICON_BLANK1, "Maximize Window|Ctrl UpArrow", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
	else uiDefIconTextBut(block, BUTM, B_FULL, ICON_BLANK1, "Tile Window|Ctrl DownArrow", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
	
	if(curarea->headertype==HEADERTOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	
	return block;
}

static void do_image_selectmenu(void *arg, int event)
{
	switch(event)
	{
	case 0: /* Border Select */
		borderselect_sima();
		break;
	case 1: /* Select/Deselect All */
		select_swap_tface_uv();
		break;
	case 2: /* Unlink Selection */
		unlink_selection();
		break;
	case 3: /* Select Linked UVs */
		select_linked_tface_uv();
		break;
	case 4: /* Toggle Local UVs Stick to Vertex in Mesh */
		if(G.sima->flag & SI_LOCALSTICKY)
			G.sima->flag &= ~SI_LOCALSTICKY;
		else {
			G.sima->flag |= SI_LOCALSTICKY;
			G.sima->flag &= ~SI_STICKYUVS;
		}
		allqueue(REDRAWIMAGE, 0);
		break;  
	case 5: /* Toggle UVs Stick to Vertex in Mesh */
		if(G.sima->flag & SI_STICKYUVS)
			G.sima->flag &= ~SI_STICKYUVS;
		else {
			G.sima->flag |= SI_STICKYUVS;
			G.sima->flag &= ~SI_LOCALSTICKY;
		}
		allqueue(REDRAWIMAGE, 0);
		break;  
	case 6: /* Toggle Active Face Select */
		if(G.sima->flag & SI_SELACTFACE)
			G.sima->flag &= ~SI_SELACTFACE;
		else
			G.sima->flag |= SI_SELACTFACE;
		allqueue(REDRAWIMAGE, 0);
		break;
	}
}

static uiBlock *image_selectmenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiNewBlock(&curarea->uiblocks, "image_selectmenu", UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_image_selectmenu, NULL);

	if(G.sima->flag & SI_SELACTFACE) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Active Face Select|C", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 6, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Active Face Select|C", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 6, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");	

	if(G.sima->flag & SI_LOCALSTICKY) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Stick Local UVs to Mesh Vertex|Shift C", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Stick Local UVs to Mesh Vertex|Shift C", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");

	if(G.sima->flag & SI_STICKYUVS) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Stick UVs to Mesh Vertex|Ctrl C", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 5, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Stick UVs to Mesh Vertex|Ctrl C", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 5, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");	

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Border Select|B", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect All|A", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Unlink Selection|Alt L", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select Linked UVs|L", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 3, "");

	if(curarea->headertype==HEADERTOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);

	return block;
}

static void do_image_image_rtmappingmenu(void *arg, int event)
{
	switch(event) {
	case 0: /* UV Co-ordinates */
		G.sima->image->flag = BCLR(G.sima->image->flag, 4);
		break;
	case 1: /* Reflection */
		G.sima->image->flag = BSET(G.sima->image->flag, 4);
		break;
		}

 	allqueue(REDRAWVIEW3D, 0);
}

static uiBlock *image_image_rtmappingmenu(void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiNewBlock(&curarea->uiblocks, "image_image_rtmappingmenu", UI_EMBOSSP, UI_HELV, G.curscreen->mainwin);
	uiBlockSetButmFunc(block, do_image_image_rtmappingmenu, NULL);
	
	if (G.sima->image->flag & IMA_REFLECT) {
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "UV Co-ordinates",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Reflection",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	} else {
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "UV Co-ordinates",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Reflection",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	}

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_image_imagemenu(void *arg, int event)
{
	Image *ima;
	char name[256];

	switch(event)
	{
	case 0: /* Open */
		if(G.sima->image) strcpy(name, G.sima->image->name);
		else strcpy(name, U.textudir);
		if(G.qual==LR_CTRLKEY)
			activate_imageselect(FILE_SPECIAL, "Open Image", name, load_space_image);
		else
			activate_fileselect(FILE_SPECIAL, "Open Image", name, load_space_image);
		break;
	case 1: /* Replace */
		if(G.sima->image) strcpy(name, G.sima->image->name);
		else strcpy(name, U.textudir);
		
		if(G.qual==LR_CTRLKEY)
			activate_imageselect(FILE_SPECIAL, "Replace Image", name, replace_space_image);
		else
			activate_fileselect(FILE_SPECIAL, "Replace Image", name, replace_space_image);
		break;
	case 2: /* Pack Image */
		ima = G.sima->image;
		if (ima) {
			if (ima->packedfile) {
				error("Image is already packed.");
			} else {
				if (ima->ibuf && (ima->ibuf->userflags & IB_BITMAPDIRTY)) {
					error("Can't pack painted image. Save the painted image first.");
				} else {
					ima->packedfile = newPackedFile(ima->name);
				}
			}
		}
		allqueue(REDRAWBUTSSHADING, 0);
		allqueue(REDRAWHEADERS, 0);
		break;
	case 3: /* Unpack Image */
		ima = G.sima->image;
		if (ima) {
			if (ima->packedfile) {
				if (G.fileflags & G_AUTOPACK) {
					if (okee("Disable AutoPack?")) {
						G.fileflags &= ~G_AUTOPACK;
					}
				}
				
				if ((G.fileflags & G_AUTOPACK) == 0) {
					unpackImage(ima, PF_ASK);
				}
			} else {
				error("There are no packed images to unpack");
			}
		}
		allqueue(REDRAWBUTSSHADING, 0);
		allqueue(REDRAWHEADERS, 0);
		break;
	case 4: /* Texture Painting */
		if(G.sima->flag & SI_DRAWTOOL) G.sima->flag &= ~SI_DRAWTOOL;
		else G.sima->flag |= SI_DRAWTOOL;
		break;
	case 5: /* Save Painted Image */
		ima = G.sima->image;
		if (ima) {
			strcpy(name, ima->name);
			if (ima->ibuf) {
				char str[32];	// sufficient for message
				save_image_filesel_str(str);
				activate_fileselect(FILE_SPECIAL, str, name, save_paint);
			}
		}
		break;
	case 6: /* Reload Image */
		ima = G.sima->image;
		if (ima) {
			if (ima->packedfile) {
				PackedFile *pf;
				pf = newPackedFile(ima->name);
				if (pf) {
					freePackedFile(ima->packedfile);
					ima->packedfile = pf;
				}
				else
					error("Image not available. Keeping packed image.");
			}
			free_image_buffers(ima);	/* force read again */
			ima->ok= 1;
			image_changed(G.sima, 0);
		}
		allqueue(REDRAWIMAGE, 0);
		break;
	}
}

static uiBlock *image_imagemenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=150;

	block= uiNewBlock(&curarea->uiblocks, "image_imagemenu", UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_image_imagemenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Open...", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	
	if (G.sima->image) {
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Save...", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 5, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Replace...", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Reload", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 6, "");

		uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");	
		
		if (G.sima->image->packedfile) {
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Unpack Image...", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 3, "");
		} else {
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Pack Image", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
		}
			
		uiDefBut(block, SEPR, 0, "",        0, yco-=7, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

		if(G.sima->flag & SI_DRAWTOOL) {
			uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Texture Painting", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
		} else {
			uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Texture Painting", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
		}
		
		uiDefBut(block, SEPR, 0, "",        0, yco-=7, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
		
		uiDefIconTextBlockBut(block, image_image_rtmappingmenu, NULL, ICON_RIGHTARROW_THIN, "Realtime Texture Mapping", 0, yco-=20, 120, 19, "");
		// uiDefIconTextBut(block, BUTM, 1, ICON_MENU_PANEL, "Realtime Texture Animation|",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 7, "");
	}
	
	if(curarea->headertype==HEADERTOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 80);

	return block;
}

static void do_image_uvs_showhidemenu(void *arg, int event)
{
	switch(event) {
	case 4: /* show hidden faces */
		reveal_tface_uv();
		break;
	case 5: /* hide selected faces */
		hide_tface_uv(0);
		break;
	case 6: /* hide deselected faces */
		hide_tface_uv(1);
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
}

static uiBlock *image_uvs_showhidemenu(void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiNewBlock(&curarea->uiblocks, "image_uvs_showhidemenu", UI_EMBOSSP, UI_HELV, G.curscreen->mainwin);
	uiBlockSetButmFunc(block, do_image_uvs_showhidemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Show Hidden Faces|Alt H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Selected Faces|H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Hide Deselected Faces|Shift H",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 6, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_image_uvs_propfalloffmenu(void *arg, int event)
{
	extern int prop_mode;
	
	switch(event) {
	case 0: /* proportional edit - sharp*/
		prop_mode = 0;
		break;
	case 1: /* proportional edit - smooth*/
		prop_mode = 1;
		break;
	}
}

static uiBlock *image_uvs_propfalloffmenu(void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;
	extern int prop_mode;

	block= uiNewBlock(&curarea->uiblocks, "image_uvs_propfalloffmenu", UI_EMBOSSP, UI_HELV, G.curscreen->mainwin);
	uiBlockSetButmFunc(block, do_image_uvs_propfalloffmenu, NULL);
	
	if (prop_mode==0) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Sharp|Shift O",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Sharp|Shift O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	if (prop_mode==1) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Smooth|Shift O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Smooth|Shift O",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
		
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_image_uvs_transformmenu(void *arg, int event)
{
	switch(event) {
	case 0: /* Grab */
		transform_tface_uv('g');
		break;
	case 1: /* Rotate */
		transform_tface_uv('r');
		break;
	case 2: /* Scale */
		transform_tface_uv('s');
		break;
	case 3: /* Weld / Align */
		transform_tface_uv('w');
		break;
	case 4: /* Mirror */
		mirrormenu_tface_uv();
		break;
	}
}

static uiBlock *image_uvs_transformmenu(void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiNewBlock(&curarea->uiblocks, "image_uvs_transformmenu", UI_EMBOSSP, UI_HELV, G.curscreen->mainwin);
	uiBlockSetButmFunc(block, do_image_uvs_transformmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Grab/Move|G", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Rotate|R", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Scale|S", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");	

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Weld/Align|W", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Mirror...|M", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}


static void do_image_uvsmenu(void *arg, int event)
{
	/* events >=20 are registered bpython scripts */
	if (event >= 20) BPY_menu_do_python(PYMENU_UV, event - 20);

	else switch(event)
	{
	case 1: /* UVs Constrained Rectangular */
		if(G.sima->flag & SI_BE_SQUARE) G.sima->flag &= ~SI_BE_SQUARE;
		else G.sima->flag |= SI_BE_SQUARE;
		break;
	case 2: /* UVs Clipped to Image Size */
		if(G.sima->flag & SI_CLIP_UV) G.sima->flag &= ~SI_CLIP_UV;
		else G.sima->flag |= SI_CLIP_UV;
		break;
	case 3: /* Limit Stitch UVs */
		stitch_uv_tface(1);
		break;
	case 4: /* Stitch UVs */
		stitch_uv_tface(0);
		break;
	case 5: /* Proportional Edit (toggle) */
		if(G.f & G_PROPORTIONAL)
			G.f &= ~G_PROPORTIONAL;
		else
			G.f |= G_PROPORTIONAL;
		break;
	case 7: /* UVs Snap to Pixel */
		if(G.sima->flag & SI_NOPIXELSNAP) G.sima->flag &= ~SI_NOPIXELSNAP;
		else G.sima->flag |= SI_NOPIXELSNAP;
		break;
    case 8:
		pin_tface_uv(1);
		break;
    case 9:
		pin_tface_uv(0);
		break;
    case 10:
		if (okee("LSCM unwrap"))
			unwrap_lscm();
		break;
	}
}

static uiBlock *image_uvsmenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	BPyMenu *pym;
	int i = 0;

	block= uiNewBlock(&curarea->uiblocks, "image_uvsmenu", UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_image_uvsmenu, NULL);

	// uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Transform Properties...|N", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	// uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	if(G.sima->flag & SI_NOPIXELSNAP) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Snap to Pixels|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 7, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Snap to Pixels|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 7, "");

	if(G.sima->flag & SI_BE_SQUARE) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Quads Constrained Rectangular|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Quads Constrained Rectangular|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	
	if(G.sima->flag & SI_CLIP_UV) uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Layout Clipped to Image Size|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
	else uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Layout Clipped to Image Size|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");	

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Unpin|Alt P", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 9, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Pin|P", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 8, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "LSCM Unwrap|E", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 10, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");	

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Limit Stitch...|Shift V", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Stitch|V", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
	uiDefIconTextBlockBut(block, image_uvs_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Transform", 0, yco-=20, 120, 19, "");

	uiDefBut(block, SEPR, 0, "",				0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	if(G.f & G_PROPORTIONAL)
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Proportional Editing|O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	else
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Proportional Editing|O", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");

	uiDefIconTextBlockBut(block, image_uvs_propfalloffmenu, NULL, ICON_RIGHTARROW_THIN, "Proportional Falloff", 0, yco-=20, 120, 19, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");	
	
	/* note that we acount for the 3 previous entries with i+3: */
	for (pym = BPyMenuTable[PYMENU_UV]; pym; pym = pym->next, i++) {

		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, pym->name, 0, yco-=20, menuwidth, 19, 
				 NULL, 0.0, 0.0, 1, i+20, 
				 pym->tooltip?pym->tooltip:pym->filename);
	}

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");	

	uiDefIconTextBlockBut(block, image_uvs_showhidemenu, NULL, ICON_RIGHTARROW_THIN, "Show/Hide Faces", 0, yco-=20, menuwidth, 19, "");

	if(curarea->headertype==HEADERTOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);

	return block;
}

void image_buttons(void)
{
	uiBlock *block;
	short xco, xmax;
	char naam[256];
	/* This should not be a static var */
	static int headerbuttons_packdummy;

	headerbuttons_packdummy = 0;
		
	sprintf(naam, "header %d", curarea->headwin);
	block= uiNewBlock(&curarea->uiblocks, naam, UI_EMBOSS, UI_HELV, curarea->headwin);

	if(area_is_active_area(curarea)) uiBlockSetCol(block, TH_HEADER);
	else uiBlockSetCol(block, TH_HEADERDESEL);

	what_image(G.sima);

	curarea->butspacetype= SPACE_IMAGE;

	xco = 8;
	uiDefIconTextButC(block, ICONTEXTROW,B_NEWSPACE, ICON_VIEW3D, windowtype_pup(), xco,0,XIC+10,YIC, &(curarea->butspacetype), 1.0, SPACEICONMAX, 0, 0, "Current Window Type. Click for menu of available types.");
	xco+= XIC+14;

	uiBlockSetEmboss(block, UI_EMBOSSN);
	if(curarea->flag & HEADER_NO_PULLDOWN) {
		uiDefIconButS(block, TOG|BIT|0, B_FLIPINFOMENU, ICON_DISCLOSURE_TRI_RIGHT,
				xco,2,XIC,YIC-2,
				&(curarea->flag), 0, 0, 0, 0, "Show pulldown menus");
	} else {
		uiDefIconButS(block, TOG|BIT|0, B_FLIPINFOMENU, ICON_DISCLOSURE_TRI_DOWN,
				xco,2,XIC,YIC-2,
				&(curarea->flag), 0, 0, 0, 0, "Hide pulldown menus");
	}
	uiBlockSetEmboss(block, UI_EMBOSS);
	xco+=XIC;

	if((curarea->flag & HEADER_NO_PULLDOWN)==0) {
		/* pull down menus */
		uiBlockSetEmboss(block, UI_EMBOSSP);
	
		xmax= GetButStringLength("View");
		uiDefBlockBut(block, image_viewmenu, NULL, "View", xco, -2, xmax-3, 24, "");
		xco+= xmax;
		
		xmax= GetButStringLength("Select");
		uiDefBlockBut(block, image_selectmenu, NULL, "Select", xco, -2, xmax-3, 24, "");
        
		xco+= xmax;
		
		xmax= GetButStringLength("Image");
		uiDefBlockBut(block, image_imagemenu, NULL, "Image", xco, -2, xmax-3, 24, "");
		xco+= xmax;
		
		xmax= GetButStringLength("UVs");
		uiDefBlockBut(block, image_uvsmenu, NULL, "UVs", xco, -2, xmax-3, 24, "");
		xco+= xmax;
	}
	
	
	/* other buttons: */
	uiBlockSetEmboss(block, UI_EMBOSS);

	// xco+=XIC;

	/*xco = 8;
	
	uiDefIconTextButC(block, ICONTEXTROW,B_NEWSPACE, ICON_VIEW3D, windowtype_pup(), xco,0,XIC+10,YIC, &(curarea->butspacetype), 1.0, SPACEICONMAX, 0, 0, "Displays Current Window Type. Click for menu of available types.");
*/
	// xco+= XIC+22;
	
	/* FULL WINDOW */
	/* if(curarea->full) uiDefIconBut(block, BUT,B_FULL, ICON_SPLITSCREEN,	xco,0,XIC,YIC, 0, 0, 0, 0, 0, "Returns to multiple views window (CTRL+Up arrow)");
	else uiDefIconBut(block, BUT,B_FULL, ICON_FULLSCREEN,	xco,0,XIC,YIC, 0, 0, 0, 0, 0, "Makes current window full screen (CTRL+Down arrow)");
	*/
	
	/* HOME*/
	/*	uiDefIconBut(block, BUT, B_SIMAGEHOME, ICON_HOME,	xco+=XIC,0,XIC,YIC, 0, 0, 0, 0, 0, "Zooms window to home view showing all items (HOMEKEY)"); 
	
	
	uiDefIconButS(block, TOG|BIT|0, B_BE_SQUARE, ICON_KEEPRECT,	xco+=XIC,0,XIC,YIC, &G.sima->flag, 0, 0, 0, 0, "Toggles constraining UV polygons to squares while editing");
	uiDefIconButS(block, ICONTOG|BIT|2, B_CLIP_UV, ICON_CLIPUV_DEHLT,xco+=XIC,0,XIC,YIC, &G.sima->flag, 0, 0, 0, 0, "Toggles clipping UV with image size");
	*/
    
	xco= std_libbuttons(block, xco, 0, 0, NULL, B_SIMABROWSE, (ID *)G.sima->image, 0, &(G.sima->imanr), 0, 0, B_IMAGEDELETE, 0, 0);

	
	if (G.sima->image) {
	
		xco+= 8;
	
		if (G.sima->image->packedfile) {
			headerbuttons_packdummy = 1;
		}
		uiDefIconButI(block, TOG|BIT|0, B_SIMAPACKIMA, ICON_PACKAGE,	xco,0,XIC,YIC, &headerbuttons_packdummy, 0, 0, 0, 0, "Pack/Unpack this image");
		
		xco+= XIC;
	}
	
	
	/*
	uiBlockSetCol(block, TH_AUTO);
	uiDefBut(block, BUT, B_SIMAGELOAD, "Load",		xco, 0, 2*XIC, YIC, 0, 0, 0, 0, 0, "Loads image - file select");
	xco+= 2*XIC;
	
	if (G.sima->image) {
		uiBlockSetCol(block, TH_AUTO);
		uiDefBut(block, BUT, B_SIMAGEREPLACE, "Replace",xco,0,(short)(3*XIC),YIC, 0, 0, 0, 0, 0, "Replaces current image - file select");
		xco+= 3.5*XIC;
		uiDefIconButS(block, TOG|BIT|4, 0, ICON_ENVMAP, xco,0,XIC,YIC, &G.sima->image->flag, 0, 0, 0, 0, "Uses this image as a reflection map (Ignores UV Coordinates)");

		uiDefIconButS(block, TOG|BIT|0, B_SIMAGEDRAW1, ICON_GRID, xco+=XIC,0,XIC,YIC, &G.sima->image->flag, 0, 0, 0, 0, "");
		uiDefButS(block, NUM, B_SIMAGEDRAW, "",	xco+=XIC,0,XIC,YIC, &G.sima->image->xrep, 1.0, 16.0, 0, 0, "Sets the degree of repetition in the X direction");
		uiDefButS(block, NUM, B_SIMAGEDRAW, "",	xco+=XIC,0,XIC,YIC, &G.sima->image->yrep, 1.0, 16.0, 0, 0, "Sets the degree of repetition in the Y direction");
	
		uiDefButS(block, TOG|BIT|1, B_TWINANIM, "Anim", xco,0,(2*XIC),YIC, &G.sima->image->tpageflag, 0, 0, 0, 0, "Toggles use of animated texture");
		xco+= XIC;
		uiDefButS(block, NUM, B_TWINANIM, "",	xco+=XIC,0,XIC,YIC, &G.sima->image->twsta, 0.0, 128.0, 0, 0, "Displays the start frame of an animated texture. Click to change.");
		uiDefButS(block, NUM, B_TWINANIM, "",	xco+=XIC,0,XIC,YIC, &G.sima->image->twend, 0.0, 128.0, 0, 0, "Displays the end frame of an animated texture. Click to change.");
//		uiDefButS(block, TOG|BIT|2, 0, "Cycle", xco+=XIC,0,2*XIC,YIC, &G.sima->image->tpageflag, 0, 0, 0, 0, "");
		
		uiDefButS(block, NUM, 0, "Speed", xco,0,4*XIC,YIC, &G.sima->image->animspeed, 1.0, 100.0, 0, 0, "Displays Speed of the animation in frames per second. Click to change.");
		xco+= 4.5*XIC;

		// texture paint button used to be here
		
		xco+= XIC;
		if (G.sima->image && G.sima->image->ibuf && (G.sima->image->ibuf->userflags & IB_BITMAPDIRTY)) {
			uiDefBut(block, BUT, B_SIMAGESAVE, "Save",		xco,0,2*XIC,YIC, 0, 0, 0, 0, 0, "Saves image");
			xco += 2*XIC;
		}
	}
*/

	xco+= 8;

	if (G.sima->image) {

#ifdef NAN_TPT
		
		uiDefIconButS(block, TOG|BIT|3, B_SIMAGEPAINTTOOL, ICON_TPAINT_HLT, xco,0,XIC,YIC, &G.sima->flag, 0, 0, 0, 0, "Enables painting textures on the image with left mouse button");
		xco+= XIC+8;
#endif /* NAN_TPT */

	}

	/* draw LOCK */
	uiDefIconButS(block, ICONTOG, 0, ICON_UNLOCKED,	xco,0,XIC,YIC, &(G.sima->lock), 0, 0, 0, 0, "Updates other affected window spaces automatically to reflect changes in real time");
	
	/* Always do this last */
	curarea->headbutlen= xco+2*XIC;
	
	uiDrawBlock(block);
}

