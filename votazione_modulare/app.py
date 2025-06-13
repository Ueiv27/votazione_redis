#### per farla funzionare digita: streamlit run votazione_modulare\app.py

import streamlit as st
import redis
import bcrypt
from config_redis import username, password, host, port
from utils import (
    get_user_id, key_user_password, key_user_votes,
    key_proposal_text, key_proposal_votes_set, key_proposal_score
)

# --- Connessione Redis ---
red = redis.Redis(
    host=host,
    port=port,
    db=0,
    username=username,
    password=password,
    decode_responses=True
)

MAX_VOTI = 3

# --- Funzioni ausiliarie ---
def get_all_proposal_ids():
    keys = red.scan_iter(match="proposal:*:text")
    return sorted([k.split(":")[1] for k in keys], key=int)

def login(user_id, password_input):
    hashed_pw = red.get(key_user_password(user_id))
    if not hashed_pw:
        return False
    return bcrypt.checkpw(password_input.encode('utf-8'), hashed_pw.encode('utf-8'))

def register(user_id, password_input):
    if red.exists(key_user_password(user_id)):
        return False
    hashed_pw = bcrypt.hashpw(password_input.encode('utf-8'), bcrypt.gensalt())
    red.set(key_user_password(user_id), hashed_pw.decode('utf-8'))
    return True

def voti_rimanenti(user_id):
    v = red.get(key_user_votes(user_id))
    return MAX_VOTI - int(v) if v else MAX_VOTI

# --- Streamlit UI ---
st.title("📊 Sistema di Votazione Studentesca")

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if not st.session_state.user_id:
    st.subheader("🔐 Login o Registrazione")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Login")
        corso = st.text_input("Corso (BD, ML)", key="login_corso")
        numero = st.text_input("Numero elenco", key="login_num")
        pw = st.text_input("Password", type="password", key="login_pw")
        if st.button("Login"):
            uid = f"{corso.strip().lower()}:{numero.strip()}"
            if login(uid, pw):
                st.session_state.user_id = uid
                st.success("Accesso effettuato!")
            else:
                st.error("Credenziali non valide.")

    with col2:
        st.markdown("#### Registrati")
        corso_r = st.text_input("Corso", key="reg_corso")
        numero_r = st.text_input("Numero elenco", key="reg_num")
        pw_r = st.text_input("Password", type="password", key="reg_pw")
        if st.button("Registrati"):
            uid_r = f"{corso_r.strip().lower()}:{numero_r.strip()}"
            if register(uid_r, pw_r):
                st.success("Registrazione avvenuta! Ora puoi fare login.")
            else:
                st.warning("Utente già registrato.")
    st.stop()

st.success(f"🎉 Benvenuto, {st.session_state.user_id}!")
st.write(f"Voti rimanenti: {voti_rimanenti(st.session_state.user_id)}")

# --- Votazione ---
st.header("🗳️ Vota una Proposta")
proposal_ids = get_all_proposal_ids()
texts = red.mget([key_proposal_text(pid) for pid in proposal_ids])
proposte = dict(zip(proposal_ids, texts))

# Etichette leggibili nel formato "1 – Titolo proposta"
etichette = [f"{pid} – {text}" for pid, text in proposte.items()]
id_mapping = {f"{pid} – {text}": pid for pid, text in proposte.items()}

scelta_label = st.selectbox("Scegli una proposta da votare:", options=etichette)
scelta = id_mapping[scelta_label]  # Ottieni solo l'ID per salvare il voto

if st.button("Vota"):
    if red.sismember(key_proposal_votes_set(scelta), st.session_state.user_id):
        st.warning("Hai già votato questa proposta.")
    elif voti_rimanenti(st.session_state.user_id) <= 0:
        st.warning("Hai raggiunto il limite massimo di voti.")
    else:
        pipe = red.pipeline()
        pipe.sadd(key_proposal_votes_set(scelta), st.session_state.user_id)
        pipe.incr(key_user_votes(st.session_state.user_id))
        pipe.incr(key_proposal_score(scelta))
        pipe.execute()
        st.success("Voto registrato!")

# --- Nuova proposta ---
st.header("➕ Proponi una nuova idea")
nuova = st.text_input("Testo proposta")
if st.button("Aggiungi"):
    if not nuova.strip():
        st.warning("La proposta non può essere vuota.")
    else:
        next_id = red.incr("proposals:id_counter")
        pipe = red.pipeline()
        pipe.set(key_proposal_text(next_id), nuova)
        pipe.set(key_proposal_score(next_id), 0)
        pipe.execute()
        st.success(f"Proposta '{nuova}' aggiunta!")

# --- Classifica ---
st.header("🏆 Classifica")
scores = red.mget([key_proposal_score(pid) for pid in proposal_ids])
classifica = [(int(score) if score else 0, pid, proposte[pid]) for pid, score in zip(proposal_ids, scores)]
classifica.sort(reverse=True)
for rank, (score, pid, text) in enumerate(classifica, 1):
    st.write(f"{rank}. {text} — {score} voti")
