/* SPDX-FileCopyrightText: 2021-2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache-2.0 */

CCL_NAMESPACE_BEGIN

/* For oneAPI implementation we do manual lookup and interpolation. */
/* TODO: share implementation with ../cpu/image.h. */

template<typename T> ccl_device_forceinline T tex_fetch(const TextureInfo &info, const int index)
{
  return reinterpret_cast<ccl_global T *>(info.data)[index];
}

ccl_device_inline int svm_image_texture_wrap_periodic(int x, int width)
{
  x %= width;
  if (x < 0) {
    x += width;
  }
  return x;
}

ccl_device_inline int svm_image_texture_wrap_clamp(const int x, const int width)
{
  return clamp(x, 0, width - 1);
}

ccl_device_inline int svm_image_texture_wrap_mirror(const int x, const int width)
{
  const int m = abs(x + (x < 0)) % (2 * width);
  if (m >= width) {
    return 2 * width - m - 1;
  }
  return m;
}

ccl_device_inline float4 svm_image_texture_read(const TextureInfo &info,
                                                const int x,
                                                int y,
                                                const int z)
{
  const int data_offset = x + info.width * y + info.width * info.height * z;
  const int texture_type = info.data_type;

  /* Float4 */
  if (texture_type == IMAGE_DATA_TYPE_FLOAT4) {
    return tex_fetch<float4>(info, data_offset);
  }
  /* Byte4 */
  if (texture_type == IMAGE_DATA_TYPE_BYTE4) {
    uchar4 r = tex_fetch<uchar4>(info, data_offset);
    float f = 1.0f / 255.0f;
    return make_float4(r.x * f, r.y * f, r.z * f, r.w * f);
  }
  /* Ushort4 */
  if (texture_type == IMAGE_DATA_TYPE_USHORT4) {
    ushort4 r = tex_fetch<ushort4>(info, data_offset);
    float f = 1.0f / 65535.f;
    return make_float4(r.x * f, r.y * f, r.z * f, r.w * f);
  }
  /* Float */
  if (texture_type == IMAGE_DATA_TYPE_FLOAT) {
    float f = tex_fetch<float>(info, data_offset);
    return make_float4(f, f, f, 1.0f);
  }
  /* UShort */
  if (texture_type == IMAGE_DATA_TYPE_USHORT) {
    ushort r = tex_fetch<ushort>(info, data_offset);
    float f = r * (1.0f / 65535.0f);
    return make_float4(f, f, f, 1.0f);
  }
  if (texture_type == IMAGE_DATA_TYPE_HALF) {
    float f = tex_fetch<half>(info, data_offset);
    return make_float4(f, f, f, 1.0f);
  }
  if (texture_type == IMAGE_DATA_TYPE_HALF4) {
    half4 r = tex_fetch<half4>(info, data_offset);
    return make_float4(r.x, r.y, r.z, r.w);
  }
  /* Byte */
  uchar r = tex_fetch<uchar>(info, data_offset);
  float f = r * (1.0f / 255.0f);
  return make_float4(f, f, f, 1.0f);
}

ccl_device_inline float4 svm_image_texture_read_2d(const int id, int x, int y)
{
  const TextureInfo &info = kernel_data_fetch(texture_info, id);

  /* Wrap */
  if (info.extension == EXTENSION_REPEAT) {
    x = svm_image_texture_wrap_periodic(x, info.width);
    y = svm_image_texture_wrap_periodic(y, info.height);
  }
  else if (info.extension == EXTENSION_EXTEND) {
    x = svm_image_texture_wrap_clamp(x, info.width);
    y = svm_image_texture_wrap_clamp(y, info.height);
  }
  else if (info.extension == EXTENSION_MIRROR) {
    x = svm_image_texture_wrap_mirror(x, info.width);
    y = svm_image_texture_wrap_mirror(y, info.height);
  }
  else {
    if (x < 0 || x >= info.width || y < 0 || y >= info.height) {
      return make_float4(0.0f, 0.0f, 0.0f, 0.0f);
    }
  }

  return svm_image_texture_read(info, x, y, 0);
}

ccl_device_inline float4 svm_image_texture_read_3d(const int id, int x, int y, int z)
{
  const TextureInfo &info = kernel_data_fetch(texture_info, id);

  /* Wrap */
  if (info.extension == EXTENSION_REPEAT) {
    x = svm_image_texture_wrap_periodic(x, info.width);
    y = svm_image_texture_wrap_periodic(y, info.height);
    z = svm_image_texture_wrap_periodic(z, info.depth);
  }
  else if (info.extension == EXTENSION_EXTEND) {
    x = svm_image_texture_wrap_clamp(x, info.width);
    y = svm_image_texture_wrap_clamp(y, info.height);
    z = svm_image_texture_wrap_clamp(z, info.depth);
  }
  else if (info.extension == EXTENSION_MIRROR) {
    x = svm_image_texture_wrap_mirror(x, info.width);
    y = svm_image_texture_wrap_mirror(y, info.height);
    z = svm_image_texture_wrap_mirror(z, info.depth);
  }
  else {
    if (x < 0 || x >= info.width || y < 0 || y >= info.height || z < 0 || z >= info.depth) {
      return make_float4(0.0f, 0.0f, 0.0f, 0.0f);
    }
  }

  return svm_image_texture_read(info, x, y, z);
}

static float svm_image_texture_frac(const float x, int *ix)
{
  int i = float_to_int(x) - ((x < 0.0f) ? 1 : 0);
  *ix = i;
  return x - (float)i;
}

#define SET_CUBIC_SPLINE_WEIGHTS(u, t) \
  { \
    u[0] = (((-1.0f / 6.0f) * t + 0.5f) * t - 0.5f) * t + (1.0f / 6.0f); \
    u[1] = ((0.5f * t - 1.0f) * t) * t + (2.0f / 3.0f); \
    u[2] = ((-0.5f * t + 0.5f) * t + 0.5f) * t + (1.0f / 6.0f); \
    u[3] = (1.0f / 6.0f) * t * t * t; \
  } \
  (void)0

ccl_device float4 kernel_tex_image_interp(KernelGlobals kg, const int id, float x, float y)
{
  const TextureInfo &info = kernel_data_fetch(texture_info, id);

  if (info.interpolation == INTERPOLATION_CLOSEST) {
    /* Closest interpolation. */
    int ix, iy;
    svm_image_texture_frac(x * info.width, &ix);
    svm_image_texture_frac(y * info.height, &iy);

    return svm_image_texture_read_2d(id, ix, iy);
  }
  if (info.interpolation == INTERPOLATION_LINEAR) {
    /* Bilinear interpolation. */
    int ix, iy;
    float tx = svm_image_texture_frac(x * info.width - 0.5f, &ix);
    float ty = svm_image_texture_frac(y * info.height - 0.5f, &iy);

    float4 r;
    r = (1.0f - ty) * (1.0f - tx) * svm_image_texture_read_2d(id, ix, iy);
    r += (1.0f - ty) * tx * svm_image_texture_read_2d(id, ix + 1, iy);
    r += ty * (1.0f - tx) * svm_image_texture_read_2d(id, ix, iy + 1);
    r += ty * tx * svm_image_texture_read_2d(id, ix + 1, iy + 1);
    return r;
  }
  /* Bicubic interpolation. */
  int ix, iy;
  float tx = svm_image_texture_frac(x * info.width - 0.5f, &ix);
  float ty = svm_image_texture_frac(y * info.height - 0.5f, &iy);

  float u[4], v[4];
  SET_CUBIC_SPLINE_WEIGHTS(u, tx);
  SET_CUBIC_SPLINE_WEIGHTS(v, ty);

  float4 r = make_float4(0.0f, 0.0f, 0.0f, 0.0f);

  for (int y = 0; y < 4; y++) {
    for (int x = 0; x < 4; x++) {
      float weight = u[x] * v[y];
      r += weight * svm_image_texture_read_2d(id, ix + x - 1, iy + y - 1);
    }
  }
  return r;
}

#ifdef WITH_NANOVDB
template<typename TexT, typename OutT> struct NanoVDBInterpolator {

  static ccl_always_inline float read(const float r)
  {
    return r;
  }

  static ccl_always_inline float4 read(const packed_float3 r)
  {
    return make_float4(r.x, r.y, r.z, 1.0f);
  }

  template<typename Acc>
  static ccl_always_inline OutT
  interp_3d_closest(const Acc &acc, const float x, float y, const float z)
  {
    const nanovdb::Coord coord(int32_t(rintf(x)), int32_t(rintf(y)), int32_t(rintf(z)));
    return read(acc.getValue(coord));
  }

  template<typename Acc>
  static ccl_always_inline OutT
  interp_3d_linear(const Acc &acc, const float x, float y, const float z)
  {
    int ix, iy, iz;
    const float tx = svm_image_texture_frac(x - 0.5f, &ix);
    const float ty = svm_image_texture_frac(y - 0.5f, &iy);
    const float tz = svm_image_texture_frac(z - 0.5f, &iz);

    return mix(mix(mix(read(acc.getValue(nanovdb::Coord(ix, iy, iz))),
                       read(acc.getValue(nanovdb::Coord(ix, iy, iz + 1))),
                       tz),
                   mix(read(acc.getValue(nanovdb::Coord(ix, iy + 1, iz + 1))),
                       read(acc.getValue(nanovdb::Coord(ix, iy + 1, iz))),
                       1.0f - tz),
                   ty),
               mix(mix(read(acc.getValue(nanovdb::Coord(ix + 1, iy + 1, iz))),
                       read(acc.getValue(nanovdb::Coord(ix + 1, iy + 1, iz + 1))),
                       tz),
                   mix(read(acc.getValue(nanovdb::Coord(ix + 1, iy, iz + 1))),
                       read(acc.getValue(nanovdb::Coord(ix + 1, iy, iz))),
                       1.0f - tz),
                   1.0f - ty),
               tx);
  }

  /* Tricubic b-spline interpolation. */
  template<typename Acc>
  static ccl_always_inline OutT
  interp_3d_cubic(const Acc &acc, const float x, float y, const float z)
  {
    int ix, iy, iz;
    int nix, niy, niz;
    int pix, piy, piz;
    int nnix, nniy, nniz;

    /* A -0.5 offset is used to center the cubic samples around the sample point. */
    const float tx = svm_image_texture_frac(x - 0.5f, &ix);
    const float ty = svm_image_texture_frac(y - 0.5f, &iy);
    const float tz = svm_image_texture_frac(z - 0.5f, &iz);

    pix = ix - 1;
    piy = iy - 1;
    piz = iz - 1;
    nix = ix + 1;
    niy = iy + 1;
    niz = iz + 1;
    nnix = ix + 2;
    nniy = iy + 2;
    nniz = iz + 2;

    const int xc[4] = {pix, ix, nix, nnix};
    const int yc[4] = {piy, iy, niy, nniy};
    const int zc[4] = {piz, iz, niz, nniz};
    float u[4], v[4], w[4];

    /* Some helper macros to keep code size reasonable.
     * Lets the compiler inline all the matrix multiplications.
     */
#  define DATA(x, y, z) (read(acc.getValue(nanovdb::Coord(xc[x], yc[y], zc[z]))))
#  define COL_TERM(col, row) \
    (v[col] * (u[0] * DATA(0, col, row) + u[1] * DATA(1, col, row) + u[2] * DATA(2, col, row) + \
               u[3] * DATA(3, col, row)))
#  define ROW_TERM(row) \
    (w[row] * (COL_TERM(0, row) + COL_TERM(1, row) + COL_TERM(2, row) + COL_TERM(3, row)))

    SET_CUBIC_SPLINE_WEIGHTS(u, tx);
    SET_CUBIC_SPLINE_WEIGHTS(v, ty);
    SET_CUBIC_SPLINE_WEIGHTS(w, tz);

    /* Actual interpolation. */
    return ROW_TERM(0) + ROW_TERM(1) + ROW_TERM(2) + ROW_TERM(3);

#  undef COL_TERM
#  undef ROW_TERM
#  undef DATA
  }

  static ccl_always_inline OutT
  interp_3d(const TextureInfo &info, const float x, float y, const float z, const int interp)
  {
    using namespace nanovdb;

    NanoGrid<TexT> *const grid = (NanoGrid<TexT> *)info.data;

    switch (interp) {
      case INTERPOLATION_CLOSEST: {
        ReadAccessor<TexT> acc(grid->tree().root());
        return interp_3d_closest(acc, x, y, z);
      }
      case INTERPOLATION_LINEAR: {
        CachedReadAccessor<TexT> acc(grid->tree().root());
        return interp_3d_linear(acc, x, y, z);
      }
      default: {
        CachedReadAccessor<TexT> acc(grid->tree().root());
        return interp_3d_cubic(acc, x, y, z);
      }
    }
  }
};
#endif /* WITH_NANOVDB */

ccl_device float4 kernel_tex_image_interp_3d(KernelGlobals kg,
                                             const int id,
                                             float3 P,
                                             const int interp)
{
  const TextureInfo &info = kernel_data_fetch(texture_info, id);

  if (info.use_transform_3d) {
    Transform tfm = info.transform_3d;
    P = transform_point(&tfm, P);
  }

  float x = P.x;
  float y = P.y;
  float z = P.z;

  uint interpolation = (interp == INTERPOLATION_NONE) ? info.interpolation : interp;

#ifdef WITH_NANOVDB
  if (info.data_type == IMAGE_DATA_TYPE_NANOVDB_FLOAT) {
    const float f = NanoVDBInterpolator<float, float>::interp_3d(info, x, y, z, interpolation);
    return make_float4(f, f, f, 1.0f);
  }
  if (info.data_type == IMAGE_DATA_TYPE_NANOVDB_FLOAT3) {
    return NanoVDBInterpolator<packed_float3, float4>::interp_3d(info, x, y, z, interpolation);
  }
  if (info.data_type == IMAGE_DATA_TYPE_NANOVDB_FPN) {
    const float f = NanoVDBInterpolator<nanovdb::FpN, float>::interp_3d(
        info, x, y, z, interpolation);
    return make_float4(f, f, f, 1.0f);
  }
  if (info.data_type == IMAGE_DATA_TYPE_NANOVDB_FP16) {
    const float f = NanoVDBInterpolator<nanovdb::Fp16, float>::interp_3d(
        info, x, y, z, interpolation);
    return make_float4(f, f, f, 1.0f);
  }
#else
  if (info.data_type == IMAGE_DATA_TYPE_NANOVDB_FLOAT ||
      info.data_type == IMAGE_DATA_TYPE_NANOVDB_FLOAT3 ||
      info.data_type == IMAGE_DATA_TYPE_NANOVDB_FPN ||
      info.data_type == IMAGE_DATA_TYPE_NANOVDB_FP16)
  {
    return make_float4(
        TEX_IMAGE_MISSING_R, TEX_IMAGE_MISSING_G, TEX_IMAGE_MISSING_B, TEX_IMAGE_MISSING_A);
  }
#endif
  else {
    x *= info.width;
    y *= info.height;
    z *= info.depth;
  }

  if (interpolation == INTERPOLATION_CLOSEST) {
    /* Closest interpolation. */
    int ix, iy, iz;
    svm_image_texture_frac(x, &ix);
    svm_image_texture_frac(y, &iy);
    svm_image_texture_frac(z, &iz);

    return svm_image_texture_read_3d(id, ix, iy, iz);
  }
  if (interpolation == INTERPOLATION_LINEAR) {
    /* Trilinear interpolation. */
    int ix, iy, iz;
    float tx = svm_image_texture_frac(x - 0.5f, &ix);
    float ty = svm_image_texture_frac(y - 0.5f, &iy);
    float tz = svm_image_texture_frac(z - 0.5f, &iz);

    float4 r;
    r = (1.0f - tz) * (1.0f - ty) * (1.0f - tx) * svm_image_texture_read_3d(id, ix, iy, iz);
    r += (1.0f - tz) * (1.0f - ty) * tx * svm_image_texture_read_3d(id, ix + 1, iy, iz);
    r += (1.0f - tz) * ty * (1.0f - tx) * svm_image_texture_read_3d(id, ix, iy + 1, iz);
    r += (1.0f - tz) * ty * tx * svm_image_texture_read_3d(id, ix + 1, iy + 1, iz);

    r += tz * (1.0f - ty) * (1.0f - tx) * svm_image_texture_read_3d(id, ix, iy, iz + 1);
    r += tz * (1.0f - ty) * tx * svm_image_texture_read_3d(id, ix + 1, iy, iz + 1);
    r += tz * ty * (1.0f - tx) * svm_image_texture_read_3d(id, ix, iy + 1, iz + 1);
    r += tz * ty * tx * svm_image_texture_read_3d(id, ix + 1, iy + 1, iz + 1);
    return r;
  }
  /* Tri-cubic interpolation. */
  int ix, iy, iz;
  float tx = svm_image_texture_frac(x - 0.5f, &ix);
  float ty = svm_image_texture_frac(y - 0.5f, &iy);
  float tz = svm_image_texture_frac(z - 0.5f, &iz);

  float u[4], v[4], w[4];
  SET_CUBIC_SPLINE_WEIGHTS(u, tx);
  SET_CUBIC_SPLINE_WEIGHTS(v, ty);
  SET_CUBIC_SPLINE_WEIGHTS(w, tz);

  float4 r = make_float4(0.0f, 0.0f, 0.0f, 0.0f);

  for (int z = 0; z < 4; z++) {
    for (int y = 0; y < 4; y++) {
      for (int x = 0; x < 4; x++) {
        float weight = u[x] * v[y] * w[z];
        r += weight * svm_image_texture_read_3d(id, ix + x - 1, iy + y - 1, iz + z - 1);
      }
    }
  }
  return r;
}

#undef SET_CUBIC_SPLINE_WEIGHTS

CCL_NAMESPACE_END
