# Fantasy F1 - Backend API

Backend API Flask per l'applicazione Fantasy F1.

## Setup

### 1. Crea un virtual environment
```bash
python -m venv venv
```

### 2. Attiva l'ambiente virtuale

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 3. Installa le dipendenze
```bash
pip install -r requirements.txt
```

### 4. Avvia il server
```bash
python app.py
```

Il server partirà su `http://localhost:5000`

## API Endpoints

### Autenticazione
- `POST /api/auth/login` - Login utente
- `POST /api/auth/register` - Registrazione nuovo utente

### Team
- `GET /api/team/<user_id>` - Recupera il team dell'utente
- `POST /api/team/<user_id>` - Salva il team dell'utente

### Leghe
- `GET /api/leagues` - Elenco tutte le leghe
- `GET /api/leagues/<code>` - Dettagli di una lega
- `POST /api/leagues/join/<user_id>/<code>` - Unisciti a una lega
- `GET /api/leagues/user/<user_id>` - Leghe dell'utente
- `GET /api/leaderboard/<league_id>` - Classifica di una lega

### Health
- `GET /api/health` - Verifica stato server

## Test con curl

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@f1.com","password":"demo123"}'

# Registrazione
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@f1.com","password":"test123"}'

# Salva team
curl -X POST http://localhost:5000/api/team/1 \
  -H "Content-Type: application/json" \
  -d '{"drivers":[...],"constructors":[...]}'
```

## Database

Il database SQLite è automaticamente creato al primo avvio in `fantasy_f1.db`.

## Deploy
- DB: Supabase
- Backend: Render (Db connection is env vars)
- Frontend: Github (backend connection in files)
