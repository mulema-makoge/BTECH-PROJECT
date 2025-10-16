import socket
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext
import json
from crypto import load_key, encrypt, decrypt

# Client Configuration
HOST = '127.0.0.1'
PORT = 65432
key = load_key()

class ChatClient:
    def __init__(self, master):
        self.master = master
        master.title("WuNa Encrypted Chat")

        self.username = simpledialog.askstring("Username", "Please enter your username", parent=master)
        if not self.username:
            master.destroy()
            return

        self.chat_box = scrolledtext.ScrolledText(master, state='disabled', wrap='word')
        self.chat_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.msg_entry = tk.Entry(master)
        self.msg_entry.pack(padx=10, pady=(0, 10), fill=tk.X, expand=True)
        self.msg_entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(master, text="Send", command=self.send_message)
        self.send_button.pack(padx=10, pady=(0, 10))

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((HOST, PORT))
        except ConnectionRefusedError:
            self.display_message("System", "Error: Connection refused. Is the server running?")
            self.master.after(3000, self.master.destroy)
            return

        encrypted_username = encrypt(self.username, key)
        self.client_socket.send(encrypted_username)

        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def receive_messages(self):
        while True:
            try:
                encrypted_message = self.client_socket.recv(1024)
                if not encrypted_message:
                    self.display_message("System", "Server has closed the connection.")
                    break

                message_data = json.loads(decrypt(encrypted_message, key))
                sender = message_data.get("sender", "Anonymous")
                content = message_data.get("content", "")
                timestamp = message_data.get("timestamp", "")

                display_content = f"[{timestamp}] {sender}: {content}"
                if message_data.get("recipient"):
                    display_content = f"(Private) {display_content}"

                self.display_message(sender, display_content)

            except Exception as e:
                self.display_message("System", f"An error occurred: {e}")
                self.client_socket.close()
                break

    def send_message(self, event=None):
        message_text = self.msg_entry.get()
        if message_text:
            recipient = None
            content = message_text

            if message_text.startswith("/msg"):
                parts = message_text.split(" ", 2)
                if len(parts) == 3:
                    recipient = parts[1]
                    content = parts[2]

            message_data = {"content": content, "recipient": recipient}
            encrypted_message = encrypt(json.dumps(message_data), key)
            self.client_socket.send(encrypted_message)

            if recipient:
                self.display_message(self.username, f"(Private to {recipient}) [{self.get_current_time()}] {self.username}: {content}")

            self.msg_entry.delete(0, tk.END)

    def display_message(self, sender, message):
        self.chat_box.config(state='normal')
        self.chat_box.insert(tk.END, message + '\n')
        self.chat_box.config(state='disabled')
        self.chat_box.yview(tk.END)

    def get_current_time(self):
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def on_closing(self):
        self.client_socket.close()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)

    if hasattr(client, 'username') and client.username:
        root.mainloop()