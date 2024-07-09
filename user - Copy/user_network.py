import socket
import json

from threading import Thread


class ControllerNetwork:
    def __init__(self, main):
        self.main = main

        self.logged_in = False
        self.connected = False

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

            self.connected = True
            # self.test_code()
        except ConnectionRefusedError:
            return False

    def receive_data(self):
        while self.connected:
            try:
                msg_length = self.client.recv(self.HEADER).decode(self.FORMAT)
                if msg_length:
                    msg_length = int(msg_length)
                    msg = self.client.recv(msg_length).decode(self.FORMAT)

                    protocol, data = msg.split(self.protocols["PROTOCOL_MESSAGE_SPLITTER"])
                    self.main.protocol_check(protocol, data)
            except ConnectionResetError:
                self.main.connect()
                exit()

    def send(self, protocol, data):
        try:
            # TODO for debug purposes data is type casted into a string
            msg = protocol + self.protocols["PROTOCOL_MESSAGE_SPLITTER"] + data
            message = msg.encode(self.FORMAT)
            msg_length = len(msg)
            send_length = str(msg_length).encode(self.FORMAT)
            send_length += b" " * (self.HEADER - len(send_length))
            self.client.send(send_length)
            self.client.send(message)
        except Exception as e:
            self.main.inform("Cannot send messages, not connected to a server!")

    def make_user(self, username):
        self.send(self.protocols["ADD_USER"], username)

    def change_username(self, current_username, new_username):
        self.send(self.protocols["CHANGE_USERNAME"], f"{current_username}{self.protocols['CHANGE_USERNAME_SEPARATOR']}{new_username}")
    def delete_user(self, username):
        self.send(self.protocols["DELETE_USER"], username)

    def login(self, username):
        self.send(self.protocols["LOG_IN"], username)
        self.logged_in = True

    def logout(self, username):
        if self.logged_in:
            self.send(self.protocols["LOG_OUT"], username)

    # the 'connector' is the person whom 'username' connects to (aka requestee in the server code)
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
        self.connected = False
        # revision needed
        self.send(self.protocols["DISCONNECT"], " ")
