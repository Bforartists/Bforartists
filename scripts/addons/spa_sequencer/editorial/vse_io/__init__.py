import logging

log = logging.getLogger(__name__)

# Safe import modules depending on OpenTimelineIO.
try:
    from spa_sequencer.editorial.vse_io import ops, ui

    HAS_OTIO = True
except ModuleNotFoundError:
    HAS_OTIO = False


def register():
    # Only register modules if OTIO is available.
    if HAS_OTIO:
        ops.register()
        ui.register()
    else:
        log.warn("VSE-IO features unavailable: 'opentimelineio' is missing")


def unregister():
    if HAS_OTIO:
        ops.unregister()
        ui.unregister()
