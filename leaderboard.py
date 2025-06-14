import redis
from config_redis import username, password, host, port
from utils import key_proposal_text

red = redis.Redis(
    host=host,
    port=port,
    db=0,
    username=username,
    password=password,
    decode_responses=True
)

LEADERBOARD_KEY = "proposals:leaderboard"

def aggiorna_classifica(proposal_id):
    """Aggiunge 1 voto alla proposta nella classifica ZSET"""
    red.zincrby(LEADERBOARD_KEY, 1, str(proposal_id))

def get_classifica():
    """Ottiene la classifica ordinata in base ai voti (dal più votato al meno votato)"""
    # Ottieni tutte le proposte ordinate per score decrescente
    ranking = red.zrevrange(LEADERBOARD_KEY, 0, -1, withscores=True)
    
    if not ranking:
        return []

    # Estrai gli ID delle proposte
    proposal_ids = [pid for pid, _ in ranking]
    
    # Ottieni i testi delle proposte in batch
    texts = red.mget([key_proposal_text(pid) for pid in proposal_ids])
    
    # Costruisci la classifica finale
    classifica = []
    for i, ((pid, score), text) in enumerate(zip(ranking, texts)):
        if text:  # Solo se il testo esiste
            classifica.append({
                "posizione": i + 1,
                "id": pid,
                "testo": text,
                "voti": int(score)
            })
    
    return classifica

def get_classifica_top(n=10):
    """Ottiene solo i primi N elementi della classifica"""
    ranking = red.zrevrange(LEADERBOARD_KEY, 0, n-1, withscores=True)
    
    if not ranking:
        return []

    proposal_ids = [pid for pid, _ in ranking]
    texts = red.mget([key_proposal_text(pid) for pid in proposal_ids])
    
    classifica = []
    for i, ((pid, score), text) in enumerate(zip(ranking, texts)):
        if text:
            classifica.append({
                "posizione": i + 1,
                "id": pid,
                "testo": text,
                "voti": int(score)
            })
    
    return classifica

def get_score_proposta(proposal_id):
    """Ottiene il punteggio di una specifica proposta"""
    score = red.zscore(LEADERBOARD_KEY, str(proposal_id))
    return int(score) if score is not None else 0

def inizializza_proposta_in_classifica(proposal_id):
    """Inizializza una nuova proposta nella classifica con 0 voti"""
    red.zadd(LEADERBOARD_KEY, {str(proposal_id): 0})

def rimuovi_proposta_da_classifica(proposal_id):
    """Rimuove una proposta dalla classifica (se necessario)"""
    red.zrem(LEADERBOARD_KEY, str(proposal_id))