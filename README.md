# 📊 Sistema di Votazione Studentesca

Un sistema completo per votare proposte studentesche utilizzando Redis come database NoSQL. Include sia un'interfaccia web moderna (Streamlit) che un'interfaccia da terminale.

## 🎯 Cos'è questo progetto?

Questo è un sistema di votazione democratica per studenti ITS che permette di:
- **Proporre** nuove idee per migliorare la vita in ITS
- **Votare** le proposte degli altri studenti (massimo 3 voti per persona)
- **Vedere** una classifica in tempo reale delle proposte più votate
- **Autenticarsi** in modo sicuro con password criptate

## 🚀 Come iniziare

### Prerequisiti
- Python 3.8 o superiore installato sul tuo computer
- Una connessione internet (per Redis Cloud)

### Installazione (passo dopo passo)

1. **Scarica il progetto**
   ```bash
   # Se hai git installato:
   git clone https://github.com/Ueiv27/votazione_redis.git
   
   # Oppure scarica lo ZIP e estrailo
   ```

2. **Vai nella cartella del progetto**
   ```bash
   cd votazione_redis   

   ```

3. **Installa le dipendenze**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configura il database**
   - Apri il file `config_redis.py`
   - Le credenziali sono già configurate per il database di test
   - **Non condividere mai queste credenziali pubblicamente!**

5. **Inizializza il database (opzionale)**
   ```bash
   python seeding_mod.py
   ```
   Questo comando:
   - Pulisce il database
   - Aggiunge 5 proposte di esempio
   - Crea utenti di test (password: `1234`)
   - Simula alcuni voti per testare il sistema

## 🖥️ Come usare il sistema

### Opzione 1: Interfaccia Web (Raccomandato per principianti)

```bash
streamlit run app.py
```

Poi apri il browser all'indirizzo che appare nel terminale (di solito `http://localhost:8501`)

**Cosa puoi fare:**
- **Registrarti** con il tuo corso (BD o ML) e numero di elenco
- **Fare login** con le tue credenziali
- **Votare** fino a 3 proposte diverse
- **Proporre** nuove idee
- **Vedere** la classifica in tempo reale con emoji per i primi 3 posti! 🥇🥈🥉

### Opzione 2: Interfaccia Terminale (Per utenti avanzati)

```bash
python main.py
```

Interfaccia testuale con le stesse funzionalità ma più spartana.

## 👥 Come registrarsi

Il sistema usa un formato specifico per gli utenti:
- **Corso**: `BD` (Big Data) o `ML` (Machine Learning)
- **Numero**: Il tuo numero nell'elenco della classe (1-30)
- **Password**: Almeno 4 caratteri (verrà criptata automaticamente)

**Esempio:**
- User ID generato: `ml:15` (studente ML numero 15)
- Password: quella che scegli tu

## 📋 Struttura del progetto

```
├── app.py              # Interfaccia web Streamlit ⭐
├── main.py             # Interfaccia terminale
├── auth.py             # Gestione login/registrazione
├── logic.py            # Logica di votazione e proposte
├── leaderboard.py      # Gestione classifica
├── utils.py            # Funzioni ausiliarie
├── config_redis.py     # Credenziali database
├── seeding_mod.py      # Script per inizializzare dati di test
├── requirements.txt    # Dipendenze Python
└── README.md          # Questa guida
```

## 🔧 Funzionalità principali

### 🗳️ Sistema di Votazione
- Ogni utente può votare **massimo 3 proposte**
- Non puoi votare la stessa proposta due volte
- I voti vengono salvati in modo permanente

### 📈 Classifica Dinamica
- Aggiornamento in tempo reale
- Ordinamento automatico per numero di voti

### 🔐 Sicurezza
- Password criptate con bcrypt (salt unico per ogni utente)
- Controllo accessi basato su credenziali
- Prevenzione voti duplicati

### 💾 Database Redis
- Memorizzazione efficiente con strutture dati NoSQL
- Classifica implementata con ZSET (Sorted Set)
- Operazioni atomiche per consistenza dati

## 🧪 Testare il sistema

### Utenti di test (se hai eseguito il seeding)
- **ml:1**, **ml:3**, **ml:5**... (password: `1234`)
- **bd:2**, **bd:4**, **bd:6**... (password: `1234`)

### Proposte di esempio
1. "Implementare una mensa universitaria con cibi biologici"
2. "Creare spazi studio aperti 24/7 durante gli esami"
3. "Introdurre corsi di programmazione pratica con progetti reali"
4. "Organizzare workshop su intelligenza artificiale e machine learning"
5. "Istituire un servizio di tutoraggio peer-to-peer gratuito"
6. "Cacciare Luca Conte"

## ⚠️ Risoluzione problemi comuni

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Connection refused" (Redis)
- Verifica che le credenziali in `config_redis.py` siano corrette
- Controlla la connessione internet

### "Streamlit command not found"
```bash
pip install streamlit
```

### L'interfaccia web non si apre
- Controlla l'URL nel terminale
- Prova a utilizzare `http://localhost:8501` direttamente

## 🎓 Concetti appresi

Questo progetto dimostra:
- **Database NoSQL** con Redis
- **Crittografia** delle password
- **Interfacce utente** multiple (web + terminale)
- **Architettura modulare** del codice
- **Gestione stato** e sessioni utente
- **Operazioni atomiche** per consistenza dati

## 📚 Tecnologie utilizzate

- **Python 3.8+**: Linguaggio principale
- **Redis**: Database NoSQL in cloud
- **Streamlit**: Framework per interfacce web
- **bcrypt**: Crittografia password

## 🤝 Supporto

Se hai problemi:
1. Leggi attentamente i messaggi di errore
2. Controlla di aver seguito tutti i passi di installazione
3. Verifica che Python e pip siano installati correttamente
4. Assicurati di essere nella cartella giusta del progetto

## 📈 Possibili miglioramenti futuri

- Sistema di notifiche per nuove proposte
- Categorizzazione delle proposte
- Sistema di commenti
- Dashboard amministratore
- App mobile
- Sistema di scadenza proposte

---

**Grazie**

---
- Mauro [Ueiv27] Panzanaro
- Luca [Gay] Conte
- Michelangelo [Chimpmunk] Suarez
