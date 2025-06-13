import redis
from config_redis import username, password, host, port
from utils import (
    key_proposal_text, key_proposal_score, key_proposal_votes_set,
    key_user_votes, get_user_id
)

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
    text_keys = list(red.scan_iter(match="proposal:*:text"))
    proposal_ids = [k.split(":")[1] for k in text_keys if k.split(":")[1].isdigit()]
    return sorted(proposal_ids, key=int)

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

def vota_proposta(user_id):
    proposte = elenco_proposte()
    if not proposte:
        return
    scelta_id = input("Inserisci il numero della proposta da votare: ")
    if scelta_id not in proposte:
        print("Errore: Proposta non valida.")
        return
    voti_utente = red.get(key_user_votes(user_id))
    if voti_utente and int(voti_utente) >= MAX_VOTI:
        print(f"Hai già raggiunto il limite massimo di {MAX_VOTI} voti.")
        return
    key_voti_set = key_proposal_votes_set(scelta_id)
    if red.sismember(key_voti_set, user_id):
        print("Hai già votato questa proposta.")
        return
    pipe = red.pipeline()
    pipe.sadd(key_voti_set, user_id)
    pipe.incr(key_user_votes(user_id))
    pipe.incr(key_proposal_score(scelta_id))
    pipe.execute()
    print(f"Voto per '{proposte[scelta_id]}' registrato con successo!")

def proponi_proposta():
    testo = input("Inserisci il testo della nuova proposta: ")
    if not testo.strip():
        print("Errore: La proposta non può essere vuota.")
        return
    next_id = red.incr(KEY_PROPOSAL_COUNTER)
    pipe = red.pipeline()
    pipe.set(key_proposal_text(next_id), testo)
    pipe.set(key_proposal_score(next_id), 0)
    pipe.execute()
    print(f"Proposta '{testo}' aggiunta con l'ID {next_id}.")

def classifica():
    print("\n--- Classifica delle Proposte ---")
    proposal_ids = get_all_proposal_ids()
    if not proposal_ids:
        print("Nessuna proposta in classifica.")
        return
    texts = red.mget([key_proposal_text(pid) for pid in proposal_ids])
    scores = red.mget([key_proposal_score(pid) for pid in proposal_ids])
    proposals_with_scores = [
        (int(scores[i]) if scores[i] else 0, proposal_ids[i], texts[i])
        for i in range(len(proposal_ids)) if texts[i]
    ]
    proposals_with_scores.sort(key=lambda x: x[0], reverse=True)
    for i, (score, pid, text) in enumerate(proposals_with_scores, 1):
        print(f"{i}. {text} - {score} voti")

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
