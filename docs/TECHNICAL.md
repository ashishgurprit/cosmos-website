# CosmosWebTech.com.au - Technical Documentation

## Project Configuration

### Package.json Dependencies

```json
{
  "name": "cosmos-website",
  "type": "module",
  "version": "1.0.0",
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "astro preview"
  },
  "dependencies": {
    "astro": "^4.x"
  }
}
```

### Astro Configuration

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://cosmoswebtech.com.au',
  output: 'static'
});
```

## Third-Party Integrations

### 1. Mautic Marketing Automation

**Base URL**: `https://mautic.cloudgeeks.com.au`

**Form ID**: 39 (Contact Form)

**Tracking Script**:
```javascript
(function(w,d,t,u,n,a,m){
  w['MauticTrackingObject']=n;
  w[n]=w[n]||function(){(w[n].q=w[n].q||[]).push(arguments)};
  a=d.createElement(t);
  m=d.getElementsByTagName(t)[0];
  a.async=1;
  a.src=u;
  m.parentNode.insertBefore(a,m)
})(window,document,'script','https://mautic.cloudgeeks.com.au/mtc.js','mt');
mt('send', 'pageview');
```

**Form Submission**:
```javascript
const data = {
  'mauticform[name]': formData.get('name'),
  'mauticform[email]': formData.get('email'),
  'mauticform[phone]': formData.get('phone'),
  'mauticform[service]': formData.get('service'),
  'mauticform[message]': formData.get('message'),
  'mauticform[lead_source]': 'Website Contact Form',
  'mauticform[formId]': '39'
};

await fetch('https://mautic.cloudgeeks.com.au/form/submit?formId=39', {
  method: 'POST',
  mode: 'no-cors',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams(data)
});
```

### 2. Google Analytics 4

**Tracking ID**: `G-W9NFCBVPD6`

**Implementation**:
```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W9NFCBVPD6"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-W9NFCBVPD6');
</script>
```

### 3. Gist Live Chat

**App ID**: `4ag9jnty`

**Implementation**:
```javascript
(function(d,h,w){
  var gist=w.gist=w.gist||[];
  gist.methods=['trackPageView','identify','track','setAppId'];
  gist.factory=function(t){
    return function(){
      var e=Array.prototype.slice.call(arguments);
      e.unshift(t);
      gist.push(e);
      return gist;
    }
  };
  for(var i=0;i<gist.methods.length;i++){
    var c=gist.methods[i];
    gist[c]=gist.factory(c)
  }
  s=d.createElement('script');
  s.src="https://widget.getgist.com";
  s.async=!0;
  e=d.getElementsByTagName(h)[0];
  e.appendChild(s);
  gist.setAppId("4ag9jnty");
  gist.trackPageView()
})(document,'head',window);
```

## CSS Design System

### Color Variables

```css
:root {
  /* Primary Colors */
  --navy-dark: #1e3a5f;
  --navy: #2d4a6f;
  --accent: #3b82f6;

  /* Neutral Colors */
  --black: #1a1a2e;
  --grey-dark: #374151;
  --grey: #6b7280;
  --grey-300: #9ca3af;
  --grey-200: #e5e7eb;
  --grey-100: #f3f4f6;
  --white: #ffffff;

  /* Semantic Colors */
  --success: #22c55e;
  --warning: #f59e0b;
  --error: #ef4444;
}
```

### Typography

```css
:root {
  --font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-heading: 'Plus Jakarta Sans', var(--font-body);
}

h1 { font-size: 2.5rem; font-weight: 800; }
h2 { font-size: 2rem; font-weight: 700; }
h3 { font-size: 1.5rem; font-weight: 700; }
h4 { font-size: 1.25rem; font-weight: 600; }
```

### Responsive Breakpoints

```css
/* Mobile First */
@media (min-width: 768px) { /* Tablet */ }
@media (min-width: 1024px) { /* Desktop */ }
@media (min-width: 1280px) { /* Large Desktop */ }
```

## Schema.org Markup

### LocalBusiness Schema

```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Cosmos Web Tech",
  "description": "Professional web design, SEO and digital marketing services for Sydney businesses",
  "url": "https://cosmoswebtech.com.au",
  "telephone": "+61433309677",
  "email": "hello@cosmoswebtech.com.au",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "608/8 Elizabeth Macarthur Drive, Bella Vista",
    "addressLocality": "Sydney",
    "addressRegion": "NSW",
    "postalCode": "2153",
    "addressCountry": "AU"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": -33.7630,
    "longitude": 150.9927
  },
  "sameAs": [
    "https://linkedin.com/company/cosmoswebtech",
    "https://facebook.com/cosmoswebtech"
  ]
}
```

### FAQPage Schema

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "How much does a website cost?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Website costs vary based on complexity..."
      }
    }
  ]
}
```

## Deployment

### Cloudflare Pages

**Project Name**: `cosmos-website`
**Production URLs**:
- `https://cosmoswebtech.com.au`
- `https://cosmoswebtech.com`
**Preview URL**: `https://cosmos-website.pages.dev`

**Deploy Command**:
```bash
npm run build
npx wrangler pages deploy dist --project-name=cosmos-website
```

### Build Output

- **38 pages** generated
- **Build time**: ~1 second
- **Output directory**: `/dist`

## Key Components

### FAQ Page with Schema

```astro
---
const faqs = [
  {
    category: "Getting Started",
    questions: [
      { q: "Question?", a: "Answer" }
    ]
  }
];

const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": faqs.flatMap(category =>
    category.questions.map(q => ({
      "@type": "Question",
      "name": q.q,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": q.a.replace(/<[^>]*>/g, '')
      }
    }))
  )
};
---

<script type="application/ld+json" set:html={JSON.stringify(faqSchema)} />
```

### Team Section

```astro
<section class="team-section">
  <div class="container">
    <h2>Meet Our Team</h2>
    <div class="team-grid">
      {teamMembers.map(member => (
        <div class="team-card">
          <div class="team-avatar">
            <span>{member.initials}</span>
          </div>
          <h3>{member.name}</h3>
          <span class="team-role">{member.role}</span>
          <p>{member.bio}</p>
          <a href={member.linkedin} class="linkedin-link">
            Connect on LinkedIn
          </a>
        </div>
      ))}
    </div>
  </div>
</section>
```

### Google Map Embed

```html
<iframe
  src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3315.8!2d150.9577!3d-33.7364!..."
  width="100%"
  height="200"
  style="border:0; border-radius: 12px;"
  allowfullscreen=""
  loading="lazy"
  referrerpolicy="no-referrer-when-downgrade"
  title="Cosmos Web Tech Office Location">
</iframe>
```

## File Size Guidelines

- HTML pages: < 100KB each
- CSS bundle: < 50KB
- JavaScript: Minimal, mostly inline
- Images: WebP format, lazy loaded

## Browser Support

- Chrome (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Edge (last 2 versions)
- Mobile Safari (iOS 14+)
- Chrome Mobile (Android 10+)
