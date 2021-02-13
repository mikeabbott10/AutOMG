# Demo application showing how once can combine the python
# threading module with GObject signals to make a simple thread
# manager class which can be used to stop horrible blocking GUIs.
#
# (c) 2008, John Stowers <john.stowers@gmail.com>
#
# This program serves as an example, and can be freely used, copied, derived
# and redistributed by anyone. No warranty is implied or given.
#
# The original module is at: 
from gi.repository import GObject as gobject
gobject.threads_init()

import threading

class _IdleObject(gobject.GObject):
    """
    Override gobject.GObject to always emit signals in the main thread
    by emmitting on an idle handler
    """
    def __init__(self):
        gobject.GObject.__init__(self)

    def emit(self, *args):
        gobject.idle_add(gobject.GObject.emit,self,*args)

class FooThread(threading.Thread, _IdleObject):
    """
    Cancellable thread which uses gobject signals to return information
    to the GUI.
    """
    __gsignals__ =  { 
            "progress": (
                gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT])
            }

    def __init__(self, progressCb):
        threading.Thread.__init__(self)
        _IdleObject.__init__(self)
        self.connect("progress", progressCb)
