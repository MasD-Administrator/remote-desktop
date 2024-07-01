import json


class Users:
    def __init__(self):
        self.users = {}

        with open("user_database.json") as database:
            for user_name in json.load(database)["clients"]:
                self.add_user(user_name)


    def add_user(self, user_name):
        username_in_database = self.username_in_database(user_name)
        if not username_in_database:
            self.users[user_name] = {
                "client_connection_object": None,
                "is_online": False,
                "has_active_tunnel": False
            }
        elif username_in_database:
            return False

        self.save_database()

    def delete_user(self, user_name):
        username_in_database = self.username_in_database(user_name)
        if username_in_database:
            self.users.pop(user_name)
        else:
            return False

        self.save_database()

    def make_user_online(self, user_name, user_connection_object):
        self.users[user_name]["is_online"] = True
        self.users[user_name]["user_connection_object"] = user_connection_object

    def make_user_offline(self, user_name):
        self.users[user_name]["is_online"] = False
        self.users[user_name]["user_connection_object"] = None
        self.users[user_name]["has_active_tunnel"] = False

    def activate_tunnel_status(self, user_name):
        self.users[user_name]["has_active_tunnel"] = True

    def disable_tunnel_status(self, user_name):
        self.users[user_name]["has_active_tunnel"] = False


    def save_database(self):
        with open("user_database.json", "w") as database:
            json.dump({"clients": list(self.users.keys())}, database, indent=4)

    def username_in_database(self, user_name):
        if user_name in self.users:
            return True
        else:
            return False





