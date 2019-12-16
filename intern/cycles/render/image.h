/*
 * Copyright 2011-2013 Blender Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef __IMAGE_H__
#define __IMAGE_H__

#include "device/device.h"
#include "device/device_memory.h"

#include "render/colorspace.h"

#include "util/util_image.h"
#include "util/util_string.h"
#include "util/util_thread.h"
#include "util/util_unique_ptr.h"
#include "util/util_vector.h"

CCL_NAMESPACE_BEGIN

class Device;
class Progress;
class RenderStats;
class Scene;
class ColorSpaceProcessor;

class ImageMetaData {
 public:
  /* Must be set by image file or builtin callback. */
  bool is_float, is_half;
  int channels;
  size_t width, height, depth;
  bool builtin_free_cache;

  /* Automatically set. */
  ImageDataType type;
  ustring colorspace;
  bool compress_as_srgb;

  ImageMetaData()
      : is_float(false),
        is_half(false),
        channels(0),
        width(0),
        height(0),
        depth(0),
        builtin_free_cache(false),
        type((ImageDataType)0),
        colorspace(u_colorspace_raw),
        compress_as_srgb(false)
  {
  }

  bool operator==(const ImageMetaData &other) const
  {
    return is_float == other.is_float && is_half == other.is_half && channels == other.channels &&
           width == other.width && height == other.height && depth == other.depth &&
           type == other.type && colorspace == other.colorspace &&
           compress_as_srgb == other.compress_as_srgb;
  }
};

class ImageManager {
 public:
  explicit ImageManager(const DeviceInfo &info);
  ~ImageManager();

  int add_image(const string &filename,
                void *builtin_data,
                bool animated,
                float frame,
                InterpolationType interpolation,
                ExtensionType extension,
                ImageAlphaType alpha_type,
                ustring colorspace,
                ImageMetaData &metadata);
  void add_image_user(int flat_slot);
  void remove_image(int flat_slot);
  void remove_image(const string &filename,
                    void *builtin_data,
                    InterpolationType interpolation,
                    ExtensionType extension,
                    ImageAlphaType alpha_type,
                    ustring colorspace);
  void tag_reload_image(const string &filename,
                        void *builtin_data,
                        InterpolationType interpolation,
                        ExtensionType extension,
                        ImageAlphaType alpha_type,
                        ustring colorspace);
  bool get_image_metadata(const string &filename,
                          void *builtin_data,
                          ustring colorspace,
                          ImageMetaData &metadata);
  bool get_image_metadata(int flat_slot, ImageMetaData &metadata);

  void device_update(Device *device, Scene *scene, Progress &progress);
  void device_update_slot(Device *device, Scene *scene, int flat_slot, Progress *progress);
  void device_free(Device *device);

  void device_load_builtin(Device *device, Scene *scene, Progress &progress);
  void device_free_builtin(Device *device);

  void set_osl_texture_system(void *texture_system);
  bool set_animation_frame_update(int frame);

  device_memory *image_memory(int flat_slot);

  void collect_statistics(RenderStats *stats);

  bool need_update;

  /* NOTE: Here pixels_size is a size of storage, which equals to
   *       width * height * depth.
   *       Use this to avoid some nasty memory corruptions.
   */
  function<void(const string &filename, void *data, ImageMetaData &metadata)>
      builtin_image_info_cb;
  function<bool(const string &filename,
                void *data,
                int tile,
                unsigned char *pixels,
                const size_t pixels_size,
                const bool associate_alpha,
                const bool free_cache)>
      builtin_image_pixels_cb;
  function<bool(const string &filename,
                void *data,
                int tile,
                float *pixels,
                const size_t pixels_size,
                const bool associate_alpha,
                const bool free_cache)>
      builtin_image_float_pixels_cb;

  struct Image {
    string filename;
    void *builtin_data;
    ImageMetaData metadata;

    ustring colorspace;
    ImageAlphaType alpha_type;
    bool need_load;
    bool animated;
    float frame;
    InterpolationType interpolation;
    ExtensionType extension;

    string mem_name;
    device_memory *mem;

    int users;
  };

 private:
  int tex_num_images[IMAGE_DATA_NUM_TYPES];
  int max_num_images;
  bool has_half_images;

  thread_mutex device_mutex;
  int animation_frame;

  vector<Image *> images[IMAGE_DATA_NUM_TYPES];
  void *osl_texture_system;

  bool file_load_image_generic(Image *img, unique_ptr<ImageInput> *in);

  template<TypeDesc::BASETYPE FileFormat, typename StorageType, typename DeviceType>
  bool file_load_image(Image *img,
                       ImageDataType type,
                       int texture_limit,
                       device_vector<DeviceType> &tex_img);

  void metadata_detect_colorspace(ImageMetaData &metadata, const char *file_format);

  void device_load_image(
      Device *device, Scene *scene, ImageDataType type, int slot, Progress *progress);
  void device_free_image(Device *device, ImageDataType type, int slot);
};

CCL_NAMESPACE_END

#endif /* __IMAGE_H__ */
