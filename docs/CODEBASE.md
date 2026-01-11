# CosmosWebTech.com.au - Codebase Structure

## Directory Overview

```
Cosmos-Website/
├── docs/                          # Documentation
│   ├── ARCHITECTURE.md            # System architecture
│   ├── TECHNICAL.md               # Technical docs
│   └── CODEBASE.md               # This file
│
├── src/
│   ├── layouts/
│   │   └── Layout.astro           # Main layout wrapper
│   │
│   ├── pages/
│   │   ├── index.astro            # Homepage
│   │   ├── about.astro            # About page with team
│   │   ├── contact.astro          # Contact page with map
│   │   ├── portfolio.astro        # Portfolio showcase
│   │   ├── privacy.astro          # Privacy policy
│   │   ├── terms.astro            # Terms of service
│   │   ├── faq.astro              # FAQ with schema
│   │   ├── web-design-hills-district.astro
│   │   ├── web-design-parramatta.astro
│   │   │
│   │   ├── blog/
│   │   │   ├── index.astro
│   │   │   └── web-design-trends-2025-complete-guide.astro
│   │   │
│   │   ├── demos/
│   │   │   ├── index.astro
│   │   │   ├── align-chiro.astro
│   │   │   ├── bella-hair.astro
│   │   │   ├── hills-home-loans.astro
│   │   │   ├── hills-legal.astro
│   │   │   ├── homekey-conveyancing.astro
│   │   │   ├── mindful-psychology.astro
│   │   │   ├── outback-goods.astro
│   │   │   ├── parramatta-medical.astro
│   │   │   ├── peak-fitness.astro
│   │   │   ├── prime-cuts.astro
│   │   │   ├── shield-insurance.astro
│   │   │   ├── skills-academy.astro
│   │   │   └── smile-dental.astro
│   │   │
│   │   ├── services/
│   │   │   ├── index.astro
│   │   │   ├── web-design.astro
│   │   │   ├── wordpress.astro
│   │   │   ├── ecommerce.astro
│   │   │   ├── seo.astro
│   │   │   ├── sem.astro
│   │   │   ├── hosting.astro
│   │   │   └── odoo.astro
│   │   │
│   │   └── resources/
│   │       ├── index.astro
│   │       ├── website-cost-guide.astro
│   │       ├── planning-checklist.astro
│   │       ├── requirements-template.astro
│   │       └── seo-checklist.astro
│   │
│   └── styles/
│       └── global.css             # Global styles & design tokens
│
├── public/
│   ├── favicon.svg
│   ├── robots.txt
│   └── images/
│       └── [various images]
│
├── dist/                          # Build output (git-ignored)
├── node_modules/                  # Dependencies (git-ignored)
├── package.json
├── package-lock.json
└── astro.config.mjs
```

## Key Files Description

### `/src/layouts/Layout.astro`

Main layout wrapper that includes:
- HTML head with meta tags
- Google Analytics script (G-W9NFCBVPD6)
- Mautic tracking script
- Gist live chat widget
- LocalBusiness schema markup
- Announcement bar
- Footer contact form section
- Blog exit intent popup (conditional)
- Mobile menu functionality

**Props**:
```typescript
interface Props {
  title: string;
  description?: string;
}
```

**Key Variables**:
```javascript
const MAUTIC_URL = "https://mautic.cloudgeeks.com.au";
const MAUTIC_CONTACT_FORM_URL = "https://mautic.cloudgeeks.com.au/form/submit?formId=39";
const SITE_URL = "https://cosmoswebtech.com.au";
```

### `/src/styles/global.css`

Global stylesheet imported via `@import '../styles/global.css'` in Layout.astro.

**Key Sections**:
- CSS Reset and normalization
- Design tokens (colors, fonts, spacing)
- Typography styles
- Component styles (buttons, forms, cards)
- Header and navigation
- Footer styles
- Utility classes

### `/src/pages/index.astro`

Homepage with sections:
1. Hero with CTA buttons
2. Services overview (6 services)
3. Industries served
4. Demo showcase
5. Why choose us
6. Process steps
7. Testimonials
8. CTA section
9. Footer

### `/src/pages/about.astro`

About page featuring:
- Page hero section
- Company intro with stats
- Values section (4 values)
- **Team section** (4 team members)
- Services overview
- Why choose us
- CTA section
- Footer with social links

**Team Members**:
1. Ashish Ganda - Founder & Lead Developer
2. Sarah Chen - Senior Web Developer
3. Michael Torres - SEO & Marketing Lead
4. Emily Watson - UI/UX Designer

### `/src/pages/contact.astro`

Contact page featuring:
- Page hero section
- Two-column layout:
  - Left: Contact form (Mautic Form ID 39)
  - Right: Contact details + service areas + **Google Map**
- CTA card
- Footer with social links

### `/src/pages/faq.astro`

FAQ page featuring:
- Page hero section
- Sticky category sidebar
- Accordion FAQ sections (4 categories, 18 questions)
- FAQPage schema markup for SEO
- CTA section
- Footer with social links

**FAQ Categories**:
1. Getting Started (5 questions)
2. Web Design & Development (5 questions)
3. SEO & Marketing (4 questions)
4. Pricing & Process (4 questions)

### `/src/pages/privacy.astro` & `/src/pages/terms.astro`

Legal pages with:
- Consistent styling
- Content sections
- Contact information
- Social links in footer
- Legal links in footer

## Component Patterns

### Page Structure

```astro
---
import Layout from '../layouts/Layout.astro';
const title = "Page Title | Cosmos Web Tech Sydney";
const description = "Page description for SEO";
---

<Layout title={title} description={description}>
  <header class="header">...</header>
  <section class="page-hero">...</section>
  <section class="content-section">...</section>
  <footer class="footer">...</footer>
</Layout>

<style>
  /* Page-specific styles */
</style>

<script>
  /* Page-specific JavaScript */
</script>
```

### Footer with Social Links

```astro
<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <a href="/" class="logo footer-logo">...</a>
        <p class="footer-desc">Sydney's trusted web design agency.</p>
        <div class="social-links">
          <a href="https://linkedin.com/company/cosmoswebtech">LinkedIn</a>
          <a href="https://facebook.com/cosmoswebtech">Facebook</a>
        </div>
      </div>
      <div class="footer-links-col">Services...</div>
      <div class="footer-links-col">Company + FAQ...</div>
      <div class="footer-links-col">Legal + Contact...</div>
    </div>
    <div class="footer-bottom">
      <p>&copy; 2025 Ganda Tech Services. ABN: 32 164 690 751</p>
    </div>
  </div>
</footer>
```

### FAQ Accordion Pattern

```astro
<div class="faq-item">
  <button class="faq-question" aria-expanded="false">
    <span>Question text?</span>
    <svg class="faq-icon">...</svg>
  </button>
  <div class="faq-answer">
    <p>Answer text...</p>
  </div>
</div>

<script>
document.querySelectorAll('.faq-question').forEach(button => {
  button.addEventListener('click', () => {
    const item = button.parentElement;
    const isOpen = item.classList.contains('open');

    // Close all
    document.querySelectorAll('.faq-item.open').forEach(openItem => {
      openItem.classList.remove('open');
      openItem.querySelector('.faq-question').setAttribute('aria-expanded', 'false');
    });

    // Open clicked
    if (!isOpen) {
      item.classList.add('open');
      button.setAttribute('aria-expanded', 'true');
    }
  });
});
</script>
```

### Team Card Pattern

```astro
<div class="team-card">
  <div class="team-avatar">
    <span>AG</span>  <!-- Initials -->
  </div>
  <h3>Team Member Name</h3>
  <span class="team-role">Role Title</span>
  <p>Brief bio description...</p>
  <a href="https://linkedin.com/in/..." class="linkedin-link">
    <svg>...</svg>
    Connect on LinkedIn
  </a>
</div>
```

## CSS Class Naming

**Convention**: BEM-inspired, lowercase with hyphens

```css
/* Block */
.team-card { }

/* Block Element */
.team-card .team-avatar { }

/* Block Modifier */
.team-card.featured { }

/* Utility classes */
.btn { }
.btn-primary { }
.btn-large { }
```

## JavaScript Patterns

### Form Submission Handler

```javascript
async function submitContactForm(form, successEl, source) {
  const formData = new FormData(form);

  const data = {
    'mauticform[name]': formData.get('name') || '',
    'mauticform[email]': formData.get('email'),
    'mauticform[phone]': formData.get('phone') || '',
    'mauticform[service]': formData.get('service') || '',
    'mauticform[message]': formData.get('message') || '',
    'mauticform[lead_source]': source,
    'mauticform[formId]': '39'
  };

  try {
    await fetch(MAUTIC_CONTACT_FORM_URL, {
      method: 'POST',
      mode: 'no-cors',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams(data)
    });
  } catch (e) {}

  form.style.display = 'none';
  if (successEl) successEl.style.display = 'block';
}
```

### URL Parameter Pre-fill

```javascript
const urlParams = new URLSearchParams(window.location.search);
const service = urlParams.get('service');
if (service) {
  const serviceSelect = document.getElementById('service');
  if (serviceSelect) serviceSelect.value = service;
}
```

## Adding New Pages

1. Create new `.astro` file in `/src/pages/`
2. Import Layout component
3. Define title and description
4. Add header, hero, content sections
5. Include footer with:
   - Social links (LinkedIn, Facebook)
   - Legal links (Privacy, Terms)
   - Contact info
6. Add page-specific styles
7. Run `npm run build` to test
8. Deploy with `npx wrangler pages deploy dist`

## Environment Variables

No environment variables required - all configuration is static.

## Testing

Manual testing checklist:
- [ ] Page loads correctly
- [ ] Mobile responsive
- [ ] Forms submit successfully
- [ ] FAQ accordions work
- [ ] Links work correctly
- [ ] Images load properly
- [ ] Google Map displays
- [ ] Schema markup validates
- [ ] Meta tags present
- [ ] Social links work
