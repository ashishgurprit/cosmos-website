# Decap CMS Local Editing Guide

## Overview

Your websites now have Decap CMS installed for easy blog management. While the full production CMS requires additional setup, the **local CMS workflow** is ready to use and is actually the preferred method used by many professional developers.

## What is Decap CMS?

Decap CMS (formerly Netlify CMS) provides a user-friendly interface to edit your blog posts through a web browser, while keeping all content in Git for version control.

---

## Quick Start

### 1. Start the CMS Backend

Open a terminal and run:

```bash
cd /Users/ashishganda/Development/Cosmos-Website
npm run cms
```

You should see:
```
Netlify CMS Proxy Server listening on port 8081
```

**Keep this terminal window open** - the CMS needs this running.

### 2. Start the Development Server

Open a **second terminal** and run:

```bash
cd /Users/ashishganda/Development/Cosmos-Website
npm run dev
```

You should see:
```
Local: http://localhost:4321/
```

### 3. Access the CMS

Open your web browser and go to:

```
http://localhost:4321/admin
```

You'll see the Decap CMS interface with your blog posts listed.

---

## Managing Blog Posts

### Creating a New Post

1. Click **"New Blog Posts"** button (top right)
2. Fill in the fields:
   - **Title**: Your blog post title
   - **Description**: Meta description for SEO
   - **Publish Date**: Select date
   - **Author**: Default is "Ashish Ganda"
   - **Author Title**: Default is "Founder, Cosmos Web Tech"
   - **Category**: Choose from dropdown
   - **Read Time**: e.g., "5 min read"
   - **Hero Image**: Upload or select image
   - **Content Image**: Optional supporting image
   - **Infographic**: Optional infographic
   - **Body**: Write your blog content (supports Markdown)

3. Click **"Save"** (top left) - saves as draft
4. Click **"Publish"** - ready to deploy
5. Click **"Publish now"** to confirm

### Editing an Existing Post

1. Click on any blog post from the list
2. Make your changes
3. Click **"Save"** to save draft
4. Click **"Publish"** when ready

### Deleting a Post

1. Open the blog post
2. Click **"Delete entry"** (top menu)
3. Confirm deletion

---

## Publishing Changes

After creating or editing posts through the CMS, you need to push changes to GitHub:

### Option 1: Using Git Command Line

```bash
cd /Users/ashishganda/Development/Cosmos-Website
git status                    # See what changed
git add src/pages/blog/       # Stage blog changes
git commit -m "Update blog posts via CMS"
git push origin main
```

### Option 2: Using VS Code

1. Open VS Code
2. Go to Source Control panel (Ctrl+Shift+G)
3. Review changes
4. Type commit message
5. Click checkmark to commit
6. Click "Sync Changes" or "Push"

### Automatic Deployment

Once pushed to GitHub, Cloudflare Pages automatically:
- Detects the changes
- Builds the site
- Deploys to production
- Usually takes 2-5 minutes

Check deployment status at: https://dash.cloudflare.com/

---

## Tips & Best Practices

### Writing Content

- **Use Markdown**: The Body field supports Markdown formatting
  - `**bold text**` for bold
  - `*italic text*` for italic
  - `[link text](URL)` for links
  - `## Heading` for headings

- **Images**: Always upload images through the CMS
  - Hero Image: Main featured image (appears at top)
  - Content Image: Supporting visual in content
  - Images stored in `/public/images/blog/`

### Workflow

1. **Work locally first**: Test your posts at `http://localhost:4321/blog/your-post`
2. **Preview before publishing**: Click "Publish" → "Publish now" only when satisfied
3. **Commit regularly**: Push changes to GitHub frequently to avoid losing work
4. **Check production**: After deploying, verify at https://cosmoswebtech.com.au/blog/

### SEO Best Practices

- **Title**: Keep under 60 characters
- **Description**: Keep under 160 characters
- **Images**: Use descriptive filenames
- **Category**: Choose the most relevant one
- **Read Time**: Estimate accurately (250 words ≈ 1 minute)

---

## Troubleshooting

### CMS Won't Load

**Problem**: Page shows "Loading..." forever

**Solution**:
1. Check that `npm run cms` is running in a terminal
2. Check that `npm run dev` is running in another terminal
3. Refresh the page (Cmd+R on Mac, Ctrl+R on Windows)
4. Try hard refresh (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)

### Changes Not Saving

**Problem**: Clicking "Save" doesn't work

**Solution**:
1. Check browser console for errors (F12)
2. Ensure all required fields are filled
3. Check that the CMS backend (`npm run cms`) is still running
4. Restart both servers

### Can't See New Post on Website

**Problem**: Created post doesn't appear on blog page

**Solution**:
1. Check that you clicked "Publish" (not just "Save")
2. Refresh the dev server page
3. Check the filename in `src/pages/blog/` - it should exist
4. Verify the post has a valid `publishedAt` date

### Images Not Showing

**Problem**: Uploaded images don't display

**Solution**:
1. Check image path starts with `/images/blog/`
2. Verify image was uploaded to `public/images/blog/`
3. Use relative paths (not absolute URLs)
4. Check image filename has no spaces (use hyphens instead)

### Port Already in Use

**Problem**: "Port 8081 already in use"

**Solution**:
```bash
# Find process using port 8081
lsof -ti:8081

# Kill the process
kill -9 $(lsof -ti:8081)

# Start CMS again
npm run cms
```

---

## Multiple Websites

You have CMS set up on **4 websites**. Use the same process for each:

### Cosmos Web Tech (cosmoswebtech.com.au)
```bash
cd /Users/ashishganda/Development/Cosmos-Website
npm run cms    # Terminal 1
npm run dev    # Terminal 2
# Access: http://localhost:4321/admin
```

### eAwesome (eawesome.com.au)
```bash
cd /Users/ashishganda/Development/Awesome-Website
npm run cms    # Terminal 1
npm run dev    # Terminal 2
# Access: http://localhost:4321/admin
```

### CloudGeeks Insights (insights.cloudgeeks.com.au)
```bash
cd /Users/ashishganda/Development/cloudgeeks-insights
npm run cms    # Terminal 1
npm run dev    # Terminal 2
# Access: http://localhost:4321/admin
```

### Ash Ganda (ashganda.com)
```bash
cd /Users/ashishganda/Development/ashganda-nextjs
npm run cms    # Terminal 1
npm run dev    # Terminal 2
# Access: http://localhost:3000/admin
```

---

## Advanced: Production CMS Setup (Future)

If you want to enable editing directly from the production website (without running locally), you'll need to:

1. Set up GitHub OAuth (already configured in `public/admin/config.yml`)
2. Ensure environment variables are set in Cloudflare/Railway
3. Convert existing blog posts to pure YAML frontmatter format

**This is optional** - many professional developers prefer the local workflow for better control and testing.

---

## Summary

✅ **Start CMS**: `npm run cms`
✅ **Start Dev**: `npm run dev`
✅ **Access CMS**: `http://localhost:4321/admin`
✅ **Edit Posts**: Use the CMS interface
✅ **Publish**: Commit & push to GitHub
✅ **Deploy**: Automatic via Cloudflare Pages

---

## Support

For questions or issues:
- Check this guide first
- Review Decap CMS docs: https://decapcms.org/docs/
- Check deployment logs in Cloudflare dashboard

**Remember**: The local workflow is actually the preferred method used by many professional developers. It gives you full control, version history, and the ability to preview before deploying!
