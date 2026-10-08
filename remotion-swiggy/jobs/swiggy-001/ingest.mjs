import {mkdir, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const job = fileURLToPath(new URL('.', import.meta.url));
const url = 'https://www.swiggy.com/corporate/';
const headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'};
const response = await fetch(url, {headers});
if (!response.ok) throw new Error(`Brand ingestion failed: ${response.status}`);
const html = await response.text();
await mkdir(`${job}/assets/imagery`, {recursive: true});
const evidence = [...html.matchAll(/data-to=["']([^"']+)["']/g)].map((match) => ({value: match[1], context: html.slice(Math.max(0, match.index - 200), match.index + 400)}));
await writeFile(`${job}/assets/site-evidence.json`, JSON.stringify({url, ingestedAt: new Date().toISOString(), counters: evidence}, null, 2));
const assets = {
  'logo.png': 'https://www.swiggy.com/corporate/wp-content/uploads/unlimited_elements/Swiggy-newsroom-logo.png',
  'imagery/food.webp': 'https://www.swiggy.com/corporate/wp-content/uploads/2024/10/food.webp',
  'imagery/essentials.webp': 'https://www.swiggy.com/corporate/wp-content/uploads/2024/10/instamart-1.webp',
  'imagery/dining.webp': 'https://www.swiggy.com/corporate/wp-content/uploads/2024/10/dineout.webp',
};
for (const [path, source] of Object.entries(assets)) {
  const file = await fetch(source, {headers});
  if (!file.ok) throw new Error(`Asset download failed: ${source} (${file.status})`);
  await writeFile(`${job}/assets/${path}`, Buffer.from(await file.arrayBuffer()));
}
process.stdout.write(`${JSON.stringify({assets: Object.keys(assets), counters: evidence.map(({value}) => value)})}\n`);
