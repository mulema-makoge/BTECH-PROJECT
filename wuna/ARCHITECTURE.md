# WuNa v2 - Software Architecture Document

## 1. Introduction

This document outlines the software architecture for WuNa v2, a secure, decentralized, peer-to-peer (P2P) mesh messaging system. The primary goal of this architecture is to provide a resilient, serverless communication platform that supports offline collaboration and is secured with modern cryptographic principles. The architectural style is a **layered, peer-to-peer network**.

## 2. Architectural Goals

The architecture is designed to meet the following key requirements:

-   **Decentralization:** The system must operate without a central server or single point of failure. All peers in the network are equal.
-   **Security:** Communication must be secure, ensuring message authenticity and integrity. Peer identity must be verifiable.
-   **Resilience:** The network must be self-forming and self-healing, capable of routing messages even if some peers are offline.
-   **Offline-First:** The system must support asynchronous communication, allowing users to send messages while offline and have them synchronized upon reconnection.

## 3. System Components (Logical View)

The application is divided into four primary logical modules. Each module has a distinct responsibility, promoting a clean separation of concerns.

```
+-------------------------------------------------------------+
|                     Application Layer                       |
|                          (app.py)                           |
|      (Handles User Input, Manages Application Lifecycle)      |
+----------------------+--------------------------------------+
                       |
                       v
+----------------------+--------------------------------------+
|                    Networking Layer                         |
|                       (network.py)                          |
| (Peer Discovery, TCP Comms, Message Flooding, P2P Logic)    |
+----------------------+--------------------------------------+
                       |
                       v
+----------------------+--------------------------------------+
|   Cryptography Layer |         Persistence Layer            |
|     (crypto.py)      |        (persistence.py)            |
| (Keys, Signatures)   |     (SQLite DB, Offline Queue)       |
+----------------------+--------------------------------------+
```

### 3.1. Application Layer (`app.py`)

-   **Responsibility:** This is the user-facing layer that serves as the main entry point of the application.
-   **Key Functions:**
    -   Handles command-line argument parsing.
    -   Initializes and orchestrates the other layers.
    -   Manages the main application loop and user input (CLI).
    -   Formats and displays incoming messages to the user.

### 3.2. Networking Layer (`network.py`)

-   **Responsibility:** This layer manages all peer-to-peer networking logic.
-   **Key Functions:**
    -   **Peer Discovery:** Implements UDP broadcasting to find other peers on the LAN.
    -   **TCP Connection Management:** Listens for and establishes persistent TCP connections with peers.
    -   **Message Propagation:** Implements the controlled flooding algorithm for relaying messages throughout the mesh.
    -   **Offline Sync Logic:** Coordinates with the persistence layer to send queued messages upon reconnection.

### 3.3. Cryptography Layer (`crypto.py`)

-   **Responsibility:** This layer handles all cryptographic operations, providing the security foundation for the system.
-   **Key Functions:**
    -   **Asymmetric Key Management:** Generates, loads, and saves persistent RSA key pairs that define a peer's identity.
    -   **Digital Signatures:** Provides functions to sign outgoing messages and verify the signatures of incoming messages, ensuring authenticity and integrity.
    -   **Symmetric Encryption:** Provides functions to manage a pre-shared symmetric (Fernet) key and to encrypt and decrypt message content for confidentiality.

### 3.4. Persistence Layer (`persistence.py`)

-   **Responsibility:** This layer manages the storage and retrieval of all persistent data.
-   **Key Functions:**
    -   **Database Initialization:** Sets up the SQLite database and the required tables.
    -   **Chat History:** Stores and retrieves all validated messages from the `messages` table.
    -   **Offline Queue:** Manages the `outgoing_queue` table for storing messages that are sent while the peer is disconnected.

## 4. Data Model

### 4.1. Message Structure

The `Message` class is the core data structure for all communication. It is serialized to JSON for transit over the network.

-   `msg_id` (UUID): A unique identifier to prevent duplicate processing.
-   `sender_pk` (String): The PEM-encoded public key of the sender, used for identity and signature verification.
-   `timestamp` (ISO 8601 String): The UTC timestamp of when the message was created.
-   `content` (String): The user-visible content of the message.
-   `signature` (Base64 String): The digital signature of the message, created by signing the concatenated `msg_id`, `sender_pk`, `timestamp`, and `content`.

### 4.2. Database Schema

The SQLite database (`chat_history.db`) contains two tables:

1.  **`messages`**: Stores the permanent chat history.
    -   `msg_id` (TEXT, PRIMARY KEY)
    -   `sender_pk` (TEXT)
    -   `timestamp` (TEXT)
    -   `content` (TEXT)
    -   `signature` (TEXT)
2.  **`outgoing_queue`**: Stores messages sent while offline. Has the same schema as the `messages` table.

## 5. Deployment View

WuNa v2 is deployed as a series of identical, standalone peer applications.

-   **Process:** Each instance of the application is a single OS process. Within this process, multiple threads are used to handle concurrent operations (e.g., listening for TCP connections, UDP discovery, user input).
-   **Network:** All peers are expected to be on the same local area network (LAN) for UDP broadcast discovery to function.
-   **State:** Each peer maintains its own state locally, including its unique RSA keys and its chat database. There is no shared state or central coordination.
