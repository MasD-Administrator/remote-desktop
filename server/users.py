import json


class Users:
    def __init__(self):
        super().__init__()
        self.users = {}

        with open("user_database.json") as database:
            data = json.load(database)

            for user in list(data.keys()):
                self.add_user(user, data[user])

    def add_user(self, user_name, restricted_mode):

        username_in_database = self.username_in_database(user_name)

        if not username_in_database:
            self.users[user_name] = {
                "user_connection_object": None,
                "tunneling_socket": None,
                "restricted": restricted_mode
            }
            self.save_database()
            return True
        elif username_in_database:
            self.save_database()
            return False

    def delete_user(self, user_name):
        username_in_database = self.username_in_database(user_name)
        if username_in_database:
            self.users.pop(user_name)
        else:
            print("user not in database")
            return False

        self.save_database()

    def change_username(self, current_username, new_username):
        try:
            data = self.users[current_username]
            self.users.pop(current_username)
            self.users[new_username] = data

            self.save_database()
            return True
        except Exception as e:
            print(e)
            return False


    def make_restricted(self, user_name):
        try:
            self.users[user_name]["restricted"] = True
            self.save_database()
            return True
        except Exception as e:
            print(e)
            return False

    def make_unrestricteded(self, user_name):
        try:
            self.users[user_name]["restricted"] = False
            self.save_database()
            return True
        except Exception as e:
            print(e)
            return False

    def login(self, user_name, user_connection_object):
        self.users[user_name]["user_connection_object"] = user_connection_object

    def logoff(self, user_name):
        self.users[user_name]["user_connection_object"] = None

    # TODO - when tunneling, the restricted mode requires the requestee to get prompted to accept the connection or decline it

    def make_tunnel(self, requester_name, requestee_name):
        if self.username_in_database(requestee_name):
            if self.is_user_online(requestee_name):
                if not self.users[requestee_name]["restricted"]:
                    self.users[requester_name]["tunneling_socket"] = self.users[requestee_name]["user_connection_object"]
                    self.users[requestee_name]["tunneling_socket"] = self.users[requester_name]["user_connection_object"]
                    return True
                else:
                    return "User restricted"
            else:
                return "User offline"
        else:
            return "User doesn't exist"

    def make_forced_tunnel(self, requester_name, requestee_name):
        self.users[requester_name]["tunneling_socket"] = self.users[requestee_name]["user_connection_object"]
        self.users[requestee_name]["tunneling_socket"] = self.users[requester_name]["user_connection_object"]

    def remove_tunnel(self, requester_name, requestee_name):
        self.users[requester_name]["tunneling_socket"] = None
        self.users[requestee_name]["tunneling_socket"] = None

    def is_user_online(self, user_name):
        if self.users[user_name]["user_connection_object"] is None:
            return False  # no connection object means not online
        else:
            return True

    def users_status(self):
        a = {}
        for name in list(self.users.keys()):
            a[name] = self.users[name]["is_online"]

        return json.dumps(a, indent=4)

    def save_database(self):
        with open("user_database.json", "w") as database:
            write_data = {}

            for user in list(self.users.keys()):
                write_data[user] = self.users[user]["restricted"]

            json.dump(write_data, database, indent=4)

    def username_in_database(self, user_name):
        return user_name in self.users

    def get_socket_of_user(self, user_name):
        return self.users[user_name]["user_connection_object"]