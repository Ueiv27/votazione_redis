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
except r.exceptions.ConnectionError as e:
    print(f"Errore di connessione a Redis: {e}")
    sys.exit(1)

# Funzioni helper per generare le chiavi, per coerenza con lo script principale
def key_user_password(user_id):
    return f"user:{user_id}:password"

def key_user_votes(user_id):
    return f"user:{user_id}:votes"

def key_proposal_votes_set(proposal_id):
    return f"proposal:votes:{proposal_id}"


def seed_data():
    """Funzione per pulire il DB e inserire i dati di prova."""
    
    print("--- Inizio del processo di seeding ---")
    
    # --- 1. Pulizia del database dalle chiavi del nostro applicativo ---
    print("1. Pulizia delle chiavi esistenti...")
    pipe = red.pipeline()
    # Trova e cancella tutte le chiavi che seguono i nostri pattern
    for key in red.scan_iter("user:*"):
        pipe.delete(key)
    for key in red.scan_iter("proposal:votes:*"):
        pipe.delete(key)
    # Cancella le chiavi fisse
    pipe.delete("proposals:id_counter", "proposals", "leaderboard")
    pipe.execute()
    
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
        proposal_id = red.incr("proposals:id_counter")
        pipe.hset("proposals", proposal_id, testo_proposta)
        pipe.zadd("leaderboard", {proposal_id: 0})
        print(f"   - Creata proposta ID {proposal_id}: '{testo_proposta}'")
    pipe.execute()
    
    print("   Proposte inserite.")

    # --- 3. Creazione degli utenti di esempio ---
    print("3. Registrazione degli utenti di esempio...")
    utenti_da_creare = [
        {'id': 'bd:10', 'pass': '1234'},
        {'id': 'ml:7', 'pass': '1234'},
        {'id': 'bd:3', 'pass': '1234'},
        {'id': 'ml:15', 'pass': '1234'}
    ]

    for user in utenti_da_creare:
        user_id = user['id']
        user_pass = user['pass']
        hashed_pw = bcrypt.hashpw(user_pass.encode('utf-8'), bcrypt.gensalt())
        # Usa la nuova chiave granulare per la password
        red.set(key_user_password(user_id), hashed_pw.decode('utf-8'))
        print(f"   - Registrato utente '{user_id}'")
        
    print("   Utenti registrati.")

    # --- 4. Simulazione dei voti ---
    print("4. Simulazione dei voti...")
    
    # Struttura: { proposal_id: [lista di user_id che la votano] }
    voti_da_simulare = {
        '1': ["bd:10", "ml:15"],                      # 2 voti
        '2': ["bd:10", "ml:7"],                      # 2 voti
        '3': ["ml:7"],                               # 1 voto
        '4': ["bd:10", "ml:7", "ml:15"]               # 3 voti
    }
    # Voti totali per utente: bd:10 (3), ml:7 (3), ml:15 (2), bd:3 (0)
    
    pipe = red.pipeline()
    for proposal_id, users in voti_da_simulare.items():
        # Aggiorna il punteggio nella classifica
        pipe.zincrby("leaderboard", len(users), proposal_id)
        for user_id in users:
            # Aggiunge il voto al set della proposta
            pipe.sadd(key_proposal_votes_set(proposal_id), user_id)
            # Incrementa il contatore granulare dei voti dell'utente
            pipe.incr(key_user_votes(user_id))
            print(f"   - Voto di '{user_id}' per la proposta ID {proposal_id}")
    
    pipe.execute()
    print("   Simulazione voti completata.")
    
    print("\n--- Dati di prova inseriti con successo! ---")
    print("Ora puoi eseguire lo script principale e fare login con gli utenti di prova.")
    print("Esempio utente: bd:10, password: password123")

if __name__ == "__main__":
    seed_data()