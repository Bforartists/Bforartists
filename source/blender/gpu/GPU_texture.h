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
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Brecht Van Lommel.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file GPU_texture.h
 *  \ingroup gpu
 */

#ifndef __GPU_TEXTURE_H__
#define __GPU_TEXTURE_H__

#ifdef __cplusplus
extern "C" {
#endif

struct Image;
struct ImageUser;
struct PreviewImage;
	
struct GPUFrameBuffer;
typedef struct GPUTexture GPUTexture;

/* GPU Texture
 * - always returns unsigned char RGBA textures
 * - if texture with non square dimensions is created, depending on the
 *   graphics card capabilities the texture may actually be stored in a
 *   larger texture with power of two dimensions.
 * - can use reference counting:
 *     - reference counter after GPU_texture_create is 1
 *     - GPU_texture_ref increases by one
 *     - GPU_texture_free decreases by one, and frees if 0
 *  - if created with from_blender, will not free the texture
 */

/* Wrapper to supported OpenGL/Vulkan texture internal storage
 * If you need a type just uncomment it. Be aware that some formats
 * are not supported by renderbuffers. All of the following formats
 * are part of the OpenGL 3.3 core
 * specification. */
typedef enum GPUTextureFormat {
	/* Formats texture & renderbuffer */
	GPU_RGBA16F,
	GPU_RGBA8,
	GPU_RG32F,
	GPU_RG16F,
	GPU_R8,
#if 0
	GPU_RGBA32F,
	GPU_RGBA32I,
	GPU_RGBA32UI,
	GPU_RGBA16,
	GPU_RGBA16I,
	GPU_RGBA16UI,
	GPU_RGBA8I,
	GPU_RGBA8UI,
	GPU_RG32I,
	GPU_RG32UI,
	GPU_RG16,
	GPU_RG16I,
	GPU_RG16UI,
	GPU_RG8,
	GPU_RG8I,
	GPU_RG8UI,
	GPU_R32F,
	GPU_R32I,
	GPU_R32UI,
	GPU_R16F,
	GPU_R16I,
	GPU_R16UI,
	GPU_R16,
	GPU_R8I,
	GPU_R8UI,
#endif

	/* Special formats texture & renderbuffer */
#if 0
	GPU_R11F_G11F_B10F,
	GPU_RGB10_A2,
	GPU_RGB10_A2UI,
	GPU_DEPTH32F_STENCIL8,
	GPU_DEPTH24_STENCIL8,
#endif

	/* Texture only format */
#if 0
	GPU_RGBA16_SNORM,
	GPU_RGBA8_SNORM,
	GPU_RGB32F,
	GPU_RGB32I,
	GPU_RGB32UI,
	GPU_RGB16_SNORM,
	GPU_RGB16F,
	GPU_RGB16I,
	GPU_RGB16UI,
	GPU_RGB16,
	GPU_RGB8_SNORM,
	GPU_RGB8,
	GPU_RGB8I,
	GPU_RGB8UI,
	GPU_RG16_SNORM,
	GPU_RG8_SNORM,
	GPU_R16_SNORM,
	GPU_R8_SNORM,
#endif

	/* Special formats texture only */
#if 0
	GPU_SRGB8_A8,
	GPU_SRGB8,
	GPU_RGB9_E5,
	GPU_COMPRESSED_RG_RGTC2,
	GPU_COMPRESSED_SIGNED_RG_RGTC2,
	GPU_COMPRESSED_RED_RGTC1,
	GPU_COMPRESSED_SIGNED_RED_RGTC1,
#endif

	/* Depth Formats */
	GPU_DEPTH_COMPONENT32F,
	GPU_DEPTH_COMPONENT24,
	GPU_DEPTH_COMPONENT16,
} GPUTextureFormat;

GPUTexture *GPU_texture_create_1D(int w, const float *pixels, char err_out[256]);
GPUTexture *GPU_texture_create_1D_custom(
        int w, int channels, GPUTextureFormat data_type, const float *pixels, char err_out[256]);
GPUTexture *GPU_texture_create_2D(int w, int h, const float *pixels, char err_out[256]);
GPUTexture *GPU_texture_create_2D_custom(
        int w, int h, int channels, GPUTextureFormat data_type, const float *pixels, char err_out[256]);
GPUTexture *GPU_texture_create_2D_multisample(int w, int h, const float *pixels, int samples, char err_out[256]);
GPUTexture *GPU_texture_create_2D_array(int w, int h, int d, const float *pixels, char err_out[256]);
GPUTexture *GPU_texture_create_3D(int w, int h, int d, const float *pixels, char err_out[256]);
GPUTexture *GPU_texture_create_3D_custom(
        int w, int h, int d, int channels, GPUTextureFormat data_type, const float *pixels, char err_out[256]);
GPUTexture *GPU_texture_create_depth(int w, int h, char err_out[256]);
GPUTexture *GPU_texture_create_depth_multisample(int w, int h, int samples, char err_out[256]);

GPUTexture *GPU_texture_from_blender(
        struct Image *ima, struct ImageUser *iuser, int textarget, bool is_data, double time, int mipmap);
GPUTexture *GPU_texture_from_preview(struct PreviewImage *prv, int mipmap);

void GPU_invalid_tex_init(void);
void GPU_invalid_tex_bind(int mode);
void GPU_invalid_tex_free(void);

void GPU_texture_free(GPUTexture *tex);

void GPU_texture_ref(GPUTexture *tex);
void GPU_texture_bind(GPUTexture *tex, int number);
void GPU_texture_unbind(GPUTexture *tex);
int GPU_texture_bound_number(GPUTexture *tex);

void GPU_texture_compare_mode(GPUTexture *tex, bool use_compare);
void GPU_texture_filter_mode(GPUTexture *tex, bool use_filter);
void GPU_texture_wrap_mode(GPUTexture *tex, bool use_repeat);

struct GPUFrameBuffer *GPU_texture_framebuffer(GPUTexture *tex);
int GPU_texture_framebuffer_attachment(GPUTexture *tex);
void GPU_texture_framebuffer_set(GPUTexture *tex, struct GPUFrameBuffer *fb, int attachment);

int GPU_texture_target(const GPUTexture *tex);
int GPU_texture_width(const GPUTexture *tex);
int GPU_texture_height(const GPUTexture *tex);
int GPU_texture_depth(const GPUTexture *tex);
int GPU_texture_opengl_bindcode(const GPUTexture *tex);

#ifdef __cplusplus
}
#endif

#endif  /* __GPU_TEXTURE_H__ */
