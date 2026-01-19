# WuNa v2 - Secure Mesh-Based Local Messaging

WuNa v2 is a secure, decentralized, and resilient local messaging system designed for peer-to-peer communication. It operates as a mesh network, meaning there is no central server, and messages are relayed through the network of peers. This makes it highly resilient and suitable for offline collaboration, disaster recovery scenarios, or any environment where a central server is not practical.

## Key Features

-   **Decentralized Mesh Network:** No single point of failure. The network is formed dynamically by peers discovering each other on the local network.
-   **Strong Security:**
    -   **Peer Identity:** Each peer has a unique, verifiable identity based on a persistent RSA public/private key pair.
    -   **Authentication & Integrity:** Every message is digitally signed with the sender's private key and verified by receiving peers, ensuring that messages are authentic and have not been tampered with.
    -   **Confidentiality:** Message content is protected with end-to-end encryption using Fernet (AES-128 in CBC mode with a 128-bit HMAC-SHA256 for integrity), ensuring that only the communicating peers can read the messages.
-   **Offline Collaboration:**
    -   **Message Persistence:** All validated messages are stored in a local database, providing a persistent chat history.
    -   **Offline Queuing:** If you send a message while disconnected, it is securely queued.
    -   **Automatic Synchronization:** Queued messages are automatically broadcast to the network as soon as you reconnect to a peer.
-   **Automatic Peer Discovery:** Peers automatically discover each other on the local network using UDP broadcasting, making setup effortless.

## How It Works

### 1. Peer Identity
On the first run, the application generates a 2048-bit RSA key pair for the peer, which is stored in the `keys/` directory. This key pair serves as the peer's permanent identity.

### 2. Peer Discovery
The application uses UDP broadcasts on port `12345` to find other peers on the local network. One thread periodically sends out a "presence" packet, and another listens for these packets. When a new peer is discovered, a TCP connection is established.

### 3. Message Propagation (Flooding)
When a peer sends or receives a message, it relays it to all of its connected peers. To prevent infinite loops and redundant transmissions, each peer keeps track of the unique IDs of the messages it has recently seen and will not re-process or re-relay duplicates.

### 4. Security
Every message is signed using the sender's private RSA key. When a peer receives a message, it uses the sender's public key (which is included in the message) to verify the signature. If the signature is invalid, the message is discarded. This guarantees that messages are from who they claim to be and have not been altered.

## How to Use

### 1. Prerequisites
-   Python 3.7+
-   `pip` for installing dependencies.

### 2. Installation
First, clone the repository:
```bash
git clone <repository-url>
cd wuna
```

Next, install the required Python libraries. The only external dependency is `cryptography`.
```bash
pip install cryptography
```

### 3. Running the Application
You can run the application with default settings, or specify a host and port.

**To run with defaults (0.0.0.0:8000):**
```bash
python app.py
```

**To run on a specific host and port:**
```bash
python app.py --host 192.168.1.10 --port 9000
```

On the first launch, a `keys/` directory will be created containing your peer's unique identity and a `session.key` for encryption. A `chat_history.db` file will also be created to store your messages.

**Important:** For other users on the network to decrypt your messages, they must have the **exact same `session.key` file** in their `keys/` directory. After one user runs the application for the first time, you must securely copy the `keys/session.key` file from their computer to all other users' computers before they launch the application.

Now, simply type your messages and press Enter. The application will handle the rest, from discovering peers to securely propagating your messages.
