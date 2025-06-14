#!/usr/bin/env python3
"""
Script per pulire il database Redis e fare seeding iniziale
Esegui con: python cleanup_and_seed.py
"""

import redis
import bcrypt
import random
from config_redis import username, password, host, port
from utils import (
    key_proposal_text, 
    key_user_password, key_user_votes, key_proposal_votes_set
)

def main():
    # Connessione Redis
    red = redis.Redis(
        host=host,
        port=port,
        db=0,
        username=username,
        password=password,
        decode_responses=True
    )
    
    print("🧹 Pulizia database Redis...")
    
    # Cancella tutto il database
    red.flushdb()
    print("✅ Database pulito!")
    
    print("\n🌱 Seeding database...")
    
    # Inizializza il contatore delle proposte
    red.set("proposals:id_counter", 0)
    
    # Proposte di esempio per il seeding
    proposte_iniziali = [
        "Implementare una mensa universitaria con cibi biologici",
        "Creare spazi studio aperti 24/7 durante gli esami",
        "Introdurre corsi di programmazione pratica con progetti reali",
        "Organizzare workshop su intelligenza artificiale e machine learning",
        "Istituire un servizio di tutoraggio peer-to-peer gratuito"
    ]
    
    # Aggiungi le proposte iniziali
    for i, proposta in enumerate(proposte_iniziali, 1):
        red.incr("proposals:id_counter")  # Incrementa il contatore
        
        # Salva testo della proposta
        red.set(key_proposal_text(i), proposta)
        
        # Inizializza la proposta nella classifica ZSET con 0 voti
        red.zadd("proposals:leaderboard", {str(i): 0})
        
        print(f"➕ Aggiunta proposta {i}: {proposta}")
    
    print(f"\n✅ Seeding completato! Aggiunte {len(proposte_iniziali)} proposte.")
    
    # --- SEEDING UTENTI ---
    print("\n👥 Creazione utenti di esempio...")
    
    # Definisci gli utenti da creare
    utenti_da_creare = []
    
    # Studenti ML (alcuni numeri casuali)
    studenti_ml = [1, 3, 5, 7, 9, 12, 15, 18, 20, 23, 25, 28]
    for num in studenti_ml:
        utenti_da_creare.append(f"ml:{num}")
    
    # Studenti BD (alcuni numeri casuali)  
    studenti_bd = [2, 4, 6, 8, 10, 13, 16, 19, 21, 24, 26, 29]
    for num in studenti_bd:
        utenti_da_creare.append(f"bd:{num}")
    
    # Crea gli utenti con password criptate individualmente
    for user_id in utenti_da_creare:
        # Genera un salt unico per ogni utente
        salt = bcrypt.gensalt()
        hashed_pw = bcrypt.hashpw("1234".encode('utf-8'), salt)
        red.set(key_user_password(user_id), hashed_pw.decode('utf-8'))
        print(f"👤 Creato utente: {user_id}")
    
    print(f"\n✅ Creati {len(utenti_da_creare)} utenti (password: 1234)")
    
    # --- SEEDING VOTI ---
    print("\n🗳️ Simulazione voti...")
    
    # Distribuisci i voti in modo realistico
    voti_per_proposta = {
        "1": 0,  # Inizia senza voti
        "2": 0,
        "3": 0,
        "4": 0,
        "5": 0
    }
    
    # Simula comportamento realistico di voto
    for user_id in utenti_da_creare:
        # Ogni utente vota da 1 a 3 proposte (casuale)
        num_voti = random.randint(1, 3)
        proposte_disponibili = list(range(1, 6))  # ID 1-5
        proposte_scelte = random.sample(proposte_disponibili, num_voti)
        
        for prop_id in proposte_scelte:
            prop_id_str = str(prop_id)
            
            # Aggiungi il voto
            pipe = red.pipeline()
            pipe.sadd(key_proposal_votes_set(prop_id_str), user_id)  # Aggiungi al set votanti
            pipe.incr(key_user_votes(user_id))  # Incrementa voti utente
            pipe.zincrby("proposals:leaderboard", 1, prop_id_str)  # Aggiorna classifica ZSET
            pipe.execute()
            
            voti_per_proposta[prop_id_str] += 1
            
        print(f"🗳️ {user_id} ha votato {num_voti} proposte: {proposte_scelte}")
    
    print(f"\n✅ Voti simulati!")
    
    # Mostra risultati finali
    print("\n📊 Riepilogo finale:")
    for prop_id, num_voti in voti_per_proposta.items():
        testo = red.get(key_proposal_text(prop_id))
        print(f"Proposta {prop_id}: {num_voti} voti - '{testo}'")
    
    print(f"\n📊 Stato attuale del database:")
    print(f"- Contatore proposte: {red.get('proposals:id_counter')}")
    print(f"- Elementi in classifica: {red.zcard('proposals:leaderboard')}")
    print(f"- Utenti totali: {len(utenti_da_creare)}")
    
    # Mostra la classifica finale
    print("\n🏆 Classifica finale:")
    classifica = red.zrevrange("proposals:leaderboard", 0, -1, withscores=True)
    for i, (prop_id, score) in enumerate(classifica, 1):
        testo = red.get(key_proposal_text(prop_id))
        print(f"{i}. {testo} - {int(score)} voti")

if __name__ == "__main__":
    main()