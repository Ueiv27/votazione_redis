import redis as r
import sys
import bcrypt
# Assicurati di avere un file config_redis.py con le tue credenziali
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

# --- CHIAVI REDIS RISTRUTTURATE ---
KEY_PROPOSAL_COUNTER = "proposals:id_counter"
# ELIMINATO: KEY_PROPOSALS_HASH, KEY_LEADERBOARD_ZSET
# Ora usiamo una struttura più logica e gerarchica

# Funzioni helper per generare chiavi granulari e coerenti
def key_user_password(user_id):
    """Genera la chiave per la password di un utente. Es: 'user:bd:17:password'"""
    return f"user:{user_id}:password"

def key_user_votes(user_id):
    """Genera la chiave per il contatore di voti di un utente. Es: 'user:bd:17:votes'"""
    return f"user:{user_id}:votes"

def key_proposal_text(proposal_id):
    """Genera la chiave per il testo di una proposta. Es: 'proposal:1:text'"""
    return f"proposal:{proposal_id}:text"

def key_proposal_votes_set(proposal_id):
    """Genera la chiave per il set di votanti di una proposta. Es: 'proposal:1:votes'"""
    return f"proposal:{proposal_id}:votes"

def key_proposal_score(proposal_id):
    """Genera la chiave per il punteggio di una proposta. Es: 'proposal:1:score'"""
    return f"proposal:{proposal_id}:score"

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

def menu():
    print("\n--- Menu ---")
    print("1. Votare una proposta")
    print("2. Inserire una nuova proposta")
    print("3. Vedere la classifica delle proposte")
    print("4. Analizzare i voti di un corso")
    print("e. Esci")
    return input("Scegli un'opzione: ").strip().lower()

def get_all_proposal_ids():
    """
    Trova tutte le proposte esistenti scandendo le chiavi 'proposal:*:text'.
    Questo è più efficiente e pulito del mantenere una lista separata.
    """
    # Cerchiamo tutte le chiavi che contengono il testo delle proposte
    text_keys = list(red.scan_iter(match="proposal:*:text"))
    # Estraiamo gli ID dalle chiavi (es: da "proposal:1:text" estraiamo "1")
    proposal_ids = []
    for key in text_keys:
        parts = key.split(":")
        if len(parts) == 3 and parts[1].isdigit():
            proposal_ids.append(parts[1])
    return sorted(proposal_ids, key=int)

def elenco_proposte():
    """
    Mostra tutte le proposte disponibili recuperando i dati dalla struttura gerarchica.
    """
    proposal_ids = get_all_proposal_ids()
    if not proposal_ids:
        print("Nessuna proposta disponibile al momento.")
        return None
    
    print("\nElenco proposte:")
    proposte = {}
    
    # Recuperiamo tutti i testi delle proposte in un'unica operazione MGET
    text_keys = [key_proposal_text(pid) for pid in proposal_ids]
    texts = red.mget(text_keys)
    
    for i, proposal_id in enumerate(proposal_ids):
        text = texts[i]
        if text:  # Controlliamo che il testo esista
            proposte[proposal_id] = text
            print(f"{proposal_id}. {text}")
    
    return proposte

def vota_proposta(user_id):
    proposte = elenco_proposte()
    if not proposte:
        return

    scelta_id = input("Inserisci il numero della proposta da votare: ")
    if scelta_id not in proposte:
        print("Errore: Proposta non valida.")
        return

    # Controlliamo se l'utente ha già raggiunto il limite di voti
    voti_utente = red.get(key_user_votes(user_id))
    if voti_utente and int(voti_utente) >= MAX_VOTI:
        print(f"Hai già raggiunto il limite massimo di {MAX_VOTI} voti.")
        return

    # Controlliamo se l'utente ha già votato questa proposta
    key_voti_set = key_proposal_votes_set(scelta_id)
    if red.sismember(key_voti_set, user_id):
        print("Hai già votato questa proposta.")
        return

    # Eseguiamo tutte le operazioni in una transazione atomica
    pipe = red.pipeline()
    pipe.sadd(key_voti_set, user_id)  # Aggiungiamo l'utente al set dei votanti
    pipe.incr(key_user_votes(user_id))  # Incrementiamo il contatore voti dell'utente
    pipe.incr(key_proposal_score(scelta_id))  # Incrementiamo il punteggio della proposta
    pipe.execute()
    
    print(f"Voto per '{proposte[scelta_id]}' registrato con successo!")

def proponi_proposta():
    testo = input("Inserisci il testo della nuova proposta: ")
    if not testo.strip():
        print("Errore: La proposta non può essere vuota.")
        return

    # Generiamo un nuovo ID e salviamo la proposta nella struttura gerarchica
    next_id = red.incr(KEY_PROPOSAL_COUNTER)
    pipe = red.pipeline()
    pipe.set(key_proposal_text(next_id), testo)  # Salviamo il testo
    pipe.set(key_proposal_score(next_id), 0)  # Inizializziamo il punteggio a 0
    pipe.execute()
    
    print(f"Proposta '{testo}' aggiunta con l'ID {next_id}.")

def classifica():
    """
    Genera la classifica delle proposte ordinandole per punteggio.
    Ora non abbiamo più bisogno di un sorted set separato!
    """
    print("\n--- Classifica delle Proposte ---")
    proposal_ids = get_all_proposal_ids()
    
    if not proposal_ids:
        print("Nessuna proposta in classifica.")
        return

    # Recuperiamo testi e punteggi in operazioni batch
    text_keys = [key_proposal_text(pid) for pid in proposal_ids]
    score_keys = [key_proposal_score(pid) for pid in proposal_ids]
    
    texts = red.mget(text_keys)
    scores = red.mget(score_keys)
    
    # Creiamo una lista di tuple (punteggio, id, testo) per ordinare facilmente
    proposals_with_scores = []
    for i, proposal_id in enumerate(proposal_ids):
        text = texts[i]
        score = int(scores[i]) if scores[i] else 0
        if text:  # Solo se la proposta ha un testo valido
            proposals_with_scores.append((score, proposal_id, text))
    
    # Ordiniamo per punteggio decrescente
    proposals_with_scores.sort(key=lambda x: x[0], reverse=True)
    
    # Mostriamo la classifica
    for i, (score, proposal_id, text) in enumerate(proposals_with_scores, 1):
        print(f"{i}. {text} - {score} voti")

def conta_voti_per_corso(nome_corso):
    """
    Analizza i voti per corso usando la struttura gerarchica degli utenti.
    """
    print(f"\n--- Analisi Voti per il Corso '{nome_corso}' ---")
    
    # Costruiamo il pattern per cercare tutte le chiavi dei voti di un corso
    prefisso_corso = nome_corso.strip().lower()
    pattern = f"user:{prefisso_corso}:*:votes"
    
    # Usiamo SCAN per trovare le chiavi
    chiavi_voti_corso = list(red.scan_iter(match=pattern))
    
    if not chiavi_voti_corso:
        print(f"Nessuno studente del corso '{nome_corso}' ha ancora votato.")
        return
        
    # Recuperiamo tutti i valori in una sola operazione
    voti_per_utente = red.mget(chiavi_voti_corso)
    
    # Calcoliamo le statistiche
    voti_totali_corso = sum(int(v) for v in voti_per_utente if v is not None)
    utenti_del_corso_votanti = len(chiavi_voti_corso)
    
    print(f"Trovati {utenti_del_corso_votanti} studenti votanti per questo corso.")
    print(f"Hanno espresso un totale di {voti_totali_corso} voti.")

def main():
    print("Benvenuto nel sistema di votazione NoSQL!")
    user_id = None
    
    while not user_id:
        print("\n1. Login")
        print("2. Registrati")
        print("e. Esci")
        scelta = input("Scegli un'opzione: ").strip().lower()

        if scelta == "1":
            user_id = login_utente()
        elif scelta == "2":
            user_id = registra_utente()
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
            corso_da_cercare = input("Di quale corso vuoi analizzare i voti? (es. bd, ml) ")
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