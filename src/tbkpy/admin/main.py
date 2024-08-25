import os
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)
import gi
gi.require_version('Gtk', '3.0')
gi.require_version("Gdk", "3.0")
gi.require_version('Notify', '0.7')
from gi.repository import Gtk as gtk, Gdk as gdk
try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3 as appindicator
except:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as appindicator
from gi.repository import GLib as glib
from gi.repository import Notify as notify
import cairo

APPINDICATOR_ID = 'indicatorfromtbk'

import time
from threading import Thread
import json
import typing
import math
from urllib.request import urlopen, Request

from tbkpy.config import TBK_STATUE_INTERVAL
from tbkpy.admin.status import StatusNode, Status

# class MainWindow(gtk.Window):
#     def __init__(self, statusNode):
#         super().__init__(title="tbkadm")
#         self.statusNode = statusNode
#         self.set_default_size(800, 600)
#         self.set_position(gtk.WindowPosition.CENTER)
#         self.button = gtk.Button(label="Click Me")
#         self.button.connect("clicked", self.on_button_clicked)
#         self.add(self.button)
    
#     def on_button_clicked(self, widget):
#         print(f"Hello World, {widget}")

# 节点数据结构示例
nodes = [
    {'ip': '192.168.1.1', 'status': 'running', 'is_current': False, 'in_cluster': True},
    {'ip': '192.168.1.2', 'status': 'stopped', 'is_current': True, 'in_cluster': True},
    {'ip': '192.168.1.3', 'status': 'running', 'is_current': False, 'in_cluster': False},
    {'ip': '192.168.1.4', 'status': 'running', 'is_current': False, 'in_cluster': True},
    {'ip': '192.168.1.5', 'status': 'stopped', 'is_current': False, 'in_cluster': False},
]

class MainWindow(gtk.Window):
    def __init__(self, statusNode):
        super().__init__(title="tbkadm")
        self.set_default_size(800, 600)
        self.statusNode = statusNode

        # 初始化缩放和拖拽状态
        self.scale_factor = 1.0
        self.end_x = 0
        self.end_y = 0
        self.clicked_node = None
        self.hovered_node = None

        # 创建一个绘图区
        self.drawing_area = gtk.DrawingArea()
        self.drawing_area.add_events(gdk.EventMask.SCROLL_MASK | gdk.EventMask.BUTTON_PRESS_MASK | gdk.EventMask.BUTTON_RELEASE_MASK | gdk.EventMask.POINTER_MOTION_MASK)
        self.drawing_area.connect("draw", self.on_draw)
        self.drawing_area.connect("scroll-event", self.on_scroll)
        self.drawing_area.connect("button-press-event", self.on_button_press)
        self.drawing_area.connect("button-release-event", self.on_button_release)
        self.drawing_area.connect("motion-notify-event", self.on_motion_notify)
        self.add(self.drawing_area)
        self.show_all()

    def on_draw(self, widget, cr):
        # 获取画布大小
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        
        # 应用缩放
        cr.translate(width/2,height/2)
        cr.scale(self.scale_factor, self.scale_factor)

        # 计算中心位置
        center_x = 0
        center_y = 0
        
        # 设置节点半径和布局半径
        node_radius = min(width, height) / 8
        layout_radius = min(width, height) / 3
        
        # 绘制每个节点
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / len(nodes)
            if node['is_current']:
                x = center_x
                y = center_y
            else:
                x = center_x + layout_radius * math.cos(angle)
                y = center_y + layout_radius * math.sin(angle)
            
            node["pose"] = (x, y, node_radius)
            # 绘制连接线
            if node['in_cluster'] and not node['is_current']:
                cr.set_line_width(2)
                cr.set_source_rgb(0.5, 0.5, 0.5)  # 灰色线条
                cr.move_to(center_x, center_y)
                cr.line_to(x, y)
                cr.stroke()
            
            # 绘制节点
            self.draw_node(cr, x, y, node_radius, node)
        if self.clicked_node is not None:
            cr.set_source_rgb(0, 0, 0)
            cr.set_line_width(4)
            cr.move_to(self.clicked_node['pose'][0], self.clicked_node['pose'][1])
            cr.line_to(self.end_x, self.end_y)
            cr.stroke()

    def draw_node(self, cr, x, y, radius, node):
        # 设置渐变填充
        gradient = cairo.RadialGradient(x, y, radius / 2, x, y, radius)
        if node['status'] == 'running':
            gradient.add_color_stop_rgb(0, 0.2, 0.8, 0.2)  # 绿色渐变
            gradient.add_color_stop_rgb(1, 0, 0.5, 0)      # 深绿色边缘
        else:
            gradient.add_color_stop_rgb(0, 0.8, 0.2, 0.2)  # 红色渐变
            gradient.add_color_stop_rgb(1, 0.5, 0, 0)      # 深红色边缘
        
        # 绘制渐变圆形
        cr.set_source(gradient)
        cr.arc(x, y, radius, 0, 2 * math.pi)
        cr.fill_preserve()

        # 添加阴影效果
        cr.set_source_rgba(0, 0, 0, 0.3)  # 黑色阴影
        cr.set_line_width(0)
        cr.stroke()

        # 绘制IP地址文本
        cr.set_source_rgb(0, 0, 0)
        cr.set_font_size(12)
        text_extents = cr.text_extents(node['ip'])
        cr.move_to(x - text_extents.width / 2, y + text_extents.height / 2)
        cr.show_text(node['ip'])

    def on_scroll(self, widget, event):
        # 实现缩放功能
        if event.direction == gdk.ScrollDirection.UP:
            self.scale_factor *= 1.1  # 放大
        elif event.direction == gdk.ScrollDirection.DOWN:
            self.scale_factor /= 1.1  # 缩小
        self.scale_factor = max(0.1, self.scale_factor)  # 缩放范围限制
        self.scale_factor = min(10, self.scale_factor)

        self.drawing_area.queue_draw()  # 重新绘制
    
    def on_button_press(self, widget, event):
        if event.button == 1:  # 检测左键点击
            if self.get_hover_node(widget, event) is not None:
                self.clicked_node = self.get_hover_node(widget, event)
                self.end_x, self.end_y = self.get_real_xy(widget, event.x, event.y)
                self.drawing_area.queue_draw()

    def on_button_release(self, widget, event):
        if event.button == 1:  # 检测左键释放
            if self.clicked_node is not None:
                hover_node = self.get_hover_node(widget, event)
                if hover_node is not None and hover_node != self.clicked_node:
                    # 连接两个节点
                    print(f"Connect {self.clicked_node['ip']} to {hover_node['ip']}")
        self.clicked_node = None
        self.drawing_area.queue_draw()
    def on_motion_notify(self, widget, event):
        if self.clicked_node is not None:
            self.end_x, self.end_y = self.get_real_xy(widget, event.x, event.y)
            self.drawing_area.queue_draw()
    def get_real_xy(self,widget,x,y):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        clicked_x = (x-width/2) / self.scale_factor
        clicked_y = (y-height/2) / self.scale_factor
        return clicked_x, clicked_y
    def get_hover_node(self, widget, event):
        x,y = self.get_real_xy(widget, event.x, event.y)
        for node in nodes:
            node_x, node_y, radius = node['pose']
            distance = math.sqrt((x - node_x) ** 2 + (y - node_y) ** 2)
            if distance <= radius:
                return node
        return None

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
        self.window = MainWindow(self.statusNode)
        self.window.show_all()
    
    def _getIcon(self, status: typing.Optional[str]=None):
        if status is None:
            status = "orange"
        return os.path.join(os.path.dirname(__file__),f"tbk_{status}.png")

    def _updateThread(self):
        while True:
            time.sleep(TBK_STATUE_INTERVAL)
            title, label = self.getLabels(self.statusNode.localStatus)
            self.resetLabel(f"TBK-({title})",label)

    def getLabels(self, status: Status):
        label = "orange"
        if status.health == "true":
            label = "blue" if len(status.clusters) > 1 else "green"
        return len(status.clusters), label

def checkScreen():
    s = gdk.Screen.get_default()
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