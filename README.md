# Sistema di Votazione con Redis

Un'applicazione da terminale per votare proposte scolastiche, usando Redis come database NoSQL.

## 📦 Struttura

- `main.py`: avvia il programma
- `auth.py`: login/registrazione utenti
- `logic.py`: gestione voti e classifica
- `utils.py`: funzioni ausiliarie e chiavi Redis
- `config_redis.py`: credenziali di accesso al DB
- `test_auth.py`: test di base per il modulo auth

## 🛠️ Requisiti

- Python 3.8+
- Redis (cloud o locale)
- Pacchetti Python: vedi `requirements.txt`

## 🚀 Avvio

1. Clona la repo o scarica i file
2. Inserisci le tue credenziali Redis in `config_redis.py`
3. Installa i pacchetti:
```bash
pip install -r requirements.txt
