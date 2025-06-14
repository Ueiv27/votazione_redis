import redis
import bcrypt
from config_redis import username, password, host, port
from utils import get_user_id, key_user_password

red = redis.Redis(
    host=host,
    port=port,
    db=0,
    username=username,
    password=password,
    decode_responses=True
)

def registra_utente():
    user_id = get_user_id()
    if red.exists(key_user_password(user_id)):
        print("Utente già registrato.")
        return None

    while True:
        user_password = input("Crea una password: ").strip()
        if len(user_password) < 4:
            print("La password deve contenere almeno 4 caratteri.")
        else:
            break

    hashed_pw = bcrypt.hashpw(user_password.encode('utf-8'), bcrypt.gensalt())
    red.set(key_user_password(user_id), hashed_pw.decode('utf-8'))
    print("Registrazione completata con successo!")
    return user_id

def login_utente():
    user_id = get_user_id()
    hashed_pw = red.get(key_user_password(user_id))

    if not hashed_pw:
        print("Utente non registrato.")
        return None

    user_password = input("Inserisci la tua password: ").strip()
    if bcrypt.checkpw(user_password.encode('utf-8'), hashed_pw.encode('utf-8')):
        print("Accesso effettuato con successo!")
        return user_id
    else:
        print("Password errata.")
        return None