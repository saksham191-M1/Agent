import {chromium} from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import type {WalkthroughTelemetry, TelemetryEvent} from '../engine/walkthrough/types';

export interface RecordSessionOptions {
  url: string;
  outputDir: string;
  actions: Array<{
    type: 'click' | 'type' | 'hover' | 'scroll';
    selector: string;
    text?: string;
    delayMs?: number;
  }>;
}

export async function recordWalkthroughSession(options: RecordSessionOptions): Promise<WalkthroughTelemetry> {
  const {url, outputDir, actions} = options;
  fs.mkdirSync(outputDir, {recursive: true});

  console.log(`[Playwright Recorder] Launching 4K Retina Chromium (3840x2160 @2x)...`);
  const browser = await chromium.launch({
    headless: true,
    args: ['--hide-scrollbars', '--disable-features=TranslateUI'],
  });

  const context = await browser.newContext({
    viewport: {width: 1920, height: 1080},
    deviceScaleFactor: 2.0, // Retina @2x -> 3840x2160 physical buffer
    recordVideo: {
      dir: outputDir,
      size: {width: 1920, height: 1080},
    },
  });

  const page = await context.newPage();
  const startTime = Date.now();
  const events: TelemetryEvent[] = [];

  console.log(`[Playwright Recorder] Navigating to ${url}...`);
  await page.goto(url, {waitUntil: 'networkidle'});

  for (let i = 0; i < actions.length; i++) {
    const act = actions[i];
    const timestampSec = (Date.now() - startTime) / 1000;

    try {
      const el = page.locator(act.selector).first();
      await el.waitFor({state: 'visible', timeout: 5000});
      const box = await el.boundingBox();

      if (box) {
        events.push({
          id: `event-${i + 1}`,
          type: act.type,
          timestampSec,
          selector: act.selector,
          boundingBox: {
            x: box.x,
            y: box.y,
            width: box.width,
            height: box.height,
          },
          payload: act.text ? {typedText: act.text} : undefined,
        });

        if (act.type === 'click') {
          await el.click();
        } else if (act.type === 'type' && act.text) {
          await el.fill(act.text);
        } else if (act.type === 'hover') {
          await el.hover();
        }
      }
    } catch (err) {
      console.warn(`[Playwright Recorder] Action on ${act.selector} failed or timed out:`, err);
    }

    if (act.delayMs) {
      await page.waitForTimeout(act.delayMs);
    }
  }

  // Final hold
  await page.waitForTimeout(1500);

  await page.close();
  await context.close();
  await browser.close();

  const telemetry: WalkthroughTelemetry = {
    viewport: {
      width: 3840,
      height: 2160,
      scaleFactor: 2.0,
    },
    events,
  };

  const telemetryPath = path.join(outputDir, 'telemetry.json');
  fs.writeFileSync(telemetryPath, JSON.stringify(telemetry, null, 2), 'utf8');
  console.log(`[Playwright Recorder] Telemetry saved to ${telemetryPath} (${events.length} events logged).`);

  return telemetry;
}
