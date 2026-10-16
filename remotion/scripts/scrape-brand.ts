import fs from 'node:fs';
import path from 'node:path';
import {chromium} from 'playwright';
import type {BrandJson} from '../engine/types';

const OFFICIAL_YOUTUBE_SVG = `<svg viewBox="0 0 28.57 20" preserveAspectRatio="xMidYMid meet" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <g>
    <path d="M 27.9727 3.16 C 28.5 5.12 28.5 9.24 28.5 10 C 28.5 10.76 28.5 14.88 27.9727 16.84 C 27.6745 17.95 26.7961 18.83 25.6868 19.13 C 23.7273 19.66 14.285 19.66 14.285 19.66 C 14.285 19.66 4.8427 19.66 2.8832 19.13 C 1.7739 18.83 0.8955 17.95 0.5973 16.84 C 0.07 14.88 0.07 10.76 0.07 10 C 0.07 9.24 0.07 5.12 0.5973 3.16 C 0.8955 2.05 1.7739 1.17 2.8832 0.87 C 4.8427 0.34 14.285 0.34 14.285 0.34 C 14.285 0.34 23.7273 0.34 25.6868 0.87 C 26.7961 1.17 27.6745 2.05 27.9727 3.16 Z" fill="#FF0000"></path>
    <polygon points="11.425,14.285 18.855,10 11.425,5.715" fill="#FFFFFF"></polygon>
  </g>
</svg>`;

export async function scrapeBrand(targetUrl: string, jobId: string): Promise<BrandJson> {
  const jobDir = path.resolve(process.cwd(), 'jobs', jobId);
  const assetsDir = path.join(jobDir, 'assets');
  const publicAssetsDir = path.resolve(process.cwd(), 'public', 'jobs', jobId, 'assets');
  fs.mkdirSync(assetsDir, {recursive: true});
  fs.mkdirSync(publicAssetsDir, {recursive: true});

  console.log(`[Playwright Ingest] Starting browser crawl for ${targetUrl} (job: ${jobId})...`);

  let extractedTitle = '';
  let extractedDesc = '';
  let extractedThemeColor = '';
  let screenshotPath = path.join(assetsDir, 'studio-hero.png');

  let browser;
  try {
    const chromeCandidates = [
      'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
      'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
      'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    ];
    const systemBrowser = chromeCandidates.find(p => fs.existsSync(p));

    browser = await chromium.launch({
      headless: true,
      executablePath: systemBrowser,
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
    });

    const context = await browser.newContext({
      viewport: {width: 1920, height: 1080},
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    });

    const page = await context.newPage();

    // Navigate to target
    console.log(`[Playwright Ingest] Navigating to ${targetUrl}...`);
    try {
      await page.goto(targetUrl, {waitUntil: 'domcontentloaded', timeout: 20000});
      extractedTitle = await page.title();
      extractedDesc = (await page.$eval('meta[name="description"]', el => el.getAttribute('content')).catch(() => '')) || '';
      extractedThemeColor = (await page.$eval('meta[name="theme-color"]', el => el.getAttribute('content')).catch(() => '')) || '';
    } catch (navErr) {
      console.warn(`[Playwright Ingest] Navigation warning:`, navErr);
    }

    // Capture visual screenshot
    try {
      await page.screenshot({path: screenshotPath, fullPage: false});
      fs.copyFileSync(screenshotPath, path.join(publicAssetsDir, 'studio-hero.png'));
      console.log(`[Playwright Ingest] Captured authentic page screenshot to ${screenshotPath}`);
    } catch (ssErr) {
      console.warn(`[Playwright Ingest] Screenshot warning:`, ssErr);
    }

    await browser.close();
  } catch (err) {
    console.warn(`[Playwright Ingest] Browser process exception, utilizing standard fallback:`, err);
    if (browser) await browser.close().catch(() => {});
  }

  // ── Derive brand identity dynamically from scraped metadata ──────────────
  const parsedUrl = new URL(targetUrl.startsWith('http') ? targetUrl : `https://${targetUrl}`);
  const domain = parsedUrl.hostname.replace(/^www\./, '');
  // Infer a clean product name: strip TLD from domain first part
  const domainBase = domain.split('.')[0]; // e.g. "youtube" from "youtube.com"
  const inferredName =
    extractedTitle
      .replace(/[-–|·•].*$/, '') // strip tagline from title
      .replace(/\s+(App|Platform|Studio|Dashboard|Home)$/i, '')
      .trim() || domainBase.charAt(0).toUpperCase() + domainBase.slice(1);

  // Accent color: prefer scraped theme-color, else generate a stable hue from domain
  let accentColor = extractedThemeColor || '';
  if (!accentColor || accentColor === '#ffffff' || accentColor === '#000000') {
    // Stable hash of domain → hue
    let hash = 0;
    for (let c = 0; c < domain.length; c++) hash = domain.charCodeAt(c) + ((hash << 5) - hash);
    const hue = Math.abs(hash) % 360;
    accentColor = `hsl(${hue}, 68%, 55%)`;
  }

  // Derive dark background family from accent
  const isYouTube = domain.includes('youtube');
  const isInstagram = domain.includes('instagram');
  const isNetflix = domain.includes('netflix');

  // Per-known-domain color overrides (for major consumer brands with established identities)
  const knownColors: Record<string, {accent: string; accentLight: string; bg: string; bg2: string}> = {
    'youtube.com':   {accent: '#FF0000', accentLight: '#FF4E45', bg: '#0F0F0F', bg2: '#1F1F1F'},
    'instagram.com': {accent: '#E1306C', accentLight: '#F77737', bg: '#000000', bg2: '#121212'},
    'netflix.com':   {accent: '#E50914', accentLight: '#FF3D2E', bg: '#141414', bg2: '#1F1F1F'},
    'spotify.com':   {accent: '#1DB954', accentLight: '#1ed760', bg: '#121212', bg2: '#181818'},
    'github.com':    {accent: '#F78166', accentLight: '#FFA198', bg: '#0D1117', bg2: '#161B22'},
    'vercel.com':    {accent: '#FFFFFF', accentLight: '#E5E5E5', bg: '#000000', bg2: '#111111'},
    'linear.app':    {accent: '#5E6AD2', accentLight: '#8B94E5', bg: '#08090C', bg2: '#12141A'},
    'notion.so':     {accent: '#FFFFFF', accentLight: '#E3E3E3', bg: '#191919', bg2: '#252525'},
    'figma.com':     {accent: '#F24E1E', accentLight: '#FF7262', bg: '#1E1E1E', bg2: '#2C2C2C'},
    'swiggy.com':    {accent: '#FC8019', accentLight: '#FFAB4B', bg: '#0D0D0D', bg2: '#1A1A1A'},
    'zomato.com':    {accent: '#E23744', accentLight: '#FF6B77', bg: '#1C1C1C', bg2: '#2B2B2B'},
  };

  const colorKit = knownColors[domain] ?? {
    accent: accentColor,
    accentLight: accentColor,
    bg: '#09090B',
    bg2: '#18181B',
  };

  // Logo: use the real YouTube SVG for YouTube, else a generic text SVG
  const logoSvgContent = isYouTube
    ? OFFICIAL_YOUTUBE_SVG
    : `<svg viewBox="0 0 200 60" xmlns="http://www.w3.org/2000/svg">
        <rect width="200" height="60" rx="8" fill="${colorKit.accent}22"/>
        <text x="100" y="40" font-family="system-ui,sans-serif" font-size="28" font-weight="800"
              text-anchor="middle" fill="${colorKit.accent}">${inferredName}</text>
      </svg>`;

  const logoSvgPath = path.join(assetsDir, 'logo.svg');
  const publicLogoSvgPath = path.join(publicAssetsDir, 'logo.svg');
  fs.writeFileSync(logoSvgPath, logoSvgContent, 'utf8');
  fs.writeFileSync(publicLogoSvgPath, logoSvgContent, 'utf8');
  fs.writeFileSync(path.join(assetsDir, 'logo.png'), logoSvgContent, 'utf8');
  fs.writeFileSync(path.join(publicAssetsDir, 'logo.png'), logoSvgContent, 'utf8');

  const brand: BrandJson = {
    name: inferredName,
    domain,
    tagline: extractedDesc.split('.')[0].trim() || `${inferredName} — built for what's next.`,
    description: extractedDesc || `${inferredName} is a modern product trusted by millions.`,
    products: [inferredName],
    logo: {
      src: `jobs/${jobId}/assets/logo.svg`,
      text: inferredName,
      alt: `${inferredName} Logo`,
      source: targetUrl,
    },
    colors: {
      accent:      colorKit.accent,
      accentLight: colorKit.accentLight,
      background:  colorKit.bg,
      background2: colorKit.bg2,
      text:        '#F9FAFB',
      muted:       '#9CA3AF',
      surface:     colorKit.bg2,
      surfaceText: '#FFFFFF',
      surfaceMuted:'#6B7280',
    },
    fonts: {
      display: {family: 'Inter, system-ui, sans-serif', source: 'Google Fonts'},
      body:    {family: 'Inter, system-ui, sans-serif', source: 'Google Fonts'},
    },
    imagery: fs.existsSync(screenshotPath)
      ? [{src: `jobs/${jobId}/assets/studio-hero.png`, alt: `${inferredName} product screenshot`, source: targetUrl}]
      : [],
    claims: [
      {id: 'product', label: inferredName, value: 'See it in action', sourceUrl: targetUrl},
    ],
  };

  const brandOutPath = path.join(jobDir, 'brand.json');
  fs.writeFileSync(brandOutPath, JSON.stringify(brand, null, 2), 'utf8');
  console.log(`[Playwright Ingest] ✅ brand.json → ${inferredName} (${domain}) accent=${colorKit.accent}`);

  return brand;
}

if (process.argv[1]?.includes('scrape-brand')) {
  const target = process.argv[2] || 'https://www.youtube.com';
  const jobId = process.argv[3] || 'promo-youtube-saas';
  scrapeBrand(target, jobId)
    .then(() => process.exit(0))
    .catch(err => {
      console.error(err);
      process.exit(1);
    });
}
