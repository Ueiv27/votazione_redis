# main.py
from auth import login_utente, registra_utente
from logic import menu, vota_proposta, proponi_proposta, classifica, conta_voti_per_corso

import sys

def main():
    print("Benvenuto nel sistema di votazione NoSQL!")
    user_id = None

    while not user_id:
        print("\n1. Login")
        print("2. Registrati")
        print("e. Esci")
        scelta = input("Scegli un'opzione: ").strip().lower()

        if scelta == "1":
            user_id = login_utente()
        elif scelta == "2":
            user_id = registra_utente()
        elif scelta == "e":
            print("Arrivederci!")
            sys.exit(0)
        else:
            print("Scelta non valida, riprova.")

    print(f"\nCiao {user_id}!")
    while True:
        scelta = menu()
        if scelta == "1":
            vota_proposta(user_id)
        elif scelta == "2":
            proponi_proposta()
        elif scelta == "3":
            classifica()
        elif scelta == "4":
            corso_da_cercare = input("Di quale corso vuoi analizzare i voti? (es. bd, ml) ")
            if corso_da_cercare.strip():
                conta_voti_per_corso(corso_da_cercare)
            else:
                print("Errore: Devi inserire un nome per il corso.")
        elif scelta == "e":
            print("Arrivederci!")
            sys.exit(0)
        else:
            print("Scelta non valida, riprova.")

if __name__ == "__main__":
    main()
