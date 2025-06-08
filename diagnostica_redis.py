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

def mostra_votanti_per_proposta():
    print("\n📥 Votanti per proposta:")
    proposte = red.hkeys("proposals")
    for pid in proposte:
        votanti = red.smembers(f"proposal:votes:{pid}")
        print(f"- Proposta {pid}: {len(votanti)} votanti")

if __name__ == "__main__":
    mostra_classifica()
    mostra_voti_utenti()
    mostra_votanti_per_proposta()
