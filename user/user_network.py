import socket
import json

import protocols
from buffer import Buffer

class ControllerNetwork:
    def __init__(self, main):
        self.main = main

        self.logged_in = False
        self.connected_to_server = False
        self.is_sending = False

    def setup(self):
        with open("user_network_data.json") as controller_data_file:
            controller_data = json.load(controller_data_file)

            self.SERVER_PORT = controller_data["server_port"]
            self.HEADER = controller_data["header"]
            self.FORMAT = controller_data["format"]

            self.tick = controller_data["tick"]

            ip = controller_data["server_ip"]
            if ip == "localhost":
                self.SERVER_IP = socket.gethostbyname(socket.gethostname())
            else:
                self.SERVER_IP = ip

    def receive_continuous(self):
        try:
            while self.connected_to_server:
                msg_length = int(self.client.recv(self.HEADER).decode(self.FORMAT))
                protocol = self.client.recv(msg_length).decode(self.FORMAT)

                self.main.protocol_check(protocol)
        except ConnectionResetError:
            self.connected_to_server = False
            self.main.connect()

    def receive(self, mode="coded"):
        if self.connected_to_server:
            msg_length = int(self.client.recv(self.HEADER).decode(self.FORMAT))
            if mode == "bytes":
                message = self.client.recv(msg_length)
                message = message
                return message
            elif mode == "coded":
                message = self.client.recv(msg_length)
                message = message.decode(self.FORMAT)
                return message

            elif mode == "img":
                image_data = b""
                while len(image_data) < msg_length:
                    packet = self.client.recv(msg_length - len(image_data))
                    if not packet:
                        break
                    image_data += packet
                return image_data

    def connect(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.SERVER_IP, self.SERVER_PORT))

            self.connected_to_server = True
            self.buffer = Buffer(self)
            return True

        except (TimeoutError, ConnectionRefusedError):
            self.connected_to_server = False
            return False

    def send(self, data, mode="coded"):
        if self.connected_to_server:
            self.buffer.add(data, mode)
        else:
            self.main.inform("Not connected to a server")

    # this is the actual function for sending the data
    def network_send(self, data, mode):
        self.is_sending = True
        if mode == "coded":
            data = data.encode(self.FORMAT)
            msg_length = len(data)
            send_length = str(msg_length).encode(self.FORMAT)
            send_length += b" " * (self.HEADER - len(send_length))

            self.client.send(send_length)
            self.client.send(data)

        elif mode == "bytes":
            data = data
            msg_length = len(data)
            send_length = str(msg_length).encode(self.FORMAT)
            send_length += b" " * (self.HEADER - len(send_length))

            self.client.send(send_length)
            self.client.sendall(data)
        self.is_sending = False

    def tunnel_to_user(self, protocol,  data, mode="coded"):
        if mode == "coded":
            self.send(protocols.CODED_TUNNEL)
            self.send(self.main.username)
            self.send(protocol)
            self.send(data)

        elif mode == "bytes":
            self.send(protocols.BYTES_TUNNEL)
            self.send(self.main.username)
            self.send(protocol)
            self.send(data, mode="bytes")

    def disconnect(self, username):
        if self.connected_to_server:
            self.send(protocols.DISCONNECT)
            self.send(username)
            print("sent disconnect msg + username")

    def disconnect_for_non_user(self):
        if self.connected_to_server:
            self.send(protocols.DISCONNECT_NON_USER)
            print("sent disconnect for non user")

    def request_login(self, username):
        #### handeling bug - what if the users internet connection is obsecured??
        # if self.main.in_remote_desktop_session:
            # check if the other user has not cancelled
            # if yes:
                # stop remote desktop image sending and other sruff
                # go on about normal businness
            # elif no:
                # start tunneling screen and other stuff
        self.send(protocols.LOG_IN_REQUEST)
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
