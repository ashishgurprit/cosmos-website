# Decap CMS Setup for Cosmos Web Tech

## What is Decap CMS?

Decap CMS (formerly Netlify CMS) provides a user-friendly interface to edit blog posts directly in your browser at `cosmoswebtech.com.au/admin`.

## Local Development

To use the CMS locally:

1. **Start the Astro dev server:**
   ```bash
   npm run dev
   ```

2. **In a new terminal, start the CMS proxy server:**
   ```bash
   npm run cms
   ```

3. **Access the CMS:**
   Open `http://localhost:4321/admin` in your browser

4. **Edit blog posts:**
   - View all blog posts
   - Create new posts
   - Edit existing content
   - Upload images

## Production Setup (GitHub OAuth)

For production use at `cosmoswebtech.com.au/admin`, you need to set up GitHub OAuth:

### Step 1: Create GitHub OAuth App

1. Go to https://github.com/settings/developers
2. Click "New OAuth App"
3. Fill in:
   - **Application name:** Cosmos Web Tech CMS
   - **Homepage URL:** https://cosmoswebtech.com.au
   - **Authorization callback URL:** https://cosmoswebtech.com.au/api/auth/callback
4. Click "Register application"
5. Copy the **Client ID** and generate a **Client Secret**

### Step 2: Add OAuth Credentials to Cloudflare

You'll need to create an API endpoint for OAuth. This requires:

1. Creating a Cloudflare Worker or Pages Function for `/api/auth`
2. Adding your GitHub OAuth credentials as environment variables

**Alternative:** Use Netlify Identity or other auth providers supported by Decap CMS.

## File Structure

```
Cosmos-Website/
├── public/
│   └── admin/
│       ├── index.html          # CMS interface
│       └── config.yml          # CMS configuration
├── src/
│   └── pages/
│       └── blog/               # Blog posts edited by CMS
│           ├── post-1.astro
│           └── post-2.astro
└── package.json
```

## Creating New Blog Posts

When creating a new post through the CMS:

1. Click "New Blog Posts"
2. Fill in all fields:
   - Title
   - Description
   - Publish Date
   - Category
   - Hero Image (optional)
3. Write content in Markdown
4. Click "Publish"

**Note:** The CMS will create files in the correct Astro format with BlogLayout wrapper.

## Editing Existing Posts

1. Go to `/admin`
2. Click on any blog post
3. Make your changes
4. Click "Save" (draft) or "Publish"

## Troubleshooting

### CMS not loading locally
- Make sure both `npm run dev` and `npm run cms` are running
- Check that you're accessing `localhost:4321/admin` (not just `localhost:4321`)

### Changes not saving
- Ensure Git is configured correctly
- Check that you have write permissions to the repository

### Images not uploading
- Check the `public/images/blog` folder exists
- Verify media_folder path in config.yml

## Support

For issues with Decap CMS, see: https://decapcms.org/docs/
