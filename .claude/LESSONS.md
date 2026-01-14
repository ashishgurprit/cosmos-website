# Master Lessons Learned

> Consolidated lessons from ALL projects using Streamlined Development.
> This file is synced to all projects and evolves over time.
>
> Version: 1.21.0 | Last Updated: 2026-01-14

---

## Quick Reference Checklist

Before ANY deployment:

### Identity & Auth
- [ ] Tested with REAL auth provider IDs (not mock UUIDs)
- [ ] Credential format matches platform (base64/raw/file)
- [ ] Auth headers pass through proxy/CDN

### Database
- [ ] ID column types handle auth provider formats
- [ ] Migrations run BEFORE app startup
- [ ] Connection pool appropriately sized

### API
- [ ] Frontend/backend IDs match (contract test)
- [ ] Error responses structured and displayed
- [ ] CORS configured for production domain
- [ ] External API datetime fields normalized to UTC (check timezone)

### Payments
- [ ] Webhook handlers are transactional
- [ ] Returns 500 on any partial failure
- [ ] Test vs live keys correct

### Mobile (Capacitor/React Native)
- [ ] Payment UI hidden on native iOS (App Store IAP rules)
- [ ] Keyboard resize mode set to 'native' for forms
- [ ] Safe area insets applied to full-screen pages
- [ ] Tested on actual device, not just simulator

### Background Tasks (Celery)
- [ ] Using sync database sessions (not async)
- [ ] Tasks tested in integration tests
- [ ] Error handling with proper retries
- [ ] Single-writer pattern: only one system owns each job status transition

### Security & Rate Limiting
- [ ] Password fields excluded from security pattern matching
- [ ] Token bucket rate limiting (not counter-based)
- [ ] Soft blocks (429) before hard blocks (403)
- [ ] Module imports validated before deployment

---

## Categories

- [Authentication & Identity](#authentication--identity)
- [Database & Data Types](#database--data-types)
- [API Contracts](#api-contracts)
- [Environment & Configuration](#environment--configuration)
- [Deployment & Infrastructure](#deployment--infrastructure)
- [Payment Integration](#payment-integration)
- [Mobile Development](#mobile-development)
- [Background Tasks](#background-tasks)
- [Testing Strategies](#testing-strategies)
- [Frontend & UI Patterns](#frontend--ui-patterns)
- [CMS Integration & Content Management](#cms-integration--content-management)
- [Monetization & Affiliate Marketing](#monetization--affiliate-marketing)
- [Security & Rate Limiting](#security--rate-limiting)

---

## Authentication & Identity

### LESSON: Firebase UID ≠ UUID
**Source**: ContentSage | **Date**: 2024-12-26

**Symptom**: `badly formed hexadecimal UUID string` in database operations

**Root Cause**: Firebase UIDs (e.g., `un42YcgdaeQreBdzKP0PAOyRD4n2`) are alphanumeric strings, not valid UUIDs. PostgreSQL UUID columns reject them.

**Solution**:
```python
import uuid

FIREBASE_NAMESPACE = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')

def firebase_uid_to_uuid(user_id: str) -> uuid.UUID:
    """Convert any user ID to valid UUID deterministically."""
    try:
        return uuid.UUID(user_id)  # Already valid UUID
    except ValueError:
        return uuid.uuid5(FIREBASE_NAMESPACE, user_id)  # Convert
```

**Prevention**:
- [ ] Test database ops with REAL Firebase UIDs, not mock UUIDs
- [ ] Add `test_firebase_uid_database_roundtrip()` integration test
- [ ] Use conversion helper in ALL database operations

---

### LESSON: Firebase Credentials Format Varies by Platform
**Source**: ContentSage | **Date**: 2024-12-26

**Symptom**: Firebase init fails silently or with JSON parse errors

**Root Cause**: Different platforms expect different formats:
- Railway: Base64-encoded JSON
- Vercel: Raw JSON (escaped)
- Local: File path

**Solution**:
```python
import base64, json, os

def parse_firebase_credentials(env_value: str) -> dict:
    """Parse Firebase credentials from multiple formats."""
    # Try base64 first (Railway)
    try:
        decoded = base64.b64decode(env_value)
        return json.loads(decoded)
    except:
        pass

    # Try raw JSON (Vercel)
    try:
        return json.loads(env_value)
    except:
        pass

    # Try file path (local)
    if os.path.exists(env_value):
        with open(env_value) as f:
            return json.load(f)

    raise ValueError(f"Cannot parse Firebase credentials")
```

**Prevention**:
- [ ] Add startup validation for credential format
- [ ] Document expected format per platform in README
- [ ] Test credential parsing in CI

---

### LESSON: Auth Headers Lost Through Proxy
**Source**: ContentSage | **Date**: 2024-12-26

**Symptom**: 401 errors only in production, works locally

**Root Cause**: Nginx/CDN strips or doesn't forward Authorization header

**Solution**:
```nginx
location /api {
    proxy_pass http://backend;
    proxy_set_header Authorization $http_authorization;
    proxy_pass_request_headers on;
}
```

**Prevention**:
- [ ] Smoke test auth endpoint after deployment
- [ ] Test with actual proxy in staging
- [ ] Verify header passthrough in proxy config

---

### LESSON: GitHub SSH Authentication Returns Exit Code 1 on Success
**Source**: Blog Publisher Docker | **Date**: 2026-01-12

**Symptom**: `ssh -T git@github.com` returns exit code 1 with message "You've successfully authenticated, but GitHub does not provide shell access"

**Root Cause**: GitHub SSH servers only handle git operations, not shell access. Exit code 1 is expected behavior (not an error) indicating successful authentication without shell access.

**Solution**: Check output message, not exit code
```bash
# Testing GitHub SSH - Exit code 1 = SUCCESS!
ssh -T git@github.com
# Expected: "Hi username! You've successfully authenticated..."
# Expected exit code: 1 (authentication worked, no shell)

# In scripts, parse output message:
output=$(ssh -T git@github.com 2>&1)
if echo "$output" | grep -q "successfully authenticated"; then
    echo "SSH authentication working"
else
    echo "SSH authentication failed"
    exit 1
fi
```

**Prevention**:
- [ ] Don't rely on exit codes for GitHub SSH tests - parse output message
- [ ] Document this behavior to avoid confusion
- [ ] Test with actual git operations (clone, push) for verification
- [ ] Exit code 0 = shell access (which GitHub doesn't allow)
- [ ] Exit code 1 = authentication worked, no shell (expected for GitHub)

---

## Database & Data Types

### LESSON: ID Format Assumptions Break at Integration
**Source**: ContentSage | **Date**: 2024-12-26

**Symptom**: Unit tests pass, production fails with ID errors

**Root Cause**: Unit tests use `uuid.uuid4()` which produces valid UUIDs. Real auth systems use provider-specific formats that aren't UUIDs.

**Solution**: Test with realistic ID formats:
```python
# In tests
SAMPLE_REALISTIC_IDS = [
    "un42YcgdaeQreBdzKP0PAOyRD4n2",  # Firebase
    "auth0|abc123def456",             # Auth0
    "google-oauth2|123456789",        # Google OAuth
    str(uuid.uuid4()),                # Actual UUID
]

@pytest.mark.parametrize("user_id", SAMPLE_REALISTIC_IDS)
def test_user_operations(user_id):
    # Test with each ID format
    result = create_user(user_id)
    assert result.success
```

**Prevention**:
- [ ] Integration tests MUST use realistic ID formats
- [ ] Parameterize tests with all expected ID formats
- [ ] Add sample IDs from each auth provider to test fixtures

---

### LESSON: Migrations Block Startup
**Source**: ContentSage | **Date**: 2024-12-26

**Symptom**: App hangs on startup, times out

**Root Cause**: Auto-migration acquires database lock, blocks if another process holds it (like a previous failed deployment)

**Solution**:
1. Run migrations as separate job, not on app startup
2. Add timeout to migration lock acquisition
3. Add `--skip-migrations` flag

```python
# In startup
if not os.environ.get("SKIP_MIGRATIONS"):
    try:
        with timeout(30):
            run_migrations()
    except TimeoutError:
        logger.error("Migration lock timeout - run manually")
```

**Prevention**:
- [ ] Never auto-run migrations in production startup
- [ ] Separate migration step in CI/CD pipeline
- [ ] Add migration health check endpoint

---

## API Contracts

### LESSON: Frontend/Backend ID Mismatch
**Source**: ContentSage | **Date**: 2024-12-26

**Symptom**: Checkout buttons do nothing, no console errors

**Root Cause**: Frontend sent `pack_10`, backend expected `credits_10`. No validation = silent failure.

**Solution**: Contract tests
```python
# tests/test_contracts.py
def test_frontend_backend_plan_ids_match():
    """Verify frontend plan IDs exist in backend."""
    # These should match frontend constants
    frontend_ids = ["credits_10", "credits_25", "credits_50"]
    backend_ids = list(PRICE_IDS.keys())

    for fid in frontend_ids:
        assert fid in backend_ids, \
            f"Frontend uses '{fid}' but backend doesn't recognize it"
```

**Prevention**:
- [ ] Contract tests in CI (run before deploy)
- [ ] Share types between FE/BE (TypeScript, OpenAPI)
- [ ] Backend returns helpful error for unknown IDs

---

### LESSON: WordPress Navigation Block Requires ref Parameter for Menu Items
**Source**: Multi-Agent Content Pipeline | **Date**: 2026-01-01

**Symptom**: Hamburger menu displays but has no menu items after updating header template

**Root Cause**: WordPress navigation block loses reference to menu entity when attributes like `overlayMenu:"always"` are added without preserving the `ref` parameter.

**Solution**:
```html
<!-- WRONG - loses menu items -->
<!-- wp:navigation {"overlayMenu":"always","icon":"menu"} /-->

<!-- CORRECT - includes ref to menu ID -->
<!-- wp:navigation {"ref":5,"overlayMenu":"always","icon":"menu"} /-->
```

**How to find menu ID**:
```bash
# Query WordPress navigation entities
curl "https://site.com/wp-json/wp/v2/navigation" -u user:pass
# Returns [{"id": 5, "title": {"rendered": "Navigation"}, ...}]
```

**Prevention**:
- [ ] Always preserve `ref` parameter when modifying navigation blocks
- [ ] Query /wp-json/wp/v2/navigation to find menu IDs before editing
- [ ] Test navigation immediately after template changes
- [ ] Keep backup of working header template

---

### LESSON: WordPress Block Theme CSS Stored in Database, Not Files
**Source**: Multi-Agent Content Pipeline | **Date**: 2026-01-02

**Symptom**: Need to customize WordPress theme CSS but can't find CSS files to edit

**Root Cause**: WordPress Block Themes (Twenty Twenty-Five, etc.) store custom CSS in database as `wp_global_styles` post type, not in theme files.

**Solution**:
```bash
# Find global styles post ID
sudo wp post list --post_type=wp_global_styles --format=csv --fields=ID,post_name

# Export, modify, update
sudo wp post get 89 --field=post_content > /tmp/styles.json
sed -i 's/old-value/new-value/g' /tmp/styles.json
sudo wp post update 89 /tmp/styles.json --post_content
```

**Key WordPress Post Types**:
- `wp_global_styles`: Custom CSS and theme settings
- `wp_template`: Page templates (home, single, archive)
- `wp_template_part`: Reusable parts (header, footer)
- `wp_navigation`: Menu structures

**Prevention**:
- [ ] Query post types to find correct IDs before modifying
- [ ] Always backup before changes: `cp /tmp/styles.json /tmp/backup.json`
- [ ] Use WP-CLI when REST API is blocked by security plugins

---

### LESSON: WordPress Block Theme Flex Layouts Override text-align CSS
**Source**: Multi-Agent Content Pipeline | **Date**: 2026-01-02

**Symptom**: Card titles appear centered despite `text-align: left !important` CSS

**Root Cause**: WordPress block themes use `is-layout-flex` class with `align-items: center` default. In flex containers, `text-align` is ignored - use `justify-content` (main axis) and `align-items` (cross axis).

**What Doesn't Work**:
```css
/* These fail on flex items */
.wp-block-post-title { text-align: left !important; }
.wp-block-group.is-vertical { align-items: flex-start !important; }
```

**Lesson**: Some alignment in block themes is "incorrigible" via CSS. Options:
1. Accept the limitation
2. Use Visual Site Editor
3. Create child theme with higher-specificity CSS
4. Use a different theme

**Prevention**:
- [ ] Test alignment early when choosing block themes
- [ ] Check if theme uses flex or flow layouts for query loops
- [ ] Use Visual Editor for complex layout changes

---

### LESSON: AI Prompt Instructions Must Explicitly Exclude Output Formatting
**Source**: Multi-Agent Content Pipeline | **Date**: 2026-01-03

**Symptom**: WordPress posts published with "No Title" - the actual title appeared as first paragraph inside the story text: `<p>Title: Zeus and the Oracle's Prophecy</p>`

**Root Cause**: The AI prompt included `TITLE: {title}` as context but didn't explicitly tell the AI NOT to include a title line in its output. The AI included "Title: ..." as the first line of the story.

**Solution**:
```python
# BEFORE (broken)
prompt = f"""...
TITLE: {raw_content.title}
...
Write the story now:"""

# AFTER (fixed)
prompt = f"""...
IMPORTANT: Do NOT include a title line in your response. Start directly with the story text.
The title is already known: "{raw_content.title}"
...
Write the story now (start with "Once upon a time" or similar, no title):"""
```

**Prevention**:
- [ ] Always explicitly state what to EXCLUDE from AI output
- [ ] Provide example of expected output format ("start with...")
- [ ] Add validation to check if generated text starts with undesired patterns
- [ ] Test AI prompts with multiple inputs to catch format variations

---

### LESSON: Silent API Failures
**Source**: ContentSage | **Date**: 2024-12-26

**Symptom**: UI does nothing on interaction

**Root Cause**: API returned error but frontend didn't handle/display it

**Solution**: Structured error handling on both sides
```typescript
// Frontend
async function callApi(endpoint: string, data: any) {
  try {
    const response = await fetch(endpoint, { ... });
    const result = await response.json();

    if (!response.ok) {
      // ALWAYS show error to user
      toast.error(result.detail || result.error || 'Request failed');
      return null;
    }
    return result;
  } catch (e) {
    toast.error('Network error - please try again');
    return null;
  }
}
```

**Prevention**:
- [ ] E2E test for error display
- [ ] Require error handling in code review
- [ ] Backend always returns `{detail: string}` on error

---

### LESSON: External APIs May Return Local Timezone, Not UTC
**Source**: Multi-Agent Content Pipeline | **Date**: 2026-01-06

**Symptom**: Scheduler showed negative `days_since` values (e.g., -0.4 days) for posts published today. Time comparisons produced impossible results.

**Root Cause**: WordPress REST API returns post dates in the site's local timezone (e.g., `2026-01-06T13:33:42` in Australia/Sydney = UTC+11), but the scheduler compared them against `datetime.utcnow()` without timezone conversion.

Example of the bug:
- API returns: `2026-01-06T13:33:42` (local time, actually UTC 02:33:42)
- Server UTC time: `2026-01-06T03:24:58`
- Naive comparison: 03:24 - 13:33 = -10 hours = -0.4 days (WRONG!)

**Solution**:
```python
# Add configurable timezone offset
WP_TIMEZONE_OFFSET_HOURS = int(os.getenv('WP_TIMEZONE_OFFSET_HOURS', '0'))

# Convert API local time to UTC before comparison
date_str = post['date'].replace('Z', '').split('+')[0]
post_date_local = datetime.fromisoformat(date_str)
post_date_utc = post_date_local - timedelta(hours=WP_TIMEZONE_OFFSET_HOURS)

# Now compare UTC to UTC
hours_since = (datetime.utcnow() - post_date_utc).total_seconds() / 3600
```

**Key Insight**: Many APIs (WordPress, CMS platforms, e-commerce) return dates in the site's configured timezone, not UTC. Always check API documentation or test empirically.

**Prevention**:
- [ ] Check timezone of external API datetime fields (don't assume UTC)
- [ ] Use configurable timezone offset rather than hardcoding
- [ ] Validate time-based values are sensible (negative = timezone bug)
- [ ] Prefer API fields that explicitly include timezone (ISO 8601 with offset)
- [ ] Look for `_gmt` or `_utc` suffix fields if available (e.g., WordPress `date_gmt`)

---

### LESSON: Instagram CDN Images Expire - Download Locally
**Source**: insta-based-shop | **Date**: 2026-01-11

**Symptom**: After 7-14 days, fashion look pages showed broken images. Instagram CDN URLs that worked initially started returning 403 Forbidden errors.

**Root Cause**: Instagram's CDN (fbcdn.net) images have authentication tokens in the URL that expire after a period. Once expired, the images become inaccessible even though the URL is still valid.

**Impact**: Content sites relying on Instagram CDN URLs experience gradual image breakage. Users see broken images, degrading UX and SEO.

**Solution**: Download Instagram images locally at content generation time.

```python
import requests
from pathlib import Path

def download_instagram_image(instagram_url: str, post_id: str) -> str:
    """Download Instagram image locally to prevent CDN expiration."""
    response = requests.get(instagram_url, timeout=10)
    response.raise_for_status()

    # Save to static directory
    local_path = Path(f"site/static/images/{post_id}.jpg")
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(response.content)

    # Return local path for markdown
    return f"/images/{post_id}.jpg"
```

**Key Insights**:
- Instagram/Facebook CDN URLs are temporary (7-14 day lifespan)
- Tokens in fbcdn.net URLs expire silently (no warning)
- Local storage prevents future breakage
- Download at generation time, not on-demand
- Store in static/ directory for Hugo/Jekyll/Gatsby sites

**Prevention**:
- [ ] Always download external images locally for content sites
- [ ] Never rely on Instagram/Facebook CDN URLs for permanent content
- [ ] Add image validation step in CI to detect broken external links
- [ ] Monitor for 403 errors in production logs
- [ ] Consider image optimization during download (WebP conversion, compression)

---

### LESSON: Profile-Based Scraping More Reliable Than Hashtag Scraping
**Source**: insta-based-shop | **Date**: 2026-01-11

**Symptom**: Hashtag scraping (#streetwear, #ootd) returned inconsistent results - sometimes 50 posts, sometimes 0. Quality varied wildly, with many spam posts and low-engagement content.

**Root Cause**: Instagram's hashtag feed algorithm prioritizes recent posts over quality. Hashtags attract spam, bot accounts, and low-quality content. No engagement filtering available at API level for hashtags.

**Solution**: Switch to profile-based scraping targeting curated influencers. Sort by engagement instead of hard filtering.

**Key Patterns**:
```python
# Curated influencers by region
INFLUENCERS = {
    "Western": ["chiaraferragni", "leoniehanne", "carodaur"],
    "Asian": ["yoona__lim", "jennierubyjane", "watanabenaomi703"],
    "Indian": ["masoomminawala", "komalpandeyofficial"]
}

# Sort by engagement, no hard threshold
posts = fetch_profile_posts(influencer)
posts.sort(key=lambda p: p['likesCount'], reverse=True)

# Interleave regions for diversity
def interleave_by_region(posts_by_influencer):
    """Prevent clustering: Western, Asian, Indian, Western, Asian..."""
    regions = ["Western", "Asian", "Indian"]
    result = []
    max_posts = max(len(posts) for posts in posts_by_influencer.values())
    for i in range(max_posts):
        for region in regions:
            for influencer in INFLUENCERS[region]:
                if i < len(posts_by_influencer.get(influencer, [])):
                    result.append(posts_by_influencer[influencer][i])
    return result
```

**Key Insights**:
- Curated influencers >>> hashtag feeds for quality
- Profile scraping provides consistent, predictable results
- Engagement-based sorting > hard thresholds (avoid missing good content)
- Regional diversity requires intentional interleaving
- Pre-vetting influencers saves processing time

**Prevention**:
- [ ] Always use profile scraping for fashion/lifestyle/influencer content
- [ ] Maintain curated list by region/niche/category
- [ ] Sort by engagement rather than filtering with hard thresholds
- [ ] Implement diversity algorithms for balanced content
- [ ] Monitor influencer quality quarterly and prune low performers

---

### LESSON: YouTube Trending API Returns Localized Results by Country
**Source**: youtube-intnl-blog | **Date**: 2026-01-11

**Context**: Fetching "Best Tech Videos" for different countries (US, GB, JP, BR, etc.) to create localized content.

**Problem**: Initial implementation used same API endpoint for all countries, resulting in US-centric content for all language versions. Japanese users saw Silicon Valley tech, not Japanese tech trends.

**Root Cause**: YouTube Data API has `regionCode` parameter that defaults to US if not specified.

**Solution**: Always pass `regionCode` parameter to get localized trending videos.

```python
def fetch_trending_videos(category: str, country_code: str) -> list:
    """Fetch localized trending videos for specific country."""
    response = youtube.videos().list(
        part='snippet,statistics,contentDetails',
        chart='mostPopular',
        regionCode=country_code,  # US, GB, JP, BR, etc.
        videoCategoryId=CATEGORY_IDS[category],
        maxResults=10
    ).execute()

    return response['items']

# Category IDs (consistent across all regions)
CATEGORY_IDS = {
    'tech': '28',       # Science & Technology
    'travel': '19',     # Travel & Events
    'health': '26'      # Howto & Style
}

# Usage
us_tech = fetch_trending_videos('tech', 'US')   # Silicon Valley
jp_tech = fetch_trending_videos('tech', 'JP')   # Japanese tech
br_tech = fetch_trending_videos('tech', 'BR')   # Brazilian tech (Portuguese)
```

**Key Insights**:
- YouTube trending content varies significantly by country
- regionCode parameter is essential for localized content
- Category IDs are consistent across all regions
- Japanese tech trending ≠ US tech trending (different creators, languages, topics)
- Test API calls for each target country to verify localization

**Prevention**:
- [ ] Always pass regionCode to YouTube API for trending content
- [ ] Test API responses for each target country during development
- [ ] Document which APIs support regionalization parameters
- [ ] Validate video availability in target region (some videos geo-blocked)
- [ ] Monitor for API quota limits (10K requests/day free tier)

---

### LESSON: Apify API Response Format Changes Require Defensive Parsing
**Source**: insta-based-shop | **Date**: 2026-01-11

**Symptom**: Content generation crashed with `KeyError: 'posts'` after switching Apify scrapers. Previous code expected flat array, new scraper returned nested object.

**Root Cause**: Third-party scraping services (Apify, Bright Data, Oxylabs) have multiple scrapers with different response formats. Format changes without warning when switching scrapers or when provider updates.

**Solution**: Defensive parsing that handles multiple formats gracefully.

```python
def extract_posts(api_response: dict | list) -> list:
    """
    Handle multiple API response formats defensively.

    Observed formats:
    1. Flat array: [post1, post2, ...]
    2. Nested object: { posts: [...] }
    3. Profile wrapper: { profile: {...}, posts: [...] }
    4. Dataset wrapper: { data: [...] }
    """
    # Handle flat array
    if isinstance(api_response, list):
        return api_response

    # Handle nested 'posts' key
    if 'posts' in api_response:
        return api_response['posts']

    # Handle dataset wrapper
    if 'data' in api_response and isinstance(api_response['data'], list):
        return api_response['data']

    # Log unexpected format for debugging
    logger.warning(f"Unexpected API response format: {api_response.keys()}")
    return []

# Safe field access with defaults
for post in extract_posts(response):
    likes = post.get('likesCount', 0)  # Default to 0 if missing
    caption = post.get('caption', '')
    image = post.get('displayUrl') or post.get('imageUrl')  # Try both field names
```

**Key Insights**:
- Third-party APIs change response formats without warning
- Different scrapers from same provider may have different structures
- Defensive parsing prevents crashes on format changes
- Log unexpected formats for future debugging
- Always validate required fields before processing

**Prevention**:
- [ ] Always use defensive parsing for third-party API responses
- [ ] Add schema validation tests for critical API integrations
- [ ] Log unexpected response structures to monitoring
- [ ] Use .get() with defaults instead of direct key access
- [ ] Document expected response format in code comments
- [ ] Version-pin API dependencies when possible

---

## Environment & Configuration

### LESSON: Validate Configuration at Startup
**Source**: ContentSage | **Date**: 2024-12-26

**Symptom**: App starts but features fail at runtime

**Root Cause**: Missing/invalid env vars not caught until user hits the feature

**Solution**: Startup validation that fails fast
```python
def validate_startup_environment():
    """Validate all config at startup. Fail fast."""
    errors = []

    # Required vars
    for var in ["DATABASE_URL", "STRIPE_SECRET_KEY"]:
        if not os.environ.get(var):
            errors.append(f"Missing required: {var}")

    # Format validation
    try:
        parse_firebase_credentials(os.environ.get("FIREBASE_CREDENTIALS", ""))
    except ValueError as e:
        errors.append(f"Invalid FIREBASE_CREDENTIALS: {e}")

    # Stripe price IDs exist
    for plan in ["credits_10", "credits_25"]:
        if not PRICE_IDS.get(plan):
            errors.append(f"Missing Stripe price for: {plan}")

    if errors:
        for e in errors:
            logger.error(f"[STARTUP] {e}")
        if os.environ.get("FAIL_ON_CONFIG_ERROR"):
            sys.exit(1)

    return len(errors) == 0
```

**Prevention**:
- [ ] Add `validate_startup_environment()` to every project
- [ ] CI runs startup in validation mode
- [ ] Log all config issues prominently

---

### LESSON: GA4 Service Account Credentials for PaaS via Base64 Encoding
**Source**: Multi-Agent Content Pipeline | **Date**: 2026-01-01

**Symptom**: GA4 analytics not working on Railway/Heroku because service account JSON file can't be deployed

**Root Cause**: PaaS platforms don't support file uploads for credentials; environment variables are the only way to pass secrets.

**Solution**:
```bash
# 1. Create service account via gcloud
gcloud iam service-accounts create my-app-ga4 --display-name="GA4 Analytics"
gcloud iam service-accounts keys create ga4-credentials.json --iam-account=...

# 2. Base64 encode the credentials
base64 -w 0 ga4-credentials.json > ga4-creds-b64.txt

# 3. Set platform environment variable
railway variables --set "GA4_CREDENTIALS_BASE64=$(cat ga4-creds-b64.txt)"
# Or for Heroku: heroku config:set GA4_CREDENTIALS_BASE64="$(cat ga4-creds-b64.txt)"
```

```python
# In code - decode base64 credentials
import base64
import json
from google.oauth2 import service_account

creds_base64 = os.getenv("GA4_CREDENTIALS_BASE64")
if creds_base64:
    creds_json = base64.b64decode(creds_base64).decode('utf-8')
    creds_info = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(creds_info)
```

**Prevention**:
- [ ] Use base64 encoding for JSON credentials in environment variables
- [ ] Add credentials files to .gitignore BEFORE creating them
- [ ] Document required environment variables in README
- [ ] Add `is_configured()` check that validates credentials exist

---

### LESSON: Multi-Repo Git Sync - Stash Before Pull, Accept Remote Deletions
**Source**: Multi-Agent Content Pipeline | **Date**: 2026-01-11

**Symptom**: Synchronizing 15+ repositories from GitHub resulted in merge conflicts when trying to `git pull`. Many repos showed "Your local changes would be overwritten by merge" errors on `.claude/` configuration files that had been deleted remotely.

**Root Cause**: Local repositories had modified `.claude/` configuration files (from Streamlined Development sync process), but these files were deleted in the remote repository as part of a cleanup. Git couldn't auto-resolve modify/delete conflicts.

**What Didn't Work**:
```bash
# Simple pull fails with conflicts
git pull origin main
# error: Your local changes would be overwritten

# Stash + pull + pop creates merge conflicts
git stash && git pull && git stash pop
# CONFLICT (modify/delete): .claude/.master-path
# CONFLICT (modify/delete): .claude/LESSONS.md
```

**Solution - Clean Conflict Resolution**:
```bash
# 1. Stash local changes (including untracked files)
git stash -u

# 2. Pull cleanly from remote
git pull origin main

# 3. Try to restore stash
git stash pop

# 4. If conflicts occur on deleted files, remove them
git rm .claude/.master-path .claude/.master-version .claude/LESSONS-PROJECT.md \
       .claude/LESSONS.md .claude/commands/* .claude/settings.json

# 5. Reset to clean state
git reset HEAD

# 6. Restore files that should be kept from remote
git checkout HEAD -- SKILLS-CHEATSHEET.md .gitignore
```

**Better Workflow - For 15+ Repos**:
```bash
# Iterate through all repos
for dir in */; do
    if [ -d "${dir}.git" ]; then
        cd "$dir"

        # Stash everything (including untracked)
        git stash -u

        # Pull latest
        git pull origin $(git symbolic-ref --short HEAD)

        # Try to restore - if conflicts, just drop the stash
        git stash pop || git stash drop

        cd ..
    fi
done
```

**Key Results**: Successfully updated 15 repositories, preserved important local changes (README.md, untracked docs), accepted remote deletions of old .claude/ files, no data loss.

**Prevention**:
- [ ] Always use `git stash -u` (include untracked) before pulling in repos with many changes
- [ ] For modify/delete conflicts, accept remote deletion if files were intentionally removed
- [ ] When managing many repos, use loops with error handling
- [ ] Keep backup of critical local files before bulk operations
- [ ] Document which local changes are disposable vs. critical

---

### LESSON: TypeScript verbatimModuleSyntax Breaks Type Re-exports
**Source**: ContentSage | **Date**: 2025-12-28

**Symptom**: Build error when importing type like `import { PanInfo } from 'framer-motion'`

**Root Cause**: With `verbatimModuleSyntax: true` in tsconfig, types must be imported with the `type` keyword to be properly elided during compilation.

**Solution**:
```typescript
// ❌ WRONG - fails with verbatimModuleSyntax
import { motion, AnimatePresence, PanInfo } from 'framer-motion';

// ✅ CORRECT - separate type import
import { motion, AnimatePresence } from 'framer-motion';
import type { PanInfo } from 'framer-motion';
```

**Prevention**:
- [ ] Use `import type { X }` for all type-only imports
- [ ] Enable ESLint rule: `@typescript-eslint/consistent-type-imports`
- [ ] When re-exporting, use `export type { X }` for types

---

## Payment Integration

### LESSON: Webhook Success ≠ Operation Success
**Source**: ContentSage | **Date**: 2024-12-26

**Symptom**: Stripe shows payment success, user has no credits

**Root Cause**: Webhook handler returned 200 (Stripe happy) before database update completed (or failed)

**Solution**: Transactional webhook handling
```python
@app.post("/webhook")
async def stripe_webhook(request: Request):
    try:
        event = stripe.Webhook.construct_event(
            await request.body(),
            request.headers.get("stripe-signature"),
            WEBHOOK_SECRET
        )

        # ALL operations must succeed
        async with database.transaction():
            await process_checkout(event)
            await update_user_credits(event)
            await log_transaction(event)

        # Only return 200 if everything worked
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Webhook failed: {e}")
        # Return 500 so Stripe retries
        return JSONResponse(status_code=500, content={"error": str(e)})
```

**Prevention**:
- [ ] Webhook handlers must be transactional
- [ ] Return 500 on ANY failure (Stripe will retry)
- [ ] Add reconciliation job: compare Stripe payments vs database

---

### LESSON: SQLite for Content Deduplication in Automated Publishing
**Source**: youtube-intnl-blog | **Date**: 2026-01-11

**Context**: Daily automated content generation for multilingual blog (8 languages, 3 categories, 10 countries = 240 posts/week potential).

**Problem**: Without tracking, the system regenerated the same content repeatedly. Weekly "Best Tech Videos" would be regenerated every day with the same videos from YouTube trending API.

**Solution**: SQLite database tracks published content by topic, country, week number.

**Key Schema**:
```sql
CREATE TABLE generated_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,              -- health | tech | travel
    country_code TEXT NOT NULL,       -- US | GB | ES | FR | DE | JP | BR | IN | MX | IT | ID
    language TEXT NOT NULL,           -- en | es | fr | de | ja | pt | hi | it | id
    week_number TEXT NOT NULL,        -- ISO week: 2026-W02
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    video_ids TEXT,                   -- JSON array of YouTube video IDs
    UNIQUE(topic, country_code, week_number)
);

CREATE INDEX idx_dedup ON generated_content(topic, country_code, week_number);
```

**Deduplication Logic**:
```python
def check_if_exists(topic: str, country: str, week: str) -> bool:
    """Check if content already published for this week."""
    cursor.execute("""
        SELECT id FROM generated_content
        WHERE topic = ? AND country_code = ? AND week_number = ?
    """, (topic, country, week))
    return cursor.fetchone() is not None

# Only generate if not already published
from datetime import datetime
week = datetime.now().strftime('%Y-W%V')  # ISO week: 2026-W02
if not check_if_exists('tech', 'US', week):
    generate_content('tech', 'US', week=week)
```

**Key Insights**:
- SQLite perfect for local content tracking (no server needed)
- ISO week numbers (`YYYY-WNN`) provide clean deduplication key
- Store video IDs as JSON for future reference
- Simple schema prevents over-engineering
- Database file commits to git for persistence (<100MB)
- Index on deduplication keys improves performance

**Prevention**:
- [ ] Always use database for automated content deduplication
- [ ] Use ISO week numbers for weekly content (`YYYY-WNN` format)
- [ ] Store JSON arrays in SQLite for lightweight relational data
- [ ] Commit database file to git for small datasets (<100MB)
- [ ] Add indexes on deduplication keys for performance
- [ ] Test deduplication with multiple runs before deploying automation

---

## Deployment & Infrastructure

### LESSON: Flux/Stable Diffusion Models May Be Available from Public Repos
**Source**: Blog Publisher Docker | **Date**: 2026-01-12

**Symptom**: Attempting to download Flux model from official repository fails with 401 Unauthorized, requiring Hugging Face authentication and license acceptance

**Root Cause**: Assumed official repository was only source. Community alternatives (comfy-org, comfyanonymous, REPA-E) provide same models without gated access.

**Solution**: Check community repositories first
```bash
# UNET from comfy-org (public, no auth)
huggingface-cli download comfy-org/flux1-schnell flux1-schnell.safetensors --local-dir .

# Text encoders from comfyanonymous (public)
huggingface-cli download comfyanonymous/flux_text_encoders clip_l.safetensors --local-dir .
huggingface-cli download comfyanonymous/flux_text_encoders t5xxl_fp16.safetensors --local-dir .

# VAE from REPA-E (public, community maintained)
huggingface-cli download REPA-E/e2e-flux-vae diffusion_pytorch_model.safetensors --local-dir .
```

**Complete Flux Schnell Stack (32.5GB, zero authentication)**:
- UNET: comfy-org/flux1-schnell (23GB)
- CLIP L: comfyanonymous/flux_text_encoders/clip_l.safetensors (235MB)
- T5-XXL: comfyanonymous/flux_text_encoders/t5xxl_fp16.safetensors (9.2GB)
- VAE: REPA-E/e2e-flux-vae (320MB)

**Prevention**:
- [ ] Check comfy-org, comfyanonymous, community repos before assuming gated access
- [ ] Document model sources in deployment docs for reproducibility
- [ ] Test availability before designing authentication workflows
- [ ] Community mirrors often have better availability than official repos

**Key Insight**: Popular models often have public community mirrors that eliminate authentication complexity and licensing restrictions.

---

### LESSON: SSH Tunnels Need systemd for Production Persistence
**Source**: Blog Publisher Docker | **Date**: 2026-01-12

**Symptom**: SSH tunnel created with `nohup ssh ... &` dies on network interruptions, doesn't survive reboots, difficult to monitor

**Root Cause**: nohup provides basic backgrounding but no supervision, health monitoring, or restart capabilities

**Solution**: Use systemd service with auto-restart
```ini
# /etc/systemd/system/service-tunnel.service
[Unit]
Description=SSH Tunnel to Remote Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/ssh -i /root/.ssh/key -N -L 0.0.0.0:LOCAL_PORT:localhost:REMOTE_PORT -p SSH_PORT root@remote.host -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Critical SSH Options**:
- `ServerAliveInterval=60` - Send keepalive every 60s to detect dead connections
- `ServerAliveCountMax=3` - Disconnect after 3 failed keepalives
- `ExitOnForwardFailure=yes` - Fail fast if port forward fails
- `Restart=always` - Auto-restart on any failure
- `RestartSec=10` - Wait 10s before restarting (prevents tight loop)

**Deployment**:
```bash
systemctl daemon-reload
systemctl enable service-tunnel.service
systemctl start service-tunnel.service

# Monitor
systemctl status service-tunnel.service
journalctl -u service-tunnel.service -f
```

**Prevention**:
- [ ] Always use systemd for persistent services (tunnels, daemons, etc.)
- [ ] Add keepalive options for SSH tunnels
- [ ] Enable auto-restart with reasonable backoff
- [ ] Use journal logging for debugging
- [ ] Test by killing process to verify auto-restart

**Key Insight**: Production services need supervision. systemd provides automatic restart, logging, and lifecycle management that nohup/screen cannot.

---

### LESSON: Flux VAE Requires 16-Channel Architecture (Not SD's 4-Channel)
**Source**: Blog Publisher Docker | **Date**: 2026-01-12

**Symptom**: `RuntimeError: expected input[1, 16, 128, 128] to have 4 channels, but got 16 channels instead` when running Flux image generation

**Root Cause**: Flux models use 16-channel latents while Stable Diffusion VAE expects 4-channel latents. VAE architecture must match model family.

**Solution**: Use Flux-specific VAE
```bash
# WRONG - SD VAE with Flux model
# VAE: stabilityai/sd-vae-ft-mse  # 4-channel, incompatible

# CORRECT - Flux VAE
cd /root/ComfyUI/models/vae
huggingface-cli download REPA-E/e2e-flux-vae diffusion_pytorch_model.safetensors --local-dir .
```

**Technical Details**:
- **Flux Latents**: 16 channels (higher information capacity)
- **SD/SDXL Latents**: 4 channels (standard VAE)
- **VAE Input Channels**: Must match latent dimensions
- **File Sizes**: Similar (~300-350MB) but different architectures

**Model Compatibility Matrix**:
```yaml
Flux Schnell/Dev:
  unet: comfy-org/flux1-schnell
  vae: REPA-E/e2e-flux-vae  # 16-channel
  clip: comfyanonymous/flux_text_encoders

SD XL / SD 1.5:
  checkpoint: stabilityai/sdxl-turbo
  vae: Built-in or stabilityai/sd-vae-ft-mse  # 4-channel
```

**Prevention**:
- [ ] Match VAE to model family - Flux VAE for Flux, SD VAE for SD/SDXL
- [ ] Check error messages for channel mismatches (`expected input[1, X, ...]`)
- [ ] Test with small workflow before deploying to production
- [ ] Document compatible VAE sources for each model type in deployment docs

**Key Insight**: VAE architecture must match the model's latent space dimensions. Channel count mismatches are the clearest indicator of VAE incompatibility.

---

### LESSON: Railway Nixpacks Python Deployment Requires Virtual Environment
**Source**: Multi-Agent Content Pipeline | **Date**: 2025-12-31

**Symptom**: Railway deployments failing with health check timeouts, "gunicorn: command not found", or "error: externally-managed-environment"

**Root Cause**:
1. Nixpacks may auto-detect wrong provider (Node.js instead of Python)
2. Nix's Python environment is "externally managed" and blocks direct pip installs
3. railway.toml startCommand path doesn't match installed dependencies

**Solution**:
```toml
# nixpacks.toml - Force Python and use virtual environment
providers = ["python"]

[phases.setup]
nixPkgs = ["python311", "python311Packages.pip", "python311Packages.virtualenv"]

[phases.install]
cmds = [
    "python -m venv /app/venv",
    "/app/venv/bin/pip install --upgrade pip",
    "/app/venv/bin/pip install -r requirements.txt"
]

[start]
cmd = "/app/venv/bin/gunicorn --bind 0.0.0.0:$PORT --workers 2 dashboard.app:app"
```

```toml
# railway.toml - Use venv path in startCommand
[deploy]
startCommand = "/app/venv/bin/gunicorn --bind 0.0.0.0:$PORT --workers 2 dashboard.app:app"
healthcheckPath = "/health"
```

**Prevention**:
- [ ] Always create nixpacks.toml for Python projects on Railway
- [ ] Use virtual environment in Nix-based builds
- [ ] Ensure railway.toml startCommand matches nixpacks.toml paths
- [ ] Add /health endpoint for Railway health checks

**Key Insight**: Railway's `railway.toml` startCommand overrides `nixpacks.toml` [start].cmd, so both must use consistent paths.

---

### LESSON: Flask Dashboard Health Checks Critical for Railway
**Source**: Multi-Agent Content Pipeline | **Date**: 2025-12-31

**Symptom**: Railway deployment stuck in "DEPLOYING" state indefinitely

**Root Cause**: Default health check path "/" returns complex HTML, not a simple health response. Railway times out waiting for healthy status.

**Solution**:
```python
@app.route("/health")
def health():
    """Health check endpoint for Railway."""
    return jsonify({
        "status": "healthy",
        "features": "full" if FULL_FEATURES else "limited"
    })
```

```toml
# railway.toml
[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
```

**Prevention**:
- [ ] Always add /health endpoint to Flask/FastAPI apps
- [ ] Return simple JSON with status field
- [ ] Set healthcheckTimeout appropriately (300s for slow starts)
- [ ] Test health endpoint locally before deploying

---

### LESSON: Class Variables Reset on Worker Restart - Use External State
**Source**: Multi-Agent Content Pipeline | **Date**: 2026-01-03

**Symptom**: All WordPress posts assigned to the same author (Ruby, ID 2) instead of rotating through 7 avatar authors

**Root Cause**: Author round-robin used a class variable `_writer_index = 0` that reset to 0 whenever the worker restarted. Since PaaS platforms (Railway, Heroku) restart workers periodically, the index always started at 0.

**Solution**:
```python
# BEFORE (broken) - class variable resets on restart
class WordPressPublisher:
    WRITER_IDS = [2, 3, 4, 5, 6, 7, 8]
    _writer_index = 0  # Resets on every worker restart!

    def get_next_writer_id(self) -> int:
        writer_id = self.WRITER_IDS[self._writer_index % len(self.WRITER_IDS)]
        self._writer_index += 1
        return writer_id

# AFTER (fixed) - use external state for deterministic round-robin
def _get_total_post_count(self) -> int:
    """Get total published count from API for round-robin."""
    response = requests.head(f"{self.api_base}/posts",
                            params={"status": "publish", "per_page": 1})
    return int(response.headers.get('X-WP-Total', 0))

def get_next_writer_id(self) -> int:
    """Uses external count for deterministic round-robin that persists."""
    post_count = self._get_total_post_count()
    return self.WRITER_IDS[post_count % len(self.WRITER_IDS)]
```

**Key Insight**: Use external state (database count, API) instead of in-memory counters for anything that must persist across restarts.

**Prevention**:
- [ ] Never use class/instance variables for state that must persist across restarts
- [ ] Use database, Redis, or external API for round-robin counters
- [ ] Test worker behavior after simulated restart
- [ ] Document which state is ephemeral vs persistent

---

### LESSON: npm Peer Dependency Conflicts in Docker
**Source**: ContentSage | **Date**: 2025-12-28

**Symptom**: Docker build fails with peer dependency conflict (e.g., `@wix/dashboard-react` expects React 17, project uses React 18).

**Root Cause**: npm v7+ enforces strict peer dependency checking by default. Third-party SDKs often lag behind React versions.

**Solution**:
```dockerfile
# In Dockerfile
RUN npm install --legacy-peer-deps

# Or in .npmrc for local development
legacy-peer-deps=true
```

**Prevention**:
- [ ] Add `.npmrc` with `legacy-peer-deps=true` for known conflicts
- [ ] Document peer dependency workarounds in README
- [ ] Consider pinning problematic package versions
- [ ] Test `npm install` in CI before Docker build

---

### LESSON: Validate Module Imports Before Deployment
**Source**: Enterprise-Translation-System | **Date**: 2026-01-01

**Symptom**: Server crashes on startup in production with "Cannot find module" error, Railway healthcheck FAILED

**Root Cause**: Code imported a non-existent module (`./audioUtils`) that was never implemented. Worked locally when code path wasn't executed, crashed in production when service initialized.

**Solution**:
```bash
# Add pre-push validation hook
# .husky/pre-push or package.json scripts
node -e "require('./server.js')" && echo "✓ Server starts successfully"

# Or in CI pipeline
- name: Validate server startup
  run: |
    timeout 10 node server.js &
    sleep 5
    curl --fail http://localhost:3000/health || exit 1
    kill %1
```

**Prevention**:
- [ ] Add server startup test to pre-commit/pre-push hooks
- [ ] Verify all imports exist before pushing to production
- [ ] Test the startup path locally: `node server.js` before deploy
- [ ] Add module import validation to CI pipeline

---

### LESSON: Railway May Require Manual Deploy Trigger
**Source**: Enterprise-Translation-System | **Date**: 2026-01-01

**Symptom**: Pushed changes to main branch, but Railway still shows old code/behavior

**Root Cause**: Railway's auto-deploy can fail silently or not trigger for some commits. The dashboard may show deployment as successful when it didn't actually pick up latest changes.

**Solution**:
```bash
# Force deploy with Railway CLI
railway up --service backend --detach

# Verify deployment
railway logs --service backend | head -20

# Or redeploy via Railway dashboard:
# Deployments → Click service → Redeploy
```

**Prevention**:
- [ ] Always verify deployment with health endpoint after push
- [ ] Use `railway up --service <name>` for critical deploys
- [ ] Check Railway deployment logs for actual commit hash
- [ ] Add post-deploy smoke tests that hit production endpoints

---

### LESSON: Single-Writer Pattern for Background Job Publishing
**Source**: Multi-Agent Content Pipeline | **Date**: 2026-01-06

**Symptom**: Pipeline published ~18 posts/day instead of expected ~7. Two background systems were both publishing from the same job queue.

**Root Cause**: Pipeline Worker processed jobs end-to-end (CREATED → PUBLISHED) while Smart Scheduler ALSO picked up QUEUED jobs to publish. Both running = double the publishing rate with no coordination.

**Solution**:
```python
# BEFORE (broken) - Pipeline Worker published directly
# Stage 8: Queue for publishing
self.mark_job_status(job_id, 'QUEUED')
# Stage 9: Publish to WordPress
publisher = WordPressPublisher()
result = publisher.publish_story(...)
self.mark_job_status(job_id, 'PUBLISHED')

# AFTER (fixed) - Pipeline Worker STOPS at QUEUED
# Stage 8: Queue for publishing (STOP HERE)
self.mark_job_status(job_id, 'QUEUED')
logger.info(f"QUEUED for scheduler: {job_id}")
# Scheduler handles publishing with rate limits
```

**Job Flow After Fix**:
```
Worker:    CREATED → PROCESSING → WRITING → EDITING → QUEUED (stops here)
Scheduler: QUEUED → PUBLISHED (rate-limited, category-based)
```

**Key Insight**: When adding a new scheduler/publisher to an existing pipeline, audit existing code for overlapping functionality. Only ONE system should own each status transition.

**Prevention**:
- [ ] Single-writer pattern: Only one system transitions jobs to each final status
- [ ] Document job status ownership (which system owns which transition)
- [ ] When adding schedulers, check if existing workers already publish
- [ ] Add publishing rate monitoring to catch anomalies early

---

### LESSON: GitHub Actions Scheduled Workflows Require UTC Timezone
**Source**: youtube-intnl-blog | **Date**: 2026-01-11

**Symptom**: Content scheduled to publish at "6:00 AM local time" was publishing at different times across languages. Spanish content at 6 AM Madrid time, Japanese at 6 AM Tokyo time - but workflow ran at same UTC time for all.

**Root Cause**: GitHub Actions cron uses UTC only. Cannot schedule based on local timezones.

**Solution**: Calculate UTC time for desired local publishing time, or use single UTC time for all regions.

**Approach 1: Single Global Time (Simpler)**:
```yaml
# .github/workflows/daily-content.yml
on:
  schedule:
    - cron: '0 6 * * *'  # 6:00 AM UTC
    # = 1 AM EST (New York)
    # = 7 AM CET (Paris)
    # = 3 PM JST (Tokyo)

jobs:
  generate-content:
    runs-on: ubuntu-latest
    steps:
      - name: Generate multilingual content
        run: python scripts/generate_weekly_roundup.py
```

**Approach 2: Multiple UTC Times (Better Coverage)**:
```yaml
on:
  schedule:
    - cron: '0 0 * * *'   # 12 AM UTC (Evening US West)
    - cron: '0 6 * * *'   # 6 AM UTC (Morning Europe)
    - cron: '0 12 * * *'  # 12 PM UTC (Evening Asia)
```

**Key Insights**:
- GitHub Actions cron is UTC-only (no local timezone support)
- Cannot schedule based on audience local time
- Best practice: Pick one global time or multiple UTC times for coverage
- Document timezone in workflow comments for team clarity
- Users see publish timestamp in their local time (static site generator handles this)

**Prevention**:
- [ ] Always use UTC for GitHub Actions schedules
- [ ] Document what UTC time means for key regions in workflow comments
- [ ] Use multiple cron runs if global coverage needed
- [ ] Let static site generator handle display timezone conversion
- [ ] Test workflow timing across timezones with manual triggers

---

## Mobile Development

### LESSON: iOS App Store Rejects Stripe for Digital Goods
**Source**: ContentSage | **Date**: 2025-12-28

**Symptom**: App Store review rejection for using Stripe payment buttons in native iOS app.

**Root Cause**: Apple requires all digital goods/services purchased within iOS apps to use In-App Purchases (30% commission). Using Stripe for credits, subscriptions, or digital content violates this policy.

**Solution**:
```typescript
// Detect native iOS/Android and hide Stripe buttons
import { Capacitor } from '@capacitor/core';

const isNativeApp = Capacitor.isNativePlatform();

// In upgrade UI:
{isNativeApp ? (
  <button onClick={() => Browser.open({ url: 'https://yourapp.com/pricing' })}>
    Open in Browser to Upgrade
  </button>
) : (
  <StripeCheckoutButton />
)}
```

**Prevention**:
- [ ] Always check `Capacitor.isNativePlatform()` before showing payment UI
- [ ] Physical goods are exempt; digital goods/subscriptions require IAP
- [ ] Android is more lenient but follow same pattern for consistency
- [ ] Add pre-submission checklist item: "Payment UI gated for native"

---

### LESSON: Capacitor Keyboard Resize Mode Breaks Forms
**Source**: ContentSage | **Date**: 2025-12-28

**Symptom**: On mobile, opening keyboard pushes auth page content off-screen, form unusable.

**Root Cause**: Capacitor's default `resize: 'body'` mode resizes the entire viewport, pushing fixed-position elements off screen.

**Solution**:
```typescript
// capacitor.config.ts
const config: CapacitorConfig = {
  plugins: {
    Keyboard: {
      resize: 'native',        // Let OS handle resize
      resizeOnFullScreen: true,
      style: 'light',
    },
  },
};

// Also add safe area insets to full-screen pages:
<div className="pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)] overflow-auto">
```

**Prevention**:
- [ ] Set `resize: 'native'` for forms that need full visibility
- [ ] Always include safe area insets on full-screen pages
- [ ] Test auth flows on actual mobile device, not just simulator
- [ ] Add `overflow-auto` to prevent content clipping

---

## Background Tasks

### LESSON: Celery Tasks Need Sync Database Sessions
**Source**: ContentSage | **Date**: 2025-12-28

**Symptom**: Celery tasks fail with async session errors or event loop issues when using SQLAlchemy.

**Root Cause**: Celery workers run synchronously. Using async SQLAlchemy sessions (`AsyncSession`) in Celery causes "no running event loop" or similar errors.

**Solution**:
```python
# connection.py - Add sync session support alongside async
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from contextlib import contextmanager

_sync_engine = None
_sync_session_factory = None

def get_sync_database_url() -> str:
    """Convert async URL to sync (asyncpg → psycopg2)."""
    url = get_async_database_url()
    return url.replace("postgresql+asyncpg://", "postgresql://")

@contextmanager
def get_sync_session():
    """Sync session for Celery tasks."""
    global _sync_engine, _sync_session_factory

    if _sync_engine is None:
        _sync_engine = create_engine(get_sync_database_url())
        _sync_session_factory = sessionmaker(bind=_sync_engine)

    session = _sync_session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# In Celery task:
@celery_app.task
def process_data(data_id: int):
    with get_sync_session() as db:
        record = db.query(Model).filter_by(id=data_id).first()
        # ... process
```

**Prevention**:
- [ ] Always use sync sessions in Celery tasks
- [ ] Create `*_sync()` variants of database helpers for background tasks
- [ ] Never import async session helpers in task modules
- [ ] Add integration tests that run actual Celery tasks
- [ ] Consider using `psycopg2` as sync driver (vs `asyncpg`)

---

## Testing Strategies

### LESSON: Contract Tests for Third-Party API Integration
**Source**: Enterprise-Translation-System | **Date**: 2026-01-11

**Context**: Using Stripe for billing and third-party APIs for services. Need to ensure our code doesn't break when APIs change, without hitting production APIs in tests.

**Problem**: Unit tests mock everything (unrealistic), integration tests hit real APIs (slow + costs money). How to test API integration without either extreme?

**Solution - Contract Tests**: Test the expected structure of third-party API responses without mocking or hitting production. Use test/sandbox modes when available.

**Implementation**:
```javascript
// billingContracts.test.js - Tests Stripe API contract
describe('Stripe API Contracts', () => {
  it('checkout session has required fields', async () => {
    // Use Stripe TEST mode (free, no real transactions)
    const session = await stripe.checkout.sessions.create({
      mode: 'subscription',
      line_items: [{ price: 'price_test_xxx', quantity: 1 }],
      success_url: 'http://localhost/success',
      cancel_url: 'http://localhost/cancel'
    });

    // Contract: Stripe MUST return these fields
    expect(session).toHaveProperty('id');
    expect(session).toHaveProperty('url');
    expect(session).toHaveProperty('customer');
    expect(session.mode).toBe('subscription');

    // Document the structure we depend on
    expect(typeof session.id).toBe('string');
    expect(typeof session.url).toBe('string');
  });

  it('webhook event structure matches expectations', () => {
    // Test our assumptions about webhook payload
    const mockEvent = {
      type: 'checkout.session.completed',
      data: {
        object: {
          id: 'cs_test_xxx',
          customer: 'cus_test_xxx',
          subscription: 'sub_test_xxx'
        }
      }
    };

    // Contract: Our webhook handler expects this structure
    expect(mockEvent.data.object).toHaveProperty('id');
    expect(mockEvent.data.object).toHaveProperty('customer');
    expect(mockEvent.data.object).toHaveProperty('subscription');

    // Ensure our handler doesn't crash
    const result = handleWebhook(mockEvent);
    expect(result).toBeDefined();
  });

  it('subscription object has required fields', async () => {
    const subscription = await stripe.subscriptions.retrieve('sub_test_xxx');

    // Contract: Fields we use in billing logic
    expect(subscription).toHaveProperty('status');
    expect(subscription).toHaveProperty('current_period_end');
    expect(subscription).toHaveProperty('items');
    expect(['active', 'past_due', 'canceled']).toContain(subscription.status);
  });
});
```

**Key Benefits**:
- **Catches breaking changes early**: If Stripe removes a field, test fails immediately
- **Documents API dependencies**: Tests show exactly which fields we rely on
- **Faster than integration tests**: No database setup, just API structure validation
- **More realistic than unit tests**: Uses real API in test mode, not mocks
- **Free in test/sandbox mode**: No cost for Stripe test transactions

**When to Use Contract Tests**:
- Third-party payment APIs (Stripe, PayPal)
- External data providers (weather, geocoding, stock prices)
- Authentication providers (Auth0, Firebase, OAuth)
- Email/SMS services (SendGrid, Twilio)
- Any API where structure changes would break your app

**Prevention**:
- [ ] Write contract tests for ALL third-party API integrations
- [ ] Run contract tests in CI before deployment
- [ ] Update contracts when APIs announce breaking changes
- [ ] Use test/sandbox modes when available (Stripe test mode, etc.)
- [ ] Document exactly which fields your code depends on
- [ ] Test both success and error response structures

---

### LESSON: Unit Tests Don't Catch Integration Issues
**Source**: ContentSage | **Date**: 2024-12-26

**Evidence**: All unit tests passed, but production had:
- Firebase UID format errors
- Nginx proxy auth failures
- Frontend/backend contract mismatches

**Solution**: Layered testing strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    TESTING PYRAMID                          │
├─────────────────────────────────────────────────────────────┤
│                        /\                                   │
│                       /  \    E2E (user flows)              │
│                      /    \   10% of tests                  │
│                     /──────\                                │
│                    /        \                               │
│                   /          \  Integration                 │
│                  /            \ (service boundaries)        │
│                 /──────────────\ 20% of tests               │
│                /                \                           │
│               /                  \  Contract Tests          │
│              /                    \ (FE/BE agreement)       │
│             /────────────────────────\ 20% of tests         │
│            /                          \                     │
│           /                            \  Unit Tests        │
│          /                              \ (logic)           │
│         /────────────────────────────────\ 50% of tests     │
│                                                             │
│  + Post-Deploy Smoke Tests (health, auth, critical paths)   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

| Layer | What It Catches | Example |
|-------|----------------|---------|
| Unit | Logic bugs | `test_calculate_discount()` |
| Contract | FE/BE mismatch | `test_plan_ids_match()` |
| Integration | Service boundaries | `test_firebase_to_database()` |
| E2E | Full user flows | `test_complete_purchase()` |
| Smoke | Deployment issues | `curl /health` after deploy |

**Prevention**:
- [ ] Require all 5 layers before production
- [ ] Smoke tests auto-run after deploy
- [ ] Block deploy if contract tests fail

---

## Contributed from Enterprise-Translation-System (2025-12-28)

### LESSON: AWS SES Requires Domain AND Email Verification
**Source**: Enterprise-Translation-System | **Date**: 2025-12-28

**Symptom**: Email sending fails with "554 Message rejected: Email address is not verified"

**Root Cause**: AWS SES in sandbox mode requires:
1. Domain verification (DKIM records)
2. Sender email verification (or domain covers all addresses)
3. In sandbox: recipient emails must also be verified

**Solution**:
1. Verify domain in SES (add DKIM CNAME records)
2. Add SPF and DMARC records for deliverability
3. Set up Custom MAIL FROM domain for professional appearance
4. Request production access to send to any recipient

```
# Required DNS Records for AWS SES

# DKIM (3 CNAME records - AWS provides values)
xxx._domainkey.domain.com CNAME xxx.dkim.amazonses.com

# SPF
domain.com TXT "v=spf1 include:amazonses.com ~all"

# DMARC
_dmarc.domain.com TXT "v=DMARC1; p=quarantine; rua=mailto:feedback@domain.com"

# Custom MAIL FROM (optional but recommended)
mail.domain.com MX 10 feedback-smtp.us-east-1.amazonses.com
mail.domain.com TXT "v=spf1 include:amazonses.com ~all"
```

**Prevention**:
- [ ] Document full SES setup checklist in deployment guide
- [ ] Add email health check on startup that logs configuration status
- [ ] Use environment variable validation for all SMTP settings
- [ ] Test email delivery after every deployment

---

### LESSON: Defensive Body Parsing in Express Routes
**Source**: Enterprise-Translation-System | **Date**: 2025-12-28

**Symptom**: `TypeError: Cannot destructure property 'x' of 'req.body' as it is undefined`

**Root Cause**: Routes that expect JSON body can receive requests with:
- No body (browser sendBeacon, beforeunload events)
- Empty body
- Malformed body that body-parser rejects silently

**Solution**:
```javascript
// Before (crashes if no body):
const { sessionId, userId } = req.body;

// After (safely handles missing body):
const { sessionId, userId } = req.body || {};

// Or with validation middleware:
const validateBody = (schema) => (req, res, next) => {
  if (!req.body || Object.keys(req.body).length === 0) {
    return res.status(400).json({ error: 'Request body required' });
  }
  // ... schema validation
  next();
};
```

**Prevention**:
- [ ] Always use defensive destructuring: `req.body || {}`
- [ ] Add Zod/Joi validation middleware to all POST/PUT/PATCH routes
- [ ] Analytics/tracking endpoints should be extra defensive (called in edge cases)
- [ ] Test routes with empty body in integration tests

---


---

## Contributed from app (2025-12-29)
### LESSON: React Strict Mode Causes Double useEffect Execution

---

## Contributed from insta-based-shop (2025-12-29)

### LESSON: OpenAI Vision API Cannot Fetch Protected CDN URLs
**Source**: insta-based-shop | **Date**: 2025-12-28

**Symptom**: OpenAI Vision API returns `400 invalid_image_url` error when analyzing social media images

**Root Cause**: Social media CDN URLs (Instagram, TikTok, etc.) are:
- Protected by authentication headers
- Time-limited (expire after a few hours)
- Blocked for external server access

OpenAI's servers cannot download these URLs directly.

**Solution**:
```python
def _download_image_as_base64(self, image_url: str) -> str | None:
    """Download image and convert to base64 data URI."""
    response = requests.get(image_url, timeout=30, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    response.raise_for_status()

    content_type = response.headers.get('Content-Type', 'image/jpeg')
    mime_type = 'image/jpeg' if 'jpeg' in content_type or 'jpg' in content_type else 'image/png'

    import base64
    image_base64 = base64.b64encode(response.content).decode('utf-8')
    return f"data:{mime_type};base64,{image_base64}"
```

**Prevention**:
- [ ] Always download protected/CDN images before sending to external vision APIs
- [ ] Add timeout and error handling for image downloads
- [ ] Consider caching downloaded images to avoid re-fetching

---

### LESSON: GitHub Actions Need Explicit Write Permissions for Push
**Source**: insta-based-shop | **Date**: 2025-12-28

**Symptom**: Workflow runs but fails at "Push changes" step with permission denied

**Root Cause**: GitHub Actions default to read-only permissions. Without explicit `contents: write`, the workflow cannot push commits.

**Solution**:
```yaml
permissions:
  contents: write

jobs:
  generate-content:
    runs-on: ubuntu-latest
    # ...
```

**Prevention**:
- [ ] Always add `permissions` block for workflows that modify the repo
- [ ] Document required permissions in workflow comments
- [ ] Test push step in a test branch first

---

### LESSON: Rate Limiting Must Account for Reverse Proxies
**Source**: insta-based-shop | **Date**: 2025-12-24

**Symptom**: Rate limiting ineffective in production - all requests appear from same IP

**Root Cause**: Using `request.remote_addr` behind a reverse proxy (nginx, Cloudflare, AWS ALB) returns the proxy IP, not the client IP. All users share the same rate limit bucket.

**Solution**:
```python
def get_client_ip() -> str:
    """Get client IP address, accounting for reverse proxies."""
    # Check X-Forwarded-For header (set by reverse proxies)
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()
        if client_ip and (client_ip.count('.') == 3 or ':' in client_ip):
            return client_ip
    # Check X-Real-IP header
    real_ip = request.headers.get('X-Real-IP', '')
    if real_ip:
        return real_ip.strip()
    return request.remote_addr or 'unknown'
```

**Prevention**:
- [ ] Always use proxy-aware IP detection in rate limiters
- [ ] Test rate limiting with actual proxy configuration
- [ ] Document expected proxy headers in deployment docs

---

### LESSON: XSS Prevention Requires Both Server and Client Escaping
**Source**: insta-based-shop | **Date**: 2025-12-24

**Symptom**: Security audit identified XSS vulnerability in dynamic content

**Root Cause**: User-generated content was inserted into DOM without escaping:
```javascript
// DANGEROUS
element.innerHTML = `<a href="${product.url}">${product.name}</a>`;
```

**Solution**:
```javascript
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeAttr(text) {
    return text.replace(/[&<>"']/g, char => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;',
        '"': '&quot;', "'": '&#39;'
    }[char]));
}

// SAFE
element.innerHTML = `<a href="${escapeAttr(product.url)}">${escapeHtml(product.name)}</a>`;
```

**Prevention**:
- [ ] Use textContent instead of innerHTML where possible
- [ ] Escape all dynamic content inserted into HTML
- [ ] Add XSS tests to security test suite
- [ ] Consider using a template library with auto-escaping

---

### LESSON: Python Packages Need __init__.py for Docker/PaaS Imports
**Source**: insta-based-shop | **Date**: 2025-12-28

**Symptom**: `ModuleNotFoundError: No module named 'backend'` on Railway/Heroku despite working locally

**Root Cause**: PaaS Dockerfile runs from repo root. Python doesn't recognize directories as packages without `__init__.py`.

**Solution**:
```bash
# Create the init file
touch backend/__init__.py
```

And in Dockerfile:
```dockerfile
COPY backend/ backend/
# Now `from backend.api_server import app` works
```

**Prevention**:
- [ ] Always add `__init__.py` to Python directories that will be imported
- [ ] Test Docker builds locally before deploying
- [ ] Use `python -c "import backend"` as a build verification step

---

## Frontend & UI Patterns

### LESSON: Avoid Chained API Calls in Conversational UIs
**Source**: Multi-Agent Content Pipeline | **Date**: 2025-12-29

**Symptom**: UI feels sluggish, multiple loading spinners, race conditions in chat interfaces

**Root Cause**: Making sequential API calls (e.g., send message → poll for response → fetch updated history) creates poor UX and complexity. Each call adds latency and potential failure points.

**Solution**:
```typescript
// BAD: Chained calls
const sendMessage = async (msg: string) => {
  await api.post('/messages', { content: msg });
  await pollForResponse();  // Polls until AI responds
  await fetchMessages();    // Refetch all messages
};

// GOOD: Single call with streaming or webhooks
const sendMessage = async (msg: string) => {
  const response = await api.post('/messages', {
    content: msg,
    stream: true
  });
  // Server returns complete state or streams response
  setMessages(response.data.messages);
};
```

**Prevention**:
- [ ] Design APIs to return complete state after mutations
- [ ] Use WebSockets/SSE for real-time updates instead of polling
- [ ] Batch related operations into single endpoints
- [ ] Consider optimistic UI updates for perceived performance

---

### LESSON: CSS Responsive Breakpoints Must Be Explicit for Dashboard Grids
**Source**: Multi-Agent Content Pipeline | **Date**: 2026-01-01

**Symptom**: Dashboard stat cards misaligned on mid-sized screens, tables overflowing without scroll

**Root Cause**: Using `grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))` creates unpredictable column counts at different widths.

**Solution**:
```css
/* Explicit breakpoints instead of auto-fit */
@media (max-width: 480px) {
    .grid { grid-template-columns: 1fr; }
}
@media (min-width: 481px) and (max-width: 768px) {
    .grid { grid-template-columns: repeat(2, 1fr); }
}
@media (min-width: 769px) and (max-width: 1024px) {
    .grid { grid-template-columns: repeat(2, 1fr); }
}
@media (min-width: 1025px) {
    .grid { grid-template-columns: repeat(4, 1fr); }
}

/* Table wrapper for horizontal scroll */
.table-wrapper {
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}
```

**Prevention**:
- [ ] Use explicit breakpoints for predictable layouts
- [ ] Always wrap tables in scrollable container
- [ ] Test at 320px, 768px, 1024px, and 1440px widths
- [ ] Add flex-wrap to navigation and button groups

---

### LESSON: Dark Mode with System Preference Detection
**Source**: Enterprise-Translation-System | **Date**: 2026-01-11

**Context**: Users want dark mode for late-night usage but shouldn't have to manually configure it.

**Solution**: Auto-detect system preference on load via `prefers-color-scheme` media query. Listen for system theme changes. Provide manual toggle for override.

**Implementation**:
```typescript
// 1. Detect system preference on mount
const [darkMode, setDarkMode] = useState(() => {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false;
});

// 2. Listen for system preference changes
useEffect(() => {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  const handler = (e: MediaQueryListEvent) => setDarkMode(e.matches);
  mediaQuery.addEventListener('change', handler);
  return () => mediaQuery.removeEventListener('change', handler);
}, []);

// 3. Create theme-aware color palette
const theme = {
  bg: darkMode ? '#1a1a1a' : '#ffffff',
  text: darkMode ? '#e0e0e0' : '#333333',
  accent: darkMode ? '#4CAF50' : '#2196F3',
  border: darkMode ? '#444' : '#ddd'
};

// 4. Apply to Material-UI
<ThemeProvider theme={createTheme({
  palette: { mode: darkMode ? 'dark' : 'light' }
})}>
```

**Key Patterns**:
- Respect system preference first (`prefers-color-scheme`)
- Listen for OS-level theme changes
- Provide manual override toggle
- Use semantic colors (bg, text, accent) not literal hex values
- Apply theme consistently across all components

**Prevention**:
- [ ] Always respect `prefers-color-scheme` media query
- [ ] Provide manual toggle for user preference
- [ ] Test all components in both modes before shipping
- [ ] Use theme context/provider, not hardcoded colors
- [ ] Store user override in localStorage for persistence

---

### LESSON: Split View Layout for Live Operation Interfaces
**Source**: Enterprise-Translation-System | **Date**: 2026-01-11

**Context**: Operators need to see data history while simultaneously controlling live operations. Single-column layouts force constant scrolling.

**Problem**: Translation operators needed to see transcript history while adjusting language settings. Original single-column layout forced scrolling between transcript and controls, causing operators to lose context.

**Solution**: Split view with scrollable content (left, 70%) and sticky controls (right, 30%).

**Implementation**:
```typescript
<Box sx={{ display: 'flex', gap: 2, height: '100vh' }}>
  {/* Left: Scrollable primary content */}
  <Box sx={{ flex: 7, overflowY: 'auto', pr: 2 }}>
    <TranscriptDisplay segments={segments} />
  </Box>

  {/* Right: Sticky controls panel */}
  <Box sx={{
    flex: 3,
    position: 'sticky',
    top: 0,
    height: 'fit-content',
    maxHeight: '100vh',
    overflowY: 'auto'
  }}>
    <ControlPanel />
    <Settings />
  </Box>
</Box>
```

**Key Patterns**:
- **70/30 split**: Prioritize primary content over controls
- **Sticky controls**: Keep tools accessible while scrolling content
- **Separate scroll containers**: Prevent loss of control access
- **Flex layout**: Adapts to screen sizes automatically
- **Full viewport height**: `height: '100vh'` for immersive experience

**Prevention**:
- [ ] For live operation interfaces, use split view (data + controls)
- [ ] Make controls sticky if primary content scrolls
- [ ] Allocate more space to primary content (70%+)
- [ ] Test on both 1920x1080 and 1366x768 screens
- [ ] Consider responsive breakpoints for mobile (single column)

---

### LESSON: Real-time Audio Waveform Visualization for User Feedback
**Source**: Enterprise-Translation-System | **Date**: 2026-01-11

**Symptom**: Operators couldn't tell if audio was being captured correctly. They would speak but get no visual feedback until processing completed (2-3 second delay).

**Root Cause**: Microphone was working, but there was no real-time visual indicator that audio was being captured at the right levels. Users had no way to know if they were too quiet, too loud, or if the mic was working at all.

**Solution**: Built AudioWaveform component using Web Audio API's AnalyserNode. Real-time waveform drawn on canvas at 60fps. Color-coded by state (green = active, gray = silent).

**Implementation**:
```typescript
const AudioWaveform = ({ stream }: { stream: MediaStream | null }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!stream) return;

    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;

    const source = audioContext.createMediaStreamSource(stream);
    source.connect(analyser);

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      analyser.getByteTimeDomainData(dataArray);

      const canvas = canvasRef.current;
      if (!canvas) return;

      const ctx = canvas.getContext('2d');
      const width = canvas.width;
      const height = canvas.height;

      // Detect if audio is active
      const hasAudio = dataArray.some(v => Math.abs(v - 128) > 10);

      ctx.fillStyle = '#1a1a1a';
      ctx.fillRect(0, 0, width, height);

      // Draw waveform
      ctx.lineWidth = 2;
      ctx.strokeStyle = hasAudio ? '#4CAF50' : '#666';  // Green if active
      ctx.beginPath();

      const sliceWidth = width / bufferLength;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * height) / 2;

        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);

        x += sliceWidth;
      }

      ctx.lineTo(width, height / 2);
      ctx.stroke();

      requestAnimationFrame(draw);
    };

    draw();

    return () => {
      audioContext.close();
    };
  }, [stream]);

  return <canvas ref={canvasRef} width={300} height={60} />;
};
```

**Key Insights**:
- Real-time feedback is critical for live audio interfaces
- Web Audio API `AnalyserNode` provides low-latency audio analysis
- 60fps animation via `requestAnimationFrame` keeps feedback responsive
- Color-coding based on audio levels provides instant visual confirmation
- Threshold detection (>10 units from baseline) filters out noise

**Prevention**:
- [ ] Always provide real-time visual feedback for audio input
- [ ] Use color to indicate state (active = green, silent = gray, error = red)
- [ ] Test with non-technical users who can't check DevTools
- [ ] Add clipping indicators if audio levels exceed threshold
- [ ] Display numerical levels for precise adjustment

---

### LESSON: Multilingual Content Requires Language-Specific Formatting
**Source**: youtube-intnl-blog | **Date**: 2026-01-11

**Symptom**: German and Japanese posts had formatting issues - dates in wrong format, numbers with incorrect separators, quotes using English style.

**Root Cause**: Copied English template to all languages without localizing formatting rules. Each language has different conventions for dates, numbers, quotes, and punctuation.

**Solution**: Language-specific formatters for common elements.

**Date Formatting**:
```python
DATE_FORMATS = {
    'en': '%B %d, %Y',           # January 10, 2026
    'es': '%d de %B de %Y',     # 10 de enero de 2026
    'de': '%d. %B %Y',          # 10. Januar 2026
    'fr': '%d %B %Y',           # 10 janvier 2026
    'ja': '%Y年%m月%d日',        # 2026年01月10日
    'pt': '%d de %B de %Y',     # 10 de janeiro de 2026
    'it': '%d %B %Y',           # 10 gennaio 2026
    'hi': '%d %B %Y',           # 10 जनवरी 2026
    'id': '%d %B %Y'            # 10 Januari 2026
}

def format_date(date: datetime, language: str) -> str:
    """Format date according to language conventions."""
    return date.strftime(DATE_FORMATS.get(language, DATE_FORMATS['en']))
```

**Number Formatting**:
```python
NUMBER_FORMATS = {
    'en': (lambda n: f"{n:,}"),                         # 1,000,000
    'de': (lambda n: f"{n:,.0f}".replace(',', '.')),   # 1.000.000
    'fr': (lambda n: f"{n:,.0f}".replace(',', ' ')),   # 1 000 000
    'es': (lambda n: f"{n:,.0f}".replace(',', '.')),   # 1.000.000
    'pt': (lambda n: f"{n:,.0f}".replace(',', '.')),   # 1.000.000
}

def format_number(num: int, language: str) -> str:
    """Format numbers with language-specific separators."""
    formatter = NUMBER_FORMATS.get(language, NUMBER_FORMATS['en'])
    return formatter(num)
```

**Quote Styles**:
```python
QUOTE_STYLES = {
    'en': ('"{}"'),              # "Hello"
    'de': ('„{}"'),              # „Hallo"
    'fr': ('« {} »'),            # « Bonjour »
    'ja': ('「{}」'),            # 「こんにちは」
    'es': ('«{}»'),              # «Hola»
    'pt': ('"{}"'),              # "Olá"
}

def format_quote(text: str, language: str) -> str:
    """Wrap text in language-appropriate quotation marks."""
    template = QUOTE_STYLES.get(language, QUOTE_STYLES['en'])
    return template.format(text)
```

**Key Insights**:
- Each language has distinct formatting conventions
- Date/number/quote formatting must be localized
- Templates alone are not enough - need code-level formatting
- ISO 8601 dates work internally, local formats for display
- Test with native speakers to catch formatting issues

**Prevention**:
- [ ] Create formatter functions for each supported language
- [ ] Never hardcode date/number formats in templates
- [ ] Use locale-aware formatting libraries (babel, ICU, intl)
- [ ] Test multilingual output with native speakers
- [ ] Document formatting conventions per language in wiki/docs

---

### LESSON: Framework/Configuration Duplication Causes Drift
**Source**: Multi-Agent Content Pipeline | **Date**: 2025-12-29

**Symptom**: Changes work in one place but not another, inconsistent behavior across environments

**Root Cause**: Same configuration or logic defined in multiple places (e.g., API routes in both Next.js config and middleware, environment variables in .env and docker-compose, validation rules in frontend and backend).

**Solution**:
```typescript
// BAD: Duplicated route config
// next.config.js
rewrites: [{ source: '/api/:path*', destination: 'http://backend:8000/:path*' }]
// middleware.ts
if (path.startsWith('/api')) { proxy(request); }

// GOOD: Single source of truth
// lib/routes.ts
export const API_ROUTES = {
  proxy: '/api/:path*',
  backend: process.env.BACKEND_URL
};
// Import and use everywhere
```

**Prevention**:
- [ ] Grep codebase for duplicated strings/patterns before adding config
- [ ] Create shared constants files for routes, env vars, validation rules
- [ ] Document canonical location for each type of configuration
- [ ] Use schema validation (Zod/Yup) shared between frontend and backend

---

### LESSON: Compact Product Pills with Hover Expand for Mobile-First Design
**Source**: insta-based-shop | **Date**: 2026-01-11

**Symptom**: Product sections with 5-10 items took up entire mobile screen, forcing users to scroll past products to read content.

**Root Cause**: Each product displayed as full card with image, title, price, and button. On mobile, this consumed 150px+ per product vertically.

**Solution**: Compact pills (30px height) with hover/tap to expand and show details.

**Implementation**:
```typescript
const ProductPill = ({ product }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`product-pill ${expanded ? 'expanded' : ''}`}
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Compact state (always visible) */}
      <div className="pill-header">
        <span className="product-name">{product.name}</span>
        <span className="price">${product.price}</span>
      </div>

      {/* Expanded state (on hover/tap) */}
      {expanded && (
        <div className="pill-details">
          <img src={product.image} alt={product.name} />
          {product.affiliateUrl ? (
            <a href={product.affiliateUrl} target="_blank">
              Shop Now
            </a>
          ) : (
            <span className="coming-soon">Links coming soon</span>
          )}
        </div>
      )}
    </div>
  );
};
```

**CSS**:
```css
.product-pill {
  height: 30px;
  background: #f5f5f5;
  border-radius: 15px;
  padding: 5px 15px;
  margin: 5px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.product-pill.expanded {
  height: auto;
  min-height: 150px;
  border-radius: 8px;
  padding: 15px;
}

.pill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pill-details {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.pill-details img {
  max-height: 80px;
  object-fit: contain;
}

/* Mobile: tap to expand/collapse */
@media (max-width: 768px) {
  .product-pill {
    touch-action: manipulation;
  }
}
```

**Key Patterns**:
- **Default state**: Tiny colored pills with product name + price only (30px height)
- **Hover/tap**: Expand to show image, affiliate link
- **Mobile**: Tap to expand, tap outside or tap again to collapse
- **Loading state**: "Links coming soon" for products without affiliate URLs yet
- **Progressive disclosure**: Show essential info first, details on demand

**Key Insights**:
- Compact default state saves vertical space (critical for mobile)
- Progressive disclosure reduces cognitive load
- Hover on desktop, tap on mobile for consistent UX
- Loading states provide context when features are incomplete
- Color-coding pills can indicate product categories

**Prevention**:
- [ ] Always design mobile-first for content-heavy pages
- [ ] Use progressive disclosure for secondary information
- [ ] Test with 10+ items to ensure scalability
- [ ] Add loading states for async data
- [ ] Provide context when features are incomplete ("coming soon" vs broken)

---

## CMS Integration & Content Management

### LESSON: Decap CMS Requires YAML Frontmatter, Not JavaScript Exports
**Source**: Cosmos Web Tech / eAwesome / CloudGeeks | **Date**: 2026-01-14

**Symptom**: Decap CMS interface loaded successfully with GitHub OAuth authentication, but blog posts appeared as white/empty boxes with no titles visible. Console showed YAML syntax errors. CMS could not parse or display existing blog posts.

**Root Cause**: Astro blog posts were using **JavaScript frontmatter format** (`export const frontmatter = {...}`) which is valid Astro code but incompatible with Decap CMS. Decap CMS is a Git-based CMS that directly reads and writes Markdown/MDX files with YAML frontmatter. It cannot parse or execute JavaScript code.

**Technical Details**:
```astro
<!-- ❌ INCOMPATIBLE: JavaScript frontmatter (Astro component format) -->
---
import BlogLayout from '../../layouts/BlogLayout.astro';

export const frontmatter = {
  title: "My Blog Post",
  description: "Post description",
  publishedAt: "2024-01-14"
};
---
<BlogLayout {...frontmatter}>
  Content here
</BlogLayout>
```

```mdx
<!-- ✅ COMPATIBLE: YAML frontmatter (Content Collections / MDX format) -->
---
title: "My Blog Post"
description: "Post description"
publishedAt: "2024-01-14"
---

Content here
```

**Attempted Solution**: Tried converting blog posts from Astro component format to Astro Content Collections with MDX format. Conversion revealed additional issues:
- Existing HTML content had structural problems (unclosed tags, invalid nesting)
- MDX parser rejected malformed HTML structures
- Would require manual cleanup of all posts

**Final Solution**: Implemented **local CMS workflow** instead of production CMS:
1. Run `npm run cms` to start Decap CMS proxy server (port 8081)
2. Run `npm run dev` to start Astro dev server
3. Access CMS at `http://localhost:4321/admin`
4. Edit posts through CMS interface
5. Commit and push changes to GitHub for deployment

**Advantages of Local Workflow**:
- ✅ Works with existing blog structure (no conversion needed)
- ✅ Full CMS interface for content management
- ✅ Live preview during editing
- ✅ Git-based version control
- ✅ Can create new posts through CMS
- ✅ Professional developers' preferred method
- ✅ Better testing before production deployment

**Multi-Site Implementation**:
```bash
# Package.json script for local CMS backend
"scripts": {
  "cms": "npx decap-server"
}

# CMS config: public/admin/config.yml
backend:
  name: github
  repo: username/repo-name
  branch: main
  base_url: https://yoursite.com
  auth_endpoint: /api/auth

local_backend: true  # Enable local workflow

media_folder: "public/images/blog"
public_folder: "/images/blog"

collections:
  - name: "blog"
    label: "Blog Posts"
    folder: "src/pages/blog"
    create: true
    slug: "{{slug}}"
    extension: "astro"
    format: "frontmatter"
    identifier_field: "title"
    summary: "{{title}} - {{publishedAt}}"
    fields:
      - { label: "Title", name: "title", widget: "string" }
      - { label: "Description", name: "description", widget: "text" }
      - { label: "Publish Date", name: "publishedAt", widget: "datetime" }
      - { label: "Category", name: "category", widget: "select", options: [...] }
      - { label: "Body", name: "body", widget: "markdown" }
```

**OAuth Handler for Production CMS** (Cloudflare Pages):
```typescript
// functions/api/auth.ts
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;
  const url = new URL(request.url);
  const code = url.searchParams.get('code');

  if (!code) {
    const clientId = env.GITHUB_CLIENT_ID;
    const redirectUri = `${url.origin}/api/auth`;
    const scope = 'repo,user';
    const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scope}`;
    return Response.redirect(githubAuthUrl, 302);
  }

  const tokenResponse = await fetch('https://github.com/login/oauth/access_token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({
      client_id: env.GITHUB_CLIENT_ID,
      client_secret: env.GITHUB_CLIENT_SECRET,
      code,
    }),
  });

  const data = await tokenResponse.json();
  return new Response(`
    <!DOCTYPE html><html><body><script>
      window.opener.postMessage(${JSON.stringify({
        token: data.access_token,
        provider: 'github'
      })}, window.location.origin);
      window.close();
    </script></body></html>
  `, { headers: { 'Content-Type': 'text/html' } });
};
```

**Next.js Variant** (for Railway/Vercel deployments):
```typescript
// src/app/api/auth/route.ts
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const code = searchParams.get('code');

  if (!code) {
    const clientId = process.env.GITHUB_CLIENT_ID;
    const redirectUri = `${request.nextUrl.origin}/api/auth`;
    const scope = 'repo,user';
    const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scope}`;
    return NextResponse.redirect(githubAuthUrl);
  }
  // ... similar token exchange logic
}
```

**Prevention**:
- [ ] Before implementing any CMS, verify content format compatibility
- [ ] Check CMS documentation for supported frontmatter formats
- [ ] Consider content structure early in project planning
- [ ] Default to YAML frontmatter for CMS-managed content
- [ ] Test CMS integration with sample posts before committing
- [ ] Local CMS workflow is industry standard - prefer it over production CMS

**Code Pattern to Follow**:
```astro
---
# ✅ GOOD: YAML frontmatter (CMS-compatible)
title: "Post Title"
description: "Post description"
publishedAt: "2024-01-14"
author: "Author Name"
---

import Layout from '../layouts/Layout.astro';

<Layout {...Astro.props}>
  <h1>{Astro.props.title}</h1>
  Content here
</Layout>
```

**Code Pattern to Avoid**:
```astro
---
# ❌ BAD: JavaScript export (CMS-incompatible)
export const frontmatter = {
  title: "Post Title",
  description: "Post description"
};
---
```

**Key Insights**:
- Git-based CMSs (Decap, Netlify CMS, Forestry) require parseable frontmatter formats
- JavaScript/TypeScript exports are compile-time constructs, not runtime data
- Local CMS workflow provides better developer experience and control
- Production CMS is optional feature, not requirement
- Multi-site OAuth requires separate GitHub OAuth apps per domain

**Impact**: 4 websites (cosmoswebtech.com.au, eawesome.com.au, insights.cloudgeeks.com.au, ashganda.com) now have local CMS capability with comprehensive documentation.

---

## Monetization & Affiliate Marketing

### LESSON: Hybrid Affiliate Strategy - Direct Tags for Amazon, Skimlinks for Others
**Source**: insta-based-shop | **Date**: 2026-01-11

**Context**: Fashion content includes products from many retailers (Amazon, Nordstrom, ASOS, Zara, etc.). Different monetization strategies have different trade-offs.

**Problem**: Single affiliate network (Skimlinks) means revenue share of 50-75%. For Amazon specifically, this results in only 50% of already-low 1-3% commission.

**Solution**: Hybrid approach - Direct Amazon Associates tags (keep 100% of commission), Skimlinks for all other merchants (handles 1000+ retailers automatically).

**Revenue Comparison**:
```
Amazon via Skimlinks:
  Base commission: 3%
  Revenue share: 50%
  Actual earnings: 1.5% per sale

Amazon Direct:
  Base commission: 3%
  Revenue share: 100%
  Actual earnings: 3% per sale  (2× revenue)

Nordstrom via Skimlinks:
  Base commission: 8%
  Revenue share: 75%
  Actual earnings: 6% per sale
```

**Implementation**:
```python
# Server-side URL processing - add Amazon tag before page generation
def process_product_url(url: str, merchant: str) -> str:
    """Add affiliate tags based on merchant."""
    if 'amazon.' in url:
        # Direct Amazon Associates tag
        tag = os.getenv('AMAZON_ASSOCIATES_TAG', 'yoursite-20')
        if '?' in url:
            return f"{url}&tag={tag}"
        else:
            return f"{url}?tag={tag}"
    else:
        # Return clean URL - Skimlinks JavaScript will handle it
        # Remove existing tracking params for clean URLs
        return remove_tracking_params(url)

def remove_tracking_params(url: str) -> str:
    """Remove affiliate tracking params for clean user experience."""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    # Remove common tracking params
    tracking_params = ['utm_source', 'utm_medium', 'utm_campaign',
                       'ref', 'referrer', 'affiliate_id']
    for param in tracking_params:
        query_params.pop(param, None)

    # Rebuild URL
    clean_query = urlencode(query_params, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path,
                       parsed.params, clean_query, parsed.fragment))
```

**Client-side Skimlinks Integration**:
```html
<!-- Skimlinks automatically converts merchant links -->
<script type="text/javascript">
  (function() {
    var s = document.createElement('script');
    s.type = 'text/javascript';
    s.async = true;
    s.src = 'https://s.skimresources.com/js/YOUR_ID.skimlinks.js';
    var x = document.getElementsByTagName('script')[0];
    x.parentNode.insertBefore(s, x);
  })();
</script>
```

**Key Insights**:
- Direct Amazon Associates doubles Amazon revenue (3% vs 1.5%)
- Skimlinks handles 1000+ other merchants automatically (no manual affiliate program signups)
- Clean URLs improve user trust and click-through rates
- Hybrid approach maximizes total revenue across all merchants
- Amazon tag must be added server-side (cannot rely on JavaScript for SEO/crawlers)
- Different regions use different Amazon domains (.com, .co.uk, .de) - handle appropriately

**Merchant-Specific Considerations**:
```python
AMAZON_DOMAINS = {
    'US': 'amazon.com',
    'UK': 'amazon.co.uk',
    'DE': 'amazon.de',
    'FR': 'amazon.fr',
    'JP': 'amazon.co.jp'
}

AMAZON_TAGS = {
    'US': 'yoursite-20',
    'UK': 'yoursite-21',
    'DE': 'yoursite-21',
    # Register separate tags per region
}
```

**Prevention**:
- [ ] Always use direct affiliate tags for high-volume merchants (Amazon, eBay)
- [ ] Use affiliate networks (Skimlinks, CJ, Rakuten) for long-tail merchants
- [ ] Test affiliate tags in multiple countries/regions (.com, .co.uk, .de)
- [ ] Monitor conversion rates by merchant to identify optimization opportunities
- [ ] Clean tracking params from outbound links for better user experience
- [ ] Document which merchants use direct vs network affiliate links

---

## Security & Rate Limiting

### LESSON: Exclude Password Fields from Security Pattern Matching
**Source**: Enterprise-Translation-System | **Date**: 2026-01-01

**Symptom**: Users with complex passwords containing special characters (`&`, `|`, `;`, `$`) get locked out for 6 hours with "SUSPICIOUS_REQUEST" error

**Root Cause**: Security pattern matching scanned ALL request body fields including passwords. Patterns like `/[;&|`$]/` designed to detect command injection matched legitimate password characters.

**Solution**:
```javascript
// Smart security with field exclusion
const CONFIG = {
  excludedFields: [
    'password', 'newPassword', 'currentPassword', 'oldPassword',
    'apiKey', 'token', 'secret', 'Authorization', 'authToken'
  ]
};

function sanitizeBodyForAnalysis(body) {
  if (!body || typeof body !== 'object') return body;
  const sanitized = { ...body };
  for (const field of CONFIG.excludedFields) {
    if (field in sanitized) {
      sanitized[field] = '[REDACTED]';
    }
  }
  return sanitized;
}

// Analyze only sanitized body
const sanitizedBody = sanitizeBodyForAnalysis(req.body);
if (suspiciousPattern.test(JSON.stringify(sanitizedBody))) {
  // Handle threat - but passwords won't trigger false positives
}
```

**Prevention**:
- [ ] Always exclude password/token fields from security pattern matching
- [ ] Use an explicit excludedFields list, not regex exclusions
- [ ] Test security with passwords containing: `&`, `|`, `;`, `$`, `<`, `>`
- [ ] Document which fields are excluded and why

---

### LESSON: Use Token Bucket Over Counter-Based Rate Limiting
**Source**: Enterprise-Translation-System | **Date**: 2026-01-01

**Symptom**: Users get hard-blocked (403) immediately after hitting rate limit, no warning or graceful degradation

**Root Cause**: Counter-based rate limiting (10 requests/minute) triggers instant hard block. No concept of burst capacity or gradual escalation.

**Solution**:
```javascript
// Token bucket with gradual escalation
const CONFIG = {
  tokenBucket: {
    maxTokens: 20,        // Burst capacity
    refillRate: 2,        // Tokens per second
    refillInterval: 1000  // ms
  },
  escalation: {
    levels: [
      { name: 'normal', threshold: 0, action: 'allow' },
      { name: 'throttle', threshold: 10, action: 'slow', duration: 2000 },
      { name: 'challenge', threshold: 20, action: 'captcha' },
      { name: 'softBlock', threshold: 30, action: 'block429', duration: 5*60*1000 },
      { name: 'hardBlock', threshold: 100, action: 'block403', duration: 60*60*1000 }
    ]
  }
};

// 429 with Retry-After is user-friendly
res.status(429)
   .set('Retry-After', Math.ceil(retryAfterSec))
   .json({
     error: 'RATE_LIMITED',
     retryAfter: retryAfterSec,
     message: `Try again in ${retryAfterSec} seconds`
   });
```

**Prevention**:
- [ ] Use token bucket for rate limiting (allows bursts, smoother UX)
- [ ] Implement gradual escalation: throttle → challenge → soft block → hard block
- [ ] Return 429 with Retry-After header instead of immediate 403
- [ ] Provide bulk unlock capability for legitimate lockout scenarios

---

## Contributed from cloudgeeks-website (2025-12-30)

### LESSON: GitHub OAuth Tokens Require `workflow` Scope for CI Files
**Source**: cloudgeeks-website | **Date**: 2025-12-30

**Symptom**: Push fails with "refusing to allow a Personal Access Token to create or update workflow" error

**Root Cause**: GitHub PATs need explicit `workflow` scope to push changes to `.github/workflows/` files, even if `repo` scope is granted.

**Solution**:
```bash
# Check current token scopes
gh auth status

# Create new token with workflow scope
gh auth login --scopes repo,workflow

# Or regenerate existing PAT with workflow scope in GitHub Settings
```

**Prevention**:
- [ ] Verify PAT scopes before pushing workflow files
- [ ] Use `gh auth status` to check token capabilities
- [ ] Document required scopes in project CONTRIBUTING.md

---

### LESSON: Hugo Template Comments Cannot Contain Shortcode Examples
**Source**: cloudgeeks-website | **Date**: 2025-12-30

**Symptom**: Hugo build fails with "shortcode not closed" or parsing errors

**Root Cause**: Hugo parses shortcode syntax `{{<` even inside HTML comments `<!-- -->`. This breaks when documenting shortcode usage in templates.

**Solution**:
```html
<!-- BAD: This breaks Hugo parsing -->
<!-- Example: {{< mautic type="form" id="1" >}} -->

<!-- GOOD: Use code blocks in markdown instead, or escape -->
<!-- Example: { {< mautic type="form" id="1" >} } (remove spaces) -->
```

**Prevention**:
- [ ] Never put shortcode examples in template comments
- [ ] Document shortcode usage in markdown files only
- [ ] Run `hugo build` after modifying shortcode templates

---

### LESSON: Hugo Deprecated `.Site.IsMultiLingual` in v0.124.0
**Source**: cloudgeeks-website | **Date**: 2025-12-30

**Symptom**: Hugo build warnings or errors about deprecated functions

**Root Cause**: Hugo v0.124.0 deprecated `.Site.IsMultiLingual` in favor of `site.IsMultiLingual` (lowercase).

**Solution**:
```html
<!-- OLD (deprecated) -->
{{ if .Site.IsMultiLingual }}

<!-- NEW -->
{{ if site.IsMultiLingual }}
```

**Prevention**:
- [ ] Check Hugo release notes when upgrading versions
- [ ] Run `hugo --gc --minify` to see deprecation warnings
- [ ] Use `site.` prefix for site-level functions going forward

---

## Contributed from Mautic Integration (2025-12-30)

### LESSON: Mautic API Auth - Password Reset via Database
**Source**: Mautic | **Date**: 2025-12-30

**Symptom**: Cannot log into Mautic admin, password reset email not working

**Root Cause**: Self-hosted Mautic instances may not have email configured, or admin email is inaccessible.

**Solution**:
```bash
# Mautic 5.x - Use CLI to reset password
php bin/console security:hash-password 'NewPassword123!'
# Copy the hash

# Then in MySQL/PostgreSQL:
UPDATE users SET password = 'HASH_FROM_ABOVE' WHERE username = 'admin';

# Clear cache
php bin/console cache:clear
```

**Prevention**:
- [ ] Create `scripts/reset-admin-password.sh` for emergencies
- [ ] Document credentials in password manager
- [ ] Set up email delivery for password reset functionality

---

### LESSON: Form Actions vs Campaigns for Simple Email Triggers
**Source**: Mautic | **Date**: 2025-12-30

**Symptom**: Confusion about whether to use Form Actions or Campaigns for email automation

**Root Cause**: Mautic has two ways to trigger emails: Form Actions (simple) and Campaigns (complex). Using campaigns for simple triggers adds unnecessary complexity.

**Solution**:
```
FORM ACTIONS (use for simple triggers):
├── Form Submit → Send Email Immediately
├── Form Submit → Add to Segment
└── Form Submit → Add Tags

CAMPAIGNS (use for complex flows):
├── Multi-step journeys
├── Time delays between actions
├── Conditional logic (if/else)
└── Multiple entry points
```

**Prevention**:
- [ ] Default to Form Actions for single-action triggers
- [ ] Use Campaigns only when you need delays, conditions, or multiple steps
- [ ] Document which approach is used for each form

---

### LESSON: External Marketing Tool Form IDs Must Be Coordinated
**Source**: Multiple Projects | **Date**: 2025-12-30

**Symptom**: Embedded forms don't load, wrong form appears, or form submission fails

**Root Cause**: Hardcoded form IDs in code don't match the actual form IDs in the marketing platform (Mautic, HubSpot, Mailchimp). IDs change between environments or when forms are recreated.

**Solution**:
```typescript
// BAD: Hardcoded IDs
<MauticForm id={3} />

// GOOD: Configuration-driven
// config/forms.ts
export const FORMS = {
  contact: process.env.NEXT_PUBLIC_MAUTIC_CONTACT_FORM_ID,
  newsletter: process.env.NEXT_PUBLIC_MAUTIC_NEWSLETTER_FORM_ID,
};

// Component
<MauticForm id={FORMS.contact} />
```

**Prevention**:
- [ ] Confirm form IDs with marketing platform before coding
- [ ] Use environment variables for form IDs
- [ ] Document form ID mappings in project config
- [ ] Add error handling for form load failures

---

### LESSON: Mautic Form Field JSON Formats Vary by Field Type
**Source**: Mautic | **Date**: 2025-12-30

**Symptom**: API returns different structures for form fields, causing parsing errors

**Root Cause**: Mautic form field properties vary by type:
- `select` fields have `list` with `{ "value": "label" }` format
- `text` fields have no `list`
- `country` fields have `list` with country codes

**Solution**:
```python
def parse_form_field(field: dict) -> dict:
    """Parse Mautic form field into consistent structure."""
    base = {
        "id": field.get("id"),
        "label": field.get("label"),
        "type": field.get("type"),
        "required": field.get("isRequired", False),
    }

    # Handle select/choice fields
    if field.get("properties", {}).get("list"):
        base["options"] = [
            {"value": k, "label": v}
            for k, v in field["properties"]["list"].items()
        ]

    return base
```

**Prevention**:
- [ ] Create form field templates in `scripts/templates/`
- [ ] Document expected field structures in API docs
- [ ] Add type guards for different field types

---

## Contributed from Infrastructure (2025-12-30)

### LESSON: Cloudflare Tunnel Migration Pattern
**Source**: Infrastructure | **Date**: 2025-12-30

**Symptom**: DNS resolution issues when migrating services to Cloudflare Tunnels

**Root Cause**: During migration, old DNS records may still be cached, or tunnel configuration doesn't match expected hostnames.

**Solution**:
```bash
# Test tunnel with explicit DNS resolution
curl --resolve "domain.com:443:127.0.0.1" https://domain.com

# Cloudflare Tunnel config.yml
tunnel: <TUNNEL_ID>
credentials-file: /etc/cloudflared/credentials.json

ingress:
  - hostname: app.domain.com
    service: http://localhost:3000
  - hostname: api.domain.com
    service: http://localhost:8000
  - service: http_status:404  # Catch-all

# Run tunnel
cloudflared tunnel run <TUNNEL_NAME>
```

**Prevention**:
- [ ] Use `--resolve` flag for testing tunnel DNS
- [ ] Document domain-based config for portable infrastructure
- [ ] Test tunnel connectivity before DNS cutover
- [ ] Keep old DNS records until tunnel is verified

---

### LESSON: site_url HTTPS Redirect Behavior in Self-Hosted Apps
**Source**: Mautic | **Date**: 2025-12-30

**Symptom**: Infinite redirect loops or mixed content warnings after enabling HTTPS

**Root Cause**: Self-hosted applications (Mautic, WordPress, etc.) store `site_url` in database. If this doesn't match the actual URL scheme (HTTP vs HTTPS), redirects fail.

**Solution**:
```sql
-- Check current site_url
SELECT * FROM site_config WHERE name = 'site_url';

-- Update to HTTPS
UPDATE site_config SET value = 'https://app.domain.com' WHERE name = 'site_url';

-- Or in Mautic local.php
'site_url' => 'https://app.domain.com',
```

**Prevention**:
- [ ] Always update site_url when changing domains or protocols
- [ ] Use environment variables for site_url when possible
- [ ] Document site_url location for each self-hosted app

---


---

## Contributed from Enterprise-Translation-System (2026-01-03)

### LESSON: Socket.IO Transport Order for Railway/Proxy Compatibility
**Source**: Enterprise-Translation-System | **Date**: 2026-01-03

**Symptom**: WebSocket connection fails with "Invalid frame header" error on Railway deployment

**Root Cause**: Railway's proxy corrupts WebSocket upgrade requests when `websocket` transport is tried first.

**Solution**:
```javascript
// Use polling first, then upgrade to websocket
const socket = io(`${WS_BASE_URL}/shared-sessions`, {
  transports: ['polling', 'websocket'],  // Polling first!
  forceNew: true
});
```

**Prevention**:
- [ ] Always use `['polling', 'websocket']` transport order for PaaS deployments
- [ ] Test WebSocket connections on actual deployment, not just localhost

---

### LESSON: Socket.IO Silent Disconnect - Use Infinite Reconnection
**Source**: Enterprise-Translation-System | **Date**: 2026-01-04

**Symptom**: Real-time viewers stop receiving data after a few minutes even though broadcaster is still sending. No error messages shown to user.

**Root Cause**: Socket.IO was configured with `reconnectionAttempts: 5`. On PaaS platforms, connections drop due to proxy timeouts or network glitches. After 5 failed attempts, Socket.IO silently gives up - `socket.emit()` fails silently.

**Solution**:
```javascript
// WRONG - gives up after 5 attempts, fails silently
const socket = io(url, {
  reconnectionAttempts: 5,  // Too few!
});

// CORRECT - infinite reconnection with proper event handling
const socket = io(url, {
  transports: ['polling', 'websocket'],
  reconnection: true,
  reconnectionAttempts: Infinity,  // Never give up
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  timeout: 15000,
  forceNew: true
});

// ALWAYS add reconnection event handlers
socket.on("disconnect", (reason) => {
  console.warn("Socket disconnected:", reason);
});

socket.on("reconnect", (attemptNumber) => {
  console.log("Reconnected after", attemptNumber, "attempts");
  // RE-JOIN ROOMS - membership is lost on disconnect!
  socket.emit("join_session", sessionId);
});

socket.on("reconnect_attempt", (attemptNumber) => {
  console.log("Reconnection attempt", attemptNumber);
});
```

**Key Insight**: Room membership is lost on disconnect - must re-join in `reconnect` handler.

**Prevention**:
- [ ] Always use `reconnectionAttempts: Infinity` for critical real-time features
- [ ] Always add `disconnect`, `reconnect`, `reconnect_attempt` event handlers
- [ ] Re-join rooms/sessions in the `reconnect` handler
- [ ] Show connection status in the UI (connected/disconnected/reconnecting)
- [ ] Test by manually disconnecting network to verify reconnection works

---

## Contributed from multi-agent-flow-content-pipeline (2026-01-05)

### LESSON: Mautic API Segment Filters Require Specific Format with Object and Properties
**Source**: Quiz Guru Pipeline | **Date**: 2026-01-05

**Symptom**: Creating Mautic segments with filters via API failed with "properties: This form should not contain extra fields" and "operator: This value is not valid".

**Root Cause**: Mautic segment filter API requires specific field structure including `object`, `type`, and `properties.filter` - not just top-level fields.

**Solution**:
```python
# WRONG format
{
    "field": "tags",
    "type": "tags",
    "operator": "in",
    "filter": ["value"]  # Wrong: filter at top level
}

# CORRECT format
{
    "glue": "and",
    "field": "project_source",
    "object": "lead",          # Required: specifies contact object
    "type": "text",            # Match the field type in Mautic
    "operator": "=",           # Use "=" not "in" for text fields
    "properties": {
        "filter": "value"      # Filter inside properties object
    }
}
```

**Prevention**:
- [ ] Query existing segment to see correct filter format: `GET /api/segments/{id}`
- [ ] Match field `type` to actual Mautic field type (text, select, datetime, number)
- [ ] Always include `object: "lead"` for contact fields
- [ ] Test with one segment before batch creation

---

### LESSON: Mautic Select Field Options Must Exist Before Using in Segment Filters
**Source**: Quiz Guru Pipeline | **Date**: 2026-01-05

**Symptom**: Segment filters for select field values failed with "filter: This value is not valid" even with correct format.

**Root Cause**: The select field didn't have the filter value as one of its dropdown options. Mautic validates filter values against the field's allowed options.

**Solution**:
```bash
# 1. Check existing field options
curl -s "$URL/api/fields/contact" | jq '.fields[] | select(.alias=="field_name") | .properties.list'

# 2. Update field with all required options FIRST
curl -X PATCH "$URL/api/fields/contact/{field_id}/edit" -d '{
    "properties": {
        "list": [
            {"label": "Option 1", "value": "OPTION_1"},
            {"label": "Option 2", "value": "OPTION_2"}
        ]
    }
}'

# 3. NOW segment filters will work
```

**Prevention**:
- [ ] Before creating segments, verify all filter values exist in select fields
- [ ] Keep field options in sync with application constants
- [ ] Add new field options BEFORE deploying features that use them
- [ ] Document which Mautic fields have enum/select constraints

---


---

## Contributed from claude-essay-agent (2026-01-12)
### LESSON: Event Loop Management in Celery Workers with Async Operations

---

## Contributed from multi-agent-flow-content-pipeline (2026-01-14)
### LESSON: WordPress Duplicate Detection Requires Graph-Based Conflict Resolution

---

## Contributed from cosmos-website (2026-01-14)
### LESSON: Decap CMS Requires YAML Frontmatter, Not JavaScript Exports
## Template for New Lessons

```markdown
### LESSON: [Short Title]
**Source**: [Project Name] | **Date**: YYYY-MM-DD

**Symptom**: [What the user/developer observed]

**Root Cause**: [Why it happened]

**Solution**:
```code if applicable```

**Prevention**:
- [ ] [Actionable checklist item]
- [ ] [Another prevention measure]
```

---

## Contributing

To add lessons to this master file:

```bash
# After debugging in your project
/project:post-mortem  # Captures lesson locally

# Then contribute to master
~/streamlined-development/scripts/contribute-lesson.sh
```
