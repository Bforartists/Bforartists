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
 * 
 */

#ifndef BLO_SIGN_VERIFY_H
#define BLO_SIGN_VERIFY_H

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifdef __cplusplus
extern "C" {
#endif

#include "BLO_sys_types.h"

#define SIGNVERIFYHEADERSTRUCTSIZE sizeof(struct BLO_sign_verify_HeaderStruct)
/* TODO use reasonable sizes
Tests showed: pubKeyLen 64, cryptedKeyLen 64 bytes
So we pick 2*64 bytes + tail for now : */

#define MAXPUBKEYLEN 130
#define MAXSIGNATURELEN 130

struct BLO_sign_verify_HeaderStruct {
	uint8_t  magic;				/* poor mans header recognize check */
	uint32_t length;			/* how much signed data is there */
	uint8_t  pubKey[MAXPUBKEYLEN];
	uint32_t pubKeyLen;			/* the actual pubKey length */
	uint8_t  signature[MAXSIGNATURELEN];
	int32_t  signatureLen;		/* the actual signature length */
	uint32_t datacrc;			/* data crc checksum */
	uint32_t headercrc;			/* header minus crc itself checksum */
};

#define SIGNERHEADERSTRUCTSIZE sizeof(struct BLO_SignerHeaderStruct)
#define MAXSIGNERLEN 100

struct BLO_SignerHeaderStruct {
	uint8_t name[MAXSIGNERLEN];	/* the signers name (from the key) */
	uint8_t email[MAXSIGNERLEN];	/* the signers email (from the key) */
	uint8_t homeUrl[MAXSIGNERLEN];	/* the signers home page */
	uint8_t text[MAXSIGNERLEN];	/* optional additional user text */
	uint8_t pubKeyUrl1[MAXSIGNERLEN];	/* the signers pubKey store */
	uint8_t pubKeyUrl2[MAXSIGNERLEN];	/* the signers pubKey at NaN */
};

#ifdef __cplusplus
}
#endif

#endif /* BLO_SIGN_VERIFY_H */

