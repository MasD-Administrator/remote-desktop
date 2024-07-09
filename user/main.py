import json
from threading import Thread

import user_graphics
import user_network


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

    def protocol_check(self, protocol, data):
        if protocol == self.network.protocols["ADD_USER"]:
            if eval(data) == False:
                self.inform("Account creation failed")
            else:
                self.network.logged_in = True
                self.inform("Account creation successful!")

                self.local_save_user_data()
                self.change_gui_data(self.username, self.restriction_mode)

        if protocol == self.network.protocols["MAKE_RESTRICTED"]:
            self.restriction_mode = True
            if eval(data) == True:
                self.inform("Restricted mode set to on")
                self.change_gui_data(self.username, self.restriction_mode)
            else:
                self.inform("Could not change the restriction mode")

            self.local_save_user_data()

        if protocol == self.network.protocols["MAKE_UNRESTRICTED"]:
            self.restriction_mode = False
            if eval(data) == True:
                self.inform("Restricted mode set to off")
                self.change_gui_data(self.username, self.restriction_mode)
            else:
                self.inform("Could not change the restriction mode")

            self.local_save_user_data()

        if protocol == self.network.protocols["CHANGE_USERNAME"]:
            if eval(data) == False:
                self.inform("Username change attempt failed")
            else:
                self.network.logged_in = True
                self.inform("Username change attempt successful!")

                self.local_save_user_data()
                self.change_gui_data(self.username, self.restriction_mode)

        if protocol == self.network.protocols["MAKE_TUNNEL"]:
            if data == "True":
                print("tunnel made")
            else:
                self.inform(data)


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

                Thread(target=self.network.receive_data).start()

                if self.username is not None:
                    self.network.login(self.username)
                break

        self.set_switch_mode()
        self.change_connection_status_gui(connection_status)

    def change_connection_status_gui(self, connection_status: dict):
        if connection_status["connected"]:
            self.graphics.main_screen.ids.connection_status_label.text = f"Connected to [b]{connection_status['ip']}[/b] on port [b]{connection_status['port']}[/b]"
        else:
            self.graphics.main_screen.ids.connection_status_label.text = "Not Connected!"

    def inform(self, msg):
        self.graphics.open_dialog(msg)

    def save_all_settings(self):
        self.save_username_setting()
        self.save_restriction_mode_setting()

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
            self.network.make_user(username)
        else:
            self.network.change_username(self.username, username)
        self.username = username

    def save_restriction_mode_setting(self):
        restricted_mode: bool = self.graphics.settings_screen.ids.restriction_mode_switch.active
        self.restriction_mode = restricted_mode

        if restricted_mode:
            self.network.make_restricted(self.username)
        elif not restricted_mode:
            self.network.make_unrestricted(self.username)

    def change_gui_data(self, username: str, restricted_mode):
        mode = "None"
        if restricted_mode:
            mode = "restricted"
        elif not restricted_mode:
            mode = "unrestricted"

        self.graphics.main_screen.ids.username_label.text = f"You name [b]{str(username)}[/b] - Mode [b]{mode}[/b]"

    def set_switch_mode(self):
        self.graphics.settings_screen.ids.restriction_mode_switch.active = self.restriction_mode

    def make_tunnel(self, connector_username_text):
        if connector_username_text != "":
            if " " not in connector_username_text:
                if "\t" not in connector_username_text:
                    if connector_username_text != self.username:
                        self.network.make_tunnel(self.username, connector_username_text)
                    else:
                        self.inform("Cannot enter your own username")
                else:
                    self.inform("No tabs allowed")
            else:
                self.inform("No spaces allowed")
        else:
            self.inform("Enter a username")

    def stop(self):
        self.network.logout(self.username)
        self.network.disconnect()
        from os import _exit
        _exit(0)

    def restart(self):
        pass


if __name__ == "__main__":
    Main()
