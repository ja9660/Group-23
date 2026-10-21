import sys
import time

import lvgl as lv
import network

from board_lvgl import start_board
from debug_log import log

from secrets import WIFI_SSID, WIFI_PASSWORD


class Application:
    def __init__(self):
        self.display, self.touch, self.handler = start_board()
        self.tile2_dark = False
        self.create_ui()
        self.connect_wifi()
        log("student application ready")

    @staticmethod
    def apply_tile_colors(tile, label, dark):
        tile.set_style_bg_opa(lv.OPA.COVER, 0)
        tile.set_style_bg_color(
            lv.color_hex(0x000000 if dark else 0xFFFFFF), 0
        )
        label.set_style_text_color(
            lv.color_hex(0xFFFFFF if dark else 0x000000), 0
        )

    def on_tile2_clicked(self, _event):
        self.tile2_dark = not self.tile2_dark
        self.apply_tile_colors(self.tile2, self.tile2_label, self.tile2_dark)

    def create_ui(self):
        'Function: Creates UI'
        self.tileview = lv.tileview(lv.screen_active())
        self.tileview.set_size(600, 450)
        self.tileview.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)

        self.tile1 = self.tileview.add_tile(0, 0, lv.DIR.RIGHT)
        self.tile2 = self.tileview.add_tile(1, 0, lv.DIR.LEFT)

        self.tile1_label = lv.label(self.tile1)
        self.tile1_label.set_text("Public Transport Information\n")
        self.tile1_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.tile1_label.align(lv.ALIGN.CENTER, 0, -20)
        self.apply_tile_colors(self.tile1, self.tile1_label, False)

        self.tile1_subtitle = lv.label(self.tile1)
        self.tile1_subtitle.set_text("Group_23\nHesam, Joudi, Elsa, Julia, Adam, Sara\nV1.2.4")
        self.tile1_subtitle.set_style_text_font(lv.font_montserrat_16, 0)
        self.tile1_subtitle.align(lv.ALIGN.CENTER, 0, 20)
        #self.tile1_subtitle.set_style_text_color(lv.color_hex(0x000000), 0)
        self.apply_tile_colors(self.tile1, self.tile1_subtitle, False)

        self.tile1_slide = lv.label(self.tile1)
        self.tile1_slide.set_text("Next Slide -->")
        self.tile1_slide.set_style_text_font(lv.font_montserrat_16, 0)
        self.tile1_slide.align(lv.ALIGN.BOTTOM_RIGHT, -10, -10)
        self.apply_tile_colors(self.tile1, self.tile1_slide, False)
        
        self.tile2_label = lv.label(self.tile2)
        self.tile2_label.set_text("Settings: ")
        self.tile2_label.set_style_text_font(lv.font_montserrat_28, 0)
        self.apply_tile_colors(self.tile2, self.tile2_label, False)
        self.tile2.add_flag(lv.obj.FLAG.CLICKABLE)
        self.tile2.add_event_cb(
            self.on_tile2_clicked, lv.EVENT.CLICKED, None
        )

        self.tile2_schedules = lv.label(self.tile2)
        self.tile2_schedules.set_text("Campus Grasvik -- Karlskrona Central\n\nKarlskrona Cental -- Campus Grasvik")
        self.tile2_schedules.set_style_text_font(lv.font_montserrat_20, 0)
        self.tile2_schedules.center()
        self.apply_tile_colors(self.tile2, self.tile2_schedules, False)
        self.tile2.add_flag(lv.obj.FLAG.CLICKABLE)
        self.tile2.add_event_cb(
            self.on_tile2_clicked, lv.EVENT.CLICKED, None
                )
    @staticmethod
    def connect_wifi():
        'Function: Connects to WiFi'
        log("connecting to Wi-Fi SSID: " + WIFI_SSID)
        station = network.WLAN(network.STA_IF)
        station.active(True)
        station.connect(WIFI_SSID, WIFI_PASSWORD)
        started = time.ticks_ms()
        while (not station.isconnected() and
               time.ticks_diff(time.ticks_ms(), started) < 15_000):
            time.sleep_ms(250)
        log("Wi-Fi connected" if station.isconnected()
            else "Wi-Fi could not connect (timeout)")


try:
    app = Application()
except Exception as error:
    log("FATAL: %r" % (error,))
    sys.print_exception(error)
    raise
