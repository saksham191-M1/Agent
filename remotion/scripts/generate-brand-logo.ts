import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import type {BrandJson} from '../engine/types';

const KNOWN_BRAND_SVGS: Record<string, {viewBox: string; path: string; fill?: string}> = {
  linear: {
    viewBox: '0 0 24 24',
    path: 'M2.886 4.18A11.982 11.982 0 0 1 11.99 0C18.624 0 24 5.376 24 12.009c0 3.64-1.62 6.903-4.18 9.105L2.887 4.18ZM1.817 5.626l16.556 16.556c-.524.33-1.075.62-1.65.866L.951 7.277c.247-.575.537-1.126.866-1.65ZM.322 9.163l14.515 14.515c-.71.172-1.443.282-2.195.322L0 11.358a12 12 0 0 1 .322-2.195Zm-.17 4.862 9.823 9.824a12.02 12.02 0 0 1-9.824-9.824Z',
  },
  supabase: {
    viewBox: '0 0 24 24',
    path: 'M11.9 1.036c-.015-.986-1.26-1.41-1.874-.637L.764 12.05C-.33 13.427.65 15.455 2.409 15.455h9.579l.113 7.51c.014.985 1.259 1.408 1.873.636l9.262-11.653c1.093-1.375.113-3.403-1.645-3.403h-9.642z',
  },
  resend: {
    viewBox: '0 0 24 24',
    path: 'M14.679 0c4.648 0 7.413 2.765 7.413 6.434s-2.765 6.434-7.413 6.434H12.33L24 24h-8.245l-8.88-8.44c-.636-.588-.93-1.273-.93-1.86 0-.831.587-1.565 1.713-1.883l4.574-1.224c1.737-.465 2.936-1.81 2.936-3.572 0-2.153-1.761-3.4-3.939-3.4H0V0z',
  },
  gemini: {
    viewBox: '0 0 24 24',
    path: 'M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96 2.19.93 3.81 2.55t2.55 3.81',
  },
};

function getBrowserPath(): string {
  const candidates = [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  throw new Error('No compatible browser (Chrome or Edge) found for logo rendering.');
}

export function generateBrandLogo(brand: BrandJson, outputPath: string): void {
  const browserPath = getBrowserPath();
  const domain = (brand.domain || '').toLowerCase();
  const name = (brand.name || '').toLowerCase();
  const accent = brand.colors?.accent || '#5E6AD2';
  const bg = brand.colors?.background || '#08090C';

  let brandKey = '';
  if (domain.includes('linear') || name.includes('linear')) brandKey = 'linear';
  else if (domain.includes('supabase') || name.includes('supabase')) brandKey = 'supabase';
  else if (domain.includes('resend') || name.includes('resend')) brandKey = 'resend';
  else if (domain.includes('gemini') || name.includes('gemini')) brandKey = 'gemini';

  const known = KNOWN_BRAND_SVGS[brandKey];

  let svgInner = '';
  if (brandKey === 'gemini' && known) {
    svgInner = `
      <svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="width: 260px; height: 260px; position: relative; z-index: 10;">
        <defs>
          <linearGradient id="geminiGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#4285F4" />
            <stop offset="50%" stop-color="#9B72CB" />
            <stop offset="100%" stop-color="#D96570" />
          </linearGradient>
        </defs>
        <path fill="url(#geminiGrad)" d="${known.path}" />
      </svg>
    `;
  } else if (known) {
    svgInner = `
      <svg role="img" viewBox="${known.viewBox}" xmlns="http://www.w3.org/2000/svg" fill="${accent}" style="width: 256px; height: 256px; position: relative; z-index: 10;">
        <path d="${known.path}" />
      </svg>
    `;
  } else {
    // Elegant procedural monogram badge
    const initial = (brand.name || 'A').slice(0, 1).toUpperCase();
    svgInner = `
      <div style="width: 240px; height: 240px; border-radius: 56px; background: linear-gradient(135deg, ${accent}33 0%, ${accent}11 100%); border: 2px solid ${accent}66; display: flex; align-items: center; justify-content: center; position: relative; z-index: 10;">
        <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 120px; font-weight: 800; color: ${accent}; letter-spacing: -2px;">
          ${initial}
        </span>
      </div>
    `;
  }

  const htmlContent = `<!DOCTYPE html>
<html>
<head>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 512px;
    height: 512px;
    background: ${bg};
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 96px;
    overflow: hidden;
    position: relative;
  }
  .glow {
    position: absolute;
    width: 340px;
    height: 340px;
    border-radius: 50%;
    background: radial-gradient(circle, ${accent}55 0%, transparent 70%);
  }
  .border-ring {
    position: absolute;
    inset: 4px;
    border-radius: 92px;
    border: 2px solid rgba(255, 255, 255, 0.12);
    pointer-events: none;
  }
</style>
</head>
<body>
  <div class="glow"></div>
  <div class="border-ring"></div>
  ${svgInner}
</body>
</html>`;

  const tempHtml = path.resolve(process.cwd(), `temp-logo-${Date.now()}.html`);
  const tempPng = path.resolve(process.cwd(), `temp-logo-${Date.now()}.png`);

  try {
    fs.writeFileSync(tempHtml, htmlContent, 'utf8');
    const args = [
      '--headless=new',
      '--disable-gpu',
      '--hide-scrollbars',
      '--window-size=512,512',
      '--default-background-color=00000000',
      `--screenshot=${tempPng}`,
      `file:///${tempHtml.replace(/\\/g, '/')}`,
    ];

    const proc = spawnSync(browserPath, args);
    if (proc.status === 0 && fs.existsSync(tempPng)) {
      fs.mkdirSync(path.dirname(outputPath), {recursive: true});
      fs.copyFileSync(tempPng, outputPath);
    } else {
      throw new Error(`Failed to screenshot logo: ${proc.stderr?.toString()}`);
    }
  } finally {
    if (fs.existsSync(tempHtml)) fs.unlinkSync(tempHtml);
    if (fs.existsSync(tempPng)) fs.unlinkSync(tempPng);
  }
}
