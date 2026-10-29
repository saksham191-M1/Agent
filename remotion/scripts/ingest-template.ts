import {mkdirSync, writeFileSync, readFileSync, existsSync, cpSync, readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {generateJobRegistry} from './job-discovery';

export type TemplateSource = 'remotion-dev' | 'rendervid' | 'cinematic' | 'universal';

export interface IngestTemplateOptions {
  source?: TemplateSource;
  inputPath?: string;
  payload?: any;
  jobId: string;
}

export function detectTemplateSource(payload: any): TemplateSource {
  if (payload.appDescriptor || payload.sidebarItems || payload.cursorPath) {
    return 'cinematic';
  }
  if (payload.templateVariables || payload.category || payload.templateId) {
    return 'rendervid';
  }
  if (payload.skills || payload.charts || payload.messaging || payload.typography) {
    return 'remotion-dev';
  }
  return 'universal';
}

export function ingestTemplate(options: IngestTemplateOptions): {jobId: string; jobDir: string} {
  const root = process.cwd();
  const {jobId} = options;
  const jobDir = resolve(root, 'jobs', jobId);

  let rawPayload = options.payload;
  if (!rawPayload && options.inputPath) {
    const fullPath = resolve(root, options.inputPath);
    if (!existsSync(fullPath)) {
      throw new Error(`Input template file not found: ${fullPath}`);
    }
    rawPayload = JSON.parse(readFileSync(fullPath, 'utf8'));
  }

  if (!rawPayload) {
    throw new Error('Either payload or inputPath must be provided.');
  }

  const source = options.source || detectTemplateSource(rawPayload);
  mkdirSync(jobDir, {recursive: true});
  mkdirSync(resolve(jobDir, 'scenes'), {recursive: true});
  mkdirSync(resolve(jobDir, 'assets'), {recursive: true});
  const targetLogo = resolve(jobDir, 'assets', 'logo.png');
  if (!existsSync(targetLogo)) {
    const candidateLogos = [
      resolve(root, 'public', 'logo.png'),
      ...readdirSync(resolve(root, 'jobs'), {withFileTypes: true})
        .filter((d: any) => d.isDirectory())
        .map((d: any) => resolve(root, 'jobs', d.name, 'assets', 'logo.png'))
    ];
    const foundLogo = candidateLogos.find(existsSync);
    if (foundLogo) {
      try {
        const {copyFileSync} = require('node:fs');
        copyFileSync(foundLogo, targetLogo);
      } catch (_err) {
        void _err;
      }
    }
  }

  const targetAudio = resolve(jobDir, 'assets', 'audio');
  if (!existsSync(targetAudio)) {
    const candidateAudio = [
      resolve(root, 'public', 'audio'),
      ...readdirSync(resolve(root, 'jobs'), {withFileTypes: true})
        .filter((d: any) => d.isDirectory())
        .map((d: any) => resolve(root, 'jobs', d.name, 'assets', 'audio'))
    ];
    const foundAudio = candidateAudio.find(d => existsSync(d) && existsSync(resolve(d, 'room-tone.wav')));
    if (foundAudio) {
      try {
        cpSync(foundAudio, targetAudio, {recursive: true});
      } catch (_err) {
        void _err;
      }
    }
  }

  // 1. Compile Brand JSON
  const brandName = rawPayload.brandName || rawPayload.appName || rawPayload.title || 'SaaS Dynamics';
  const accentColor =
    rawPayload.colors?.accent ||
    rawPayload.accentColor ||
    rawPayload.theme?.primary ||
    '#6366F1';

  const brandJson = {
    name: brandName,
    domain: rawPayload.domain || `${brandName.toLowerCase().replace(/\s+/g, '')}.io`,
    tagline: rawPayload.tagline || 'Intelligent Automation for Modern Teams',
    description: rawPayload.description || 'Enterprise-grade SaaS workflow automation platform.',
    products: rawPayload.products || ['Autonomous Workflows', 'Dynamic Telemetry', 'AI Agent Grid'],
    logo: {
      src: rawPayload.logoUrl || `jobs/${jobId}/assets/logo.png`,
      text: brandName,
      alt: `${brandName} Logo`,
      source: 'https://example.com',
    },
    colors: {
      accent: accentColor,
      accentLight: rawPayload.colors?.accentLight || '#818CF8',
      background: rawPayload.colors?.background || '#090D16',
      background2: rawPayload.colors?.background2 || '#111827',
      text: rawPayload.colors?.text || '#F9FAFB',
      muted: rawPayload.colors?.muted || '#9CA3AF',
      surface: rawPayload.colors?.surface || '#161E2E',
      surfaceText: '#F9FAFB',
      surfaceMuted: '#6B7280',
    },
    fonts: {
      display: {family: 'Inter', source: 'Google Fonts'},
      body: {family: 'Inter', source: 'Google Fonts'},
    },
    imagery: [],
    claims: [
      {
        id: 'claim_perf',
        label: 'Performance',
        value: 'Enterprise Grade',
        sourceUrl: 'https://example.com',
      },
    ],
  };

  // 2. Compile UI Tree based on Source
  const uiNodes: any[] = [];

  if (source === 'remotion-dev') {
    // Official Remotion SaaS Template Skills
    uiNodes.push({
      id: 'skill-typo-hero',
      type: 'kinetic_typography',
      effect: 'word_carousel',
      words: rawPayload.typography?.words || ['Automate.', 'Accelerate.', 'Dominate.'],
      subtext: rawPayload.typography?.subtext || 'The Autonomous SaaS Platform',
      fontSize: 68,
      position3D: [0, 0, 0],
    });

    uiNodes.push({
      id: 'skill-chart-metric',
      type: 'chart',
      chartType: rawPayload.charts?.chartType || 'bar',
      title: rawPayload.charts?.title || 'Monthly Active Workflows',
      data: rawPayload.charts?.data || [
        {label: 'Jan', value: 340},
        {label: 'Feb', value: 680},
        {label: 'Mar', value: 1120},
        {label: 'Apr', value: 1850},
        {label: 'May', value: 2940},
      ],
      accentColor,
      position3D: [0, 0, 0],
    });

    uiNodes.push({
      id: 'skill-chat-feed',
      type: 'chat_messaging',
      messages: rawPayload.messaging?.messages || [
        {id: 'm1', sender: 'user', text: 'Optimize latency for our EU clusters.', time: '09:12 AM'},
        {id: 'm2', sender: 'agent', text: 'Rerouting global traffic through edge caches.', time: '09:12 AM'},
        {id: 'm3', sender: 'agent', text: 'Latency reduced by -64ms across 12 regions.', time: '09:13 AM'},
      ],
      typingIndicator: true,
      position3D: [0, 0, 0],
    });
  } else if (source === 'rendervid') {
    // Rendervid Catalog JSON-in format
    const vars = rawPayload.templateVariables || rawPayload;
    uiNodes.push({
      id: 'rv-pill',
      type: 'pill_tag',
      text: vars.badge || vars.category || 'Data Engine V2',
      variant: 'glass',
      accent: accentColor,
      position3D: [0, 0, 0],
    });

    uiNodes.push({
      id: 'rv-chart',
      type: 'chart',
      chartType: vars.chartType || 'area',
      title: vars.chartTitle || 'Quarterly Performance Surge',
      data: vars.chartData || [
        {label: 'Q1', value: 120},
        {label: 'Q2', value: 280},
        {label: 'Q3', value: 590},
        {label: 'Q4', value: 940},
      ],
      accentColor,
      position3D: [0, 0, 0],
    });

    uiNodes.push({
      id: 'rv-card-kpi',
      type: 'metric_card',
      label: vars.kpiLabel || 'Gross Volume Processed',
      value: vars.kpiValue || '$42.8M',
      delta: vars.kpiDelta || '+184%',
      chartPoints: [30, 45, 60, 95, 140, 190],
      accentColor,
      position3D: [0, 0, 0],
    });
  } else if (source === 'cinematic') {
    // Codeverbojan Cinematic Remotion Engine
    const desc = rawPayload.appDescriptor || rawPayload;
    uiNodes.push({
      id: 'cinematic-frame',
      type: 'app_frame',
      appName: desc.appName || brandName,
      topbarTitle: desc.topbarTitle || 'Performance Studio',
      badgeText: desc.badgeText || 'Live Production',
      sidebarItems: desc.sidebarItems || [
        {id: 'overview', label: 'Overview', active: true},
        {id: 'analytics', label: 'Analytics', active: false},
        {id: 'pipelines', label: 'Pipelines', active: false},
        {id: 'security', label: 'Security', active: false},
      ],
      position3D: [0, 0, 0],
    });

    uiNodes.push({
      id: 'cinematic-metric',
      type: 'metric_card',
      label: 'Edge Compute Latency',
      value: '4.2 ms',
      delta: '-58% p99',
      chartPoints: [45, 38, 26, 18, 12, 4],
      accentColor,
      position3D: [0, 0, 0],
    });
  } else {
    // Universal Unified Engine
    uiNodes.push({
      id: 'univ-frame',
      type: 'app_frame',
      appName: brandName,
      topbarTitle: 'Autonomous Dashboard',
      badgeText: 'Verified',
      sidebarItems: [
        {id: 'dash', label: 'Dashboard', active: true},
        {id: 'models', label: 'Models', active: false},
        {id: 'logs', label: 'Audit Logs', active: false},
      ],
      position3D: [0, 0, 0],
    });

    uiNodes.push({
      id: 'univ-chart',
      type: 'chart',
      chartType: 'area',
      title: 'Neural Inference Throughput',
      data: [
        {label: 'Mon', value: 80},
        {label: 'Tue', value: 140},
        {label: 'Wed', value: 230},
        {label: 'Thu', value: 410},
        {label: 'Fri', value: 680},
      ],
      accentColor,
      position3D: [0, 0, 0],
    });

    uiNodes.push({
      id: 'univ-chat',
      type: 'chat_messaging',
      messages: [
        {id: 'm1', sender: 'user', text: 'Deploy model across 4 global regions.', time: '11:00 AM'},
        {id: 'm2', sender: 'agent', text: 'Deploying with zero downtime.', time: '11:00 AM'},
        {id: 'm3', sender: 'agent', text: 'All regions live. Health checks: 100% OK.', time: '11:01 AM'},
      ],
      typingIndicator: true,
      position3D: [0, 0, 0],
    });
  }

  const uiTreeJson = {
    brandId: jobId,
    worldBounds: {width: 1920, height: 1080, depth: 1000},
    nodes: uiNodes,
  };

  // 3. Compile Ad Spec (Validates with spec.schema.json & contiguous duration)
  const durationSec = rawPayload.durationSec || 10;
  const fps = rawPayload.fps || 30;

  const specJson = {
    brand: jobId,
    format: '16:9',
    fps,
    durationSec,
    bpm: 120,
    scenes: [
      {
        id: 'scene_hook',
        start: 0,
        duration: 2,
        layout: 'hero-type',
        headline: brandName,
        subline: 'Intelligent automation for modern teams.',
        caption: 'Next generation workflow automation',
        visual: {kicker: brandName, pulseText: 'Instant Acceleration'},
        motion: {enter: 'type-slam', idle: 'pulse-orbit', exit: 'push-through'},
        vo: '',
        sfx: [
          {t: 0.19, type: 'pop', gain: 0.85},
          {t: 1.80, type: 'tick', gain: 0.55},
        ],
        transitionOut: 'fade',
      },
      {
        id: 'scene_feature',
        start: 2,
        duration: 5,
        layout: 'browser',
        headline: 'Unified Telemetry and Insights',
        subline: 'Real-time metrics with autonomous agent supervision.',
        caption: 'High throughput data stream',
        visual: {kicker: 'Live Engine', pulseText: 'Operational Excellence'},
        motion: {enter: 'slide-up', idle: 'float', exit: 'zoom-in'},
        vo: '',
        sfx: [
          {t: 0.40, type: 'click', gain: 0.70},
          {t: 0.65, type: 'click', gain: 0.70},
          {t: 0.90, type: 'click', gain: 0.70},
          {t: 2.70, type: 'pop', gain: 0.85},
          {t: 4.10, type: 'tick', gain: 0.60},
          {t: 4.115, type: 'tick', gain: 0.60},
          {t: 4.13, type: 'tick', gain: 0.60},
        ],
        transitionOut: 'slide',
      },
      {
        id: 'scene_cta',
        start: 7,
        duration: 3,
        layout: 'cta',
        headline: 'Build Faster Today',
        subline: 'Start free with zero credit card.',
        caption: 'Experience the modern engine',
        visual: {kicker: brandName, pulseText: 'Get Started'},
        motion: {enter: 'scale-up', idle: 'pulse', exit: 'fade'},
        vo: '',
        sfx: [
          {t: 0.50, type: 'tick', gain: 0.55},
          {t: 1.50, type: 'pop', gain: 0.90},
        ],
        transitionOut: 'fade',
      },
    ],
    audio: {
      assetsRoot: `jobs/${jobId}/assets`,
      voice: {provider: 'elevenlabs', voiceId: 'none', model: 'none', clips: {}},
      music: {file: '', mood: 'none', volume: 0},
      room: {file: 'audio/room-tone.wav', volume: 0.85},
      sfxFiles: {
        click: 'audio/click.wav',
        tick: 'audio/tick.wav',
        pop: 'audio/pop.wav',
      },
      duck: 7,
    },
  };

  // 4. Compile Storyboard JSON (For schema & pipeline consistency)
  const storyboardJson = {
    shots: [
      {
        n: 1,
        t0: 0,
        t1: 2,
        role: 'hook',
        source: 'motion-graphic',
        visual: 'hero-type',
        headline: brandName,
        subline: 'Intelligent automation for modern teams.',
        onScreenText: 'Next generation workflow automation',
        transitionOut: 'fade',
        camera: null,
      },
      {
        n: 2,
        t0: 2,
        t1: 7,
        role: 'feature',
        source: 'screen-demo',
        visual: 'browser',
        headline: 'Unified Telemetry and Insights',
        subline: 'Real-time metrics with autonomous agent supervision.',
        onScreenText: 'High throughput data stream',
        transitionOut: 'slide',
        camera: null,
      },
      {
        n: 3,
        t0: 7,
        t1: 10,
        role: 'cta',
        source: 'motion-graphic',
        visual: 'cta',
        headline: 'Build Faster Today',
        subline: 'Start free with zero credit card.',
        onScreenText: 'Experience the modern engine',
        transitionOut: 'fade',
        camera: null,
      },
    ],
  };

  // 5. Generate Dynamic Scene Component (scenes/index.tsx)
  const sceneComponentTsx = `import React from 'react';
import {useCurrentFrame, useVideoConfig, spring, interpolate} from 'remotion';
import type {SceneRendererProps} from '../../../engine';
import {VectorRenderer} from '../../../engine/semantic-ui/VectorRenderer';
import type {UITree, VectorNode} from '../../../engine/semantic-ui/types';
import uiTreeData from '../ui_tree.json';

const SANS_FONT_STACK = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

const TemplateScene: React.FC<SceneRendererProps> = ({scene: _scene, tokens}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const tree = uiTreeData as unknown as UITree;
  const nodes = tree.nodes || [];

  // Smooth camera entrance spring
  const entrance = spring({
    frame,
    fps,
    config: {damping: 14, mass: 0.6},
  });

  const sceneProgress = frame / durationInFrames;
  const activeNodeIdx = Math.min(nodes.length - 1, Math.floor(sceneProgress * nodes.length));
  const activeNode = nodes[activeNodeIdx] as VectorNode;

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        backgroundColor: tokens.colors.background,
        backgroundImage: \`radial-gradient(circle at 50% 30%, \${tokens.colors.accent}18 0%, transparent 70%), radial-gradient(circle at 80% 80%, \${tokens.colors.background2} 0%, \${tokens.colors.background} 100%)\`,
        overflow: 'hidden',
        fontFamily: SANS_FONT_STACK,
      }}
    >
      {/* Background Grid Pattern */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: \`linear-gradient(to right, rgba(255, 255, 255, 0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 255, 255, 0.04) 1px, transparent 1px)\`,
          backgroundSize: '48px 48px',
          opacity: 0.6,
          pointerEvents: 'none',
        }}
      />

      {/* Primary Semantic Stage */}
      <div
        style={{
          transform: \`scale(\${interpolate(entrance, [0, 1], [0.92, 1])})\`,
          opacity: interpolate(entrance, [0, 1], [0, 1]),
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 28,
          zIndex: 10,
        }}
      >
        {activeNode && (
          <VectorRenderer
            node={activeNode}
            tokens={tokens}
            sheenProgress={sceneProgress}
          />
        )}
      </div>

      {/* Floating Accent Glow */}
      <div
        style={{
          position: 'absolute',
          width: 500,
          height: 500,
          borderRadius: '50%',
          backgroundColor: tokens.colors.accent,
          filter: 'blur(160px)',
          opacity: 0.12,
          pointerEvents: 'none',
          top: '20%',
          left: '35%',
        }}
      />
    </div>
  );
};

export default TemplateScene;
`;

  // Write all artifacts
  writeFileSync(resolve(jobDir, 'brand.json'), JSON.stringify(brandJson, null, 2), 'utf8');
  writeFileSync(resolve(jobDir, 'spec.json'), JSON.stringify(specJson, null, 2), 'utf8');
  writeFileSync(resolve(jobDir, 'ui_tree.json'), JSON.stringify(uiTreeJson, null, 2), 'utf8');
  writeFileSync(resolve(jobDir, 'storyboard.json'), JSON.stringify(storyboardJson, null, 2), 'utf8');
  writeFileSync(resolve(jobDir, 'known-exceptions.json'), JSON.stringify({}, null, 2), 'utf8');
  writeFileSync(resolve(jobDir, 'scenes', 'index.tsx'), sceneComponentTsx, 'utf8');

  // Regenerate job registry
  generateJobRegistry(root);

  return {jobId, jobDir};
}

// CLI Execution Support
if (process.argv[1] && process.argv[1].includes('ingest-template')) {
  const args = process.argv.slice(2);
  let source: TemplateSource | undefined;
  let inputPath: string | undefined;
  let jobId = 'saas-template-demo';

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--source' && args[i + 1]) source = args[++i] as TemplateSource;
    else if (args[i] === '--input' && args[i + 1]) inputPath = args[++i];
    else if (args[i] === '--job' && args[i + 1]) jobId = args[++i];
  }

  // If no input file passed, generate a rich demonstration template showcasing all three integrated engines
  const payload = inputPath
    ? undefined
    : {
        brandName: 'OmniFlow AI',
        appName: 'OmniFlow Studio',
        accentColor: '#6366F1',
        tagline: 'Autonomous AI Orchestration at Planetary Scale',
        skills: {
          charts: true,
          typography: true,
          messaging: true,
        },
        charts: {
          chartType: 'area',
          title: 'Daily Agent Operations',
          data: [
            {label: 'Mon', value: 1200},
            {label: 'Tue', value: 2400},
            {label: 'Wed', value: 4100},
            {label: 'Thu', value: 6800},
            {label: 'Fri', value: 9500},
          ],
        },
        messaging: {
          messages: [
            {id: 'm1', sender: 'user', text: 'Synthesize user analytics and optimize throughput.', time: '10:00 AM'},
            {id: 'm2', sender: 'agent', text: 'Processing 4.2M events across distributed clusters.', time: '10:00 AM'},
            {id: 'm3', sender: 'agent', text: 'Optimization complete: P99 latency dropped to 4.2ms.', time: '10:01 AM'},
          ],
        },
      };

  console.log(`Ingesting template (source: ${source || 'auto-detect'}, job: ${jobId})...`);
  const result = ingestTemplate({source, inputPath, payload, jobId});
  console.log(`Successfully ingested template to ${result.jobDir}!`);
}
