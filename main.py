import mygui, mouse_sequence, key_map, config
import copy, threading
from time import sleep

from gi.repository import GObject as gobject
gobject.threads_init()

import sys

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
        "open-dialog": (
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_STRING]
        ),
        "open-exception-dialog": (
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_STRING]
        ),
        "update-gui": (
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]
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
            try:
                if config.state == config.RECORDING_MOUSE_SEQ:
                    mouse_sequence.start_recording(self)
                    config.state = config.TASK_JUST_STOPPED
                elif config.state == config.PLAYING_MOUSE_SEQ:
                    mouse_sequence.play_sequence(self)
                    config.state = config.TASK_JUST_STOPPED
                elif config.state == config.RECORDING_KBM_CONNECTIONS:
                    key_map.start_recording(self)
                    config.state = config.TASK_JUST_STOPPED
                elif config.state == config.PLAYING_KBM_CONNECTIONS:
                    key_map.play_kbm_map(self)
                    config.state = config.TASK_JUST_STOPPED
                if config.state == config.TASK_JUST_STOPPED:
                    self.emit('update-gui', "Thinking about life...")
                    sleep(1.0) # be sure keyboard or mouse event queue is ready
                    config.state = config.READY
                    self.emit('update-gui', "Ready")
            except (config.InvalidPreset, TypeError):
                config.state = config.READY
                self.emit('update-gui', "Ready")
                self.emit("open-dialog",
                    "Wrong preset format",
                    self.gui.Gtk.MessageType.ERROR,
                    "Current preset has been resetted because of a format error")
                config.resetCurrentPreset(None)
            except Exception as exc_obj:
                import traceback
                config.state = config.READY
                self.emit('update-gui', "Ready")
                self.emit("open-exception-dialog",
                    "Unknown error",
                    ''.join(traceback.format_exception(None, exc_obj, exc_obj.__traceback__)
                    )
                )
            sleep(0.1) # keeping cpu calm :P
        #print(sys.exc_info())

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