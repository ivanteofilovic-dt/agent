# Deployment Guide - Easiest Options

This guide covers the **easiest** ways to deploy the Combined Agent Platform. For more advanced options, see [GOOGLE_CLOUD_DEPLOYMENT.md](GOOGLE_CLOUD_DEPLOYMENT.md).

## 🚀 Option 1: Streamlit Cloud (Easiest - Recommended)

**Streamlit Cloud** is the absolute easiest way to deploy a Streamlit app. It's free, requires no Docker configuration, and deploys automatically from GitHub.

### Prerequisites
- GitHub account
- Repository pushed to GitHub

### Steps

1. **Push your code to GitHub** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/combined-agent.git
   git push -u origin main
   ```

2. **Go to [Streamlit Cloud](https://streamlit.io/cloud)**
   - Sign in with your GitHub account
   - Click "New app"

3. **Configure your app**:
   - **Repository**: Select your `combined-agent` repository
   - **Branch**: `main` (or your default branch)
   - **Main file path**: `app.py`
   - **Python version**: 3.12

4. **Add your secrets** (environment variables):
   - Click "Advanced settings"
   - Add each secret:
     - `ANTHROPIC_API_KEY` = `your_anthropic_api_key`
     - `SALESFORCE_CLIENT_ID` = `your_client_id` (if using Salesforce)
     - `SALESFORCE_CLIENT_SECRET` = `your_client_secret` (if using Salesforce)
     - `SALESFORCE_REFRESH_TOKEN` = `your_refresh_token` (if using Salesforce)
     - `SALESFORCE_INSTANCE_URL` = `https://yourinstance.salesforce.com` (if using Salesforce)
     - `SLACK_BOT_TOKEN` = `xoxb-your-token` (if using Slack)
     - `SLACK_SIGNING_SECRET` = `your-secret` (if using Slack)

5. **Deploy!**
   - Click "Deploy"
   - Your app will be live at `https://your-app-name.streamlit.app`

### Advantages
- ✅ **Free tier available**
- ✅ **Zero configuration** - no Docker, no build scripts
- ✅ **Automatic deployments** on git push
- ✅ **Built-in HTTPS**
- ✅ **Handles dependencies automatically** from `pyproject.toml`

### Limitations
- ⚠️ Free tier has resource limits
- ⚠️ App sleeps after inactivity (wakes on first request)
- ⚠️ No custom domain on free tier

---

## 🚂 Option 2: Railway (Very Easy)

**Railway** is another excellent option that's almost as easy as Streamlit Cloud, with more flexibility.

### Prerequisites
- GitHub account
- Railway account (free tier available)

### Steps

1. **Push your code to GitHub** (if not already done)

2. **Go to [Railway](https://railway.app)**
   - Sign in with GitHub
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure the service**:
   - Railway will auto-detect it's a Python app
   - **Start Command**: `streamlit run app.py --server.port $PORT`
   - Railway automatically sets the `PORT` environment variable

4. **Add environment variables**:
   - Go to "Variables" tab
   - Add all your secrets (same as Streamlit Cloud above)

5. **Deploy!**
   - Railway will automatically build and deploy
   - Your app will be live at `https://your-app-name.up.railway.app`

### Create a `Procfile` (optional but recommended)

Create a `Procfile` in the root directory:
```
web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

### Advantages
- ✅ **Free tier with $5 credit/month**
- ✅ **More flexible** than Streamlit Cloud
- ✅ **Custom domains** available
- ✅ **Better for production** workloads
- ✅ **Automatic HTTPS**

---

## 🎨 Option 3: Render (Very Easy)

**Render** is similar to Railway and also very easy to use.

### Prerequisites
- GitHub account
- Render account (free tier available)

### Steps

1. **Push your code to GitHub**

2. **Go to [Render](https://render.com)**
   - Sign in with GitHub
   - Click "New +" → "Web Service"
   - Connect your repository

3. **Configure the service**:
   - **Name**: `combined-agent` (or your choice)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -e .` or `uv sync` (if uv is available)
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

4. **Add environment variables**:
   - Scroll to "Environment Variables"
   - Add all your secrets

5. **Deploy!**
   - Click "Create Web Service"
   - Your app will be live at `https://your-app-name.onrender.com`

### Advantages
- ✅ **Free tier available**
- ✅ **Simple setup**
- ✅ **Automatic HTTPS**
- ⚠️ Free tier apps sleep after 15 minutes of inactivity

---

## 🐳 Option 4: Docker + Any Platform (More Setup, More Control)

If you want more control or need to deploy to a specific platform, you can containerize the app.

### Create a Dockerfile

Create a `Dockerfile` in the root directory:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the app
ENTRYPOINT ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Create a `.dockerignore`

```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
.env
.git/
.gitignore
*.md
docs/
```

### Deploy to Docker-compatible platforms

Once you have a Dockerfile, you can deploy to:
- **Fly.io** - `flyctl launch`
- **DigitalOcean App Platform** - Connect GitHub repo
- **AWS App Runner** - Connect container registry
- **Google Cloud Run** - `gcloud run deploy`
- **Azure Container Apps** - Connect container registry

---

## 📊 Comparison Table

| Platform | Ease | Free Tier | Auto-Deploy | Custom Domain | Best For |
|----------|------|-----------|-------------|---------------|----------|
| **Streamlit Cloud** | ⭐⭐⭐⭐⭐ | ✅ | ✅ | ❌ (paid) | Streamlit apps |
| **Railway** | ⭐⭐⭐⭐ | ✅ ($5/mo) | ✅ | ✅ | Production apps |
| **Render** | ⭐⭐⭐⭐ | ✅ | ✅ | ✅ | Simple deployments |
| **Docker** | ⭐⭐⭐ | Varies | Varies | Varies | Custom requirements |

---

## 🔒 Security Best Practices

Regardless of which platform you choose:

1. **Never commit secrets** to Git
   - Use `.gitignore` to exclude `.env` files
   - Use platform secrets/environment variables

2. **Use HTTPS** (all platforms above provide this automatically)

3. **Set up monitoring** (most platforms provide basic monitoring)

4. **Regular updates** - Keep dependencies updated

---

## 🚀 Quick Start Recommendation

**For the absolute easiest deployment:**

1. Push your code to GitHub
2. Use **Streamlit Cloud** (Option 1)
3. Add your secrets in the Streamlit Cloud dashboard
4. Deploy!

**Total time: ~5 minutes** ⚡

---

## 📝 Next Steps After Deployment

1. **Test your deployment** - Make sure all features work
2. **Set up monitoring** - Monitor logs and errors
3. **Configure custom domain** (if needed, on paid tiers)
4. **Set up CI/CD** - Most platforms auto-deploy on git push
5. **Backup your secrets** - Store them securely

---

## 🆘 Troubleshooting

### App won't start
- Check that all required environment variables are set
- Verify your `app.py` file is in the root directory
- Check platform logs for errors

### Dependencies not installing
- Ensure `pyproject.toml` is in the root directory
- For platforms using pip, you may need a `requirements.txt` (see below)

### Port issues
- Make sure your start command uses `$PORT` environment variable
- Streamlit Cloud handles this automatically

### Creating requirements.txt (if needed)

Some platforms prefer `requirements.txt`. You can generate one:

```bash
# If using uv
uv pip compile pyproject.toml -o requirements.txt

# Or manually extract from pyproject.toml
```

---

## 📚 Additional Resources

- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [Railway Documentation](https://docs.railway.app)
- [Render Documentation](https://render.com/docs)
- [Google Cloud Deployment Guide](GOOGLE_CLOUD_DEPLOYMENT.md) (for advanced setup)
