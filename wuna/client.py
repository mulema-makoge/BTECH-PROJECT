import socket
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext
from crypto import load_key, encrypt, decrypt

# Client Configuration
HOST = '127.0.0.1'
PORT = 65432
key = load_key()

class ChatClient:
    def __init__(self, master):
        self.master = master
        master.title("WuNa Encrypted Chat")

        # Get username
        self.username = simpledialog.askstring("Username", "Please enter your username", parent=master)
        if not self.username:
            master.destroy()
            return

        # UI Elements
        self.chat_box = scrolledtext.ScrolledText(master, state='disabled', wrap='word')
        self.chat_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.msg_entry = tk.Entry(master)
        self.msg_entry.pack(padx=10, pady=(0, 10), fill=tk.X, expand=True)
        self.msg_entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(master, text="Send", command=self.send_message)
        self.send_button.pack(padx=10, pady=(0, 10))

        # Socket setup
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((HOST, PORT))
        except ConnectionRefusedError:
            self.display_message("Error: Connection refused. Is the server running?")
            self.master.after(3000, self.master.destroy)
            return

        # Send username to server
        encrypted_username = encrypt(self.username, key)
        self.client_socket.send(encrypted_username)

        # Start a thread to receive messages
        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def receive_messages(self):
        while True:
            try:
                encrypted_message = self.client_socket.recv(1024)
                if not encrypted_message:
                    self.display_message("Server has closed the connection.")
                    break
                message = decrypt(encrypted_message, key)
                self.display_message(message)
            except Exception as e:
                self.display_message(f"An error occurred: {e}")
                self.client_socket.close()
                break

    def send_message(self, event=None):
        message = self.msg_entry.get()
        if message:
            encrypted_message = encrypt(message, key)
            self.client_socket.send(encrypted_message)
            self.msg_entry.delete(0, tk.END)

    def display_message(self, message):
        self.chat_box.config(state='normal')
        self.chat_box.insert(tk.END, message + '\n')
        self.chat_box.config(state='disabled')
        self.chat_box.yview(tk.END)

    def on_closing(self):
        self.client_socket.close()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)

    # Only start the main loop if the client was initialized properly
    if hasattr(client, 'username') and client.username:
        root.mainloop()