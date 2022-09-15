import mygui, mouse_sequence, key_map, config
import copy, threading
from time import sleep
from gi.repository import GObject as gobject
from gi.repository import GLib as glib
import sys

"""
    Override gobject.GObject to always emit signals in the main thread
    by emmitting on an idle handler
"""
class _IdleObject(gobject.GObject):
    def __init__(self):
        gobject.GObject.__init__(self)

    def emit(self, *args):
        glib.idle_add(gobject.GObject.emit,self,*args)

"""
    Cancellable thread which uses gobject signals to return information
    to the GUI.
"""
class Main(threading.Thread, _IdleObject):
    __gsignals__ =  { 
        "open-dialog": (
            gobject.SignalFlags.RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_STRING]
        ),
        "open-exception-dialog": (
            gobject.SignalFlags.RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_STRING]
        ),
        "update-gui": (
            gobject.SignalFlags.RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]
        )
    }

    def __init__(self):
        threading.Thread.__init__(self)
        _IdleObject.__init__(self)
        self.cancelled = False
        self.gui = None
        self.lastPreset = copy.deepcopy(config.currentPreset)
        self.lastPresetPath = None
        self.connect("open-dialog", self._openDialog)
        self.connect("open-exception-dialog", self._openExceptionDialog)
        self.connect("update-gui", self._update_gui)

    # set the gui object
    def setGui(self, win):
        self.gui = win

    # stop this thread
    def stop(self):
        self.cancelled = True

    # the loop this thread stays on
    def run(self):
        while not self.cancelled:
            if config.state == config.READY:
                config.stateEvent.wait(timeout=None)
                config.stateEvent.clear()
            try:
                if config.state == config.RECORDING_MOUSE_SEQ:
                    mouse_sequence.start_recording(self)
                elif config.state == config.PLAYING_MOUSE_SEQ:
                    mouse_sequence.play_sequence(self) # blocked here until playing sequence is stopped
                    self.get_ready_state() # get ready state programmatically
                elif config.state == config.RECORDING_KBM_CONNECTIONS:
                    key_map.start_recording(self)
                elif config.state == config.PLAYING_KBM_CONNECTIONS:
                    key_map.play_kbm_map(self)
                    if config.state != config.READY: 
                        self.get_ready_state() # get ready state programmatically
            except (config.InvalidPreset, TypeError):
                self.get_ready_state()
                self.emit("open-dialog",
                    "Wrong preset format",
                    self.gui.Gtk.MessageType.ERROR,
                    "Current preset has been resetted because of a format error")
                config.resetCurrentPreset(None)
            except Exception as exc_obj:
                import traceback
                self.get_ready_state()
                self.emit("open-exception-dialog",
                    "Unknown error",
                    ''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)
                    )
                )
        print(sys.exc_info())

    def get_ready_state(self):
        config.state = config.READY
        self.emit('update-gui', "Ready")

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
        self.get_ready_state()
        if self.gui.quit_cb(self.lastPreset != config.currentPreset):
            self.stop()
            self.gui.Gtk.main_quit()
        else:
            return True

    # update gui widgets and set status bar text
    def _update_gui(self, thread, text):
        getattr(self.gui, "modifyWidgetsWithState_"+config.state, lambda: None)()
        self.gui.statusBar.pop(self.gui.context_id)
        self.gui.statusBar.push(self.gui.context_id, text)

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