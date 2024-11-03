import json
from time import sleep
from math import ceil
from threading import Thread
from io import BytesIO
from pickle import dumps, loads
from tkinter import filedialog
import os

from pynput import keyboard
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController
from pynput.mouse import Button
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

        self.mouse_controller = MouseController()

        self.change_gui_data(self.username, self.restriction_mode)

        # Globals
        self.in_remote_desktop_session = False
        self.host_x_size, self.host_y_size = None, None
        self.mouse_lock = False
        self.new_image_received = False
        self.file_share_type = None  # file or folder

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

        elif protocol == protocols.MAKE_USER_REQUEST_RESULT:
            result = self.network.receive()
            if eval(result) == False:
                self.inform("Account creation failed")
                self.username = None
            else:
                username = self.network.receive()
                self.username = username
                self.network.logged_in = True
                self.inform("Account creation successful!")

                self.local_save_user_data()
                self.change_gui_data(self.username, self.restriction_mode)

        elif protocol == protocols.CHANGE_USERNAME_REQUEST_RESULT:
            result = self.network.receive()

            if not eval(result):
                self.inform("Username change attempt failed")
            else:
                new_username = self.network.receive()
                self.username = new_username
                self.network.logged_in = True
                self.inform("Username change attempt successful!")

                self.local_save_user_data()
                self.change_gui_data(self.username, self.restriction_mode)

        elif protocol == protocols.MAKE_RESTRICTED_REQUEST_RESULT:
            result = self.network.receive()
            self.restriction_mode = True
            if eval(result) == True:
                self.inform("Restricted mode set to on")
                self.change_gui_data(self.username, self.restriction_mode)
            else:
                self.inform("Could not change the restriction mode")
            self.local_save_user_data()

        elif protocol == protocols.MAKE_UNRESTRICTED_REQUEST_RESULT:
            result = self.network.receive()
            self.restriction_mode = False
            if eval(result) == True:
                self.inform("Restricted mode set to off")
                self.change_gui_data(self.username, self.restriction_mode)
            else:
                self.inform("Could not change the restriction mode")
            self.local_save_user_data()

        elif protocol == protocols.DECIDE_TUNNEL_CREATION:
            requester_name = self.network.receive()
            self.graphics.notify("Mas D Controller", f"User {requester_name} is trying to connect", 2)
            self.graphics.open_choose_tunnel_dialog(requester_name)

        elif protocol == protocols.MAKE_TUNNEL_REQUEST_RESULT:
            result = self.network.receive()
            if result == protocols.USER_DOESNT_EXIST:
                self.inform("User does not exist")
            elif result == protocols.USER_OFFLINE:
                self.inform("User is offline")
            elif result == protocols.USER_DECLINED_TUNNEL_REQEUST:
                self.inform("User declined tunnel request")
            elif result == protocols.USER_IN_REMOTE_DESKTOP_SESSION:
                self.inform("User is currently in a remote desktop session")
            elif result == str(True) or protocols.USER_ACCEPTED_TUNNEL_REQEUST:  # Tunnel made
                self.C_start_remote_desktop()

        elif protocol == protocols.TUNNELED:
            tunneled_protocol = self.network.receive()
            if tunneled_protocol == protocols.START_REMOTE_DESKTOP:
                _ = self.network.receive()
                self.H_start_remote_desktop()
            elif tunneled_protocol == protocols.STOP_REMOTE_DESKTOP:
                _ = self.network.receive()
                self.stop_remote_desktop()
            elif tunneled_protocol == protocols.SEND_SCREEN:
                request = self.network.receive()
                if request == "on":
                    self.H_send_screenshot_to_user()

            elif tunneled_protocol == protocols.SCREEN_DATA:  # An image received
                image_bytes = self.network.receive(mode="big")
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

            elif tunneled_protocol == protocols.MOUSE_UP:
                button = self.network.receive()
                self.H_mouse_up(button)

            elif tunneled_protocol == protocols.MOUSE_DOWN:
                button = self.network.receive()
                self.H_mouse_down(button)

            elif tunneled_protocol == protocols.MOUSE_SCROLL:
                axis = self.network.receive()
                self.H_scroll(axis)

            elif tunneled_protocol == protocols.KEY_DOWN:
                key = self.network.receive(mode="bytes")
                self.H_key_down(key)

            elif tunneled_protocol == protocols.KEY_UP:
                key = self.network.receive(mode="bytes")
                self.H_key_up(key)

            elif tunneled_protocol == protocols.START_FILE_SHARE:  # a command from the controller
                _ = self.network.receive()
                Thread(target=self.H_open_folder_select_destination).start()

            elif tunneled_protocol == protocols.FILE_SHARE_INITIALIZED:
                _ = self.network.receive()
                Thread(target=self.C_setup_fileshare).start()

            elif tunneled_protocol == protocols.DIRECTORY_STRUCTURE:
                directory_structure = self.network.receive(mode="bytes")
                directory_structure = loads(directory_structure)
                Thread(target=self.H_setup_directory_structure, args=(directory_structure,)).start()

            elif tunneled_protocol == protocols.DIRECTORY_STRUCTURE_SETUP_FINISHED:
                _ = self.network.receive()
                Thread(target=self.C_send_file_data).start()

            elif tunneled_protocol == protocols.FILE_DATA:
                file_data_pair = loads(self.network.receive(mode="big"))
                file_meta_data, file_byte_data = file_data_pair[0], file_data_pair[1]

                Thread(target=self.H_create_file, args=(file_meta_data, file_byte_data)).start()

            elif tunneled_protocol == protocols.SEND_CURRENT_SETTINGS:
                self.network.tunnel_to_user(protocols.CURRENT_SETTINGS, dumps(self.current_settings()), mode="bytes")

            elif tunneled_protocol == protocols.CURRENT_SETTINGS:
                self.settings = self.network.receive(mode="bytes")
                self.graphics.open_host_settings(loads(self.settings))

            elif tunneled_protocol == protocols.SET_SETTINGS:
                settings = self.network.receive(mode="bytes")
                settings = loads(settings)

                image_quality = int(settings[0])
                image_rate = float(settings[1])
                mouse_rate = float(settings[2])
                if image_quality > 100:
                    image_quality = 100
                if image_quality < 0:
                    image_quality = 0

                self.screen_share_image_quality = image_quality
                self.screen_share_rate = image_rate
                self.mouse_send_rate = mouse_rate

                Thread(target=self.local_save_user_data).start()

    def send_host_settings(self, settings):
        self.network.tunnel_to_user(protocols.SET_SETTINGS, dumps(settings), mode="bytes")

    def current_settings(self):
        return [self.screen_share_image_quality, self.screen_share_rate, self.mouse_send_rate]

    def C_host_settings(self):
        self.network.tunnel_to_user(protocols.SEND_CURRENT_SETTINGS, " ")

    def H_open_folder_select_destination(self):
        path = filedialog.askdirectory(title="Select a folder as destination")
        self.H_selected_file_share_destination(path)

    def H_create_file(self, file_meta_data, file_byte_data):
        with open(self.H_file_share_directory_path + "/" + file_meta_data, "wb") as file:
            file.write(file_byte_data)
            self.graphics.notify("File sharing", f"Finished writing {file_meta_data} to disk", 1)

    def C_send_file_data(self):
        # in file pair index 0 is local 1 is to be sent
        for file_pair in self.file_structure:
            file = file_pair[0]
            with open(file, "rb") as opened_file:
                file_byte_data = opened_file.read()
                file_metadata = file_pair[1]
                self.network.tunnel_to_user(protocols.FILE_DATA, dumps([file_metadata, file_byte_data]), mode="bytes")
                

    def H_selected_file_share_destination(self, path):
        if path != "":
            self.H_file_share_directory_path = str(path)
            self.network.tunnel_to_user(protocols.FILE_SHARE_INITIALIZED, " ")
        else:
            self.H_file_share_directory_path = None

    def H_setup_directory_structure(self, directory_structure):
        try:
            for directory_path in directory_structure:
                os.mkdir(self.H_file_share_directory_path + "/" + directory_path)
            self.network.tunnel_to_user(protocols.DIRECTORY_STRUCTURE_SETUP_FINISHED, " ")
        except FileExistsError:
            self.graphics.notify("MasDController", "Folder already exists", 2)

    def C_share_file(self, path):
        if path != "":
            self.file_share_type = "file"
            self.C_path = path
            self.network.tunnel_to_user(protocols.START_FILE_SHARE, " ")

    def C_share_folder(self, path):
        if path != "":
            self.file_share_type = "folder"
            self.C_path = path
            self.network.tunnel_to_user(protocols.START_FILE_SHARE, " ")

    def C_setup_fileshare(self):
        if self.file_share_type == "folder":
            folder_name = self.C_path.split('/')[-1]
            if self.C_path:
                self.directory_structure = []
                self.file_structure = []

                self.directory_structure.append(folder_name)

                a = os.walk(self.C_path)
                os.chdir(self.C_path)
                os.chdir("..")
                cwd = os.getcwd()
                root_root_len = len(cwd)

                for root, dirs, files in a:
                    new_root = root[root_root_len:]

                    if files:
                        for file in files:
                            self.file_structure.append([os.path.join(root, file), os.path.join(new_root, file)])

                    for directory in dirs:
                        relative_dir = os.path.join(new_root, directory)

                        self.directory_structure.append(relative_dir)

                if self.network.connected_to_server and self.in_remote_desktop_session:
                    self.network.tunnel_to_user(protocols.DIRECTORY_STRUCTURE, dumps(self.directory_structure),
                                                mode="bytes")
        elif self.file_share_type == "file":
            if type(self.C_path) is str:
                self.send_file(self.C_path)
            elif type(self.C_path) is tuple:
                for file_path in self.C_path:
                    self.send_file(file_path)


    def send_file(self, path):
        file_meta_data = path.split("/")[-1]
        with open(path, "rb") as file:
            file_byte_data = file.read()
        self.network.tunnel_to_user(protocols.FILE_DATA, dumps([file_meta_data, file_byte_data]), mode="bytes")

    def H_scroll(self, axis):
        if axis == "scrollup":
            self.mouse_controller.scroll(0, -1)
        elif axis == "scrolldown":
            self.mouse_controller.scroll(0, 1)


    # TODO add modifiers to mouse - no

    def H_mouse_up(self, button):
        if button == "scrollup" or button == "scrolldown":
            self.H_scroll(button)
        else:
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
        self.mouse_controller.position = (x, y)

    def C_send_mouse_down(self, button):  # mouse pressed
        if button == "scrollup" or button == "scrolldown":
            return
        if self.in_remote_desktop_session:
            self.network.tunnel_to_user(protocols.MOUSE_DOWN, button)

    def C_send_mouse_up(self, button):  # mouse released
        if self.in_remote_desktop_session:
            self.network.tunnel_to_user(protocols.MOUSE_UP, button)

    def C_send_mouse_pos(self):
        self.graphics.set_screen("remote_desktop")
        while self.in_remote_desktop_session:
            if not self.mouse_lock:
                x, y = Window.mouse_pos
                send_x, send_y = self.convert_screen_to_image_coordinates(x, y)

                self.network.tunnel_to_user(protocols.MOUSE_POS, f"{send_x}{protocols.DATA_SPLITTER}{send_y}")
            sleep(self.mouse_send_rate)

    def C_start_remote_desktop(self):
        self.in_remote_desktop_session = True
        self.network.tunnel_to_user(protocols.START_REMOTE_DESKTOP, " ")

        self.C_start_screen_share()
        Thread(target=self.C_start_key).start()

    def C_start_key(self):
        with keyboard.Listener(on_press=self.C_on_key_down, on_release=self.C_on_key_up) as self.listener:
            self.listener.join()

    def C_on_key_down(self, key):
        if self.in_remote_desktop_session and Window.focus:
            self.network.tunnel_to_user(protocols.KEY_DOWN, dumps(key), mode="bytes")

    def C_on_key_up(self, key):
        if self.in_remote_desktop_session and Window.focus:
            self.network.tunnel_to_user(protocols.KEY_UP, dumps(key), mode="bytes")

    def H_key_down(self, key):
        key = loads(key)
        try:
            self.keyboard.press(key.char)
        except AttributeError:
            self.keyboard.press(key)

    def H_key_up(self, key):
        key = loads(key)
        try:
            self.keyboard.release(key.char)
        except AttributeError:
            self.keyboard.release(key)

    def C_start_screen_share(self):
        self.graphics.set_screen("remote_desktop")
        self.network.tunnel_to_user(protocols.SEND_SCREEN, "on")

    def H_start_remote_desktop(self):
        self.in_remote_desktop_session = True
        self.keyboard = KeyboardController()
        x, y = screen_size()
        self.network.tunnel_to_user(protocols.SCREEN_SIZE, f"{x}{protocols.DATA_SPLITTER}{y}")

    def C_stop_remote_desktop(self):
        self.network.tunnel_to_user(protocols.STOP_REMOTE_DESKTOP, " ")
        self.listener.stop()
        self.stop_remote_desktop()  # both parties need to remove tunnel

    def stop_remote_desktop(self):
        self.in_remote_desktop_session = False
        self.network.send(protocols.REMOVE_TUNNEL)
        self.network.send(self.username)

    def C_set_image(self, image_bytes):
        self.graphics.set_image(image_bytes)
        self.new_image_received = True
        if self.in_remote_desktop_session:
            self.network.tunnel_to_user(protocols.SEND_SCREEN, "on")

    def H_send_screenshot_to_user(self):
        screenshot = take_screenshot()
        image_byte_io = BytesIO()
        screenshot.save(image_byte_io, format="jpeg", quality=self.screen_share_image_quality)
        image_in_bytes = image_byte_io.getvalue()
        if self.in_remote_desktop_session:
            self.network.tunnel_to_user(protocols.SCREEN_DATA, image_in_bytes, mode="bytes")
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

                if self.username != None:
                    self.network.request_login(self.username)
                Thread(target=self.network.receive_continuous).start()

                break

        self.set_switch_mode()
        self.change_connection_status_gui(connection_status)

    def change_connection_status_gui(self, connection_status: dict):
        if connection_status["connected"]:
            self.graphics.main_screen.ids.connection_status_label.text = f"Connected to [b]{connection_status['ip']}[/b] on port [b]{connection_status['port']}[/b]"
        else:
            self.graphics.main_screen.ids.connection_status_label.text = "Not Connected!"
    
    def open_file_share_dialog(self):
        self.graphics.open_file_share_dialog()

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

        if not self.username == username:
            if self.username is None:
                self.network.request_make_new_user(username)
            elif self.username != None:
                self.network.request_change_username(self.username, username)
        else:
            self.inform("Entered your own username!")
            
    def save_restriction_mode_setting(self):
        restricted_mode: bool = self.graphics.settings_screen.ids.restriction_mode_switch.active
        self.restriction_mode = restricted_mode
        if self.username != None:
            if restricted_mode:
                self.network.request_make_restricted(self.username)
            elif not restricted_mode:
                self.network.request_make_unrestricted(self.username)
        else:
            self.inform("Make an account first")

    def change_gui_data(self, username: str, restricted_mode):
        mode = "None"
        if restricted_mode:
            mode = "restricted"
        elif not restricted_mode:
            mode = "unrestricted"

        self.graphics.main_screen.ids.username_label.text = f"Your name [b]{str(username)}[/b] - Mode [b]{mode}[/b]"

    def set_switch_mode(self):
        self.graphics.settings_screen.ids.restriction_mode_switch.active = self.restriction_mode

    def make_tunnel_request(self, requestee_name):
        if self.username != None:
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
        else:
            self.inform("Make an account first")

    def mouse_lock_toggle(self):
        if not self.mouse_lock:
            self.graphics.remote_desktop_screen.ids.mouse_lock.icon = "mouse"
        else:
            self.graphics.remote_desktop_screen.ids.mouse_lock.icon = "mouse-off"
                   
        self.mouse_lock = not self.mouse_lock
        
    def stop(self):
        if self.network.connected_to_server:
            if self.username != None:
                self.network.disconnect(self.username)
            else:
                self.network.disconnect_for_non_user()
        elif not self.network.connected_to_server:
            self.exit()

    def exit(self):  # this is used so that all the threads get stopped
        from os import _exit
        _exit(0)


if __name__ == "__main__":
    Main()
