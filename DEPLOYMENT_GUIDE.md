# mNAV API - Deployment Guide

This guide provides step-by-step instructions for deploying the mNAV API to various platforms.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Railway Deployment](#railway-deployment)
3. [Heroku Deployment](#heroku-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Manual VPS Deployment](#manual-vps-deployment)
6. [GitHub Actions Setup](#github-actions-setup)
7. [Environment Configuration](#environment-configuration)
8. [Testing Deployment](#testing-deployment)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying, ensure you have:

- Git installed and configured
- GitHub account with repository access
- Account on your chosen deployment platform
- Basic command line knowledge

## Railway Deployment

Railway is the recommended deployment platform for this API.

### Step 1: Create Railway Account

1. Visit [Railway.app](https://railway.app)
2. Sign up with GitHub (recommended) or email
3. Verify your account

### Step 2: Create New Project

1. Click **"New Project"** on Railway dashboard
2. Select **"Deploy from GitHub repo"**
3. Connect your GitHub account if not already connected
4. Select your `mnav-api` repository

### Step 3: Configure Environment (Optional)

1. Click on your project
2. Go to **Variables** tab
3. Add any custom environment variables:
   ```
   DEBUG=False
   API_KEY=your-api-key-here
   ```

### Step 4: Deploy

1. Railway automatically detects the configuration
2. Deployment starts automatically
3. Wait for build to complete (2-3 minutes)
4. Your API URL will be displayed: `https://your-app.railway.app`

### Step 5: Get Railway Token (for CI/CD)

1. Go to [Railway Dashboard](https://railway.app/account/tokens)
2. Click **"Create Token"**
3. Name it `GitHub Actions`
4. Copy the token
5. Add to GitHub repository secrets as `RAILWAY_TOKEN`

## Heroku Deployment

### Step 1: Install Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Windows
# Download installer from https://heroku.com/cli

# Ubuntu/Debian
curl https://cli-assets.heroku.com/install.sh | sh
```

### Step 2: Create Heroku App

```bash
# Login to Heroku
heroku login

# Create new app
heroku create your-mnav-api

# Add to existing repository
heroku git:remote -a your-mnav-api
```

### Step 3: Deploy

```bash
# Deploy main branch
git push heroku main

# Or deploy specific branch
git push heroku feature-branch:main
```

### Step 4: Configure Environment

```bash
# Set environment variables
heroku config:set DEBUG=False
heroku config:set API_KEY=your-api-key

# View logs
heroku logs --tail
```

### Step 5: Get Heroku API Key (for CI/CD)

1. Run `heroku auth:token`
2. Copy the token
3. Add to GitHub secrets:
   - `HEROKU_API_KEY`: Your token
   - `HEROKU_APP_NAME`: your-mnav-api
   - `HEROKU_EMAIL`: your-email@example.com

## Docker Deployment

### Local Docker

```bash
# Build image
docker build -t mnav-api .

# Run container
docker run -d \
  --name mnav-api \
  -p 80:8080 \
  -e PORT=8080 \
  mnav-api

# View logs
docker logs -f mnav-api
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "80:8080"
    environment:
      - PORT=8080
      - DEBUG=False
    restart: unless-stopped
```

Run:
```bash
docker-compose up -d
```

### Docker Hub

```bash
# Login to Docker Hub
docker login

# Tag image
docker tag mnav-api:latest yourusername/mnav-api:latest

# Push to Docker Hub
docker push yourusername/mnav-api:latest
```

## Manual VPS Deployment

### Step 1: Server Setup (Ubuntu/Debian)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx supervisor -y

# Install Git
sudo apt install git -y
```

### Step 2: Clone Repository

```bash
# Create app directory
sudo mkdir -p /var/www/mnav-api
cd /var/www/mnav-api

# Clone repository
sudo git clone https://github.com/yourusername/mnav-api.git .

# Set permissions
sudo chown -R www-data:www-data /var/www/mnav-api
```

### Step 3: Setup Python Environment

```bash
# Create virtual environment
sudo python3 -m venv venv

# Activate environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Configure Supervisor

Create `/etc/supervisor/conf.d/mnav-api.conf`:

```ini
[program:mnav-api]
command=/var/www/mnav-api/venv/bin/gunicorn app:app --bind 127.0.0.1:8000 --workers 2
directory=/var/www/mnav-api
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/mnav-api.log
environment=PATH="/var/www/mnav-api/venv/bin",PORT="8000"
```

### Step 5: Configure Nginx

Create `/etc/nginx/sites-available/mnav-api`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/health {
        proxy_pass http://127.0.0.1:8000/api/health;
        proxy_read_timeout 10s;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/mnav-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo supervisorctl reread
sudo supervisorctl update
```

## GitHub Actions Setup

### Step 1: Add Repository Secrets

Go to your GitHub repository → Settings → Secrets → Actions

Add these secrets based on your deployment platform:

#### For Railway:
- `RAILWAY_TOKEN`: Your Railway API token

#### For Heroku:
- `HEROKU_API_KEY`: Your Heroku API key
- `HEROKU_APP_NAME`: Your Heroku app name
- `HEROKU_EMAIL`: Your Heroku email

#### For Docker Hub:
- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_PASSWORD`: Your Docker Hub password

### Step 2: Enable Workflows

1. Go to Actions tab in your repository
2. Enable workflows if prompted
3. The deployment will trigger on push to main/master

### Step 3: Configure Deployment Targets

Edit `.github/workflows/deploy.yml` to enable/disable platforms:

```yaml
env:
  ENABLE_HEROKU: 'false'    # Set to 'true' to enable
  ENABLE_DOCKER_HUB: 'false' # Set to 'true' to enable
  ENABLE_RENDER: 'false'     # Set to 'true' to enable
```

## Environment Configuration

### Required Variables

None - the API works with defaults

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `5000` |
| `DEBUG` | Debug mode | `False` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Platform-Specific Variables

#### Railway
- Automatically sets `PORT`
- No additional configuration needed

#### Heroku
- Automatically sets `PORT`
- Add other variables via dashboard or CLI

#### Docker
- Set via `-e` flag or compose file
- Example: `-e DEBUG=True`

## Testing Deployment

### Basic Health Check

```bash
# Replace with your deployed URL
curl https://your-app.railway.app/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000000",
  "service": "mnav-api",
  "version": "1.0.0"
}
```

### Test All Endpoints

```bash
# Set your API URL
API_URL="https://your-app.railway.app"

# Test root
curl $API_URL/

# Test health
curl $API_URL/api/health

# Test mNAV data
curl $API_URL/api/mnav?fund_code=TEST123

# Test webhook
curl -X POST $API_URL/webhook/mnav \
  -H "Content-Type: application/json" \
  -d '{"fund_code":"TEST123","nav":100.50,"date":"2024-01-01"}'

# Test webhook history
curl $API_URL/webhook/mnav/history
```

### Load Testing

```bash
# Install hey (HTTP load tester)
go install github.com/rakyll/hey@latest

# Test with 100 requests, 10 concurrent
hey -n 100 -c 10 $API_URL/api/health
```

## Troubleshooting

### Common Issues

#### 1. **Application Error on Heroku**
```bash
# Check logs
heroku logs --tail

# Restart dynos
heroku restart

# Check environment
heroku run env
```

#### 2. **Railway Build Failed**
- Check build logs in Railway dashboard
- Ensure `requirements.txt` is valid
- Check Python version compatibility

#### 3. **Docker Container Exits**
```bash
# Check logs
docker logs mnav-api

# Debug interactively
docker run -it --rm mnav-api /bin/bash
```

#### 4. **502 Bad Gateway (Nginx)**
```bash
# Check if app is running
sudo supervisorctl status mnav-api

# Check app logs
sudo tail -f /var/log/mnav-api.log

# Restart app
sudo supervisorctl restart mnav-api
```

### Debug Mode

Enable debug mode for detailed errors:

```bash
# Railway/Heroku
# Add DEBUG=True to environment variables

# Docker
docker run -e DEBUG=True -p 5000:8080 mnav-api

# Local
DEBUG=True python app.py
```

### Performance Issues

1. **Increase workers**:
   ```bash
   # In Procfile or command
   gunicorn app:app --workers 4
   ```

2. **Add caching**:
   - Implement Redis for webhook storage
   - Add response caching

3. **Monitor resources**:
   - Railway: Check metrics dashboard
   - Heroku: `heroku ps`
   - VPS: `htop` or monitoring tools

## Security Considerations

1. **HTTPS**: Always use HTTPS in production
2. **API Keys**: Use environment variables, never commit
3. **Rate Limiting**: Implement rate limiting for production
4. **Input Validation**: Already implemented in webhook endpoint
5. **CORS**: Configure for your specific domains

## Scaling

### Horizontal Scaling

#### Railway
- Increase replicas in dashboard
- Use `numReplicas` in railway.json

#### Heroku
```bash
heroku ps:scale web=2
```

#### Docker Swarm
```bash
docker service scale mnav-api=3
```

### Vertical Scaling

- Increase worker count in Procfile
- Upgrade server resources
- Optimize code performance

## Monitoring

### Application Monitoring

1. **Logs**:
   - Railway: Built-in log viewer
   - Heroku: `heroku logs --tail`
   - Docker: `docker logs -f mnav-api`

2. **Health Checks**:
   - Set up uptime monitoring (UptimeRobot, Pingdom)
   - Monitor `/api/health` endpoint

3. **Metrics**:
   - Add APM tool (New Relic, DataDog)
   - Track response times and errors

### Alerts

Configure alerts for:
- Application downtime
- High error rates
- Slow response times
- Resource usage

## Backup and Recovery

1. **Code**: Already in Git
2. **Data**: Implement database backups if using persistence
3. **Configuration**: Document all environment variables
4. **Rollback**: Use Git tags for versions

---

## Quick Reference

### One-Command Deployments

```bash
# Railway (with CLI)
railway up

# Heroku
git push heroku main

# Docker local
docker run -d -p 80:8080 mnav-api

# Update deployment
git push origin main  # Triggers GitHub Actions
```

### Useful Commands

```bash
# View logs
railway logs         # Railway
heroku logs --tail   # Heroku
docker logs -f mnav-api  # Docker

# Restart app
railway restart      # Railway
heroku restart       # Heroku
docker restart mnav-api  # Docker

# Check status
railway status       # Railway
heroku ps           # Heroku
docker ps           # Docker
```

---

For additional help, please open an issue on GitHub or consult the platform-specific documentation.