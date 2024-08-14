import json
import protocols


class Users:
    def __init__(self):
        super().__init__()
        self.users = {}

        with open("user_database.json") as database:
            data = json.load(database)

            for user in list(data.keys()):
                self.make_new_user(user, data[user])

    # The reason for getting restricted mode as an argument is because it's saved in the database therefore needs to be
    # re-initialized at the beginning.
    def make_new_user(self, user_name, restricted_mode):
        username_in_database = self.username_in_database(user_name)

        if not username_in_database:
            self.users[user_name] = {
                "user_connection_object": None,
                "tunneling_socket_object": None,
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
            self.save_database()
            return True
        else:
            self.save_database()
            return False

    def change_username(self, current_username, new_username):

        if not self.username_in_database(new_username):
            data = self.users[current_username]
            self.users.pop(current_username)
            self.users[new_username] = data

            self.save_database()
            return True
        else:
            return False

    def make_restricted(self, user_name):
        try:
            self.users[user_name]["restricted"] = True
            self.save_database()
            return True
        except Exception as e:
            print(e)
            return False

    def make_unrestricted(self, user_name):
        try:
            self.users[user_name]["restricted"] = False
            self.save_database()
            return True
        except Exception as e:
            print(e)
            return False

    def login(self, user_name, user_connection_object):
        print(f"{user_name} logged in")
        self.users[user_name]["user_connection_object"] = user_connection_object

    def logout(self, user_name):
        print(f"{user_name} logged out")
        self.users[user_name]["user_connection_object"] = None

    def make_tunnel(self, requester_name, requestee_name):
        if self.username_in_database(requestee_name):
            if self.is_user_online(requestee_name):
                if not self.users[requestee_name]["restricted"]:
                    self.users[requester_name]["tunneling_socket_object"] = self.users[requestee_name]["user_connection_object"]
                    self.users[requestee_name]["tunneling_socket_object"] = self.users[requester_name]["user_connection_object"]
                    return True
                else:
                    return protocols.USER_RESTRICTED
            else:
                return protocols.USER_OFFLINE
        else:
            return protocols.USER_DOESNT_EXIST

    def make_forced_tunnel(self, requester_name, requestee_name):
        self.users[requester_name]["tunneling_socket_object"] = self.users[requestee_name]["user_connection_object"]
        self.users[requestee_name]["tunneling_socket_object"] = self.users[requester_name]["user_connection_object"]

    def remove_tunnel(self, username):
        print(f"remove tunnel of : {username}")
        self.users[username]["tunneling_socket_object"] = None

    def is_user_online(self, user_name):
        if self.users[user_name]["user_connection_object"] is None:
            return False  # no connection object means not online
        else:
            return True

    def username_in_database(self, user_name):
        return user_name in self.users

    def save_database(self):
        with open("user_database.json", "w") as database:
            write_data = {}

            for user in list(self.users.keys()):
                write_data[user] = self.users[user]["restricted"]

            json.dump(write_data, database, indent=4)

    def get_socket_of_user(self, user_name):
        return self.users[user_name]["user_connection_object"]

    def get_tunnel_of_user(self, username):
        return self.users[username]["tunneling_socket_object"]