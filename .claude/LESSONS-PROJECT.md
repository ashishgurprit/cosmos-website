# Project Lessons Learned

Lessons specific to this project. General lessons go to the master repository.

---

### LESSON: Decap CMS Requires YAML Frontmatter, Not JavaScript Exports
**Date**: 2026-01-14
**Category**: CMS Integration & Content Management

**Symptom**:
- Decap CMS interface loaded successfully with GitHub OAuth authentication
- Blog posts appeared as white/empty boxes with no titles visible
- Console showed YAML syntax errors
- CMS could not parse or display existing blog posts

**Root Cause**:
Astro blog posts were using **JavaScript frontmatter format** (`export const frontmatter = {...}`) which is valid Astro code but incompatible with Decap CMS. Decap CMS is a Git-based CMS that directly reads and writes Markdown/MDX files with YAML frontmatter. It cannot parse or execute JavaScript code.

**Technical Details**:
```astro
<!-- INCOMPATIBLE: JavaScript frontmatter (Astro component format) -->
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
<!-- COMPATIBLE: YAML frontmatter (Content Collections / MDX format) -->
---
title: "My Blog Post"
description: "Post description"
publishedAt: "2024-01-14"
---

Content here
```

**Attempted Solution**:
Tried converting 27 blog posts from Astro component format to Astro Content Collections with MDX format. Conversion revealed additional issues:
- Existing HTML content had structural problems (unclosed tags, invalid nesting)
- MDX parser rejected malformed HTML structures
- Would require manual cleanup of all 27 posts

**Final Solution**:
Implemented **local CMS workflow** instead of production CMS:
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

**Prevention**:
- [ ] Before implementing any CMS, verify content format compatibility
- [ ] Check CMS documentation for supported frontmatter formats
- [ ] Consider content structure early in project planning
- [ ] Default to YAML frontmatter for CMS-managed content
- [ ] Test CMS integration with sample posts before committing

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

**Related Files**:
- `/public/admin/config.yml` - Decap CMS configuration
- `/public/admin/index.html` - CMS entry point
- `/functions/api/auth.ts` - OAuth handler (for production, not needed for local)
- `CMS-INSTRUCTIONS.md` - Complete workflow documentation

**Documentation Created**:
- Comprehensive `CMS-INSTRUCTIONS.md` with:
  - Quick start guide
  - Troubleshooting section
  - Multi-website setup instructions
  - Publishing workflow

**Impact**:
- No production impact (new feature implementation)
- Development time: ~3 hours of debugging
- 4 websites now have local CMS capability
- Future blog posts can use CMS interface

**Alternative Considered**:
Migrating to Astro Content Collections would enable production CMS but requires:
1. Converting all 27 existing posts to MDX
2. Cleaning up HTML structure in each post
3. Updating BlogLayout to work with Content Collections
4. Testing all posts individually

**Recommendation**: Stick with local workflow unless production editing is critical requirement.

---

### LESSON: Astro Scoped Styles Don't Apply to Slotted Content Without :global()
**Date**: 2026-01-14
**Category**: Frontend & Styling

**Symptom**:
- Blog post list items were flush left instead of properly indented
- Section headers (strong tags) had no spacing before lists
- Headings and paragraphs had inconsistent margins
- CSS rules appeared correct in source files but weren't being applied
- Initial fix for mobile worked but desktop remained broken

**Root Cause**:
Astro's scoped styling system adds `data-astro-cid` attributes to elements for style isolation. However, content rendered through `<slot />` doesn't receive these attributes. CSS selectors like `.post-content[data-astro-cid-4dqtj3le] strong[data-astro-cid-4dqtj3le]` only match if BOTH the parent AND child have the attribute, causing styles to never apply to slotted blog content.

**Contributing Factors**:
1. Global CSS file (src/styles/global.css) had conflicting `.blog-content` rules (193 lines)
2. Global CSS used wrong property (`margin-left` instead of `padding-left`) for list indentation
3. Global CSS set `display: block` on ALL strong tags, breaking inline formatting
4. Multiple CSS files competing for specificity
5. Browser caching made it appear that fixes weren't working

**Technical Details**:

Astro generates scoped CSS that looks like this:
```css
.post-content[data-astro-cid-4dqtj3le] strong[data-astro-cid-4dqtj3le] {
  font-weight: 600;
}
```

But slotted HTML doesn't have the attribute:
```html
<div class="post-content" data-astro-cid-4dqtj3le>
  <strong>Section Header</strong>  <!-- No data-astro-cid attribute! -->
  <ul>  <!-- No data-astro-cid attribute! -->
    <li>Item</li>
  </ul>
</div>
```

**Solution**:

1. **Remove conflicting global CSS** (193 lines deleted from src/styles/global.css):
```css
/* REMOVED ALL OF THIS from global.css */
.blog-content h1 { ... }
.blog-content h2 { ... }
.blog-content strong { display: block; ... }  /* This broke inline strong */
.blog-content ul, .blog-content ol { margin-left: 1.5rem; ... }  /* Wrong property */
```

2. **Use :global() in BlogLayout.astro** for all child selectors:
```astro
<style>
  .post-content {
    max-width: 800px;
    margin: 0 auto;
  }

  /* :global() allows styles to apply without data-astro-cid attributes */
  .post-content :global(h1) {
    font-size: 1.625rem;
    margin: 0 0 1.5rem 0;
    color: var(--navy-dark);
    line-height: 1.4;
    font-weight: 700;
  }

  .post-content :global(ul),
  .post-content :global(ol) {
    margin: 1.25rem 0;
    padding-left: 2rem;  /* CORRECT: padding-left, not margin-left */
    list-style-position: outside;  /* REQUIRED for proper indentation */
  }

  .post-content :global(strong) {
    font-weight: 600;
    color: var(--navy-dark);
    /* NO display: block here - only on section labels */
  }

  /* Target only standalone strong tags as section labels */
  .post-content :global(> strong) {
    display: block;
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
  }
</style>
```

**Debugging Process**:
1. Checked source CSS files - looked correct
2. Checked browser DevTools - CSS rules not being applied
3. Inspected HTML - elements missing data-astro-cid attributes
4. Checked built CSS file in `dist/_astro/*.css` - saw scoped selectors with attributes
5. Discovered `:global()` wrapper needed for slotted content
6. Found conflicting global CSS rules
7. Removed all conflicts and rebuilt

**Prevention**:
- [ ] Always use `:global()` for styling slotted content in Astro components
- [ ] Avoid global CSS rules that target common elements (strong, ul, p, h1-h6)
- [ ] Test both desktop AND mobile styling before considering issues fixed
- [ ] Use browser DevTools to verify which CSS rules are actually being applied
- [ ] Check built output (dist/) when debugging CSS issues
- [ ] Use hard refresh (Ctrl+Shift+R) or incognito mode to bypass cache
- [ ] Document Astro scoping behavior in team knowledge base

**Pattern to Follow**:
```astro
<!-- Component with slotted content -->
<div class="wrapper">
  <slot />
</div>

<style>
  .wrapper {
    /* Styles for wrapper itself - no :global() needed */
    max-width: 800px;
    margin: 0 auto;
  }

  .wrapper :global(h1) {
    /* Styles for slotted h1 - needs :global() */
    font-size: 2rem;
  }

  .wrapper :global(ul) {
    /* Styles for slotted lists - needs :global() */
    padding-left: 2rem;
    list-style-position: outside;
  }
</style>
```

**Pattern to Avoid**:
```astro
<!-- DON'T: Scoped selectors won't match slotted content -->
<style>
  .wrapper h1 {
    /* ❌ This won't work for slotted h1 elements */
    /* Generates: .wrapper[data-astro-cid-xxx] h1[data-astro-cid-xxx] */
    /* But slotted h1 doesn't have the attribute */
  }
</style>
```

**CSS List Indentation Best Practices**:
```css
/* ✅ CORRECT */
ul, ol {
  padding-left: 2rem;           /* Use padding-left, not margin-left */
  list-style-position: outside;  /* Required for proper bullet placement */
}

/* ❌ WRONG */
ul, ol {
  margin-left: 2rem;            /* Wrong property */
  /* Missing list-style-position causes bullets to appear flush left */
}
```

**Impact**:
- **Time to debug**: ~4 hours across multiple attempts
- **Files changed**: 5 files (global.css, BlogLayout.astro × 3 projects)
- **Lines removed**: 193 lines of conflicting CSS
- **Lines added**: ~130 lines with :global() wrappers
- **Severity**: P3 (Cosmetic issue, no functional impact)
- **User impact**: Blog posts had poor readability, unprofessional appearance
- **Sites affected**: cosmos-website, Awesome-Website, cloudgeeks-insights

**What Went Well**:
- Systematic debugging process uncovered root cause
- Fixed consistently across all three websites
- Implemented unified spacing standard
- Comprehensive documentation of the issue

**What Went Poorly**:
- Initial diagnosis was surface-level (mobile CSS only)
- Assumed the issue was simpler than it was
- Did not check built output until late in debugging
- Multiple deployment cycles before finding root cause

**Related Issues Fixed**:
1. List indentation (bullets flush left)
2. Section header spacing (strong tags before lists)
3. Heading margins inconsistency
4. Mobile vs desktop styling differences
5. Strong tags breaking inline formatting

**Files Modified**:
- `src/styles/global.css` - Removed 193 lines of conflicting rules
- `src/layouts/BlogLayout.astro` - Added :global() wrappers to all child selectors
- Applied same fix to Awesome-Website and cloudgeeks-insights

**Deployment Method**:
cosmos-website requires Wrangler deployment:
```bash
npm run build
npx wrangler pages deploy dist --project-name cosmos-website --commit-dirty=true
```

Other sites auto-deploy via Cloudflare Pages on git push.
