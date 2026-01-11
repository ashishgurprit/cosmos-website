# Resource Forms Update Instructions

The following 4 resource pages need to be updated with Turnstile and proxy:

1. src/pages/resources/planning-checklist.astro
2. src/pages/resources/requirements-template.astro
3. src/pages/resources/seo-checklist.astro
4. src/pages/resources/website-cost-guide.astro

## Changes Needed for Each File:

### 1. Add Turnstile Widget to Form HTML
Find the form's submit button and add Turnstile widget BEFORE it:
```html
<!-- Cloudflare Turnstile Widget -->
<div class="cf-turnstile" data-sitekey="0x4AAAAAAAzsB5pP7TqT9oRx" data-theme="light"></div>
```

### 2. Update JavaScript Form Submission
Replace the old `no-cors` submission with the new Turnstile + proxy approach:

**OLD CODE (to replace):**
```javascript
await fetch(MAUTIC_FORM_URL, {
  method: 'POST',
  mode: 'no-cors',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams(data)
});
```

**NEW CODE:**
```javascript
// Get Turnstile token
const turnstileWidget = form.querySelector('.cf-turnstile');
const turnstileToken = turnstileWidget ? window.turnstile.getResponse(turnstileWidget) : null;

if (!turnstileToken) {
  alert('Please complete the spam verification.');
  // Reset button state
  return;
}

const submitData = {
  turnstileToken,
  formData: {
    formId: 'XX', // Use correct form ID for each resource
    'mauticform[email]': data['mauticform[email]'],
    'mauticform[name]': data['mauticform[name]'] || '',
    'mauticform[lead_source]': data['mauticform[lead_source]'],
  }
};

const response = await fetch('/api/submit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(submitData)
});

const result = await response.json();

if (result.success) {
  // Show success message
} else {
  alert(result.error || 'There was an error. Please try again.');
  if (turnstileWidget) window.turnstile.reset(turnstileWidget);
}
```

## Form IDs (from forms.ts):
- Planning Checklist: '41'
- Requirements Template: '42'
- SEO Checklist: '43'
- Cost Guide: '44'

Note: These are configured in `/src/config/forms.ts`
