import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import type {BrandJson} from '../engine/types';

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
  const accent = brand.colors?.accent || '#6366F1';
  const bg = brand.colors?.background || '#09090B';
  const initial = (brand.name || 'A').slice(0, 1).toUpperCase();

  // Procedural, brand-agnostic monogram badge with dynamic brand tokens
  const svgInner = `
    <div style="width: 240px; height: 240px; border-radius: 56px; background: linear-gradient(135deg, ${accent}33 0%, ${accent}11 100%); border: 2px solid ${accent}66; display: flex; align-items: center; justify-content: center; position: relative; z-index: 10;">
      <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 120px; font-weight: 800; color: ${accent}; letter-spacing: -2px;">
        ${initial}
      </span>
    </div>
  `;

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
