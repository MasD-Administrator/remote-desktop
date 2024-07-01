import socket
import json
import threading

import tunnels
import users

class ServerNetwork:
    def __init__(self):
        self.tunnels = tunnels.Tunnels()
        self.users = users.Users()

        with open("../protocols.json") as protocols_file:
            self.protocols = json.load(protocols_file)

        with open("server_data.json") as server_data_file:
            server_data = json.load(server_data_file)

            self.PORT = server_data["port"]
            self.HEADER = server_data["header"]
            self.FORMAT = server_data["format"]

            if server_data["ip"] == True:
                self.IP = socket.gethostbyname(socket.gethostname())
            elif type(server_data["ip"]) is str:
                self.IP = server_data["ip"]
            else:
                self.IP = None

    def main(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.IP, self.PORT))
        self.server_socket.listen()

        threading.Thread(target=self.input_check).start()

        while True:
            conn, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr)).start()

    def handle_client(self, client, address):
        self.client_connected = True

        while self.client_connected:
            msg_length = client.recv(self.HEADER).decode(self.FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = client.recv(msg_length).decode(self.FORMAT)

                self.protocol_check(msg, client)

    def protocol_check(self, message: str, user):
        # TODO - server user msg handeling
        protocol, data = message.split(self.protocols["PROTOCOL_MESSAGE_SPLITTER"])

        if protocol == self.protocols["DISCONNECT"]:
            self.client_connected = False

        elif protocol == self.protocols["ADD_USER"]:
            name = data
            if self.users.add_user(name):
                self.users.make_user_online(name, user)
                # send(success)
            else:
                print("alrdy exists mofos")
                # send(failure)

        elif protocol == self.protocols["DELETE_USER"]:
            name = data
            self.users.delete_user(name)

        elif protocol == self.protocols["LOG_IN"]:
            name = data
            self.users.make_user_online(name, user)

        elif protocol == self.protocols["LOG_OFF"]:
            name = data
            self.users.make_user_offline(name)

    def send(self, msg, client_connection_object):
        message = msg.encode(self.FORMAT)
        msg_length = len(msg)
        send_length = str(msg_length).encode(self.FORMAT)
        send_length += b" " * (self.HEADER - len(send_length))
        client_connection_object.send(send_length)
        client_connection_object.send(message)

    def shutdown(self):
        from os import _exit
        _exit(0)

    # DEBUGGER
    def input_check(self):
        debug = False
        while debug == True:
            inpt = input(":> ")
            # TODO - add the debugging functionality


if __name__ == "__main__":
    ServerNetwork().main()
