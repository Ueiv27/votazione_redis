import redis
from config_redis import username, password, host, port
from utils import (
    key_proposal_text, key_proposal_votes_set,
    key_user_votes, get_user_id
)
from leaderboard import aggiorna_classifica, get_classifica, inizializza_proposta_in_classifica

red = redis.Redis(
    host=host,
    port=port,
    db=0,
    username=username,
    password=password,
    decode_responses=True
)

MAX_VOTI = 3
KEY_PROPOSAL_COUNTER = "proposals:id_counter"

def menu():
    print("\n--- Menu ---")
    print("1. Votare una proposta")
    print("2. Inserire una nuova proposta")
    print("3. Vedere la classifica delle proposte")
    print("4. Analizzare i voti di un corso")
    print("e. Esci")
    return input("Scegli un'opzione: ").strip().lower()

def get_all_proposal_ids():
    """Ottiene tutti gli ID delle proposte dalla classifica ZSET"""
    # Ottieni tutti gli ID dalla classifica (più efficiente)
    proposal_ids = red.zrange("proposals:leaderboard", 0, -1)
    return sorted(proposal_ids, key=lambda x: int(x))

def elenco_proposte():
    proposal_ids = get_all_proposal_ids()
    if not proposal_ids:
        print("Nessuna proposta disponibile al momento.")
        return None
        
    print("\nElenco proposte:")
    proposte = {}
    texts = red.mget([key_proposal_text(pid) for pid in proposal_ids])
    
    for i, pid in enumerate(proposal_ids):
        if texts[i]:
            proposte[pid] = texts[i]
            print(f"{pid}. {texts[i]}")
    
    return proposte

def voti_rimanenti(user_id):
    """Calcola i voti rimanenti per un utente"""
    voti_utilizzati = red.get(key_user_votes(user_id))
    utilizzati = int(voti_utilizzati) if voti_utilizzati else 0
    return max(0, MAX_VOTI - utilizzati)

def vota_proposta(user_id):
    proposte = elenco_proposte()
    if not proposte:
        return
        
    print(f"\nVoti rimanenti: {voti_rimanenti(user_id)}")
    scelta_id = input("Inserisci il numero della proposta da votare: ").strip()
    
    if scelta_id not in proposte:
        print("Errore: Proposta non valida.")
        return
        
    # Controlla se l'utente ha ancora voti disponibili
    if voti_rimanenti(user_id) <= 0:
        print(f"Hai già raggiunto il limite massimo di {MAX_VOTI} voti.")
        return
        
    # Controlla se l'utente ha già votato questa proposta
    key_voti_set = key_proposal_votes_set(scelta_id)
    if red.sismember(key_voti_set, user_id):
        print("Hai già votato questa proposta.")
        return
    
    # Esegui il voto in una transazione
    pipe = red.pipeline()
    pipe.sadd(key_voti_set, user_id)  # Aggiungi utente al set dei votanti
    pipe.incr(key_user_votes(user_id))  # Incrementa voti utente
    pipe.execute()
    
    # Aggiorna la classifica ZSET
    aggiorna_classifica(scelta_id)
    
    print(f"Voto per '{proposte[scelta_id]}' registrato con successo!")

def proponi_proposta():
    testo = input("Inserisci il testo della nuova proposta: ").strip()
    if not testo:
        print("Errore: La proposta non può essere vuota.")
        return
        
    # Ottieni il prossimo ID
    next_id = red.incr(KEY_PROPOSAL_COUNTER)
    
    # Salva la proposta
    red.set(key_proposal_text(next_id), testo)
    
    # Inizializza la proposta nella classifica ZSET
    inizializza_proposta_in_classifica(next_id)
    
    print(f"Proposta '{testo}' aggiunta con l'ID {next_id}.")

def classifica():
    """Mostra la classifica usando il ZSET"""
    print("\n--- Classifica delle Proposte ---")
    
    classifica_data = get_classifica()
    
    if not classifica_data:
        print("Nessuna proposta in classifica.")
        return
    
    for entry in classifica_data:
        print(f"{entry['posizione']}. {entry['testo']} - {entry['voti']} voti")

def conta_voti_per_corso(nome_corso):
    print(f"\n--- Analisi Voti per il Corso '{nome_corso}' ---")
    pattern = f"user:{nome_corso.strip().lower()}:*:votes"
    chiavi = list(red.scan_iter(match=pattern))
    
    if not chiavi:
        print(f"Nessuno studente del corso '{nome_corso}' ha ancora votato.")
        return
        
    voti = red.mget(chiavi)
    totale = sum(int(v) for v in voti if v)
    
    print(f"Trovati {len(chiavi)} studenti votanti per questo corso.")
    print(f"Hanno espresso un totale di {totale} voti.")