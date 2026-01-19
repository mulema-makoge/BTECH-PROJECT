import json
import uuid
from datetime import datetime
import socket
import threading
import time
from crypto import verify_signature
from persistence import save_message, save_message_to_queue, load_and_clear_queue

DISCOVERY_PORT = 12345
BROADCAST_INTERVAL = 10

class Peer:
    def __init__(self, host, port, message_callback):
        self.host = host
        self.port = port
        self.message_callback = message_callback
        self.peers = set()
        self.seen_message_ids = set()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))

    def start(self):
        self.sock.listen()
        print(f"[*] Listening for TCP connections on {self.host}:{self.port}")
        listen_thread = threading.Thread(target=self._listen_for_tcp_connections)
        listen_thread.daemon = True
        listen_thread.start()

        discovery_thread = threading.Thread(target=self._start_discovery)
        discovery_thread.daemon = True
        discovery_thread.start()

    def _start_discovery(self):
        broadcast_thread = threading.Thread(target=self._broadcast_presence)
        broadcast_thread.daemon = True
        broadcast_thread.start()

        listen_thread = threading.Thread(target=self._listen_for_peers)
        listen_thread.daemon = True
        listen_thread.start()

    def _broadcast_presence(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.settimeout(0.2)
        message = f"{self.host}:{self.port}".encode('utf-8')
        while True:
            udp_socket.sendto(message, ('<broadcast>', DISCOVERY_PORT))
            time.sleep(BROADCAST_INTERVAL)

    def _listen_for_peers(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(('', DISCOVERY_PORT))
        print(f"[*] Listening for peer discovery broadcasts on port {DISCOVERY_PORT}")
        while True:
            data, addr = udp_socket.recvfrom(1024)
            peer_address = data.decode('utf-8')
            peer_host, peer_port = peer_address.split(':')
            peer_port = int(peer_port)

            # Avoid connecting to self
            if peer_host == self.host and peer_port == self.port:
                continue

            # This is a simple check to avoid reconnecting. A more robust
            # solution would involve checking against a set of known peer addresses.
            is_already_connected = False
            for p_socket in self.peers:
                try:
                    # This check is not perfect, as getpeername can fail
                    if p_socket.getpeername() == (peer_host, peer_port):
                        is_already_connected = True
                        break
                except OSError: # Can happen if the socket is not connected
                    continue

            if not is_already_connected:
                print(f"[*] Discovered peer: {peer_host}:{peer_port}")
                self.connect_to_peer(peer_host, peer_port)

    def _listen_for_tcp_connections(self):
        while True:
            conn, addr = self.sock.accept()
            print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")
            self.peers.add(conn)
            handle_thread = threading.Thread(target=self._handle_connection, args=(conn,))
            handle_thread.daemon = True
            handle_thread.start()

    def _handle_connection(self, conn):
        buffer = ""
        while True:
            try:
                data = conn.recv(4096)
                if not data:
                    break

                buffer += data.decode('utf-8')

                # Process all complete messages in the buffer
                while '\n' in buffer:
                    json_str, buffer = buffer.split('\n', 1)
                    if json_str:
                        try:
                            message = Message.from_json(json_str)

                            # --- Security Step 1: Verify Signature ---
                            is_valid = verify_signature(
                                public_key_pem=message.sender_pk,
                                signature=message.signature,
                                message=message.get_signed_data()
                            )

                            if not is_valid:
                                print(f"[!] Received message with invalid signature from {message.sender_pk[:20]}...")
                                continue

                            # --- Security Step 2: Decrypt Message (Placeholder) ---
                            # For now, we assume content is not encrypted.
                            # This is where decryption would happen.

                            # --- Duplicate check ---
                            if message.msg_id not in self.seen_message_ids:
                                self.seen_message_ids.add(message.msg_id)

                                # Pass to the application layer
                                self.message_callback(message)

                                # Relay to other peers
                                self.relay(message, conn)

                        except json.JSONDecodeError:
                            print(f"[!] Received malformed JSON: {json_str}")

            except ConnectionResetError:
                break
        print(f"[*] Connection closed.")
        self.peers.remove(conn)
        conn.close()

    def connect_to_peer(self, peer_host, peer_port):
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((peer_host, peer_port))
            self.peers.add(conn)
            print(f"[*] Connected to {peer_host}:{peer_port}")

            # --- Sync Offline Messages ---
            queued_messages = load_and_clear_queue()
            if queued_messages:
                print(f"[*] Syncing {len(queued_messages)} offline messages...")
                for msg in queued_messages:
                    self.broadcast(msg) # Re-broadcast queued messages

            handle_thread = threading.Thread(target=self._handle_connection, args=(conn,))
            handle_thread.daemon = True
            handle_thread.start()
            return True
        except ConnectionRefusedError:
            print(f"[!] Connection refused by {peer_host}:{peer_port}")
            return False

    def broadcast(self, message):
        """
        Sends a message object to all connected peers.
        If no peers are connected, it queues the message.
        """
        # Always save our own message to our history
        save_message(message)

        if not self.peers:
            print("[*] No peers connected. Queuing message.")
            save_message_to_queue(message)
            return

        self.seen_message_ids.add(message.msg_id)
        json_message = message.to_json() + '\n'
        for peer_socket in self.peers:
            try:
                peer_socket.sendall(json_message.encode('utf-8'))
            except Exception as e:
                print(f"[!] Error broadcasting to a peer: {e}")

    def relay(self, message, source_conn):
        """
        Relays a message to all peers except the original sender.
        """
        json_message = message.to_json() + '\n'
        for peer_socket in self.peers:
            if peer_socket != source_conn:
                try:
                    peer_socket.sendall(json_message.encode('utf-8'))
                except Exception as e:
                    print(f"[!] Error relaying message: {e}")


class Message:
    def __init__(self, sender_pk, content, signature=None, msg_id=None, timestamp=None):
        self.msg_id = msg_id if msg_id else str(uuid.uuid4())
        self.sender_pk = sender_pk
        self.timestamp = timestamp if timestamp else datetime.utcnow().isoformat()
        self.content = content
        self.signature = signature

    def get_signed_data(self):
        """
        Returns a consistent, signable representation of the message.
        """
        return f"{self.msg_id}{self.sender_pk}{self.timestamp}{self.content}"

    def to_json(self):
        return json.dumps({
            "msg_id": self.msg_id,
            "sender_pk": self.sender_pk,
            "timestamp": self.timestamp,
            "content": self.content,
            "signature": self.signature
        })

    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        return Message(
            sender_pk=data["sender_pk"],
            content=data["content"],
            signature=data["signature"],
            msg_id=data["msg_id"],
            timestamp=data["timestamp"]
        )
