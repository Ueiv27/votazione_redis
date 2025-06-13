import redis as r
import sys
import bcrypt
from config_redis import username, password, host, port

try:
    red = r.Redis(
        host=host,
        port=port,
        db=0,
        username=username,
        password=password,
        decode_responses=True
    )
    red.ping()
    print("Connessione a Redis riuscita!")
except r.exceptions.ConnectionError as e:
    print(f"Errore di connessione a Redis: {e}")
    sys.exit(1)

MAX_VOTI = 3

# --- CHIAVI REDIS ---
KEY_PROPOSAL_COUNTER = "proposals:id_counter"
KEY_PROPOSALS_HASH = "proposals"
KEY_USER_VOTES_HASH = "user:votes"
KEY_LEADERBOARD_ZSET = "leaderboard"
KEY_USER_PASSWORDS_HASH = "user:passwords"

def key_proposal_votes_set(proposal_id):
    return f"proposal:votes:{proposal_id}"

def get_user_id():
    corso = input("Che corso frequenti? (BD, ML) ")
    while True:
        numero = input("Qual è il tuo numero dell'elenco? ")
        if numero.isdigit() and 1 <= int(numero) <= 30:
            break
        print("Le classi sono composte da massimo 30 persone, inserisci un numero valido. ")
    return f"{corso.strip().lower()}:{numero.strip()}"

def registra_utente():
    user_id = get_user_id()
    if red.hexists(KEY_USER_PASSWORDS_HASH, user_id):
        print("Utente già registrato.")
        return None

    while True:
        user_password = input("Crea una password: ").strip()
        if len(user_password) < 4:
            print("La password deve contenere almeno 4 caratteri.")
        else:
            break

    hashed_pw = bcrypt.hashpw(user_password.encode('utf-8'), bcrypt.gensalt())
    red.hset(KEY_USER_PASSWORDS_HASH, user_id, hashed_pw.decode('utf-8'))
    print("Registrazione completata con successo!")
    return user_id

def login_utente():
    user_id = get_user_id()
    hashed_pw = red.hget(KEY_USER_PASSWORDS_HASH, user_id)

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

def menu():
    print("\n--- Menu ---")
    print("1. Votare una proposta")
    print("2. Inserire una nuova proposta")
    print("3. Vedere la classifica delle proposte")
    print("4. Analizzare i voti di un corso")
    print("e. Esci")
    return input("Scegli un'opzione: ").strip().lower()

def elenco_proposte():
    proposte = red.hgetall(KEY_PROPOSALS_HASH)
    if not proposte:
        print("Nessuna proposta disponibile al momento.")
        return None
    print("\nElenco proposte:")
    for k in sorted(proposte.keys(), key=int):
        print(f"{k}. {proposte[k]}")
    return proposte

def vota_proposta(user_id):
    proposte = elenco_proposte()
    if not proposte:
        return

    scelta_id = input("Inserisci il numero della proposta da votare: ")
    if scelta_id not in proposte:
        print("Errore: Proposta non valida.")
        return

    voti_utente = red.hget(KEY_USER_VOTES_HASH, user_id)
    if voti_utente and int(voti_utente) >= MAX_VOTI:
        print(f"Hai già raggiunto il limite massimo di {MAX_VOTI} voti.")
        return

    key_voti_set = key_proposal_votes_set(scelta_id)
    if red.sismember(key_voti_set, user_id):
        print("Hai già votato questa proposta.")
        return

    pipe = red.pipeline()
    pipe.sadd(key_voti_set, user_id)
    pipe.hincrby(KEY_USER_VOTES_HASH, user_id, 1)
    pipe.zincrby(KEY_LEADERBOARD_ZSET, 1, scelta_id)
    pipe.execute()
    print(f"Voto per '{proposte[scelta_id]}' registrato con successo!")

def proponi_proposta():
    testo = input("Inserisci il testo della nuova proposta: ")
    if not testo.strip():
        print("Errore: La proposta non può essere vuota.")
        return

    next_id = red.incr(KEY_PROPOSAL_COUNTER)
    pipe = red.pipeline()
    pipe.hset(KEY_PROPOSALS_HASH, next_id, testo)
    pipe.zadd(KEY_LEADERBOARD_ZSET, {next_id: 0})
    pipe.execute()
    print(f"Proposta '{testo}' aggiunta con l'ID {next_id}.")

def classifica():
    print("\n--- Classifica delle Proposte ---")
    classifica_ids = red.zrevrange(KEY_LEADERBOARD_ZSET, 0, -1, withscores=True)
    if not classifica_ids:
        print("Nessuna proposta in classifica.")
        return

    proposal_ids = [item[0] for item in classifica_ids]
    proposal_names = red.hmget(KEY_PROPOSALS_HASH, proposal_ids)

    for i, (proposal_id, score) in enumerate(classifica_ids, 1):
        nome = proposal_names[i-1]
        voti = int(score)
        print(f"{i}. {nome} - {voti} voti")

def conta_voti_per_corso(nome_corso):
    print(f"\n--- Analisi Voti per il Corso '{nome_corso}' ---")
    utenti_e_voti = red.hgetall(KEY_USER_VOTES_HASH)
    if not utenti_e_voti:
        print("Nessun voto è stato ancora registrato.")
        return

    voti_totali_corso = 0
    utenti_del_corso_votanti = 0
    prefisso_corso = f"{nome_corso.strip().lower()}:"

    for user_id, num_voti in utenti_e_voti.items():
        if user_id.startswith(prefisso_corso):
            voti_totali_corso += int(num_voti)
            utenti_del_corso_votanti += 1

    if utenti_del_corso_votanti > 0:
        print(f"Trovati {utenti_del_corso_votanti} studenti votanti per questo corso.")
        print(f"Hanno espresso un totale di {voti_totali_corso} voti.")
    else:
        print(f"Nessuno studente del corso '{nome_corso}' ha ancora votato.")

def main():
    print("Benvenuto nel sistema di votazione NoSQL!")
    while True:
        print("\n1. Login")
        print("2. Registrati")
        print("e. Esci")
        scelta = input("Scegli un'opzione: ").strip().lower()

        if scelta == "1":
            user_id = login_utente()
            if user_id:
                break
        elif scelta == "2":
            user_id = registra_utente()
            if user_id:
                break
        elif scelta == "e":
            print("Arrivederci!")
            sys.exit(0)
        else:
            print("Scelta non valida, riprova.")

    print(f"\nCiao {user_id}!")
    while True:
        scelta = menu()
        if scelta == "1":
            vota_proposta(user_id)
        elif scelta == "2":
            proponi_proposta()
        elif scelta == "3":
            classifica()
        elif scelta == "4":
            corso_da_cercare = input("Di quale corso vuoi analizzare i voti? ")
            if corso_da_cercare.strip():
                conta_voti_per_corso(corso_da_cercare)
            else:
                print("Errore: Devi inserire un nome per il corso.")
        elif scelta == "e":
            print("Arrivederci!")
            sys.exit(0)
        else:
            print("Scelta non valida, riprova.")

if __name__ == "__main__":
    main()
