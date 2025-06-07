import redis as r
import sys

# --- CONFIGURAZIONE ---
# Inserisci qui le tue credenziali
username = "default"
password = "O9uv1t8Sxp93vkDYnnHX6NOhN953ZlZw"
host = 'redis-15081.crce198.eu-central-1-3.ec2.redns.redis-cloud.com'
port = 15081

try:
    red = r.Redis(
        host=host,
        port=port,
        db=0,
        username=username,
        password=password,
        decode_responses=True # Decodifica automaticamente le risposte da bytes a stringhe
    )
    red.ping() # Controlla la connessione all'avvio
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

def key_proposal_votes_set(proposal_id):
    """Genera la chiave per il set di voti di una proposta."""
    return f"proposal:votes:{proposal_id}"

# --- FUNZIONI PRINCIPALI ---

def get_user_id():
    corso = input("Che corso frequenti? ")
    numero = input("Qual è il tuo numero dell'elenco? ")
    return f"{corso.strip().lower()}:{numero.strip()}"

def menu():
    print("\n--- Menu ---")
    print("1. Votare una proposta")
    print("2. Inserire una nuova proposta")
    print("3. Vedere la classifica delle proposte")
    print("e. Esci")
    return input("Scegli un'opzione: ").strip().lower()

def elenco_proposte():
    proposte = red.hgetall(KEY_PROPOSALS_HASH)
    if not proposte:
        print("Nessuna proposta disponibile al momento.")
        return None
    print("\nElenco proposte:")
    # Ordiniamo per ID numerico
    for k in sorted(proposte.keys(), key=int):
        print(f"{k}. {proposte[k]}")
    return proposte

def vota_proposta(user_id):
    proposte = elenco_proposte()
    if not proposte:
        return

    try:
        scelta_id = input("Inserisci il numero della proposta da votare: ")
        if scelta_id not in proposte:
            print("Errore: Proposta non valida.")
            return
    except ValueError:
        print("Errore: Inserisci un numero valido.")
        return
    
    # OTTIMIZZAZIONE 1: Controllo del limite voti utente (1 chiamata a Redis)
    voti_utente = red.hget(KEY_USER_VOTES_HASH, user_id)
    if voti_utente and int(voti_utente) >= MAX_VOTI:
        print(f"Hai già raggiunto il limite massimo di {MAX_VOTI} voti.")
        return

    # Controllo voto doppio sulla stessa proposta
    key_voti_set = key_proposal_votes_set(scelta_id)
    if red.sismember(key_voti_set, user_id):
        print("Hai già votato questa proposta.")
        return

    # Eseguiamo le operazioni di voto in una pipeline per garantirne l'atomicità
    # (se un comando fallisce, non vengono eseguiti gli altri)
    pipe = red.pipeline()
    pipe.sadd(key_voti_set, user_id) # Aggiunge l'utente al set dei votanti della proposta
    pipe.hincrby(KEY_USER_VOTES_HASH, user_id, 1) # OTTIMIZZAZIONE 1: Incrementa il contatore dei voti dell'utente
    pipe.zincrby(KEY_LEADERBOARD_ZSET, 1, scelta_id) # OTTIMIZZAZIONE 3: Incrementa il punteggio nella classifica
    pipe.execute()
    
    print(f"Voto per '{proposte[scelta_id]}' registrato con successo!")

def proponi_proposta():
    testo = input("Inserisci il testo della nuova proposta: ")
    if not testo.strip():
        print("Errore: La proposta non può essere vuota.")
        return

    # OTTIMIZZAZIONE 2: ID atomico e a prova di race condition (1 chiamata a Redis)
    next_id = red.incr(KEY_PROPOSAL_COUNTER)
    
    # Usiamo una pipeline per assicurare che entrambe le operazioni abbiano successo
    pipe = red.pipeline()
    pipe.hset(KEY_PROPOSALS_HASH, next_id, testo)
    # Inizializza la proposta nella classifica con 0 voti per mostrarla subito
    pipe.zadd(KEY_LEADERBOARD_ZSET, {next_id: 0}) 
    pipe.execute()

    print(f"Proposta '{testo}' aggiunta con l'ID {next_id}.")

def classifica():
    print("\n--- Classifica delle Proposte ---")
    
    # OTTIMIZZAZIONE 3: Recupera la classifica direttamente da Redis (1 chiamata)
    # ZREVRANGE restituisce gli elementi dal punteggio più alto al più basso
    classifica_ids = red.zrevrange(KEY_LEADERBOARD_ZSET, 0, -1, withscores=True)

    if not classifica_ids:
        print("Nessuna proposta in classifica.")
        return

    # Recupera i nomi di tutte le proposte necessarie con un unico comando (HMGET)
    # per evitare chiamate multiple nel ciclo
    proposal_ids = [item[0] for item in classifica_ids]
    proposal_names = red.hmget(KEY_PROPOSALS_HASH, proposal_ids)
    
    for i, (proposal_id, score) in enumerate(classifica_ids, 1):
        # Il nome corrisponde all'indice, dato che abbiamo richiesto gli ID nello stesso ordine
        nome = proposal_names[i-1]
        voti = int(score)
        print(f"{i}. {nome} - {voti} voti")

def main():
    print("Benvenuto nel sistema di votazione NoSQL!")
    user_id = get_user_id()
    print(f"\nCiao {user_id}!")

    while True:
        scelta = menu()
        if scelta == "1":
            vota_proposta(user_id)
        elif scelta == "2":
            proponi_proposta()
        elif scelta == "3":
            classifica()
        elif scelta == "e":
            print("Arrivederci!")
            sys.exit(0)
        else:
            print("Scelta non valida, riprova.")

if __name__ == "__main__":
    main()