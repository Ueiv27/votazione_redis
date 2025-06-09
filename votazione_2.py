import redis as r
import sys
from config_redis import username, password, host, port


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
    corso = input("Che corso frequenti? (BD, ML) ")
    while True:
        numero = input("Qual è il tuo numero dell'elenco? ")
        if numero.isdigit() and 1 <= int(numero) <= 30:
            break
        print("Le classi sono composte da massimo 30 persone, inserisci un numero valido. ")
    return f"{corso.strip().lower()}:{numero.strip()}"

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


def conta_voti_per_corso(nome_corso):
    """
    Conta il totale dei voti espressi da tutti gli studenti di un corso specifico.
    """
    print(f"\n--- Analisi Voti per il Corso '{nome_corso}' ---")
    
    # 1. Recupera l'intero hash con tutti gli utenti e i loro conteggi di voti
    utenti_e_voti = red.hgetall(KEY_USER_VOTES_HASH) 
    
    if not utenti_e_voti:
        print("Nessun voto è stato ancora registrato.")
        return

    voti_totali_corso = 0
    utenti_del_corso_votanti = 0
    prefisso_corso = f"{nome_corso.strip().lower()}:" 

    # 2. Itera sul dizionario in Python
    for user_id, num_voti in utenti_e_voti.items():
        # 3. Controlla se l'ID utente inizia con il prefisso del corso desiderato
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
        elif scelta == "4":
            corso_da_cercare = input("Di quale corso vuoi analizzare i voti? ")
            if corso_da_cercare.strip(): # Controlla che l'utente abbia scritto qualcosa
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