import redis
import bcrypt
from config_redis import username, password, host, port

KEY_USER_VOTES_HASH = "user:votes"
KEY_USER_PASSWORDS_HASH = "user:passwords"

# Connessione
red = redis.Redis(
    host=host,
    port=port,
    db=0,
    username=username,
    password=password,
    decode_responses=True
)

# Password comune
plain_pw = "1234"
hashed_pw = bcrypt.hashpw(plain_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Recupera gli utenti esistenti (che hanno votato)
utenti = red.hkeys(KEY_USER_VOTES_HASH)

for user_id in utenti:
    if not red.hexists(KEY_USER_PASSWORDS_HASH, user_id):
        red.hset(KEY_USER_PASSWORDS_HASH, user_id, hashed_pw)
        print(f"Inserita password per {user_id}")
    else:
        print(f"{user_id} ha già una password")

print("Popolamento password completato.")
