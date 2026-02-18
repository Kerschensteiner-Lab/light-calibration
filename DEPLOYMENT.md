# Deployment Guide

This guide explains how to deploy the Photoisomerization Rate Calculator web app to a server so it can be accessed as a public website.

## Deployment Options

The app can be deployed to various hosting platforms. Below are instructions for the most common options:

### Option 1: Render.com (Recommended - Free Tier Available)

Render.com offers a free tier and is easy to set up.

1. **Create a Render account** at [render.com](https://render.com)

2. **Connect your GitHub repository**:
   - Click "New +" → "Web Service"
   - Connect your GitHub account and select the `light-calibration` repository
   - Render will automatically detect the `render.yaml` configuration file

3. **Configure the service**:
   - Name: `light-calibration` (or your preferred name)
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn src.app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - Select your plan (Free tier is sufficient for basic use)

4. **Deploy**:
   - Click "Create Web Service"
   - Render will automatically build and deploy your app
   - Once deployed, you'll receive a URL like `https://light-calibration-xxxx.onrender.com`

5. **Share the URL** with your team to access the calculator from anywhere.

**Note**: The free tier on Render spins down after 15 minutes of inactivity, so the first request after inactivity may take 30-60 seconds to load.

---

### Option 2: Fly.io

Fly.io offers a generous free tier and uses Docker for deployment.

1. **Install the Fly CLI**:
   ```bash
   # macOS
   brew install flyctl
   
   # Linux
   curl -L https://fly.io/install.sh | sh
   
   # Windows
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Authenticate**:
   ```bash
   fly auth login
   ```

3. **Launch the app** (from the repository root):
   ```bash
   fly launch
   ```
   
   When prompted:
   - App name: Choose a unique name (e.g., `light-calibration-yourlab`)
   - Region: Select the closest region to your users
   - PostgreSQL: No
   - Redis: No
   - Deploy now: Yes

4. **Access your app**:
   - Your app will be available at `https://your-app-name.fly.dev`

5. **Update the app** (after making changes):
   ```bash
   fly deploy
   ```

---

### Option 3: Docker (Self-hosted or Cloud Platforms)

Use the included `Dockerfile` to deploy to any platform that supports Docker containers (Google Cloud Run, AWS ECS, Azure Container Instances, etc.).

#### Building the Docker image:

```bash
docker build -t light-calibration .
```

#### Running locally with Docker:

```bash
docker run -p 8080:8080 light-calibration
```

Then access the app at `http://localhost:8080`

#### Deploying to Google Cloud Run:

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/light-calibration

# Deploy to Cloud Run
gcloud run deploy light-calibration \
  --image gcr.io/YOUR_PROJECT_ID/light-calibration \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

### Option 4: Heroku

Heroku is a popular platform with a free tier (requires credit card verification).

1. **Install the Heroku CLI**:
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Other platforms: https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login to Heroku**:
   ```bash
   heroku login
   ```

3. **Create a new app**:
   ```bash
   heroku create your-app-name
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```
   
   Or if you're on a different branch:
   ```bash
   git push heroku your-branch:main
   ```

5. **Open your app**:
   ```bash
   heroku open
   ```

---

## Environment Variables

The app automatically detects whether it's running in production or development mode:

- **Development mode** (default): Runs on `localhost:5050` and automatically opens in your browser
- **Production mode**: Detected when `PORT` environment variable is set or `FLASK_ENV=production`

### Setting environment variables:

**Render.com**: Add environment variables in the "Environment" section of your web service settings.

**Fly.io**: Use `fly secrets set KEY=value`

**Heroku**: Use `heroku config:set KEY=value`

**Docker**: Pass with `-e` flag: `docker run -e FLASK_ENV=production -p 8080:8080 light-calibration`

---

## Production Considerations

### Security

The app is designed for scientific collaboration within a research lab. If deploying publicly, consider:

1. **Add authentication**: Implement login/password protection if needed
2. **Rate limiting**: Prevent abuse by limiting API requests
3. **HTTPS**: All recommended platforms (Render, Fly.io, Heroku, Cloud Run) provide HTTPS by default
4. **File upload limits**: Current implementation accepts CSV files; ensure proper validation

### Performance

- **Workers**: The default configuration uses 2 Gunicorn workers. Increase for higher traffic:
  ```bash
  gunicorn src.app:app --workers 4 --timeout 120
  ```

- **Caching**: Consider adding caching for spectrum files if you have high traffic

### Data Persistence

- User-uploaded spectra are saved to the `spectra/` directory
- For cloud deployments, these files are ephemeral (lost on restart) unless using persistent storage
- To persist user-uploaded spectra:
  - **Render**: Use Render Disks (persistent storage)
  - **Fly.io**: Use Fly Volumes
  - **Heroku**: Use S3 or similar object storage
  - **Docker**: Mount a persistent volume

**Example for Docker with persistent volume**:
```bash
docker run -p 8080:8080 -v $(pwd)/spectra:/app/spectra light-calibration
```

---

## Troubleshooting

### App crashes on startup

Check logs:
- **Render**: View logs in the Render dashboard
- **Fly.io**: `fly logs`
- **Heroku**: `heroku logs --tail`
- **Docker**: `docker logs <container-id>`

### Import issues with numpy/scipy

Ensure sufficient memory is allocated. These scientific libraries require ~512MB RAM minimum.

### Port binding errors

The app automatically uses the `PORT` environment variable in production. Ensure your platform sets this correctly.

---

## Reverting to Local-Only Mode

If you want to run the app locally after deploying, simply use the existing run scripts:

```bash
./run.sh        # macOS/Linux
run.bat         # Windows
```

The app will automatically detect it's running locally and use `localhost:5050`.

---

## Cost Estimates

- **Render.com**: Free tier available (limited resources, sleeps after inactivity)
- **Fly.io**: Free tier includes 3 shared-cpu VMs with 256MB RAM each
- **Heroku**: Free tier available (requires credit card, sleeps after 30 min inactivity)
- **Google Cloud Run**: Pay-per-use, ~$5-10/month for moderate usage
- **Self-hosted Docker**: Cost of your server/VPS

---

## Support

For deployment issues specific to this app, please open an issue on the GitHub repository.

For platform-specific questions:
- Render: [docs.render.com](https://docs.render.com)
- Fly.io: [fly.io/docs](https://fly.io/docs)
- Heroku: [devcenter.heroku.com](https://devcenter.heroku.com)
- Google Cloud: [cloud.google.com/run/docs](https://cloud.google.com/run/docs)
