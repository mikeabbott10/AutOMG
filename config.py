"""
State is the program state. Every state changes make the gui and the currently running thread change
"""
READY = 'ready'
RECORDING_MOUSE_SEQ = 'recording_mouse_seq'
PLAYING_MOUSE_SEQ = 'playing_mouse_seq'
RECORDING_KBM_CONNECTIONS = 'recording_kbm_connections'
PLAYING_KBM_CONNECTIONS = 'playing_kbm_connections'
TASK_JUST_STOPPED = 'task_just_stopped'
state = READY


"""
Mouse sequence constants 
"""
mouse_sequence_playingTimes = 0
mouse_sequence_movementSamplingTime = 0


"""
Current preset is the preset currently in memory
"""
currentPreset = {
    'mouseSeq': {
        'recordedEvents': [],
        'recordedTimes': []
    },
    'kbmMap': {}
}
# reste the current preset
def resetCurrentPreset(widget):
    global currentPreset
    currentPreset = {
        'mouseSeq': {
            'recordedEvents': [],
            'recordedTimes': []
        },
        'kbmMap': {}
    }

class InvalidPreset(Exception): pass

# check if data is a valid preset
def isPresetValid(data):
    if len(data.keys()) != 2:
        raise InvalidPreset()
    if len(data['mouseSeq'].keys()) != 2:
        raise InvalidPreset()
    #from collections.abc import Mapping
    if not isinstance(data['kbmMap'], dict):
        raise InvalidPreset()
    if not isinstance(data['mouseSeq'], dict):
        raise InvalidPreset()
    if not ( isinstance(data['mouseSeq']['recordedEvents'], list) and 
            isinstance(data['mouseSeq']['recordedTimes'], list) ):
        raise InvalidPreset()
