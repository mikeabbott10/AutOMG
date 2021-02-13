from pynput import keyboard, mouse
from pynput.mouse import Controller as MouseCtr
import config
from time import sleep

mainThread = None

# start recording kbm mapping
def start_recording(runningThread):
    global mainThread
    mainThread = runningThread
    with keyboard.Events() as events:
        while config.state == config.RECORDING_KBM_CONNECTIONS:
             # Block at most 0.01 second
            event = events.get(0.01)
            if event is not None:
                if type(event) == keyboard.Events.Press:
                    on_recording_press(event.key)
    mainThread = None

# play the kbm mapping
def play_kbm_map():
    if(len(config.currentPreset['kbmMap']) > 0):
        with keyboard.Events() as events:
            while config.state == config.PLAYING_KBM_CONNECTIONS:
                # Block at most 0.01 second
                event = events.get(0.01)
                if event is not None:
                    if type(event) == keyboard.Events.Press:
                        on_playing_press(event.key)
                    elif type(event) == keyboard.Events.Release:
                        on_playing_release(event.key)


# keyboard callbacks
def on_playing_press(key):
    if key in config.currentPreset['kbmMap'].keys():
        button, x, y = config.currentPreset['kbmMap'][key]
        MouseCtr().position = (x, y)
        MouseCtr().press(button)

def on_playing_release(key):
    if key in config.currentPreset['kbmMap'].keys():
        button, x, y = config.currentPreset['kbmMap'][key]
        MouseCtr().position = (x, y)
        MouseCtr().release(button)

def on_recording_press(key):
    global mainThread
    # map key to the next mouse click
    mainThread.emit('key-map-recording-progress', config.WAITING_FOR_MOUSE)
    with mouse.Events() as events:
        while config.state == config.RECORDING_KBM_CONNECTIONS:
             # Block at most 0.01 second
            event = events.get(0.01)
            if event is not None:
                if type(event) == mouse.Events.Click:
                    on_click_map_key(event, key)
                    break


# mouse callback
def on_click_map_key(event, key_to_map):
    global mainThread
    # we save the mouse click 
    config.currentPreset['kbmMap'][key_to_map] = [event.button, event.x, event.y]
    mainThread.emit('key-map-recording-progress', config.WAITING_FOR_KEYBOARD)
    sleep(0.05)
