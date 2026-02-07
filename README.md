# HOW.IS.STAT

A cricket stats trump-card game. Challenger vs Defender, real stats, AI opponent.

You and an AI each hold 7 player cards. The Challenger declares a stat (e.g. "Most runs in IPL"), the Defender picks a card to compete — stats are resolved via Cricinfo + Gemini, and the winner keeps both cards. First side to 0 cards loses.

Play in the **terminal** (CLI) or in the **browser** (Next.js frontend + Flask API).

See [HOW_TO_PLAY.md](HOW_TO_PLAY.md) for full rules.

---

## Run locally

**1. Backend (Flask API)**

```bash
cd howisstat
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp secrets/.env.example secrets/.env   # then add your GEMINI_API_KEY
python api_server.py                   # serves on http://localhost:5050
```

**2. Frontend (Next.js)**

```bash
cd howisstat/web
cp .env.example .env.local             # uses http://localhost:5050 by default
npm install
npm run dev                            # serves on http://localhost:3000
```

Open `http://localhost:3000` in your browser.

**3. Terminal CLI (optional)**

```bash
cd howisstat
source venv/bin/activate
python main/cli.py
```

---

## Push to Git

Secrets are already in `.gitignore`. Verify before pushing.

```bash
cd howisstat
git init
git remote add origin <your-repo-url>
git add .
git status                             # confirm no secrets/ or .env files listed
git commit -m "Initial commit: HOW.IS.STAT"
git branch -M main
git push -u origin main
```

---

## Deploy on GCP VM

**Get code on the VM:**

```bash
ssh <your-vm>
git clone https://github.com/<you>/howisstat.git && cd howisstat
```

Create `secrets/.env` on the VM with your `GEMINI_API_KEY` (never commit this).

**Run the stack:**

```bash
# Backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python api_server.py &                 # port 5050, binds 0.0.0.0

# Frontend
cd web
npm install
NEXT_PUBLIC_API_URL=https://howisstat.xyz npm run build
npm run start &                        # port 3000
```

**Reverse proxy (Caddy — recommended):**

Install Caddy, then create `/etc/caddy/Caddyfile`:

```
howisstat.xyz {
    handle /api/* {
        reverse_proxy localhost:5050
    }
    handle {
        reverse_proxy localhost:3000
    }
}
```

Caddy handles HTTPS (Let's Encrypt) automatically. Restart Caddy:

```bash
sudo systemctl restart caddy
```

**GCP firewall:** Open ports 80 and 443 (HTTP/HTTPS) in your VPC firewall rules.

---

## Point howisstat.xyz to the VM

1. Get your VM's **external IP** from GCP Console (Compute Engine → VM instances).
2. In your domain registrar, add a **DNS A record**:
   - Name: `@`
   - Value: `<VM external IP>`
3. Wait for DNS propagation (a few minutes to hours).
4. Visit `https://howisstat.xyz` — Caddy will auto-provision the TLS certificate on first request.

---

## Environment variables

| Variable | Where | Purpose |
|----------|-------|---------|
| `GEMINI_API_KEY` | `secrets/.env` (backend only) | Google Gemini API key for AI + stat resolution |
| `NEXT_PUBLIC_API_URL` | `web/.env.local` or build-time env | Base URL the frontend uses to call the API |
