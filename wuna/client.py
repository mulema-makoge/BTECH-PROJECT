import socket
import threading
from crypto import load_key, encrypt, decrypt

# Client Configuration
HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server
key = load_key()

def receive_messages(client_socket):
    """
    Receives messages from the server.
    """
    while True:
        try:
            # Receive and decrypt the message
            encrypted_message = client_socket.recv(1024)
            if not encrypted_message:
                break
            message = decrypt(encrypted_message, key)
            print(message)
        except Exception as e:
            print(f"An error occurred: {e}")
            client_socket.close()
            break

def main():
    """
    Main function to start the client.
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    # Get username and send it to the server
    username = input("Enter your username: ")
    encrypted_username = encrypt(username, key)
    client_socket.send(encrypted_username)

    # Start a thread to receive messages
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.daemon = True  # Thread will die when main thread dies
    receive_thread.start()

    # Main loop to send messages
    while True:
        message = input()
        if message.lower() == 'exit':
            break
        encrypted_message = encrypt(message, key)
        client_socket.send(encrypted_message)

    client_socket.close()

if __name__ == "__main__":
    main()