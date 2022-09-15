#!/usr/bin/python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
import config
import webbrowser, copy

# open url url in browser
def _launchBrowser(windown, url):
    webbrowser.open(url)

# build the menu bar and attach it to window
def _buildMenu(window):
    menu = Gtk.MenuBar()

    filemenu = Gtk.Menu()
    file_item = Gtk.MenuItem("File")
    file_item.set_submenu(filemenu)
    
    reset_item = Gtk.MenuItem("Reset preset")
    reset_item.connect("activate", config.resetCurrentPreset)
    filemenu.append(reset_item)
    save_item = Gtk.MenuItem("Save preset")
    save_item.connect("activate", window._save_preset)
    filemenu.append(save_item)
    save_as_item = Gtk.MenuItem("Save preset as...")
    save_as_item.connect("activate", window._save_preset_as)
    filemenu.append(save_as_item)
    load_item = Gtk.MenuItem("Load preset")
    load_item.connect("activate", window._load_preset)
    filemenu.append(load_item)
    exit_item = Gtk.MenuItem("Exit")
    exit_item.connect("activate", window._emit_delete_event)
    filemenu.append(exit_item)

    helpmenu = Gtk.Menu()
    help_item = Gtk.MenuItem("Help")
    help_item.set_submenu(helpmenu)
    
    mouseSeq_item = Gtk.MenuItem("Mouse sequence")
    mouseSeq_item.connect("activate", window._mouseSeqInfo)
    helpmenu.append(mouseSeq_item)
    kbmMap_item = Gtk.MenuItem("Keyboard to mouse map")
    kbmMap_item.connect("activate", window._kbmInfo)
    helpmenu.append(kbmMap_item)

    aboutmenu = Gtk.Menu()
    about_item = Gtk.MenuItem("About")
    about_item.set_submenu(aboutmenu)

    github_item = Gtk.MenuItem("This project on GitHub")
    github_item.connect("activate", _launchBrowser, "https://github.com/mikeabbott10/AutOMG")
    aboutmenu.append(github_item)
    aboutUs_item = Gtk.MenuItem("Who i am")
    aboutUs_item.connect("activate", _launchBrowser, "https://amorellilorenzo.it")
    aboutmenu.append(aboutUs_item)

    menu.append(file_item)
    menu.append(help_item)
    menu.append(about_item)
    window._menu = menu

class AutOMGWindow(Gtk.Window):
    """
    Window class, here we build the gui
    """
    def __init__(self, MainProgram):
        Gtk.Window.__init__(self, title="AutOMG")
        self.Gtk = Gtk
        self.MainProgram = MainProgram # the non-gui thread
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
    
        _buildMenu(self)

        self._mainBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(self._mainBox)
        self._mainBox.add(self._menu)

        frame1 = Gtk.Frame()
        frame1.set_label("Mouse sequence")
        frame1.set_border_width(4)
        firstRow = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        frame1.add(firstRow)
        self._mainBox.add(frame1)

        frame2 = Gtk.Frame()
        frame2.set_label("Keyboard to mouse map")
        frame2.set_border_width(4)
        secondRow = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        frame2.add(secondRow)
        self._mainBox.add(frame2)

        statusbarRow = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._mainBox.add(statusbarRow)


        # record mouse sequence stuff
        self._recordMouseSeq_box = Gtk.Box(spacing=5) # box
        # label
        label = Gtk.Label(label="Samples:")
        self._recordMouseSeq_box.pack_start(label, True, True, 0)
        # spin
        adjustment = Gtk.Adjustment(value=0, upper=9, step_increment=1, page_increment=1) # number range
        self._recordSpinbutton = Gtk.SpinButton()
        self._recordSpinbutton.set_adjustment(adjustment)
        self._recordSpinbutton.set_numeric(True)
        self._recordSpinbutton.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID) # update values only if valid (in range)
        self._recordSpinbutton.connect("value-changed", self._on_record_spin_value_changed)
        self._recordMouseSeq_box.pack_start(self._recordSpinbutton, True, True, 0)
        # record mouse sequence button
        self._recordMouseSeq_button = Gtk.ToggleButton.new_with_label("Record")
        self._recordMouseSeq_button.set_active(False)
        self._recordMouseSeq_button.connect("toggled", self._on_recordMouseSequence_click)
        self._recordMouseSeq_box.pack_start(self._recordMouseSeq_button, True, True, 0)
        firstRow.pack_start(self._recordMouseSeq_box, True, True, 0)
        self._recordMouseSeq_box.set_border_width(3)

        # play mouse sequence stuff
        self._playMSeq_box = Gtk.Box(spacing=5) # box
        # label
        label = Gtk.Label(label="Times:")
        self._playMSeq_box.pack_start(label, True, True, 0)
        # spin
        adjustment = Gtk.Adjustment(value=0, upper=100, step_increment=1, page_increment=10) # number range
        self._playingSpinbutton = Gtk.SpinButton()
        self._playingSpinbutton.set_adjustment(adjustment)
        self._playingSpinbutton.set_numeric(True)
        self._playingSpinbutton.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID) # update values only if valid (in range)
        self._playingSpinbutton.connect("value-changed", self._on_playing_spin_value_changed)
        self._playMSeq_box.pack_start(self._playingSpinbutton, True, True, 0)

        # label
        label = Gtk.Label(label="Play")
        self._playMSeq_box.pack_start(label, True, True, 0)
        # switch
        self._playMouseSeq_switch = Gtk.Switch()
        self._playMouseSeq_switch.connect("notify::active", self._on_playMouseSeq_switch_click)
        self._playMouseSeq_switch.set_active(False)
        self._playMouseSeq_switch.set_margin_top(2)
        self._playMouseSeq_switch.set_margin_bottom(2)
        self._playMSeq_box.pack_start(self._playMouseSeq_switch, True, True, 0)
        firstRow.pack_start(self._playMSeq_box, True, True, 0) # attach to secondRow
        self._playMSeq_box.set_border_width(3)


    
        # keyboard-mouse mapping stuff
        self._record_kbm_box = Gtk.Box(spacing=5) # box
        # record keyboard-mouse mapping button
        self._recordKeyboardToMouse_button = Gtk.ToggleButton.new_with_label("Record map")
        self._recordKeyboardToMouse_button.set_active(False)
        self._recordKeyboardToMouse_button.connect("toggled", self._on_recordKeyboardToMouse_click)
        self._record_kbm_box.pack_start(self._recordKeyboardToMouse_button, True, True, 0)
        # mapping button
        self._kbm_map_button = Gtk.Button.new_with_label("Map")
        self._kbm_map_button.connect("clicked", self._on_kbm_map_button_click)
        self._record_kbm_box.pack_start(self._kbm_map_button, True, True, 0)
        secondRow.pack_start(self._record_kbm_box, True, True, 0)
        self._record_kbm_box.set_border_width(3)

        # keyboard-mouse mapping mode
        self._playKBM_box = Gtk.Box(spacing=5)
        item = Gtk.Label(label="Play mapping mode")
        item.set_margin_left(10)
        item.set_margin_right(5)
        self._playKBM_box.pack_start(item, True, True, 0)
        self._playKeyboardToMouse_switch = Gtk.Switch()
        self._playKeyboardToMouse_switch.connect("notify::active", self._on_playKeyboardToMouseSwitch_click)
        self._playKeyboardToMouse_switch.set_active(False)
        self._playKeyboardToMouse_switch.set_margin_left(5)
        self._playKeyboardToMouse_switch.set_margin_right(10)
        self._playKBM_box.pack_start(self._playKeyboardToMouse_switch,True,True,0)
        secondRow.pack_start(self._playKBM_box, True, True, 0)
        self._playKBM_box.set_border_width(3)

        # status bar
        self.statusBar = Gtk.Statusbar()
        # context identifier
        self.context_id = self.statusBar.get_context_id("Statusbar example")
        # push() method pushes a new message with the specified context_id onto a statusbar's stack 
        self.statusBar.push(self.context_id, "Ready")
        statusbarRow.pack_start(self.statusBar, True, True, 0)

    # spin change callbacks
    def _on_playing_spin_value_changed(self, scroll):
        config.mouse_sequence_playingTimes = self._playingSpinbutton.get_value_as_int()
    def _on_record_spin_value_changed(self, scroll):
        val = self._recordSpinbutton.get_value_as_int()
        config.mouse_sequence_movementSamplingTime = 0 if val==0 else (mapp(val, 1, 9, 18, 2)/10)

    # mouse sequence related buttons and switch click callbacks
    def _on_recordMouseSequence_click(self, btn):
        config.state = config.RECORDING_MOUSE_SEQ if btn.get_active() else config.READY
        getattr(self, "modifyWidgetsWithState_"+config.state, lambda: None)()
        config.stateEvent.set()
    def _on_playMouseSeq_switch_click(self, switch, gparam):
        config.state = config.PLAYING_MOUSE_SEQ if switch.get_active() else config.READY
        getattr(self, "modifyWidgetsWithState_"+config.state, lambda: None)()
        config.stateEvent.set()
    # kbm mapping related buttons and switch click callbacks
    def _on_recordKeyboardToMouse_click(self, btn):
        config.state = config.RECORDING_KBM_CONNECTIONS if btn.get_active() else config.READY
        getattr(self, "modifyWidgetsWithState_"+config.state, lambda: None)()
        config.stateEvent.set()
    def _on_playKeyboardToMouseSwitch_click(self, switch, gparam):
        config.state = config.PLAYING_KBM_CONNECTIONS if switch.get_active() else config.READY
        getattr(self, "modifyWidgetsWithState_"+config.state, lambda: None)()
        config.stateEvent.set()
    def _on_kbm_map_button_click(self, btn):
        txt = '  '.join(f'{key}' for key in config.currentPreset['kbmMap'].keys())
        self.openDialog(
            title="Mapped keys", 
            messageType=Gtk.MessageType.INFO,
            text=txt
        )
    # disable or enable widgets related
    def modifyWidgetsWithState_recording_mouse_seq(self):
        self._recordMouseSeq_box.set_sensitive(True)
        self._recordMouseSeq_button.set_label("Stop")
        self._menu.set_sensitive(False)
        self._record_kbm_box.set_sensitive(False)
        self._playKBM_box.set_sensitive(False)
        self._playMSeq_box.set_sensitive(False)
        self.statusBar.pop(self.context_id)
        self.statusBar.push(self.context_id, "Recording mouse events")
    def modifyWidgetsWithState_playing_mouse_seq(self):
        self._playMSeq_box.set_sensitive(True)
        self._menu.set_sensitive(False)
        self._recordMouseSeq_box.set_sensitive(False)
        self._record_kbm_box.set_sensitive(False)
        self._playKBM_box.set_sensitive(False)
        self.statusBar.pop(self.context_id)
        self.statusBar.push(self.context_id, "Playing mouse events")
    def modifyWidgetsWithState_recording_kbm_connections(self):
        self._record_kbm_box.set_sensitive(True)
        self._recordKeyboardToMouse_button.set_label("Stop")
        self._menu.set_sensitive(False)
        self._recordMouseSeq_box.set_sensitive(False)
        self._playMSeq_box.set_sensitive(False)
        self._playKBM_box.set_sensitive(False)
        self.statusBar.pop(self.context_id)
        self.statusBar.push(self.context_id, "Waiting for keyboard input")
    def modifyWidgetsWithState_playing_kbm_connections(self):
        self._playKBM_box.set_sensitive(True)
        self._menu.set_sensitive(False)
        self._recordMouseSeq_box.set_sensitive(False)
        self._record_kbm_box.set_sensitive(False)
        self._playMSeq_box.set_sensitive(False)
        self.statusBar.pop(self.context_id)
        self.statusBar.push(self.context_id, "Mapping mode on")
    def modifyWidgetsWithState_ready(self):
        self._menu.set_sensitive(True)
        self._recordMouseSeq_box.set_sensitive(True)
        self._recordMouseSeq_button.set_label("Record")
        self._recordMouseSeq_button.set_active(False)
        self._playMSeq_box.set_sensitive(True)
        self._record_kbm_box.set_sensitive(True)
        self._recordKeyboardToMouse_button.set_label("Record")
        self._recordKeyboardToMouse_button.set_active(False)
        self._playKBM_box.set_sensitive(True)
        self._playMouseSeq_switch.set_active(False)
        self._playKeyboardToMouse_switch.set_active(False)
        self.statusBar.pop(self.context_id)
        self.statusBar.push(self.context_id, "Ready")

    # menu bar callbacks
    def _save_preset(self, widget):
        if(self.MainProgram.lastPresetPath != None):
            import pickle
            self.MainProgram.lastPreset = copy.deepcopy(config.currentPreset) # update last preset 
            with open(self.MainProgram.lastPresetPath, 'wb') as fp:
                pickle.dump(config.currentPreset, fp, protocol=pickle.HIGHEST_PROTOCOL)
        else:
            self._save_preset_as(widget)
    def _save_preset_as(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Save as...", parent=self, action=Gtk.FileChooserAction.SAVE
        )
        if(self.MainProgram.lastPresetPath != None):
            lastPresetName = self.MainProgram.lastPresetPath.split('/')[-1]
            dialog.set_current_name(lastPresetName)
        dialog.set_do_overwrite_confirmation(True)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE,
            Gtk.ResponseType.OK,
        )

        response = dialog.run()
        filepath = ''
        if response == Gtk.ResponseType.OK:
            # print("Open clicked")
            filepath = dialog.get_filename()
            dialog.destroy()
            if(filepath[-4:]!=".omg"):
                filepath += ".omg"
            import pickle
            self.MainProgram.lastPreset = copy.deepcopy(config.currentPreset) # update last preset 
            self.MainProgram.lastPresetPath = filepath # update last preset path
            with open(filepath, 'wb') as fp:
                pickle.dump(config.currentPreset, fp, protocol=pickle.HIGHEST_PROTOCOL)
        elif response == Gtk.ResponseType.CANCEL:
            #print("Cancel clicked")
            dialog.destroy()
    #filters for file chooser dialog
    def _add_filters(self, dialog):
        filter_omg = Gtk.FileFilter()
        filter_omg.set_name("OMG files")
        filter_omg.add_pattern("*.omg")
        dialog.add_filter(filter_omg)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)
    def _load_preset(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Please choose a file", parent=self, action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )

        self._add_filters(dialog)

        response = dialog.run()
        filepath = ''
        if response == Gtk.ResponseType.OK:
            # print("Open clicked")
            filepath = dialog.get_filename()
            dialog.destroy()
            if(filepath[-4:]!=".omg"):
                self.openDialog(
                    title="Wrong file",
                    messageType= Gtk.MessageType.ERROR,
                    text="Please choose a valid .omg file")
            else:
                try:
                    import pickle
                    with open(filepath, 'rb') as fp:
                        data = pickle.load(fp)
                
                    config.isPresetValid(data)
                
                    config.currentPreset = data # upload current preset
                    self.MainProgram.lastPreset = copy.deepcopy(config.currentPreset) # and last preset 
                    self.MainProgram.lastPresetPath = filepath # update last preset path
                except:
                    self.openDialog(
                        title="Wrong file",
                        messageType= Gtk.MessageType.ERROR,
                        text="Please choose a valid .omg file")
                
        elif response == Gtk.ResponseType.CANCEL:
            #print("Cancel clicked")
            dialog.destroy()
        
    # dialog related functions
    # open message dialog
    def openDialog(self, title, messageType, text):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=messageType,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        dialog.format_secondary_text(text)
        dialog.run()
        dialog.destroy()
    # open dialog for "unhandled" exception
    def openExceptionDialog(self, title, exceptionText):
        dialog = Gtk.Dialog(
            transient_for=self,
            flags=0,
            title=title
        )

        label = Gtk.Label(label="Please report this issue on GitHub:")
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_cursor_visible(False)
        exceptionTextBuffer = Gtk.TextBuffer()
        exceptionTextBuffer.set_text(exceptionText)
        text_view.set_buffer(exceptionTextBuffer)
        
        box = dialog.get_content_area()
        box.add(label)
        box.add(text_view)
        dialog.show_all()
        dialog.run()
        dialog.destroy()
    # info 
    def _mouseSeqInfo(self, widget):
        self.openDialog(
            title="Usage", 
            messageType=Gtk.MessageType.INFO,
            text="You can record mouse events (movement, clicks and drags) using the 'Record' button."+
            " You are going to append your mouse events to the end of the current sequence already recorded."+
            " If you want to clear the sequence AND the keyboard-mouse mapping, please click on File -> Reset preset.\n\n"+
            "Samples: how many mouse movement samples per 2 seconds. If zero only clicks and drags will be recorded.\n\n"+
            "Times: how many times the recorded sequence will be played. If zero it will play forever.\n\n"+
            "Click on Play switch to start, then, if needed, 'Esc' key on keyboard to stop."
        )
    def _kbmInfo(self, widget):
        self.openDialog(
            title="Usage", 
            messageType=Gtk.MessageType.INFO,
            text="You can record mouse clicks and map them to keys on keyboard\n\n"+
            "Record map button: start recording your mapping. You can read the next expected event in the status bar below."+
            " Tap on a key and then perform a click on the screen with the mouse."+
            " The mapping between these two actions are automatically saved. Click the Stop button to stop recording.\n\n"+
            "Map button: you can see a list of keys already mapped.\n\n"+
            "Start and stop the mapping mode using the switch.\n\n"+
            " If you want to clear the keyboard-mouse mapping AND the recorded mouse sequence, please click on File -> Reset preset.\n\n"
            "Note: the keyboard actions are propagated to the system."
        )

    # fixing size (called from main)
    def fixWidgetsSize(self):
        # wanna fix mouse sequence button
        self._recordMouseSeq_button.set_size_request(
            self._recordMouseSeq_button.get_allocated_width(),
            self._recordMouseSeq_button.get_allocated_height()
        )
         # wanna fix kbm button
        self._recordKeyboardToMouse_button.set_size_request(
            self._recordKeyboardToMouse_button.get_allocated_width(),
            self._recordKeyboardToMouse_button.get_allocated_height()
        )

        # same size for similar widgets
        self._playKeyboardToMouse_switch.set_size_request(
            self._playMouseSeq_switch.get_allocated_width(),
            self._playMouseSeq_switch.get_allocated_height()
        )

    # quit callback
    def quit_cb(self, unsavedChanges):
        if(not unsavedChanges):
            return True # quit
        else:
            dialog = Gtk.Dialog(title="Unsaved changes", transient_for=self, flags=0)
            dialog.add_buttons(
                Gtk.STOCK_QUIT, Gtk.ResponseType.OK, 
                Gtk.STOCK_GO_BACK, Gtk.ResponseType.CANCEL
            )

            dialog.set_default_size(150, 100)

            label = Gtk.Label(label="\nChanges you made may not be saved")

            box = dialog.get_content_area()
            box.add(label)
            dialog.show_all()
            response = dialog.run()
            dialog.destroy()
            return response == Gtk.ResponseType.OK
    
    # this function override the delete-event signal handler (called when the "x" button is clicked)
    def _emit_delete_event(self, widget):
        self.emit("delete-event", None)

# map a value in a range
def mapp(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)
