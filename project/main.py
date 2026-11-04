import sys
import time
import json
import requests
import lvgl as lv
import network

from board_lvgl import start_board
from debug_log import log
from secrets import WIFI_SSID, WIFI_PASSWORD, TRAFIKLAB_API_KEY

STOPS = {
    "Campus Grasvik": "740032188",
    "Karlskrona Centralstation": "740000230"
}
INTERVALS = [30, 60, 120]
SETTINGS_FILE = "settings.json"

WHITE = 0xFFFFFF
NAVY = 0x172B4D
BLUE = 0x1764C0
LIGHT_BLUE = 0xEAF2FF
LIGHT_GRAY = 0xF4F7FB
GRAY = 0x64748B


class Application:
    def __init__(self):
        self.display, self.touch, self.handler = start_board()
        self.stop_name = "Campus Grasvik"
        self.refresh_interval = 60
        self.load_settings()
        self.create_ui()
        self.connect_wifi()
        self.fetch_departures()
        self.refresh_timer = lv.timer_create(self.update_departures, self.refresh_interval * 1000, None)
        log("student application ready")

    @staticmethod
    def background(obj, color):
        obj.set_style_bg_opa(lv.OPA.COVER, 0)
        obj.set_style_bg_color(lv.color_hex(color), 0)

    @staticmethod
    def text_style(obj, color, font):
        obj.set_style_text_color(lv.color_hex(color), 0)
        obj.set_style_text_font(font, 0)

    def add_label(self, parent, text, x, y, color=NAVY, font=None):
        label = lv.label(parent)
        label.set_text(text)
        self.text_style(label, color, font or lv.font_montserrat_20)
        label.align(lv.ALIGN.TOP_LEFT, x, y)
        return label

    def create_ui(self):
        self.tileview = lv.tileview(lv.screen_active())
        self.tileview.set_size(600, 450)
        self.tileview.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)

        self.tile1 = self.tileview.add_tile(0, 0, lv.DIR.RIGHT)
        self.tile2 = self.tileview.add_tile(1, 0, lv.DIR.LEFT | lv.DIR.RIGHT)
        self.tile3 = self.tileview.add_tile(2, 0, lv.DIR.LEFT)

        for tile in (self.tile1, self.tile2, self.tile3):
            self.background(tile, WHITE)

        self.create_start_screen()
        self.create_departure_screen()
        self.create_settings_screen()

    def create_start_screen(self):
        title = self.add_label(self.tile1, "Public Transport Information", 0, 0, NAVY, lv.font_montserrat_28)
        title.align(lv.ALIGN.CENTER, 0, -45)

        subtitle = self.add_label(self.tile1, "Group_23\nHesam, Joudi, Elsa, Julia, Adam, Sara\nV1.2.4", 0, 0, GRAY, lv.font_montserrat_16)
        subtitle.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        subtitle.align(lv.ALIGN.CENTER, 0, 20)

        slide = self.add_label(self.tile1, "Swipe left for departures >>", 0, 0, BLUE, lv.font_montserrat_16)
        slide.align(lv.ALIGN.BOTTOM_RIGHT, -15, -15)

    def create_departure_screen(self):
        self.heading = self.add_label(self.tile2, self.stop_name, 24, 18, NAVY, lv.font_montserrat_28)
        self.add_label(self.tile2, "LIVE DEPARTURES", 26, 56, GRAY, lv.font_montserrat_16)

        banner = lv.obj(self.tile2)
        banner.set_size(552, 46)
        banner.align(lv.ALIGN.TOP_LEFT, 24, 90)
        banner.set_style_radius(10, 0)
        banner.set_style_border_width(0, 0)
        banner.set_style_pad_all(0, 0)
        banner.remove_flag(lv.obj.FLAG.SCROLLABLE)
        self.background(banner, LIGHT_BLUE)

        text = self.add_label(banner, "Upcoming departures", 15, 0, BLUE)
        text.align(lv.ALIGN.LEFT_MID, 15, 0)

        for name, x in [("LINE", 28), ("DESTINATION", 115), ("TIME", 390), ("STOP", 510)]:
            self.add_label(self.tile2, name, x, 151, GRAY, lv.font_montserrat_16)

        self.rows = []

        for i in range(5):
            row = lv.obj(self.tile2)
            row.set_size(552, 36)
            row.align(lv.ALIGN.TOP_LEFT, 24, 183 + i * 39)
            row.set_style_radius(7, 0)
            row.set_style_border_width(0, 0)
            row.set_style_pad_all(0, 0)
            row.remove_flag(lv.obj.FLAG.SCROLLABLE)
            self.background(row, LIGHT_GRAY if i % 2 == 0 else WHITE)

            badge = lv.obj(row)
            badge.set_size(48, 29)
            badge.align(lv.ALIGN.LEFT_MID, 5, 0)
            badge.set_style_radius(6, 0)
            badge.set_style_border_width(0, 0)
            badge.set_style_pad_all(0, 0)
            badge.remove_flag(lv.obj.FLAG.SCROLLABLE)
            self.background(badge, BLUE)

            line = self.add_label(badge, "-", 0, 0, WHITE)
            line.center()

            destination = self.add_label(row, "-", 91, 0)
            destination.align(lv.ALIGN.LEFT_MID, 91, 0)

            departure_time = self.add_label(row, "--:--", 365, 0)
            departure_time.align(lv.ALIGN.LEFT_MID, 365, 0)

            stop = self.add_label(row, "-", 488, 0, GRAY)
            stop.align(lv.ALIGN.LEFT_MID, 488, 0)

            self.rows.append((line, destination, departure_time, stop))

        self.status = self.add_label(self.tile2, "Connecting...", 24, 410, GRAY, lv.font_montserrat_16)
        self.add_label(self.tile2, "Data: Trafiklab.se", 420, 410, GRAY, lv.font_montserrat_16)

    def create_settings_screen(self):
        self.add_label(self.tile3, "Settings", 24, 18, NAVY, lv.font_montserrat_28)
        self.add_label(self.tile3, "Customize your departure display", 26, 58, GRAY, lv.font_montserrat_16)

        self.add_label(self.tile3, "Bus stop", 30, 115)

        self.stop_dropdown = lv.dropdown(self.tile3)
        self.stop_dropdown.set_options("\n".join(STOPS.keys()))
        self.stop_dropdown.set_size(520, 45)
        self.stop_dropdown.align(lv.ALIGN.TOP_LEFT, 30, 145)
        self.stop_dropdown.set_selected(list(STOPS.keys()).index(self.stop_name))

        self.add_label(self.tile3, "Refresh interval", 30, 215)

        self.interval_dropdown = lv.dropdown(self.tile3)
        self.interval_dropdown.set_options("30 seconds\n60 seconds\n120 seconds")
        self.interval_dropdown.set_size(520, 45)
        self.interval_dropdown.align(lv.ALIGN.TOP_LEFT, 30, 245)
        self.interval_dropdown.set_selected(INTERVALS.index(self.refresh_interval))

        self.save_button = lv.button(self.tile3)
        self.save_button.set_size(220, 50)
        self.save_button.align(lv.ALIGN.TOP_MID, 0, 325)
        self.background(self.save_button, BLUE)
        self.save_button.add_event_cb(self.save_settings, lv.EVENT.CLICKED, None)

        save_text = lv.label(self.save_button)
        save_text.set_text("Save Settings")
        self.text_style(save_text, WHITE, lv.font_montserrat_20)
        save_text.center()

        self.settings_status = self.add_label(self.tile3, "Swipe right to return", 30, 405, GRAY, lv.font_montserrat_16)

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, "r") as file:
                data = json.load(file)

            stop = data.get("stop", self.stop_name)
            interval = data.get("interval", self.refresh_interval)

            if stop in STOPS:
                self.stop_name = stop
            if interval in INTERVALS:
                self.refresh_interval = interval

            log("Settings loaded")
        except (OSError, ValueError, TypeError):
            log("Using default settings")

    def save_settings(self, event):
        stop_index = self.stop_dropdown.get_selected()
        interval_index = self.interval_dropdown.get_selected()

        new_stop = list(STOPS.keys())[stop_index]
        new_interval = INTERVALS[interval_index]

        try:
            with open(SETTINGS_FILE, "w") as file:
                json.dump({"stop": new_stop, "interval": new_interval}, file)
        except OSError as error:
            log("Settings save failed: %r" % (error,))
            self.settings_status.set_text("Could not save settings")
            return

        self.stop_name = new_stop
        self.refresh_interval = new_interval
        self.heading.set_text(self.stop_name)
        self.refresh_timer.set_period(self.refresh_interval * 1000)
        self.settings_status.set_text("Settings saved!")
        self.fetch_departures()
        log("Settings saved")

    @staticmethod
    def connect_wifi():
        station = network.WLAN(network.STA_IF)
        station.active(True)

        if not station.isconnected():
            station.connect(WIFI_SSID, WIFI_PASSWORD)

        started = time.ticks_ms()
        while not station.isconnected() and time.ticks_diff(time.ticks_ms(), started) < 15000:
            time.sleep_ms(250)

        log("Wi-Fi connected" if station.isconnected() else "Wi-Fi connection failed")

    def update_departures(self, timer):
        log("Refreshing departures...")
        self.fetch_departures()

    def fetch_departures(self):
        if not network.WLAN(network.STA_IF).isconnected():
            self.status.set_text("Wi-Fi disconnected")
            return

        url = "https://realtime-api.trafiklab.se/v1/departures/" + STOPS[self.stop_name] + "?key=" + TRAFIKLAB_API_KEY
        response = None

        try:
            response = requests.get(url)
            log("HTTP status: " + str(response.status_code))

            if response.status_code != 200:
                self.status.set_text("Trafiklab request failed")
                return

            departures = response.json().get("departures", [])
            log("Departures received: " + str(len(departures)))

            for line, destination, departure_time, stop in self.rows:
                line.set_text("-")
                destination.set_text("-")
                departure_time.set_text("--:--")
                stop.set_text("-")

            for row, departure in zip(self.rows, departures[:5]):
                route = departure.get("route") or {}
                platform = departure.get("realtime_platform") or departure.get("scheduled_platform") or {}
                time_value = departure.get("realtime") or departure.get("scheduled") or ""

                row[0].set_text(str(route.get("designation") or "-"))
                destination = str(route.get("direction") or "-")
                for old, new in [("å", "a"), ("ä", "a"), ("ö", "o"), ("Å", "A"), ("Ä", "A"), ("Ö", "O")]:
                    destination = destination.replace(old, new)
                row[1].set_text(destination)
                row[2].set_text(time_value[11:16] if len(time_value) >= 16 else "--:--")
                row[3].set_text(str(platform.get("designation") or "-"))

            self.status.set_text("Departures loaded" if departures else "No departures available")

        except Exception as error:
            log("Trafiklab error: %r" % (error,))
            self.status.set_text("Error loading departures")

        finally:
            if response is not None:
                response.close()


try:
    app = Application()
except Exception as error:
    log("FATAL: %r" % (error,))
    sys.print_exception(error)
    raise
