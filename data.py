import getpass

# Prompts the user and stores the hidden input in 'pswd'
pswd = getpass.getpass('Enter your password: ')

print("Password received!")
import string

# Generate a 12-character secure random password
# Write your code here :-)
import secrets
alphabet = string.ascii_letters + string.digits + string.punctuation
new_password = ''.join(secrets.choice(alphabet) for i in range(12))

print(f"Generated password: {new_password}")
import keyring

# Get password for 'my_app' from the system keychain
password = keyring.get_password("my_app", "username")
