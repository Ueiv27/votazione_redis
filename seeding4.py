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

# Funzioni helper per generare le chiavi - AGGIORNATE per la nuova struttura
def key_user_password(user_id):
    """Genera la chiave per la password di un utente. Es: 'user:bd:10:password'"""
    return f"user:{user_id}:password"

def key_user_votes(user_id):
    """Genera la chiave per il contatore di voti di un utente. Es: 'user:bd:10:votes'"""
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

def clean_database():
    """
    Pulisce completamente il database dalle chiavi del nostro applicativo.
    Questa funzione è molto più robusta della precedente perché utilizza
    i pattern della nuova struttura gerarchica.
    """
    print("🧹 Pulizia del database in corso...")
    
    # Contiamo le chiavi prima della pulizia per dare feedback all'utente
    patterns_to_clean = [
        "user:*:password",
        "user:*:votes", 
        "proposal:*:text",
        "proposal:*:votes",
        "proposal:*:score"
    ]
    
    total_keys_found = 0
    for pattern in patterns_to_clean:
        keys = list(red.scan_iter(match=pattern))
        total_keys_found += len(keys)
        print(f"   Trovate {len(keys)} chiavi per il pattern '{pattern}'")
    
    # Puliamo anche le chiavi legacy nel caso qualcuno abbia usato la vecchia versione
    legacy_keys = ["proposals:id_counter", "proposals", "leaderboard"]
    for key in legacy_keys:
        if red.exists(key):
            total_keys_found += 1
            print(f"   Trovata chiave legacy: '{key}'")
    
    if total_keys_found == 0:
        print("   Database già pulito!")
        return
    
    print(f"   Eliminando {total_keys_found} chiavi in totale...")
    
    # Eseguiamo la pulizia usando pipeline per efficienza
    pipe = red.pipeline()
    for pattern in patterns_to_clean:
        for key in red.scan_iter(match=pattern):
            pipe.delete(key)
    
    # Puliamo anche le chiavi legacy e il counter
    for key in legacy_keys:
        pipe.delete(key)
    
    deleted_count = pipe.execute()
    actual_deleted = sum(1 for result in deleted_count if result == 1)
    print(f"   ✅ Eliminate {actual_deleted} chiavi con successo!")

def create_sample_proposals():
    """
    Crea le proposte di esempio usando la nuova struttura gerarchica.
    Ogni proposta avrà le sue chiavi separate per testo e punteggio.
    """
    print("📝 Creazione delle proposte di esempio...")
    
    # Proposte più realistiche e interessanti per un contesto universitario
    proposte = [
        "Caffè gratuito per tutti gli studenti durante le sessioni d'esame",
        "Installazione di più prese elettriche e USB nelle aule studio",
        "Estensione dell'orario di apertura della biblioteca fino alle 24:00",
        "Creazione di un'area ricreativa con ping pong e calcio balilla",
        "Implementazione di un sistema di bike sharing per il campus",
        "Aggiunta di distributori di snack salutari nelle aree comuni"
    ]
    
    # Resettiamo il contatore delle proposte per partire da 1
    red.set("proposals:id_counter", 0)
    
    pipe = red.pipeline()
    created_proposals = []
    
    for testo_proposta in proposte:
        # Generiamo un nuovo ID incrementando il contatore
        proposal_id = red.incr("proposals:id_counter")
        
        # Salviamo il testo della proposta nella sua chiave dedicata
        pipe.set(key_proposal_text(proposal_id), testo_proposta)
        
        # Inizializziamo il punteggio a 0
        pipe.set(key_proposal_score(proposal_id), 0)
        
        created_proposals.append((proposal_id, testo_proposta))
        print(f"   ✏️  Proposta ID {proposal_id}: '{testo_proposta}'")
    
    pipe.execute()
    print(f"   ✅ Create {len(proposte)} proposte con successo!")
    return created_proposals

def create_sample_users():
    """
    Crea gli utenti di esempio con password hashate.
    Includiamo studenti di diversi corsi per testare le funzionalità di analisi.
    """
    print("👥 Registrazione degli utenti di esempio...")
    
    # Dataset più realistico con studenti di diversi corsi
    utenti_da_creare = [
        # Studenti di Database (BD)
        {'id': 'bd:1', 'pass': 'password123'},
        {'id': 'bd:5', 'pass': 'password123'},
        {'id': 'bd:10', 'pass': 'password123'},
        {'id': 'bd:15', 'pass': 'password123'},
        
        # Studenti di Machine Learning (ML)
        {'id': 'ml:3', 'pass': 'password123'},
        {'id': 'ml:7', 'pass': 'password123'},
        {'id': 'ml:12', 'pass': 'password123'},
        {'id': 'ml:18', 'pass': 'password123'},
    ]

    pipe = red.pipeline()
    
    for user in utenti_da_creare:
        user_id = user['id']
        user_pass = user['pass']
        
        # Hassiamo la password usando bcrypt per sicurezza
        hashed_pw = bcrypt.hashpw(user_pass.encode('utf-8'), bcrypt.gensalt())
        
        # Salviamo la password nella chiave dedicata dell'utente
        pipe.set(key_user_password(user_id), hashed_pw.decode('utf-8'))
        
        print(f"   👤 Registrato utente '{user_id}' (password: {user_pass})")
        
    pipe.execute()
    print(f"   ✅ Registrati {len(utenti_da_creare)} utenti con successo!")
    return [user['id'] for user in utenti_da_creare]

def simulate_realistic_voting(user_ids, proposal_count):
    """
    Simula un pattern di voto realistico che rispetta i vincoli del sistema.
    Questa funzione dimostra come la nuova struttura renda più semplice
    gestire le relazioni tra utenti, proposte e voti.
    """
    print("🗳️  Simulazione di voti realistici...")
    
    # Definiamo un pattern di voto che simula preferenze reali
    # Alcune proposte sono più popolari di altre, alcuni utenti votano di più
    voti_simulati = {
        # Proposta 1 (Caffè gratis) - molto popolare
        '1': ['bd:1', 'bd:5', 'ml:3', 'ml:7', 'bd:15'],
        
        # Proposta 2 (Prese elettriche) - abbastanza popolare
        '2': ['bd:10', 'ml:12', 'bd:1', 'ml:18'],
        
        # Proposta 3 (Biblioteca 24h) - popolare tra studenti seri
        '3': ['bd:5', 'ml:7', 'bd:15'],
        
        # Proposta 4 (Area ricreativa) - popolare tra alcuni studenti
        '4': ['ml:3', 'bl:10', 'ml:18'],
        
        # Proposta 5 (Bike sharing) - nicchia ma interessante
        '5': ['bd:1', 'ml:12'],
        
        # Proposta 6 (Snack salutari) - meno popolare
        '6': ['ml:7']
    }
    
    # Verifichiamo che i voti rispettino i vincoli del sistema (max 3 voti per utente)
    user_vote_count = {}
    for proposal_id, voters in voti_simulati.items():
        for user_id in voters:
            user_vote_count[user_id] = user_vote_count.get(user_id, 0) + 1
    
    print(f"   📊 Verifica vincoli: max 3 voti per utente")
    for user_id, count in user_vote_count.items():
        if count > 3:
            print(f"   ⚠️  ATTENZIONE: {user_id} ha {count} voti (limite superato)")
        else:
            print(f"   ✅ {user_id}: {count} voti")
    
    # Eseguiamo la simulazione dei voti usando pipeline per efficienza
    pipe = red.pipeline()
    total_votes = 0
    
    for proposal_id, voters in voti_simulati.items():
        # Controlliamo che la proposta esista davvero
        if int(proposal_id) > proposal_count:
            print(f"   ⚠️  Saltando proposta inesistente ID {proposal_id}")
            continue
            
        print(f"   🗳️  Proposta {proposal_id}: {len(voters)} voti")
        
        for user_id in voters:
            # Controlliamo che l'utente esista
            if user_id not in user_ids:
                print(f"   ⚠️  Saltando utente inesistente: {user_id}")
                continue
            
            # Aggiungiamo l'utente al set dei votanti per questa proposta
            pipe.sadd(key_proposal_votes_set(proposal_id), user_id)
            
            # Incrementiamo il contatore dei voti dell'utente
            pipe.incr(key_user_votes(user_id))
            
            # Incrementiamo il punteggio della proposta
            pipe.incr(key_proposal_score(proposal_id))
            
            total_votes += 1
            print(f"      👍 Voto di '{user_id}' per la proposta {proposal_id}")
    
    pipe.execute()
    print(f"   ✅ Simulati {total_votes} voti con successo!")
    
    # Mostriamo un riepilogo finale
    print(f"\n📈 Riepilogo finale dei voti per utente:")
    for user_id in user_ids:
        vote_count = red.get(key_user_votes(user_id))
        vote_count = int(vote_count) if vote_count else 0
        print(f"   {user_id}: {vote_count} voti espressi")

def verify_data_integrity():
    """
    Verifica l'integrità dei dati inseriti controllando la coerenza
    tra le diverse strutture dati. Questa funzione dimostra come
    la nuova architettura renda più facile fare controlli di consistenza.
    """
    print("🔍 Verifica dell'integrità dei dati...")
    
    # Troviamo tutte le proposte
    proposal_text_keys = list(red.scan_iter(match="proposal:*:text"))
    proposal_ids = []
    for key in proposal_text_keys:
        parts = key.split(":")
        if len(parts) == 3 and parts[1].isdigit():
            proposal_ids.append(parts[1])
    
    print(f"   📋 Trovate {len(proposal_ids)} proposte")
    
    # Verifichiamo che ogni proposta abbia tutte le chiavi necessarie
    for proposal_id in proposal_ids:
        text_key = key_proposal_text(proposal_id)
        score_key = key_proposal_score(proposal_id)
        votes_key = key_proposal_votes_set(proposal_id)
        
        text_exists = red.exists(text_key)
        score_exists = red.exists(score_key)
        votes_exist = red.exists(votes_key)
        
        if not all([text_exists, score_exists]):
            print(f"   ❌ Proposta {proposal_id}: dati inconsistenti")
        else:
            # Verifichiamo la coerenza tra punteggio e numero di voti
            score = int(red.get(score_key))
            vote_count = red.scard(votes_key) if votes_exist else 0
            
            if score == vote_count:
                print(f"   ✅ Proposta {proposal_id}: {score} voti (coerente)")
            else:
                print(f"   ❌ Proposta {proposal_id}: score={score}, voti={vote_count} (INCONSISTENTE)")
    
    # Verifichiamo gli utenti
    user_password_keys = list(red.scan_iter(match="user:*:password"))
    user_ids = []
    for key in user_password_keys:
        parts = key.split(":")
        if len(parts) == 4:  # user:course:number:password
            user_id = f"{parts[1]}:{parts[2]}"
            user_ids.append(user_id)
    
    print(f"   👥 Trovati {len(user_ids)} utenti registrati")
    
    # Verifichiamo la coerenza dei voti degli utenti
    total_user_votes = 0
    for user_id in user_ids:
        vote_count = red.get(key_user_votes(user_id))
        vote_count = int(vote_count) if vote_count else 0
        total_user_votes += vote_count
    
    # Calcoliamo il totale dei voti dalle proposte
    total_proposal_votes = 0
    for proposal_id in proposal_ids:
        score = red.get(key_proposal_score(proposal_id))
        score = int(score) if score else 0
        total_proposal_votes += score
    
    if total_user_votes == total_proposal_votes:
        print(f"   ✅ Coerenza voti: {total_user_votes} voti totali")
    else:
        print(f"   ❌ INCONSISTENZA: utenti={total_user_votes}, proposte={total_proposal_votes}")

def seed_data():
    """
    Funzione principale che orchestra tutto il processo di seeding.
    Questa versione è molto più robusta e informatica della precedente.
    """
    print("🚀 === INIZIALIZZAZIONE DATABASE SISTEMA VOTAZIONE ===")
    print("Questo script creerà un set completo di dati di test per il sistema di votazione.")
    print("La nuova struttura usa chiavi gerarchiche per una migliore organizzazione.\n")
    
    try:
        # Fase 1: Pulizia
        clean_database()
        print()
        
        # Fase 2: Creazione proposte
        created_proposals = create_sample_proposals()
        print()
        
        # Fase 3: Creazione utenti
        user_ids = create_sample_users()
        print()
        
        # Fase 4: Simulazione voti
        simulate_realistic_voting(user_ids, len(created_proposals))
        print()
        
        # Fase 5: Verifica integrità
        verify_data_integrity()
        print()
        
        print("🎉 === SEEDING COMPLETATO CON SUCCESSO! ===")
        print("\n📖 Come utilizzare i dati di test:")
        print("   • Esegui il sistema di votazione principale")
        print("   • Usa qualsiasi degli utenti creati per fare login")
        print("   • Password per tutti gli utenti: 'password123'")
        print("   • Esempi di utenti: bd:1, ml:7, bd:10, ml:12")
        print("\n🔬 Funzionalità da testare:")
        print("   • Login con utenti esistenti")
        print("   • Visualizzazione classifica proposte")
        print("   • Analisi voti per corso (bd, ml)")
        print("   • Tentativo di voto multiplo sulla stessa proposta")
        print("   • Raggiungimento limite massimo voti per utente")
        
    except Exception as e:
        print(f"❌ Errore durante il seeding: {e}")
        print("Verifica la connessione a Redis e riprova.")
        sys.exit(1)

if __name__ == "__main__":
    seed_data()