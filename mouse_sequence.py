from pynput import mouse, keyboard
from time import sleep, time
import config
import threading

tic = 0

"""
    Record the mouse events.
    Quit if state is not config.RECORDING_MOUSE_SEQ anymore
"""
def start_recording(runningThread):
    global tic
    config.resetCurrentMouseSequencePreset(None)
    tic = time()
    try:
        with mouse.Events() as events:
            while config.state == config.RECORDING_MOUSE_SEQ:
                # Block at most 0.1 second
                event = events.get(timeout=0.1)
                if event is not None:
                    if type(event) == mouse.Events.Move:
                        on_move(event)
                    elif type(event) == mouse.Events.Click:
                        on_click(event)
            # remove the click on Stop button from the sequence
            i = len(config.currentPreset['mouseSeq']['recordedEvents']) - 1
            cnt = 0
            while i>=0 and cnt<2:
                if (config.currentPreset['mouseSeq']['recordedEvents'][i][0] and 
                        config.currentPreset['mouseSeq']['recordedEvents'][i][1] == mouse.Button.left):
                    cnt+=1
                    del config.currentPreset['mouseSeq']['recordedEvents'][i]
                    del config.currentPreset['mouseSeq']['recordedTimes'][i]
                i-=1
            raise mouse.Listener.StopException()
    except mouse.Listener.StopException:
        # we need to raise these exceptions because of a listener.stop() bug with Xorg
        pass
      
"""
    Start a thread which plays the mouse sequence and keep listening to keyboard events. 
    Stop playing if "esc" key is pressed.
"""
def play_sequence(runningThread):
    if(len(config.currentPreset['mouseSeq']['recordedEvents']) > 0):
        threading.Thread(target=play_recorded_mouse_sequence).start()
        try:
            with keyboard.Events() as events:
                while config.state == config.PLAYING_MOUSE_SEQ:
                    # Block at most 0.1 second 
                    # TODO: diminuire
                    event = events.get(timeout=0.1)
                    if event is not None and event.key == keyboard.Key.esc:
                        break
                raise keyboard.Listener.StopException()
        except keyboard.Listener.StopException:
            # we need to raise these exceptions because of a listener.stop() bug with Xorg
            pass
    
"""
    Play the recorded mouse sequence
"""
def play_recorded_mouse_sequence():
    MouseCtr = mouse.Controller
    cnt = 0
    while config.state == config.PLAYING_MOUSE_SEQ:
        if config.mouse_sequence_playingTimes==0 or cnt<config.mouse_sequence_playingTimes:
            i = 0
            for tempo in config.currentPreset['mouseSeq']['recordedTimes']:
                sleep(tempo)
                if config.state != config.PLAYING_MOUSE_SEQ:
                    return
                isButtonEvent = config.currentPreset['mouseSeq']['recordedEvents'][i][0]
                if(isButtonEvent): # mouse button event
                    button, press, x, y = config.currentPreset['mouseSeq']['recordedEvents'][i][1:]
                    MouseCtr().position = (x,y)
                    if(press): # button was pressed
                        MouseCtr().press(button)
                    else:
                        MouseCtr().release(button)
                else: # mouse movement event
                    x, y = config.currentPreset['mouseSeq']['recordedEvents'][i][1:]
                    MouseCtr().position = (x,y)
                i+=1
            sleep(0.05)
            if(config.mouse_sequence_playingTimes!=0):
                cnt+=1
        else: 
            config.state = config.READY 

# mouse callbacks
def on_move(event):
    global tic
    if(config.mouse_sequence_movementSamplingTime > 0 and time() - tic >= config.mouse_sequence_movementSamplingTime):
        # more than movementSamplingTime tenth of a second from the last event recorded event
        toc = time()
        config.currentPreset['mouseSeq']['recordedTimes'].append(toc - tic) # time between 2 events
        eventCoordinates = [False, event.x, event.y] # False stands for mouse movement event
        config.currentPreset['mouseSeq']['recordedEvents'].append(eventCoordinates)
        tic = time()

def on_click(event):
    global tic
    toc = time()
    config.currentPreset['mouseSeq']['recordedTimes'].append(toc - tic) # time between 2 events
    eventCoordinates = [True, event.button, event.pressed, event.x, event.y] # True stands for mouse button event
    config.currentPreset['mouseSeq']['recordedEvents'].append(eventCoordinates)
    tic = time()

# unused
def on_scroll(x, y, dx, dy):
    pass # print('Scrolled {0} at {1}'.format( 'down' if dy < 0 else 'up', (x, y)))


"""
movementSamplingTime map:
time->lvl
0.2 -> 9
0.4 -> 8
0.6 -> 7
0.8 -> 6
1.0 -> 5
1.2 -> 4
1.4 -> 3
1.6 -> 2
1.8 -> 1
no -> 0
"""