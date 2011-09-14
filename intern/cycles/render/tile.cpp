/*
 * Copyright 2011, Blender Foundation.
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
 */

#include "tile.h"

#include "util_algorithm.h"

CCL_NAMESPACE_BEGIN

TileManager::TileManager(bool progressive_, int passes_, int tile_size_, int min_size_)
{
	progressive = progressive_;
	tile_size = tile_size_;
	min_size = min_size_;

	reset(0, 0, 0);
}

TileManager::~TileManager()
{
}

void TileManager::reset(int width_, int height_, int passes_)
{
	full_width = width_;
	full_height = height_;

	start_resolution = 1;

	int w = width_, h = height_;

	if(min_size != INT_MAX) {
		while(w*h > min_size*min_size) {
			w = max(1, w/2); 
			h = max(1, h/2); 

			start_resolution *= 2;
		}
	}

	passes = passes_;

	state.width = 0;
	state.height = 0;
	state.pass = -1;
	state.resolution = start_resolution;
	state.tiles.clear();
}

void TileManager::set_passes(int passes_)
{
	passes = passes_;
}

void TileManager::set_tiles()
{
	int resolution = state.resolution;
	int image_w = max(1, full_width/resolution);
	int image_h = max(1, full_height/resolution);
	int tile_w = (image_w + tile_size - 1)/tile_size;
	int tile_h = (image_h + tile_size - 1)/tile_size;
	int sub_w = image_w/tile_w;
	int sub_h = image_h/tile_h;

	state.tiles.clear();

	for(int tile_y = 0; tile_y < tile_h; tile_y++) {
		for(int tile_x = 0; tile_x < tile_w; tile_x++) {
			int x = tile_x * sub_w;
			int y = tile_y * sub_h;
			int w = (tile_x == tile_w-1)? image_w - x: sub_w;
			int h = (tile_y == tile_h-1)? image_h - y: sub_h;

			state.tiles.push_back(Tile(x, y, w, h));
		}
	}

	state.width = image_w;
	state.height = image_h;
}

bool TileManager::done()
{
	return (state.pass+1 >= passes);
}

bool TileManager::next()
{
	if(done())
		return false;

	if(progressive && state.resolution > 1) {
		state.pass = 0;
		state.resolution /= 2;
		set_tiles();
	}
	else {
		state.pass++;
		state.resolution = 1;
		set_tiles();
	}

	return true;
}

CCL_NAMESPACE_END

