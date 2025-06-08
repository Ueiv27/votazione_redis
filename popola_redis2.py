import redis as r
import sys
from config_redis import username, password, host, port


try:
    # Usiamo decode_responses=True per non dover convertire manualmente i valori da bytes a stringhe
    red = r.Redis(
        host=host,
        port=port,
        db=0,
        username=username,
        password=password,
        decode_responses=True 
    )
    red.ping()
except r.exceptions.ConnectionError as e:
    print(f"Errore di connessione a Redis: {e}")
    sys.exit(1)

# --- NOMI DELLE CHIAVI (per coerenza con lo script principale) ---
KEY_PROPOSAL_COUNTER = "proposals:id_counter"
KEY_PROPOSALS_HASH = "proposals"
KEY_USER_VOTES_HASH = "user:votes"
KEY_LEADERBOARD_ZSET = "leaderboard"

def key_proposal_votes_set(proposal_id):
    """Genera la chiave per il set di voti di una proposta."""
    return f"proposal:votes:{proposal_id}"

def seed_data():
    """Funzione per pulire il DB e inserire i dati di prova."""
    
    print("--- Inizio del processo di seeding ---")
    
    # --- 1. Pulizia del database dalle chiavi del nostro applicativo ---
    print("1. Pulizia delle chiavi esistenti...")
    
    existing_vote_sets = red.keys("proposal:votes:*")
    
    keys_to_delete = [
        KEY_PROPOSAL_COUNTER,
        KEY_PROPOSALS_HASH,
        KEY_USER_VOTES_HASH,
        KEY_LEADERBOARD_ZSET
    ]
    if existing_vote_sets:
        keys_to_delete.extend(existing_vote_sets)
    
    if keys_to_delete:
        red.delete(*keys_to_delete)
    
    print("   Pulizia completata.")
    
    # --- 2. Creazione delle proposte di esempio ---
    print("2. Inserimento delle proposte di esempio...")
    
    proposte = [
        "Caffè gratis per gli studenti",
        "Più prese elettriche nelle aule studio",
        "Estensione orario di apertura della biblioteca",
        "Creazione di un'area relax con ping pong"
    ]
    
    pipe = red.pipeline()
    for testo_proposta in proposte:
        proposal_id = red.incr(KEY_PROPOSAL_COUNTER)
        pipe.hset(KEY_PROPOSALS_HASH, proposal_id, testo_proposta)
        pipe.zadd(KEY_LEADERBOARD_ZSET, {proposal_id: 0})
        print(f"   - Creata proposta ID {proposal_id}: '{testo_proposta}'")
    pipe.execute()
    
    print("   Proposte inserite.")
    
    # --- 3. Simulazione dei voti con i nuovi corsi e ID utente ---
    print("3. Simulazione dei voti degli utenti (Corsi: BD, ML; Elenco: 1-25)...")
    
    # MODIFICA: Utenti e voti aggiornati secondo le nuove regole
    voti_da_simulare = {
        '1': ["bd:10", "ml:5", "bd:21", "ml:15"],      # 4 voti
        '2': ["bd:10", "ml:7", "bd:3"],                # 3 voti
        '3': ["ml:5", "ml:7"],                         # 2 voti
        '4': ["bd:3"],                                 # 1 voto
    }
    # Note sui voti totali per utente:
    # 'bd:10' -> 2 voti
    # 'ml:5' -> 2 voti
    # 'ml:7' -> 2 voti
    # 'bd:3' -> 2 voti
    # 'bd:21' -> 1 voto
    # 'ml:15' -> 1 voto
    
    pipe = red.pipeline()
    for proposal_id, users in voti_da_simulare.items():
        key_voti = key_proposal_votes_set(proposal_id)
        for user_id in users:
            pipe.sadd(key_voti, user_id)
            pipe.hincrby(KEY_USER_VOTES_HASH, user_id, 1)
            print(f"   - Utente '{user_id}' ha votato per la proposta ID {proposal_id}")
        
        # Aggiorna il punteggio nella classifica
        pipe.zincrby(KEY_LEADERBOARD_ZSET, len(users), proposal_id)
    
    pipe.execute()
    print("   Simulazione voti completata.")
    
    print("\n--- Dati di prova inseriti con successo! ---")
    print("Ora puoi eseguire lo script principale per testare le funzionalità.")

if __name__ == "__main__":
    seed_data()