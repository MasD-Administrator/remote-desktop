import socket
import json
import threading

import users


class ServerNetwork:
    def __init__(self):
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
        # TODO - server user msg handling
        # TODO - loads of error handling to do
        # 'data' for most of the user related protocols is the name of the user
        protocol, data = message.split(self.protocols["PROTOCOL_MESSAGE_SPLITTER"])

        if protocol == self.protocols["DISCONNECT"]:
            self.client_connected = False

        elif protocol == self.protocols["ADD_USER"]:
            if self.users.add_user(data, False):
                self.users.login(data, user)
                self.send(self.protocols["ADD_USER"], True, user)
            else:
                self.send(self.protocols["ADD_USER"], False, user)

        elif protocol == self.protocols["DELETE_USER"]:
            self.users.delete_user(data)

        elif protocol == self.protocols["LOG_IN"]:
            self.users.login(data, user)

        elif protocol == self.protocols["LOG_OUT"]:
            self.users.logoff(data)

        elif protocol == self.protocols["MAKE_RESTRICTED"]:
            made_restricted = self.users.make_restricted(data)
            if made_restricted:
                self.send(self.protocols["MAKE_RESTRICTED"], True, user)
            elif not made_restricted:
                self.send(self.protocols["MAKE_RESTRICTED"], False, user)

        elif protocol == self.protocols["MAKE_UNRESTRICTED"]:
            made_unrestricted = self.users.make_unrestricteded(data)
            if made_unrestricted:
                self.send(self.protocols["MAKE_UNRESTRICTED"], True, user)
            elif not made_unrestricted:
                self.send(self.protocols["MAKE_UNRESTRICTED"], False, user)

        elif protocol == self.protocols["MAKE_TUNNEL"]:
            requester_name, requestee_name = data.split(self.protocols["MAKE_TUNNEL_INPUT_SEPARATOR"])
            result = self.users.make_tunnel(requester_name, requestee_name)
            print(result)
            self.send(self.protocols["MAKE_TUNNEL"], result, user)

        elif protocol == self.protocols["REMOVE_TUNNEL"]:
            requester_name, requestee_name = data.split(self.protocols["REMOVE_TUNNEL_INPUT_SEPARATOR"])
            self.users.remove_tunnel(requester_name, requestee_name)

        elif protocol == self.protocols["TUNNEL_STREAM"]:
            username, send_data = data.split(self.protocols["TUNNEL_STREAM_NAME_DATA_SEPARATOR"])
            self.send(self.protocols["TUNNEL_STREAM"], data, self.users.users[username]["tunneling_socket"])

        elif protocol == self.protocols["CHANGE_USERNAME"]:
            current_username, new_username = data.split(self.protocols["CHANGE_USERNAME_SEPARATOR"])
            result = self.users.change_username(current_username, new_username)

            self.send(self.protocols["CHANGE_USERNAME"], result, user)
    def send(self, protocol, data , client_connection_object):
        print("sent: " + str(protocol) + str(data))
        msg = f"{protocol}{self.protocols["PROTOCOL_MESSAGE_SPLITTER"]}{data}"
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
            if inpt == "users":
                for name in self.users.users:
                    print(f"{name}: [is_online:{self.users.users[name]['is_online']}, has_active_tunnel:{self.users.users[name]['has_active_tunnel']}] ")

if __name__ == "__main__":
    ServerNetwork().main()
