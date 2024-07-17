import socket
import json
import threading

import users
import protocols

class ServerNetwork:
    def __init__(self):
        self.users = users.Users()

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

        while True:
            conn, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(conn,)).start()

    def send(self, data, client_connection_object):
        message = data.encode(self.FORMAT)
        msg_length = len(data)
        send_length = str(msg_length).encode(self.FORMAT)
        send_length += b" " * (self.HEADER - len(send_length))
        client_connection_object.send(send_length)
        client_connection_object.send(message)

    def send_as_string(self, data, client_connection_object):
        data = str(data)
        message = data.encode(self.FORMAT)
        msg_length = len(data)
        send_length = str(msg_length).encode(self.FORMAT)
        send_length += b" " * (self.HEADER - len(send_length))
        client_connection_object.send(send_length)
        client_connection_object.send(message)

    def handle_client(self, client):
        self.client = client
        self.client_connected = True

        while self.client_connected:
            msg_length = client.recv(self.HEADER).decode(self.FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = client.recv(msg_length).decode(self.FORMAT)

                self.protocol_check(msg, client)

    def receive(self, client):
        if client is not None:
            msg_length = client.recv(self.HEADER).decode(self.FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = client.recv(msg_length).decode(self.FORMAT)
                return msg

    def receive_as_string(self, client):
        if client is not None:
            msg_length = client.recv(self.HEADER).decode(self.FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = client.recv(msg_length).decode(self.FORMAT)
                return msg

    def protocol_check(self, protocol, user_socket):
        if protocol == protocols.DISCONNECT:
            self.client_connected = False

        elif protocol == protocols.MAKE_USER_REQUEST:
            username = self.receive(user_socket)
            self.make_new_user(username, user_socket)

        elif protocol == protocols.DELETE_USER_REQUEST:
            username = self.receive(user_socket)
            self.delete_user(username)

        elif protocol == protocols.CHANGE_USERNAME_REQUEST:
            current_username = self.receive(user_socket)
            new_username = self.receive(user_socket)
            self.change_username(current_username, new_username)

        elif protocol == protocols.LOG_IN_REQUEST:
            username = self.receive(user_socket)
            self.users.login(username, user_socket)

        elif protocol == protocols.LOG_OUT_REQUEST:
            username = self.receive(user_socket)
            self.users.logout(username)

        elif protocol == protocols.MAKE_RESTRICTED_REQUEST:
            username = self.receive(user_socket)
            self.make_restricted(username)

        elif protocol == protocols.MAKE_UNRESTRICTED_REQUEST:
            username = self.receive(user_socket)
            self.make_unrestricted(username)

        elif protocol == protocols.MAKE_TUNNEL_REQUEST:
            original_requester = self.receive(user_socket)
            requestee_name = self.receive(user_socket)
            result = self.users.make_tunnel(original_requester, requestee_name)

            if result == protocols.USER_RESTRICTED:  # User restricted
                self.send(protocols.DECIDE_TUNNEL_CREATION, self.users.get_socket_of_user(requestee_name))
                self.send(original_requester, self.users.get_socket_of_user(requestee_name))
            else:
                self.send(protocols.MAKE_TUNNEL_REQUEST_RESULT, user_socket)
                self.send_as_string(result, user_socket)

        # these two  function are both continuation and subsets of make_tunnel initially
        # based on the requestee inputs
        elif protocol == protocols.DECIDE_TUNNEL_CREATION_RETURN:
            decision = self.receive_as_string(user_socket)
            if eval(decision) == False:
                original_requester = self.receive(user_socket)
                self.send(protocols.MAKE_TUNNEL_REQUEST_RESULT, self.users.get_socket_of_user(original_requester))
                self.send(protocols.USER_DECLINED_TUNNEL_REQEUST, self.users.get_socket_of_user(original_requester))

            elif eval(decision) == True:
                original_requester = self.receive(user_socket)
                original_requestee = self.receive(user_socket)
                self.send(protocols.MAKE_TUNNEL_REQUEST_RESULT, self.users.get_socket_of_user(original_requester))
                self.send(protocols.USER_ACCEPTED_TUNNEL_REQEUST, self.users.get_socket_of_user(original_requester))

                # self.users.make_forced_tunnel(original_requester_name, original_requestee_name) # TODO make this work

        # elif protocol == self.protocols["REMOVE_TUNNEL"]:
        #     requester_name, requestee_name = data.split(self.protocols["REMOVE_TUNNEL_INPUT_SEPARATOR"])
        #     self.users.remove_tunnel(requester_name, requestee_name)
        #
        # elif protocol == self.protocols["TUNNEL_STREAM"]:
        #     username, tunnel_data = data.split(self.protocols["TUNNEL_STREAM_USERNAME_DATA_SEPARATOR"])
        #     self.send(self.protocols["TUNNEL_STREAM"], tunnel_data, self.users.users[username]["tunneling_socket_object"])
    def make_new_user(self, username, user_socket):
        result = self.users.make_new_user(username, False)

        if result:
            self.users.login(username, user_socket)

        self.send(protocols.MAKE_USER_REQUEST_RESULT, user_socket)
        self.send_as_string(result, self.client)

    def delete_user(self, username):
        user_socket = self.users.get_socket_of_user(username)
        result = self.users.delete_user(username)

        self.send(protocols.DELETE_USER_REQUEST_RESULT, user_socket)
        self.send_as_string(result, user_socket)

    def change_username(self, current_username, new_username):
        result = self.users.change_username(current_username, new_username)

        self.send(protocols.CHANGE_USERNAME_REQUEST_RESULT, self.users.get_socket_of_user(new_username))
        self.send_as_string(result, self.users.get_socket_of_user(new_username))

    def make_restricted(self, username):
        result = self.users.make_restricted(username)
        self.send(protocols.MAKE_RESTRICTED_REQUEST_RESULT, self.users.get_socket_of_user(username))
        self.send_as_string(result, self.users.get_socket_of_user(username))

    def make_unrestricted(self, username):
        result = self.users.make_unrestricted(username)
        self.send(protocols.MAKE_UNRESTRICTED_REQUEST_RESULT, self.users.get_socket_of_user(username))
        self.send_as_string(result, self.users.get_socket_of_user(username))



if __name__ == "__main__":
    ServerNetwork().main()
