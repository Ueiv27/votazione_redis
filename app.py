#### per farla funzionare digita: streamlit run app.py

import streamlit as st
import redis
import bcrypt
from config_redis import username, password, host, port
from utils import (
    get_user_id, key_user_password, key_user_votes,
    key_proposal_text, key_proposal_votes_set
)
from leaderboard import get_classifica, aggiorna_classifica, inizializza_proposta_in_classifica

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
    """Ottiene tutti gli ID delle proposte dalla classifica ZSET"""
    proposal_ids = red.zrange("proposals:leaderboard", 0, -1)
    return sorted(proposal_ids, key=lambda x: int(x))

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
    utilizzati = int(v) if v else 0
    return max(0, MAX_VOTI - utilizzati)

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
                st.rerun()
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

# --- Area utente autenticato ---
st.success(f"🎉 Benvenuto, {st.session_state.user_id}!")

# Mostra informazioni utente
col1, col2 = st.columns(2)
with col1:
    st.metric("Voti rimanenti", voti_rimanenti(st.session_state.user_id))
with col2:
    voti_usati = red.get(key_user_votes(st.session_state.user_id))
    st.metric("Voti utilizzati", int(voti_usati) if voti_usati else 0)

# --- Votazione ---
st.header("🗳️ Vota una Proposta")

proposal_ids = get_all_proposal_ids()
if proposal_ids:
    texts = red.mget([key_proposal_text(pid) for pid in proposal_ids])
    proposte = {pid: text for pid, text in zip(proposal_ids, texts) if text}
    
    if proposte:
        # Etichette leggibili nel formato "1 – Titolo proposta"
        etichette = [f"{pid} – {text}" for pid, text in proposte.items()]
        id_mapping = {f"{pid} – {text}": pid for pid, text in proposte.items()}
        
        scelta_label = st.selectbox("Scegli una proposta da votare:", options=etichette)
        scelta = id_mapping[scelta_label]  # Ottieni solo l'ID per salvare il voto
        
        col1, col2 = st.columns([1, 3])
        with col1:
            vota_button = st.button("Vota", type="primary")
        with col2:
            if voti_rimanenti(st.session_state.user_id) <= 0:
                st.warning("⚠️ Hai raggiunto il limite massimo di voti.")
        
        if vota_button:
            if red.sismember(key_proposal_votes_set(scelta), st.session_state.user_id):
                st.warning("⚠️ Hai già votato questa proposta.")
            elif voti_rimanenti(st.session_state.user_id) <= 0:
                st.warning("⚠️ Hai raggiunto il limite massimo di voti.")
            else:
                # Esegui il voto
                pipe = red.pipeline()
                pipe.sadd(key_proposal_votes_set(scelta), st.session_state.user_id)
                pipe.incr(key_user_votes(st.session_state.user_id))
                pipe.execute()
                
                # Aggiorna la classifica ZSET
                aggiorna_classifica(scelta)
                
                st.success("✅ Voto registrato!")
                st.rerun()
    else:
        st.info("Nessuna proposta disponibile per la votazione.")
else:
    st.info("Nessuna proposta disponibile per la votazione.")

# --- Nuova proposta ---
st.header("➕ Proponi una nuova idea")

nuova = st.text_input("Testo proposta", placeholder="Inserisci la tua proposta...")

col1, col2 = st.columns([1, 3])
with col1:
    aggiungi_button = st.button("Aggiungi Proposta", type="primary")

if aggiungi_button:
    if not nuova.strip():
        st.warning("⚠️ La proposta non può essere vuota.")
    else:
        next_id = red.incr("proposals:id_counter")
        red.set(key_proposal_text(next_id), nuova.strip())
        
        # Inizializza nella classifica ZSET
        inizializza_proposta_in_classifica(next_id)
        
        st.success(f"✅ Proposta '{nuova}' aggiunta!")
        st.rerun()

# --- Classifica ---
st.header("🏆 Classifica")

classifica = get_classifica()

if not classifica:
    st.info("Nessuna proposta ancora votata.")
else:
    # Mostra la classifica in modo più bello
    for i, entry in enumerate(classifica):
        col1, col2, col3 = st.columns([1, 6, 1])
        
        with col1:
            # Emoji per i primi 3 posti
            if entry['posizione'] == 1:
                st.markdown("🥇")
            elif entry['posizione'] == 2:
                st.markdown("🥈")
            elif entry['posizione'] == 3:
                st.markdown("🥉")
            else:
                st.markdown(f"**{entry['posizione']}.**")
        
        with col2:
            st.markdown(f"**{entry['testo']}**")
        
        with col3:
            st.metric("Voti", entry['voti'])
        
        # Aggiungi una linea separatrice tranne per l'ultimo elemento
        if i < len(classifica) - 1:
            st.divider()

# --- Sezione di logout ---
st.sidebar.header("⚙️ Impostazioni")
if st.sidebar.button("Logout", type="secondary"):
    st.session_state.user_id = None
    st.rerun()