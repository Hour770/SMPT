import socket
import threading
import time
from datetime import datetime

PORT = 5050
SERVER = "localhost"
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"

def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class ChatClient:
    def __init__(self):
        self.username = None
        self.email = None
        self.connection = None

    def send(self, msg):
        try:
            message = msg.encode(FORMAT)
            self.connection.sendall(message)
        except Exception as e:
            print(f"\033[1;31m[ERROR] Failed to send message: {e}\033[0m")

    def receive(self):
        while True:
            try:
                message = self.connection.recv(1024).decode(FORMAT)
                if message:
                    print(f"\r\033[1;34m{message}\033[0m\n\033[1;32m{self.username}:\033[0m ", end="", flush=True)
            except Exception as e:
                print(f"\033[1;31m[ERROR] {e}\033[0m")
                break

    def connect(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(ADDR)
        return client

    def start(self):
        self.username = input('Enter your username: ')
        self.email = input(f'Enter your email: ')
        
        answer = input(f'Would you like to connect with username: {self.username} and email: {self.email} (yes/no)? ')
        if answer.lower() != 'yes':
            return

        self.connection = self.connect()
        self.send(f"{self.username}|{self.email}")

        receive_thread = threading.Thread(target=self.receive)
        receive_thread.daemon = True
        receive_thread.start()

        while True:
            msg = input(f"\033[1;32m{self.username}:\033[0m ")

            if msg.lower() == 'q':
                self.send(DISCONNECT_MESSAGE)
                break

            self.send(msg)

        print('\033[1;33mDisconnected\033[0m')
        self.connection.close()

if __name__ == "__main__":
    client = ChatClient()
    client.start()
