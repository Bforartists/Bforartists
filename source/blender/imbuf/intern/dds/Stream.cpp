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
 * Contributors: Amorilia (amorilia@gamebox.net)
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#include <Stream.h>

#include <stdio.h>  // printf
#include <string.h> // memcpy

unsigned int Stream::seek(unsigned int p)
{
	if (p > size) {
		printf("DDS: trying to seek beyond end of stream (corrupt file?)");
	}
	else {
		pos = p;
	}

	return pos;
}

unsigned int mem_read(Stream & mem, unsigned long long & i)
{
	if (mem.pos + 8 > mem.size) {
		printf("DDS: trying to read beyond end of stream (corrupt file?)");
		return(0);
	};
	memcpy(&i, mem.mem + mem.pos, 8); // @@ todo: make sure little endian
	mem.pos += 8;
	return(8);
}

unsigned int mem_read(Stream & mem, unsigned int & i)
{
	if (mem.pos + 4 > mem.size) {
		printf("DDS: trying to read beyond end of stream (corrupt file?)");
		return(0);
	};
	memcpy(&i, mem.mem + mem.pos, 4); // @@ todo: make sure little endian
	mem.pos += 4;
	return(4);
}

unsigned int mem_read(Stream & mem, unsigned short & i)
{
	if (mem.pos + 2 > mem.size) {
		printf("DDS: trying to read beyond end of stream (corrupt file?)");
		return(0);
	};
	memcpy(&i, mem.mem + mem.pos, 2); // @@ todo: make sure little endian
	mem.pos += 2;
	return(2);
}

unsigned int mem_read(Stream & mem, unsigned char & i)
{
	if (mem.pos + 1 > mem.size) {
		printf("DDS: trying to read beyond end of stream (corrupt file?)");
		return(0);
	};
	i = (mem.mem + mem.pos)[0];
	mem.pos += 1;
	return(1);
}

