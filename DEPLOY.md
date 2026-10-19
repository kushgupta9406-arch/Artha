# Deploying ARTHA with Ask ARTHA built in

Goal: a public link that anyone (e.g. a faculty reviewer) can open, with **Ask ARTHA** working
straight away and no API key on their side. The Anthropic key is stored only on the server as a
secret; the browser never receives it.

The recommended host is **Streamlit Community Cloud** (free, runs `app.py` directly, has a built-in
secrets store). Any other Python host works the same way if you set the variables listed in
step 4 as environment variables.

---

## 1. Choose the Ask ARTHA engine (free options first)

| Option | Cost | What to put in Secrets |
|---|---|---|
| **Offline mode** (default) | Free, no sign-up | nothing — answers set question types straight from ARTHA's data |
| **Groq free plan** (recommended) | Free (about 1,000 questions a day on the free plan) | `GROQ_API_KEY = "gsk_..."` from <https://console.groq.com/keys> |
| Claude | Paid | `ANTHROPIC_API_KEY = "sk-ant-..."` |

If the free AI plan is busy or unreachable, Ask ARTHA automatically falls back to the offline answer.

### Optional: Claude API key and spend cap

1. Sign in at <https://console.anthropic.com>, add billing credit, and create an API key.
2. In **Settings → Limits**, set a monthly spend limit you are comfortable with. This is the real
   safety net for a public site.
3. ARTHA adds its own guards on top: max questions per browser session (default 25), max
   questions per day for the whole site (default 300), at most 6 lookup rounds and ~1,400 output
   tokens per answer, and prompt caching to cut repeat cost.

## 2. Build the live snapshot and the validation results on your laptop

Yahoo Finance often throttles requests from shared cloud servers, so create the live data locally
and ship it with the app. From the project folder (Windows PowerShell):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe pipeline\live_refresh.py        # prices + latest fundamentals + full rerank (~10–15 min first time)
.\.venv\Scripts\python.exe pipeline\validation.py          # Pearson validation (~5 min first time)
```

This writes `data/live/` (live ranking, provenance, reconciliation) and `data/validation/`
(`validation.json` + CSVs). If some tickers fail because Yahoo rate-limited you, run
`live_refresh.py` again: already-downloaded statements are reused from cache for 20 hours.

## 3. Put the project on GitHub

1. Create a new repository on GitHub (private is fine).
2. In the project folder:

```powershell
git init
git add .
git commit -m "ARTHA with live fundamentals, Ask ARTHA and validation"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

`.gitignore` already keeps out `.streamlit/secrets.toml`, the virtual environment and download
caches. Never commit a file containing your API key.

## 4. Deploy on Streamlit Community Cloud

1. Go to <https://share.streamlit.io>, sign in with GitHub, click **Create app → Deploy a public app from GitHub**.
2. Repository: your repo · Branch: `main` · Main file path: `app.py`.
3. **Advanced settings**: choose Python 3.12, and paste this into **Secrets**:

```toml
GROQ_API_KEY = "gsk_..."                 # free; leave out to use offline mode
ARTHA_ADMIN_PASSWORD = "pick-a-password"
# optional:
# ARTHA_MODEL = "openai/gpt-oss-120b"   # Groq model with tool calling
# ARTHA_MAX_QUESTIONS_PER_SESSION = 25
# ARTHA_MAX_QUESTIONS_PER_DAY = 300
```

4. Click **Deploy**. After a few minutes you get a link like `https://<name>.streamlit.app`.
   Share that link. Set the app's sharing to public if you want reviewers to open it without a
   Streamlit login.

## 5. What visitors can and cannot do

| Feature | Visitor | You (after entering the admin password in the sidebar) |
|---|---|---|
| All pages, Historical/Live switch, Ask ARTHA | ✅ | ✅ |
| Refresh live data & rerank | – (sees your latest snapshot) | ✅ |
| Run validation | – | ✅ |
| Rebuild data / upload Capitaline files | – | ✅ |

Admin tools are open when no `ARTHA_ADMIN_PASSWORD` is set, which is what you want on your laptop.

## 6. Updating the site

Re-run step 2 on your laptop, then:

```powershell
git add data/live data/validation
git commit -m "Refresh live snapshot"
git push
```

Streamlit Cloud redeploys automatically. (You can also press *Refresh live data & rerank* on the
deployed site as admin; if Yahoo blocks the server, the committed snapshot stays in use. Files
written on the server are lost when the app restarts, so committing is the durable route.)

## Running Ask ARTHA locally

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, paste your key, then
`streamlit run app.py`. Alternatively set an environment variable:
`$env:ANTHROPIC_API_KEY = "sk-ant-..."` in PowerShell before starting Streamlit.

## Troubleshooting

- *"Ask ARTHA is not configured on this server"* → `ANTHROPIC_API_KEY` is missing from Secrets.
- *"key was rejected"* → the key was revoked or mistyped; create a new one.
- *"model … was not found"* → set `ARTHA_MODEL` to a model your account can use.
- The app sleeps after a period without visitors on the free tier; the first visit wakes it in about a minute.
