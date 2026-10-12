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

# --- INITIALISATION DE LA BASE DE DONNÉES CENTRALE ---
def init_db():
    conn = sqlite3.connect("plateforme_saas.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Table des utilisateurs / commerçants abonnés
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
    
    # Table des produits (liée à l'utilisateur via user_id)
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

# Fonction de hashage simple pour sécuriser le mot de passe
def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- GESTION DE LA SESSION DE CONNEXION ---
if 'user' not in st.session_state:
    st.session_state['user'] = None

# ==================== PAGE DE CONNEXION / INSCRIPTION ====================
if st.session_state['user'] is None:
    st.title("🔐 Plateforme SaaS - GestionStock Pro")
    st.write("Connectez-vous à votre espace commerçant ou créez votre compte.")
    
    choix_auth = st.selectbox("Action", ["Connexion", "Créer un compte commerçant"])
    
    if choix_auth == "Connexion":
        with st.form("form_login"):
            username = st.text_input("Identifiant (ex: nom de votre boutique)").strip()
            password = st.text_input("Mot de passe", type="password")
            submit_login = st.form_submit_button("Se connecter")
            
            if submit_login:
                cursor.execute("SELECT id, nom_boutique, username, password, date_expiration, statut FROM utilisateurs WHERE username = ?", (username,))
                user_data = cursor.fetchone()
                
                if user_data and user_data[3] == make_hash(password):
                    # Vérifier si l'abonnement est actif
                    date_exp = datetime.datetime.strptime(user_data[4], "%Y-%m-%d").date()
                    if user_data[5] == "Actif" and datetime.date.today() <= date_exp:
                        st.session_state['user'] = {
                            "id": user_data[0],
                            "boutique": user_data[1],
                            "username": user_data[2]
                        }
                        st.success("Connexion réussie ! Chargement...")
                        st.rerun()
                    else:
                        st.error("⚠️ Votre abonnement a expiré. Veuillez régler votre abonnement par Mobile Money pour réactiver l'accès.")
                else:
                    st.error("Identifiant ou mot de passe incorrect.")
                    
    else:
        with st.form("form_signup"):
            st.info("🎁 Profitez de 7 jours d'essai gratuit à l'inscription !")
            nom_boutique = st.text_input("Nom de votre boutique").strip()
            username = st.text_input("Choisissez un identifiant unique").strip()
            password = st.text_input("Mot de passe", type="password")
            submit_signup = st.form_submit_button("S'inscrire")
            
            if submit_signup:
                if nom_boutique and username and password:
                    try:
                        # Offrir 7 jours d'essai gratuit par défaut
                        date_essai = (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
                        hashed_pw = make_hash(password)
                        
                        cursor.execute("INSERT INTO utilisateurs (nom_boutique, username, password, date_expiration, statut) VALUES (?, ?, ?, ?, ?)",
                                       (nom_boutique, username, hashed_pw, date_essai, "Actif"))
                        conn.commit()
                        st.success("Compte créé avec succès ! Vous pouvez maintenant vous connecter dans l'onglet Connexion.")
                    except sqlite3.IntegrityError:
                        st.error("Cet identifiant existe déjà. Choisissez-en un autre.")
                else:
                    st.error("Veuillez remplir tous les champs.")
    
    st.stop() # Arrête l'affichage si l'utilisateur n'est pas connecté

# ==================== APPLICATION PRINCIPALE (UTILISATEUR CONNECTÉ) ====================
user = st.session_state['user']
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

# ==================== 1. TABLEAU DE BORD ====================
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
    col3.metric("⚠️ Produits en Alerte Stock", f"{alertes_stock}")

    st.markdown("---")
    if alertes_stock > 0:
        st.warning(f"🚨 Attention : {alertes_stock} produit(s) ont un stock critique (≤ 5).")

    st.subheader("📈 Ventes par article")
    cursor.execute("SELECT produit, SUM(quantite) FROM ventes WHERE user_id = ? GROUP BY produit", (user_id,))
    data_v = cursor.fetchall()
    if data_v:
        df_v = pd.DataFrame(data_v, columns=["Produit", "Quantité"]).set_index("Produit")
        st.bar_chart(df_v)
    else:
        st.info("Aucune vente enregistrée.")

# ==================== 2. CAISSE & VENTES ====================
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

# ==================== 3. GESTION DES STOCKS ====================
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

# ==================== 4. CARNET DE CRÉDITS ====================
elif menu == "📝 Carnet de Crédits":
    st.header("📝 Ardoises & Crédits")
    tab1, tab2 = st.tabs(["Nouveau Crédit", "Suivi"])
    with tab1:
        with st.form("form_cred"):
            client = st.text_input("Nom du client")
            montant = st.number_input("Montant (FCFA)", min_value=0.0)
            motif = st.text_input("Motif")
            if st.form_submit_button("Enregistrer") and client and montant > 0:
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

# ==================== 5. MON ABONNEMENT ====================
elif menu == "📅 Mon Abonnement":
    st.header("📅 Gestion de votre Abonnement")
    cursor.execute("SELECT nom_boutique, date_expiration, statut FROM utilisateurs WHERE id = ?", (user_id,))
    ab = cursor.fetchone()
    
    st.info(f"**Boutique :** {ab[0]}")
    st.success(f"**Statut :** {ab[2]}")
    st.warning(f"**Date d'expiration :** {ab[1]}")
    
    st.markdown("### 💳 Comment renouveler ?")
    st.write("Effectuez votre paiement par **Mobile Money** et contactez l'administrateur pour prolonger votre accès de 30 jours.")
