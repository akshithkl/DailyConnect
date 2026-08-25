# DailyConnect

> **Connect. Share. Chat.**

DailyConnect is a small-scale social communication platform for sharing photo moments and staying in touch. It is designed as a clear, interview-friendly portfolio project using one FastAPI backend, one database, and a simple React client.

## Live Demo

- **Website:** [dailyconnect-frontend.onrender.com](https://dailyconnect-frontend.onrender.com)
- **API documentation:** [dailyconnect-api.onrender.com/docs](https://dailyconnect-api.onrender.com/docs)

The free backend may take a few seconds to wake after inactivity. Create an account to explore the feed, comments, photo publishing, search, and messaging features.

## Features

- Account registration, login, JWT authentication, and logout
- Editable user profiles with bios and profile photos
- Photo posts with captions, likes, comments, and owner-only deletion
- Username search with a direct message action
- One-to-one conversations with real-time text messages over WebSockets
- Image validation, resizing, and JPEG compression before storage
- Responsive interface for desktop and mobile screens

## Technology

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite, JavaScript, Axios, React Router |
| Backend | Python, FastAPI, SQLAlchemy, Pydantic, Uvicorn |
| Authentication | JWT and PBKDF2 password hashing |
| Local database | SQLite |
| Production database | PostgreSQL, such as Neon or Supabase |
| Image storage | Cloudinary in production, local uploads in development |

## Architecture

```mermaid
flowchart LR
	Browser[React and Vite] -->|REST and WebSocket| API[FastAPI]
	API --> DB[(SQLite locally or PostgreSQL)]
	API --> Images[Cloudinary images]
```

The browser sends API requests to FastAPI. The backend authenticates users, validates ownership, and stores application data with SQLAlchemy. Images are compressed before being sent to Cloudinary. The database stores the image identifier, not the image binary.

## Project structure

```text
DailyConnect/
├── backend/
│   ├── app/
│   │   ├── core/          # Settings, database, security
│   │   ├── routers/       # Auth, users, posts, messaging
│   │   ├── services/      # Image storage
│   │   ├── models.py
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── services/      # Axios API client
│   │   ├── App.jsx
│   │   └── styles.css
│   └── package.json
├── render.yaml
└── README.md
```

## Local development

### 1. Backend

From PowerShell:

```powershell
cd E:\DailyConnect
C:\Users\akshi\AppData\Local\Programs\Python\Python314\python.exe -m pip install -r backend\requirements.txt
C:\Users\akshi\AppData\Local\Programs\Python\Python314\python.exe -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

The API runs at `http://127.0.0.1:8000`. Open `http://127.0.0.1:8000/docs` for Swagger API documentation.

### 2. Frontend

Open a second terminal:

```powershell
cd E:\DailyConnect\frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, usually `http://localhost:5173`.

The local backend uses SQLite and creates `backend/dailyconnect.db`. Without Cloudinary credentials, compressed images are stored in `backend/uploads` for local testing.

## Environment variables

Copy `backend/.env.example` to `backend/.env` for local configuration. Never commit `.env` files.

### Backend

```env
DATABASE_URL=sqlite:///./dailyconnect.db
SECRET_KEY=replace-with-a-long-random-value
FRONTEND_URL=http://localhost:5173
API_URL=http://127.0.0.1:8000
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
```

### Frontend

```env
VITE_API_URL=http://127.0.0.1:8000
```

When `CLOUDINARY_URL` is empty, local image storage is used. For production, use a managed PostgreSQL URL and a real Cloudinary URL.

## API overview

| Area | Endpoints |
| --- | --- |
| Authentication | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` |
| Users | `GET /api/users/search`, `GET /api/users/username/{username}`, `PUT /api/users/me` |
| Posts | `POST /api/posts`, `GET /api/posts`, `DELETE /api/posts/{id}` |
| Likes | `POST/DELETE /api/posts/{id}/like` |
| Comments | `POST/GET /api/posts/{id}/comments`, `DELETE /api/comments/{id}` |
| Conversations | `GET/POST /api/conversations`, `GET /api/conversations/{id}/messages` |
| Real-time chat | WebSocket `/api/conversations/ws/chat/{conversation_id}` |

All write endpoints require a JWT bearer token. Conversation access is checked before messages are returned or WebSocket connections are accepted.

## Deploy on Render

The root [render.yaml](render.yaml) defines the API and frontend services.

1. Push this repository to GitHub.
2. Create a PostgreSQL database on Neon or Supabase.
3. Create a Cloudinary account and copy the `CLOUDINARY_URL` from the dashboard.
4. In Render, choose **New > Blueprint** and select this repository.
5. Set `DATABASE_URL`, `FRONTEND_URL`, `API_URL`, and `CLOUDINARY_URL` on `dailyconnect-api`.
6. Set `VITE_API_URL` on `dailyconnect-frontend` to the deployed API URL.
7. Deploy both services and test registration, login, photo upload, comments, deletion, and messaging.

Use the exact URLs generated by Render. For example:

```text
FRONTEND_URL=https://dailyconnect-frontend.onrender.com
API_URL=https://dailyconnect-api.onrender.com
VITE_API_URL=https://dailyconnect-api.onrender.com
```

Free Render services can sleep after inactivity. This delays the first request but does not delete data stored in managed PostgreSQL or Cloudinary.

## Security notes

- Passwords are hashed and never stored as plain text.
- JWT-protected routes validate the current user.
- Users can delete only their own posts and comments.
- Private conversations validate membership.
- Uploads accept JPG, PNG, and WEBP files up to 5 MB.
- Images are resized and compressed before storage.
- Secrets belong in hosting-provider environment variables, not source control.

## Future improvements

Refresh tokens, pagination, profile photo controls, chat image messages, automated tests, moderation, unread counts, and database migrations can be added as the project grows.
