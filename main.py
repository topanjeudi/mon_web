from flask import Flask, render_template, request, redirect, url_for, session
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)
app.secret_key = 'topan_secret_key'

# Configuration Firebase
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://entreprise-topanservice-default-rtdb.firebaseio.com/'
})

# Page d'accueil (choix visiteur ou agent)
@app.route('/')
def home():
    return render_template('index.html')

# Page visiteur (affiche les produits et permet de commander et commenter)
@app.route('/visiteur', methods=['GET', 'POST'])
def visiteur():
    produits_ref = db.reference('produits')
    produits = produits_ref.get()
    
    if request.method == 'POST':
        commentaire = request.form['commentaire']
        db.reference('commentaires').push({'message': commentaire})
    
    commentaires = db.reference('commentaires').get()
    return render_template('visiteur.html', produits=produits, commentaires=commentaires)

# Page agent (connexion/inscription)
@app.route('/agent', methods=['GET', 'POST'])
def agent():
    if request.method == 'POST':
        prenom = request.form['prenom']
        code = request.form['code']
        
        agents_ref = db.reference('agents')
        agents = agents_ref.get()
        
        if agents and prenom in agents and agents[prenom]['code'] == code:
            if agents[prenom]['validé']:
                session['agent'] = prenom
                return redirect(url_for('agent_dashboard'))
            else:
                return "Votre compte doit être validé par l'administrateur."
        else:
            return "Identifiants incorrects."
    return render_template('agent.html')

# Tableau de bord agent (vente de produits)
@app.route('/agent/dashboard', methods=['GET', 'POST'])
def agent_dashboard():
    if 'agent' not in session:
        return redirect(url_for('agent'))
    produits_ref = db.reference('produits')
    produits = produits_ref.get()
    
    if request.method == 'POST':
        produit = request.form['produit']
        quantite = int(request.form['quantite'])
        prix = float(request.form['prix'])
        
        ventes_ref = db.reference('ventes')
        ventes_ref.push({'agent': session['agent'], 'produit': produit, 'quantite': quantite, 'prix': prix})
        
        # Mettre à jour le stock
        produit_ref = db.reference(f'produits/{produit}')
        produit_data = produit_ref.get()
        if produit_data:
            nouvelle_quantite = max(0, produit_data['quantite'] - quantite)
            produit_ref.update({'quantite': nouvelle_quantite})
    
    return render_template('agent_dashboard.html', produits=produits)

# Connexion administrateur
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        code_admin = request.form['code']
        if code_admin == 'jeudit':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        return "Code incorrect."
    return render_template('admin.html')

# Tableau de bord administrateur
@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin'))
    
    agents_ref = db.reference('agents')
    agents = agents_ref.get()
    produits_ref = db.reference('produits')
    produits = produits_ref.get()
    ventes_ref = db.reference('ventes')
    ventes = ventes_ref.get()
    
    if request.method == 'POST':
        action = request.form['action']
        if action == 'ajouter_produit':
            nom = request.form['nom']
            prix_initial = float(request.form['prix_initial'])
            prix_vendu = float(request.form['prix_vendu'])
            quantite = int(request.form['quantite'])
            db.reference('produits').push({
                'nom': nom, 'prix_initial': prix_initial, 'prix_vendu': prix_vendu, 'quantite': quantite
            })
        elif action == 'modifier_produit':
            produit_id = request.form['produit_id']
            nom = request.form['nom']
            prix_initial = float(request.form['prix_initial'])
            prix_vendu = float(request.form['prix_vendu'])
            quantite = int(request.form['quantite'])
            db.reference(f'produits/{produit_id}').update({
                'nom': nom, 'prix_initial': prix_initial, 'prix_vendu': prix_vendu, 'quantite': quantite
            })
        elif action == 'supprimer_produit':
            produit_id = request.form['produit_id']
            db.reference(f'produits/{produit_id}').delete()
        elif action == 'valider_agent':
            agent_id = request.form['agent_id']
            db.reference(f'agents/{agent_id}').update({'validé': True})
        elif action == 'supprimer_agent':
            agent_id = request.form['agent_id']
            db.reference(f'agents/{agent_id}').delete()
    
    return render_template('admin_dashboard.html', agents=agents, produits=produits, ventes=ventes)

if __name__ == '__main__':
    app.run(debug=True)
