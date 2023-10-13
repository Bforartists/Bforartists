import json
import os
from pathlib import Path


import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper

import opentimelineio as otio
from opentimelineio.opentime import TimeRange, RationalTime

from spa_sequencer.utils import register_classes, unregister_classes

from spa_sequencer.editorial.vse_io.core import (
    get_media_reference_filepath,
    sequencer_add_media_func,
    strip_apply_frame_offsets,
)


# Name of custom property to store source AAF metadata on a strip.
STRIP_PROP_AAF_METADATA = "aaf_metadata"

# Name of custom property to store the path to a missing media reference after import.
STRIP_PROP_MISSING_REFERENCE_PATH = "missing_reference"

# Strip color to use for missing media references when importing timelines.
STRIP_MISSING_REFERENCE_COLOR = 0.7, 0.0, 0.7

# Prefix to add to AAF metadata written to source clips on export.
EXPORT_AAF_BLENDER_METADATA_PREFIX = "Blender."


class IMPORT_OT_otio(bpy.types.Operator, ImportHelper):
    bl_idname = "import.vse_otio"
    bl_label = "Import Timeline"
    bl_description = "Import a timeline using OTIO"
    bl_options = {"UNDO", "REGISTER", "PRESET"}

    filter_glob: bpy.props.StringProperty(
        default="*.otio;*.xml;*.aaf;*.edl;", options={"HIDDEN"}
    )

    def transcribe_otio_track(
        self, track: otio.schema.Track, frame_start: int, channel: int
    ):
        """
        Transcribe an OTIO `track` to Blender, by creating VSE strips from
        OTIO clips on specified `channel`.

        :param track: The track to transcribe.
        :param frame_start: Frame start of the track.
        :param channel: VSE channel index.
        """

        insert_frame = frame_start

        for clip in track.each_child():
            # Only consider source clips and gaps for now, skip everything else.
            if not isinstance(clip, (otio.schema.Clip, otio.schema.Gap)):
                continue
            # Gaps: only move insertion frame by its duration.
            if isinstance(clip, otio.schema.Gap):
                insert_frame += otio.opentime.to_frames(clip.source_range.duration)
            else:
                insert_frame += self.transcribe_otio_source_clip(
                    clip, insert_frame, channel
                )

    def add_missing_reference_clip(
        self, name: str, frame_start: int, duration: int, channel: int
    ) -> bpy.types.Sequence:
        """Add a strip representing a missing media clip.

        :param seq_editor: Sequence editor to add the strip to.
        :param name: Strip name.
        :param frame_start: Strip frame start.
        :param duration: Strip duration.
        :param channel: Strip channel.
        """
        new_strip = self.seq_editor.sequences.new_effect(
            name=name,
            type="COLOR",
            channel=channel,
            frame_start=frame_start,
            frame_end=frame_start + duration,
        )
        # Indicate missing media reference.
        new_strip.color = STRIP_MISSING_REFERENCE_COLOR
        return new_strip

    def add_valid_reference_clip(
        self,
        clip: otio.schema.Clip,
        filepath: str,
        channel: int,
        insert_frame: int,
        duration: int,
    ) -> bpy.types.Sequence:
        """Create a media strip from given `filepath`, based on the given OTIO `clip`.

        :param clip: The reference OTIO clip.
        :param filepath: The solved media reference filepath.
        :param channel: The channel to add the strip to.
        :param insert_frame: The frame the strip to create the strip at.
        :param duration: The final duration of the strip.
        :return: The newly created media strip.
        """
        # Create a new media strip to an external reference.
        add_media_strip = sequencer_add_media_func(
            self.seq_editor, clip.parent(), filepath
        )
        strip = add_media_strip(
            name=clip.name,
            filepath=filepath,
            channel=channel,
            frame_start=insert_frame,
        )
        offset_start = otio.opentime.to_frames(clip.source_range.start_time)
        strip_apply_frame_offsets(strip, insert_frame, duration, offset_start)
        return strip

    def transcribe_otio_source_clip(
        self,
        clip: otio.schema.Clip,
        insert_frame: int,
        channel: int,
    ) -> int:
        """Transcribe an OTIO `clip` into a media strip.

        If the strip does not point to a valid reference on disk, the created strip
        will be a ColorSequence with a custom property set to the missing media
        filepath (see `STRIP_PROP_MISSING_REFERENCE_PATH`).

        :param clip: The source OTIO clip.
        :param insert_frame: The frame to create the media strip at.
        :param channel: The target sequence editor channel.
        :return: The newly created strip.
        """

        if isinstance(clip.media_reference, otio.schema.ExternalReference):
            filepath = get_media_reference_filepath(
                clip.media_reference, os.path.dirname(self.filepath)
            )
        else:
            filepath = ""

        duration = otio.opentime.to_frames(clip.source_range.duration)
        has_valid_external_reference = os.path.isfile(filepath)
        new_strip = None

        if has_valid_external_reference:
            new_strip = self.add_valid_reference_clip(
                clip, filepath, channel, insert_frame, duration
            )

        else:
            # Add a missing media strip
            new_strip = self.add_missing_reference_clip(
                clip.name, insert_frame, duration, channel
            )
            if filepath:
                # Store missing reference filepath that can
                # be used for a-posteriori relinking.
                new_strip[STRIP_PROP_MISSING_REFERENCE_PATH] = filepath

        # Store comments as a custom property on strip.
        metadata = clip.media_reference.metadata
        if user_comments := metadata.get("AAF", {}).get("UserComments"):
            new_strip[STRIP_PROP_AAF_METADATA] = json.dumps(dict(user_comments))
            # Restore Blender related metadata as strip properties
            for key, value in user_comments.items():
                if key.startswith(EXPORT_AAF_BLENDER_METADATA_PREFIX):
                    new_strip[
                        key.replace(EXPORT_AAF_BLENDER_METADATA_PREFIX, "")
                    ] = value

        return duration

    def execute(self, context: bpy.types.Context):
        scene = context.scene
        if not scene.sequence_editor:
            scene.sequence_editor_create()

        self.seq_editor = scene.sequence_editor

        timeline = otio.adapters.read_from_file(self.filepath)
        tracks = timeline.audio_tracks() + timeline.video_tracks()

        for idx, track in enumerate(tracks):
            channel = idx + 1
            self.transcribe_otio_track(track, scene.frame_start, channel)

        bpy.ops.sequencer.refresh_all()
        return {"FINISHED"}


class EXPORT_OT_otio(bpy.types.Operator, ExportHelper):
    bl_idname = "export.vse_otio"
    bl_label = "Export Timeline"
    bl_description = "Export a VSE timeline using OTIO"
    bl_options = {"PRESET"}

    filename_ext = ""

    file_format: bpy.props.EnumProperty(
        items=(
            ("aaf", "AAF", "Avid Authoring Format"),
            ("edl", "EDL", "EDL CXMP"),
            ("otio", "OTIO", "OTIO"),
        )
    )

    filter_glob: bpy.props.StringProperty(
        default="*.aaf;*.edl;*.otio", options={"HIDDEN"}
    )

    relative_paths: bpy.props.BoolProperty(
        name="Relative Paths",
        description="Use relative paths for media URLs instead of absolute paths",
        default=False,
    )

    write_metadata: bpy.props.BoolProperty(
        name="Metadata",
        description="Write metadata to AAF files",
        default=True,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.scene.sequence_editor is not None

    def execute(self, context: bpy.types.Context):
        seq_editor: bpy.types.SequenceEditor = context.scene.sequence_editor

        try:
            timeline = self.build_otio_timeline(seq_editor)
        except RuntimeError as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}

        # Write output file.
        export_filepath = bpy.path.ensure_ext(self.filepath, f".{self.file_format}")
        params = dict()
        if self.file_format == "aaf":
            params["use_empty_mob_ids"] = True
        otio.adapters.write_to_file(timeline, export_filepath, **params)

        self.report({"INFO"}, "Export done!")
        return {"FINISHED"}

    def build_otio_timeline(
        self, seq_editor: bpy.types.SequenceEditor
    ) -> otio.schema.Timeline:
        """Build an OTIO timeline from a Blender sequence editor.

        :param seq_editor: The sequence editor.
        :return: The created timeline.
        """

        scene: bpy.types.Scene = seq_editor.id_data
        fps = scene.render.fps

        # Create an OTIO timeline
        timeline = otio.schema.Timeline(name=scene.name)
        timeline.global_start_time = RationalTime(scene.frame_start, fps)

        # Build a map of strips per channels.
        tracks = {}
        for strip in seq_editor.sequences:
            if strip.channel not in tracks:
                tracks[strip.channel] = []
            tracks[strip.channel].append(strip)

        # Transcribe VSE channels to OTIO tracks.
        for track_id, strips in tracks.items():
            self.add_track(
                timeline,
                seq_editor.channels[track_id].name,
                scene.frame_start,
                strips,
                fps,
            )

        return timeline

    @staticmethod
    def track_kind_from_strip(strip: bpy.types.Sequence) -> otio.schema.TrackKind:
        """Return otio track kind based on strip type."""
        match type(strip):
            case bpy.types.SoundSequence:
                return otio.schema.TrackKind.Audio
            case _:
                return otio.schema.TrackKind.Video

    def add_track(
        self,
        timeline: otio.schema.Timeline,
        track_name: str,
        frame_start: int,
        strips: list[bpy.types.Sequence],
        timeline_fps: int,
    ) -> otio.schema.Track:
        """Add a new track to `timeline` from input VSE `strips`.

        :param timeline: OTIO timeline.
        :param track_name: New track name.
        :param frame_start: New track frame start.
        :param strips: The list of strips.
        :param timeline_fps: Timeline framerate.
        :return: The created track.
        """

        # Create a new otio track and use first strip's type to assign a track kind.
        track = otio.schema.Track(name=track_name)

        # Ensure all strips are of the same kind.
        kinds = set(self.track_kind_from_strip(s) for s in strips)
        if not len(kinds) == 1:
            raise ValueError(f"Different strip types on track '{track_name}'")
        track.kind = kinds.pop()

        # Sort strips by frame start.
        sorted_strip = sorted(strips, key=lambda x: x.frame_final_start)
        # Initialize insert time using first strip start frame.
        # Getting first element is safe, sequences can not be empty here.
        insert_time = frame_start

        # Iterate over strips.
        for strip in sorted_strip:
            # Add a gap if the clip is not starting right at current insertion time.
            if insert_time < strip.frame_final_start:
                gap_duration = strip.frame_final_start - insert_time
                self.add_gap(track, insert_time, gap_duration, timeline_fps)
            # Add a clip to the track to represent current strip.
            self.add_clip(track, strip, timeline_fps)
            insert_time = strip.frame_final_end

        timeline.tracks.append(track)
        return track

    @staticmethod
    def add_gap(
        track: otio.schema.Track, frame_start: int, duration: int, fps: int
    ) -> otio.schema.Gap:
        """Add a gap of the specified `duration` to `track`, at `frame_start`.

        :param track: The track to add the clip to.
        :param frame_start: Gap start frame.
        :param duration: Gap duration
        :param timeline_fps: Timeline framerate.
        :return: The created gap.
        """
        gap = otio.schema.Gap()
        gap.source_range = TimeRange(
            start_time=RationalTime(frame_start, fps),
            duration=RationalTime(duration, fps),
        )
        track.append(gap)
        return gap

    def add_clip(
        self, track: otio.schema.Track, strip: bpy.types.Sequence, timeline_fps: int
    ) -> otio.schema.Clip:
        """Add a new clip on `track` based on input `strip`.

        :param track: The track to add the clip to.
        :param strip: The input sequence strip.
        :param timeline_fps: Timeline framerate.
        :return: The newly created clip.
        """
        media_fps = timeline_fps

        # Retrieve filepath based on strip type.
        match type(strip):
            case bpy.types.SoundSequence:
                media_filepath = strip.sound.filepath
            case bpy.types.ImageSequence:
                media_filepath = os.path.join(
                    strip.directory, strip.elements[0].filename
                )
            case bpy.types.MovieSequence:
                media_filepath = strip.filepath
                media_fps = strip.fps or timeline_fps
            case _:
                media_filepath = ""

        # Conform filepath.
        if media_filepath:
            if self.relative_paths:
                # This seems to work best with Avid: simple relative path
                media_filepath = (
                    Path(bpy.path.relpath(media_filepath)).as_posix().strip("//")
                )
            else:
                # This works best with Resolve, full absolute path
                abspath = bpy.path.abspath(media_filepath)
                media_filepath = Path(abspath).as_posix()

        # Compute strip internal offset.
        # TODO: Test for the sign of this offset when importing in other software.
        offset = strip.frame_final_start - strip.frame_start
        clip = otio.schema.Clip(
            name=strip.name,
            source_range=otio.opentime.TimeRange(
                start_time=RationalTime(offset, timeline_fps),
                duration=RationalTime(strip.frame_final_duration, timeline_fps),
            ),
        )

        clip.media_reference = otio.schema.ExternalReference(
            media_filepath,
            available_range=TimeRange(
                start_time=RationalTime(0, media_fps),
                duration=RationalTime(strip.frame_duration, media_fps),
            ),
        )

        if self.write_metadata:
            self.write_aaf_clip_metadata(clip, strip)

        track.append(clip)
        return clip

    @staticmethod
    def write_aaf_clip_metadata(clip: otio.schema.Clip, strip: bpy.types.Sequence):
        """
        Write custom AAF metadata to `clip` to identify its source.
        This includes:
         - the media filepath as UNC Path
         - source scene strip information if `strip` is the output of a render

        :param clip: The clip to write metadata to.
        :param strip: The source sequence strip.
        """
        # Only handle clips with external references.
        if not isinstance(clip.media_reference, otio.schema.ExternalReference):
            return

        # Fill UNC path property with media's filepath, as it is considered as
        # part of media location solving when importing an AAF via OTIO.
        metadata = {"UNC Path": clip.media_reference.target_url}

        # Consider strip's custom properties (accessed via `items`) as metadata.

        metadata.update(
            {
                f"{EXPORT_AAF_BLENDER_METADATA_PREFIX}{key}": str(value)
                for key, value in strip.items()
            }
        )

        clip.media_reference.metadata.update({"AAF": {"UserComments": metadata}})


classes = (
    EXPORT_OT_otio,
    IMPORT_OT_otio,
)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
