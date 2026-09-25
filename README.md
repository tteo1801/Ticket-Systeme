# Système de Tickets — Guide rapide

Application complète et fonctionnelle :
- **Backend** : Python (FastAPI + SQLite) — API REST complète (créer, lister, filtrer, mettre à jour, supprimer des tickets, commentaires, statistiques).
- **Frontend** : JS moderne (vanilla, `fetch`/`async-await`), un seul fichier HTML autonome, stylé avec Tailwind (CDN).

## 1. Tester en local

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
L'API tourne sur `http://localhost:8000` (doc interactive sur `http://localhost:8000/docs`).

### Frontend
Ouvre simplement `frontend/index.html` dans ton navigateur (double-clic, ou `open index.html`).
Dans le champ "URL de l'API" en haut de la page, laisse `http://localhost:8000` si tu testes en local.

## 2. Où héberger gratuitement

### Backend (FastAPI) — besoin d'un serveur qui tourne en continu
| Plateforme | Notes |
|---|---|
| **Render.com** (recommandé) | Free tier "Web Service". Connecte ton repo GitHub, Render détecte `requirements.txt` et le `Procfile`. Le service s'endort après inactivité (redémarre en ~30s au réveil). |
| **Railway.app** | Free tier avec crédit mensuel limité. Déploiement très simple depuis GitHub. |
| **Fly.io** | Free tier généreux, nécessite leur CLI (`flyctl launch`). |
| **PythonAnywhere** | Bon pour un usage simple, gratuit avec limitations réseau (domaines autorisés restreints). |

**Étapes typiques (Render) :**
1. Pousse le dossier `backend/` sur un repo GitHub.
2. Sur render.com → "New +" → "Web Service" → connecte le repo.
3. Build command : `pip install -r requirements.txt`
4. Start command : `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Récupère l'URL fournie (ex. `https://ton-app.onrender.com`).

⚠️ La base SQLite (`tickets.db`) est stockée sur disque local du service : sur les plans gratuits, le disque n'est **pas persistant** entre redéploiements. Pour un usage réel/durable, passe à une base hébergée gratuite comme **Supabase** (Postgres gratuit) ou **Neon.tech** (Postgres gratuit) — il faudra juste adapter le code SQLite → Postgres.

### Frontend (le fichier `index.html`)
Comme c'est un fichier statique unique, héberge-le sur :
- **Netlify** (glisser-déposer le dossier `frontend/` sur app.netlify.com/drop)
- **Vercel** (import du repo, aucune config nécessaire)
- **Cloudflare Pages**
- **GitHub Pages**

Une fois en ligne, ouvre le site, colle l'URL de ton backend Render dans le champ "URL de l'API" et clique "Enregistrer" — c'est mémorisé dans le navigateur (localStorage).

## 3. Résumé du flux recommandé (100% gratuit)
1. Backend → **Render.com** (Web Service gratuit)
2. Frontend → **Netlify** ou **Vercel** (site statique gratuit)
3. Connecte les deux via le champ "URL de l'API" dans l'interface

## Fonctionnalités incluses
- Créer un ticket (titre, description, demandeur, catégorie, priorité)
- Lister / filtrer par statut, priorité, recherche texte
- Voir le détail d'un ticket, changer statut/priorité, supprimer
- Ajouter des commentaires sur un ticket
- Tableau de bord avec statistiques (total, par statut)
