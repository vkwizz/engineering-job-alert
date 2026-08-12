# Engineering Opportunity Intelligence Agent

A personal, automated job/internship intelligence system for engineering students. 
Discovers new opportunities from major job sources, filters aggressively according to user technical and company preferences, ranks the remaining jobs with deterministic rules and AI classification, and sends high-value alerts via Telegram and Email.

---

## Local Setup

1. **Create Virtual Environment:**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Unix:
   source venv/bin/activate
   ```

2. **Install Dependencies:**
   ```bash
   pip install -e .
   ```

3. **Environment Variables:**
   Copy `.env.example` to `.env` and fill in your API keys (`OPENAI_API_KEY`, `SERPAPI_API_KEY`, `TELEGRAM_BOT_TOKEN`, etc.).

4. **Configuration:**
   Update the YAML files in `config/` (`user_preferences.yaml` and `companies.yaml`) as needed.

---

## Running the Agent Locally

### One-Time / CLI Execution:
```bash
python -m src.job_alert.main
```

### Full-Time Server & Continuous Scheduler:
```bash
python -m src.job_alert.server
```
- Health Check: `http://localhost:10000/health`
- Manual Trigger: `http://localhost:10000/run`

---

## Pushing to GitHub

1. Initialize Git repository (if not already done):
   ```bash
   git init -b main
   git add .
   git commit -m "Initial commit for engineering job alert system"
   ```

2. Link your GitHub repository and push:
   ```bash
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/engineering-job-alert.git
   git push -u origin main
   ```

---

## Deploying 24/7 Full-Time on Render

### Option A: Using Render Blueprint (`render.yaml`) - **Recommended**

1. Go to [Render Dashboard](https://dashboard.render.com/) -> **New +** -> **Blueprint**.
2. Connect your GitHub repository (`engineering-job-alert`).
3. Render will detect `render.yaml` and automatically configure:
   - **Web Service**: `engineering-job-alert-service` (Runs 24/7 with FastAPI + APScheduler)
   - **PostgreSQL Database**: `job-alert-db`
4. Under Environment Variables for `engineering-job-alert-service`, fill in your secrets:
   - `OPENAI_API_KEY`
   - `SERPAPI_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `GMAIL_SENDER_ADDRESS` / `SMTP_PASSWORD`

### Option B: Free Tier 24/7 Keep-Alive Setup

Render Free Web Services sleep after 15 minutes of HTTP inactivity. To keep it running **100% free 24/7**:
1. Once deployed on Render, copy your service's URL (e.g. `https://engineering-job-alert-service.onrender.com`).
2. Create a free account at [UptimeRobot.com](https://uptimerobot.com/) or [Cron-job.org](https://cron-job.org/).
3. Add an HTTP monitor to ping `https://engineering-job-alert-service.onrender.com/health` every **5 or 10 minutes**.
4. This keeps your Render container active full-time so the internal scheduler runs continuously!
