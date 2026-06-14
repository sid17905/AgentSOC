# AgentSOC

Member D implementation for CSIRT Autopilot: multimodal image OCR, incident reporting, Slack alert fallback, and GitHub Issues ticket creation.

See `MEMBER_D_INTEGRATION.md` for wiring instructions for Member A.

## Run in WSL

Backend:

```bash
cd /mnt/c/Users/shubham/Documents/AgentSOC
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd /mnt/c/Users/shubham/Documents/AgentSOC/frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Open `http://localhost:5173`.

## Automatic Ingestion

To analyze files automatically without uploading them in the UI, enable the folder watcher:

```bash
mkdir -p samples/inbox samples/processed samples/failed
export AUTO_INGEST_ENABLED=true
export AUTO_INGEST_DIR=samples/inbox
export AUTO_INGEST_ARCHIVE_DIR=samples/processed
export AUTO_INGEST_ERROR_DIR=samples/failed
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Drop `.log`, `.txt`, `.json`, `.eml`, `.pdf`, `.png`, `.jpg`, or `.webp` files into `samples/inbox`. The backend will analyze each file, send live updates to the dashboard, then move processed files to `samples/processed`. Files that cannot be ingested are moved to `samples/failed`.

To fetch logs automatically every N seconds from a live log file or URL:

```bash
touch samples/live.log
export AUTO_FETCH_ENABLED=true
export AUTO_FETCH_SOURCES=samples/live.log
export AUTO_FETCH_INTERVAL_SECONDS=30
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Append new log lines and they will be analyzed on the next fetch interval:

```bash
cat >> samples/live.log <<'EOF'
Jan 15 14:22:01 web-01 sshd[1234]: Failed password for root from 185.220.101.5 port 22
EOF
```

You can use multiple sources separated by commas:

```bash
export AUTO_FETCH_SOURCES=samples/live.log,/var/log/auth.log,http://localhost:9000/latest-alerts
```
