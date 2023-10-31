/* SPDX-FileCopyrightText: 2022-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/**
 * Convert hit list to occupancy bit-field for the material pass.
 */

#pragma BLENDER_REQUIRE(eevee_occupancy_lib.glsl)

bool is_front_face_hit(float stored_hit_depth)
{
  return stored_hit_depth < 0.0;
}

void main()
{
  float hit_depths[VOLUME_HIT_DEPTH_MAX];
  float hit_ordered[VOLUME_HIT_DEPTH_MAX];
  int hit_index[VOLUME_HIT_DEPTH_MAX];

  ivec2 texel = ivec2(gl_FragCoord.xy);

  int hit_count = int(imageLoad(hit_count_img, texel).x);
  hit_count = min(hit_count, VOLUME_HIT_DEPTH_MAX);

  if (hit_count == 0) {
    return;
  }

  /* Clear the texture for next layer / frame. */
  imageStore(hit_count_img, texel, uvec4(0));

  for (int i = 0; i < hit_count; i++) {
    hit_depths[i] = imageLoad(hit_depth_img, ivec3(texel, i)).r;
  }

  for (int i = 0; i < hit_count; i++) {
    hit_index[i] = 0;
    for (int j = 0; j < hit_count; j++) {
      hit_index[i] += int(abs(hit_depths[i]) > abs(hit_depths[j]));
    }
  }

  for (int i = 0; i < hit_count; i++) {
    hit_ordered[hit_index[i]] = hit_depths[i];
  }

#if 0 /* Debug. Need to adjust the qualifier of the texture adjusted. */
  for (int i = 0; i < hit_count; i++) {
    imageStore(hit_depth_img, ivec3(texel, i), vec4(hit_ordered[i]));
  }
#endif

  /* Convert to occupancy bits. */
  OccupancyBits occupancy = occupancy_new();
  /* True if last interface was a volume entry. */
  /* Initialized to front facing if first hit is a backface to support camera inside the volume. */
  bool last_frontfacing = !is_front_face_hit(hit_ordered[0]);
  /* Bit index of the last interface. */
  int last_bit = 0;
  for (int i = 0; i < hit_count; i++) {
    bool frontfacing = is_front_face_hit(hit_ordered[i]);
    if (last_frontfacing == frontfacing) {
      /* Same facing, do not treat as a volume interface. */
      continue;
    }
    last_frontfacing = frontfacing;

    int occupancy_bit_n = occupancy_bit_index_from_depth(abs(hit_ordered[i]),
                                                         uniform_buf.volumes.tex_size.z);
    if (last_bit == occupancy_bit_n) {
      /* We did not cross a new voxel center. Do nothing. */
      continue;
    }
    int bit_start = last_bit;
    int bit_count = occupancy_bit_n - last_bit;
    last_bit = occupancy_bit_n;

    if (last_frontfacing == false) {
      /* OccupancyBits is cleared by default. No need to do anything for empty regions. */
      continue;
    }
    occupancy = occupancy_set_bits_high(occupancy, bit_start, bit_count);
  }

  /* Write the occupancy bits */
  for (int i = 0; i < imageSize(occupancy_img).z; i++) {
    if (occupancy.bits[i] != 0u) {
      /* Note: Doesn't have to be atomic but we need to blend with other method. */
      imageAtomicOr(occupancy_img, ivec3(texel, i), occupancy.bits[i]);
    }
  }
}
