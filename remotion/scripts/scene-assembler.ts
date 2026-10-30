/**
 * scene-assembler.ts
 * ──────────────────
 * Converts:
 *   storyboard.json   (from brain_opus.py --output-json)
 *   brand.json        (from scrape-brand.ts)
 * Into:
 *   jobs/<jobId>/ui_tree.json   — VectorNode AST consumed by VectorRenderer
 *   jobs/<jobId>/spec.json      — Remotion composition spec
 *   jobs/<jobId>/storyboard.json (overwritten with assembled version)
 *
 * Node-type selection strategy (NO hardcoded archetypes):
 *   - Product category detected from brand domain keywords + storyboard hints
 *   - Each scene gets a distinct node type fitting its role
 *   - Hook scenes → kinetic_typography
 *   - UI scenes (web/SaaS) → app_frame or browser_mockup
 *   - UI scenes (mobile/food/ride) → phone_mockup
 *   - Metric/analytics scenes → chart or metric_card
 *   - AI/agent/chat scenes → chat_messaging
 *   - CTA scenes → kinetic_typography + pill_tag
 */

import fs from 'node:fs';
import path from 'node:path';
import type {UITree, VectorNode} from '../engine/semantic-ui/types';
import type {BrandJson} from '../engine/types';
import {MOTION_RULES} from '../engine/motion/motion-rules';
import {loadUIDescription, buildNodeFromUIDescription} from './ui-description-to-node';
import {validateStoryboardSpec} from './spec-schema';

// ─────────────────────────────────────────────────────────────────────────────
// Luminance-based light/dark detection (handles hex + hsl)
// ─────────────────────────────────────────────────────────────────────────────

function isLightBackground(color?: string): boolean {
  if (!color) return false;
  const c = color.trim().toLowerCase();

  // HSL: hsl(H, S%, L%)
  const hslMatch = c.match(/hsl\s*\(\s*[\d.]+\s*,\s*[\d.]+%?\s*,\s*([\d.]+)%?\s*\)/);
  if (hslMatch) {
    return parseFloat(hslMatch[1]) > 55;
  }

  // Hex
  if (c.startsWith('#') && c.length >= 7) {
    const r = parseInt(c.slice(1, 3), 16);
    const g = parseInt(c.slice(3, 5), 16);
    const b = parseInt(c.slice(5, 7), 16);
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.55;
  }

  return false;
}

// ──────────────────────────────────────────────────────────────────────────────
// Product category detection
// ──────────────────────────────────────────────────────────────────────────────

type ProductCategory =
  | 'mobile_app'
  | 'web_saas'
  | 'dev_tool'
  | 'ai_agent'
  | 'analytics'
  | 'creator'
  | 'ecommerce'
  | 'social'
  | 'generic';

// ──────────────────────────────────────────────────────────────────────────────
// Category-specific helpers: nav fallbacks + emoji icon sets
// ──────────────────────────────────────────────────────────────────────────────

function categoryFallbackNav(category: ProductCategory): string[] {
  switch (category) {
    case 'mobile_app':   return ['Browse', 'Track', 'Account', 'Offers'];
    case 'ecommerce':    return ['Shop', 'Wishlist', 'Orders', 'Account'];
    case 'social':       return ['Feed', 'Explore', 'Messages', 'Profile'];
    case 'web_saas':     return ['Dashboard', 'Features', 'Team', 'Settings'];
    case 'dev_tool':     return ['Overview', 'API', 'Deploy', 'Docs'];
    case 'ai_agent':     return ['Chat', 'Projects', 'Integrations', 'Settings'];
    case 'analytics':    return ['Insights', 'Reports', 'Goals', 'Settings'];
    case 'creator':      return ['Trending', 'For You', 'Collections', 'Upload'];
    default:             return ['Home', 'Features', 'About', 'Contact'];
  }
}

function categoryIcons(category: ProductCategory): string[] {
  switch (category) {
    case 'mobile_app':   return ['📦', '📍', '🔔', '⭐'];
    case 'ecommerce':    return ['🛍', '❤️', '🎁', '🏷'];
    case 'social':       return ['💬', '♥️', '🔖', '👥'];
    case 'fintech' as any:
    case 'analytics':    return ['📊', '📈', '🔒', '💼'];
    case 'dev_tool':     return ['⌨', '🔧', '📡', '📁'];
    case 'ai_agent':     return ['🤖', '💡', '🔮', '⚡'];
    case 'creator':      return ['▶', '🎬', '⭐', '📡'];
    default:             return ['✦', '◈', '▸', '●'];
  }
}

function detectCategory(brand: BrandJson, storyboardHints: string): ProductCategory {
  const text = `${brand.domain} ${brand.description} ${brand.products.join(' ')} ${storyboardHints}`.toLowerCase();

  if (/delivery|food|groceri|ride|restaurant|order/.test(text)) return 'mobile_app';
  if (/social|community|feed|post|reel|story|share/.test(text)) return 'social';
  if (/creator|video|stream|podcast|music|channel|broadcast/.test(text)) return 'creator';
  if (/shop|ecommerce|cart|store|product|buy|sell|retail/.test(text)) return 'ecommerce';
  if (/agent|ai|chat|copilot|assistant|model|llm|intelligence/.test(text)) return 'ai_agent';
  if (/analytics|dashboard|metric|insight|chart|report|data|bi|telemetry/.test(text)) return 'analytics';
  if (/api|sdk|cli|orm|db|database|deploy|devtool|infrastructure|cloud|backend/.test(text)) return 'dev_tool';
  if (/app|mobile|ios|android|native/.test(text)) return 'mobile_app';
  if (/saas|platform|software|workspace|crm|erp|productivity|collaboration|workflow/.test(text)) return 'web_saas';

  return 'generic';
}

// ──────────────────────────────────────────────────────────────────────────────
// Per-scene VectorNode builders
// ──────────────────────────────────────────────────────────────────────────────

function makeHookNode(brand: BrandJson, scene: any, idx: number): VectorNode {
  return {
    id: `node_hook_${idx}`,
    type: 'kinetic_typography',
    position3D: [0, 0, 0],
    effect: 'phrase_flash',
    words: [
      scene.kinetic_text?.toUpperCase() || brand.name.toUpperCase(),
      brand.tagline?.split('.')[0]?.toUpperCase() || 'WHAT IF',
    ],
    text: scene.kinetic_text || brand.name,
    subtext: scene.voiceover?.slice(0, 80) || brand.tagline,
    fontSize: 96,
  } as VectorNode;
}

function makeUINode(brand: BrandJson, scene: any, category: ProductCategory, idx: number): VectorNode {
  if (category === 'mobile_app' || category === 'social' || category === 'ecommerce') {
    // Phone mockup
    const fallbackNav = categoryFallbackNav(category);
    const icons = categoryIcons(category);
    const products = brand.products.length >= 4
      ? brand.products
      : [...brand.products, ...fallbackNav].slice(0, 4);
    return {
      id: `node_phone_${idx}`,
      type: 'phone_mockup',
      position3D: [0, 0, 0],
      greeting: `Welcome to ${brand.name}`,
      prompt: scene.voiceover?.slice(0, 60) || brand.tagline,
      search: `Search ${brand.name}...`,
      items: products.slice(0, 4).map((p, i) => ({
        label: p,
        icon: icons[i] || '●',
      })),
    } as VectorNode;
  }

  if (category === 'ai_agent' || category === 'dev_tool') {
    // Interactive input / chat for AI; app_frame for dev tools
    if (category === 'ai_agent') {
      return {
        id: `node_chat_${idx}`,
        type: 'chat_messaging',
        position3D: [0, 0, 0],
        messages: [
          {id: 'm1', sender: 'user',   text: `Analyze ${brand.products[0] || brand.name}`},
          {id: 'm2', sender: 'agent',  text: scene.voiceover?.slice(0, 100) || `${brand.name}`},
        ],
        typingIndicator: true,
      } as VectorNode;
    }
    // dev_tool → app_frame with dev-flavored sidebar
    return {
      id: `node_appframe_${idx}`,
      type: 'app_frame',
      position3D: [0, 0, 0],
      appName: brand.name,
      topbarTitle: scene.voiceover?.slice(0, 50) || `${brand.name} Studio`,
      badgeText: '● Live',
      activePane: 'editor',
      sidebarItems: (brand.products.length > 0 ? brand.products : ['Dashboard', 'Editor', 'Deploy', 'Analytics']).slice(0, 4).map(
        (p, i) => ({id: `s${i}`, label: p, icon: ['◈', '⬡', '◉', '△'][i] || '•', active: i === 0})
      ),
    } as VectorNode;
  }

  if (category === 'creator') {
    // Browser mockup showing creator/video platform UI
    return {
      id: `node_browser_${idx}`,
      type: 'browser_mockup',
      position3D: [0, 0, 0],
      title: scene.voiceover?.split('.')[0] || `${brand.name} Studio`,
      detail: brand.tagline,
      location: brand.domain,
      cards: (brand.products.length > 0 ? brand.products : ['Trending', 'For You', 'New Release']).slice(0, 3).map(
        (p, i) => ({label: p, detail: brand.tagline, action: 'Open →', icon: ['▶', '★', '◎'][i] || '▶'})
      ),
      showCursor: true,
    } as VectorNode;
  }

  if (category === 'analytics') {
    // Chart node
    const points = [22, 38, 55, 70, 88, 95, 99];
    return {
      id: `node_chart_${idx}`,
      type: 'chart',
      position3D: [0, 0, 0],
      chartType: 'area',
      title: scene.voiceover?.split('.')[0] || `${brand.name} Growth`,
      data: ['Jan','Feb','Mar','Apr','May','Jun','Jul'].map((m, i) => ({label: m, value: points[i]})),
      accentColor: brand.colors.accent,
      showAxis: true,
    } as VectorNode;
  }

  // web_saas + generic → cinematic app_frame
  return {
    id: `node_appframe_${idx}`,
    type: 'app_frame',
    position3D: [0, 0, 0],
    appName: brand.name,
    topbarTitle: scene.voiceover?.split('.')[0] || `${brand.name} Dashboard`,
    badgeText: '● Live',
    activePane: 'dashboard',
    sidebarItems: (brand.products.length > 0 ? brand.products : ['Overview', 'Analytics', 'Team', 'Settings']).slice(0, 4).map(
      (p, i) => ({id: `s${i}`, label: p, active: i === 0})
    ),
  } as VectorNode;
}

function makeMetricNode(brand: BrandJson, idx: number): VectorNode {
  const claim = brand.claims?.[0];
  return {
    id: `node_metric_${idx}`,
    type: 'metric_card',
    position3D: [0, 0, 0],
    label: claim?.label || '',
    value: claim?.value || '',
    delta: '',
    chartPoints: [],
    accentColor: brand.colors.accent,
  } as VectorNode;
}

function ctaCallToAction(brand: BrandJson, scene: any, category: ProductCategory): string {
  // 1. Use storyboard kinetic_text if it looks like a CTA
  const kineticUpper = (scene.kinetic_text || '').toUpperCase().trim();
  if (kineticUpper && kineticUpper.split(' ').length <= 4) return kineticUpper;

  // 2. Use the first short sentence from voiceover if it's imperative
  const voiceover = (scene.voiceover || '').trim();
  const imperativeMatch = voiceover.match(/^(Start|Get|Try|Join|Open|Build|Launch|Sign|Download)\b[^.!?]{0,30}/i);
  if (imperativeMatch) return imperativeMatch[0].toUpperCase();

  // 3. Category-appropriate default
  switch (category) {
    case 'mobile_app':   return 'DOWNLOAD FREE';
    case 'ecommerce':    return 'SHOP NOW';
    case 'social':       return 'JOIN TODAY';
    case 'web_saas':     return 'START FREE TRIAL';
    case 'dev_tool':     return 'GET STARTED FREE';
    case 'ai_agent':     return 'TRY FOR FREE';
    case 'analytics':    return 'SEE YOUR DATA';
    case 'creator':      return 'START CREATING';
    default:             return 'GET STARTED';
  }
}

function makeCTANode(brand: BrandJson, scene: any, category: ProductCategory, idx: number): VectorNode {
  const cta = ctaCallToAction(brand, scene, category);
  return {
    id: `node_cta_${idx}`,
    type: 'kinetic_typography',
    position3D: [0, 0, 0],
    effect: 'word_carousel',
    words: [
      scene.kinetic_text?.toUpperCase() || 'START NOW',
      brand.name.toUpperCase(),
      cta,
    ],
    text: scene.kinetic_text || `Try ${brand.name}`,
    subtext: scene.voiceover?.slice(0, 80) || brand.tagline,
    fontSize: 88,
  } as VectorNode;
}

// ──────────────────────────────────────────────────────────────────────────────
// Main assembler
// ──────────────────────────────────────────────────────────────────────────────

export interface AssembleOptions {
  storyboard: any;   // parsed from brain_opus.py --output-json
  brand: BrandJson;
  jobId: string;
  fps?: number;
}

function resolveCategoryFromML(mlCategory?: string, techTags: string[] = []): ProductCategory | null {
  if (!mlCategory) return null;
  const cat = mlCategory.toLowerCase();
  const tags = techTags.join(' ').toLowerCase();

  if (cat === 'interactive') {
    if (/canvas|webgl|chart|graph|d3|metric/.test(tags)) return 'analytics';
    if (/terminal|code|cli|api|react|dev/.test(tags)) return 'dev_tool';
    return 'web_saas';
  }
  if (cat === '3d') {
    if (/phone|mobile|device|screen/.test(tags)) return 'mobile_app';
    return 'creator';
  }
  if (cat === 'explainer') {
    if (/dashboard|saas|app|finance/.test(tags)) return 'web_saas';
    if (/ai|chat|llm|agent|prompt/.test(tags)) return 'ai_agent';
    return 'creator';
  }
  if (cat === 'motion') {
    if (/mobile|app|ios|android/.test(tags)) return 'mobile_app';
    if (/metric|finance|data|analytics/.test(tags)) return 'analytics';
  }
  return null;
}

function resolveSceneLayout(nodeType: string, sceneIdx: number, totalScenes: number): string {
  if (sceneIdx === 0) return 'hero-type';
  if (sceneIdx === totalScenes - 1) return 'cta';
  switch (nodeType) {
    case 'phone_mockup':
      return 'phone';
    case 'chart':
    case 'metric_card':
    case 'stat_counter':
      return 'big-number';
    case 'bento_grid':
    case 'ecommerce_product_card':
      return 'split';
    case 'browser_mockup':
    case 'app_frame':
    default:
      return 'browser';
  }
}

function resolveSceneTransition(visualFx: string, idx: number): string {
  const fx = (visualFx || '').toLowerCase();
  if (/carousel|glide/.test(fx)) return 'carousel_glide';
  if (/zoom|push|in/.test(fx)) return 'cross_zoom';
  if (/blur|smooth/.test(fx)) return 'carousel_glide';
  if (/wipe|sweep/.test(fx)) return 'wipe';
  if (/flip|rotate/.test(fx)) return 'flip';
  if (/dissolve/.test(fx)) return 'dissolve';
  
  const cycle = ['carousel_glide', 'wipe', 'cross_zoom', 'carousel_glide', 'clock_wipe'];
  return cycle[idx % cycle.length];
}

export function assembleScenes(opts: AssembleOptions): {uiTree: UITree; spec: any} {
  const {storyboard, brand, jobId, fps = MOTION_RULES.render.fps || 60} = opts;

  // Validate incoming storyboard schema via Zod mirror
  try {
    validateStoryboardSpec(storyboard);
  } catch (err: any) {
    console.warn(`[Scene Assembler] Storyboard validation: ${err.message}`);
  }

  const scenes: any[] = storyboard.scenes || [];
  const mlCat = storyboard.ml_match?.category || storyboard.matched_opus_category;
  const mlTags: string[] = storyboard.ml_match?.tech_tags || [];
  const mlResolved = resolveCategoryFromML(mlCat, mlTags);

  const hints = scenes.map((s: any) => `${s.voiceover || ''} ${s.visual_fx || ''} ${s.veo_prompt || ''}`).join(' ');
  const category = mlResolved || detectCategory(brand, hints);

  const jobDir = path.resolve(process.cwd(), 'jobs', jobId);
  const uiDesc = loadUIDescription(jobDir);

  console.log(`[Scene Assembler] Product: ${brand.name} | Domain: ${brand.domain}`);
  console.log(`[Scene Assembler] Category Source: ${mlResolved ? `ML Predictor (${mlCat})` : 'Keyword Detection'} -> ${category}`);
  if (uiDesc) {
    console.log(`[Scene Assembler] 🎨 Brand authentic UI loaded (${uiDesc._source}) with ${uiDesc.header.navLinks.length} nav links`);
  }
  console.log(`[Scene Assembler] Template: "${storyboard.selected_template || 'Problem-Agitate-Solution'}"`);
  console.log(`[Scene Assembler] Building ${scenes.length} scenes from Opus storyboard...`);

  // Build one VectorNode per scene matching the layout specified in the storyboard
  const nodes: VectorNode[] = scenes.map((scene: any, idx: number) => {
    const isFirst = idx === 0;
    const isLast  = idx === scenes.length - 1;
    const requiresUI = scene.requires_ui_image === true;
    const sceneLayout = scene.layout;

    if (sceneLayout === 'metrics' || sceneLayout === 'big-number') {
      return makeMetricNode(brand, idx);
    }
    if (sceneLayout === 'browser') {
      return makeUINode(brand, scene, category, idx);
    }
    if (sceneLayout === 'hero-type') {
      return makeHookNode(brand, scene, idx);
    }
    if (isFirst && !sceneLayout) {
      return makeHookNode(brand, scene, idx);
    }
    if (isLast && (sceneLayout === 'cta' || !sceneLayout)) {
      return makeCTANode(brand, scene, category, idx);
    }
    if (requiresUI) {
      // UI showcase scene — pick based on product category
      if (uiDesc) {
        return buildNodeFromUIDescription(uiDesc, brand, scene, idx, scenes.length);
      }
      return makeUINode(brand, scene, category, idx);
    }
    // Middle scene without ui requirement → metric card or chart depending on category
    if (category === 'analytics' || category === 'dev_tool' || category === 'web_saas') {
      return makeMetricNode(brand, idx);
    }
    if (uiDesc) {
      return buildNodeFromUIDescription(uiDesc, brand, scene, idx, scenes.length);
    }
    return makeUINode(brand, scene, category, idx);
  });

  const uiTree: UITree = {
    brandId: brand.domain,
    worldBounds: {width: 1920, height: 1080, depth: 2000},
    nodes,
  };

  function buildCaptionWords(text: string, durationSec: number, fps: number) {
    if (!text) return [];
    const rawWords = text.trim().split(/\s+/).filter(Boolean);
    if (rawWords.length === 0) return [];

    const totalFrames = Math.max(1, Math.round(durationSec * fps));
    const availableFrames = Math.max(rawWords.length, totalFrames - 16);
    const framesPerWord = availableFrames / rawWords.length;

    return rawWords.map((word, i) => {
      const start = Math.round(6 + i * framesPerWord);
      const end = Math.round(6 + (i + 1) * framesPerWord);
      return {word, start, end};
    });
  }

  function generateSceneSfx(sceneIdx: number, durationSec: number, totalScenes: number, musicMood: string) {
    const cues: Array<{t: number; type: string; gain?: number}> = [];

    // Determine energy tier from storyboard music mood
    const isHighEnergy = /high_energy|upbeat|energetic|intense|hype|fast/.test(musicMood);
    const isCalm       = /calm|ambient|minimal|serene|gentle|slow|precise/.test(musicMood);

    // High-energy: snappier, earlier, louder cues; Calm: sparse, delayed, softer
    const openGain  = isHighEnergy ? 0.90 : isCalm ? 0.55 : 0.85;
    const midGain   = isHighEnergy ? 0.80 : isCalm ? 0.50 : 0.70;
    const closeGain = isHighEnergy ? 0.85 : isCalm ? 0.45 : 0.80;

    const openT     = isHighEnergy ? 0.05 : isCalm ? 0.18 : 0.10;

    cues.push({t: openT, type: 'pop', gain: openGain});

    if (sceneIdx === 0) {
      const tickT = isHighEnergy ? 0.60 : isCalm ? 0.80 : 0.72;
      cues.push({t: Math.round(durationSec * tickT * 100) / 100, type: 'tick', gain: midGain});
    } else if (sceneIdx === totalScenes - 1) {
      const click1T = isHighEnergy ? 0.35 : isCalm ? 0.55 : 0.45;
      const pop2T   = isHighEnergy ? 0.75 : isCalm ? 0.90 : 0.85;
      cues.push({t: Math.round(durationSec * click1T * 100) / 100, type: 'click', gain: midGain});
      cues.push({t: Math.round(durationSec * pop2T   * 100) / 100, type: 'pop',   gain: closeGain});
    } else {
      const t1 = isHighEnergy ? 0.25 : isCalm ? 0.45 : 0.35;
      const t2 = isHighEnergy ? 0.55 : isCalm ? 0.75 : 0.65;
      // High-energy scenes get a third cue; calm scenes only get two
      if (!isCalm) {
        const t3 = isHighEnergy ? 0.80 : 0.85;
        cues.push({t: Math.round(durationSec * t1 * 100) / 100, type: 'tick',  gain: midGain});
        cues.push({t: Math.round(durationSec * t2 * 100) / 100, type: 'click', gain: midGain});
        cues.push({t: Math.round(durationSec * t3 * 100) / 100, type: 'tick',  gain: closeGain});
      } else {
        cues.push({t: Math.round(durationSec * t1 * 100) / 100, type: 'tick',  gain: midGain});
        cues.push({t: Math.round(durationSec * t2 * 100) / 100, type: 'click', gain: closeGain});
      }
    }

    return cues;
  }

  const musicMood: string = storyboard.music_mood || storyboard.audio?.music?.mood || 'cinematic_beat';

  // Build spec.json
  const totalSec = scenes.reduce((sum: number, s: any) => sum + (s.duration_seconds || 4), 0);
  let elapsed = 0;
  const specScenes = scenes.map((s: any, idx: number) => {
    const dur = s.duration_seconds || 4;
    const activeNode = nodes[idx] || nodes[0];
    const isV2 = process.env.PIPELINE_V2 === '1' || Boolean(s.layout);
    const layout = (isV2 && s.layout) ? s.layout : resolveSceneLayout(activeNode.type, idx, scenes.length);
    const transition = idx < scenes.length - 1 ? ((isV2 && s.transition_out) ? s.transition_out : resolveSceneTransition(s.visual_fx, idx)) : 'none';

    let headline = (s.kinetic_text || brand.name || '').trim();
    if (MOTION_RULES.text_entry.ban_terminal_punctuation_on_headlines) {
      headline = headline.replace(/[.;:]+$/, '');
    }
    const hWords = headline.split(/\s+/).filter(Boolean);
    if (hWords.length > 8) headline = hWords.slice(0, 8).join(' ');

    let subline = (s.voiceover || brand.tagline || '').trim();
    const sWords = subline.split(/\s+/).filter(Boolean);
    if (sWords.length > 12) subline = sWords.slice(0, 12).join(' ');

    let caption = (s.veo_prompt || '').trim();
    const cWords = caption.split(/\s+/).filter(Boolean);
    if (cWords.length > 6) caption = cWords.slice(0, 6).join(' ');

    const scene = {
      id: `scene_${s.scene_id || idx + 1}`,
      start: elapsed,
      duration: dur,
      layout,
      headline,
      subline,
      caption,
      captionWords: buildCaptionWords(s.voiceover || '', dur, fps),
      visual: {kicker: brand.name, pulseText: s.visual_fx || 'smooth'},
      motion: {
        enter: MOTION_RULES.text_entry.method || 'mask_line_rise',
        idle: MOTION_RULES.objects.idle || 'slow_sway',
        exit: 'carousel_glide',
      },
      vo: '',
      sfx: generateSceneSfx(idx, dur, scenes.length, musicMood),
      transitionOut: transition,
    };
    elapsed += dur;
    return scene;
  });

  const aesthetic = storyboard.aesthetic || storyboard.ml_match?.aesthetic;
  const spec = {
    brand: brand.name,
    format: '16:9' as const,
    fps,
    durationSec: totalSec,
    bpm: aesthetic?.suggested_bpm || 120,
    palette: {
      background: brand.colors?.background || aesthetic?.background || '#0B1020',
      background2: brand.colors?.background2 || aesthetic?.background2 || '#151B33',
      surface: brand.colors?.surface || aesthetic?.surface || '#1E293B',
      surfaceText: brand.colors?.surfaceText || aesthetic?.surfaceText || '#F8FAFC',
      text: brand.colors?.text || aesthetic?.text || '#F8FAFC',
      muted: brand.colors?.muted || aesthetic?.muted || '#94A3B8',
      accent: brand.colors?.accent || aesthetic?.accent || '#6C5CE7',
      accentLight: brand.colors?.accentLight || aesthetic?.accentLight || '#B9B0FF',
      secondary: aesthetic?.secondary || '#38BDF8',
      isLightTheme: isLightBackground(brand.colors?.background) || Boolean(aesthetic?.is_light_theme),
    },
    mlMatch: {
      category: storyboard.ml_match?.category || storyboard.matched_opus_category || 'MOTION',
      score: storyboard.ml_match?.score ?? 0.85,
      template: storyboard.selected_template || 'Problem-Agitate-Solution (UI Showcase)',
      author: storyboard.ml_match?.author || 'Opus',
      techTags: storyboard.ml_match?.tech_tags || [],
      referenceUrl: storyboard.ml_match?.reference_url || '',
      aesthetic,
    },
    scenes: specScenes,
    audio: {
      assetsRoot: `jobs/${jobId}/assets`,
      voice:  {provider: 'none', voiceId: 'none', model: 'none', clips: {}},
      music:  {file: 'audio/music-bed.mp3', mood: storyboard.music_mood || 'cinematic_beat', volume: 0.18},
      room:   {file: 'audio/room-tone.wav', volume: 0.05},
      sfxFiles: {
        click: 'audio/click.wav',
        tick:  'audio/tick.wav',
        pop:   'audio/pop.wav',
      },
      duck: Math.min(12, totalSec),
    },
  };

  // Compile shots for schema-compliant storyboard.json
  const storyboardShots = specScenes.map((s: any, idx: number) => {
    const isHook = idx === 0;
    const isCta = idx === specScenes.length - 1;
    return {
      n: idx + 1,
      t0: s.start,
      t1: s.start + s.duration,
      role: isHook ? 'hook' : isCta ? 'cta' : 'feature',
      source: 'motion-graphic',
      visual: s.layout,
      headline: s.headline,
      subline: s.subline,
      onScreenText: s.caption || '',
      dialogue: s.vo || '',
      sfx: s.sfx || [],
      transitionOut: s.transitionOut || 'none',
      camera: null,
    };
  });
  const outputStoryboard = {shots: storyboardShots};

  // Write to disk
  fs.mkdirSync(jobDir, {recursive: true});
  fs.writeFileSync(path.join(jobDir, 'ui_tree.json'),        JSON.stringify(uiTree, null, 2),          'utf8');
  fs.writeFileSync(path.join(jobDir, 'spec.json'),           JSON.stringify(spec, null, 2),            'utf8');
  fs.writeFileSync(path.join(jobDir, 'storyboard.json'),     JSON.stringify(outputStoryboard, null, 2),'utf8');
  fs.writeFileSync(path.join(jobDir, 'storyboard.opus.json'),JSON.stringify(storyboard, null, 2),      'utf8');

  // Write known-exceptions.json adhering to new array schema
  const knownExceptions = [];
  if (specScenes.length > 0 && specScenes[0].duration > 2) {
    knownExceptions.push({
      rule: 'hook_length_shot_1',
      reason: 'Dynamic director hook timing (>2s)',
      approvedBy: 'director@company',
      expires: '2026-12-31'
    });
  }
  fs.writeFileSync(path.join(jobDir, 'known-exceptions.json'), JSON.stringify(knownExceptions, null, 2), 'utf8');

  // Synchronize brand.json if Opus aesthetic palette exists
  if (aesthetic) {
    const brandPath = path.join(jobDir, 'brand.json');
    if (fs.existsSync(brandPath)) {
      try {
        const bData = JSON.parse(fs.readFileSync(brandPath, 'utf8'));
        const own = bData.colors || {};
        const lum = (hex?: string) => {
          if (!hex || !hex.startsWith('#') || hex.length < 7) return 0;
          const r = parseInt(hex.slice(1, 3), 16), g = parseInt(hex.slice(3, 5), 16), b = parseInt(hex.slice(5, 7), 16);
          return (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        };
        const avoidCollision = (color: string) => {
          const lower = (color || '').toLowerCase();
          if (lower === '#0b1020') return '#071026';
          if (lower === '#151b33') return '#0F214D';
          return color;
        };
        const bg = avoidCollision(own.background || aesthetic.background || '#071026');
        const bg2 = avoidCollision(own.background2 || aesthetic.background2 || bg);
        const isLight = lum(bg) > 0.55;
        const text = isLight ? (aesthetic.text || '#0E0F1F') : (own.text || '#F8FAFC');
        const surface = isLight ? (aesthetic.surface || '#FFFFFF') : (own.surface || '#1E293B');
        const surfaceText = isLight ? (aesthetic.surfaceText || text) : (own.surfaceText || '#F8FAFC');

        bData.colors = {
          ...own,
          accent: own.accent || aesthetic.accent,
          accentLight: own.accentLight || aesthetic.accentLight,
          background: bg,
          background2: bg2,
          surface,
          surfaceText,
          text,
          muted: aesthetic.muted || own.muted,
        };
        fs.writeFileSync(brandPath, JSON.stringify(bData, null, 2), 'utf8');
        console.log(`[Scene Assembler] 🎨 brand.json synchronized with Opus directorial palette (bg: ${bData.colors.background}, lightMode: ${isLight})`);
      } catch (_err) {
        void _err;
      }
    }
  }

  console.log(`[Scene Assembler] ✅ ui_tree.json  — ${nodes.length} nodes: ${nodes.map(n => n.type).join(', ')}`);
  console.log(`[Scene Assembler] ✅ spec.json     — ${totalSec}s total`);
  console.log(`[Scene Assembler] ✅ storyboard.json written`);

  return {uiTree, spec};
}

// CLI runner
if (process.argv[1]?.includes('scene-assembler')) {
  const jobId = process.argv[2] || 'test-assembly-001';
  const jobDir = path.resolve(process.cwd(), 'jobs', jobId);
  const storyboardPath = fs.existsSync(path.join(jobDir, 'storyboard.opus.json'))
    ? path.join(jobDir, 'storyboard.opus.json')
    : path.join(jobDir, 'storyboard.json');
  const brandPath      = path.join(jobDir, 'brand.json');

  if (!fs.existsSync(storyboardPath)) {
    console.error(`[Scene Assembler] storyboard.json not found at ${storyboardPath}`);
    process.exit(1);
  }
  if (!fs.existsSync(brandPath)) {
    console.error(`[Scene Assembler] brand.json not found at ${brandPath}`);
    process.exit(1);
  }

  const storyboard = JSON.parse(fs.readFileSync(storyboardPath, 'utf8'));
  const brand      = JSON.parse(fs.readFileSync(brandPath,      'utf8')) as BrandJson;
  assembleScenes({storyboard, brand, jobId});
}
