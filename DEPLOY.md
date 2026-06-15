# CSIRT Autopilot — Deploy Guide (Railway + Vercel)

## Files changed and where they go

| Output file           | Destination in your repo                                      |
|-----------------------|---------------------------------------------------------------|
| main.py               | backend/main.py                (replace)                      |
| database.py           | backend/db/database.py         (replace)                      |
| useIncidentStream.ts  | frontend/src/hooks/useIncidentStream.ts  (replace)            |
| vite.config.ts        | frontend/vite.config.ts        (replace)                      |
| Procfile              | backend/Procfile               (new file)                     |
| railway.toml          | railway.toml (repo root)       (new file)                     |
| .env.production       | frontend/.env.production       (new file)                     |
| vercel.json           | frontend/vercel.json           (new file)                     |

---

## PART 1 — Railway (Backend)

### Step 1 — Push all file changes to GitHub
```
git add .
git commit -m "chore: Railway + Vercel deploy config"
git push
```

### Step 2 — Create Railway project
1. Go to https://railway.app and sign in with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your csirt-autopilot repo
4. Railway auto-detects Python via nixpacks — let it build

### Step 3 — Add a persistent volume (critical for SQLite)
1. In your Railway service, go to "Volumes" tab
2. Click "Add Volume"
3. Mount path: /data
4. This survives redeploys. Without this, your DB resets every deploy.

### Step 4 — Set environment variables in Railway
Go to your service → "Variables" tab, add ALL of these:

```
FRONTEND_ORIGIN=https://your-app.vercel.app        ← fill after Vercel deploy
DB_PATH=/data/csirt_incidents.db
GROQ_API_KEY=your_groq_key
GITHUB_TOKEN=your_github_token                      ← if using GitHub Issues
SLACK_WEBHOOK_URL=your_slack_webhook                ← if using Slack
ABUSEIPDB_API_KEY=your_key                         ← if using enrichment
```

### Step 5 — Get your Railway URL
After deploy succeeds, Railway shows a URL like:
  https://csirt-autopilot-production.up.railway.app

Test it:
```
curl https://csirt-autopilot-production.up.railway.app/api/v1/incidents
```
Should return []. If you get a 502, check the deploy logs.

---

## PART 2 — Vercel (Frontend)

### Step 1 — Update .env.production
Edit frontend/.env.production with your actual Railway URL:
```
VITE_API_URL=https://csirt-autopilot-production.up.railway.app
VITE_WS_URL=wss://csirt-autopilot-production.up.railway.app/ws/incidents
```

### Step 2 — Check your API client
In frontend/src/api/client.ts, the base URL must read from env:
```ts
const BASE_URL = import.meta.env.VITE_API_URL ?? "";
```
If it's hardcoded to localhost, change it now.

### Step 3 — Deploy to Vercel
Option A — Vercel CLI (recommended):
```
npm i -g vercel
cd frontend
vercel --prod
```
When prompted:
- Root directory: frontend
- Framework: Vite
- Build command: npm run build
- Output directory: dist

Option B — Vercel Dashboard:
1. Go to https://vercel.com → "Add New Project"
2. Import your GitHub repo
3. Set Root Directory to: frontend
4. Framework Preset: Vite
5. Click Deploy

### Step 4 — Add env vars in Vercel dashboard
Go to your Vercel project → Settings → Environment Variables, add:
```
VITE_API_URL = https://csirt-autopilot-production.up.railway.app
VITE_WS_URL  = wss://csirt-autopilot-production.up.railway.app/ws/incidents
```
Then go to Deployments → Redeploy (env vars don't apply until redeploy).

### Step 5 — Update FRONTEND_ORIGIN on Railway
Now that you have your Vercel URL (e.g. https://csirt-autopilot.vercel.app),
go back to Railway → Variables and set:
```
FRONTEND_ORIGIN=https://csirt-autopilot.vercel.app
```
Railway redeploys automatically.

---

## Verification checklist

- [ ] curl Railway /api/v1/incidents returns []
- [ ] Open Vercel URL, incident feed loads without console CORS errors
- [ ] "Live" indicator in top right turns green (WebSocket connected)
- [ ] Submit a log — incident appears in feed
- [ ] Agent Log tab does not auto-scroll when you're reading mid-log

---

## Common failures

**CORS error in browser console**
  → FRONTEND_ORIGIN on Railway does not match your exact Vercel URL.
  → Include https://, no trailing slash.

**WebSocket stuck "connecting"**
  → VITE_WS_URL starts with wss:// not https://
  → Railway plan: free tier may not support WebSockets — upgrade to Hobby ($5/mo)

**DB resets on redeploy**
  → Volume not mounted, or DB_PATH not set to /data/csirt_incidents.db

**Vercel 404 on page refresh**
  → vercel.json not in frontend/ directory, or not committed to git

**502 on Railway immediately after deploy**
  → Check Railway logs. Usually a missing env var (GROQ_API_KEY etc.)
  → The healthcheck hits /api/v1/incidents — if DB init fails, it 502s
