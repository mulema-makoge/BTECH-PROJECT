import socket
import threading
from crypto import load_key, decrypt, encrypt

# Server Configuration
HOST = '0.0.0.0'  # Listen on all available interfaces
PORT = 65432

# Global Variables
clients = []
key = load_key()

def broadcast(message, _client_socket):
    """
    Broadcasts a message to all clients except the sender.
    """
    for client_socket in clients:
        if client_socket != _client_socket:
            try:
                # Encrypt the message before sending
                encrypted_message = encrypt(message, key)
                client_socket.send(encrypted_message)
            except:
                # Remove the client if unable to send a message
                clients.remove(client_socket)

def handle_client(client_socket):
    """
    Handles a single client connection.
    """
    # Get and send client's username
    try:
        encrypted_username = client_socket.recv(1024)
        username = decrypt(encrypted_username, key)
        welcome_message = f"Welcome {username}! You are connected to the WuNa chat."
        client_socket.send(encrypt(welcome_message, key))
        broadcast(f"{username} has joined the chat!", client_socket)
    except Exception as e:
        print(f"Error receiving username: {e}")
        clients.remove(client_socket)
        client_socket.close()
        return

    while True:
        try:
            # Receive and decrypt the message
            encrypted_message = client_socket.recv(1024)
            if not encrypted_message:
                break
            message = decrypt(encrypted_message, key)

            # Prepend username to the message
            full_message = f"{username}: {message}"
            print(f"Received: {full_message}")

            # Broadcast the message to other clients
            broadcast(full_message, client_socket)

        except:
            # Remove the client from the list and close the connection
            clients.remove(client_socket)
            broadcast(f"{username} has left the chat.", client_socket)
            client_socket.close()
            break

def main():
    """
    Main function to start the server.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"[*] Listening as {HOST}:{PORT}")

    # Generate key if it doesn't exist
    try:
        load_key()
    except FileNotFoundError:
        from crypto import generate_key
        generate_key()
        print("Generated a new secret key.")

    while True:
        # Accept a new connection
        client_socket, addr = server_socket.accept()
        print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")

        # Add the new client to the list
        clients.append(client_socket)

        # Start a new thread to handle the client
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

if __name__ == "__main__":
    main()