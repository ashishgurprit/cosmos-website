# Deployment Guide - Cosmos Web Tech

## Critical Setup Steps for Cloudflare Pages

### 1. Configure Turnstile Secret Key

**IMPORTANT**: Before the form proxy will work, you must add your Turnstile secret key as an environment variable in Cloudflare Pages.

1. Go to your [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Navigate to **Turnstile** section
3. Use the existing site or create a new one:
   - Site name: `cosmoswebtech.com.au`
   - Domain: `cosmoswebtech.com.au`
   - Widget mode: **Managed** (recommended)
4. Copy the **Secret Key** (NOT the Site Key)
5. Go to **Pages** → **cosmos-website** → **Settings** → **Environment Variables**
6. Add a new environment variable:
   - **Name**: `TURNSTILE_SECRET_KEY`
   - **Value**: [Your secret key from step 4]
   - **Environment**: Select both Production and Preview
7. Click **Save**

**Note**: The Site Key is already configured in the code (`0x4AAAAAAAzsB5pP7TqT9oRx`). If you need a different site key, update it in:
- `/src/config/forms.ts`
- All form files (search for `data-sitekey`)

### 2. Enable Git Integration (Automated Deployments)

To enable automatic deployments on every git push:

1. Go to **Pages** → **cosmos-website** → **Settings** → **Builds & Deployments**
2. Click **Connect to Git** (if not already connected)
3. Select **GitHub** and authorize Cloudflare
4. Choose the repository (if applicable)
5. Configure build settings:
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
   - **Root directory**: `/` (leave empty)
6. Click **Save and Deploy**

**Benefits**:
- Every push to `main` automatically deploys to production
- Pull requests get unique preview URLs
- No need for manual `wrangler pages deploy` commands

### 3. Verify Sitemap Generation

After deployment, verify the sitemap is accessible:
- Production: https://cosmoswebtech.com.au/sitemap-index.xml
- Check it includes all 38+ pages

Submit the sitemap to Google Search Console:
1. Go to [Google Search Console](https://search.google.com/search-console)
2. Select your property (cosmoswebtech.com.au)
3. Go to **Sitemaps** in the left sidebar
4. Add `sitemap-index.xml`
5. Click **Submit**

## Forms Implemented

All 6 forms now use Turnstile + Proxy:

1. **Footer Contact Form** (Layout.astro)
   - Form ID: 39
   - Collects: name, email, phone, service, message

2. **Blog Newsletter Popup** (Layout.astro)
   - Form ID: 39
   - Collects: email

3. **Planning Checklist Download** (resources/planning-checklist.astro)
   - Form ID: 41
   - Collects: name, email

4. **Requirements Template Download** (resources/requirements-template.astro)
   - Form ID: 42
   - Collects: name, email

5. **SEO Checklist Download** (resources/seo-checklist.astro)
   - Form ID: 43
   - Collects: name, email

6. **Website Cost Guide Download** (resources/website-cost-guide.astro)
   - Form ID: 44
   - Collects: name, email

## Form Submission Architecture

**Before (with no-cors issue)**:
```
Browser → Mautic (no-cors) → Opaque Response → Always shows "success"
```

**After (with proxy)**:
```
Browser → Turnstile Verification
       ↓
     /api/submit (Cloudflare Function)
       ↓
     Turnstile API (validate token)
       ↓
     Mautic API (submit form)
       ↓
     Return actual success/error
       ↓
     Browser (shows real status)
```

### Benefits
1. **Spam Protection**: Turnstile blocks bot submissions before they reach Mautic
2. **Real Error Handling**: Users see actual errors (invalid email, server down, etc.)
3. **Better UX**: No false "success" messages
4. **Rate Limiting**: Cloudflare automatically rate-limits the proxy endpoint
5. **Analytics**: Can log submissions and track conversion rates

## Testing the Forms

### Local Testing

```bash
cd ~/Development/Cosmos-Website
npm run dev

# Visit http://localhost:4321
# Test all 6 forms:
# - Footer form (on any page)
# - Blog popup (on blog pages after mouse exit)
# - Each resource download page
```

### Production Testing

After deployment:
1. Visit each form page
2. Fill out with valid data
3. Complete Turnstile challenge (if shown)
4. Submit and verify success
5. Check Mautic for the lead entry

### Error Testing

Test error scenarios:
1. **Invalid email**: Submit with `test@invalid` → Should show validation error
2. **No Turnstile**: Block the token in DevTools → Should show spam error
3. **Network error**: Block Mautic URL → Should show error message

## Monitoring & Debugging

### Cloudflare Logs

View function logs:
```bash
wrangler pages deployment tail
```

Or in dashboard:
1. Go to **Pages** → **cosmos-website**
2. Click on a deployment
3. Go to **Functions** tab
4. View request logs

### Common Issues

**Issue**: "Missing spam protection token"
- **Cause**: Turnstile script not loaded or widget not rendered
- **Fix**: Check browser console, verify script URL

**Issue**: "Spam protection verification failed"
- **Cause**: Invalid Turnstile token or secret key
- **Fix**: Verify `TURNSTILE_SECRET_KEY` environment variable

**Issue**: "There was an error submitting your form"
- **Cause**: Mautic is down or rejecting the submission
- **Fix**: Check Mautic dashboard, verify form IDs, check function logs

## Performance Optimization

Implemented optimizations:

1. **Preconnect hints**: Reduces DNS/TLS handshake time
   - `mautic.cloudgeeks.com.au`
   - `www.googletagmanager.com`
   - `challenges.cloudflare.com`

2. **Async script loading**: Turnstile loads asynchronously
3. **Edge caching**: Static assets cached on Cloudflare's edge
4. **Function proximity**: Pages Functions run on edge (low latency)

## Security Notes

- Turnstile secret key must remain private (never commit to git)
- The proxy function validates all inputs before forwarding to Mautic
- Cloudflare provides automatic DDoS protection
- HTTPS is enforced on all routes

## Cost Estimate

Based on Cloudflare Pages pricing:

- **Pages hosting**: Free (unlimited requests)
- **Pages Functions**: Free for first 100,000 requests/day
- **Turnstile**: Free (unlimited requests)
- **Bandwidth**: Free (unlimited)

**Expected costs**: $0/month for current traffic levels

## Deployment Commands

### Manual Deployment (if needed)

```bash
cd ~/Development/Cosmos-Website
npm run build
wrangler pages deploy dist --project-name cosmos-website --commit-dirty=true
```

### Check Deployment Status

```bash
wrangler pages deployment list --project-name cosmos-website
```

## Next Steps After Deployment

1. ✅ Configure Turnstile secret key (CRITICAL)
2. ✅ Test all 6 forms
3. ✅ Submit sitemap to Google Search Console
4. ✅ Monitor form submissions in Mautic
5. ✅ Check Cloudflare Functions logs for errors
6. ✅ Enable Git integration (optional but recommended)

## Support

If you need help:
- Check function logs: `wrangler pages deployment tail`
- View in Cloudflare Dashboard: Pages → cosmos-website → Functions
- Common issues documented above
