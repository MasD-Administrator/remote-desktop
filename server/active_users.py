import json


class ActiveUsers:
    def __init__(self):
        self.clients = {}

        with open("permanent_database.json") as permanent_database_file:
            self.data = json.load(permanent_database_file)

        self.client_names = self.data.keys()

    def add_client(self, client_name, client_connection_object):
        name_in_list = self.check(client_name)
        if not name_in_list:
            self.clients[client_name] = {"client_connection_object": client_connection_object,
                                         "has_active_tunnel": False,
                                         "is_online": False}
            return True
        else:
            return False

    def remove_client(self, name):
        self.clients.pop(name)

    def set_active_tunnel(self, name, boolean):
        self.clients[name]["has_active_tunnel"] = boolean

    def get_clients(self):
        return self.clients

    def check(self, client_name):
        if client_name in self.clients.keys():
            return True
        else:
            return False

    def log_in(self, client_name):
        self.clients[client_name]["is_online"] = True

    def log_out(self, client_name):
        self.clients[client_name]["is_online"] = False

    def get_socket_object(self, client_name):
        return self.clients[client_name]["client_connection_object"]

    def get_tunnel_status(self, client_name):
        return self.clients[client_name]["has_active_tunnel"]
