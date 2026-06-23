# SotuHire Local Scripts

## Web-first launcher

From the repository root:

```powershell
.\start-sotuhire.ps1
```

The launcher starts the FastAPI layer at `http://127.0.0.1:8787`, starts the
modern frontend at `http://localhost:5173`, waits for both services and opens the
browser.

Useful flags:

```powershell
.\start-sotuhire.ps1 -NoBrowser
.\start-sotuhire.ps1 -SkipInstall
.\start-sotuhire.ps1 -ApiOnly
.\start-sotuhire.ps1 -WebOnly
.\start-sotuhire.ps1 -Production
```

Default local CORS:

```txt
SOTUHIRE_API_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173
```

## Manual mode

API:

```powershell
python scripts/run_api.py
```

Frontend:

```powershell
cd apps/web
npm install
npm run dev
```

Streamlit remains available for legacy/dev/local debugging and is not started by
the web-first launcher.
