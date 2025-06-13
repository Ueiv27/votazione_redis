# utils.py
def key_user_password(user_id):
    return f"user:{user_id}:password"

def key_user_votes(user_id):
    return f"user:{user_id}:votes"

def key_proposal_text(proposal_id):
    return f"proposal:{proposal_id}:text"

def key_proposal_votes_set(proposal_id):
    return f"proposal:{proposal_id}:votes"

def key_proposal_score(proposal_id):
    return f"proposal:{proposal_id}:score"

def get_user_id():
    corso = input("Che corso frequenti? (BD, ML) ")
    while True:
        numero = input("Qual è il tuo numero dell'elenco? ")
        if numero.isdigit() and 1 <= int(numero) <= 30:
            break
        print("Le classi sono composte da massimo 30 persone, inserisci un numero valido.")
    return f"{corso.strip().lower()}:{numero.strip()}"
