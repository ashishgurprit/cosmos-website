# Cosmos Website - Deployment Guide

## GitHub Repository

**Repository**: https://github.com/ashishgurprit/cosmos-website
**Branch**: main
**Deployment Method**: Cloudflare Pages (GitHub Integration)

---

## Current Setup Status

✅ GitHub repository created and code pushed
⚠️ **ACTION REQUIRED**: Connect Cloudflare Pages to GitHub repository

---

## Connect Cloudflare Pages to GitHub (One-Time Setup)

### Step 1: Access Cloudflare Pages Dashboard

1. Go to https://dash.cloudflare.com/
2. Select your account
3. Navigate to **Workers & Pages**
4. Find project: **cosmos-website**
5. Click **Settings** tab

### Step 2: Configure Git Integration

1. In Settings, scroll to **Builds & deployments** section
2. Click **Configure Production deployments**
3. Select **Connect to Git**
4. Choose **GitHub** as the source
5. Authorize Cloudflare to access your GitHub account (if not already done)
6. Select repository: **ashishgurprit/cosmos-website**
7. Configure build settings:

**Production branch**: `main`

**Build settings**:
```
Build command:    npm run build
Build output dir: dist
Root directory:   (leave empty or /)
```

**Environment variables**: (if needed)
```
NODE_VERSION = 18
```

8. Click **Save and Deploy**

### Step 3: Verify Connection

After connecting, Cloudflare Pages will:
- Automatically deploy on every push to `main` branch
- Build using the command: `npm run build`
- Deploy the `dist` folder
- Apply to all configured domains

---

## Future Deployments (After Setup)

Once GitHub integration is configured, deployments are automatic:

```bash
cd ~/Development/Cosmos-Website

# Make changes to code

# Commit changes
git add .
git commit -m "Your commit message"

# Push to GitHub (triggers automatic deployment)
git push origin main
```

Cloudflare Pages will automatically deploy within ~2 minutes.

---

## Manual Deployment (Fallback - Not Recommended)

```bash
npm run build
wrangler pages deploy dist --project-name cosmos-website --commit-dirty=true
```

---

## Important Notes

1. **Never use both methods**: Once GitHub integration is set up, always use git push
2. **Preview deployments**: Pull requests automatically get preview URLs
3. **Rollback**: Use Cloudflare Pages dashboard to rollback if needed

---

**Last Updated**: 2026-01-12
**Repository**: https://github.com/ashishgurprit/cosmos-website
