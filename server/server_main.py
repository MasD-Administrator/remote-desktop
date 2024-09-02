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

            ip = server_data["ip"]
            if ip == "localhost":
                self.IP = socket.gethostbyname(socket.gethostname())
            else:
                self.IP = ip

    def main(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.IP, self.PORT))
        self.server_socket.listen()

        print(f"IP: {self.IP}\nPORT: {self.PORT}")

        while True:
            conn, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(conn,)).start()

    def send(self, data, client_connection_object, mode="coded"):
        # mode = coded, raw, string
        if mode == "string":
            data = str(data).encode(self.FORMAT)
        elif mode == "coded":
            data = data.encode(self.FORMAT)
        elif mode == "raw":
            data = data
        elif mode == "sendall":
            data = data
            msg_length = len(data)
            send_length = str(msg_length).encode(self.FORMAT)
            send_length += b" " * (self.HEADER - len(send_length))
            try:
                client_connection_object.send(send_length)
                client_connection_object.sendall(data)
            except AttributeError:
                print("Warning [SENDALL]: cannot send")
            return

        msg_length = len(data)
        send_length = str(msg_length).encode(self.FORMAT)
        send_length += b" " * (self.HEADER - len(send_length))
        try:
            client_connection_object.send(send_length)
            client_connection_object.send(data)
        except AttributeError as e:
            print(e)
            print(f"data: {data}")
            print("Warning [NORM]: cannot send")

    def handle_client(self, client):
        self.client_connected = True

        while self.client_connected:
            msg_length = client.recv(self.HEADER)
            msg_length = msg_length.decode(self.FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                protocol = client.recv(msg_length).decode(self.FORMAT)
                should_quit = self.protocol_check(protocol, client)
                if should_quit:
                    break
                    

    def receive(self, client, mode="coded"):
        if client is not None:
            msg_length = client.recv(self.HEADER).decode(self.FORMAT)
            msg_length = int(msg_length)
            if msg_length:
                if mode == "coded":
                    msg = client.recv(msg_length)
                    msg = msg.decode(self.FORMAT)
                    return msg
                elif mode == "raw":
                    msg = client.recv(msg_length)
                    msg = msg
                    return msg
                elif mode == "big":
                    big_data = b""
                    while len(big_data) < msg_length:
                        packet = client.recv(msg_length - len(big_data))
                        if not packet:
                            break
                        big_data += packet
                    return big_data

    def protocol_check(self, protocol, user_socket):
        if protocol == protocols.DISCONNECT:
            username = self.receive(user_socket)
            self.users.logout(username)
            self.send(protocols.DISCONNECT_RESULT, user_socket)
            return True

        elif protocol == protocols.DISCONNECT_NON_USER:
            self.send(protocols.DISCONNECT_RESULT, user_socket)
            return True

        elif protocol == protocols.MAKE_USER_REQUEST:
            username = self.receive(user_socket)
            self.make_new_user(username, user_socket)

        elif protocol == protocols.DELETE_USER_REQUEST:
            username = self.receive(user_socket)
            self.delete_user(username)

        elif protocol == protocols.CHANGE_USERNAME_REQUEST:
            current_username = self.receive(user_socket)
            new_username = self.receive(user_socket)
            result = self.users.change_username(current_username, new_username)

            self.send(protocols.CHANGE_USERNAME_REQUEST_RESULT, user_socket)
            self.send(result, user_socket, mode="string")

        elif protocol == protocols.LOG_IN_REQUEST:
            username = self.receive(user_socket)
            self.users.login(username, user_socket)

        elif protocol == protocols.MAKE_RESTRICTED_REQUEST:
            username = self.receive(user_socket)
            self.make_restricted(username)

        elif protocol == protocols.MAKE_UNRESTRICTED_REQUEST:
            username = self.receive(user_socket)
            self.make_unrestricted(username)

        elif protocol == protocols.MAKE_TUNNEL_REQUEST:
            print("request received")
            original_requester = self.receive(user_socket)
            requestee_name = self.receive(user_socket)
            result = self.users.make_tunnel(original_requester, requestee_name)

            if result == protocols.USER_RESTRICTED:  # User restricted
                self.send(protocols.DECIDE_TUNNEL_CREATION, self.users.get_socket_of_user(requestee_name))
                self.send(original_requester, self.users.get_socket_of_user(requestee_name))
            else:
                self.send(protocols.MAKE_TUNNEL_REQUEST_RESULT, user_socket)
                self.send(result, user_socket, mode="string")

        elif protocol == protocols.DECIDE_TUNNEL_CREATION_RETURN:
            # these two  function are both continuation and functions of make_tunnel initially
            # based on the requestee inputs
            decision = eval(self.receive(user_socket)) # True if accepted
            print(f"decision of requestee: {decision}")
            if not decision:
                original_requester = self.receive(user_socket)
                self.send(protocols.MAKE_TUNNEL_REQUEST_RESULT, self.users.get_socket_of_user(original_requester))
                self.send(protocols.USER_DECLINED_TUNNEL_REQEUST, self.users.get_socket_of_user(original_requester))

            elif decision:
                original_requester = self.receive(user_socket)
                original_requestee = self.receive(user_socket)
                self.send(protocols.MAKE_TUNNEL_REQUEST_RESULT, self.users.get_socket_of_user(original_requester))
                self.send(protocols.USER_ACCEPTED_TUNNEL_REQEUST, self.users.get_socket_of_user(original_requester))

                self.users.make_forced_tunnel(original_requester, original_requestee)

        elif protocol == protocols.CODED_TUNNEL:
            username = self.receive(user_socket)
            tunnel_protocol = self.receive(user_socket)
            data = self.receive(user_socket)

            self.server_tunnel(username, tunnel_protocol, data)

        elif protocol == protocols.BYTES_TUNNEL:
            username = self.receive(user_socket)
            tunnel_protocol = self.receive(user_socket)
            data = self.receive(user_socket, mode="big")

            self.server_tunnel(username, tunnel_protocol, data, mode="sendall")

        elif protocol == protocols.REMOVE_TUNNEL:
            username = self.receive(user_socket)
            self.users.remove_tunnel(username)



    def server_tunnel(self, username, tunneled_protocol, data, mode="coded"):
        tunnel_to = self.users.get_tunnel_of_user(username)
        self.send(protocols.TUNNELED, tunnel_to)
        self.send(tunneled_protocol, tunnel_to)
        if mode == "coded":
            self.send(data, tunnel_to)
        elif mode == "raw":
            self.send(data, tunnel_to, mode="raw")
        elif mode == "sendall":
            self.send(data, tunnel_to, mode="sendall")

    def make_new_user(self, username, user_socket):
        result = self.users.make_new_user(username, False)

        if result:
            self.users.login(username, user_socket)

        self.send(protocols.MAKE_USER_REQUEST_RESULT, user_socket)
        self.send(result, self.client, mode="string")

    def delete_user(self, username):
        user_socket = self.users.get_socket_of_user(username)
        result = self.users.delete_user(username)

        self.send(protocols.DELETE_USER_REQUEST_RESULT, user_socket)
        self.send(result, user_socket, mode="string")


    def make_restricted(self, username):
        result = self.users.make_restricted(username)
        self.send(protocols.MAKE_RESTRICTED_REQUEST_RESULT, self.users.get_socket_of_user(username))
        self.send(result, self.users.get_socket_of_user(username), mode="string")

    def make_unrestricted(self, username):
        result = self.users.make_unrestricted(username)
        self.send(protocols.MAKE_UNRESTRICTED_REQUEST_RESULT, self.users.get_socket_of_user(username))
        self.send(result, self.users.get_socket_of_user(username), mode="string")


if __name__ == "__main__":
    ServerNetwork().main()
