import { defineConfig } from 'astro/config';
// Note: Sitemap integration temporarily removed due to compatibility issue with Astro 4.x
// TODO: Upgrade Astro or use manual sitemap generation
// import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://cosmoswebtech.com.au',
  output: 'static',
  // integrations: [sitemap()],
});
