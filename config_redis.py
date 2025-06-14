## --- CONFIGURAZIONE ---
# !!! INSERISCI QUI LE TUE CREDENZIALI
import redis

# Istanza di connessione centralizzata
red = redis.Redis(
    host='redis-15081.crce198.eu-central-1-3.ec2.redns.redis-cloud.com',
    port=15081,
    db=0,
    username="default",
    password="O9uv1t8Sxp93vkDYnnHX6NOhN953ZlZw",
    decode_responses=True
)