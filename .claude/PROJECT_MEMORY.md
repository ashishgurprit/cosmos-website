---
project: Cosmos Web Tech Website
initialized: 2026-01-05
last_post_mortem: 2026-01-14T12:54:17Z
post_mortem_count: 2
---

# Project Memory: Cosmos Web Tech Website

> Persistent memory for Claude across sessions.
> **Security**: Only variable NAMES stored, never values.

## Post-Mortem History

| Date | Lesson | Files Changed |
|------|--------|---------------|
| 2026-01-14 | Decap CMS requires YAML frontmatter, not JavaScript exports | 1 |
| 2026-01-14 | Astro scoped styles don't apply to slotted content without :global() | 5 |

## Scripts Created

| Script | Purpose | Location |
|--------|---------|----------|
| `convert-to-content-collections.py` | Convert Astro pages to MDX content collections | Root |
| `fix-mdx-html.py` | Fix HTML structure issues in MDX files | Root |
| `fix-mdx-comprehensive.py` | Comprehensive HTML cleaning for MDX | Root |
| `remove-spacing-br-tags.py` | Remove unnecessary `<br>` tags used for CSS spacing | Root |
| `add-breaks-to-headings.py` | Add `<br>` tags after headings for spacing | Root |
| `fix-strong-breaks.py` | Add `<br>` after strong tags before lists | Root |

## Environment Variables

| Name | Purpose |
|------|---------|
| GITHUB_CLIENT_ID | OAuth client ID for Decap CMS |
| GITHUB_CLIENT_SECRET | OAuth client secret for Decap CMS |

## Infrastructure

| Component | Technology | Notes |
|-----------|------------|-------|
| Hosting | Cloudflare Pages | Main deployment platform |
| CMS | Decap CMS | Local workflow implemented |
| OAuth | GitHub OAuth App | For production CMS (optional) |
| Functions | Cloudflare Pages Functions | `/functions/api/auth.ts` for OAuth |

## Activity Log

| Date | Activity | Files |
|------|----------|-------|
| 2026-01-14 | Implemented Decap CMS for 4 websites | 12 |
| 2026-01-14 | Fixed CMS configuration issues (YAML formatting, repo URLs) | 8 |
| 2026-01-14 | Post-mortem: CMS frontmatter compatibility | 2 |
| 2026-01-14 | Fixed blog styling: Unified CSS spacing across 3 websites | 60 |
| 2026-01-14 | Post-mortem: Astro scoped styles and :global() requirement | 2 |

## Key Decisions

### Decap CMS Local Workflow (2026-01-14)
**Decision**: Use local CMS editing workflow instead of production CMS
**Rationale**:
- Existing blog posts use JavaScript frontmatter (incompatible with CMS)
- Converting to MDX revealed HTML structure issues requiring manual cleanup
- Local workflow is industry standard and provides better control
**Trade-offs**:
- Cannot edit directly from production website
- Requires local development environment
- But: Better testing, version control, professional workflow

## Known Issues

### Blog Structure Not CMS-Compatible
**Issue**: 27 blog posts use `export const frontmatter = {}` format
**Impact**: Production CMS cannot parse or edit these posts
**Workaround**: Local CMS workflow works perfectly
**Future**: Consider migrating to Content Collections if production editing becomes requirement

## Documentation

| Document | Purpose |
|----------|---------|
| `CMS-INSTRUCTIONS.md` | Complete guide to using local CMS workflow |
| `.claude/LESSONS-PROJECT.md` | Project-specific lessons learned |

## Multi-Site Setup

This project is part of a portfolio of 4 websites with Decap CMS:

1. **cosmoswebtech.com.au** - Main site (this repo)
2. **eawesome.com.au** - Mobile app development
3. **insights.cloudgeeks.com.au** - Cloud/AI blog
4. **ashganda.com** - Personal site (Next.js on Railway)

All use same CMS configuration pattern with local editing workflow.
