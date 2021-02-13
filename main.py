import mygui, mouse_sequence, key_map, config
import copy, threading
from time import sleep

from gi.repository import GObject as gobject
gobject.threads_init()

class _IdleObject(gobject.GObject):
    """
    Override gobject.GObject to always emit signals in the main thread
    by emmitting on an idle handler
    """
    def __init__(self):
        gobject.GObject.__init__(self)

    def emit(self, *args):
        gobject.idle_add(gobject.GObject.emit,self,*args)


class Main(threading.Thread, _IdleObject):
    """
    Cancellable thread which uses gobject signals to return information
    to the GUI.
    """
    __gsignals__ =  { 
        "key-map-recording-progress": (
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT]
        ),
        "get-ready-state": (
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []
        ),
        "open-dialog": (
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_STRING]
        ),
        "open-exception-dialog": (
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_STRING]
        ),
    }

    def __init__(self):
        threading.Thread.__init__(self)
        _IdleObject.__init__(self)
        self.cancelled = False
        self.gui = None
        self.lastPreset = copy.deepcopy(config.currentPreset)
        self.lastPresetPath = None
        self.connect("key-map-recording-progress", self._on_key_map_recording_progress)
        self.connect("get-ready-state", self._get_ready_state)
        self.connect("open-dialog", self._openDialog)
        self.connect("open-exception-dialog", self._openExceptionDialog)

    # set the gui object
    def setGui(self, win):
        self.gui = win
    
    # stop this thread
    def stop(self):
        self.cancelled = True

    # the loop this thread stays on
    def run(self):
        while not self.cancelled:
            try:
                if config.state == config.RECORDING_MOUSE_SEQ:
                    mouse_sequence.start_recording()
                elif config.state == config.PLAYING_MOUSE_SEQ:
                    mouse_sequence.play_sequence()
                    if config.state != config.READY: # we can here stop execution from inside
                        self.emit("get-ready-state")
                elif config.state == config.RECORDING_KBM_CONNECTIONS:
                    key_map.start_recording(self)
                elif config.state == config.PLAYING_KBM_CONNECTIONS:
                    key_map.play_kbm_map()
                    if config.state != config.READY: # we can here stop execution from inside
                        self.emit("get-ready-state")
            except (config.InvalidPreset, TypeError):
                self.emit("get-ready-state")
                self.emit("open-dialog",
                    "Wrong preset format",
                    self.gui.Gtk.MessageType.ERROR,
                    "Current preset has been resetted because of a format error")
                config.resetCurrentPreset(None)
            except Exception as exc_obj:
                import traceback
                self.emit("get-ready-state")
                self.emit("open-exception-dialog",
                    "Unknown error",
                    ''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)
                    )
                )
            sleep(0.1) # keeping cpu calm :P

    # change state to READY and update gui
    def _get_ready_state(self, thread):
        config.state = config.READY
        getattr(self.gui, 'modifyWidgetsWithState_' + config.state, lambda: None)()

    # open dialog
    def _openDialog(self, thread, title, messageType, text):
        self.gui.openDialog(
            title=title,
            messageType=messageType,
            text=text
        )
    # open dialog in order to show exception
    def _openExceptionDialog(self, thread, title, text):
        self.gui.openExceptionDialog(
            title=title,
            exceptionText=text
        )

    # quit callback
    def _quit(self, sender, event):
        self.emit("get-ready-state")
        if self.gui.quit_cb(self.lastPreset != config.currentPreset):
            self.stop()
            self.gui.Gtk.main_quit()
        else:
            return True

    # key-map-recording-progress signal handler (update the gui status bar)
    def _on_key_map_recording_progress(self, thread, progress):
        if(progress == config.WAITING_FOR_KEYBOARD):
            self.gui.statusBar.pop(self.gui.context_id)
            self.gui.statusBar.push(self.gui.context_id, "Waiting for keyboard input")
        else:
            self.gui.statusBar.pop(self.gui.context_id)
            self.gui.statusBar.push(self.gui.context_id, "Waiting for mouse input")



if __name__ == "__main__":
    main = Main()
    win = mygui.AutOMGWindow(main)
    main.setGui(win)
    win.connect("delete-event", main._quit)
    win.show_all()
    win.fixWidgetsSize() # workaround in order to keep widgets size fixed and make similar widgets size the same
    main.daemon = True
    main.start()
    mygui.Gtk.main()