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
# È buona pratica avere una sola istanza di connessione
@st.cache_resource
def get_redis_connection():
    return redis.Redis(
        host=host,
        port=port,
        db=0,
        username=username,
        password=password,
        decode_responses=True
    )

red = get_redis_connection()

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

# --- Inizializzazione dello stato di sessione ---
if "user_id" not in st.session_state:
    st.session_state.user_id = None
# NUOVA LOGICA: Gestione dello stato della pagina (login/registrazione)
if "page" not in st.session_state:
    st.session_state.page = "login"


# --- Flusso di Autenticazione ---
if not st.session_state.user_id:
    
    # NUOVA LOGICA: Mostra la pagina di LOGIN
    if st.session_state.page == "login":
        st.subheader("🔐 Login")
        corso = st.text_input("Corso (BD, ML)", key="login_corso")
        numero = st.text_input("Numero elenco", key="login_num")
        pw = st.text_input("Password", type="password", key="login_pw")
        
        if st.button("Login", type="primary"):
            uid = f"{corso.strip().lower()}:{numero.strip()}"
            if login(uid, pw):
                st.session_state.user_id = uid
                st.success("Accesso effettuato!")
                st.rerun() # Ricarica l'app per mostrare l'area utente
            else:
                st.error("Credenziali non valide.")
        
        st.divider()
        if st.button("Non hai un account? Registrati qui"):
            st.session_state.page = "register"
            st.rerun()

    # NUOVA LOGICA: Mostra la pagina di REGISTRAZIONE
    elif st.session_state.page == "register":
        st.subheader("✍️ Registrati")
        corso_r = st.text_input("Corso", key="reg_corso")
        numero_r = st.text_input("Numero elenco", key="reg_num")
        pw_r = st.text_input("Password", type="password", key="reg_pw")
        
        if st.button("Registrati", type="primary"):
            uid_r = f"{corso_r.strip().lower()}:{numero_r.strip()}"
            if register(uid_r, pw_r):
                # MODIFICATO: Esegue il login automatico dopo la registrazione
                st.session_state.user_id = uid_r 
                st.success("Registrazione completata! Accesso effettuato.")
                st.rerun()
            else:
                st.warning("Utente già registrato.")
        
        st.divider()
        if st.button("Hai già un account? Torna al Login"):
            st.session_state.page = "login"
            st.rerun()
    st.stop()

# --- Area utente autenticato (viene mostrata solo se il login ha successo) ---
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
    # MODIFICATO: La logica per recuperare i testi rimane uguale ma il codice è pulito
    texts = red.mget([key_proposal_text(pid) for pid in proposal_ids])
    proposte = {pid: text for pid, text in zip(proposal_ids, texts) if text}
    
    if proposte:
        etichette = [f"{pid} – {text}" for pid, text in proposte.items()]
        id_mapping = {label: pid for label, pid in zip(etichette, proposte.keys())}
        
        scelta_label = st.selectbox("Scegli una proposta da votare:", options=etichette)
        scelta_id = id_mapping.get(scelta_label)
        
        if st.button("Vota", type="primary"):
            if voti_rimanenti(st.session_state.user_id) <= 0:
                st.warning("⚠️ Hai raggiunto il limite massimo di voti.")
            elif red.sismember(key_proposal_votes_set(scelta_id), st.session_state.user_id):
                st.warning("⚠️ Hai già votato questa proposta.")
            else:
                pipe = red.pipeline()
                pipe.sadd(key_proposal_votes_set(scelta_id), st.session_state.user_id)
                pipe.incr(key_user_votes(st.session_state.user_id))
                pipe.execute()
                aggiorna_classifica(scelta_id)
                st.success("✅ Voto registrato!")
                st.rerun()
else:
    st.info("Nessuna proposta disponibile per la votazione.")

# --- Nuova proposta ---
st.header("➕ Proponi una nuova idea")
nuova = st.text_input("Testo proposta", placeholder="Inserisci la tua proposta...")

if st.button("Aggiungi Proposta", type="primary"):
    if not nuova.strip():
        st.warning("⚠️ La proposta non può essere vuota.")
    else:
        next_id = red.incr("proposals:id_counter")
        red.set(key_proposal_text(next_id), nuova.strip())
        inizializza_proposta_in_classifica(next_id)
        st.success(f"✅ Proposta '{nuova}' aggiunta!")
        st.rerun()

# --- Classifica ---
st.header("🏆 Classifica")
classifica = get_classifica()

if not classifica:
    st.info("Nessuna proposta ancora votata.")
else:
    for i, entry in enumerate(classifica):
        col1, col2, col3 = st.columns([1, 6, 1])
        with col1:
            if entry['posizione'] == 1: st.markdown("🥇")
            elif entry['posizione'] == 2: st.markdown("🥈")
            elif entry['posizione'] == 3: st.markdown("🥉")
            else: st.markdown(f"**{entry['posizione']}.**")
        with col2:
            st.markdown(f"**{entry['testo']}**")
        with col3:
            st.metric("Voti", entry['voti'])
        if i < len(classifica) - 1:
            st.divider()

# --- Sezione di logout ---
st.sidebar.header("⚙️ Impostazioni")
if st.sidebar.button("Logout", type="secondary"):
    # Resetta tutti i valori di sessione per un logout pulito
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()
