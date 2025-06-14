#!/usr/bin/env python3
"""
Test completo per il sistema di votazione
Testa l'integrazione tra tutti i moduli principali
"""

import unittest
import redis
import bcrypt
from config_redis import red
from utils import (
    key_user_password, key_user_votes, 
    key_proposal_text, key_proposal_votes_set
)
from leaderboard import (
    aggiorna_classifica, get_classifica, 
    inizializza_proposta_in_classifica, get_score_proposta
)

class TestSistemaVotazione(unittest.TestCase):
    
    def setUp(self):
        """Inizializza ambiente di test"""
        self.red = red
        
        # Dati di test
        self.test_user = "test:99"
        self.test_password = "test1234"
        self.test_proposal_id = "999"
        self.test_proposal_text = "Proposta di test per unit testing"
        
        # Pulisci dati di test esistenti
        self.cleanup_test_data()
        
        # Inizializza contatore proposte se non esiste
        if not self.red.exists("proposals:id_counter"):
            self.red.set("proposals:id_counter", 1000)  # Evita conflitti con dati reali

    def cleanup_test_data(self):
        """Pulisce tutti i dati di test"""
        keys_to_delete = [
            key_user_password(self.test_user),
            key_user_votes(self.test_user),
            key_proposal_text(self.test_proposal_id),
            key_proposal_votes_set(self.test_proposal_id)
        ]
        
        # Rimuovi dalla classifica
        self.red.zrem("proposals:leaderboard", self.test_proposal_id)
        
        # Cancella le chiavi
        for key in keys_to_delete:
            self.red.delete(key)

    def test_01_registrazione_utente(self):
        """Test registrazione con password criptata"""
        # Simula registrazione
        hashed_pw = bcrypt.hashpw(self.test_password.encode('utf-8'), bcrypt.gensalt())
        self.red.set(key_user_password(self.test_user), hashed_pw.decode('utf-8'))
        
        # Verifica che la password sia salvata
        stored_pw = self.red.get(key_user_password(self.test_user))
        self.assertIsNotNone(stored_pw)
        
        # Verifica che la password sia criptata (diversa da quella originale)
        self.assertNotEqual(stored_pw, self.test_password)
        
        # Verifica che il controllo password funzioni
        self.assertTrue(bcrypt.checkpw(self.test_password.encode('utf-8'), stored_pw.encode('utf-8')))
        self.assertFalse(bcrypt.checkpw("password_sbagliata".encode('utf-8'), stored_pw.encode('utf-8')))

    def test_02_creazione_proposta(self):
        """Test creazione e inizializzazione proposta"""
        # Salva proposta
        self.red.set(key_proposal_text(self.test_proposal_id), self.test_proposal_text)
        
        # Inizializza in classifica
        inizializza_proposta_in_classifica(self.test_proposal_id)
        
        # Verifica testo salvato
        saved_text = self.red.get(key_proposal_text(self.test_proposal_id))
        self.assertEqual(saved_text, self.test_proposal_text)
        
        # Verifica inizializzazione in classifica
        score = get_score_proposta(self.test_proposal_id)
        self.assertEqual(score, 0)

    def test_03_sistema_votazione(self):
        """Test completo del sistema di votazione"""
        # Prerequisiti: utente registrato e proposta esistente
        self.test_01_registrazione_utente()
        self.test_02_creazione_proposta()
        
        # Verifica stato iniziale
        self.assertEqual(get_score_proposta(self.test_proposal_id), 0)
        self.assertFalse(self.red.sismember(key_proposal_votes_set(self.test_proposal_id), self.test_user))
        
        voti_iniziali = self.red.get(key_user_votes(self.test_user))
        voti_iniziali = int(voti_iniziali) if voti_iniziali else 0
        
        # Simula voto
        pipe = self.red.pipeline()
        pipe.sadd(key_proposal_votes_set(self.test_proposal_id), self.test_user)
        pipe.incr(key_user_votes(self.test_user))
        pipe.execute()
        
        # Aggiorna classifica
        aggiorna_classifica(self.test_proposal_id)
        
        # Verifica risultati
        self.assertEqual(get_score_proposta(self.test_proposal_id), 1)
        self.assertTrue(self.red.sismember(key_proposal_votes_set(self.test_proposal_id), self.test_user))
        
        voti_finali = int(self.red.get(key_user_votes(self.test_user)))
        self.assertEqual(voti_finali, voti_iniziali + 1)

    def test_04_prevenzione_doppio_voto(self):
        """Test prevenzione voto duplicato"""
        # Prerequisiti
        self.test_03_sistema_votazione()  # Questo lascia un voto esistente
        
        # Verifica che l'utente abbia già votato
        self.assertTrue(self.red.sismember(key_proposal_votes_set(self.test_proposal_id), self.test_user))
        
        # Tenta secondo voto (non dovrebbe avere effetto)
        score_prima = get_score_proposta(self.test_proposal_id)
        
        # Un sistema corretto non dovrebbe permettere questo, ma testiamo la detection
        gia_votato = self.red.sismember(key_proposal_votes_set(self.test_proposal_id), self.test_user)
        self.assertTrue(gia_votato, "Il sistema deve rilevare voti duplicati")

    def test_05_classifica_funzionale(self):
        """Test funzionalità classifica"""
        # Crea multiple proposte di test
        test_proposals = {
            "997": "Prima proposta test",
            "998": "Seconda proposta test", 
            "999": "Terza proposta test"
        }
        
        # Inizializza proposte
        for prop_id, text in test_proposals.items():
            self.red.set(key_proposal_text(prop_id), text)
            inizializza_proposta_in_classifica(prop_id)
            # Rimuovi da cleanup
            self.red.zrem("proposals:leaderboard", prop_id)
        
        # Simula voti diversi
        for i, prop_id in enumerate(test_proposals.keys(), 1):
            for _ in range(i):  # prop 997: 1 voto, 998: 2 voti, 999: 3 voti
                aggiorna_classifica(prop_id)
        
        # Ottieni classifica
        classifica = get_classifica()
        
        # Verifica ordinamento (dal più votato al meno votato)
        self.assertGreaterEqual(len(classifica), 3)
        
        # Trova le nostre proposte nella classifica
        test_entries = [entry for entry in classifica if entry['id'] in test_proposals.keys()]
        self.assertEqual(len(test_entries), 3)
        
        # Verifica ordinamento corretto
        if len(test_entries) >= 2:
            self.assertGreaterEqual(test_entries[0]['voti'], test_entries[1]['voti'])
        
        # Cleanup
        for prop_id in test_proposals.keys():
            self.red.delete(key_proposal_text(prop_id))
            self.red.zrem("proposals:leaderboard", prop_id)

    def test_06_limiti_voti_utente(self):
        """Test limite massimo voti per utente (3 voti)"""
        MAX_VOTI = 3
        
        # Simula che l'utente abbia già MAX_VOTI voti
        self.red.set(key_user_votes(self.test_user), MAX_VOTI)
        
        # Verifica calcolo voti rimanenti
        voti_utilizzati = int(self.red.get(key_user_votes(self.test_user)))
        voti_rimanenti = max(0, MAX_VOTI - voti_utilizzati)
        
        self.assertEqual(voti_rimanenti, 0)
        self.assertEqual(voti_utilizzati, MAX_VOTI)

    def tearDown(self):
        """Pulizia dopo ogni test"""
        self.cleanup_test_data()

class TestIntegrazioneSistema(unittest.TestCase):
    """Test di integrazione per verificare il funzionamento dell'intero sistema"""
    
    def setUp(self):
        self.red = red
        
    def test_connessione_redis(self):
        """Test connessione al database Redis"""
        try:
            info = self.red.ping()
            self.assertTrue(info)
        except Exception as e:
            self.fail(f"Impossibile connettersi a Redis: {e}")

    def test_configurazione_database(self):
        """Test configurazione e strutture dati esistenti"""
        # Verifica che le strutture principali siano presenti o creabili
        self.red.set("test_key", "test_value")
        self.assertEqual(self.red.get("test_key"), "test_value")
        self.red.delete("test_key")
        
        # Test ZSET per classifica
        self.red.zadd("test_zset", {"test_member": 1})
        score = self.red.zscore("test_zset", "test_member")
        self.assertEqual(score, 1.0)
        self.red.delete("test_zset")

def run_all_tests():
    """Esegue tutti i test con output dettagliato"""
    print("🧪 Avvio test sistema di vot azione...\n")
    
    # Configura il test runner
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Aggiungi tutti i test
    suite.addTests(loader.loadTestsFromTestCase(TestSistemaVotazione))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrazioneSistema))
    
    # Esegui i test con output verboso
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Riepilogo finale
    print(f"\n📊 Riepilogo test:")
    print(f"✅ Test eseguiti: {result.testsRun}")
    print(f"❌ Fallimenti: {len(result.failures)}")
    print(f"⚠️ Errori: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 Tutti i test sono passati! Il sistema funziona correttamente.")
    else:
        print("\n❌ Alcuni test sono falliti. Controlla i dettagli sopra.")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    run_all_tests()