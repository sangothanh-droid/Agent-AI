# 🤖 Agent IA Personnel — Web

Interface web pour l'agent IA. Frontend sur Netlify, backend sur Render (les deux gratuits).

---

## Structure

```
agent-web/
├── frontend/          → Netlify (HTML/CSS/JS)
│   ├── index.html
│   ├── style.css
│   └── app.js
├── backend/           → Render (FastAPI Python)
│   ├── main.py
│   ├── agent.py
│   ├── tools/
│   ├── requirements.txt
│   ├── Procfile
│   └── .env.example
└── netlify.toml
```

---

## Étape 1 — Mettre sur GitHub

Crée un repo GitHub et push tout le projet :

```bash
git init
git add .
git commit -m "init agent ia"
git remote add origin https://github.com/TON_USER/agent-ia.git
git push -u origin main
```

---

## Étape 2 — Déployer le backend sur Render

1. Va sur **render.com** → crée un compte gratuit
2. **New** → **Web Service**
3. Connecte ton repo GitHub
4. Configure :
   - **Root Directory** : `backend`
   - **Runtime** : `Python 3`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Dans **Environment Variables**, ajoute :
   - `GROQ_API_KEY` = ta clé Groq
   - `ALLOWED_ORIGINS` = `https://TON-SITE.netlify.app` (à remplir après l'étape 3)
6. **Deploy** — Render te donne une URL type `https://agent-ia-xxxx.onrender.com`

---

## Étape 3 — Déployer le frontend sur Netlify

1. Va sur **netlify.com** → crée un compte gratuit
2. **Add new site** → **Import an existing project** → GitHub
3. Sélectionne ton repo
4. Configure :
   - **Base directory** : (vide)
   - **Publish directory** : `frontend`
5. **Deploy**

Netlify te donne une URL type `https://mon-agent.netlify.app`

---

## Étape 4 — Relier les deux

### Dans `frontend/app.js` :
Remplace la ligne :
```js
const BACKEND_URL = "https://TON-BACKEND.onrender.com";
```
Par l'URL de ton backend Render, ex :
```js
const BACKEND_URL = "https://agent-ia-xxxx.onrender.com";
```

### Dans Render (Variables d'environnement) :
Mets à jour `ALLOWED_ORIGINS` avec ton URL Netlify :
```
ALLOWED_ORIGINS=https://mon-agent.netlify.app
```

Push tes changements → Netlify et Render redéploient automatiquement.

---

## ⚠️ Note Render gratuit

Le plan gratuit de Render **met le service en veille** après 15 min d'inactivité.
Le premier message après une pause peut prendre ~30s (cold start).
C'est normal, le service redémarre automatiquement.

---

## Test en local

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # Remplis GROQ_API_KEY
uvicorn main:app --reload

# Frontend (dans un autre terminal)
# Ouvre simplement frontend/index.html dans ton navigateur
# ou lance un serveur local :
cd frontend
python -m http.server 8080
# → http://localhost:8080
```
