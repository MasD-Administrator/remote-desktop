import socket
import json

from threading import Thread


class ControllerNetwork:
    def __init__(self):
        with open("../protocols.json") as file:
            self.protocols = json.load(file)

        with open("user_network_data.json") as controller_data_file:
            controller_data = json.load(controller_data_file)

            self.SERVER_PORT = controller_data["server_port"]
            self.HEADER = controller_data["header"]
            self.FORMAT = controller_data["format"]

            if controller_data["server_ip"] == True:
                self.SERVER_IP = socket.gethostbyname(socket.gethostname())
            elif type(controller_data["ip"]) is str:
                self.SERVER_IP = controller_data["ip"]
            else:
                self.SERVER_IP = None

    def main(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.SERVER_IP, self.SERVER_PORT))

        Thread(target=self.receive_data).start()
        Thread(target=self.input_check).start()

        self.test_code()

    def receive_data(self):
        connected = True
        while connected:
            msg_length = self.client.recv(self.HEADER).decode(self.FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = self.client.recv(msg_length).decode(self.FORMAT)

                print(msg)
                # TODO this is where protocol check should be

    def send(self, protocol, data):
        msg = protocol + self.protocols["PROTOCOL_MESSAGE_SPLITTER"] + data
        message = msg.encode(self.FORMAT)
        msg_length = len(msg)
        send_length = str(msg_length).encode(self.FORMAT)
        send_length += b" " * (self.HEADER - len(send_length))
        self.client.send(send_length)
        self.client.send(message)

    def test_code(self):
        ...
        self.make_user("a", 'a1')
        self.make_user("b", "b1")

        self.login("a")
        self.login("b")

        self.make_tunnel("a", "b", "b1")
        self.tunnel_stream("hello world")

        self.remove_tunnel("a", "b")




    def make_user(self, username, password):
        self.send(self.protocols["ADD_USER"], f"{username}{self.protocols['NAME_PASSWORD_SEPARATOR']}{password}")

    def delete_user(self, username, password):
        self.send(self.protocols["DELETE_USER"], f"{username}{self.protocols['NAME_PASSWORD_SEPARATOR']}{password}")

    def login(self, username):
        self.send(self.protocols["LOG_IN"], username)

    def logout(self, username):
        self.send(self.protocols["LOG_OUT"], username)

    def make_tunnel(self, username, connector_name, connector_password):
        self.send(self.protocols["MAKE_TUNNEL"], f"{username}{self.protocols['MAKE_TUNNEL_INPUT_SEPARATOR']}{connector_name}{self.protocols['MAKE_TUNNEL_INPUT_SEPARATOR']}{connector_password}")

    def remove_tunnel(self, username, connector_name):
        self.send(self.protocols["REMOVE_TUNNEL"], f"{username}{self.protocols['REMOVE_TUNNEL_INPUT_SEPARATOR']}{connector_name}")

    def tunnel_stream(self, data):
        self.send(self.protocols['TUNNEL_STREAM'], data)

    def network_shutdown(self):

        self.send(self.protocols["DISCONNECT"], " ")

        from os import _exit
        _exit(0)

    def input_check(self):
        debug = True
        while debug == True:
            inpt = input(":> ")
            if inpt == "exit":
                self.network_shutdown()


if __name__ == "__main__":
    ControllerNetwork().main()