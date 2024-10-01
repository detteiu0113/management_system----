import secrets
import string

def generate_strong_password(length=16):
    alphabet = string.ascii_letters + string.digits
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        if (any(c.islower() for c in password) and
            any(c.isupper() for c in password) and
            any(c.isdigit() for c in password)):
            break
    return password

# 16文字の強力なパスワードを生成する例
strong_password = generate_strong_password(16)
print(strong_password)
