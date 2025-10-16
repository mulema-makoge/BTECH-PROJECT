import socket
import threading
import json
from datetime import datetime
from crypto import load_key, decrypt, encrypt

# Server Configuration
HOST = '0.0.0.0'
PORT = 65432

# Global Variables
clients = {}  # Dictionary to store {username: client_socket}
key = load_key()

def broadcast(message_data, sender_username=None):
    """
    Broadcasts a message to all clients or a specific client.
    """
    recipient = message_data.get("recipient")

    if recipient and recipient in clients:
        # Private message
        try:
            encrypted_message = encrypt(json.dumps(message_data), key)
            clients[recipient].send(encrypted_message)
        except Exception as e:
            print(f"Error sending private message to {recipient}: {e}")
            clients.pop(recipient, None)
    else:
        # Broadcast to all except the sender
        for username, client_socket in clients.items():
            if username != sender_username:
                try:
                    encrypted_message = encrypt(json.dumps(message_data), key)
                    client_socket.send(encrypted_message)
                except Exception as e:
                    print(f"Error broadcasting to {username}: {e}")
                    clients.pop(username, None)

def handle_client(client_socket):
    """
    Handles a single client connection.
    """
    username = None
    try:
        encrypted_username = client_socket.recv(1024)
        username = decrypt(encrypted_username, key)

        if username in clients:
            # Handle username conflict
            error_message = {"sender": "Server", "content": "Username already taken.", "timestamp": ""}
            client_socket.send(encrypt(json.dumps(error_message), key))
            client_socket.close()
            return

        clients[username] = client_socket

        welcome_message = {
            "sender": "Server",
            "content": f"Welcome {username}! You are connected. Type /msg <user> <message> for private messages.",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        client_socket.send(encrypt(json.dumps(welcome_message), key))

        join_message = {
            "sender": "Server",
            "content": f"{username} has joined the chat!",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        broadcast(join_message, sender_username=username)

    except Exception as e:
        print(f"Error during user setup: {e}")
        client_socket.close()
        return

    while True:
        try:
            encrypted_message = client_socket.recv(1024)
            if not encrypted_message:
                break

            message_data = json.loads(decrypt(encrypted_message, key))
            message_data["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message_data["sender"] = username

            broadcast(message_data, sender_username=username)

        except:
            break

    # Cleanup
    clients.pop(username, None)
    if username:
        leave_message = {
            "sender": "Server",
            "content": f"{username} has left the chat.",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        broadcast(leave_message)
    client_socket.close()

def main():
    """
    Main function to start the server.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"[*] Listening as {HOST}:{PORT}")

    try:
        load_key()
    except FileNotFoundError:
        from crypto import generate_key
        generate_key()
        print("Generated a new secret key.")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

if __name__ == "__main__":
    main()