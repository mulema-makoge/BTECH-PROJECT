from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet

KEY_DIR = "keys"
PRIVATE_KEY_FILE = f"{KEY_DIR}/private_key.pem"
PUBLIC_KEY_FILE = f"{KEY_DIR}/public_key.pem"
SYMMETRIC_KEY_FILE = f"{KEY_DIR}/session.key"

def generate_keys():
    """
    Generates a new RSA public/private key pair and saves them to files.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    # Serialize private key
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize public key
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    import os
    os.makedirs(KEY_DIR, exist_ok=True)

    with open(PRIVATE_KEY_FILE, 'wb') as f:
        f.write(pem_private)

    with open(PUBLIC_KEY_FILE, 'wb') as f:
        f.write(pem_public)

    return private_key, public_key

def load_or_generate_keys():
    """
    Loads existing keys or generates new ones if they don't exist.
    """
    try:
        with open(PRIVATE_KEY_FILE, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
            )
        with open(PUBLIC_KEY_FILE, 'rb') as f:
            public_key = serialization.load_pem_public_key(
                f.read(),
            )
        print("[*] Loaded existing RSA keys.")
        return private_key, public_key
    except FileNotFoundError:
        print("[*] No existing keys found. Generating new keys...")
        return generate_keys()

def get_public_key_pem(public_key):
    """
    Returns the PEM-encoded string of a public key object.
    """
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

def sign_message(private_key, message):
    """
    Signs a message with the given private key.
    Message should be a string.
    Returns the signature in base64 format.
    """
    import base64
    signature = private_key.sign(
        message.encode('utf-8'),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')

def verify_signature(public_key_pem, signature, message):
    """
    Verifies the signature of a message using the sender's public key.
    Returns True if the signature is valid, False otherwise.
    """
    import base64
    try:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
        )
        signature_bytes = base64.b64decode(signature)
        public_key.verify(
            signature_bytes,
            message.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except (InvalidSignature, ValueError):
        return False

# --- Symmetric Encryption ---

def load_or_generate_symmetric_key():
    """
    Loads the symmetric key from file, or generates a new one.
    """
    try:
        with open(SYMMETRIC_KEY_FILE, 'rb') as f:
            key = f.read()
        print("[*] Loaded existing session key.")
        return key
    except FileNotFoundError:
        print("[*] No session key found. Generating a new one...")
        key = Fernet.generate_key()
        with open(SYMMETRIC_KEY_FILE, 'wb') as f:
            f.write(key)
        return key

def encrypt_message_content(symmetric_key, content):
    """
    Encrypts message content using the symmetric key.
    Content should be a string.
    Returns the ciphertext as a base64-encoded string.
    """
    f = Fernet(symmetric_key)
    encrypted_content = f.encrypt(content.encode('utf-8'))
    return encrypted_content.decode('utf-8')

def decrypt_message_content(symmetric_key, encrypted_content):
    """
    Decrypts message content using the symmetric key.
    Encrypted_content should be a base64-encoded string.
    Returns the decrypted plaintext as a string.
    """
    f = Fernet(symmetric_key)
    decrypted_content = f.decrypt(encrypted_content.encode('utf-8'))
    return decrypted_content.decode('utf-8')
