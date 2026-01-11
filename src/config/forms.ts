// Centralized Mautic form configuration for Cosmos Web Tech
export const MAUTIC_URL = "https://mautic.cloudgeeks.com.au";

export const FORM_IDS = {
  CONTACT: '39',           // Main contact form
  FOOTER: '40',            // Footer newsletter/contact
  PLANNING: '41',          // Planning checklist download
  REQUIREMENTS: '42',      // Requirements template download
  SEO: '43',              // SEO checklist download
  COST_GUIDE: '44',       // Website cost guide download
} as const;

export const TURNSTILE_SITE_KEY = '0x4AAAAAACL6iirwP7c-dYYc'; // Turnstile site key for form spam protection

export interface FormSubmissionData {
  formId: string;
  [key: string]: string | number | boolean;
}
