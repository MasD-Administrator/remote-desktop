
class Tunnels:
    def __init__(self):
        self.tunnels = {}

    def make_new_tunnel(self, requester_name, requester_socket_object, requestee_name, requestee_socket_object):
        self.tunnels[requester_name] = [requestee_name, requestee_socket_object]
        self.tunnels[requestee_name] = [requester_name, requester_socket_object]

    def get_socket_object(self, requester_name):
        return self.tunnels[requester_name][1]

    def delete_tunnel(self, requester_name):
        self.tunnels.pop(requester_name)