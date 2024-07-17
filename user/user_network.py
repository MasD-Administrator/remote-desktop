import socket
import json

from threading import Thread

import protocols

class ControllerNetwork:
    def __init__(self, main):
        self.main = main

        self.logged_in = False
        self.connected_to_server = False

    def setup(self):
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

    def receive_continuous(self):
        try:
            while self.connected_to_server:
                msg_length = int(self.client.recv(self.HEADER).decode(self.FORMAT))
                protocol = self.client.recv(msg_length).decode(self.FORMAT)

                self.main.protocol_check(protocol)
        except ConnectionResetError:
            self.main.connect()

    def receive(self):
        if self.connected_to_server:
            msg_length = int(self.client.recv(self.HEADER).decode(self.FORMAT))
            message = self.client.recv(msg_length).decode(self.FORMAT)

            return message

    def connect(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.SERVER_IP, self.SERVER_PORT))

            self.connected_to_server = True
        except ConnectionRefusedError:
            return False

    def send(self, data):
        try:
            message = data.encode(self.FORMAT)
            msg_length = len(data)
            send_length = str(msg_length).encode(self.FORMAT)
            send_length += b" " * (self.HEADER - len(send_length))
            self.client.send(send_length)
            self.client.send(message)
        except WindowsError:
            self.main.inform("Not connected to a server")

    def disconnect(self):
        self.send(protocols.DISCONNECT)

    def request_login(self, username):
        self.send(protocols.LOG_IN_REQUEST)
        self.send(username)

    def request_logout(self, username):
        self.send(protocols.LOG_OUT_REQUEST)
        self.send(username)

    def request_make_new_user(self, username):
        self.send(protocols.MAKE_USER_REQUEST)
        self.send(username)

    def request_change_username(self, current_username, new_username):
        self.send(protocols.CHANGE_USERNAME_REQUEST)
        self.send(current_username)
        self.send(new_username)

    def request_make_restricted(self, username):
        self.send(protocols.MAKE_RESTRICTED_REQUEST)
        self.send(username)

    def request_make_unrestricted(self, username):
        self.send(protocols.MAKE_UNRESTRICTED_REQUEST)
        self.send(username)

    def make_tunnel(self, requester_name, requestee_name):
        self.send(protocols.MAKE_TUNNEL_REQUEST)
        self.send(requester_name)
        self.send(requestee_name)
