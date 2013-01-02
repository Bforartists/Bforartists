/*
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
 * The Original Code is Copyright (C) 2010 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef __FREESTYLE_POW_23_GRID_DENSITY_PROVIDER_H__
#define __FREESTYLE_POW_23_GRID_DENSITY_PROVIDER_H__

/** \file blender/freestyle/intern/view_map/Pow23GridDensityProvider.h
 *  \ingroup freestyle
 *  \brief Class to define a cell grid surrounding the projected image of a scene
 *  \author Alexander Beels
 *  \date 2011-2-8
 */

#include "GridDensityProvider.h"

class Pow23GridDensityProvider : public GridDensityProvider
{
	// Disallow copying and assignment
	Pow23GridDensityProvider(const Pow23GridDensityProvider& other);
	Pow23GridDensityProvider& operator=(const Pow23GridDensityProvider& other);

public:
	Pow23GridDensityProvider(OccluderSource& source, const real proscenium[4], unsigned numFaces);
	Pow23GridDensityProvider(OccluderSource& source, const BBox<Vec3r>& bbox, const GridHelpers::Transform& transform,
	                         unsigned numFaces);
	Pow23GridDensityProvider(OccluderSource& source, unsigned numFaces);
	virtual ~Pow23GridDensityProvider();

protected:
	unsigned numFaces;

private:
	void initialize(const real proscenium[4]);
};

class Pow23GridDensityProviderFactory : public GridDensityProviderFactory
{
public:
	Pow23GridDensityProviderFactory(unsigned numFaces);
	~Pow23GridDensityProviderFactory();

	auto_ptr<GridDensityProvider> newGridDensityProvider(OccluderSource& source, const real proscenium[4]);
	auto_ptr<GridDensityProvider> newGridDensityProvider(OccluderSource& source, const BBox<Vec3r>& bbox,
	                                                     const GridHelpers::Transform& transform);
	auto_ptr<GridDensityProvider> newGridDensityProvider(OccluderSource& source);

protected:
	unsigned numFaces;
};

#endif // __FREESTYLE_POW_23_GRID_DENSITY_PROVIDER_H__
