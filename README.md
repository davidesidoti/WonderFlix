# 🍿 WonderFlix

Un **Discord Bot** self‑hosted in **Python** per gestire il tuo media server (Jellyfin, Sonarr, Radarr, Jellyseerr) direttamente dal server Discord.

[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-v2.4.0‑%2B-yellow)](https://discordpy.readthedocs.io/)

---

## 🔧 Funzionalità principali

- `/request-movie` e `/request-series`: richiedi direttamente nuovi contenuti
- Notifiche Discord su **nuovi episodi/film** o **upgrade di qualità**
- Cultura sicura delle credenziali da `.env`
- Struttura modulare (cogs), logging e gestione errori robusta
- Self‑hosting easy su Alpine Linux con init tramite **OpenRC**

---

## 🚀 Installazione

### Prerequisiti
- Python 3.10+
- Alpine Linux (compatibile con musl)
- OpenRC configurato

### Setup
```bash
git clone https://github.com/tuo-username/wonderflix.git
cd wonderflix
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
````

### Configura `.env`

```dotenv
DISCORD_TOKEN=your_token
JELLYFIN_URL=http://localhost:8096
JELLYFIN_APIKEY=...
RADARR_URL=...
RADARR_APIKEY=...
SONARR_URL=...
SONARR_APIKEY=...
JELLYSEERR_URL=...
JELLYSEERR_APIKEY=...
```

---

## ▶️ Esecuzione

```bash
python main.py
```

### ✅ Test

Utilizza `pytest` per eseguire i test:

```bash
pytest
```

---

## 📚 Esempi d’uso

```markdown
/user request-movie "Inception"
```

→ Notifica in canale dedicato + comando a Radarr.

```markdown
/user request-series "Stranger Things"
```

---

## ✨ Roadmap

* [x] `/request-*` commands
* [ ] Auto-clean libreria (cancella vecchi episodi)
* [ ] Notifiche avanzate "quality upgrade"
* [ ] Dashboard web integrata

---

## 🛠️ Architettura & Best Practice

* Usa `discord.ext.commands` + `discord.Embed`
* `.env` via `os.getenv`
* Logging configurato (level, file/console)
* Servizio init con OpenRC: `rc-service wonderflix start`

---

## ⚠️ Sicurezza

* Nessuna credentiale hardcoded
* I permessi Discord configurati con cautela
* Validazione dei payload da API esterne

---

## 📝 Licenza

Licenza MIT – vedi [`LICENSE`](LICENSE).
