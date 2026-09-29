// NEXUS Backend URLs - Add more Render instances for load balancing
const RENDER_URLS = [
  "https://nexus-core-1qk0.onrender.com",
  // "https://nexus-core-2.onrender.com",  // Add when created
  // "https://nexus-core-3.onrender.com",  // Add when created
];

// Pick a random backend per session for load distribution
window.NEXUS_API_URL = RENDER_URLS[Math.floor(Math.random() * RENDER_URLS.length)];
window.NEXUS_FALLBACK_URLS = RENDER_URLS;
