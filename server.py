import smtplib
import socket
import threading
from datetime import datetime
from email.mime.text import MIMEText

PORT = 5050
SERVER = "localhost"
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
FROM_EMAIL = "cheamenghour20@gmail.com"
PASSWORD = "tqfi lpdm jcva xvzx"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

clients = {}
clients_lock = threading.Lock()
user_email_map = {}  #library email

def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def broadcast_message(message, sender_conn=None):
    with clients_lock:
        for c in clients:
            if c != sender_conn:
                try:
                    c.sendall(message.encode(FORMAT))
                except Exception as e:
                    print(f"[ERROR] Failed to send message to {clients[c]}: {e}")

def send_email(to_username, subject, body, from_user):
    to_email = user_email_map.get(to_username)
    
    if not to_email:
        print(f"\033[1;31m[ERROR] Email not found for username {to_username}\033[0m")
        return
    
    try:
        msg = MIMEText(f"From: {from_user}\n\n{body}")
        msg['Subject'] = f"Message from {from_user}: {subject}"
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(FROM_EMAIL, PASSWORD)
            smtp.send_message(msg)
        
        print(f"\033[1;32mEmail successfully sent to {to_username} at {to_email}\033[0m")
    except Exception as e:
        print(f"\033[1;31m[ERROR] Failed to send email: {e}\033[0m")

class ClientHandler(threading.Thread):
    def __init__(self, conn, addr):
        super().__init__()
        self.conn = conn
        self.addr = addr

    def run(self):
        try:
            user_data = self.conn.recv(1024).decode(FORMAT)
            username, email = user_data.split('|')
            print(f"\r\033[1m[{get_current_time()}] [NEW CONNECTION]\033[0m {self.addr} with username: \033[1m{username}\033[0m connected.\n\033[1;36m[Server Message]:\033[0m ", end="", flush=True)
            #store email
            with clients_lock:
                clients[self.conn] = username
                user_email_map[username] = email

            join_message = f"\033[3m{username} joined the room\033[0m"
            broadcast_message(join_message, self.conn)

            connected = True
            while connected:
                msg = self.conn.recv(1024).decode(FORMAT)
                if not msg:
                    break

                if msg == DISCONNECT_MESSAGE:
                    connected = False
                    disconnect_message = f"\033[3m{username} has left the chat.\033[0m"
                    print(disconnect_message)
                    broadcast_message(disconnect_message, self.conn)
                else:
                    formatted_message = f"[{get_current_time()}] {username}: {msg}"
                    print(f"\r\033[1m{formatted_message}\033[0m\n\033[1;36m[Server Message]:\033[0m ", end="", flush=True)
                    broadcast_message(formatted_message, self.conn)
                    
                    # Handle email sending
                    if msg.startswith("/email"):
                        try:
                            _, to_username, subject, *body_parts = msg.split(maxsplit=3)
                            body = " ".join(body_parts)
                            if to_username in user_email_map:
                                send_email(to_username, subject, body, username)
                                self.conn.sendall(f"\033[1;32mEmail sent to {to_username}\033[0m".encode(FORMAT))
                            else:
                                self.conn.sendall(f"\033[1;31mUser {to_username} not found\033[0m".encode(FORMAT))
                        except ValueError:
                            self.conn.sendall(f"\033[1;31mInvalid email format. Use: /email <username> <subject> <body>\033[0m".encode(FORMAT))

        finally:
            with clients_lock:
                del clients[self.conn]
                del user_email_map[username] #remove email and name when close
            self.conn.close()

def server_input():
    while True:
        command = input("\033[1;32m[SERVER INPUT]: \033[0m")
        
        if command.lower() == 'q':
            print('\033[1;33m[SERVER SHUTTING DOWN]\033[0m')
            server.close()
            break
        elif command.startswith('/kick'):
            username_to_kick = command.split()[1]
            conn_to_kick = next((conn for conn, user in clients.items() if user == username_to_kick), None)
            if conn_to_kick:
                kick_message = f"\033[3mYou have been kicked from the server.\033[0m"
                conn_to_kick.sendall(kick_message.encode(FORMAT))
                conn_to_kick.close()
                with clients_lock:
                    del clients[conn_to_kick]
                print(f'\033[1;31mKicked {username_to_kick}\033[0m')
            else:
                print(f'\033[1;31mUser {username_to_kick} not found\033[0m')
        elif command.startswith('/list'):
            print('\033[1;34mConnected clients:\033[0m')
            with clients_lock:
                for username in clients.values():
                    print(f'- {username}')
        else:
            print('\033[1;31mUnknown command. Use /list to see connected users or /kick <username> to remove a user.\033[0m')

def start():
    print('\033[1;32m[SERVER STARTED]!\033[0m')
    server.listen()
    
    threading.Thread(target=server_input, daemon=True).start()

    while True:
        try:
            conn, addr = server.accept()
            client_handler = ClientHandler(conn, addr)
            client_handler.start()
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    start()
