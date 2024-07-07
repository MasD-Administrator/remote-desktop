import socket
import json

from threading import Thread


class ControllerNetwork:
    def __init__(self, main):
        self.main = main

    def setup(self):
        with open("../protocols.json") as file:
            self.protocols = json.load(file)

        with open("user_network_data.json") as controller_data_file:
            controller_data = json.load(controller_data_file)

            self.SERVER_PORT = controller_data["server_port"]
            self.HEADER = controller_data["header"]
            self.FORMAT = controller_data["format"]

            if controller_data["server_ip"]:
                self.SERVER_IP = socket.gethostbyname(socket.gethostname())
            elif type(controller_data["server_ip"]) is str:
                self.SERVER_IP = controller_data["server_ip"]
            elif type(controller_data["server_ip"]) is not str:
                self.SERVER_IP = None



    def connect(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.SERVER_IP, self.SERVER_PORT))

            # self.test_code()
        except ConnectionRefusedError:
            return False

    def receive_data(self):
        msg_length = self.client.recv(self.HEADER).decode(self.FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = self.client.recv(msg_length).decode(self.FORMAT)

            print(msg)
            # TODO this is where protocol check should be

    def send(self, protocol, data):
        try:
            # TODO for debug purposes data is type casted into a string
            msg = protocol + self.protocols["PROTOCOL_MESSAGE_SPLITTER"] + str(data)
            message = msg.encode(self.FORMAT)
            msg_length = len(msg)
            send_length = str(msg_length).encode(self.FORMAT)
            send_length += b" " * (self.HEADER - len(send_length))
            self.client.send(send_length)
            self.client.send(message)
        except OSError:
            print("os error")
            self.main.inform("Cannot send messages whilst not connected!")

    def make_user(self, username):
        self.send(self.protocols["ADD_USER"], username)

    def delete_user(self, username):
        self.send(self.protocols["DELETE_USER"], username)

    def login(self, username):
        self.send(self.protocols["LOG_IN"], username)

    def logout(self, username):
        self.send(self.protocols["LOG_OUT"], username)

    # the 'connector' is the person whom 'username' connects to
    def make_tunnel(self, username, connector_name):
        self.send(self.protocols["MAKE_TUNNEL"], f"{username}{self.protocols['MAKE_TUNNEL_INPUT_SEPARATOR']}{connector_name}")

    def remove_tunnel(self, username, connector_name):
        self.send(self.protocols["REMOVE_TUNNEL"], f"{username}{self.protocols['REMOVE_TUNNEL_INPUT_SEPARATOR']}{connector_name}")

    def tunnel_stream(self, name, data):
        self.send(self.protocols['TUNNEL_STREAM'], f"{name}{self.protocols['TUNNEL_STREAM_NAME_DATA_SEPARATOR']}{data}")

    def make_restricted(self, username):
        self.send(self.protocols["MAKE_RESTRICTED"], username)

    def make_unrestricted(self, username):
        self.send(self.protocols["MAKE_UNRESTRICTED"], username)

    def disconnect(self):
        # revision needed
        if self.main.username != None or self.main.username != "None":
            self.send(self.protocols["DISCONNECT"], " ")
        else:
            return False

    def shutdown(self):
        from os import _exit
        _exit(0)

    def input_check(self):
        debug = True
        while debug == True:
            inpt = input(":> ")
            if inpt == "exit":
                self.shutdown()


if __name__ == "__main__":
    ControllerNetwork().connect()