import os
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')
from gi.repository import Gtk as gtk
try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3 as appindicator
except:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as appindicator
from gi.repository import GLib as glib
from gi.repository import Notify as notify

APPINDICATOR_ID = 'indicatorfromtbk'

import time
from threading import Thread
import json
import typing
from urllib.request import urlopen, Request

from tbkpy.config import TBK_STATUE_INTERVAL
from tbkpy.admin.status import StatusNode, Status

class MainWindow(gtk.Window):
    def __init__(self):
        super().__init__(title="tbkadm")
        self.set_default_size(800, 600)
        self.set_position(gtk.WindowPosition.CENTER)
        self.button = gtk.Button(label="Click Me")
        self.button.connect("clicked", self.on_button_clicked)
        self.add(self.button)
    
    def on_button_clicked(self, widget):
        print(f"Hello World, {widget}")

class Indicator():
    def __init__(self):
        self.indicator = appindicator.Indicator.new(APPINDICATOR_ID, self._getIcon(), appindicator.IndicatorCategory.SYSTEM_SERVICES)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self._create_menu())
        self.indicator.set_label("TBK", APPINDICATOR_ID)

        self.statusNode = StatusNode()
        self._updateThread = Thread(target=self._updateThread)
        self._updateThread.start()
    def _create_menu(self):
        menu = gtk.Menu()

        nodes_menu = gtk.Menu()

        # a = gtk.MenuItem(label='Node A')
        # nodes_menu.append(a)
        # b = gtk.MenuItem(label='Node B')
        # nodes_menu.append(b)

        # radioTest = gtk.RadioMenuItem(label='Radio Test')
        # menu.append(radioTest)

        # checkTest = gtk.CheckMenuItem(label='Check Test')
        # menu.append(checkTest)

        item_current_nodes = gtk.MenuItem(label='Current Nodes')
        item_current_nodes.set_submenu(nodes_menu)
        menu.append(item_current_nodes)

        item_local_reset = gtk.MenuItem(label='Local Reset Cluster')
        item_local_reset.connect('activate', self._localReset)
        menu.append(item_local_reset)

        item_local_init = gtk.MenuItem(label='Local Init New Cluster')
        item_local_init.connect('activate', self._localInit)
        menu.append(item_local_init)

        item_window = gtk.MenuItem(label='Open Window')
        item_window.connect('activate', self._create_win)
        menu.append(item_window)

        item_quit = gtk.MenuItem(label='Quit')
        item_quit.connect('activate', self._quit)
        menu.append(item_quit)

        menu.show_all()
        return menu
    
    def _quit(self, source):
        notify.uninit()
        gtk.main_quit()

    def _localReset(self, source):
        self.statusNode.tbklocal.adminReset()

    def _localInit(self, source):
        self.statusNode.tbklocal.adminInit()

    def resetNodeList(self, nodes):
        pass
    def resetLabel(self,label,status=None):
        glib.idle_add(
            self.indicator.set_label,
            label, APPINDICATOR_ID,
            priority=glib.PRIORITY_DEFAULT
        )
        if status:
            glib.idle_add(
                self.indicator.set_icon,
                self._getIcon(status),
                priority=glib.PRIORITY_DEFAULT
            )
    def _create_win(self, source):
        self.window = MainWindow()
        self.window.show_all()
    
    def _getIcon(self, status: typing.Optional[str]=None):
        if status is None:
            status = "orange"
        return os.path.join(os.path.dirname(__file__),f"tbk_{status}.png")

    def _updateThread(self):
        while True:
            time.sleep(TBK_STATUE_INTERVAL)
            # print(self.statusNode.localStatus)
            title, label = self.getLabels(self.statusNode.localStatus)
            self.resetLabel(f"TBK-({title})",label)

    def getLabels(self, status: Status):
        label = "orange"
        if status.health == "true":
            label = "blue" if len(status.clusters) > 1 else "green"
        return len(status.clusters), label

def checkScreen():
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk
    s = Gdk.Screen.get_default()
    return s is not None

def main():
    if checkScreen():
        indicator = Indicator()
        notify.init(APPINDICATOR_ID)
        gtk.main()
        return
    print("No Screen Found")
    statusNode = StatusNode()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()