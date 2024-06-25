import socket

PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
HEADER = 64
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!EX"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER, PORT))

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(msg)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b" "* (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)


send("hello server")