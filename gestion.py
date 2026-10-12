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

    # Table des annonces / notifications globales de l'admin (Seth Prod)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS annonces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            contenu TEXT NOT NULL,
            date_annonce TEXT NOT NULL
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
    
    st.sidebar.markdown("### 📞 Support & Paiement")
    st.sidebar.info("""
    Besoin d'aide ou d'activer votre compte ?
    * **Développeur :** Seth Prod
    * **WhatsApp / Mobile Money :** `053119132`
    """)

    choix_auth = st.selectbox("Action", ["Connexion", "Créer un compte commerçant"])
    
    if choix_auth == "Connexion":
        with st.form("form_login"):
            username = st.text_input("Identifiant (Nom de votre boutique)").strip()
            password = st.text_input("Mot de passe", type="password")
            submit_login = st.form_submit_button("Se connecter")
            
            if submit_login:
                # Vérification Admin Seth
                if username == "adminseth" and password == "admin2309":
                    st.session_state['user'] = {"id": 9999, "boutique": "ADMINISTRATION", "username": "adminseth"}
                    st.success("Connexion Admin réussie !")
                    st.rerun()
                
                # Connexion commerçant classique
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
                        st.error("⚠️ Votre abonnement a expiré. Veuillez contacter Seth Prod au 053119132 pour renouveler.")
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
                if username == "adminseth":
                    st.error("Cet identifiant est réservé.")
                elif nom_boutique and username and password:
                    try:
                        date_essai = (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
                        hashed_pw = make_hash(password)
                        
                        cursor.execute("INSERT INTO utilisateurs (nom_boutique, username, password, date_expiration, statut) VALUES (?, ?, ?, ?, ?)",
                                       (nom_boutique, username, hashed_pw, date_essai, "Actif"))
                        conn.commit()
                        
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
                    
    st.stop()

# ==================== PANNEAU ADMINISTRATEUR (SETH PROD) ====================
user = st.session_state['user']
if user['id'] == 9999:
    st.title("👑 Panneau de Contrôle - Seth Prod")
    if st.button("Se déconnecter de l'admin"):
        st.session_state['user'] = None
        st.rerun()
        
    tab_adm1, tab_adm2 = st.tabs(["👥 Gestion des Abonnés", "📢 Publier une Notification / Nouveauté"])
    
    with tab_adm1:
        st.subheader("Liste de tous les commerçants abonnés")
        cursor.execute("SELECT id, nom_boutique, username, date_expiration, statut FROM utilisateurs")
        clients = cursor.fetchall()
        
        if clients:
            df_clients = pd.DataFrame(clients, columns=["ID", "Boutique", "Identifiant", "Expiration", "Statut"])
            st.dataframe(df_clients, use_container_width=True, hide_index=True)
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("### 🔄 Prolonger un abonnement")
                c_id = st.number_input("ID du client à prolonger", min_value=1, step=1, key="p_id")
                jours_plus = st.number_input("Nombre de jours à ajouter", min_value=1, value=30, key="p_jours")
                
                if st.button("Valider la prolongation"):
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
            
            with col_b:
                st.markdown("### 🗑️ Nettoyage des inactifs")
                st.write("Supprimer automatiquement les comptes dont l'abonnement a expiré depuis plus d'une semaine.")
                if st.button("Supprimer les inactifs (> 7 jours)", type="primary"):
                    date_limite = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
                    cursor.execute("SELECT id, nom_boutique FROM utilisateurs WHERE date_expiration < ?", (date_limite,))
                    inactifs = cursor.fetchall()
                    
                    if inactifs:
                        for ina in inactifs:
                            uid = ina[0]
                            # Supprimer l'utilisateur et ses données associées
                            cursor.execute("DELETE FROM utilisateurs WHERE id = ?", (uid,))
                            cursor.execute("DELETE FROM produits WHERE user_id = ?", (uid,))
                            cursor.execute("DELETE FROM ventes WHERE user_id = ?", (uid,))
                            cursor.execute("DELETE FROM credits WHERE user_id = ?", (uid,))
                        conn.commit()
                        st.success(f"{len(inactifs)} compte(s) inactif(s) supprimé(s) avec succès !")
                        st.rerun()
                    else:
                        st.info("Aucun compte inactif de plus d'une semaine trouvé.")
        else:
            st.info("Aucun commerçant inscrit.")

    with tab_adm2:
        st.subheader("Diffusez une notification ou une mise à jour")
        with st.form("form_annonce"):
            titre_notif = st.text_input("Titre de la nouveauté / notification")
            contenu_notif = st.text_area("Détails de la mise à jour")
            sub_notif = st.form_submit_button("Envoyer à tous les utilisateurs")
            
            if sub_notif and titre_notif and contenu_notif:
                date_du_jour = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                cursor.execute("INSERT INTO annonces (titre, contenu, date_annonce) VALUES (?, ?, ?)",
                               (titre_notif, contenu_notif, date_du_jour))
                conn.commit()
                st.success("Notification diffusée avec succès à tous les commerçants !")
            elif sub_notif:
                st.error("Veuillez remplir le titre et le contenu.")

    st.stop()

# ==================== APPLICATION PRINCIPALE (COMMERÇANT) ====================
user_id = user['id']

# --- VÉRIFICATION DES NOTIFICATIONS & EXPIRATION POUR LE COMMERÇANT ---
cursor.execute("SELECT date_expiration FROM utilisateurs WHERE id = ?", (user_id,))
date_exp_str = cursor.fetchone()[0]
date_exp_obj = datetime.datetime.strptime(date_exp_str, "%Y-%m-%d").date()
jours_restants = (date_exp_obj - datetime.date.today()).days

# Alerte si l'abonnement expire bientôt (moins de 3 jours)
if 0 <= jours_restants <= 3:
    st.warning(f"⚠️ **Attention :** Votre abonnement expire dans {jours_restants} jour(s) (le {date_exp_str}). Pensez à renouveler auprès de Seth Prod (053119132).")

# Affichage des dernières notifications / nouveautés de l'admin
cursor.execute("SELECT titre, contenu, date_annonce FROM annonces ORDER BY id DESC LIMIT 3")
dernieres_annonces = cursor.fetchall()
if dernieres_annonces:
    with st.expander("🔔 **Nouveautés & Notifications de Seth Prod** (Cliquez pour voir)"):
        for ann in dernieres_annonces:
            st.markdown(f"**📢 {ann[0]}** *({ann[2]})\n{ann[1]}")
            st.markdown("---")

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
    * **Développeur :** Seth Prod
    * **Numéro Mobile Money / WhatsApp :** `053119132`
    
    Effectuez votre paiement au numéro ci-dessus, puis envoyez la capture du transfert sur WhatsApp avec le nom de votre boutique pour prolonger votre accès de 30 jours.
    """)
