import sqlite3
import streamlit as st
import pandas as pd
import datetime

# --- CONFIGURATION DE LA PAGE STREAMLIT ---
st.set_page_config(
    page_title="GestionStock Pro - Mobile",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DESIGN CSS PERSONNALISÉ POUR UNE PLUS BELLE INTERFACE ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .alert-box {
        padding: 15px;
        border-radius: 8px;
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURATION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect("stock_pro_mobile.db", check_same_thread=False)
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
    
    # Table de l'historique des ventes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produit TEXT NOT NULL,
            prix_unitaire REAL NOT NULL,
            quantite INTEGER NOT NULL,
            total REAL NOT NULL,
            date_vente TEXT NOT NULL
        )
    ''')

    # Table des crédits / ardoises clients
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_nom TEXT NOT NULL,
            montant REAL NOT NULL,
            motif TEXT NOT NULL,
            date_credit TEXT NOT NULL,
            statut TEXT NOT NULL
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
    
    # Licence par défaut si inexistante
    cursor.execute("SELECT COUNT(*) FROM abonnement")
    if cursor.fetchone()[0] == 0:
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
        return False, "Aucune licence."
    date_exp_str, statut = ab_info
    date_exp = datetime.datetime.strptime(date_exp_str, "%Y-%m-%d").date()
    if statut != "Actif" or datetime.date.today() > date_exp:
        return False, date_exp_str
    return True, date_exp_str

# --- EN-TÊTE ET VÉRIFICATION ---
st.title("📦 GestionStock & Caisse Pro")
est_actif, info_exp = verifier_abonnement()

if not est_actif:
    st.error("⚠️ **Votre abonnement a expiré !** Veuillez régler l'abonnement par Mobile Money pour continuer.")
    with st.expander("🔑 Espace Admin (Prolonger la licence)"):
        nouveau_jours = st.number_input("Ajouter des jours", min_value=1, value=30)
        if st.button("Prolonger"):
            nouvelle_date = (datetime.date.today() + datetime.timedelta(days=nouveau_jours)).strftime("%Y-%m-%d")
            cursor.execute("UPDATE abonnement SET date_expiration = ?, statut = 'Actif'", (nouvelle_date,))
            conn.commit()
            st.success("Licence prolongée avec succès ! Rechargez la page.")
            st.rerun()
    st.stop()

# --- BARRE LATÉRALE DE NAVIGATION (DESIGN PRO) ---
st.sidebar.markdown("### 🎛️ Menu Principal")
menu = st.sidebar.radio("Navigation", [
    "📊 Tableau de Bord", 
    "🛒 Caisse & Ventes", 
    "📦 Gestion des Stocks", 
    "📝 Carnet de Crédits", 
    "📅 Mon Abonnement"
])

# ==================== 1. TABLEAU DE BORD ====================
if menu == "📊 Tableau de Bord":
    st.header("📊 Vue d'ensemble de l'activité")
    
    # Calcul des métriques clés
    cursor.execute("SELECT SUM(total) FROM ventes")
    ca_total = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT COUNT(*) FROM ventes")
    nb_ventes = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM produits WHERE quantite <= 5")
    alertes_stock = cursor.fetchone()[0] or 0

    # Affichage en colonnes modernes
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Chiffre d'Affaires", f"{ca_total:,.0f} FCFA")
    col2.metric("🛍️ Total des Ventes", f"{nb_ventes}")
    col3.metric("⚠️ Produits en Alerte Stock", f"{alertes_stock}", delta_color="inverse")

    st.markdown("---")

    # Alerte visuelle stock bas
    if alertes_stock > 0:
        st.warning(f"🚨 **Attention :** Vous avez {alertes_stock} produit(s) avec un stock inférieur ou égal à 5 unités !")

    # Graphique des ventes par produit
    st.subheader("📈 Répartition des ventes par article")
    cursor.execute("SELECT produit, SUM(quantite) FROM ventes GROUP BY produit")
    data_ventes = cursor.fetchall()
    if data_ventes:
        df_v = pd.DataFrame(data_ventes, columns=["Produit", "Quantité Vendue"])
        df_v.set_index("Produit", inplace=True)
        st.bar_chart(df_v)
    else:
        st.info("Aucune vente enregistrée pour le moment pour afficher les graphiques.")

# ==================== 2. CAISSE & VENTES ====================
elif menu == "🛒 Caisse & Ventes":
    st.header("🛒 Enregistrer une Vente")
    
    cursor.execute("SELECT id, nom, prix, quantite FROM produits")
    produits = cursor.fetchall()
    
    if not produits:
        st.warning("Aucun produit disponible. Veuillez en ajouter dans l'onglet Stock.")
    else:
        col_c1, col_c2 = st.columns([2, 1])
        
        with col_c1:
            options_produits = {f"{p[1]} (Stock: {p[3]} | Prix: {p[2]:,.0f} FCFA)": p for p in produits}
            choix = st.selectbox("Sélectionner un produit", list(options_produits.keys()))
            
            p_id, p_nom, p_prix, p_stock = options_produits[choix]
            qte_achat = st.number_input("Quantité achetée", min_value=1, max_value=max(1, p_stock), step=1)
            
            montant_total = p_prix * qte_achat
            st.info(f"Montant total à régler : **{montant_total:,.0f} FCFA**")
            
            if st.button("✅ Valider la Vente", type="primary", use_container_width=True):
                nouveau_stock = p_stock - qte_achat
                cursor.execute("UPDATE produits SET quantite = ? WHERE id = ?", (nouveau_stock, p_id))
                
                date_du_jour = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                    INSERT INTO ventes (produit, prix_unitaire, quantite, total, date_vente) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (p_nom, p_prix, qte_achat, montant_total, date_du_jour))
                conn.commit()
                
                st.success(f"Vente validée avec succès ! Total : {montant_total:,.0f} FCFA")
                st.balloons()

        with col_c2:
            st.markdown("### 📋 Rappel Stock")
            df_stock_rapide = pd.DataFrame(produits, columns=["ID", "Nom", "Prix", "Stock"])
            st.dataframe(df_stock_rapide[["Nom", "Stock"]], hide_index=True, use_container_width=True)

# ==================== 3. GESTION DES STOCKS ====================
elif menu == "📦 Gestion des Stocks":
    st.header("📦 Gestion des Stocks & Inventaire")
    
    tab_ajout, tab_voir = st.tabs(["➕ Ajouter un produit", "📋 Liste & Export"])
    
    with tab_ajout:
        st.subheader("Nouveau Produit")
        with st.form("form_produit"):
            nom_p = st.text_input("Nom du produit")
            prix_p = st.number_input("Prix unitaire (FCFA)", min_value=0.0, step=100.0)
            qte_p = st.number_input("Quantité initiale", min_value=0, step=1)
            submitted = st.form_submit_button("Enregistrer le produit")
            
            if submitted:
                if nom_p and prix_p > 0:
                    cursor.execute("INSERT INTO produits (nom, prix, quantite) VALUES (?, ?, ?)", (nom_p, prix_p, qte_p))
                    conn.commit()
                    st.success(f"Produit '{nom_p}' ajouté avec succès !")
                else:
                    st.error("Veuillez remplir correctement les champs.")

    with tab_voir:
        st.subheader("Inventaire Actuel")
        cursor.execute("SELECT id, nom, prix, quantite FROM produits")
        data_p = cursor.fetchall()
        
        if data_p:
            df_p = pd.DataFrame(data_p, columns=["ID", "Nom du Produit", "Prix (FCFA)", "Quantité"])
            st.dataframe(df_p, use_container_width=True, hide_index=True)
            
            # Option d'export en CSV/Excel
            csv_data = df_p.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Télécharger l'inventaire (CSV)",
                data=csv_data,
                file_name="inventaire_boutique.csv",
                mime="text/csv"
            )
        else:
            st.info("Le stock est vide pour le moment.")

# ==================== 4. CARNET DE CRÉDITS (ARDOISES) ====================
elif menu == "📝 Carnet de Crédits":
    st.header("📝 Gestion des Crédits et Dettes Clients")
    
    tab_c_ajout, tab_c_voir = st.tabs(["➕ Enregistrer un crédit", "📋 Suivi des ardoises"])
    
    with tab_c_ajout:
        with st.form("form_credit"):
            nom_client = st.text_input("Nom du client")
            montant_c = st.number_input("Montant dû (FCFA)", min_value=0.0, step=500.0)
            motif_c = st.text_input("Motif / Articles pris à crédit")
            sub_c = st.form_submit_button("Enregistrer le crédit")
            
            if sub_c and nom_client and montant_c > 0:
                date_c = datetime.datetime.now().strftime("%Y-%m-%d")
                cursor.execute("INSERT INTO credits (client_nom, montant, motif, date_credit, statut) VALUES (?, ?, ?, ?, ?)",
                               (nom_client, montant_c, motif_c, date_c, "Impayé"))
                conn.commit()
                st.success(f"Crédit de {montant_c} FCFA enregistré pour {nom_client}.")
            elif sub_c:
                st.error("Veuillez remplir tous les champs.")

    with tab_c_voir:
        cursor.execute("SELECT id, client_nom, montant, motif, date_credit, statut FROM credits")
        credits_data = cursor.fetchall()
        
        if credits_data:
            df_cred = pd.DataFrame(credits_data, columns=["ID", "Client", "Montant (FCFA)", "Motif", "Date", "Statut"])
            st.dataframe(df_cred, use_container_width=True, hide_index=True)
            
            cred_id_a_regler = st.number_input("ID du crédit remboursé", min_value=1, step=1)
            if st.button("Marquer comme Réglé / Payé"):
                cursor.execute("UPDATE credits SET statut = 'Payé' WHERE id = ?", (cred_id_a_regler,))
                conn.commit()
                st.success("Crédit mis à jour avec succès !")
                st.rerun()
        else:
            st.info("Aucun crédit en cours enregistré.")

# ==================== 5. MON ABONNEMENT ====================
elif menu == "📅 Mon Abonnement":
    st.header("📅 Statut de votre Abonnement")
    cursor.execute("SELECT client_nom, date_expiration, statut FROM abonnement LIMIT 1")
    ab = cursor.fetchone()
    
    col_a1, col_a2 = st.columns(2)
    col_a1.metric("👤 Nom de la Boutique", ab[0])
    col_a2.metric("🟢 Statut", ab[2])
    
    st.warning(f"📅 **Date limite d'accès :** {ab[1]}")
    st.info("Pour renouveler votre abonnement mensuel ou obtenir de l'aide, contactez le support technique.")
