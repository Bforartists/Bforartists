/* SPDX-FileCopyrightText: 2007 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edsnd
 */

#include <cstddef>
#include <cstdlib>
#include <cstring>

#include "MEM_guardedalloc.h"

#include "BLI_listbase.h"
#include "BLI_path_utils.hh"
#include "BLI_string.h"
#include "BLI_utildefines.h"

#include "DNA_scene_types.h"
#include "DNA_sequence_types.h"
#include "DNA_sound_types.h"
#include "DNA_space_types.h"

#include "BKE_context.hh"
#include "BKE_fcurve.hh"
#include "BKE_global.hh"
#include "BKE_lib_id.hh"
#include "BKE_library.hh"
#include "BKE_main.hh"
#include "BKE_packedFile.hh"
#include "BKE_report.hh"
#include "BKE_scene.hh"
#include "BKE_sound.h"

#include "RNA_access.hh"
#include "RNA_define.hh"
#include "RNA_enum_types.hh"
#include "RNA_prototypes.hh"

#include "SEQ_iterator.hh"

#include "UI_interface.hh"
#include "UI_interface_layout.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#ifdef WITH_AUDASPACE
#  include <AUD_Special.h>
#endif

#include "DEG_depsgraph_query.hh"

#include "ED_sound.hh"
#include "ED_util.hh"

/******************** open sound operator ********************/

static void sound_open_cancel(bContext * /*C*/, wmOperator *op)
{
  MEM_delete(static_cast<PropertyPointerRNA *>(op->customdata));
  op->customdata = nullptr;
}

static void sound_open_init(bContext *C, wmOperator *op)
{
  PropertyPointerRNA *pprop;

  op->customdata = pprop = MEM_new<PropertyPointerRNA>(__func__);
  UI_context_active_but_prop_get_templateID(C, &pprop->ptr, &pprop->prop);
}

#ifdef WITH_AUDASPACE
static wmOperatorStatus sound_open_exec(bContext *C, wmOperator *op)
{
  char filepath[FILE_MAX];
  bSound *sound;
  PropertyPointerRNA *pprop;
  Main *bmain = CTX_data_main(C);

  RNA_string_get(op->ptr, "filepath", filepath);
  sound = BKE_sound_new_file(bmain, filepath);

  if (!op->customdata) {
    sound_open_init(C, op);
  }

  if (RNA_boolean_get(op->ptr, "mono")) {
    sound->flags |= SOUND_FLAGS_MONO;
  }

  if (RNA_boolean_get(op->ptr, "cache")) {
    sound->flags |= SOUND_FLAGS_CACHING;
  }

  /* hook into UI */
  pprop = static_cast<PropertyPointerRNA *>(op->customdata);

  if (pprop->prop) {
    /* when creating new ID blocks, use is already 1, but RNA
     * pointer use also increases user, so this compensates it */
    id_us_min(&sound->id);

    PointerRNA idptr = RNA_id_pointer_create(&sound->id);
    RNA_property_pointer_set(&pprop->ptr, pprop->prop, idptr, nullptr);
    RNA_property_update(C, &pprop->ptr, pprop->prop);
  }

  DEG_relations_tag_update(bmain);

  MEM_delete(pprop);
  return OPERATOR_FINISHED;
}

#else /* WITH_AUDASPACE */

static wmOperatorStatus sound_open_exec(bContext * /*C*/, wmOperator *op)
{
  BKE_report(op->reports, RPT_ERROR, "Compiled without sound support");

  return OPERATOR_CANCELLED;
}

#endif

static wmOperatorStatus sound_open_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
  if (RNA_struct_property_is_set(op->ptr, "filepath")) {
    return sound_open_exec(C, op);
  }

  sound_open_init(C, op);

  return WM_operator_filesel(C, op, event);
}

static void SOUND_OT_open(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Open Sound";
  ot->description = "Load a sound file";
  ot->idname = "SOUND_OT_open";

  /* API callbacks. */
  ot->exec = sound_open_exec;
  ot->invoke = sound_open_invoke;
  ot->cancel = sound_open_cancel;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* properties */
  WM_operator_properties_filesel(ot,
                                 FILE_TYPE_FOLDER | FILE_TYPE_SOUND | FILE_TYPE_MOVIE,
                                 FILE_SPECIAL,
                                 FILE_OPENFILE,
                                 WM_FILESEL_FILEPATH | WM_FILESEL_RELPATH,
                                 FILE_DEFAULTDISPLAY,
                                 FILE_SORT_DEFAULT);
  RNA_def_boolean(ot->srna, "cache", false, "Cache", "Cache the sound in memory");
  RNA_def_boolean(ot->srna, "mono", false, "Mono", "Merge all the sound's channels into one");
}

static void SOUND_OT_open_mono(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Open Sound Mono";
  ot->description = "Load a sound file as mono";
  ot->idname = "SOUND_OT_open_mono";

  /* API callbacks. */
  ot->exec = sound_open_exec;
  ot->invoke = sound_open_invoke;
  ot->cancel = sound_open_cancel;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* properties */
  WM_operator_properties_filesel(ot,
                                 FILE_TYPE_FOLDER | FILE_TYPE_SOUND | FILE_TYPE_MOVIE,
                                 FILE_SPECIAL,
                                 FILE_OPENFILE,
                                 WM_FILESEL_FILEPATH | WM_FILESEL_RELPATH,
                                 FILE_DEFAULTDISPLAY,
                                 FILE_SORT_DEFAULT);
  RNA_def_boolean(ot->srna, "cache", false, "Cache", "Cache the sound in memory");
  RNA_def_boolean(ot->srna, "mono", true, "Mono", "Mixdown the sound to mono");
}

/* ******************************************************* */

static void sound_update_animation_flags(Scene *scene);

static bool sound_update_animation_flags_fn(Strip *strip, void *user_data)
{
  const FCurve *fcu;
  Scene *scene = (Scene *)user_data;
  bool driven;

  fcu = id_data_find_fcurve(&scene->id, strip, &RNA_Strip, "volume", 0, &driven);
  if (fcu || driven) {
    strip->flag |= SEQ_AUDIO_VOLUME_ANIMATED;
  }
  else {
    strip->flag &= ~SEQ_AUDIO_VOLUME_ANIMATED;
  }

  fcu = id_data_find_fcurve(&scene->id, strip, &RNA_Strip, "pitch", 0, &driven);
  if (fcu || driven) {
    strip->flag |= SEQ_AUDIO_PITCH_ANIMATED;
  }
  else {
    strip->flag &= ~SEQ_AUDIO_PITCH_ANIMATED;
  }

  fcu = id_data_find_fcurve(&scene->id, strip, &RNA_Strip, "pan", 0, &driven);
  if (fcu || driven) {
    strip->flag |= SEQ_AUDIO_PAN_ANIMATED;
  }
  else {
    strip->flag &= ~SEQ_AUDIO_PAN_ANIMATED;
  }

  if (strip->type == STRIP_TYPE_SCENE) {
    /* TODO(sergey): For now we do manual recursion into the scene strips,
     * but perhaps it should be covered by recursive_apply?
     */
    sound_update_animation_flags(strip->scene);
  }

  return true;
}

static void sound_update_animation_flags(Scene *scene)
{
  const FCurve *fcu;
  bool driven;

  if (scene->id.tag & ID_TAG_DOIT) {
    return;
  }
  scene->id.tag |= ID_TAG_DOIT;

  if (scene->ed != nullptr) {
    blender::seq::for_each_callback(&scene->ed->seqbase, sound_update_animation_flags_fn, scene);
  }

  fcu = id_data_find_fcurve(&scene->id, scene, &RNA_Scene, "audio_volume", 0, &driven);
  if (fcu || driven) {
    scene->audio.flag |= AUDIO_VOLUME_ANIMATED;
  }
  else {
    scene->audio.flag &= ~AUDIO_VOLUME_ANIMATED;
  }
}

static wmOperatorStatus sound_update_animation_flags_exec(bContext *C, wmOperator * /*op*/)
{
  Scene *scene = CTX_data_scene(C);

  BKE_main_id_tag_idcode(CTX_data_main(C), ID_SCE, ID_TAG_DOIT, false);
  sound_update_animation_flags(CTX_data_scene(C));
  DEG_id_tag_update(&scene->id, ID_RECALC_SEQUENCER_STRIPS);
  return OPERATOR_FINISHED;
}

static void SOUND_OT_update_animation_flags(wmOperatorType *ot)
{
  /*
   * This operator is needed to set a correct state of the sound animation
   * System. Unfortunately there's no really correct place to call the exec
   * function, that's why I made it an operator that's only visible in the
   * search menu. Apart from that the bake animation operator calls it too.
   */

  /* identifiers */
  ot->name = "Update Animation";
  ot->description = "Update animation flags";
  ot->idname = "SOUND_OT_update_animation_flags";

  /* API callbacks. */
  ot->exec = sound_update_animation_flags_exec;

  /* flags */
  ot->flag = OPTYPE_REGISTER;
}

/* ******************************************************* */

static wmOperatorStatus sound_bake_animation_exec(bContext *C, wmOperator * /*op*/)
{
  Scene *scene = CTX_data_scene(C);
  /* NOTE: We will be forcefully evaluating dependency graph at every frame, so no need to ensure
   * current scene state is evaluated as it will be lost anyway. */
  Depsgraph *depsgraph = CTX_data_depsgraph_pointer(C);
  int oldfra = scene->r.cfra;
  int cfra;

  sound_update_animation_flags_exec(C, nullptr);

  for (cfra = (scene->r.sfra > 0) ? (scene->r.sfra - 1) : 0; cfra <= scene->r.efra + 1; cfra++) {
    scene->r.cfra = cfra;
    /* Make sure the camera is updated, since it will affect stereo/surround output. */
    BKE_scene_camera_switch_update(scene);
    BKE_scene_graph_update_for_newframe(depsgraph);
  }

  scene->r.cfra = oldfra;
  BKE_scene_graph_update_for_newframe(depsgraph);

  return OPERATOR_FINISHED;
}

static void SOUND_OT_bake_animation(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Update Animation Cache";
  ot->description = "Update the audio animation cache";
  ot->idname = "SOUND_OT_bake_animation";

  /* API callbacks. */
  ot->exec = sound_bake_animation_exec;

  /* flags */
  ot->flag = OPTYPE_REGISTER;
}

/******************** mixdown operator ********************/

static wmOperatorStatus sound_mixdown_exec(bContext *C, wmOperator *op)
{
#ifdef WITH_AUDASPACE
  char filepath[FILE_MAX];
  Depsgraph *depsgraph = CTX_data_ensure_evaluated_depsgraph(C);
  Scene *scene_eval = DEG_get_evaluated_scene(depsgraph);
  Main *bmain = CTX_data_main(C);
  int split;

  int bitrate, accuracy;
  AUD_DeviceSpecs specs;
  AUD_Container container;
  AUD_Codec codec;
  int result;
  char error_message[1024] = {'\0'};

  sound_bake_animation_exec(C, op);

  RNA_string_get(op->ptr, "filepath", filepath);
  bitrate = RNA_int_get(op->ptr, "bitrate") * 1000;
  accuracy = RNA_int_get(op->ptr, "accuracy");
  specs.format = AUD_SampleFormat(RNA_enum_get(op->ptr, "format"));
  container = AUD_Container(RNA_enum_get(op->ptr, "container"));
  codec = AUD_Codec(RNA_enum_get(op->ptr, "codec"));
  split = RNA_boolean_get(op->ptr, "split_channels");
  specs.channels = AUD_Channels(RNA_enum_get(op->ptr, "channels"));
  specs.rate = RNA_int_get(op->ptr, "mixrate");

  BLI_path_abs(filepath, BKE_main_blendfile_path(bmain));

  const double fps = double(scene_eval->r.frs_sec) / double(scene_eval->r.frs_sec_base);
  const int start_frame = scene_eval->r.sfra;
  const int end_frame = scene_eval->r.efra;

  if (split) {
    result = AUD_mixdown_per_channel(scene_eval->sound_scene,
                                     start_frame * specs.rate / fps,
                                     (end_frame - start_frame + 1) * specs.rate / fps,
                                     accuracy,
                                     filepath,
                                     specs,
                                     container,
                                     codec,
                                     bitrate,
                                     AUD_RESAMPLE_QUALITY_MEDIUM,
                                     nullptr,
                                     nullptr,
                                     error_message,
                                     sizeof(error_message));
  }
  else {
    result = AUD_mixdown(scene_eval->sound_scene,
                         start_frame * specs.rate / fps,
                         (end_frame - start_frame + 1) * specs.rate / fps,
                         accuracy,
                         filepath,
                         specs,
                         container,
                         codec,
                         bitrate,
                         AUD_RESAMPLE_QUALITY_MEDIUM,
                         nullptr,
                         nullptr,
                         error_message,
                         sizeof(error_message));
  }

  BKE_sound_reset_scene_specs(scene_eval);

  if (!result) {
    BKE_report(op->reports, RPT_ERROR, error_message);
    return OPERATOR_CANCELLED;
  }
#else  /* WITH_AUDASPACE */
  (void)C;
  (void)op;
#endif /* WITH_AUDASPACE */
  return OPERATOR_FINISHED;
}

#ifdef WITH_AUDASPACE
static const EnumPropertyItem container_items[] = {
#  ifdef WITH_FFMPEG
    {AUD_CONTAINER_AAC, "AAC", 0, "AAC", "Advanced Audio Coding"},
    {AUD_CONTAINER_AC3, "AC3", 0, "AC3", "Dolby Digital ATRAC 3"},
#  endif
    {AUD_CONTAINER_FLAC, "FLAC", 0, "FLAC", "Free Lossless Audio Codec"},
#  ifdef WITH_FFMPEG
    {AUD_CONTAINER_MATROSKA, "MATROSKA", 0, "MKV", "Matroska"},
    {AUD_CONTAINER_MP2, "MP2", 0, "MP2", "MPEG-1 Audio Layer II"},
    {AUD_CONTAINER_MP3, "MP3", 0, "MP3", "MPEG-2 Audio Layer III"},
#  endif
    {AUD_CONTAINER_OGG, "OGG", 0, "OGG", "Xiph.Org Ogg Container"},
    {AUD_CONTAINER_WAV, "WAV", 0, "WAV", "Waveform Audio File Format"},
    {0, nullptr, 0, nullptr, nullptr},
};

static const char *snd_ext_sound[] = {
    ".ac3",
    ".flac",
    ".mkv",
    ".mp2",
    ".mp3",
    ".ogg",
    ".wav",
    ".aac",
    nullptr,
};

static bool sound_mixdown_check(bContext * /*C*/, wmOperator *op)
{
  AUD_Container container = AUD_Container(RNA_enum_get(op->ptr, "container"));

  const char *extension = nullptr;

  const EnumPropertyItem *item = container_items;
  while (item->identifier != nullptr) {
    if (item->value == container) {
      const char **ext = snd_ext_sound;
      while (*ext != nullptr) {
        if (STRCASEEQ(*ext + 1, item->name)) {
          extension = *ext;
          break;
        }

        ext++;
      }
    }
    item++;
  }

  if (extension) {
    PropertyRNA *prop;
    char filepath[FILE_MAX];

    int check;

    prop = RNA_struct_find_property(op->ptr, "filepath");
    RNA_property_string_get(op->ptr, prop, filepath);

    if (BLI_path_extension_check_array(filepath, snd_ext_sound)) {
      check = BLI_path_extension_replace(filepath, FILE_MAX, extension);
    }
    else {
      check = BLI_path_extension_ensure(filepath, FILE_MAX, extension);
    }

    if (!check) {
      return check;
    }

    RNA_property_string_set(op->ptr, prop, filepath);
    return true;
  }

  return false;
}

#endif /* WITH_AUDASPACE */

static wmOperatorStatus sound_mixdown_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
  if (RNA_struct_property_is_set(op->ptr, "filepath")) {
    return sound_mixdown_exec(C, op);
  }

  return WM_operator_filesel(C, op, event);
}

#ifdef WITH_AUDASPACE

static bool sound_mixdown_draw_check_prop(PointerRNA * /*ptr*/,
                                          PropertyRNA *prop,
                                          void * /*user_data*/)
{
  const char *prop_id = RNA_property_identifier(prop);
  return !STR_ELEM(prop_id, "filepath", "directory", "filename");
}

static void sound_mixdown_draw(bContext *C, wmOperator *op)
{
  static const EnumPropertyItem pcm_format_items[] = {
      {AUD_FORMAT_U8, "U8", 0, "U8", "8-bit unsigned"},
      {AUD_FORMAT_S16, "S16", 0, "S16", "16-bit signed"},
#  ifdef WITH_SNDFILE
      {AUD_FORMAT_S24, "S24", 0, "S24", "24-bit signed"},
#  endif
      {AUD_FORMAT_S32, "S32", 0, "S32", "32-bit signed"},
      {AUD_FORMAT_FLOAT32, "F32", 0, "F32", "32-bit floating-point"},
      {AUD_FORMAT_FLOAT64, "F64", 0, "F64", "64-bit floating-point"},
      {0, nullptr, 0, nullptr, nullptr},
  };

  static const EnumPropertyItem mp3_format_items[] = {
      {AUD_FORMAT_S16, "S16", 0, "S16", "16-bit signed"},
      {AUD_FORMAT_S32, "S32", 0, "S32", "32-bit signed"},
      {0, nullptr, 0, nullptr, nullptr},
  };

#  ifdef WITH_SNDFILE
  static const EnumPropertyItem flac_format_items[] = {
      {AUD_FORMAT_S16, "S16", 0, "S16", "16-bit signed"},
      {AUD_FORMAT_S24, "S24", 0, "S24", "24-bit signed"},
      {0, nullptr, 0, nullptr, nullptr},
  };
#  endif

  static const EnumPropertyItem all_codec_items[] = {
      {AUD_CODEC_AAC, "AAC", 0, "AAC", "Advanced Audio Coding"},
      {AUD_CODEC_AC3, "AC3", 0, "AC3", "Dolby Digital ATRAC 3"},
      {AUD_CODEC_FLAC, "FLAC", 0, "FLAC", "Free Lossless Audio Codec"},
      {AUD_CODEC_MP2, "MP2", 0, "MP2", "MPEG-1 Audio Layer II"},
      {AUD_CODEC_MP3, "MP3", 0, "MP3", "MPEG-2 Audio Layer III"},
      {AUD_CODEC_PCM, "PCM", 0, "PCM", "Pulse Code Modulation (RAW)"},
      {AUD_CODEC_OPUS, "OPUS", 0, "Opus", "Opus Interactive Audio Codec"},
      {AUD_CODEC_VORBIS, "VORBIS", 0, "Vorbis", "Xiph.Org Vorbis Codec"},
      {0, nullptr, 0, nullptr, nullptr},
  };

  static const EnumPropertyItem ogg_codec_items[] = {
      {AUD_CODEC_FLAC, "FLAC", 0, "FLAC", "Free Lossless Audio Codec"},
      {AUD_CODEC_OPUS, "OPUS", 0, "Opus", "Opus Interactive Audio Codec"},
      {AUD_CODEC_VORBIS, "VORBIS", 0, "Vorbis", "Xiph.Org Vorbis Codec"},
      {0, nullptr, 0, nullptr, nullptr},
  };

  uiLayout *layout = op->layout;
  wmWindowManager *wm = CTX_wm_manager(C);
  PropertyRNA *prop_format;
  PropertyRNA *prop_codec;
  PropertyRNA *prop_bitrate;

  layout->use_property_split_set(true);
  layout->use_property_decorate_set(false);

  AUD_Container container = AUD_Container(RNA_enum_get(op->ptr, "container"));
  AUD_Codec codec = AUD_Codec(RNA_enum_get(op->ptr, "codec"));

  prop_format = RNA_struct_find_property(op->ptr, "format");
  prop_codec = RNA_struct_find_property(op->ptr, "codec");
  prop_bitrate = RNA_struct_find_property(op->ptr, "bitrate");

  RNA_def_property_clear_flag(prop_bitrate, PROP_HIDDEN);
  RNA_def_property_flag(prop_codec, PROP_HIDDEN);
  RNA_def_property_flag(prop_format, PROP_HIDDEN);

  switch (container) {
    case AUD_CONTAINER_AAC:
      RNA_def_property_enum_items(prop_codec, all_codec_items);
      RNA_enum_set(op->ptr, "codec", AUD_CODEC_AAC);
      RNA_enum_set(op->ptr, "format", AUD_FORMAT_FLOAT32);
      break;
    case AUD_CONTAINER_AC3:
      RNA_def_property_enum_items(prop_codec, all_codec_items);
      RNA_enum_set(op->ptr, "codec", AUD_CODEC_AC3);
      RNA_enum_set(op->ptr, "format", AUD_FORMAT_FLOAT32);
      break;
    case AUD_CONTAINER_FLAC:
      RNA_def_property_flag(prop_bitrate, PROP_HIDDEN);
      RNA_def_property_enum_items(prop_codec, all_codec_items);
      RNA_enum_set(op->ptr, "codec", AUD_CODEC_FLAC);
#  ifdef WITH_SNDFILE
      RNA_def_property_clear_flag(prop_format, PROP_HIDDEN);
      RNA_def_property_enum_items(prop_format, flac_format_items);
#  else
      RNA_enum_set(op->ptr, "format", AUD_FORMAT_S16);
#  endif
      break;
    case AUD_CONTAINER_MATROSKA:
      RNA_def_property_clear_flag(prop_codec, PROP_HIDDEN);
      RNA_def_property_enum_items(prop_codec, all_codec_items);

      switch (codec) {
        case AUD_CODEC_AAC:
          RNA_enum_set(op->ptr, "format", AUD_FORMAT_S16);
          break;
        case AUD_CODEC_AC3:
          RNA_enum_set(op->ptr, "format", AUD_FORMAT_FLOAT32);
          break;
        case AUD_CODEC_FLAC:
          RNA_def_property_flag(prop_bitrate, PROP_HIDDEN);
          RNA_enum_set(op->ptr, "format", AUD_FORMAT_S16);
          break;
        case AUD_CODEC_MP2:
          RNA_enum_set(op->ptr, "format", AUD_FORMAT_S16);
          break;
        case AUD_CODEC_MP3:
          RNA_def_property_enum_items(prop_format, mp3_format_items);
          RNA_def_property_clear_flag(prop_format, PROP_HIDDEN);
          break;
        case AUD_CODEC_PCM:
          RNA_def_property_flag(prop_bitrate, PROP_HIDDEN);
          RNA_def_property_enum_items(prop_format, pcm_format_items);
          RNA_def_property_clear_flag(prop_format, PROP_HIDDEN);
          break;
        case AUD_CODEC_VORBIS:
          RNA_enum_set(op->ptr, "format", AUD_FORMAT_S16);
          break;
        default:
          break;
      }

      break;
    case AUD_CONTAINER_MP2:
      RNA_enum_set(op->ptr, "format", AUD_FORMAT_S16);
      RNA_enum_set(op->ptr, "codec", AUD_CODEC_MP2);
      RNA_def_property_enum_items(prop_codec, all_codec_items);
      break;
    case AUD_CONTAINER_MP3:
      RNA_def_property_clear_flag(prop_format, PROP_HIDDEN);
      RNA_def_property_enum_items(prop_format, mp3_format_items);
      RNA_def_property_enum_items(prop_codec, all_codec_items);
      RNA_enum_set(op->ptr, "codec", AUD_CODEC_MP3);
      break;
    case AUD_CONTAINER_OGG:
      RNA_def_property_clear_flag(prop_codec, PROP_HIDDEN);
      RNA_def_property_enum_items(prop_codec, ogg_codec_items);
      RNA_enum_set(op->ptr, "format", AUD_FORMAT_S16);
      break;
    case AUD_CONTAINER_WAV:
      RNA_def_property_flag(prop_bitrate, PROP_HIDDEN);
      RNA_def_property_clear_flag(prop_format, PROP_HIDDEN);
      RNA_def_property_enum_items(prop_format, pcm_format_items);
      RNA_def_property_enum_items(prop_codec, all_codec_items);
      RNA_enum_set(op->ptr, "codec", AUD_CODEC_PCM);
      break;
    default:
      break;
  }

  PointerRNA ptr = RNA_pointer_create_discrete(&wm->id, op->type->srna, op->properties);

  /* main draw call */
  uiDefAutoButsRNA(layout,
                   &ptr,
                   sound_mixdown_draw_check_prop,
                   nullptr,
                   nullptr,
                   UI_BUT_LABEL_ALIGN_NONE,
                   false);
}
#endif /* WITH_AUDASPACE */

static void SOUND_OT_mixdown(wmOperatorType *ot)
{
#ifdef WITH_AUDASPACE
  static const EnumPropertyItem format_items[] = {
      {AUD_FORMAT_U8, "U8", 0, "U8", "8-bit unsigned"},
      {AUD_FORMAT_S16, "S16", 0, "S16", "16-bit signed"},
      {AUD_FORMAT_S24, "S24", 0, "S24", "24-bit signed"},
      {AUD_FORMAT_S32, "S32", 0, "S32", "32-bit signed"},
      {AUD_FORMAT_FLOAT32, "F32", 0, "F32", "32-bit floating-point"},
      {AUD_FORMAT_FLOAT64, "F64", 0, "F64", "64-bit floating-point"},
      {0, nullptr, 0, nullptr, nullptr},
  };

  static const EnumPropertyItem codec_items[] = {
#  ifdef WITH_FFMPEG
      {AUD_CODEC_AAC, "AAC", 0, "AAC", "Advanced Audio Coding"},
      {AUD_CODEC_AC3, "AC3", 0, "AC3", "Dolby Digital ATRAC 3"},
#  endif
      {AUD_CODEC_FLAC, "FLAC", 0, "FLAC", "Free Lossless Audio Codec"},
#  ifdef WITH_FFMPEG
      {AUD_CODEC_MP2, "MP2", 0, "MP2", "MPEG-1 Audio Layer II"},
      {AUD_CODEC_MP3, "MP3", 0, "MP3", "MPEG-2 Audio Layer III"},
#  endif
      {AUD_CODEC_PCM, "PCM", 0, "PCM", "Pulse Code Modulation (RAW)"},
      {AUD_CODEC_VORBIS, "VORBIS", 0, "Vorbis", "Xiph.Org Vorbis Codec"},
      {0, nullptr, 0, nullptr, nullptr},
  };

  static const EnumPropertyItem channel_items[] = {
      {AUD_CHANNELS_MONO, "MONO", 0, "Mono", "Single audio channel"},
      {AUD_CHANNELS_STEREO, "STEREO", 0, "Stereo", "Stereo audio channels"},
      {AUD_CHANNELS_STEREO_LFE, "STEREO_LFE", 0, "Stereo LFE", "Stereo with LFE channel"},
      {AUD_CHANNELS_SURROUND4, "SURROUND4", 0, "4 Channels", "4 channel surround sound"},
      {AUD_CHANNELS_SURROUND5, "SURROUND5", 0, "5 Channels", "5 channel surround sound"},
      {AUD_CHANNELS_SURROUND51, "SURROUND51", 0, "5.1 Surround", "5.1 surround sound"},
      {AUD_CHANNELS_SURROUND61, "SURROUND61", 0, "6.1 Surround", "6.1 surround sound"},
      {AUD_CHANNELS_SURROUND71, "SURROUND71", 0, "7.1 Surround", "7.1 surround sound"},
      {0, nullptr, 0, nullptr, nullptr}};

#endif /* WITH_AUDASPACE */

  /* identifiers */
  ot->name = "Mixdown Audio";
  ot->description = "Mixdown and export the scene's audio to a sound file"; /* BFA - more explicit*/
  ot->idname = "SOUND_OT_mixdown";

  /* API callbacks. */
  ot->exec = sound_mixdown_exec;
  ot->invoke = sound_mixdown_invoke;

#ifdef WITH_AUDASPACE
  ot->check = sound_mixdown_check;
  ot->ui = sound_mixdown_draw;
#endif
  /* flags */
  ot->flag = OPTYPE_REGISTER;

  /* properties */
  WM_operator_properties_filesel(ot,
                                 FILE_TYPE_FOLDER | FILE_TYPE_SOUND,
                                 FILE_SPECIAL,
                                 FILE_SAVE,
                                 WM_FILESEL_FILEPATH | WM_FILESEL_RELPATH | WM_FILESEL_SHOW_PROPS,
                                 FILE_DEFAULTDISPLAY,
                                 FILE_SORT_DEFAULT);
#ifdef WITH_AUDASPACE
  RNA_def_int(
      ot->srna,
      "accuracy",
      1024,
      1,
      16777216,
      "Accuracy",
      "Sample accuracy, important for animation data (the lower the value, the more accurate)",
      1,
      16777216);
  RNA_def_enum(
      ot->srna, "container", container_items, AUD_CONTAINER_FLAC, "Container", "File format");
  RNA_def_enum(ot->srna, "codec", codec_items, AUD_CODEC_FLAC, "Codec", "Audio Codec");
  RNA_def_enum(
      ot->srna, "channels", channel_items, AUD_CHANNELS_STEREO, "Channels", "Audio channel count");
  RNA_def_enum(ot->srna, "format", format_items, AUD_FORMAT_S16, "Format", "Sample format");
  RNA_def_int(ot->srna,
              "mixrate",
              48000,
              8000,
              192000,
              "Sample Rate",
              "Sample rate in samples/s",
              8000,
              192000);
  RNA_def_int(ot->srna, "bitrate", 192, 32, 512, "Bitrate", "Bitrate in kbit/s", 32, 512);
  RNA_def_boolean(ot->srna,
                  "split_channels",
                  false,
                  "Split channels",
                  "Each channel will be rendered into a mono file");
#endif /* WITH_AUDASPACE */
}

/* ******************************************************* */

static bool sound_poll(bContext *C)
{
  Editing *ed = CTX_data_sequencer_scene(C)->ed;

  if (!ed || !ed->act_strip || ed->act_strip->type != STRIP_TYPE_SOUND_RAM) {
    return false;
  }

  return true;
}
/********************* pack operator *********************/

static wmOperatorStatus sound_pack_exec(bContext *C, wmOperator *op)
{
  Main *bmain = CTX_data_main(C);
  Editing *ed = CTX_data_sequencer_scene(C)->ed;
  bSound *sound;

  if (!ed || !ed->act_strip || ed->act_strip->type != STRIP_TYPE_SOUND_RAM) {
    return OPERATOR_CANCELLED;
  }

  sound = ed->act_strip->sound;

  if (!sound || sound->packedfile) {
    return OPERATOR_CANCELLED;
  }

  sound->packedfile = BKE_packedfile_new(
      op->reports, sound->filepath, ID_BLEND_PATH(bmain, &sound->id));

  DEG_id_tag_update_ex(bmain, &sound->id, ID_RECALC_AUDIO);

  return OPERATOR_FINISHED;
}

static void SOUND_OT_pack(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Pack Sound";
  ot->description = "Pack the sound into the current blend file";
  ot->idname = "SOUND_OT_pack";

  /* API callbacks. */
  ot->exec = sound_pack_exec;
  ot->poll = sound_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/********************* unpack operator *********************/

static wmOperatorStatus sound_unpack_exec(bContext *C, wmOperator *op)
{
  Main *bmain = CTX_data_main(C);
  int method = RNA_enum_get(op->ptr, "method");
  bSound *sound = nullptr;

  /* find the supplied image by name */
  if (RNA_struct_property_is_set(op->ptr, "id")) {
    char sndname[MAX_ID_NAME - 2];
    RNA_string_get(op->ptr, "id", sndname);
    sound = static_cast<bSound *>(BLI_findstring(&bmain->sounds, sndname, offsetof(ID, name) + 2));
  }

  if (!sound || !sound->packedfile) {
    return OPERATOR_CANCELLED;
  }

  if (!ID_IS_EDITABLE(&sound->id)) {
    BKE_report(op->reports, RPT_ERROR, "Sound is not editable");
    return OPERATOR_CANCELLED;
  }

  if (G.fileflags & G_FILE_AUTOPACK) {
    BKE_report(op->reports,
               RPT_WARNING,
               "AutoPack is enabled, so image will be packed again on file save");
  }

  BKE_packedfile_unpack_sound(bmain, op->reports, sound, ePF_FileStatus(method));

  return OPERATOR_FINISHED;
}

static wmOperatorStatus sound_unpack_invoke(bContext *C, wmOperator *op, const wmEvent * /*event*/)
{
  Editing *ed = CTX_data_sequencer_scene(C)->ed;
  bSound *sound;

  if (RNA_struct_property_is_set(op->ptr, "id")) {
    return sound_unpack_exec(C, op);
  }

  if (!ed || !ed->act_strip || ed->act_strip->type != STRIP_TYPE_SOUND_RAM) {
    return OPERATOR_CANCELLED;
  }

  sound = ed->act_strip->sound;

  if (!sound || !sound->packedfile) {
    return OPERATOR_CANCELLED;
  }

  if (!ID_IS_EDITABLE(&sound->id)) {
    BKE_report(op->reports, RPT_ERROR, "Sound is not editable");
    return OPERATOR_CANCELLED;
  }

  if (G.fileflags & G_FILE_AUTOPACK) {
    BKE_report(op->reports,
               RPT_WARNING,
               "AutoPack is enabled, so image will be packed again on file save");
  }

  unpack_menu(
      C, "SOUND_OT_unpack", sound->id.name + 2, sound->filepath, "sounds", sound->packedfile);

  return OPERATOR_FINISHED;
}

static void SOUND_OT_unpack(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Unpack Sound";
  ot->description = "Unpack the sound to the samples filename";
  ot->idname = "SOUND_OT_unpack";

  /* API callbacks. */
  ot->exec = sound_unpack_exec;
  ot->invoke = sound_unpack_invoke;
  ot->poll = sound_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* properties */
  RNA_def_enum(
      ot->srna, "method", rna_enum_unpack_method_items, PF_USE_LOCAL, "Method", "How to unpack");
  /* XXX: weak!, will fail with library, name collisions */
  RNA_def_string(
      ot->srna, "id", nullptr, MAX_ID_NAME - 2, "Sound Name", "Sound data-block name to unpack");
}

/* ******************************************************* */

void ED_operatortypes_sound()
{
  WM_operatortype_append(SOUND_OT_open);
  WM_operatortype_append(SOUND_OT_open_mono);
  WM_operatortype_append(SOUND_OT_mixdown);
  WM_operatortype_append(SOUND_OT_pack);
  WM_operatortype_append(SOUND_OT_unpack);
  WM_operatortype_append(SOUND_OT_update_animation_flags);
  WM_operatortype_append(SOUND_OT_bake_animation);
}
