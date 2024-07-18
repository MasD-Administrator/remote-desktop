import json
import time
from threading import Thread
from io import BytesIO
from PIL.ImageGrab import grab as take_screenshot


import user_graphics
import user_network
import protocols


class Main:
    def __init__(self):

        with open("data.json") as data_file:
            data = json.load(data_file)
            self.username = data["username"]
            self.restriction_mode = data["restriction_mode"]

        self.network = user_network.ControllerNetwork(self)
        self.graphics = user_graphics.MasDController(self)

        self.network.setup()

        self.change_gui_data(self.username, self.restriction_mode)

        Thread(target=self.connect).start()
        # kivy.run() is a thread by itself so no need to make it a separate one
        self.graphics.run()

    def local_save_user_data(self):
        with open("data.json", "w") as user_data_file:
            data = {
                "username": self.username,
                "restriction_mode": self.restriction_mode
            }
            json.dump(data, user_data_file, indent=4)

    def protocol_check(self, protocol):

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

            elif result == protocols.USER_ACCEPTED_TUNNEL_REQEUST:
                self.start_remote_desktop()
            elif result == str(True):  # no barriers to enter
                self.start_remote_desktop()

        if protocol == protocols.TUNNELED:
            tunneled_protocol = self.network.receive()

            if tunneled_protocol == protocols.SCREEN_STREAM:
                request = self.network.receive()
                if request == "on":
                    self.start_screen_stream()
                elif request == "off":
                    self.stop_screen_stream()

            elif tunneled_protocol == protocols.SCREEN_DATA:  # An image received
                image_bytes = self.network.receive(mode="raw")
                print(f"screen data recv: {len(image_bytes)}")
                self.set_image(image_bytes)

    def set_image(self, image_bytes):
        self.graphics.set_screen("remote_desktop")
        self.graphics.set_image(image_bytes)

    def start_screen_stream(self):
        self.can_tunnel_screenshot = True
        Thread(target=self.tunnel_screenshot).start()

    def stop_screen_stream(self):
        self.can_tunnel_screenshot = False

    def tunnel_screenshot(self):
        while self.can_tunnel_screenshot:
            screenshot = take_screenshot()
            image_byte_io = BytesIO()
            screenshot.save(image_byte_io, format="jpeg", quality=8)
            image_in_bytes = image_byte_io.getvalue()

            self.network.tunnel_to_user(protocols.SCREEN_DATA, image_in_bytes, mode="raw")
            print(f"len of the sent image: {len(image_byte_io.getvalue())}")
            self.can_tunnel_screenshot = False

    def start_remote_desktop(self):
        self.network.tunnel_to_user(protocols.SCREEN_STREAM, "on")
        # self.network.tunnel_to_user(protocols.SCREEN_STREAM_STATUS, "off")


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

    ######## GUI #########

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
        self.network.request_logout(self.username)
        self.network.disconnect()
        from os import _exit
        _exit(0)



if __name__ == "__main__":
    Main()
