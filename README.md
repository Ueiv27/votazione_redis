# Premessa:
Prova per familiarizzare con github. Si tratta di un semplice script python che gestisce un piccolo server redis. Per comodità, **ho lasciato di proposito tutte le informazioni "private" per accedervi.**

Sappiate che se userete le mie credenziali, tutti i cambiamenti avverranno sul mio cloud server redis, e non potrete vederli con redis insight ma solo facendo richieste al server tramite codice. Perciò se volete giocarci e fare casino, mettete le vostre.


# Sistema di Votazione NoSQL con Redis

Questo progetto implementa un semplice sistema di votazione per proposte utilizzando Redis come database NoSQL. Permette agli utenti di inserire proposte, votarle e visualizzare una classifica delle proposte più votate. È pensato come un esempio didattico per mostrare come utilizzare Redis in un'applicazione reale.

---

### Caratteristiche

* **Autenticazione Utente:** Gli utenti sono identificati tramite corso e numero di elenco.
* **Gestione Proposte:** Gli utenti possono inserire nuove proposte.
* **Votazione:** Gli utenti possono votare le proposte. È presente un limite massimo di voti per utente.
* **Classifica:** Visualizzazione delle proposte ordinate per numero di voti.
* **Ottimizzazioni Redis:** Utilizzo di pipeline per l'atomicità delle operazioni, gestione efficiente degli ID delle proposte e recupero ottimizzato dei dati per la classifica.

---

### Prerequisiti

* **Python 3.x**
* **Redis Server** (assicurati che sia in esecuzione e accessibile, anche se remoto)
* Libreria Python **`redis-py`** (installabile con `pip install redis`)

---

### Configurazione

1.  **Clona il repository:**

    ```bash
    git clone [https://github.com/Ueiv27/votazione_redis.git](https://github.com/Ueiv27/votazione_redis.git)
    cd votazione_redis
    ```
2.  **Configura le credenziali di Redis:**
    * Sia nel file principale del sistema di votazione (`votazione_2.py`) che nello script di popolamento dati (`popola_redis2.py`), modifica le seguenti variabili con le tue credenziali Redis. **È fondamentale che siano le stesse in entrambi i file!**

        ```python
        username = "default"  # o il tuo username
        password = "O9uv1t8Sxp93vkDYnnHX6NOhN953ZlZw"  # o la tua password
        host = 'redis-15081.crce198.eu-central-1-3.ec2.redns.redis-cloud.com'
        port = 15081
        ```

---

### Utilizzo

#### 1. Popolamento del Database (Iniziale)

Prima di avviare il sistema di votazione, è consigliabile popolare il database con alcune proposte e voti di esempio. Lo script `popola_redis2.py` è stato creato proprio per questo.

1.  Assicurati che Redis sia attivo e che le credenziali in `popola_redis2.py` siano corrette.
2.  Esegui lo script di seeding:

    ```bash
    python popola_redis2.py
    ```

    Questo script pulirà le chiavi dell'applicazione da Redis e inserirà un set di proposte e voti predefiniti, permettendoti di testare le funzionalità immediatamente.

#### 2. Avvio del Sistema di Votazione

Una volta popolato il database:

1.  Assicurati che Redis sia attivo e che le credenziali nel tuo script principale (`votazione_2.py`) siano corrette.
2.  Esegui lo script principale:

    ```bash
    python votazione_2.py
    ```

    Segui le istruzioni a menu per interagire con il sistema (votare, inserire nuove proposte, visualizzare la classifica).

---

### Struttura del Database Redis

Di seguito sono elencate le chiavi Redis utilizzate e il loro scopo:

* `proposals:id_counter`: Un **Counter** (String incrementabile) utilizzato per generare ID univoci per ogni nuova proposta.
* `proposals`: Un **Hash** che memorizza i testi delle proposte, mappando l'ID della proposta al suo testo (`ID proposta => testo della proposta`).
* `user:votes`: Un **Hash** che tiene traccia del numero totale di voti espressi da ciascun utente (`user_id => numero di voti`).
* `proposal:votes:{proposal_id}`: Un **Set** per ogni proposta, che memorizza gli `user_id` di tutti gli utenti che hanno votato quella specifica proposta. Questo impedisce voti doppi.
* `leaderboard`: Un **Sorted Set** che memorizza le proposte e il loro punteggio (numero di voti), permettendo di ottenere rapidamente la classifica. Il punteggio è il numero di voti e il membro è l'ID della proposta (`ID proposta => punteggio`).

---

### Autori

* Ueiv27
* Luca (gay) Conte
* Michelangelo (chimpmunk) Suarez
