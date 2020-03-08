/*
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

#ifndef __BLI_HASH_MD5_H__
#define __BLI_HASH_MD5_H__

/** \file
 * \ingroup bli
 */

#ifdef __cplusplus
extern "C" {
#endif

/* Compute MD5 message digest for LEN bytes beginning at BUFFER.  The
 * result is always in little endian byte order, so that a byte-wise
 * output yields to the wanted ASCII representation of the message
 * digest.  */

void *BLI_hash_md5_buffer(const char *buffer, size_t len, void *resblock);

/* Compute MD5 message digest for bytes read from STREAM.  The
 * resulting message digest number will be written into the 16 bytes
 * beginning at RESBLOCK.  */

int BLI_hash_md5_stream(FILE *stream, void *resblock);

char *BLI_hash_md5_to_hexdigest(void *resblock, char r_hex_digest[33]);

#ifdef __cplusplus
}
#endif

#endif /* __BLI_HASH_MD5_H__ */
