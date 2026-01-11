/**
 * Cloudflare Pages Function to proxy Mautic form submissions for Cosmos Web Tech
 * This function:
 * 1. Validates Turnstile token to prevent spam
 * 2. Forwards form data to Mautic
 * 3. Returns actual success/error status to frontend
 * 4. Eliminates the no-cors blind spot
 */

interface Env {
  TURNSTILE_SECRET_KEY: string;
}

const MAUTIC_URL = "https://mautic.cloudgeeks.com.au";

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  // Parse JSON body
  let body: any;
  try {
    body = await request.json();
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: 'Invalid request body'
    }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  const { turnstileToken, formData } = body;

  // Validate Turnstile token
  if (!turnstileToken) {
    return new Response(JSON.stringify({
      success: false,
      error: 'Missing spam protection token'
    }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  try {
    // Verify Turnstile token with Cloudflare
    const turnstileResponse = await fetch(
      'https://challenges.cloudflare.com/turnstile/v0/siteverify',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          secret: env.TURNSTILE_SECRET_KEY,
          response: turnstileToken,
        }),
      }
    );

    const turnstileResult = await turnstileResponse.json();

    if (!turnstileResult.success) {
      return new Response(JSON.stringify({
        success: false,
        error: 'Spam protection verification failed. Please try again.'
      }), {
        status: 403,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Forward to Mautic
    const formId = formData.formId || '39';
    const mauticFormData = new FormData();

    // Convert formData object to FormData format expected by Mautic
    Object.keys(formData).forEach(key => {
      if (key !== 'formId') {
        mauticFormData.append(key, formData[key]);
      }
    });

    const mauticResponse = await fetch(
      `${MAUTIC_URL}/form/submit?formId=${formId}`,
      {
        method: 'POST',
        body: mauticFormData,
      }
    );

    // Check if Mautic accepted the submission
    if (!mauticResponse.ok) {
      // Log the error for debugging
      console.error('Mautic error:', mauticResponse.status, await mauticResponse.text());

      return new Response(JSON.stringify({
        success: false,
        error: 'There was an error submitting your form. Please try again or contact us directly.'
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Parse Mautic response to check for validation errors
    const mauticResult = await mauticResponse.text();

    // Mautic returns HTML by default, but we can check for error indicators
    if (mauticResult.includes('error') || mauticResult.includes('invalid')) {
      return new Response(JSON.stringify({
        success: false,
        error: 'Form validation failed. Please check your information and try again.'
      }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Success!
    return new Response(JSON.stringify({
      success: true,
      message: 'Thank you! We will get back to you within 24 hours.'
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('Form submission error:', error);

    return new Response(JSON.stringify({
      success: false,
      error: 'An unexpected error occurred. Please try again later.'
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
};
