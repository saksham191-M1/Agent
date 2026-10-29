import fs from 'node:fs';
import path from 'node:path';
import https from 'node:https';
import http from 'node:http';
import {chromium} from 'playwright';
import type {BrandJson} from '../engine/types';
import {getCachedBrand, saveBrandToCache} from './brand-cache';

// ──────────────────────────────────────────────────────────────────────────────
// Load environment variables (.env parser without external dependencies)
// ──────────────────────────────────────────────────────────────────────────────

function loadEnvFile(): void {
  const envPaths = [
    path.resolve(process.cwd(), '.env'),
    path.resolve(process.cwd(), '..', '.env'),
  ];
  for (const envPath of envPaths) {
    if (fs.existsSync(envPath)) {
      try {
        const content = fs.readFileSync(envPath, 'utf8');
        for (const line of content.split('\n')) {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith('#')) continue;
          const eqIdx = trimmed.indexOf('=');
          if (eqIdx > 0) {
            const key = trimmed.slice(0, eqIdx).trim();
            const val = trimmed.slice(eqIdx + 1).trim().replace(/^["']|["']$/g, '');
            if (!process.env[key]) {
              process.env[key] = val;
            }
          }
        }
      } catch (_err) {
        void _err;
      }
    }
  }
}
loadEnvFile();

// ──────────────────────────────────────────────────────────────────────────────
// UI Description schema & types
// ──────────────────────────────────────────────────────────────────────────────

export interface UIDescription {
  header: {
    bg: string;
    navLinks: string[];
  };
  searchBar: {
    placeholder: string;
    bg: string;
  };
  card_style: {
    bg: string;
    radius: number;
    shadow: string;
  };
  price_style: {
    color: string;
    discountColor: string;
    originalColor: string;
  };
  price_info?: {
    current?: string | null;
    original?: string | null;
    discount_pct?: string | null;
  } | null;
  rating?: {
    value?: number | null;
    count_text?: string | null;
  } | null;
  trust_badges: string[];
  layout_type: 'ecommerce_grid' | 'feed' | 'dashboard' | 'landing' | 'generic';
  brand_distinguishers: string[];
  cta_buttons: Array<{text: string; bg: string; color: string}>;
  _source: 'vision' | 'dom' | 'fallback';
}

interface DOMHints {
  navLinks: string[];
  searchPlaceholder: string;
  headerBg: string;
  ctaButtons: Array<{text: string; bg: string; color: string}>;
  prices: Array<{text: string; color: string}>;
  badges: Array<{text: string; bg: string; color: string}>;
}

// ──────────────────────────────────────────────────────────────────────────────
// Vision analysis via CodeCraft / OpenAI compatible Vision API
// ──────────────────────────────────────────────────────────────────────────────

async function analyzeWithVision(
  screenshotPath: string,
  domHints: DOMHints,
  brandName: string,
  jobDir: string,
): Promise<UIDescription | null> {
  const apiKey = process.env.CODECRAFT_API_KEY;
  const baseUrl = (process.env.CODECRAFT_BASE_URL || 'https://codecraftapi.com/v1').replace(/\/+$/, '');
  const model = process.env.CODECRAFT_MODEL || 'claude-opus-5.5';

  if (!apiKey || !fs.existsSync(screenshotPath)) {
    return null;
  }

  let imageBase64: string;
  try {
    const imgBuffer = fs.readFileSync(screenshotPath);
    imageBase64 = imgBuffer.toString('base64');
  } catch {
    return null;
  }

  const promptText = `You are a precision UI analysis engine. Given this mobile screenshot and DOM hints for "${brandName}", extract an accurate structural UI description.

DOM hints observed from page:
- Navigation Links: ${JSON.stringify(domHints.navLinks)}
- Search Placeholder: ${JSON.stringify(domHints.searchPlaceholder)}
- CTA Buttons: ${JSON.stringify(domHints.ctaButtons)}
- Price Patterns: ${JSON.stringify(domHints.prices)}
- Trust / Offer Badges: ${JSON.stringify(domHints.badges)}
- Header Background: ${JSON.stringify(domHints.headerBg)}

Return ONLY valid JSON matching this exact structure (no markdown, no backticks, no explanatory text):
{
  "header": {
    "bg": "<exact hex color of the top bar/header, e.g. #2874F0>",
    "navLinks": ["<up to 6 real nav tab or category labels visible>"]
  },
  "searchBar": {
    "placeholder": "<exact search placeholder string>",
    "bg": "<search input background hex color>"
  },
  "card_style": {
    "bg": "<product card or content card background hex>",
    "radius": <border radius in px as a number>,
    "shadow": "<box-shadow string or 'none'>"
  },
  "price_style": {
    "color": "<price text hex color>",
    "discountColor": "<discount percentage or deal text hex color, e.g. #388E3C>",
    "originalColor": "<strikethrough original price hex color>"
  },
  "trust_badges": ["<up to 4 badge texts e.g. 'Flipkart Assured', 'Free Delivery', 'Best Seller'>"],
  "layout_type": "<one of: ecommerce_grid | feed | dashboard | landing | generic>",
  "brand_distinguishers": ["<up to 4 unique brand perks/sections e.g. 'SuperCoins', 'Minutes', 'Plus'>"],
  "cta_buttons": [{"text": "<label>", "bg": "<hex>", "color": "<hex>"}]
}`;

  const payload = JSON.stringify({
    model,
    messages: [
      {
        role: 'user',
        content: [
          {
            type: 'text',
            text: promptText,
          },
          {
            type: 'image_url',
            image_url: {
              url: `data:image/png;base64,${imageBase64}`,
            },
          },
        ],
      },
    ],
    temperature: 0.2,
    max_tokens: 1000,
  });

  try {
    console.log(`[Brand Ingest] 🔍 Running Vision UI Analysis with ${model}...`);
    const endpointUrl = new URL(`${baseUrl}/chat/completions`);
    const isHttps = endpointUrl.protocol === 'https:';
    const client = isHttps ? https : http;

    const resBody = await new Promise<string>((resolve, reject) => {
      const req = client.request(
        {
          hostname: endpointUrl.hostname,
          port: endpointUrl.port || (isHttps ? 443 : 80),
          path: `${endpointUrl.pathname}${endpointUrl.search}`,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${apiKey}`,
            'Content-Length': Buffer.byteLength(payload),
          },
        },
        res => {
          let data = '';
          res.on('data', chunk => (data += chunk));
          res.on('end', () => resolve(data));
        },
      );
      req.on('error', reject);
      req.write(payload);
      req.end();
    });

    const parsed = JSON.parse(resBody);
    const content = parsed.choices?.[0]?.message?.content || '';
    if (!content) throw new Error('Empty vision response');

    const cleanJson = content.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '').trim();
    const result = JSON.parse(cleanJson);

    const uiDesc: UIDescription = {
      header: {
        bg: result.header?.bg || domHints.headerBg || '#111827',
        navLinks: Array.isArray(result.header?.navLinks) && result.header.navLinks.length > 0
          ? result.header.navLinks
          : domHints.navLinks.slice(0, 5),
      },
      searchBar: {
        placeholder: result.searchBar?.placeholder || domHints.searchPlaceholder || `Search ${brandName}...`,
        bg: result.searchBar?.bg || '#FFFFFF',
      },
      card_style: {
        bg: result.card_style?.bg || '#FFFFFF',
        radius: Number(result.card_style?.radius) || 8,
        shadow: result.card_style?.shadow || '0 2px 8px rgba(0,0,0,0.08)',
      },
      price_style: {
        color: result.price_style?.color || '#111827',
        discountColor: result.price_style?.discountColor || '#16A34A',
        originalColor: result.price_style?.originalColor || '#9CA3AF',
      },
      price_info: result.price_info || (domHints.prices.length > 0 ? {
        current: domHints.prices[0]?.text || null,
        original: domHints.prices[1]?.text || null,
        discount_pct: null,
      } : null),
      rating: result.rating || null,
      trust_badges: Array.isArray(result.trust_badges) ? result.trust_badges : [],
      layout_type: result.layout_type || 'generic',
      brand_distinguishers: Array.isArray(result.brand_distinguishers) ? result.brand_distinguishers : [],
      cta_buttons: Array.isArray(result.cta_buttons) ? result.cta_buttons : domHints.ctaButtons,
      _source: 'vision',
    };

    fs.writeFileSync(path.join(jobDir, 'ui_description_raw.json'), JSON.stringify(result, null, 2), 'utf8');
    console.log(`[Brand Ingest] ✨ Vision analysis identified layout: ${uiDesc.layout_type} with ${uiDesc.header.navLinks.length} nav links`);
    return uiDesc;
  } catch (err) {
    console.warn(`[Brand Ingest] Vision analysis unavailable (${(err as Error).message}), fallback to DOM hints.`);
    return null;
  }
}

function buildFallbackUIDescription(
  domHints: DOMHints,
  brandName: string,
  accentColor: string,
  isDark: boolean,
): UIDescription {
  return {
    header: {
      bg: domHints.headerBg || accentColor,
      navLinks: domHints.navLinks.length > 0 ? domHints.navLinks : ['Home', 'Categories', 'Orders', 'Account'],
    },
    searchBar: {
      placeholder: domHints.searchPlaceholder || `Search ${brandName}...`,
      bg: isDark ? '#1F2937' : '#FFFFFF',
    },
    card_style: {
      bg: isDark ? '#1F2937' : '#FFFFFF',
      radius: 8,
      shadow: '0 2px 8px rgba(0,0,0,0.08)',
    },
    price_style: {
      color: isDark ? '#F9FAFB' : '#111827',
      discountColor: '#16A34A',
      originalColor: '#9CA3AF',
    },
    price_info: domHints.prices.length > 0 ? {
      current: domHints.prices[0]?.text || null,
      original: domHints.prices[1]?.text || null,
      discount_pct: null,
    } : null,
    rating: null,
    trust_badges: domHints.badges.slice(0, 4).map(b => b.text).filter(Boolean),
    layout_type: 'generic',
    brand_distinguishers: [],
    cta_buttons: domHints.ctaButtons.slice(0, 3),
    _source: 'dom',
  };
}

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

  const parsedUrl = new URL(targetUrl.startsWith('http') ? targetUrl : `https://${targetUrl}`);
  const domain = parsedUrl.hostname.replace(/^www\./, '');
  const domainBase = domain.split('.')[0] || 'brand';

  // 1. Check persistent brand token cache first
  const cached = getCachedBrand(domain);
  if (cached) {
    console.log(`[Brand Ingest] 📦 Found existing saved brand tokens for "${cached.name}" (${domain}) in cache.`);
    const brand: BrandJson = {
      ...cached,
      logo: {
        src: `jobs/${jobId}/assets/logo.svg`,
        text: cached.name,
        alt: `${cached.name} Logo`,
        source: targetUrl,
      },
    };

    const logoSvgContent = `<svg viewBox="0 0 200 60" xmlns="http://www.w3.org/2000/svg">
      <rect width="200" height="60" rx="10" fill="${brand.colors?.accent || '#6366F1'}22" stroke="${brand.colors?.accent || '#6366F1'}44" stroke-width="1.5"/>
      <text x="100" y="38" font-family="system-ui,sans-serif" font-size="24" font-weight="800"
            text-anchor="middle" fill="${brand.colors?.accent || '#6366F1'}">${brand.name}</text>
    </svg>`;
    fs.writeFileSync(path.join(assetsDir, 'logo.svg'), logoSvgContent, 'utf8');
    fs.writeFileSync(path.join(publicAssetsDir, 'logo.svg'), logoSvgContent, 'utf8');
    fs.writeFileSync(path.join(assetsDir, 'logo.png'), logoSvgContent, 'utf8');
    fs.writeFileSync(path.join(publicAssetsDir, 'logo.png'), logoSvgContent, 'utf8');

    const brandOutPath = path.join(jobDir, 'brand.json');
    fs.writeFileSync(brandOutPath, JSON.stringify(brand, null, 2), 'utf8');
    return brand;
  }

  // 2. Dynamic live crawl via Playwright
  console.log(`[Playwright Ingest] Starting browser crawl for ${targetUrl} (job: ${jobId})...`);

  let extractedTitle = '';
  let extractedDesc = '';
  let extractedThemeColor = '';
  let extractedAccent = '';
  let extractedLogoSvg = '';
  let extractedFont = '';
  let isSiteDark = false;
  const screenshotPath = path.join(assetsDir, 'studio-hero.png');
  const mobileScreenshotPath = path.join(assetsDir, 'studio-mobile.png');

  let domHints: DOMHints = {
    navLinks: [],
    searchPlaceholder: '',
    headerBg: '',
    ctaButtons: [],
    prices: [],
    badges: [],
  };

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

    console.log(`[Playwright Ingest] Navigating to ${targetUrl}...`);
    try {
      await page.goto(targetUrl, {waitUntil: 'domcontentloaded', timeout: 20000});
      extractedTitle = await page.title();
      extractedDesc =
        (await page.$eval('meta[name="description"]', el => el.getAttribute('content')).catch(() => '')) ||
        (await page.$eval('meta[property="og:description"]', el => el.getAttribute('content')).catch(() => '')) ||
        '';
      extractedThemeColor = (await page.$eval('meta[name="theme-color"]', el => el.getAttribute('content')).catch(() => '')) || '';

      // Detailed DOM extraction
      const evaluated = await page.evaluate(() => {
        const rgbToHex = (str: string): string => {
          const m = str.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)/i);
          if (!m) return '';
          const r = parseInt(m[1], 10).toString(16).padStart(2, '0');
          const g = parseInt(m[2], 10).toString(16).padStart(2, '0');
          const b = parseInt(m[3], 10).toString(16).padStart(2, '0');
          const hex = `#${r}${g}${b}`.toUpperCase();
          return hex === '#000000' || hex === '#FFFFFF' ? '' : hex;
        };

        // Accent detection
        let foundAccent: string | null = null;
        const candidates = Array.from(document.querySelectorAll('button, a[role="button"], [class*="btn"], header a'));
        for (const el of candidates) {
          const style = window.getComputedStyle(el);
          const bg = rgbToHex(style.backgroundColor);
          if (bg && bg !== '#FFFFFF' && bg !== '#000000' && !bg.startsWith('#F') && !bg.startsWith('#0')) {
            foundAccent = bg;
            break;
          }
        }

        // Dark background detection
        const bodyStyle = window.getComputedStyle(document.body);
        const bodyBg = rgbToHex(bodyStyle.backgroundColor);
        let dark = false;
        if (bodyBg && bodyBg.startsWith('#')) {
          const r = parseInt(bodyBg.slice(1, 3), 16);
          const g = parseInt(bodyBg.slice(3, 5), 16);
          const b = parseInt(bodyBg.slice(5, 7), 16);
          const lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
          dark = lum < 0.5;
        }

        // Primary Font detection
        let primaryFont = '';
        if (document.body) {
          primaryFont = window.getComputedStyle(document.body).fontFamily || '';
        }

        // Header logo SVG
        let svgHtml = '';
        const headerSvg = document.querySelector('header svg, nav svg, a[class*="logo"] svg, a[id*="logo"] svg');
        if (headerSvg && headerSvg.clientWidth > 16 && headerSvg.clientHeight > 16) {
          svgHtml = headerSvg.outerHTML;
        }

        // Nav links
        const navLinks: string[] = [];
        const navEls = Array.from(document.querySelectorAll('nav a, header a, [role="navigation"] a'));
        for (const el of navEls) {
          const text = (el as HTMLElement).innerText?.trim();
          if (text && text.length > 1 && text.length < 25 && !navLinks.includes(text)) {
            navLinks.push(text);
            if (navLinks.length >= 8) break;
          }
        }

        // Search placeholder
        let searchPlaceholder = '';
        const searchEl = document.querySelector('input[type="search"], input[placeholder*="Search" i], input[aria-label*="search" i]') as HTMLInputElement | null;
        if (searchEl) {
          searchPlaceholder = searchEl.placeholder || searchEl.getAttribute('aria-label') || '';
        }

        // Header background
        let headerBg = '';
        const headerEl = document.querySelector('header, nav, [role="banner"]');
        if (headerEl) {
          headerBg = rgbToHex(window.getComputedStyle(headerEl).backgroundColor);
        }

        // CTA buttons
        const ctaButtons: Array<{text: string; bg: string; color: string}> = [];
        const btnEls = Array.from(document.querySelectorAll('button, a[role="button"], [class*="btn-primary"]'));
        for (const el of btnEls) {
          const style = window.getComputedStyle(el);
          const bg = rgbToHex(style.backgroundColor);
          const color = rgbToHex(style.color);
          const text = (el as HTMLElement).innerText?.trim();
          if (bg && text && text.length < 25) {
            ctaButtons.push({text, bg, color});
            if (ctaButtons.length >= 4) break;
          }
        }

        // Prices
        const prices: Array<{text: string; color: string}> = [];
        const priceEls = Array.from(document.querySelectorAll('[class*="price" i], [class*="cost" i], [class*="amount" i]'));
        for (const el of priceEls) {
          const text = (el as HTMLElement).innerText?.trim();
          if (text && /[₹$€£¥]/.test(text)) {
            const color = rgbToHex(window.getComputedStyle(el).color);
            prices.push({text, color});
            if (prices.length >= 4) break;
          }
        }

        // Badges
        const badges: Array<{text: string; bg: string; color: string}> = [];
        const badgeEls = Array.from(document.querySelectorAll('[class*="badge" i], [class*="tag" i], [class*="chip" i], [class*="assured" i]'));
        for (const el of badgeEls) {
          const text = (el as HTMLElement).innerText?.trim();
          if (text && text.length < 30) {
            const style = window.getComputedStyle(el);
            const bg = rgbToHex(style.backgroundColor);
            const color = rgbToHex(style.color);
            badges.push({text, bg, color});
            if (badges.length >= 6) break;
          }
        }

        return {
          foundAccent,
          isDark: dark,
          primaryFont,
          svgHtml,
          navLinks,
          searchPlaceholder,
          headerBg,
          ctaButtons,
          prices,
          badges,
        };
      }).catch(() => null);

      if (evaluated) {
        if (evaluated.foundAccent) extractedAccent = evaluated.foundAccent;
        if (evaluated.svgHtml) extractedLogoSvg = evaluated.svgHtml;
        if (evaluated.primaryFont) extractedFont = evaluated.primaryFont;
        isSiteDark = evaluated.isDark;
        domHints = {
          navLinks: evaluated.navLinks,
          searchPlaceholder: evaluated.searchPlaceholder,
          headerBg: evaluated.headerBg,
          ctaButtons: evaluated.ctaButtons,
          prices: evaluated.prices,
          badges: evaluated.badges,
        };
      }
    } catch (navErr) {
      console.warn(`[Playwright Ingest] Navigation warning:`, navErr);
    }

    // Capture desktop screenshot
    try {
      await page.screenshot({path: screenshotPath, fullPage: false});
      fs.copyFileSync(screenshotPath, path.join(publicAssetsDir, 'studio-hero.png'));
    } catch (ssErr) {
      console.warn(`[Playwright Ingest] Desktop screenshot warning:`, ssErr);
    }

    // Capture mobile viewport screenshot for mobile authentic UI analysis
    try {
      await page.setViewportSize({width: 390, height: 844});
      await page.waitForTimeout(1500);
      await page.screenshot({path: mobileScreenshotPath, fullPage: false});
      fs.copyFileSync(mobileScreenshotPath, path.join(publicAssetsDir, 'studio-mobile.png'));
      console.log(`[Playwright Ingest] 📱 Captured mobile screenshot to ${mobileScreenshotPath}`);
    } catch (mErr) {
      console.warn(`[Playwright Ingest] Mobile screenshot warning:`, mErr);
    }

    await browser.close();
  } catch (err) {
    console.warn(`[Playwright Ingest] Browser process exception, utilizing standard fallback:`, err);
    if (browser) await browser.close().catch(() => {});
  }

  // ── Derive brand identity dynamically ─────────────────────────────────────
  let inferredName =
    extractedTitle
      .replace(/[-–|·•].*$/, '')
      .replace(/\s+(App|Platform|Studio|Dashboard|Home)$/i, '')
      .trim();

  if (!inferredName || inferredName.length > 35 || /online shopping|official site|homepage|welcome to/i.test(inferredName)) {
    inferredName = domainBase.charAt(0).toUpperCase() + domainBase.slice(1);
  }

  const isYouTube = domain.includes('youtube');

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
    'flipkart.com':  {accent: '#2874F0', accentLight: '#FFE11B', bg: '#071026', bg2: '#0F214D'},
  };

  let finalAccent = extractedAccent || (extractedThemeColor && extractedThemeColor.startsWith('#') ? extractedThemeColor.toUpperCase() : '');
  if (!finalAccent) {
    if (knownColors[domain]) {
      finalAccent = knownColors[domain].accent;
    } else {
      let hash = 0;
      for (let c = 0; c < domain.length; c++) hash = domain.charCodeAt(c) + ((hash << 5) - hash);
      const hue = Math.abs(hash) % 360;
      finalAccent = `hsl(${hue}, 75%, 52%)`;
    }
  }

  const colorKit = knownColors[domain] ?? {
    accent: finalAccent,
    accentLight: finalAccent,
    bg: isSiteDark ? '#09090B' : '#FAFAFA',
    bg2: isSiteDark ? '#141418' : '#F4F4F5',
  };

  const logoSvgContent = isYouTube
    ? OFFICIAL_YOUTUBE_SVG
    : (extractedLogoSvg || `<svg viewBox="0 0 200 60" xmlns="http://www.w3.org/2000/svg">
        <rect width="200" height="60" rx="10" fill="${colorKit.accent}22" stroke="${colorKit.accent}44" stroke-width="1.5"/>
        <text x="100" y="38" font-family="system-ui,-apple-system,sans-serif" font-size="24" font-weight="800"
              text-anchor="middle" fill="${colorKit.accent}">${inferredName}</text>
      </svg>`);

  const logoSvgPath = path.join(assetsDir, 'logo.svg');
  const publicLogoSvgPath = path.join(publicAssetsDir, 'logo.svg');
  fs.writeFileSync(logoSvgPath, logoSvgContent, 'utf8');
  fs.writeFileSync(publicLogoSvgPath, logoSvgContent, 'utf8');
  fs.writeFileSync(path.join(assetsDir, 'logo.png'), logoSvgContent, 'utf8');
  fs.writeFileSync(path.join(publicAssetsDir, 'logo.png'), logoSvgContent, 'utf8');

  // ── Vision UI Analysis ────────────────────────────────────────────────────
  let uiDesc: UIDescription | null = null;
  if (fs.existsSync(mobileScreenshotPath)) {
    uiDesc = await analyzeWithVision(mobileScreenshotPath, domHints, inferredName, jobDir);
  }
  if (!uiDesc) {
    uiDesc = buildFallbackUIDescription(domHints, inferredName, colorKit.accent, isSiteDark);
  }

  const uiDescPath = path.join(jobDir, 'ui_description.json');
  const publicUiDescPath = path.join(path.resolve(process.cwd(), 'public', 'jobs', jobId), 'ui_description.json');
  fs.writeFileSync(uiDescPath, JSON.stringify(uiDesc, null, 2), 'utf8');
  try {
    fs.mkdirSync(path.dirname(publicUiDescPath), {recursive: true});
    fs.writeFileSync(publicUiDescPath, JSON.stringify(uiDesc, null, 2), 'utf8');
  } catch (_e) {
    void _e;
  }
  console.log(`[Brand Ingest] 📑 Structured ui_description.json written for ${inferredName} (source: ${uiDesc._source})`);

  // ── Contrast & Font Extraction (Phase 9) ─────────────────────────────────
  function getLuminance(hex: string): number {
    const clean = hex.replace('#', '');
    const r = (parseInt(clean.slice(0, 2), 16) || 0) / 255;
    const g = (parseInt(clean.slice(2, 4), 16) || 0) / 255;
    const b = (parseInt(clean.slice(4, 6), 16) || 0) / 255;
    const [rs, gs, bs] = [r, g, b].map(c => c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  }

  function getContrastRatio(hex1: string, hex2: string): number {
    const l1 = getLuminance(hex1);
    const l2 = getLuminance(hex2);
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);
    return (lighter + 0.05) / (darker + 0.05);
  }

  let textCol = isSiteDark ? '#F9FAFB' : '#09090B';
  if (colorKit.bg.startsWith('#') && textCol.startsWith('#')) {
    const ratio = getContrastRatio(textCol, colorKit.bg);
    if (ratio < 4.5) {
      textCol = isSiteDark ? '#FFFFFF' : '#000000';
      console.log(`[Brand Ingest] ⚠️ Adjusted text color for WCAG 4.5:1 contrast compliance against ${colorKit.bg}`);
    }
  }

  const cleanFont = extractedFont
    ? extractedFont.split(',')[0].replace(/['"]/g, '').trim()
    : 'Inter';
  const resolvedFontFamily = `${cleanFont}, system-ui, -apple-system, sans-serif`;

  const brand: BrandJson = {
    name: inferredName,
    domain,
    tagline: extractedDesc.split('.')[0].trim() || `${inferredName} — built for what's next.`,
    description: extractedDesc || `${inferredName} is a modern product trusted by millions.`,
    products: uiDesc.brand_distinguishers.length > 0 ? uiDesc.brand_distinguishers : [inferredName],
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
      text:        textCol,
      muted:       isSiteDark ? '#9CA3AF' : '#71717A',
      surface:     colorKit.bg2,
      surfaceText: isSiteDark ? '#FFFFFF' : '#09090B',
      surfaceMuted:'#6B7280',
    },
    fonts: {
      display: {family: resolvedFontFamily, source: extractedFont ? 'Site Extracted' : 'Google Fonts'},
      body:    {family: resolvedFontFamily, source: extractedFont ? 'Site Extracted' : 'Google Fonts'},
    },
    imagery: fs.existsSync(screenshotPath)
      ? [{src: `jobs/${jobId}/assets/studio-hero.png`, alt: `${inferredName} product screenshot`, source: targetUrl}]
      : [],
    claims: [
      {id: 'product', label: inferredName, value: 'See it in action', sourceUrl: targetUrl},
    ],
  };

  saveBrandToCache(domain, brand);

  const brandOutPath = path.join(jobDir, 'brand.json');
  fs.writeFileSync(brandOutPath, JSON.stringify(brand, null, 2), 'utf8');
  console.log(`[Playwright Ingest] ✅ brand.json → ${inferredName} (${domain}) accent=${colorKit.accent}`);

  return brand;
}

if (process.argv[1]?.includes('scrape-brand')) {
  const target = process.argv[2] || 'https://www.flipkart.com';
  const jobId = process.argv[3] || 'flipkart-001';
  scrapeBrand(target, jobId)
    .then(() => process.exit(0))
    .catch(err => {
      console.error(err);
      process.exit(1);
    });
}
