import argparse
import threading
import time
from network import Peer, Message
from crypto import load_or_generate_keys, get_public_key_pem, sign_message, load_or_generate_symmetric_key, encrypt_message_content, decrypt_message_content
from persistence import initialize_db, save_message, load_all_messages

class ChatApp:
    def __init__(self, host, port):
        self.private_key, self.public_key = load_or_generate_keys()
        self.public_key_pem = get_public_key_pem(self.public_key)
        self.symmetric_key = load_or_generate_symmetric_key()
        self.peer = Peer(host, port, self.handle_incoming_message)

        initialize_db()
        self._load_and_display_history()

    def start(self):
        self.peer.start()
        print("Welcome to the Secure Mesh Chat!")
        print("Type your messages and press Enter to send.")
        print("-------------------------------------------")

        # Start input thread
        input_thread = threading.Thread(target=self._handle_user_input)
        input_thread.daemon = True
        input_thread.start()

        # Keep main thread alive
        while True:
            time.sleep(1)

    def _load_and_display_history(self):
        messages = load_all_messages()
        print("--- Chat History ---")
        for msg in messages:
            self.display_message(msg)
        print("--------------------")

    def handle_incoming_message(self, message):
        # Decrypt content before saving or displaying
        try:
            decrypted_content = decrypt_message_content(self.symmetric_key, message.content)
            message.content = decrypted_content # Replace ciphertext with plaintext
        except Exception as e:
            print(f"\n[!] Failed to decrypt message from {message.sender_pk.splitlines()[1][:10]}...: {e}")
            return

        was_new = save_message(message)
        if was_new:
            self.display_message(message)

    def _handle_user_input(self):
        while True:
            try:
                content = input("> ")
                if content:
                    # Encrypt the content
                    encrypted_content = encrypt_message_content(self.symmetric_key, content)

                    # Create the message with encrypted content
                    message = Message(sender_pk=self.public_key_pem, content=encrypted_content)

                    # Sign the message (note: content is signed as ciphertext)
                    signature = sign_message(self.private_key, message.get_signed_data())
                    message.signature = signature

                    # Broadcast the message
                    self.peer.broadcast(message)
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break

    def display_message(self, message):
        # Using the first 10 chars of the public key as a short identifier
        sender_short_id = message.sender_pk.splitlines()[1][:10]
        # The content is already decrypted at this point
        print(f"\n[{message.timestamp}] {sender_short_id}...: {message.content}")

def main():
    parser = argparse.ArgumentParser(description="Secure Mesh Chat")
    parser.add_argument('--host', default='0.0.0.0', help="Host to bind to.")
    parser.add_argument('--port', type=int, default=8000, help="Port to listen on.")
    args = parser.parse_args()

    app = ChatApp(host=args.host, port=args.port)
    app.start()

if __name__ == "__main__":
    main()
