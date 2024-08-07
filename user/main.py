import json
import time
from time import sleep
from math import ceil
from threading import Thread
from io import BytesIO

from pynput.mouse import Controller, Button
from pyautogui import size as screen_size
from PIL.ImageGrab import grab as take_screenshot

from kivy.core.window import Window

import user_graphics
import user_network
import protocols


class Main:
    def __init__(self):

        with open("data.json") as data_file:
            data = json.load(data_file)
            self.username = data["username"]
            self.restriction_mode = data["restriction_mode"]
            self.screen_share_image_quality = data["screen_share_image_quality"]
            self.screen_share_rate = data["screen_share_rate"]
            self.mouse_send_rate = data["mouse_rate"]

        self.network = user_network.ControllerNetwork(self)
        self.graphics = user_graphics.MasDController(self)

        self.network.setup()

        self.mouse_controller = Controller()

        self.change_gui_data(self.username, self.restriction_mode)

        # Globals
        self.in_remote_desktop_session = False
        self.host_x_size, self.host_y_size = None, None

        Thread(target=self.connect).start()
        self.graphics.run()  # kivy.run() is a thread by itself so no need to make it a separate one

    def local_save_user_data(self):
        with open("data.json", "w") as user_data_file:
            data = {
                "username": self.username,
                "restriction_mode": self.restriction_mode,
                "screen_share_image_quality": self.screen_share_image_quality,
                "screen_share_rate": self.screen_share_rate,
                "mouse_rate": self.mouse_send_rate
            }
            json.dump(data, user_data_file, indent=4)

    def protocol_check(self, protocol):

        if protocol == protocols.DISCONNECT_RESULT:
            self.exit()

        if protocol == protocols.MAKE_USER_REQUEST_RESULT:
            result = self.network.receive()
            if eval(result) == False:
                self.inform("Account creation failed")
            else:
                self.network.logged_in = True
                self.inform("Account creation successful!")

                self.local_save_user_data()
                self.change_gui_data(self.username, self.restriction_mode)

        if protocol == protocols.CHANGE_USERNAME_REQUEST_RESULT:
            result = self.network.receive()
            if not eval(result):
                self.inform("Username change attempt failed")
            else:
                self.network.logged_in = True
                self.inform("Username change attempt successful!")

                self.local_save_user_data()
                self.change_gui_data(self.username, self.restriction_mode)

        if protocol == protocols.MAKE_RESTRICTED_REQUEST_RESULT:
            result = self.network.receive()
            self.restriction_mode = True
            if eval(result) == True:
                self.inform("Restricted mode set to on")
                self.change_gui_data(self.username, self.restriction_mode)
            else:
                self.inform("Could not change the restriction mode")
            self.local_save_user_data()

        if protocol == protocols.MAKE_UNRESTRICTED_REQUEST_RESULT:
            result = self.network.receive()
            self.restriction_mode = False
            if eval(result) == True:
                self.inform("Restricted mode set to off")
                self.change_gui_data(self.username, self.restriction_mode)
            else:
                self.inform("Could not change the restriction mode")
            self.local_save_user_data()

        if protocol == protocols.DECIDE_TUNNEL_CREATION:
            requester_name = self.network.receive()
            self.graphics.notify("Mas D Controller", f"User {requester_name} is trying to connect")
            self.graphics.open_choose_tunnel_dialog(requester_name)

        if protocol == protocols.MAKE_TUNNEL_REQUEST_RESULT:
            result = self.network.receive()
            if result == protocols.USER_DOESNT_EXIST:
                self.inform("User does not exist")
            elif result == protocols.USER_OFFLINE:
                self.inform("User is offline")
            elif result == protocols.USER_DECLINED_TUNNEL_REQEUST:
                self.inform("User declined tunnel request")

            elif result == protocols.USER_ACCEPTED_TUNNEL_REQEUST or result == str(True):  # Tunnel made
                self.C_start_remote_desktop()

        if protocol == protocols.TUNNELED:
            tunneled_protocol = self.network.receive()

            if tunneled_protocol == protocols.START_REMOTE_DESKTOP:
                _ = self.network.receive()
                self.H_start_remote_desktop()
            elif tunneled_protocol == protocols.STOP_REMOTE_DESKTOP:
                _ = self.network.receive()
                self.H_stop_remote_desktop()
            elif tunneled_protocol == protocols.SEND_SCREEN:
                request = self.network.receive()
                if request == "on":
                    self.H_send_screenshot_to_user()

            elif tunneled_protocol == protocols.SCREEN_DATA:  # An image received
                image_bytes = self.network.receive(mode="img")
                self.C_set_image(image_bytes)

            elif tunneled_protocol == protocols.CHANGE_SCREEN_STREAM_QUALITY:
                quality_requested = self.network.receive()
                self.H_set_screen_share_image_quality(quality_requested)

            elif tunneled_protocol == protocols.SCREEN_SIZE:
                self.host_x_size, self.host_y_size = self.network.receive().split(protocols.DATA_SPLITTER)
                Thread(target=self.C_send_mouse_pos).start()

            elif tunneled_protocol == protocols.MOUSE_POS:
                x, y = self.network.receive().split(protocols.DATA_SPLITTER)
                self.H_set_mouse(x, y)

            elif tunneled_protocol == protocols.MOUSE_DOWN:
                button = self.network.receive() 
                self.H_mouse_down(button)

            elif tunneled_protocol == protocols.MOUSE_UP:
                button = self.network.receive()
                self.H_mouse_up(button)

            elif tunneled_protocol == protocols.MOUSE_SCROLL:
                direction = self.network.receive()
                if direction == "up":
                    self.H_scroll_up()
                elif direction == "down":
                    self.H_scroll_down()

    def C_scroll_up(self):
        if self.in_remote_desktop_session:
            self.network.tunnel_to_user(protocols.MOUSE_SCROLL, "up")

    def C_scroll_down(self):
        if self.in_remote_desktop_session:
            self.network.tunnel_to_user(protocols.MOUSE_SCROLL, "down")

    def H_scroll_up(self):
        self.mouse_controller.scroll(0, 1)

    def H_scroll_down(self):
        self.mouse_controller.scroll(0, -1)

    # TODO for now dont need to add modifiers but will have to soon

    def H_mouse_up(self, button):
        click_button = None
        if button == "left":
            click_button = Button.left
        elif button == "right":
            click_button = Button.right
        elif button == "middle":
            click_button = Button.middle
        self.mouse_controller.release(click_button)

    def H_mouse_down(self, button):

        click_button = None
        if button == "left":
            click_button = Button.left
        elif button == "right":
            click_button = Button.right
        elif button == "middle":
            click_button = Button.middle
        self.mouse_controller.press(click_button)

    def H_set_mouse(self, x, y):
        x = int(x)
        y = int(y)
        # self.mouse_controller.position = (x, y) # TODO undo
        print(x,y)

    def C_send_mouse_down(self, button):
        if self.in_remote_desktop_session:
            self.network.tunnel_to_user(protocols.MOUSE_DOWN, button)

    def C_send_mouse_up(self, button):
        if self.in_remote_desktop_session:
            self.network.tunnel_to_user(protocols.MOUSE_UP, button)

    def C_send_mouse_pos(self):
        self.graphics.set_screen("remote_desktop")
        while self.in_remote_desktop_session:
            x, y = Window.mouse_pos
            send_x, send_y = self.convert_screen_to_image_coordinates(x, y)

            self.network.tunnel_to_user(protocols.MOUSE_POS, f"{send_x}{protocols.DATA_SPLITTER}{send_y}")
            # TODO fix bug - server trying to read the protocol as an int (probably buffer overlap or something idk)
            sleep(self.mouse_send_rate)

    def C_start_remote_desktop(self):
        self.in_remote_desktop_session = True
        self.network.tunnel_to_user(protocols.START_REMOTE_DESKTOP, " ")
        self.C_start_screen_share()

        # Thread(target=self.C_send_key).start()
        # TODO start the above (not finished)

    def C_send_key(self):
        if self.in_remote_desktop_session:
            ...

    def C_start_screen_share(self):
        self.graphics.set_screen("remote_desktop")
        self.network.tunnel_to_user(protocols.SEND_SCREEN, "on")

    def H_start_remote_desktop(self):
        x, y = screen_size()
        self.network.tunnel_to_user(protocols.SCREEN_SIZE, f"{x}{protocols.DATA_SPLITTER}{y}")

    def C_stop_remote_desktop(self):
        self.in_remote_desktop_session = False
        self.network.tunnel_to_user(protocols.STOP_REMOTE_DESKTOP, " ")
        self.H_stop_remote_desktop()

    def H_stop_remote_desktop(self):
        self.network.send(protocols.REMOVE_TUNNEL)
        self.network.send(self.username)

    def C_set_image(self, image_bytes):
        self.graphics.set_image(image_bytes)
        if self.in_remote_desktop_session:
            self.network.tunnel_to_user(protocols.SEND_SCREEN, "on")

    def H_send_screenshot_to_user(self):
        screenshot = take_screenshot()
        image_byte_io = BytesIO()
        screenshot.save(image_byte_io, format="jpeg", quality=self.screen_share_image_quality)
        image_in_bytes = image_byte_io.getvalue()

        self.network.tunnel_to_user(protocols.SCREEN_DATA, image_in_bytes, mode="img")
        sleep(self.screen_share_rate)

    def H_set_screen_share_image_quality(self, quality):
        self.screen_share_image_quality = int(quality)

    def H_set_screen_share_rate(self, rate):
        self.screen_share_rate = rate

    def H_set_mouse_pos_send_rate(self, rate):
        self.mouse_send_rate = rate

    def convert_screen_to_image_coordinates(self, x, y):
        window_size = Window.size
        nav_rail_width = ceil(self.graphics.remote_desktop_screen.ids.nav_rail.width)

        x = (x - nav_rail_width)
        y = -1 * (y - window_size[1])  # y
        if x <= 0: x = 0

        ratio_x = int(self.host_x_size) / (window_size[0] - nav_rail_width)
        ratio_y = int(self.host_y_size) / window_size[1]

        converted_x = ceil(x * ratio_x)
        converted_y = ceil(y * ratio_y)
        return converted_x, converted_y

    def connect(self):
        connection_status = {}
        while True:
            result = self.network.connect()

            if result == False:
                connection_status["connected"] = False
                self.change_connection_status_gui(connection_status)
                continue
            else:
                connection_status["connected"] = True
                connection_status["ip"] = self.network.SERVER_IP
                connection_status["port"] = self.network.SERVER_PORT

                Thread(target=self.network.receive_continuous).start()

                if self.username is not None:
                    self.network.request_login(self.username)
                break

        self.set_switch_mode()
        self.change_connection_status_gui(connection_status)

    def change_connection_status_gui(self, connection_status: dict):
        if connection_status["connected"]:
            self.graphics.main_screen.ids.connection_status_label.text = f"Connected to [b]{connection_status['ip']}[/b] on port [b]{connection_status['port']}[/b]"
        else:
            self.graphics.main_screen.ids.connection_status_label.text = "Not Connected!"

    def inform(self, msg):
        self.graphics.open_information_dialog(msg)

    def accept_tunnel_creation(self, requester_name):
        self.network.send(protocols.DECIDE_TUNNEL_CREATION_RETURN)
        self.network.send(str(True))
        self.network.send(requester_name)
        self.network.send(self.username)

    def decline_tunnel_creation(self, requester_name):
        self.network.send(protocols.DECIDE_TUNNEL_CREATION_RETURN)
        self.network.send(str(False))
        self.network.send(requester_name)

    def dev(self):
        self.graphics.screen_manager.current = "remote_desktop"

    def save_username_setting(self):
        inputs = [self.graphics.settings_screen.ids.company_name_text_input.text,
                  self.graphics.settings_screen.ids.location_text_input.text,
                  self.graphics.settings_screen.ids.type_text_input.text,
                  self.graphics.settings_screen.ids.number_text_input.text]

        username = ""
        for input in inputs:
            if input == "":
                self.inform("Please fill all the inputs")
                return
            elif " " in input:
                self.inform("No spaces allowed")
                return
            elif "\t" in input:
                self.inform("No tabs allowed")
                return
            else:
                username += input

        username = username.upper()

        if self.username is None or self.username == "":
            self.network.request_make_new_user(username)
        else:
            self.network.request_change_username(self.username, username)

        if self.network.connected_to_server:
            self.username = username
        else:
            self.username = self.username

    def save_restriction_mode_setting(self):
        restricted_mode: bool = self.graphics.settings_screen.ids.restriction_mode_switch.active
        self.restriction_mode = restricted_mode

        if restricted_mode:
            self.network.request_make_restricted(self.username)
        elif not restricted_mode:
            self.network.request_make_unrestricted(self.username)

    def change_gui_data(self, username: str, restricted_mode):
        mode = "None"
        if restricted_mode:
            mode = "restricted"
        elif not restricted_mode:
            mode = "unrestricted"

        self.graphics.main_screen.ids.username_label.text = f"You name [b]{str(username)}[/b] - Mode [b]{mode}[/b]"

    def set_switch_mode(self):
        self.graphics.settings_screen.ids.restriction_mode_switch.active = self.restriction_mode

    def make_tunnel_request(self, requestee_name):
        if requestee_name != "":
            if " " not in requestee_name:
                if "\t" not in requestee_name:
                    if requestee_name != self.username:
                        self.network.make_tunnel(self.username, requestee_name)
                    else:
                        self.inform("Cannot enter your own username")
                else:
                    self.inform("No tabs allowed")
            else:
                self.inform("No spaces allowed")
        else:
            self.inform("Enter a username")

    def stop(self):
        if self.network.connected_to_server:
            self.network.request_logout(self.username)
            self.network.disconnect()
        else:
            self.exit()

    def exit(self):
        from os import _exit
        _exit(0)


if __name__ == "__main__":
    Main()
