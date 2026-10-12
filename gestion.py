import sqlite3
import streamlit as st
import pandas as pd
import datetime
import hashlib
import urllib.parse

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="SaaS GestionStock Pro - Seth Prod",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- INJECTION CSS ADAPTÉE AU MOTEUR DE THÈME STREAMLIT ---
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    iframe[data-testid="stStatusWidget"] {display: none !important; visibility: hidden;}
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }
    
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    div[data-testid="stMetricLabel"] p {
        color: #e0e0e0 !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- INITIALISATION DE LA BASE DE DONNÉES AVEC MIGRATIONS TOTALES ---
def init_db():
    conn = sqlite3.connect("plateforme_saas.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # 1. Table Utilisateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_boutique TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            date_expiration TEXT NOT NULL,
            statut TEXT NOT NULL,
            role TEXT DEFAULT 'Gerant',
            parent_id INTEGER DEFAULT 0
        )
    ''')
    try: cursor.execute("ALTER TABLE utilisateurs ADD COLUMN role TEXT DEFAULT 'Gerant'")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE utilisateurs ADD COLUMN parent_id INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass

    # 2. Table Produits
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            nom TEXT NOT NULL,
            code_barre TEXT,
            prix REAL NOT NULL,
            quantite INTEGER NOT NULL,
            fournisseur_id INTEGER
        )
    ''')
    try: cursor.execute("ALTER TABLE produits ADD COLUMN code_barre TEXT")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE produits ADD COLUMN fournisseur_id INTEGER")
    except sqlite3.OperationalError: pass
    
    # 3. Table Ventes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vendeur TEXT NOT NULL,
            produit TEXT NOT NULL,
            prix_unitaire REAL NOT NULL,
            quantite INTEGER NOT NULL,
            total REAL NOT NULL,
            date_vente TEXT NOT NULL
        )
    ''')
    try: cursor.execute("ALTER TABLE ventes ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE ventes ADD COLUMN vendeur TEXT NOT NULL DEFAULT 'Admin'")
    except sqlite3.OperationalError: pass

    # 4. Table Credits
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
    try: cursor.execute("ALTER TABLE credits ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError: pass

    # 5. Table Fournisseurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fournisseurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            nom TEXT NOT NULL,
            telephone TEXT NOT NULL,
            adresse TEXT
        )
    ''')
    try: cursor.execute("ALTER TABLE fournisseurs ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError: pass

    # 6. Table Annonces
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

if 'user' not in st.session_state:
    st.session_state['user'] = None

# ==================== PAGE DE CONNEXION / INSCRIPTION ====================
if st.session_state['user'] is None:
    st.title("📱 GestionStock Pro")
    st.caption("Développé par **Seth Prod** • Support : `053119132`")
    
    choix_auth = st.segmented_control("Accès", ["Connexion", "Créer un compte"], default="Connexion")
    
    if choix_auth == "Connexion":
        with st.form("form_login"):
            username = st.text_input("Identifiant (Boutique ou Caissier)").strip()
            password = st.text_input("Mot de passe", type="password")
            submit_login = st.form_submit_button("Se connecter", type="primary", use_container_width=True)
            
            if submit_login:
                if username == "adminseth" and password == "admin2309":
                    st.session_state['user'] = {"id": 9999, "boutique": "ADMINISTRATION", "username": "adminseth", "role": "Admin", "owner_id": 9999}
                    st.success("Connexion Admin réussie !")
                    st.rerun()
                
                cursor.execute("SELECT id, nom_boutique, username, password, date_expiration, statut, role, parent_id FROM utilisateurs WHERE username = ?", (username,))
                user_data = cursor.fetchone()
                
                if user_data and user_data[3] == make_hash(password):
                    owner_id = user_data[0] if user_data[6] == 'Gerant' else user_data[7]
                    
                    cursor.execute("SELECT date_expiration, statut FROM utilisateurs WHERE id = ?", (owner_id,))
                    ab_data = cursor.fetchone()
                    
                    date_exp = datetime.datetime.strptime(ab_data[0], "%Y-%m-%d").date()
                    if ab_data[1] == "Actif" and datetime.date.today() <= date_exp:
                        st.session_state['user'] = {
                            "id": user_data[0],
                            "boutique": user_data[1],
                            "username": user_data[2],
                            "role": user_data[6],
                            "owner_id": owner_id
                        }
                        st.success("Connexion réussie !")
                        st.rerun()
                    else:
                        st.error("⚠️ L'abonnement de cette boutique a expiré. Contactez Seth Prod au 053119132.")
                else:
                    st.error("Identifiant ou mot de passe incorrect.")
                    
    else:
        with st.form("form_signup"):
            st.info("🎁 7 jours d'essai gratuits à l'inscription !")
            nom_boutique = st.text_input("Nom de votre boutique").strip()
            username = st.text_input("Choisissez un identifiant unique").strip()
            password = st.text_input("Mot de passe", type="password")
            submit_signup = st.form_submit_button("S'inscrire et se connecter", type="primary", use_container_width=True)
            
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
                            "username": username,
                            "role": "Gerant",
                            "owner_id": new_user[0]
                        }
                        st.success("Compte créé avec succès !")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Cet identifiant existe déjà. Choisissez-en un autre.")
                else:
                    st.error("Veuillez remplir tous les champs.")
                    
    st.stop()

# ==================== PANNEAU ADMINISTRATEUR (SETH PROD) ====================
user = st.session_state['user']
if user['id'] == 9999:
    st.title("👑 Admin - Seth Prod")
    if st.button("Se déconnecter"):
        st.session_state['user'] = None
        st.rerun()
        
    tab_adm1, tab_adm2 = st.tabs(["👥 Abonnés", "📢 Annonces"])
    
    with tab_adm1:
        cursor.execute("SELECT id, nom_boutique, username, date_expiration, statut FROM utilisateurs WHERE role = 'Gerant'")
        clients = cursor.fetchall()
        
        if clients:
            df_clients = pd.DataFrame(clients, columns=["ID", "Boutique", "Identifiant", "Expiration", "Statut"])
            st.dataframe(df_clients, use_container_width=True, hide_index=True)
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.markdown("### 🔄 Prolonger Abonnement")
                c_id = st.number_input("ID Client", min_value=1, step=1, key="p_id")
                jours_plus = st.number_input("Jours à ajouter", min_value=1, value=30, key="p_jours")
                
                if st.button("Prolonger"):
                    cursor.execute("SELECT date_expiration FROM utilisateurs WHERE id = ?", (c_id,))
                    res = cursor.fetchone()
                    if res:
                        base_date = max(datetime.datetime.strptime(res[0], "%Y-%m-%d").date(), datetime.date.today())
                        nouvelle_exp = (base_date + datetime.timedelta(days=jours_plus)).strftime("%Y-%m-%d")
                        cursor.execute("UPDATE utilisateurs SET date_expiration = ?, statut = 'Actif' WHERE id = ?", (nouvelle_exp, c_id))
                        conn.commit()
                        st.success(f"Prolongé jusqu'au {nouvelle_exp} !")
                        st.rerun()
            
            with col_b:
                st.markdown("### 🗑️ Supprimer un abonné")
                del_id = st.number_input("ID de la boutique/gérant à retirer", min_value=1, step=1, key="del_id")
                if st.button("Supprimer ce compte", type="primary"):
                    cursor.execute("SELECT id FROM utilisateurs WHERE id = ? AND role = 'Gerant'", (del_id,))
                    if cursor.fetchone():
                        # Suppression de la boutique, de ses caissiers, et de toutes ses données
                        cursor.execute("DELETE FROM utilisateurs WHERE id = ? OR parent_id = ?", (del_id, del_id))
                        cursor.execute("DELETE FROM produits WHERE user_id = ?", (del_id,))
                        cursor.execute("DELETE FROM ventes WHERE user_id = ?", (del_id,))
                        cursor.execute("DELETE FROM credits WHERE user_id = ?", (del_id,))
                        cursor.execute("DELETE FROM fournisseurs WHERE user_id = ?", (del_id,))
                        conn.commit()
                        st.success(f"Le compte ID {del_id} et ses données associées ont été supprimés.")
                        st.rerun()
                    else:
                        st.error("ID Gérant introuvable.")

            with col_c:
                st.markdown("### 🧹 Nettoyer Inactifs (> 7j)")
                if st.button("Nettoyer les inactifs"):
                    date_limite = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
                    cursor.execute("SELECT id FROM utilisateurs WHERE date_expiration < ? AND role = 'Gerant'", (date_limite,))
                    inactifs = cursor.fetchall()
                    for ina in inactifs:
                        uid = ina[0]
                        cursor.execute("DELETE FROM utilisateurs WHERE id = ? OR parent_id = ?", (uid, uid))
                        cursor.execute("DELETE FROM produits WHERE user_id = ?", (uid,))
                        cursor.execute("DELETE FROM ventes WHERE user_id = ?", (uid,))
                        cursor.execute("DELETE FROM credits WHERE user_id = ?", (uid,))
                        cursor.execute("DELETE FROM fournisseurs WHERE user_id = ?", (uid,))
                    conn.commit()
                    st.success(f"{len(inactifs)} compte(s) inactif(s) nettoyé(s) !")
                    st.rerun()

    with tab_adm2:
        with st.form("form_annonce"):
            titre = st.text_input("Titre de la nouveauté")
            contenu = st.text_area("Contenu de l'annonce")
            if st.form_submit_button("Diffuser") and titre and contenu:
                cursor.execute("INSERT INTO annonces (titre, contenu, date_annonce) VALUES (?, ?, ?)",
                               (titre, contenu, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                st.success("Annonce envoyée !")

    st.stop()

# ==================== APPLICATION COMMERÇANT / EMPLOYÉ ====================
owner_id = user['owner_id']
role = user['role']

col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.markdown(f"### 🏪 {user['boutique']} `({role})`")
with col_head2:
    if st.button("Déconnexion", use_container_width=True):
        st.session_state['user'] = None
        st.rerun()

if role == "Gerant":
    menu_options = ["🛒 Caisse", "📊 Tableau de Bord", "📦 Stocks", "📝 Crédits", "🏭 Fournisseurs", "👥 Caissiers", "📅 Abonnement"]
else:
    menu_options = ["🛒 Caisse", "📦 Stocks (Lecture)", "📝 Crédits"]

menu = st.radio("Navigation", menu_options, horizontal=True)

cursor.execute("SELECT date_expiration FROM utilisateurs WHERE id = ?", (owner_id,))
date_exp_str = cursor.fetchone()[0]
jours_restants = (datetime.datetime.strptime(date_exp_str, "%Y-%m-%d").date() - datetime.date.today()).days

if 0 <= jours_restants <= 3:
    st.warning(f"⚠️ Votre abonnement expire dans {jours_restants} jour(s). Contactez Seth Prod (053119132).")

# ==================== 1. CAISSE ====================
if menu == "🛒 Caisse":
    st.subheader("🛒 Caisse & Scan Code-Barres")
    
    recherche = st.text_input("🔍 Rechercher par nom ou scanner le code-barres").strip()
    
    if recherche:
        cursor.execute("SELECT id, nom, prix, quantite, code_barre FROM produits WHERE user_id = ? AND (nom LIKE ? OR code_barre = ?)", 
                       (owner_id, f"%{recherche}%", recherche))
    else:
        cursor.execute("SELECT id, nom, prix, quantite, code_barre FROM produits WHERE user_id = ?", (owner_id,))
    
    produits = cursor.fetchall()
    
    if not produits:
        st.warning("Aucun produit trouvé.")
    else:
        options = {f"{p[1]} | Code: {p[4] or 'N/A'} (Stock: {p[3]} | {p[2]:,.0f} FCFA)": p for p in produits}
        choix = st.selectbox("Sélectionner un produit", list(options.keys()))
        p_id, p_nom, p_prix, p_stock, p_code = options[choix]
        
        qte_achat = st.number_input("Quantité", min_value=1, max_value=max(1, p_stock), step=1)
        total = p_prix * qte_achat
        st.info(f"Montant Total : **{total:,.0f} FCFA**")
        
        nom_client_recu = st.text_input("Nom du client (optionnel pour le reçu WhatsApp)")
        
        if st.button("✅ Valider la Vente", type="primary", use_container_width=True):
            cursor.execute("UPDATE produits SET quantite = ? WHERE id = ?", (p_stock - qte_achat, p_id))
            date_v = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO ventes (user_id, vendeur, produit, prix_unitaire, quantite, total, date_vente) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (owner_id, user['username'], p_nom, p_prix, qte_achat, total, date_v))
            conn.commit()
            
            st.success(f"Vente enregistrée par {user['username']} !")
            
            texte_recu = f"🧾 *REÇU DE CAISSE - {user['boutique']}*\n" \
                         f"Client : {nom_client_recu or 'Client'}\n" \
                         f"Article : {p_nom} (x{qte_achat})\n" \
                         f"Total : {total:,.0f} FCFA\n" \
                         f"Date : {date_v}\nMerci pour votre confiance !"
            
            url_wa = f"https://api.whatsapp.com/send?text={urllib.parse.quote(texte_recu)}"
            st.markdown(f"[📲 Envoyer le reçu sur WhatsApp]({url_wa})", unsafe_allow_html=True)
            st.balloons()

# ==================== 2. TABLEAU DE BORD ====================
elif menu == "📊 Tableau de Bord":
    st.subheader("📊 Tableau de Bord Financier")
    cursor.execute("SELECT SUM(total), COUNT(*) FROM ventes WHERE user_id = ?", (owner_id,))
    ca, nb = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM produits WHERE user_id = ? AND quantite <= 5", (owner_id,))
    alertes = cursor.fetchone()[0] or 0

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Chiffre d'Affaires", f"{ca or 0:,.0f} FCFA")
    col2.metric("🛍️ Ventes", f"{nb or 0}")
    col3.metric("⚠️ Stocks Bas", f"{alertes}")

    st.markdown("---")
    st.subheader("📊 Ventes récentes par caissier")
    cursor.execute("SELECT vendeur, produit, quantite, total, date_vente FROM ventes WHERE user_id = ? ORDER BY id DESC LIMIT 10", (owner_id,))
    v_data = cursor.fetchall()
    if v_data:
        st.dataframe(pd.DataFrame(v_data, columns=["Vendeur", "Produit", "Qte", "Total FCFA", "Date"]), use_container_width=True, hide_index=True)
    else:
        st.info("Aucune vente enregistrée pour le moment.")

# ==================== 3. GESTION DES STOCKS ====================
elif menu in ["📦 Stocks", "📦 Stocks (Lecture)"]:
    st.subheader("📦 Gestion des Stocks & Codes-Barres")
    
    if role == "Gerant":
        tab1, tab2 = st.tabs(["Ajouter / Modifier", "Inventaire"])
        with tab1:
            with st.form("form_p"):
                nom = st.text_input("Nom de l'article")
                code_barre = st.text_input("Code-barres / Référence (Facultatif)")
                prix = st.number_input("Prix unitaire (FCFA)", min_value=0.0, step=100.0)
                qte = st.number_input("Quantité initiale", min_value=0, step=1)
                
                cursor.execute("SELECT id, nom FROM fournisseurs WHERE user_id = ?", (owner_id,))
                f_list = cursor.fetchall()
                f_dict = {f[1]: f[0] for f in f_list}
                f_choix = st.selectbox("Fournisseur associé", ["Aucun"] + list(f_dict.keys()))
                
                if st.form_submit_button("Enregistrer l'article", type="primary"):
                    fid = f_dict[f_choix] if f_choix != "Aucun" else None
                    cursor.execute("INSERT INTO produits (user_id, nom, code_barre, prix, quantite, fournisseur_id) VALUES (?, ?, ?, ?, ?, ?)",
                                   (owner_id, nom, code_barre, prix, qte, fid))
                    conn.commit()
                    st.success("Produit ajouté avec succès !")
        with tab2:
            cursor.execute("SELECT id, nom, code_barre, prix, quantite FROM produits WHERE user_id = ?", (owner_id,))
            data = cursor.fetchall()
            if data:
                df = pd.DataFrame(data, columns=["ID", "Article", "Code-Barres", "Prix FCFA", "Stock"])
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.download_button("Télécharger Inventaire (CSV)", df.to_csv(index=False).encode('utf-8'), "inventaire.csv", "text/csv")
    else:
        cursor.execute("SELECT nom, code_barre, prix, quantite FROM produits WHERE user_id = ?", (owner_id,))
        data = cursor.fetchall()
        st.dataframe(pd.DataFrame(data, columns=["Article", "Code-Barres", "Prix FCFA", "Stock"]), use_container_width=True, hide_index=True)

# ==================== 4. CARNET DE CRÉDITS ====================
elif menu == "📝 Crédits":
    st.subheader("📝 Crédits & Ardoises Clients")
    tab1, tab2 = st.tabs(["Nouveau Crédit", "Suivi & Règlement"])
    with tab1:
        with st.form("form_cred"):
            client = st.text_input("Nom du client")
            montant = st.number_input("Montant dû (FCFA)", min_value=0.0)
            motif = st.text_input("Articles pris à crédit")
            if st.form_submit_button("Enregistrer le crédit") and client and montant > 0:
                cursor.execute("INSERT INTO credits (user_id, client_nom, montant, motif, date_credit, statut) VALUES (?, ?, ?, ?, ?, ?)",
                               (owner_id, client, montant, motif, datetime.datetime.now().strftime("%Y-%m-%d"), "Impayé"))
                conn.commit()
                st.success("Crédit enregistré !")
    with tab2:
        cursor.execute("SELECT id, client_nom, montant, motif, date_credit, statut FROM credits WHERE user_id = ?", (owner_id,))
        c_data = cursor.fetchall()
        if c_data:
            st.dataframe(pd.DataFrame(c_data, columns=["ID", "Client", "Montant FCFA", "Motif", "Date", "Statut"]), use_container_width=True, hide_index=True)
            if role == "Gerant":
                c_id = st.number_input("ID du crédit réglé", min_value=1, step=1)
                if st.button("Marquer comme Payé"):
                    cursor.execute("UPDATE credits SET statut = 'Payé' WHERE id = ? AND user_id = ?", (c_id, owner_id))
                    conn.commit()
                    st.success("Mis à jour !")
                    st.rerun()

# ==================== 5. FOURNISSEURS & COMMANDES ====================
elif menu == "🏭 Fournisseurs":
    st.subheader("🏭 Gestion des Fournisseurs & Commandes")
    tab1, tab2 = st.tabs(["Ajouter Fournisseur", "Commander sur WhatsApp"])
    with tab1:
        with st.form("form_f"):
            nom_f = st.text_input("Nom du fournisseur")
            tel_f = st.text_input("Numéro WhatsApp / Téléphone")
            adresse_f = st.text_input("Adresse / Marché")
            if st.form_submit_button("Enregistrer Fournisseur") and nom_f and tel_f:
                cursor.execute("INSERT INTO fournisseurs (user_id, nom, telephone, adresse) VALUES (?, ?, ?, ?)",
                               (owner_id, nom_f, tel_f, adresse_f))
                conn.commit()
                st.success("Fournisseur ajouté !")
    with tab2:
        cursor.execute("SELECT id, nom, telephone FROM fournisseurs WHERE user_id = ?", (owner_id,))
        fournis = cursor.fetchall()
        if fournis:
            f_dict = {f[1]: f[2] for f in fournis}
            choix_f = st.selectbox("Choisir le fournisseur", list(f_dict.keys()))
            message_cmd = st.text_area("Articles à commander", "Bonjour, je souhaite commander : \n- Article A : 10 unités\n- Article B : 5 unités")
            
            url_cmd = f"https://api.whatsapp.com/send?phone={f_dict[choix_f]}&text={urllib.parse.quote(message_cmd)}"
            st.markdown(f"[📲 Envoyer le bon de commande sur WhatsApp]({url_cmd})", unsafe_allow_html=True)

# ==================== 6. CAISSIERS ====================
elif menu == "👥 Caissiers":
    st.subheader("👥 Création des comptes Caissiers")
    
    with st.form("form_caissier"):
        user_c = st.text_input("Identifiant du caissier").strip()
        pass_c = st.text_input("Mot de passe caissier", type="password")
        if st.form_submit_button("Créer le compte Caissier"):
            if user_c and pass_c:
                try:
                    hashed_p = make_hash(pass_c)
                    cursor.execute("INSERT INTO utilisateurs (nom_boutique, username, password, date_expiration, statut, role, parent_id) VALUES (?, ?, ?, ?, 'Actif', 'Caissier', ?)",
                                   (user['boutique'], user_c, hashed_p, date_exp_str, owner_id))
                    conn.commit()
                    st.success(f"Compte Caissier '{user_c}' créé !")
                except sqlite3.IntegrityError:
                    st.error("Cet identifiant existe déjà.")

    st.markdown("### Liste de vos Caissiers")
    cursor.execute("SELECT id, username, role FROM utilisateurs WHERE parent_id = ?", (owner_id,))
    caissiers = cursor.fetchall()
    if caissiers:
        st.dataframe(pd.DataFrame(caissiers, columns=["ID", "Identifiant", "Rôle"]), use_container_width=True, hide_index=True)

# ==================== 7. ABONNEMENT ====================
elif menu == "📅 Abonnement":
    st.subheader("📅 Votre Abonnement SaaS")
    st.info(f"**Boutique :** {user['boutique']}")
    st.warning(f"**Date d'expiration :** {date_exp_str} ({jours_restants} jours restants)")
    
    st.markdown("### 💳 Contact Développeur")
    st.write("""
    * **Développeur :** Seth Prod
    * **WhatsApp / Mobile Money :** `053119132`
    """)
