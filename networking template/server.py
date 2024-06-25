import socket
import threading

PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
HEADER = 64
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!EX"


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((SERVER, PORT))

def handle_client(conn, addr):
    print("new connection")
    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)

            if msg == DISCONNECT_MESSAGE:
                connected = False
            print(f"msg : {msg}")

    conn.close()
def start():
    server.listen()
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr)).start()
        print("current clients : " + str(threading.active_count() - 1))

print("server starting...")
start()