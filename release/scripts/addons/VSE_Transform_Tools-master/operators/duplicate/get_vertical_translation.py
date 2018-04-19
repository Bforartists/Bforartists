import bpy
from operator import attrgetter


def get_vertical_translation(strips):
    """
    Determine how many channels up the strips need to be moved
    in order to accomodate them all

    Parameters
    ----------
    strips : list of bpy.types.Sequence()
        A group of strips in the sequencer

    Returns
    -------
    int
        The number of channels UP that the group of strips need to move
        in order to prevent any conflicts with other strips in the
        sequencer.
    """
    scene = bpy.context.scene

    min_channel = min(strips, key=attrgetter('channel')).channel
    max_channel = max(strips, key=attrgetter('channel')).channel

    channel_count = (max_channel - min_channel) + 1

    frame_start = min(strips,
        key=attrgetter('frame_start')).frame_start
    frame_end = max(strips,
        key=attrgetter('frame_final_end')).frame_final_end

    all_sequences = list(sorted(scene.sequence_editor.sequences,
                                key=lambda x: x.frame_start))

    blocked_channels = []
    for seq in all_sequences:
        if (seq not in strips and
                seq.frame_start <= frame_end and
                seq.frame_final_end >= frame_start):
            blocked_channels.append(seq.channel)
        elif seq.frame_start > frame_end:
            break

    i = max_channel + 1
    while True:
        for x in range(i, i + channel_count):
            conflict = False
            if x in blocked_channels:
                conflict = True
                break
        if not conflict:
            return x - max_channel
        i += 1
