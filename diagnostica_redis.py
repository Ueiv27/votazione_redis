# diagnostica_redis.py

import redis
from config_redis import username, password, host, port

red = redis.Redis(
    host=host,
    port=port,
    db=0,
    username=username,
    password=password,
    decode_responses=True
)

def mostra_classifica():
    print("\n📊 Classifica:")
    ranks = red.zrevrange("leaderboard", 0, -1, withscores=True)
    proposte = red.hgetall("proposals")
    for i, (pid, score) in enumerate(ranks, 1):
        print(f"{i}. {proposte.get(pid, '(sconosciuta)')} - {int(score)} voti")

def mostra_voti_utenti():
    print("\n👤 Voti per utente:")
    voti = red.hgetall("user:votes")
    for user, count in voti.items():
        print(f"- {user}: {count} voti")

def mostra_utenti_per_proposta():
    print("\n👥 Utenti che hanno votato ogni proposta:")
    proposte = red.hgetall("proposals")
    if not proposte:
        print("Nessuna proposta trovata.")
        return
    for pid, nome in proposte.items():
        utenti = red.smembers(f"proposal:votes:{pid}")
        if utenti:
            print(f"- Proposta {pid} ('{nome}') votata da: {', '.join(utenti)}")
        else:
            print(f"- Proposta {pid} ('{nome}') non ha ancora ricevuto voti.")

if __name__ == "__main__":
    mostra_classifica()
    mostra_voti_utenti()
    mostra_utenti_per_proposta()
