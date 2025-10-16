from cryptography.fernet import Fernet

KEY_FILE = "secret.key"

def generate_key():
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)

def load_key():
    """
    Loads the key from the current directory named `secret.key`
    """
    return open(KEY_FILE, "rb").read()

def encrypt(message, key):
    """
    Encrypts a message
    """
    f = Fernet(key)
    encrypted_message = f.encrypt(message.encode())
    return encrypted_message

def decrypt(encrypted_message, key):
    """
    Decrypts an encrypted message
    """
    f = Fernet(key)
    decrypted_message = f.decrypt(encrypted_message)
    return decrypted_message.decode()

if __name__ == "__main__":
    # Generate a key if one doesn't exist
    try:
        load_key()
    except FileNotFoundError:
        generate_key()

    key = load_key()
    message = "This is a secret message"
    encrypted = encrypt(message, key)
    decrypted = decrypt(encrypted, key)

    print(f"Original message: {message}")
    print(f"Encrypted message: {encrypted}")
    print(f"Decrypted message: {decrypted}")