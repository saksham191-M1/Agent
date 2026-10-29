import fs from 'node:fs';
import path from 'node:path';
import type {BrandJson} from '../engine/types';

const CACHE_FILE = path.resolve(process.cwd(), 'jobs', 'brand-cache.json');

export function normalizeBrandKey(input: string): string {
  return input
    .toLowerCase()
    .replace(/^https?:\/\//, '')
    .replace(/^www\./, '')
    .replace(/[/?#].*$/, '')
    .trim();
}

export function loadBrandCache(): Record<string, BrandJson> {
  if (!fs.existsSync(CACHE_FILE)) {
    return {};
  }
  try {
    const raw = fs.readFileSync(CACHE_FILE, 'utf8');
    return JSON.parse(raw);
  } catch (err) {
    console.warn(`[Brand Cache] Warning reading brand cache:`, err);
    return {};
  }
}

export function getCachedBrand(identifier: string): BrandJson | null {
  const cache = loadBrandCache();
  const key = normalizeBrandKey(identifier);
  if (cache[key]) return cache[key];

  // Try matching by brand name
  const normalizedName = identifier.toLowerCase().replace(/[^a-z0-9]/g, '');
  for (const entry of Object.values(cache)) {
    const entryName = (entry.name || '').toLowerCase().replace(/[^a-z0-9]/g, '');
    const entryDomain = (entry.domain || '').toLowerCase().replace(/[^a-z0-9]/g, '');
    if (entryName === normalizedName || entryDomain.includes(normalizedName) || normalizedName.includes(entryName)) {
      return entry;
    }
  }

  return null;
}

export function saveBrandToCache(identifier: string, brand: BrandJson): void {
  const cache = loadBrandCache();
  const key = normalizeBrandKey(identifier || brand.domain || brand.name);
  cache[key] = brand;

  // Also index by domain if present
  if (brand.domain) {
    const domainKey = normalizeBrandKey(brand.domain);
    cache[domainKey] = brand;
  }

  try {
    fs.mkdirSync(path.dirname(CACHE_FILE), {recursive: true});
    fs.writeFileSync(CACHE_FILE, JSON.stringify(cache, null, 2), 'utf8');
    console.log(`[Brand Cache] 💾 Saved brand tokens for "${brand.name}" (${key}) into persistent cache.`);
  } catch (err) {
    console.warn(`[Brand Cache] Failed to write to brand cache:`, err);
  }
}
