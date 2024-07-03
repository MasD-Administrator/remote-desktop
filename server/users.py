import json


class Users:
    def __init__(self):
        super().__init__()
        self.users = {}

        with open("user_database.json") as database:
            data = json.load(database)

            for user in list(data.keys()):
                self.add_user(user, data[user])


    def add_user(self, user_name, password):


        username_in_database = self.username_in_database(user_name)
        password_in_database = self.password_in_database(password)

        if not username_in_database and not password_in_database:
            self.users[user_name] = {
                "user_connection_object": None,
                "is_online": False,
                "has_active_tunnel": False,
                "tunneling_socket": None,
                "password": password
            }
            self.save_database()
            return True
        elif username_in_database or password_in_database:
            self.save_database()
            return False


    def delete_user(self, user_name, password):
        username_in_database = self.username_in_database(user_name)
        if username_in_database and password == self.users[user_name]["password"]:
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

    def make_tunnel(self, requester_name, requestee_name, requestee_password):
        if self.is_user_online(requester_name) and self.is_user_online(requestee_name) and requestee_password == self.users[requestee_name]["password"]:
            self.users[requester_name]["has_active_tunnel"] = True
            self.users[requestee_name]["has_active_tunnel"] = True

            self.users[requester_name]["tunneling_socket"] = self.users[requestee_name]["user_connection_object"]
            self.users[requestee_name]["tunneling_socket"] = self.users[requester_name]["user_connection_object"]
            return True
        else:
            print("user offline or wrong password")
            return False

    def remove_tunnel(self,  requester_name, requestee_name):
        self.users[requester_name]["has_active_tunnel"] = False
        self.users[requestee_name]["has_active_tunnel"] = False

        self.users[requester_name]["tunneling_socket"] = None
        self.users[requestee_name]["tunneling_socket"] = None

    def is_user_online(self, user_name):
        return self.users[user_name]["is_online"]


    def users_status(self):
        a = {}
        for name in list(self.users.keys()):
            a[name] = self.users[name]["is_online"]

        return json.dumps(a, indent=4)

    def save_database(self):
        with open("user_database.json", "w") as database:
            write_data = {}

            for user in list(self.users.keys()):
                write_data[user] = self.users[user]["password"]

            json.dump(write_data, database, indent=4)

    def username_in_database(self, user_name):
        return user_name in self.users

    def password_in_database(self, password):
        for user in self.users:
            if self.users[user]["password"] == password:
                return True
        return False





