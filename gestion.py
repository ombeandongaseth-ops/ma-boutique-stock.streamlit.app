import sqlite3
import streamlit as st
import pandas as pd

# --- CONFIGURATION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect("stock_mobile.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prix REAL NOT NULL,
            quantite INTEGER NOT NULL
        )
    ''')
    conn.commit()
    return conn, cursor

conn, cursor = init_db()

st.title("📱 GestionStock Mobile")
st.subheader("Solution pour Smartphone")

# --- MENU DE NAVIGATION ---
menu = st.sidebar.selectbox("Menu", ["Caisse & Vente", "Ajouter Produit", "Voir le Stock"])

if menu == "Ajouter Produit":
    st.header("Ajouter un article")
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
    st.header("Enregistrer une Vente")
    
    # Récupérer les produits
    cursor.execute("SELECT id, nom, prix, quantite FROM produits")
    produits = cursor.fetchall()
    
    if not produits:
        st.warning("Aucun produit en stock pour l'instant.")
    else:
        # Créer un dictionnaire pour le sélecteur
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
            st.success(f"Vente validée ! Total à payer : **{total} FCFA**")
            st.balloons()

elif menu == "Voir le Stock":
    st.header("État du Stock Actuel")
    cursor.execute("SELECT id, nom, prix, quantite FROM produits")
    data = cursor.fetchall()
    
    if data:
        df = pd.DataFrame(data, columns=["ID", "Nom", "Prix (FCFA)", "Quantité"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Le stock est vide.")