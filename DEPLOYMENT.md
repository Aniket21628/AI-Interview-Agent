# Deployment guide

This project has two deployable parts:

- Frontend: Next.js app in the client folder
- Backend: current JavaScript server in server, or the Python migration in server-py

## 1) Backend deployment on Render

### Option A: Python backend on Render

1. Push the repository to GitHub.
2. In Render, create a new Web Service.
3. Connect the repository and choose the branch.
4. Set the root directory to the project root.
5. Use the following build/start settings:
   - Build command: `python -m pip install --upgrade pip && pip install -r server-py/requirements.txt`
   - Start command: `uvicorn server-py.main:socket_app --host 0.0.0.0 --port 10000`
6. Set environment variables in Render:
   - `LLM_PROVIDER=gemini`
   - `GOOGLE_API_KEY=your_google_key`
   - `PORT=10000`
   - `CLIENT_URL=https://your-frontend-domain.vercel.app`
   - `ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app,http://localhost:3000`
7. Add a health check route if desired, but the default `/health` endpoint already exists.
8. Save and deploy.

### Option B: Keep the JavaScript backend on Render

If you want to keep the current backend, use the same Render web service pattern with the existing Node app:

- Root directory: project root
- Build command: `npm install`
- Start command: `npm run start`
- Environment variables:
  - `PORT=10000`
  - `CLIENT_URL=https://your-frontend-domain.vercel.app`

## 2) Frontend deployment on Vercel

1. Open Vercel and import the repository.
2. Set the project root to the repository root.
3. Set the framework to Next.js automatically.
4. In the project root, the app is under the client folder. If needed, set the app directory to `client` depending on your Vercel project config.
5. Add environment variables:
   - `NEXT_PUBLIC_SERVER_URL=https://your-backend-url.onrender.com`
6. Deploy.

## 3) Local development

### Python backend

```bash
cd e:/interview-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r server-py/requirements.txt
python -m uvicorn server-py.main:socket_app --host 0.0.0.0 --port 5000
```

### Frontend

```bash
cd e:/interview-agent/client
npm install
npm run dev
```

## 4) CORS notes

The backend allows a list of allowed origins. For local development the default values are:

- `http://localhost:3000`
- `http://127.0.0.1:3000`

For deployment, set `CLIENT_URL` and `ALLOWED_ORIGINS` to your Vercel frontend URL.

## 5) Recommended setup for this project

For a clean portfolio-friendly setup:

- Use Vercel for the Next.js frontend
- Use Render for the Python backend
- Keep the original JS server in the repo as a fallback reference
- Use the Python backend as the main migration target

## 6) Quick checklist

- [ ] GitHub repo connected
- [ ] Render backend service created
- [ ] Vercel frontend created
- [ ] `NEXT_PUBLIC_SERVER_URL` added in Vercel
- [ ] `CLIENT_URL` and `ALLOWED_ORIGINS` added in Render
- [ ] `GOOGLE_API_KEY` or `OPENAI_API_KEY` set
- [ ] Health route tested
- [ ] Socket connection tested
