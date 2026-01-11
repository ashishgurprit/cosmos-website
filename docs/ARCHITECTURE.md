# CosmosWebTech.com.au - System Architecture

## Overview

Cosmos Web Tech is a static website built with Astro 4.x, deployed on Cloudflare Pages. The site serves as a lead generation platform for web design and digital marketing services targeting Sydney businesses.

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND                               │
├─────────────────────────────────────────────────────────────┤
│  Framework:     Astro 4.x (Static Site Generator)           │
│  Styling:       CSS with Custom Properties (Design Tokens)  │
│  Fonts:         Google Fonts (Inter, Plus Jakarta Sans)     │
│  Icons:         Inline SVG                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      HOSTING                                │
├─────────────────────────────────────────────────────────────┤
│  Platform:      Cloudflare Pages                            │
│  CDN:           Cloudflare Edge Network                     │
│  Domain:        cosmoswebtech.com.au                        │
│  SSL:           Cloudflare Universal SSL                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  THIRD-PARTY SERVICES                       │
├─────────────────────────────────────────────────────────────┤
│  Analytics:     Google Analytics 4 (G-W9NFCBVPD6)           │
│  Marketing:     Mautic (mautic.cloudgeeks.com.au)           │
│  Live Chat:     Gist (App ID: 4ag9jnty)                     │
└─────────────────────────────────────────────────────────────┘
```

## Architecture Diagram

```
                    ┌──────────────────┐
                    │    User/Browser  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Cloudflare CDN  │
                    │  (Edge Cache)    │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
       ┌──────────┐   ┌──────────┐   ┌──────────┐
       │  HTML    │   │   CSS    │   │   JS     │
       │  Pages   │   │  Styles  │   │ Scripts  │
       └──────────┘   └──────────┘   └──────────┘

        External Services (async load)
              │
    ┌─────────┼─────────┬──────────────┐
    │         │         │              │
    ▼         ▼         ▼              ▼
┌──────┐  ┌──────┐  ┌──────┐     ┌──────────┐
│ GA4  │  │Mautic│  │ Gist │     │  Google  │
│      │  │      │  │      │     │  Fonts   │
└──────┘  └──────┘  └──────┘     └──────────┘
```

## Page Structure

```
/
├── index.astro                    # Homepage
├── about.astro                    # About page with team section
├── contact.astro                  # Contact form with Google Map
├── portfolio.astro                # Portfolio showcase
├── privacy.astro                  # Privacy policy
├── terms.astro                    # Terms of service
├── faq.astro                      # FAQ with schema markup
├── web-design-hills-district.astro  # Location landing page
├── web-design-parramatta.astro      # Location landing page
│
├── blog/
│   ├── index.astro                # Blog listing
│   └── web-design-trends-2025.astro # Blog article
│
├── demos/
│   ├── index.astro                # Demo showcase
│   ├── align-chiro.astro          # Chiropractor demo
│   ├── bella-hair.astro           # Hair salon demo
│   ├── hills-home-loans.astro     # Mortgage broker demo
│   ├── hills-legal.astro          # Law firm demo
│   ├── homekey-conveyancing.astro # Conveyancer demo
│   ├── mindful-psychology.astro   # Psychology demo
│   ├── outback-goods.astro        # E-commerce demo
│   ├── parramatta-medical.astro   # Medical centre demo
│   ├── peak-fitness.astro         # Gym demo
│   ├── prime-cuts.astro           # Butcher demo
│   ├── shield-insurance.astro     # Insurance demo
│   ├── skills-academy.astro       # Education demo
│   └── smile-dental.astro         # Dental demo
│
├── services/
│   ├── index.astro                # Services overview
│   ├── web-design.astro           # Web design service
│   ├── wordpress.astro            # WordPress service
│   ├── ecommerce.astro            # E-commerce service
│   ├── seo.astro                  # SEO service
│   ├── sem.astro                  # Google Ads service
│   ├── hosting.astro              # Hosting service
│   └── odoo.astro                 # Odoo ERP service
│
└── resources/
    ├── index.astro                # Resources hub
    ├── website-cost-guide.astro   # Cost guide
    ├── planning-checklist.astro   # Planning checklist
    ├── requirements-template.astro # Requirements template
    └── seo-checklist.astro        # SEO checklist
```

## Build Process

```
┌─────────────────┐
│  Source Files   │
│  (.astro, .css) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Astro Build    │
│  `npm run build`│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Static Output  │
│  /dist folder   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Wrangler Deploy │
│ to Cloudflare   │
└─────────────────┘
```

## Data Flow

### Form Submissions

```
User fills form
       │
       ▼
JavaScript captures form data
       │
       ▼
POST to Mautic endpoint
(https://mautic.cloudgeeks.com.au/form/submit?formId=39)
       │
       ▼
Mautic processes lead
       │
       ├──► Lead stored in Mautic CRM
       │
       └──► Email notification sent
```

### Analytics Tracking

```
Page Load
   │
   ▼
GA4 script loads (async)
   │
   ▼
gtag('config', 'G-W9NFCBVPD6')
   │
   ▼
Pageview sent to Google Analytics
   │
   ▼
User interactions tracked
```

## SEO Architecture

- **Meta tags**: Title, description, keywords per page
- **Open Graph**: og:title, og:description, og:image
- **Twitter Cards**: summary_large_image
- **Canonical URLs**: Self-referencing canonicals
- **Schema.org**: LocalBusiness, Service, FAQPage
- **Sitemap**: Auto-generated by Astro
- **Robots.txt**: Standard allow-all configuration
- **Geo meta tags**: geo.region, geo.placename, ICBM

## Security Measures

1. **HTTPS**: Enforced via Cloudflare
2. **CSP**: Content Security Policy headers
3. **Form CSRF**: Mautic handles token validation
4. **XSS Prevention**: Astro auto-escapes by default
5. **No Database**: Static site, no SQL injection risk

## Performance Optimizations

- Static HTML generation (no server-side rendering)
- Cloudflare CDN edge caching
- Lazy loading for images and iframes
- Critical CSS inlined
- Async loading for third-party scripts
- Google Fonts with display=swap
- Preconnect hints for external resources

## Key Features

### FAQ Page with Schema
- Accordion-style FAQ sections
- FAQPage schema for rich results
- Sticky category navigation
- 18 questions across 4 categories

### Team Section
- 4 team members with avatars
- LinkedIn profile links
- Roles and bios
- Responsive grid layout

### Demo Showcase
- 13 industry-specific demos
- Interactive previews
- Service area targeting
