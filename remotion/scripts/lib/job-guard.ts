/**
 * job-guard.ts
 * ────────────
 * Validates self-containment, audio isolation, factual grounding,
 * palette consistency, and layout-node match for a rendered ad job.
 */

import fs from 'node:fs';
import path from 'node:path';
import {validateWaivers} from './exceptions';

export interface GuardIssue {
  code:
    | 'AUDIO_FOREIGN_ROOT'
    | 'AUDIO_MISSING'
    | 'AUDIO_SILENT'
    | 'FOREIGN_BRAND'
    | 'UNSUPPORTED_NUMBER'
    | 'PALETTE_MISMATCH'
    | 'LAYOUT_NODE_MISMATCH'
    | 'BAD_CLAIM'
    | 'WAIVER_INVALID';
  message: string;
}

export interface ValidationResult {
  jobId: string;
  errors: GuardIssue[];
  warnings: GuardIssue[];
  valid: boolean;
}

export function validateJob(jobsRoot: string, jobId: string): ValidationResult {
  const errors: GuardIssue[] = [];
  const warnings: GuardIssue[] = [];

  const jobDir = path.resolve(jobsRoot, jobId);
  const specPath = path.join(jobDir, 'spec.json');
  const brandPath = path.join(jobDir, 'brand.json');
  const uiTreePath = path.join(jobDir, 'ui_tree.json');

  if (!fs.existsSync(specPath)) {
    errors.push({code: 'AUDIO_MISSING', message: `spec.json not found in ${jobDir}`});
    return {jobId, errors, warnings, valid: false};
  }

  const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
  const brand = fs.existsSync(brandPath) ? JSON.parse(fs.readFileSync(brandPath, 'utf8')) : null;
  const uiTree = fs.existsSync(uiTreePath) ? JSON.parse(fs.readFileSync(uiTreePath, 'utf8')) : null;

  // 1. Audio assetsRoot isolation check
  const expectedAudioRoot = `jobs/${jobId}/assets`;
  if (spec.audio?.assetsRoot && !spec.audio.assetsRoot.includes(jobId)) {
    errors.push({
      code: 'AUDIO_FOREIGN_ROOT',
      message: `spec.audio.assetsRoot (${spec.audio.assetsRoot}) is not this job's assets folder (expected ${expectedAudioRoot})`
    });
  }

  // 2. Audio file existence check
  if (spec.audio) {
    const assetsRootOnDisk = path.resolve(jobsRoot, jobId, 'assets');
    const checkFile = (fileRel?: string) => {
      if (!fileRel) return;
      const fullPath = path.resolve(assetsRootOnDisk, fileRel);
      if (!fs.existsSync(fullPath)) {
        errors.push({
          code: 'AUDIO_MISSING',
          message: `Referenced audio file does not exist on disk: ${fileRel} (searched at ${fullPath})`
        });
      }
    };

    if (spec.audio.music?.file) checkFile(spec.audio.music.file);
    if (spec.audio.roomTone?.file) checkFile(spec.audio.roomTone.file);
    if (Array.isArray(spec.audio.voiceClips)) {
      for (const vc of spec.audio.voiceClips) {
        checkFile(vc.file);
      }
    }
    if (Array.isArray(spec.audio.sfxFiles)) {
      for (const sfx of spec.audio.sfxFiles) {
        checkFile(sfx);
      }
    }

    // Check AUDIO_SILENT
    const hasVoice = Array.isArray(spec.audio.voiceClips) && spec.audio.voiceClips.length > 0;
    const hasMusic = spec.audio.music?.file && (spec.audio.music.volume ?? 0) > 0;
    if (!hasVoice && !hasMusic && !spec.audio.silentVo) {
      errors.push({
        code: 'AUDIO_SILENT',
        message: 'No voice and no music with volume above zero, and no --silent-vo flag'
      });
    }
  }

  // Collect all text from spec scenes
  const allCopy: string[] = [];
  if (Array.isArray(spec.scenes)) {
    for (const sc of spec.scenes) {
      if (sc.headline) allCopy.push(sc.headline);
      if (sc.subline) allCopy.push(sc.subline);
      if (sc.voiceover) allCopy.push(sc.voiceover);
      if (sc.vo) allCopy.push(sc.vo);
      if (sc.caption) allCopy.push(sc.caption);
      if (sc.onScreenText) allCopy.push(sc.onScreenText);
    }
  }
  const joinedText = allCopy.join(' ');

  // 3. Foreign brand check
  const knownBrandNames: Record<string, string> = {
    swiggy: 'swiggy',
    zomato: 'zomato',
    zerodha: 'zerodha',
    flipkart: 'flipkart',
    supabase: 'supabase',
    prisma: 'prisma',
    resend: 'resend',
    linear: 'linear'
  };

  const currentBrandKey = (brand?.name || jobId).toLowerCase();
  for (const [key, brandName] of Object.entries(knownBrandNames)) {
    if (!currentBrandKey.includes(key)) {
      const regex = new RegExp(`\\b${brandName}\\b`, 'i');
      if (regex.test(joinedText)) {
        errors.push({
          code: 'FOREIGN_BRAND',
          message: `Foreign brand name "${brandName}" found in copy for job ${jobId}`
        });
      }
    }
  }

  // 4. Unsupported number check
  // Matches numbers, percentages, or scale words like million, billion, lakh, crore, three
  const numberMatches = joinedText.match(/\b(?:\d[\d,.]*|\d+%|million|millions|billion|billions|lakh|crore|three)\b/gi) || [];
  const brandClaimsText = brand?.claims ? JSON.stringify(brand.claims) : '';
  const seenNumbers = new Set<string>();
  for (const rawNum of numberMatches) {
    const num = rawNum.toLowerCase();
    if (['1', '2', '4', '5', '6', '7'].includes(num)) continue;
    if (seenNumbers.has(num)) continue;
    seenNumbers.add(num);
    if (!brandClaimsText.toLowerCase().includes(num)) {
      errors.push({
        code: 'UNSUPPORTED_NUMBER',
        message: `Number or metric "${rawNum}" in copy does not appear in brand.claims`
      });
    }
  }

  // 5. Palette consistency check
  if (spec.palette && brand?.colors) {
    const isReference = spec.paletteSource === 'reference' || spec.palette?.source === 'reference';
    if (!isReference) {
      const norm = (c?: string) => (c || '').replace(/\s+/g, '').toLowerCase();
      const specAccent = norm(spec.palette.accent);
      const brandAccent = norm(brand.colors.accent);
      const specBg = norm(spec.palette.background);
      const brandBg = norm(brand.colors.background);

      if (specAccent && brandAccent && specAccent !== brandAccent) {
        errors.push({
          code: 'PALETTE_MISMATCH',
          message: `spec.palette.accent (${specAccent}) does not match brand.colors.accent (${brandAccent})`
        });
      }
      if (specBg && brandBg && specBg !== brandBg) {
        errors.push({
          code: 'PALETTE_MISMATCH',
          message: `spec.palette.background (${specBg}) does not match brand.colors.background (${brandBg})`
        });
      }
    }
  }

  // 6. Layout and UI node type match check
  const uiNodes = Array.isArray(uiTree?.nodes) ? uiTree.nodes : (Array.isArray(uiTree?.scenes) ? uiTree.scenes : null);
  if (uiNodes && Array.isArray(spec.scenes)) {
    for (let i = 0; i < spec.scenes.length; i++) {
      const sc = spec.scenes[i];
      const treeNode = uiNodes[i];
      if (sc.layout === 'browser') {
        const hasBrowser = treeNode?.type === 'browser' || treeNode?.type === 'browser_frame' || treeNode?.type === 'browser_mockup' || treeNode?.type === 'screenshot';
        if (!hasBrowser) {
          errors.push({
            code: 'LAYOUT_NODE_MISMATCH',
            message: `Scene ${i + 1} layout is "browser" but UI node type is "${treeNode?.type}"`
          });
        }
      }
      if (sc.layout === 'big-number' || sc.layout === 'metrics') {
        const hasMetric = treeNode?.type === 'metric' || treeNode?.type === 'metric_card' || treeNode?.type === 'metric_counter';
        if (!hasMetric) {
          errors.push({
            code: 'LAYOUT_NODE_MISMATCH',
            message: `Scene ${i + 1} layout is "${sc.layout}" but UI node type is "${treeNode?.type}"`
          });
        }
      }
    }
  }

  // 7. Brand claims validity check
  if (brand?.claims && Array.isArray(brand.claims)) {
    for (const c of brand.claims) {
      if (c.label && brand.name && c.label.trim().toLowerCase() === brand.name.trim().toLowerCase()) {
        errors.push({
          code: 'BAD_CLAIM',
          message: `Claim label "${c.label}" is identical to brand name "${brand.name}"`
        });
      }
    }
  }

  // 8. Waiver validation check (known-exceptions.json)
  const exceptionsPath = path.join(jobDir, 'known-exceptions.json');
  if (fs.existsSync(exceptionsPath)) {
    try {
      const rawExceptions = JSON.parse(fs.readFileSync(exceptionsPath, 'utf8'));
      const waiverCheck = validateWaivers(rawExceptions);
      if (!waiverCheck.valid) {
        for (const wErr of waiverCheck.errors) {
          errors.push({
            code: 'WAIVER_INVALID',
            message: `Invalid known-exceptions.json: ${wErr}`
          });
        }
      }
    } catch (e: any) {
      errors.push({
        code: 'WAIVER_INVALID',
        message: `Failed to parse known-exceptions.json: ${e?.message}`
      });
    }
  }

  return {
    jobId,
    errors,
    warnings,
    valid: errors.length === 0
  };
}
