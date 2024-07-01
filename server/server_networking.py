import socket
import json
import threading

import active_users
import tunnels


class ServerNetwork:
    def __init__(self):
        self.active_users = active_users.ActiveUsers()
        self.tunnels = tunnels.Tunnels()

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
        self.client_name = ""

        while self.client_connected:
            msg_length = client.recv(self.HEADER).decode(self.FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = client.recv(msg_length).decode(self.FORMAT)

                self.protocol_check(msg, client)

    def protocol_check(self, message: str, client):
        protocol, data = message.split(self.protocols["PROTOCOL_MESSAGE_SPLITTER"])

        if protocol == self.protocols["DISCONNECT"]:
            self.client_connected = False

        # TODO - get the return values of the add client function and return a message appropriately
        elif protocol == self.protocols["ADD_ACTIVE_USER"]:
            name = data
            self.active_users.add_client(name, client)
            self.client_name = name

        elif protocol == self.protocols["REMOVE_ACTIVE_USER"]:
            name = data
            self.active_users.remove_client(name)
            self.client_name = None

        elif protocol == self.protocols["LOG_IN"]:
            pass

        elif protocol == self.protocols["LOG_OUT"]:
            pass

        elif protocol == self.protocols["MAKE_TUNNEL"]:
            requester_name, requestee_name = data.split(self.protocols["TUNNEL_CREATION_NAME_SEPARATOR"])

            if not self.active_users.get_tunnel_status(requester_name) and not self.active_users.get_tunnel_status(
                    requestee_name):
                self.active_users.set_active_tunnel(requester_name, True)
                self.active_users.set_active_tunnel(requestee_name, True)

                self.tunnels.make_new_tunnel(requester_name,
                                             self.active_users.get_socket_object(requester_name),
                                             requestee_name,
                                             self.active_users.get_socket_object(requestee_name))

                self.requestee = self.tunnels.get_socket_object(requester_name)
                self.client_name = requester_name
                # do the messaging to let the client know

        elif protocol == self.protocols["DELETE_TUNNEL"]:
            self.tunnels.delete_tunnel(self.client_name)

        elif protocol == self.protocols["TUNNEL"]:
            self.send(data, self.requestee)

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
        while True:
            inpt = input(":> ")
            if inpt == "report":
                print(self.active_users.clients.keys())
                print(self.tunnels.tunnels.keys())
            elif inpt == "user count":
                print(str(threading.active_count() - 2))
            elif inpt == "exit":
                self.shutdown()


if __name__ == "__main__":
    ServerNetwork().main()
