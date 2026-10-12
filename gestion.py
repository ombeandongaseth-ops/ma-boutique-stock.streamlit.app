import sqlite3
import streamlit as st
import pandas as pd
import datetime

# --- CONFIGURATION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect("stock_mobile.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Table des produits
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prix REAL NOT NULL,
            quantite INTEGER NOT NULL
        )
    ''')
    
    # Table de gestion des licences / abonnements
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS abonnement (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_nom TEXT NOT NULL,
            date_expiration TEXT NOT NULL,
            statut TEXT NOT NULL
        )
    ''')
    
    # Insérer une licence par défaut si elle n'existe pas (pour les tests)
    cursor.execute("SELECT COUNT(*) FROM abonnement")
    if cursor.fetchone()[0] == 0:
        # Date d'expiration fixée par défaut à 30 jours plus tard
        date_exp_defaut = (datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO abonnement (client_nom, date_expiration, statut) VALUES (?, ?, ?)", 
                       ("Boutique Partenaire", date_exp_defaut, "Actif"))
        conn.commit()
        
    return conn, cursor

conn, cursor = init_db()

# --- VÉRIFICATION DE L'ABONNEMENT ---
def verifier_abonnement():
    cursor.execute("SELECT date_expiration, statut FROM abonnement LIMIT 1")
    ab_info = cursor.fetchone()
    
    if not ab_info:
        return False, "Aucune licence trouvée."
        
    date_exp_str, statut = ab_info
    date_exp = datetime.datetime.strptime(date_exp_str, "%Y-%m-%d").date()
    aujourdhui = datetime.date.today()
    
    if statut != "Actif" or aujourdhui > date_exp:
        return False, date_exp_str
    return True, date_exp_str

# --- INTERFACE PRINCIPALE ---
st.title("📱 GestionStock Mobile & Caisse Pro")

# Vérification du statut de l'abonnement
est_actif, info_exp = verifier_abonnement()

if not est_actif:
    st.error("⚠️ **Votre abonnement ou période d'essai a expiré !**")
    st.warning(f"Date limite dépassée (Expiré le : {info_exp}). L'accès aux fonctionnalités est suspendu.")
    
    st.markdown("### 💳 Comment renouveler ?")
    st.info("""
    Pour réactiver votre logiciel instantanément :
    1. Effectuez le paiement de l'abonnement mensuel par **Mobile Money** au numéro : `+242 XX XXX XXXX`
    2. Envoyez la capture du transfert ou contactez le support technique.
    3. Votre compte sera prolongé de 30 jours.
    """)
    
    # Espace Administrateur pour prolonger la licence (Utile pour vous ou pour tester)
    with st.expander("🔑 Espace Admin (Prolonger la licence)"):
        nouveau_jours = st.number_input("Ajouter des jours d'abonnement", min_value=1, value=30)
        if st.button("Prolonger la licence"):
            nouvelle_date = (datetime.date.today() + datetime.timedelta(days=nouveau_jours)).strftime("%Y-%m-%d")
            cursor.execute("UPDATE abonnement SET date_expiration = ?, statut = 'Actif'", (nouvelle_date,))
            conn.commit()
            st.success(f"Licence prolongée avec succès jusqu'au {nouvelle_date} !")
            st.rerun()
    
    st.stop() # Bloque l'exécution du reste de l'application si l'abonnement est inactif

# Si l'abonnement est actif, l'application s'ouvre normalement :
menu = st.sidebar.selectbox("Menu", ["Caisse & Vente", "Ajouter Produit", "Voir le Stock", "Mon Abonnement"])

if menu == "Ajouter Produit":
    st.header("➕ Ajouter un article")
    nom = st.text_input("Nom du produit")
    prix = st.number_input("Prix (FCFA)", min_value=0.0, step=100.0)
    qte = st.number_input("Quantité en stock", min_value=0, step=1)
    
    if st.button("Enregistrer"):
        if nom and prix > 0:
            cursor.execute("INSERT INTO produits (nom, prix, quantite) VALUES (?, ?, ?)", (nom, prix, qte))
            conn.commit()
            st.success(f"Produit '{nom}' ajouté avec succès !")
        else:
            st.error("Veuillez remplir correctement les champs.")

elif menu == "Caisse & Vente":
    st.header("🛒 Enregistrer une Vente")
    
    cursor.execute("SELECT id, nom, prix, quantite FROM produits")
    produits = cursor.fetchall()
    
    if not produits:
        st.warning("Aucun produit en stock pour l'instant. Ajoutez-en via le menu.")
    else:
        options_produits = {f"{p[1]} (Stock: {p[3]} - Prix: {p[2]} FCFA)": p for p in produits}
        choix = st.selectbox("Choisir un produit", list(options_produits.keys()))
        
        produit_selectionne = options_produits[choix]
        p_id, p_nom, p_prix, p_stock = produit_selectionne
        
        qte_achat = st.number_input("Quantité achetée", min_value=1, max_value=max(1, p_stock), step=1)
        
        if st.button("Valider la Vente"):
            nouveau_stock = p_stock - qte_achat
            cursor.execute("UPDATE produits SET quantite = ? WHERE id = ?", (nouveau_stock, p_id))
            conn.commit()
            
            total = p_prix * qte_achat
            st.success(f"✅ Vente validée !\n\nTotal à payer : **{total} FCFA**")
            st.balloons()

elif menu == "Voir le Stock":
    st.header("📦 État du Stock Actuel")
    cursor.execute("SELECT id, nom, prix, quantite FROM produits")
    data = cursor.fetchall()
    
    if data:
        df = pd.DataFrame(data, columns=["ID", "Nom", "Prix (FCFA)", "Quantité"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Le stock est vide.")

elif menu == "Mon Abonnement":
    st.header("📅 Gestion de votre Abonnement")
    cursor.execute("SELECT client_nom, date_expiration, statut FROM abonnement LIMIT 1")
    ab = cursor.fetchone()
    
    st.info(f"**Client :** {ab[0]}")
    st.success(f"**Statut du compte :** {ab[2]}")
    st.warning(f"**Date d'expiration :** {ab[1]}")
    
    st.write("Pour toute question concernant le renouvellement de votre licence, contactez le support technique.")
