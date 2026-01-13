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
