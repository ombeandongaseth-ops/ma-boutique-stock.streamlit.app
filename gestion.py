import sqlite3
import streamlit as st
import pandas as pd
import datetime
import hashlib

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="SaaS GestionStock Pro",
    page_icon="📦",
    layout="wide"
)

# --- INITIALISATION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect("plateforme_saas.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Table des utilisateurs / commerçants
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_boutique TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            date_expiration TEXT NOT NULL,
            statut TEXT NOT NULL
        )
    ''')
    
    # Table des produits
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            nom TEXT NOT NULL,
            prix REAL NOT NULL,
            quantite INTEGER NOT NULL
        )
    ''')
    
    # Table des ventes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            produit TEXT NOT NULL,
            prix_unitaire REAL NOT NULL,
            quantite INTEGER NOT NULL,
            total REAL NOT NULL,
            date_vente TEXT NOT NULL
        )
    ''')

    # Table des crédits
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            client_nom TEXT NOT NULL,
            montant REAL NOT NULL,
            motif TEXT NOT NULL,
            date_credit TEXT NOT NULL,
            statut TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    return conn, cursor

conn, cursor = init_db()

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# Gestion de la session
if 'user' not in st.session_state:
    st.session_state['user'] = None

# ==================== PAGE DE CONNEXION / INSCRIPTION ====================
if st.session_state['user'] is None:
    st.title("🔐 GestionStock Pro - Espace Connexion")
    
    # Vos coordonnées affichées pour que les clients sachent comment vous joindre
    st.sidebar.markdown("### 📞 Support & Paiement")
    st.sidebar.info("""
    Besoin d'aide ou d'activer votre compte ?
    * **WhatsApp / Mobile Money :** `+242 XX XXX XXXX`
    * **Développeur :** Votre Nom / Support Technique
    """)

    choix_auth = st.selectbox("Action", ["Connexion", "Créer un compte commerçant", "🔑 Accès Administrateur (Développeur)"])
    
    if choix_auth == "Connexion":
        with st.form("form_login"):
            username = st.text_input("Identifiant (Nom de votre boutique)").strip()
            password = st.text_input("Mot de passe", type="password")
            submit_login = st.form_submit_button("Se connecter")
            
            if submit_login:
                cursor.execute("SELECT id, nom_boutique, username, password, date_expiration, statut FROM utilisateurs WHERE username = ?", (username,))
                user_data = cursor.fetchone()
                
                if user_data and user_data[3] == make_hash(password):
                    date_exp = datetime.datetime.strptime(user_data[4], "%Y-%m-%d").date()
                    if user_data[5] == "Actif" and datetime.date.today() <= date_exp:
                        st.session_state['user'] = {
                            "id": user_data[0],
                            "boutique": user_data[1],
                            "username": user_data[2]
                        }
                        st.success("Connexion réussie !")
                        st.rerun()
                    else:
                        st.error("⚠️ Votre abonnement a expiré. Veuillez contacter le support pour renouveler.")
                else:
                    st.error("Identifiant ou mot de passe incorrect.")
                    
    elif choix_auth == "Créer un compte commerçant":
        with st.form("form_signup"):
            st.info("🎁 7 jours d'essai offerts à l'inscription !")
            nom_boutique = st.text_input("Nom de votre boutique").strip()
            username = st.text_input("Choisissez un identifiant unique").strip()
            password = st.text_input("Mot de passe", type="password")
            submit_signup = st.form_submit_button("S'inscrire et se connecter")
            
            if submit_signup:
                if nom_boutique and username and password:
                    try:
                        date_essai = (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
                        hashed_pw = make_hash(password)
                        
                        cursor.execute("INSERT INTO utilisateurs (nom_boutique, username, password, date_expiration, statut) VALUES (?, ?, ?, ?, ?)",
                                       (nom_boutique, username, hashed_pw, date_essai, "Actif"))
                        conn.commit()
                        
                        # Connexion automatique immédiate après l'inscription
                        cursor.execute("SELECT id, nom_boutique, username FROM utilisateurs WHERE username = ?", (username,))
                        new_user = cursor.fetchone()
                        st.session_state['user'] = {
                            "id": new_user[0],
                            "boutique": new_user[1],
                            "username": username
                        }
                        st.success("Compte créé avec succès ! Redirection...")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Cet identifiant existe déjà. Choisissez-en un autre.")
                else:
                    st.error("Veuillez remplir tous les champs.")
                    
    else:
        # --- ESPACE ADMIN POUR VOUS (LE DÉVELOPPEUR) ---
        with st.form("form_admin"):
            st.subheader("🛠️ Panneau d'administration de la plateforme")
            admin_code = st.text_input("Code secret administrateur", type="password")
            sub_admin = st.form_submit_button("Accéder au panneau")
            
            if sub_admin:
                # Mettez ici votre mot de passe secret de développeur
                if admin_code == "admin1234": 
                    st.session_state['user'] = {"id": 9999, "boutique": "ADMINISTRATION", "username": "admin"}
                    st.rerun()
                else:
                    st.error("Code administrateur incorrect.")
                    
    st.stop()

# ==================== SI VOUS ÊTES CONNECTÉ EN TANT QU'ADMIN ====================
user = st.session_state['user']
if user['id'] == 9999:
    st.title("👑 Panneau de Contrôle Administrateur")
    if st.button("Se déconnecter de l'admin"):
        st.session_state['user'] = None
        st.rerun()
        
    st.subheader("Liste de tous les commerçants abonnés")
    cursor.execute("SELECT id, nom_boutique, username, date_expiration, statut FROM utilisateurs")
    clients = cursor.fetchall()
    
    if clients:
        df_clients = pd.DataFrame(clients, columns=["ID", "Boutique", "Identifiant", "Expiration", "Statut"])
        st.dataframe(df_clients, use_container_width=True, hide_index=True)
        
        st.markdown("### 🔄 Prolonger l'abonnement d'un client")
        c_id = st.number_input("ID du client à prolonger", min_value=1, step=1)
        jours_plus = st.number_input("Nombre de jours à ajouter", min_value=1, value=30)
        
        if st.button("Valider la prolongation"):
            # Calculer la nouvelle date d'expiration
            cursor.execute("SELECT date_expiration FROM utilisateurs WHERE id = ?", (c_id,))
            res = cursor.fetchone()
            if res:
                date_actuelle_exp = datetime.datetime.strptime(res[0], "%Y-%m-%d").date()
                base_date = max(date_actuelle_exp, datetime.date.today())
                nouvelle_exp = (base_date + datetime.timedelta(days=jours_plus)).strftime("%Y-%m-%d")
                
                cursor.execute("UPDATE utilisateurs SET date_expiration = ?, statut = 'Actif' WHERE id = ?", (nouvelle_exp, c_id))
                conn.commit()
                st.success(f"Abonnement du client ID {c_id} prolongé jusqu'au {nouvelle_exp} !")
                st.rerun()
    else:
        st.info("Aucun commerçant inscrit pour le moment.")
    st.stop()

# ==================== APPLICATION PRINCIPALE (COMMERÇANT) ====================
user_id = user['id']

st.sidebar.title(f"🏪 {user['boutique']}")
if st.sidebar.button("Déconnexion"):
    st.session_state['user'] = None
    st.rerun()

menu = st.sidebar.radio("Navigation", [
    "📊 Tableau de Bord", 
    "🛒 Caisse & Ventes", 
    "📦 Gestion des Stocks", 
    "📝 Carnet de Crédits", 
    "📅 Mon Abonnement"
])

# 1. TABLEAU DE BORD
if menu == "📊 Tableau de Bord":
    st.header("📊 Vue d'ensemble de votre activité")
    cursor.execute("SELECT SUM(total) FROM ventes WHERE user_id = ?", (user_id,))
    ca_total = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT COUNT(*) FROM ventes WHERE user_id = ?", (user_id,))
    nb_ventes = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM produits WHERE user_id = ? AND quantite <= 5", (user_id,))
    alertes_stock = cursor.fetchone()[0] or 0

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Chiffre d'Affaires", f"{ca_total:,.0f} FCFA")
    col2.metric("🛍️ Total des Ventes", f"{nb_ventes}")
    col3.metric("⚠️ Alerte Stock", f"{alertes_stock}")

    st.markdown("---")
    if alertes_stock > 0:
        st.warning(f"🚨 Attention : {alertes_stock} produit(s) ont un stock critique (≤ 5).")

# 2. CAISSE & VENTES
elif menu == "🛒 Caisse & Ventes":
    st.header("🛒 Caisse Enregistreuse")
    cursor.execute("SELECT id, nom, prix, quantite FROM produits WHERE user_id = ?", (user_id,))
    produits = cursor.fetchall()
    
    if not produits:
        st.warning("Votre stock est vide. Ajoutez des produits.")
    else:
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            options = {f"{p[1]} (Stock: {p[3]} | Prix: {p[2]:,.0f} FCFA)": p for p in produits}
            choix = st.selectbox("Choisir un produit", list(options.keys()))
            p_id, p_nom, p_prix, p_stock = options[choix]
            
            qte_achat = st.number_input("Quantité", min_value=1, max_value=max(1, p_stock), step=1)
            total = p_prix * qte_achat
            st.info(f"Total : **{total:,.0f} FCFA**")
            
            if st.button("Valider la Vente", type="primary"):
                cursor.execute("UPDATE produits SET quantite = ? WHERE id = ?", (p_stock - qte_achat, p_id))
                cursor.execute("INSERT INTO ventes (user_id, produit, prix_unitaire, quantite, total, date_vente) VALUES (?, ?, ?, ?, ?, ?)",
                               (user_id, p_nom, p_prix, qte_achat, total, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success("Vente enregistrée avec succès !")
                st.balloons()
        with col_c2:
            st.markdown("### Stock Rapide")
            st.dataframe(pd.DataFrame(produits, columns=["ID", "Nom", "Prix", "Stock"])[["Nom", "Stock"]], hide_index=True, use_container_width=True)

# 3. GESTION DES STOCKS
elif menu == "📦 Gestion des Stocks":
    st.header("📦 Gestion de vos Stocks")
    tab1, tab2 = st.tabs(["Ajouter", "Voir & Exporter"])
    with tab1:
        with st.form("form_p"):
            nom = st.text_input("Nom du produit")
            prix = st.number_input("Prix (FCFA)", min_value=0.0, step=100.0)
            qte = st.number_input("Quantité", min_value=0, step=1)
            if st.form_submit_button("Ajouter") and nom and prix > 0:
                cursor.execute("INSERT INTO produits (user_id, nom, prix, quantite) VALUES (?, ?, ?, ?)", (user_id, nom, prix, qte))
                conn.commit()
                st.success("Produit ajouté !")
    with tab2:
        cursor.execute("SELECT id, nom, prix, quantite FROM produits WHERE user_id = ?", (user_id,))
        data = cursor.fetchall()
        if data:
            df = pd.DataFrame(data, columns=["ID", "Nom", "Prix", "Stock"])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("Télécharger l'inventaire (CSV)", df.to_csv(index=False).encode('utf-8'), "inventaire.csv", "text/csv")
        else:
            st.info("Aucun produit.")

# 4. CARNET DE CRÉDITS
elif menu == "📝 Carnet de Crédits":
    st.header("📝 Ardoises & Crédits")
    tab1, tab2 = st.tabs(["Nouveau Crédit", "Suivi"])
    with tab1:
        with st.form("form_cred"):
            client = st.text_input("Nom du client")
            montant = st.number_input("Montant (FCFA)", min_value=0.0)
            motif = st.text_input("Motif")
            if st.form_submit_button("Enregistrer")and client and montant > 0:
                cursor.execute("INSERT INTO credits (user_id, client_nom, montant, motif, date_credit, statut) VALUES (?, ?, ?, ?, ?, ?)",
                               (user_id, client, montant, motif, datetime.datetime.now().strftime("%Y-%m-%d"), "Impayé"))
                conn.commit()
                st.success("Crédit enregistré !")
    with tab2:
        cursor.execute("SELECT id, client_nom, montant, motif, date_credit, statut FROM credits WHERE user_id = ?", (user_id,))
        c_data = cursor.fetchall()
        if c_data:
            st.dataframe(pd.DataFrame(c_data, columns=["ID", "Client", "Montant", "Motif", "Date", "Statut"]), hide_index=True, use_container_width=True)
            c_id = st.number_input("ID du crédit réglé", min_value=1, step=1)
            if st.button("Marquer comme Payé"):
                cursor.execute("UPDATE credits SET statut = 'Payé' WHERE id = ? AND user_id = ?", (c_id, user_id))
                conn.commit()
                st.success("Mis à jour !")
                st.rerun()
        else:
            st.info("Aucun crédit.")

# 5. MON ABONNEMENT
elif menu == "📅 Mon Abonnement":
    st.header("📅 Gestion de votre Abonnement")
    cursor.execute("SELECT nom_boutique, date_expiration, statut FROM utilisateurs WHERE id = ?", (user_id,))
    ab = cursor.fetchone()
    
    st.info(f"**Boutique :** {ab[0]}")
    st.success(f"**Statut :** {ab[2]}")
    st.warning(f"**Date d'expiration :** {ab[1]}")
    
    st.markdown("### 💳 Comment renouveler ?")
    st.write("""
    Pour renouveler votre abonnement :
    1. Effectuez le paiement par **Mobile Money** au numéro : `+242 XX XXX XXXX`
    2. Envoyez une capture du transfert au support technique par WhatsApp avec le nom de votre boutique.
    3. Votre compte sera prolongé de 30 jours rapidement.
    """)
