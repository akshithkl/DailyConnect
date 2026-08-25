# DailyConnect

**Connect. Share. Chat.**

DailyConnect is a small portfolio social app built with React, FastAPI, SQLite, and Cloudflare R2. It demonstrates authentication, profiles, photo posts, likes, comments, user search, and private real-time messaging without introducing microservices or complex infrastructure.

## Run locally

1. Copy `backend/.env.example` to `backend/.env` and set `SECRET_KEY`. The app uses SQLite locally and creates `backend/dailyconnect.db` automatically.
2. Install backend dependencies: `pip install -r backend/requirements.txt`.
3. Start the API from `backend`: `uvicorn app.main:app --reload`.
4. Start the frontend with `npm install` and `npm run dev` from `frontend`.

R2 settings are required for permanent image uploads. The service validates JPG, PNG, and WEBP files at 5 MB and stores only object keys in SQL.

## Architecture

React calls FastAPI over REST for accounts, profiles, posts, and conversation history. FastAPI uses SQLAlchemy for SQLite and boto3 for Cloudflare R2. A WebSocket at `/api/conversations/ws/chat/{conversation_id}` authenticates with the JWT query parameter, checks conversation membership, saves messages, and broadcasts them to connected members. This single-process connection manager is intentionally suitable for a small app.

## Data model

`users` has one `profile`; `posts` belong to users and have unique `(user_id, post_id)` likes. Comments belong to users and posts. Conversations have two `conversation_members`, and messages belong to a conversation and sender. Foreign keys cascade child records.

## Main API

- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `GET /api/users/search?q=`, `GET /api/users/username/{username}`, `PUT /api/users/me`
- `POST /api/posts`, `GET /api/posts`, `POST/DELETE /api/posts/{id}/like`
- `POST/GET /api/posts/{id}/comments`, `DELETE /api/comments/{id}`
- `GET/POST /api/conversations`, `GET /api/conversations/{id}/messages`

## Deployment

The repository includes `render.yaml` for the Render backend and frontend services.

1. Push the project to GitHub.
2. Create a free PostgreSQL database on Neon or Supabase and copy its connection string.
3. Create a Cloudflare R2 bucket and public URL for images.
4. In Render, choose **New > Blueprint**, connect the GitHub repository, and select `render.yaml`.
5. Set `DATABASE_URL` to the PostgreSQL connection string.
6. After Render creates the URLs, set `FRONTEND_URL` and `API_URL` on `dailyconnect-api`.
7. Set `VITE_API_URL` on `dailyconnect-frontend` to the API URL, then redeploy the frontend.
8. Open the frontend URL and test registration, photo upload, comments, and deletion.

Use `uvicorn app.main:app --host 0.0.0.0 --port $PORT` for the backend. SQLite and `backend/uploads` are suitable for local development only; use PostgreSQL and R2 for permanent production data and images. Free Render services may sleep after inactivity, but sleeping does not delete hosted database or R2 data.

## Future improvements

Add refresh tokens, pagination, moderation, unread counts, automated tests, and a multi-instance WebSocket broker only when product scale requires them.
