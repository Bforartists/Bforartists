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
 
#ifndef BIF_GENERATE_H
#define BIF_GENERATE_H

struct bContext;
struct EditBone;
struct BArcIterator;
struct bArmature;
struct ListBase;

typedef int(NextSubdivisionFunc)(struct bContext*, struct BArcIterator*, int, int, float[3], float[3]);
 
float calcArcCorrelation(struct BArcIterator *iter, int start, int end, float v0[3], float n[3]);

int nextFixedSubdivision(struct bContext *C, struct BArcIterator *iter, int start, int end, float head[3], float p[3]);
int nextLengthSubdivision(struct bContext *C, struct BArcIterator *iter, int start, int end, float head[3], float p[3]);
int nextAdaptativeSubdivision(struct bContext *C, struct BArcIterator *iter, int start, int end, float head[3], float p[3]);

struct EditBone * subdivideArcBy(struct bContext *C, struct bArmature *arm, ListBase *editbones, struct BArcIterator *iter, float invmat[][4], float tmat[][3], NextSubdivisionFunc next_subdividion);

void setBoneRollFromNormal(struct EditBone *bone, float *no, float invmat[][4], float tmat[][3]);
 

#endif /* BIF_GENERATE_H */
