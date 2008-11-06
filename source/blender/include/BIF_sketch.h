/**
 * $Id:  $
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
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef BIF_SKETCH_H
#define BIF_SKETCH_H

int BIF_paintSketch(short mbut);
void BIF_endStrokeSketch();
void BIF_convertSketch();
void BIF_deleteSketch();
void BIF_selectAllSketch(int mode); /* -1: deselect, 0: select, 1: toggle */
int BIF_validSketchMode();
int BIF_fullSketchMode(); /* full sketch turned on (not Quick) */
void BIF_cancelStrokeSketch();

void  BIF_makeListTemplates();
char *BIF_listTemplates();
int   BIF_currentTemplate();
void  BIF_freeTemplates();
void  BIF_setTemplate(int);	

#endif /* BIF_SKETCH_H */
