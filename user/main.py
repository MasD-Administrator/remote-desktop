import json
from threading import Thread

import user_graphics
import user_network


class Main:
    def __init__(self):

        with open("data.json") as data_file:
            data = json.load(data_file)
            self.username = data["username"]
            self.restricted_mode = data["restricted_mode"]

        self.network = user_network.ControllerNetwork(self)
        self.graphics = user_graphics.MasDController(self)

        self.network.setup()

        self.main()

    def inform(self, msg):
        self.graphics.open_dialog(msg)

    def save_restriction_mode(self):
        restricted: bool = self.graphics.settings_screen.ids.restriction_mode_switch.active
        self.network.restricted_mode = restricted
        if restricted:
            self.network.make_restricted(self.username)
        elif not restricted:
            self.network.make_unrestricted(self.username)

    def stop(self):
        from os import _exit
        self.network.disconnect()
        _exit(0)

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
                break

        # TODO change labels to fit information

        self.change_connection_status_gui(connection_status)

    def change_connection_status_gui(self, connection_status: dict):
        if connection_status["connected"]:
            self.graphics.main_screen.ids.connection_status_label.text = f"Connected to [b]{connection_status['ip']}[/b] on port [b]{connection_status['port']}[/b]"
        else:
            self.graphics.main_screen.ids.connection_status_label.text = "Not Connected!"

    def change_username_gui(self, username: str, restricted_mode):
        mode = None
        if restricted_mode == True:
            mode = "restricted"
        elif restricted_mode == False:
            mode = "unrestricted"

        self.graphics.main_screen.ids.username_label.text = f"You name [b]{str(username)}[/b] - Mode [b]{mode}[/b]"
        pass

    def main(self):
        self.change_username_gui(self.username, self.restricted_mode)

        Thread(target=self.connect).start()
        # kivy.run() is a thread by itself so no need to make it a separate one
        self.graphics.run()


if __name__ == "__main__":
    Main()
