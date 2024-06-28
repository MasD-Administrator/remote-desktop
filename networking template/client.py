import socket

PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
HEADER = 64
FORMAT = "utf-8"

with open("../protocols.json") as file:
    import json
    protocols = json.load(file)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER, PORT))

def send(protocol, data):
    msg = protocol + protocols["PROTOCOL_MESSAGE_SPLITTER"] + data
    message = msg.encode(FORMAT)
    msg_length = len(msg)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b" " * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)

def main():
    connected = True
    while connected:
        msg_length = client.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = client.recv(msg_length).decode(FORMAT)

            print(msg)


from threading import Thread
Thread(target=main).start()


send(protocols["ADD_ACTIVE_USER"], "sooriya")
send(protocols["ADD_ACTIVE_USER"], "deepana")

send(protocols["MAKE_TUNNEL"], f"sooriya{protocols['TUNNEL_CREATION_NAME_SEPARATOR']}deepana")

for i in range(0, 3):
    send(protocols["TUNNEL"], "hello me!")

send("DELETE_TUNNEL", "hOW dId YoU sEE tHIs MesSAge")

