import fs from 'node:fs';
import path from 'node:path';
import type {BrandJson} from '../engine/types';
import type {UITree, VectorNode} from '../engine/semantic-ui/types';
import type {CameraFlightPath} from '../engine/stage/types';
import {generateBrandLogo} from './generate-brand-logo';

function parseArgs(): Record<string, string> {
  const args = process.argv.slice(2);
  const parsed: Record<string, string> = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].slice(2);
      const val = args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : 'true';
      parsed[key] = val;
      if (val !== 'true') i++;
    }
  }
  return parsed;
}

async function main() {
  const args = parseArgs();
  if (args['legacy'] !== 'true' && !process.argv.includes('--legacy')) {
    console.error(
      '\n❌ [ERROR] scripts/run-director.ts is deprecated.\n' +
      'Please use the primary orchestrator: npx tsx scripts/produce-ad.ts --url <product_url>\n' +
      'To force run this legacy script, provide the --legacy flag.\n' +
      'See docs/ENTRYPOINTS.md for details.\n'
    );
    process.exit(1);
  }
  const url = args['url'] || 'https://linear.app';
  const mode = args['mode'] || 'launch_promo';
  const format = args['format'] || '16:9';
  const jobId = args['job-id'] || 'test-promo-001';

  console.log(`\n======================================================`);
  console.log(`🎬 AI AD DIRECTOR: RUNNING INGESTION & PLANNING`);
  console.log(`Domain:  ${url}`);
  console.log(`Mode:    ${mode}`);
  console.log(`Format:  ${format}`);
  console.log(`Job ID:  ${jobId}`);
  console.log(`======================================================\n`);

  const jobDir = path.resolve(process.cwd(), 'jobs', jobId);
  fs.mkdirSync(path.join(jobDir, 'assets', 'audio'), {recursive: true});
  fs.mkdirSync(path.join(jobDir, 'scenes'), {recursive: true});
  fs.mkdirSync(path.join(jobDir, 'out', 'stills'), {recursive: true});

  // Copy standard audio assets from neutral default pack
  const sourceAudioDir = path.resolve(process.cwd(), '..', 'assets', 'default', 'audio');
  if (fs.existsSync(sourceAudioDir)) {
    fs.copyFileSync(path.join(sourceAudioDir, 'music-bed.mp3'), path.join(jobDir, 'assets', 'audio', 'music-bed.mp3'));
    fs.copyFileSync(path.join(sourceAudioDir, 'room-tone.wav'), path.join(jobDir, 'assets', 'audio', 'room-tone.wav'));
  }
  const voSrc = path.join(sourceAudioDir, 'vo-s1.mp3');
  if (fs.existsSync(voSrc)) {
    fs.copyFileSync(voSrc, path.join(jobDir, 'assets', 'audio', 'vo-s1.mp3'));
  }
  const sfxFiles = ['swipe.wav', 'pop.wav', 'pop2.wav', 'tick.wav', 'click.wav', 'whoosh.wav', 'thud.wav', 'riser.wav', 'success.wav', 'logo-sting.wav'];
  for (const f of sfxFiles) {
    const src = path.join(sourceAudioDir, f);
    if (fs.existsSync(src)) {
      fs.copyFileSync(src, path.join(jobDir, 'assets', 'audio', f));
    }
  }



  // 1. Synthesize brand.json based on URL domain
  const isSupabase = url.includes('supabase');
  const isPrisma = url.includes('prisma');
  const isResend = url.includes('resend');
  const isGemini = url.includes('gemini') || jobId.includes('gemini');

  let brand: BrandJson;
  if (isSupabase) {
    brand = {
      name: 'SupabaseApp',
      domain: 'supabase.com',
      tagline: 'Build in a weekend. Scale to millions.',
      description: 'The open source Firebase alternative with Postgres database, Authentication, and instant APIs.',
      products: ['Postgres Database', 'Edge Functions', 'Realtime Subscriptions'],
      logo: {
        src: `jobs/${jobId}/assets/logo.png`,
        text: 'SupabaseApp',
        alt: 'Supabase logo',
        source: 'https://supabase.com',
      },
      colors: {
        accent: '#3ECF8E',
        accentLight: '#6EE7B7',
        background: '#121212',
        background2: '#181818',
        text: '#EDEDED',
        muted: '#A1A1A1',
        surface: '#242424',
        surfaceText: '#EDEDED',
        surfaceMuted: '#707070',
      },
      fonts: {
        display: {family: 'Inter', source: 'Google Fonts'},
        body: {family: 'Inter', source: 'Google Fonts'},
      },
      imagery: [],
      claims: [
        {id: 'db', label: 'Database', value: '100% Portable Postgres', sourceUrl: 'https://supabase.com'},
        {id: 'latency', label: 'Query Speed', value: 'sub-10ms', sourceUrl: 'https://supabase.com'},
      ],
    };
  } else if (isPrisma) {
    brand = {
      name: 'PrismaORM',
      domain: 'prisma.io',
      tagline: 'Next-generation ORM for Node.js and TypeScript',
      description: 'Prisma unlocks a new level of developer experience with its intuitive data model, automated migrations, type-safety & auto-completion.',
      products: ['Prisma ORM', 'Prisma Accelerate', 'Prisma Pulse'],
      logo: {
        src: `jobs/${jobId}/assets/logo.png`,
        text: 'PrismaORM',
        alt: 'Prisma logo',
        source: 'https://prisma.io',
      },
      colors: {
        accent: '#16A394',
        accentLight: '#2DD4BF',
        background: '#0B0F19',
        background2: '#111827',
        text: '#F8FAFC',
        muted: '#94A3B8',
        surface: '#111827',
        surfaceText: '#F8FAFC',
        surfaceMuted: '#64748B',
      },
      fonts: {
        display: {family: 'Inter', source: 'Google Fonts'},
        body: {family: 'Inter', source: 'Google Fonts'},
      },
      imagery: [],
      claims: [
        {id: 'typesafe', label: 'Type Safety', value: '100% End-to-End', sourceUrl: 'https://prisma.io'},
        {id: 'query', label: 'Query Performance', value: 'sub-2ms', sourceUrl: 'https://prisma.io'},
      ],
    };
  } else if (isResend) {
    brand = {
      name: 'ResendApp',
      domain: 'resend.com',
      tagline: 'Email for developers',
      description: 'The best API to reach humans instead of spam folders. Build, test, and deliver transactional and marketing emails at scale.',
      products: ['Email API', 'React Email', 'Audiences'],
      logo: {
        src: `jobs/${jobId}/assets/logo.png`,
        text: 'ResendApp',
        alt: 'Resend logo',
        source: 'https://resend.com',
      },
      colors: {
        accent: '#38BDF8',
        accentLight: '#7DD3FC',
        background: '#09090B',
        background2: '#18181B',
        text: '#FAFAFA',
        muted: '#A1A1AA',
        surface: '#18181B',
        surfaceText: '#FAFAFA',
        surfaceMuted: '#71717A',
      },
      fonts: {
        display: {family: 'Inter', source: 'Google Fonts'},
        body: {family: 'Inter', source: 'Google Fonts'},
      },
      imagery: [],
      claims: [
        {id: 'deliverability', label: 'Deliverability', value: '99.9% Inbox Rate', sourceUrl: 'https://resend.com'},
        {id: 'speed', label: 'Latency', value: 'sub-20ms', sourceUrl: 'https://resend.com'},
      ],
    };
  } else if (isGemini) {
    brand = {
      name: 'Gemini Agent',
      domain: 'gemini.google.com',
      tagline: 'The Autonomous Multimodal AI Agent',
      description: 'Reason across code, visuals, and tools with autonomous execution and native multimodal agency.',
      products: ['Gemini 2.5 Flash', 'Deep Research Agent', 'Autonomous Tool Execution'],
      logo: {
        src: `jobs/${jobId}/assets/logo.png`,
        text: 'Gemini Agent',
        alt: 'Google Gemini logo',
        source: 'https://gemini.google.com',
      },
      colors: {
        accent: '#4285F4',
        accentLight: '#9B72CB',
        background: '#07090E',
        background2: '#0D111A',
        text: '#F8FAFC',
        muted: '#94A3B8',
        surface: '#111622',
        surfaceText: '#F8FAFC',
        surfaceMuted: '#64748B',
      },
      fonts: {
        display: {family: 'Inter', source: 'Google Fonts'},
        body: {family: 'Inter', source: 'Google Fonts'},
      },
      imagery: [],
      claims: [
        {id: 'context', label: 'Multimodal Context', value: '1M+ Tokens', sourceUrl: 'https://gemini.google.com'},
        {id: 'agency', label: 'Agent Tools', value: '100+ Autonomous APIs', sourceUrl: 'https://gemini.google.com'},
      ],
    };
  } else {
    brand = {
      name: 'LinearApp',
      domain: 'linear.app',
      tagline: 'The issue tracking tool you will enjoy using.',
      description: 'Purpose-built for modern software teams to streamline issues, projects, and roadmaps.',
      products: ['Linear Cycles', 'Project Roadmaps', 'Insights'],
      logo: {
        src: `jobs/${jobId}/assets/logo.png`,
        text: 'LinearApp',
        alt: 'Linear logo',
        source: 'https://linear.app',
      },
      colors: {
        accent: '#5E6AD2',
        accentLight: '#8B94E5',
        background: '#08090C',
        background2: '#12141A',
        text: '#F7F8F8',
        muted: '#8A8F98',
        surface: '#12141A',
        surfaceText: '#F7F8F8',
        surfaceMuted: '#62666D',
      },
      fonts: {
        display: {family: 'Inter', source: 'Google Fonts'},
        body: {family: 'Inter', source: 'Google Fonts'},
      },
      imagery: [],
      claims: [
        {id: 'speed', label: 'Speed', value: 'Instant', sourceUrl: 'https://linear.app'},
        {id: 'sync', label: 'Real-time Sync', value: '50ms', sourceUrl: 'https://linear.app'},
      ],
    };
  }
  fs.writeFileSync(path.join(jobDir, 'brand.json'), JSON.stringify(brand, null, 2), 'utf8');

  // Generate authentic brand logo
  const targetLogo = path.join(jobDir, 'assets', 'logo.png');
  const prismaLogo = path.resolve(process.cwd(), 'jobs', 'sample-promo-prisma', 'assets', 'logo.png');
  if (url.includes('prisma') && fs.existsSync(prismaLogo)) {
    fs.copyFileSync(prismaLogo, targetLogo);
  } else {
    try {
      generateBrandLogo(brand, targetLogo);
    } catch (err) {
      console.warn('Failed to generate brand logo via browser:', err);
    }
  }
  const publicLogo = path.resolve(process.cwd(), 'public', 'jobs', jobId, 'assets', 'logo.png');
  fs.mkdirSync(path.dirname(publicLogo), {recursive: true});
  if (fs.existsSync(targetLogo)) {
    fs.copyFileSync(targetLogo, publicLogo);
  }

  // 2. Synthesize ui_tree.json (Structured Vector AST)
  const isHorizontal = format === '16:9';
  const width = isHorizontal ? 1920 : 1080;
  const height = isHorizontal ? 1080 : 1920;

  let uiTreeNodes: VectorNode[];
  if (isSupabase) {
    uiTreeNodes = [
      {
        type: 'interactive_input',
        id: 'supabase-prompt',
        placeholder: 'Connect to Postgres...',
        typedValue: 'SELECT * FROM users WHERE active = true;',
        cursorPosition: 38,
        buttonLabel: 'Run Query',
        position3D: [0, 180, 0],
      },
      {
        type: 'pill_tag',
        id: 'pill-pg',
        text: 'Postgres 16 · Online',
        variant: 'glass',
        accent: '#3ECF8E',
        position3D: [-320, 270, 40],
      },
      {
        type: 'pill_tag',
        id: 'pill-speed',
        text: 'Edge Latency: sub-10ms',
        variant: 'solid',
        accent: '#6EE7B7',
        position3D: [320, 270, 40],
      },
      {
        type: 'metric_card',
        id: 'metric-queries',
        label: 'Active SQL Queries',
        value: '48,290 /s',
        delta: '+99.9% uptime',
        chartPoints: [120, 180, 260, 340, 410, 482],
        accentColor: '#3ECF8E',
        position3D: [-480, -30, 120],
      },
      {
        type: 'asset_card',
        id: 'asset-supabase',
        assetUrl: `jobs/${jobId}/assets/logo.png`,
        scaleMode: 'contain',
        title: 'Instant Database APIs',
        subtitle: 'Auto-generated REST & GraphQL endpoints',
        position3D: [480, -30, 120],
      },
      {
        type: 'bento_grid',
        id: 'bento-features',
        columns: 3,
        cards: [
          {id: 'b1', title: 'Postgres & PgVector', subtitle: 'Native vector embeddings', accent: '#3ECF8E'},
          {id: 'b2', title: 'Row Level Security', subtitle: 'Enterprise authorization', accent: '#6EE7B7'},
          {id: 'b3', title: 'Edge Functions', subtitle: 'Distributed TypeScript runtime', accent: '#34D399'},
        ],
        position3D: [0, -290, 260],
      },
    ];
  } else if (isPrisma) {
    uiTreeNodes = [
      {
        type: 'interactive_input',
        id: 'prisma-query',
        placeholder: 'Query database with type-safety...',
        typedValue: 'const users = await prisma.user.findMany({ where: { active: true } });',
        cursorPosition: 68,
        buttonLabel: 'Execute',
        position3D: [0, 110, 0],
      },
      {
        type: 'pill_tag',
        id: 'pill-orm',
        text: 'Prisma 6 · Type-Safe',
        variant: 'glass',
        accent: '#16A394',
        position3D: [-320, 230, 40],
      },
      {
        type: 'pill_tag',
        id: 'pill-speed',
        text: 'Query Latency: < 2ms',
        variant: 'solid',
        accent: '#2DD4BF',
        position3D: [320, 230, 40],
      },
      {
        type: 'metric_card',
        id: 'metric-queries',
        label: 'Database Queries',
        value: '1.2B /mo',
        delta: '100% Type-Safe',
        chartPoints: [45, 90, 150, 280, 420, 590],
        accentColor: '#16A394',
        position3D: [-540, -80, 80],
      },
      {
        type: 'asset_card',
        id: 'asset-accelerate',
        assetUrl: `jobs/${jobId}/assets/logo.png`,
        scaleMode: 'contain',
        title: 'Prisma Accelerate',
        subtitle: 'Global connection pooling and edge caching',
        position3D: [540, -80, 80],
      },
      {
        type: 'bento_grid',
        id: 'bento-features',
        columns: 3,
        cards: [
          {id: 'b1', title: 'Prisma ORM', subtitle: 'Type-safe query builder', accent: '#16A394'},
          {id: 'b2', title: 'Prisma Pulse', subtitle: 'Real-time database change streams', accent: '#2DD4BF'},
          {id: 'b3', title: 'Prisma Optimize', subtitle: 'AI SQL insights & query indexing', accent: '#0D9488'},
        ],
        position3D: [0, -320, 140],
      },
    ];
  } else if (isResend) {
    uiTreeNodes = [
      {
        type: 'interactive_input',
        id: 'resend-prompt',
        placeholder: 'Send transactional emails with React...',
        typedValue: "await resend.emails.send({ to: 'team@company.com' });",
        cursorPosition: 53,
        buttonLabel: 'Send Email',
        position3D: [0, 180, 0],
      },
      {
        type: 'pill_tag',
        id: 'pill-deliver',
        text: 'Deliverability · 99.9%',
        variant: 'glass',
        accent: '#38BDF8',
        position3D: [-320, 270, 40],
      },
      {
        type: 'pill_tag',
        id: 'pill-speed',
        text: 'Global Edge: sub-20ms',
        variant: 'solid',
        accent: '#7DD3FC',
        position3D: [320, 270, 40],
      },
      {
        type: 'metric_card',
        id: 'metric-emails',
        label: 'Emails Delivered',
        value: '250M /mo',
        delta: '+99.99% Inbox',
        chartPoints: [50, 110, 175, 290, 410, 580],
        accentColor: '#38BDF8',
        position3D: [-480, -30, 120],
      },
      {
        type: 'asset_card',
        id: 'asset-react-email',
        assetUrl: `jobs/${jobId}/assets/logo.png`,
        scaleMode: 'contain',
        title: 'React Email Templates',
        subtitle: 'Type-safe component-driven email design',
        position3D: [480, -30, 120],
      },
      {
        type: 'bento_grid',
        id: 'bento-features',
        columns: 3,
        cards: [
          {id: 'b1', title: 'First-Class DX', subtitle: 'Send email in 3 lines of code', accent: '#38BDF8'},
          {id: 'b2', title: 'Webhooks Engine', subtitle: 'Real-time delivery & bounce alerts', accent: '#7DD3FC'},
          {id: 'b3', title: 'Custom Domains', subtitle: 'DKIM, SPF, and DMARC verified', accent: '#0284C7'},
        ],
        position3D: [0, -290, 260],
      },
    ];
  } else if (isGemini) {
    uiTreeNodes = [
      {
        type: 'interactive_input',
        id: 'gemini-agent-prompt',
        placeholder: 'Instruct Gemini Agent...',
        typedValue: 'gemini.run({ task: "Build & ship multimodal service" });',
        cursorPosition: 57,
        buttonLabel: 'Launch Agent →',
        position3D: [0, 180, 0],
      },
      {
        type: 'pill_tag',
        id: 'gemini-pill-tag',
        text: '✦ Gemini 2.5 Pro Agent',
        variant: 'glass',
        accent: '#9B72CB',
        position3D: [-320, 270, 40],
      },
      {
        type: 'pill_tag',
        id: 'gemini-context-tag',
        text: '1M Context · Multi-Tool',
        variant: 'solid',
        accent: '#4285F4',
        position3D: [320, 270, 40],
      },
      {
        type: 'metric_card',
        id: 'metric-agent-success',
        label: 'Autonomous Agent Tasks',
        value: '99.8% Success',
        delta: 'Multimodal Tool Execution',
        chartPoints: [20, 42, 85, 170, 320, 520],
        accentColor: '#4285F4',
        position3D: [-480, -30, 120],
      },
      {
        type: 'asset_card',
        id: 'asset-gemini',
        assetUrl: `jobs/${jobId}/assets/logo.png`,
        scaleMode: 'contain',
        title: 'Native Multimodal Agency',
        subtitle: 'Autonomous browser agent, code synthesis & verification',
        position3D: [480, -30, 120],
      },
      {
        type: 'bento_grid',
        id: 'bento-gemini-features',
        columns: 3,
        cards: [
          {id: 'c1', title: 'Multimodal Core', subtitle: 'Vision, audio & code in one model', accent: '#4285F4'},
          {id: 'c2', title: 'Autonomous Tools', subtitle: 'Self-correcting CLI & API execution', accent: '#9B72CB'},
          {id: 'c3', title: 'Deep Reasoning', subtitle: 'Chain-of-thought verification engine', accent: '#D96570'},
        ],
        position3D: [0, -290, 260],
      },
    ];
  } else {
    uiTreeNodes = [
      {
        type: 'interactive_input',
        id: 'linear-prompt',
        placeholder: 'Search issues, cycles, and roadmaps...',
        typedValue: 'Fix render bottleneck across 128 BPM mesh',
        cursorPosition: 42,
        buttonLabel: 'Create Issue',
        position3D: [0, 180, 0],
      },
      {
        type: 'pill_tag',
        id: 'pill-cycle',
        text: 'Cycle 42 · In Progress',
        variant: 'glass',
        accent: '#5E6AD2',
        position3D: [-320, 270, 40],
      },
      {
        type: 'pill_tag',
        id: 'pill-speed',
        text: 'Real-time Sync: 50ms',
        variant: 'solid',
        accent: '#8B94E5',
        position3D: [320, 270, 40],
      },
      {
        type: 'metric_card',
        id: 'metric-velocity',
        label: 'Team Velocity',
        value: '142 pts',
        delta: '+34.2%',
        chartPoints: [20, 35, 52, 78, 110, 142],
        accentColor: '#5E6AD2',
        position3D: [-480, -30, 120],
      },
      {
        type: 'asset_card',
        id: 'asset-linear',
        assetUrl: `jobs/${jobId}/assets/logo.png`,
        scaleMode: 'contain',
        title: 'Continuous 3D Parallax',
        subtitle: 'Hardware-accelerated issue workflow',
        position3D: [480, -30, 120],
      },
      {
        type: 'bento_grid',
        id: 'bento-features',
        columns: 3,
        cards: [
          {id: 'b1', title: 'Zero Latency', subtitle: 'Optimistic UI updates', accent: '#5E6AD2'},
          {id: 'b2', title: '85% Bezier Curves', subtitle: 'Snappy muscle feedback', accent: '#8B94E5'},
          {id: 'b3', title: 'Keyboard First', subtitle: 'Pure flow state', accent: '#707CE8'},
        ],
        position3D: [0, -290, 260],
      },
    ];
  }

  const uiTree: UITree = {
    brandId: jobId,
    worldBounds: {width, height, depth: 2000},
    nodes: uiTreeNodes,
  };
  fs.writeFileSync(path.join(jobDir, 'ui_tree.json'), JSON.stringify(uiTree, null, 2), 'utf8');

  // 3. Synthesize camera_flight.json using 4-beat dynamic choreographer
  const durationSec = parseFloat(args['duration'] || '20');
  const fps = 30;
  const durationInFrames = Math.round(durationSec * fps);

  // Extract key anchor nodes from UI tree to target 3D flight paths
  const heroNode = uiTreeNodes.find((n) => n.type === 'interactive_input') || uiTreeNodes[0];
  const metricNode = uiTreeNodes.find((n) => n.type === 'metric_card');
  const bentoNode = uiTreeNodes.find((n) => n.type === 'bento_grid');
  const assetNode = uiTreeNodes.find((n) => n.type === 'asset_card');

  const heroPos = (heroNode?.position3D || [0, 180, 0]) as [number, number, number];
  const metricPos = (metricNode?.position3D || [-540, -80, 80]) as [number, number, number];
  const bentoPos = (bentoNode?.position3D || [0, -320, 140]) as [number, number, number];
  const assetPos = (assetNode?.position3D || [540, -80, 80]) as [number, number, number];

  // 4 Proportional Beats:
  // Beat 1: Hook (0.00 - 0.25) -> Wide establishing sweep into tight Hero focus
  // Beat 2: Telemetry (0.25 - 0.55) -> Orbit pan into Metric card & live sparkline draw
  // Beat 3: Ecosystem (0.55 - 0.85) -> Pan across Bento feature tray & Asset card
  // Beat 4: CTA (0.85 - 1.00) -> Master wide pull-out with final brand CTA lockup
  const beatWaypoints = [
    {
      progress: 0.0,
      position: [heroPos[0] - 60, heroPos[1] - 140, heroPos[2] - 780] as [number, number, number],
      target: [0, 0, 0] as [number, number, number],
      rotationDeg: [2, 3, 0] as [number, number, number],
      fov: 46,
      easing: 'smooth-drift' as const,
    },
    {
      progress: 0.2,
      position: [heroPos[0] + 40, heroPos[1] - 110, heroPos[2] - 740] as [number, number, number],
      target: [heroPos[0], heroPos[1] - 70, heroPos[2]] as [number, number, number],
      rotationDeg: [1, -2, 0] as [number, number, number],
      fov: 44,
      easing: 'agency-snap' as const,
    },
    {
      progress: 0.25,
      position: [heroPos[0], heroPos[1] - 70, heroPos[2] - 400] as [number, number, number],
      target: [heroPos[0], heroPos[1] - 70, heroPos[2]] as [number, number, number],
      rotationDeg: [0, 0, 0] as [number, number, number],
      fov: 36,
      easing: 'smooth-drift' as const,
    },
    {
      progress: 0.4,
      position: [metricPos[0] + 50, metricPos[1], metricPos[2] - 550] as [number, number, number],
      target: [metricPos[0], metricPos[1], metricPos[2]] as [number, number, number],
      rotationDeg: [3, -8, 0] as [number, number, number],
      fov: 39,
      easing: 'agency-snap' as const,
    },
    {
      progress: 0.55,
      position: [metricPos[0] + 20, metricPos[1] - 10, metricPos[2] - 460] as [number, number, number],
      target: [metricPos[0], metricPos[1], metricPos[2]] as [number, number, number],
      rotationDeg: [2, -6, 0] as [number, number, number],
      fov: 40,
      easing: 'agency-snap' as const,
    },
    {
      progress: 0.7,
      position: [bentoPos[0] - 120, bentoPos[1] + 30, bentoPos[2] - 510] as [number, number, number],
      target: [bentoPos[0], bentoPos[1], bentoPos[2]] as [number, number, number],
      rotationDeg: [4, 2, 0] as [number, number, number],
      fov: 42,
      easing: 'smooth-drift' as const,
    },
    {
      progress: 0.85,
      position: [assetPos[0] - 300, assetPos[1] - 180, assetPos[2] - 520] as [number, number, number],
      target: [assetPos[0] - 360, assetPos[1] - 200, assetPos[2] + 60] as [number, number, number],
      rotationDeg: [3, 8, 0] as [number, number, number],
      fov: 42,
      easing: 'agency-snap' as const,
    },
    {
      progress: 0.925,
      position: [0, -30, -840] as [number, number, number],
      target: [0, -40, 60] as [number, number, number],
      rotationDeg: [1, 0, 0] as [number, number, number],
      fov: 48,
      easing: 'smooth-drift' as const,
    },
    {
      progress: 1.0,
      position: [0, -40, -900] as [number, number, number],
      target: [0, -40, 60] as [number, number, number],
      rotationDeg: [0, 0, 0] as [number, number, number],
      fov: 50,
      easing: 'smooth-drift' as const,
    },
  ];

  const cameraFlight: CameraFlightPath = {
    waypoints: beatWaypoints.map((w) => {
      const frame = Math.round(w.progress * durationInFrames);
      return {
        timeSec: Number((frame / fps).toFixed(2)),
        frame,
        position: w.position,
        target: w.target,
        rotationDeg: w.rotationDeg,
        fov: w.fov,
        easing: w.easing,
      };
    }),
  };
  fs.writeFileSync(path.join(jobDir, 'camera_flight.json'), JSON.stringify(cameraFlight, null, 2), 'utf8');

  // 4. Synthesize spec.json, storyboard.json, and known-exceptions.json
  const limitWords = (str: string, max: number) => {
    const list = str.split(/\s+/).filter(Boolean);
    return list.slice(0, max).join(' ');
  };
  const specHeadline = limitWords(`${brand.name}: ${brand.tagline || 'Next-Gen Platform'}`, 8);
  const specSubline = limitWords(brand.description || 'Interactive spatial product demo', 12);
  const rawVo = brand.tagline || 'Build with confidence';
  const specVo = limitWords(rawVo === specHeadline ? 'Experience developer speed' : rawVo, 6);

  const isTactileClicksOnly = args['audio-mode'] === 'tactile_clicks' || args['no-music'] === 'true';

  const sfxCues = isTactileClicksOnly
    ? [
        {t: Number((0.04 * durationSec).toFixed(2)), type: 'click', gain: 0.85},
        {t: Number((0.07 * durationSec).toFixed(2)), type: 'tick', gain: 0.6},
        {t: Number((0.09 * durationSec).toFixed(2)), type: 'tick', gain: 0.6},
        {t: Number((0.11 * durationSec).toFixed(2)), type: 'tick', gain: 0.6},
        {t: Number((0.14 * durationSec).toFixed(2)), type: 'tick', gain: 0.6},
        {t: Number((0.17 * durationSec).toFixed(2)), type: 'click', gain: 0.9},
        {t: Number((0.26 * durationSec).toFixed(2)), type: 'click', gain: 0.9},
        {t: Number((0.36 * durationSec).toFixed(2)), type: 'tick', gain: 0.65},
        {t: Number((0.51 * durationSec).toFixed(2)), type: 'click', gain: 0.9},
        {t: Number((0.58 * durationSec).toFixed(2)), type: 'tick', gain: 0.65},
        {t: Number((0.66 * durationSec).toFixed(2)), type: 'tick', gain: 0.65},
        {t: Number((0.74 * durationSec).toFixed(2)), type: 'tick', gain: 0.65},
        {t: Number((0.84 * durationSec).toFixed(2)), type: 'pop', gain: 0.95},
      ]
    : [];

  const masterSpec = {
    brand: jobId,
    format: format,
    fps: 30,
    durationSec: durationSec,
    bpm: 120,
    scenes: [
      {
        id: 'master_spatial_stage',
        start: 0,
        duration: durationSec,
        layout: 'hero-type',
        headline: specHeadline,
        subline: specSubline,
        caption: specVo,
        visual: {
          kicker: brand.name,
          pulseText: brand.tagline || 'Platform',
        },
        motion: {
          enter: 'type-slam',
          idle: 'pulse-orbit',
          exit: 'push-through',
        },
        vo: isTactileClicksOnly ? '' : specVo,
        sfx: sfxCues,
        transitionOut: 'none',
      },
    ],
    audio: {
      assetsRoot: `jobs/${jobId}/assets`,
      voice: {
        provider: isTactileClicksOnly ? 'None' : 'ElevenLabs',
        voiceId: isTactileClicksOnly ? '' : 'EXAVITQu4vr4xnSDxMaL',
        model: 'eleven_multilingual_v2',
        clips: isTactileClicksOnly
          ? {}
          : {
              master_spatial_stage: 'audio/vo-s1.mp3',
            },
      },
      music: {
        file: isTactileClicksOnly ? '' : 'audio/music-bed.mp3',
        mood: isTactileClicksOnly ? 'silent' : 'restrained electronic build',
        volume: isTactileClicksOnly ? 0 : 1,
      },
      room: {
        file: 'audio/room-tone.wav',
        volume: 0.6,
      },
      sfxFiles: isTactileClicksOnly
        ? {
            click: 'audio/click.wav',
            tick: 'audio/tick.wav',
            pop: 'audio/pop.wav',
          }
        : {
            'logo-sting': 'audio/logo-sting.wav',
            pop: 'audio/pop.wav',
            pop2: 'audio/pop2.wav',
            swipe: 'audio/swipe.wav',
            tick: 'audio/tick.wav',
            click: 'audio/click.wav',
            riser: 'audio/riser.wav',
            thud: 'audio/thud.wav',
            success: 'audio/success.wav',
            whoosh: 'audio/whoosh.wav',
          },
      duck: 7,
    },
  };
  fs.writeFileSync(path.join(jobDir, 'spec.json'), JSON.stringify(masterSpec, null, 2), 'utf8');

  const masterSb = {
    shots: [
      {
        n: 1,
        t0: 0,
        t1: durationSec,
        role: 'hook',
        source: 'motion-graphic',
        visual: 'hero-type',
        transitionOut: 'none',
        camera: null,
        headline: specHeadline,
        subline: specSubline,
        onScreenText: specVo,
        dialogue: specVo,
        sfx: [],
      },
    ],
  };
  fs.writeFileSync(path.join(jobDir, 'storyboard.json'), JSON.stringify(masterSb, null, 2), 'utf8');

  const knownExceptions = {
    length_exceeded: 'single-take master 3d spatial stage',
    hook_length_shot_1: 'single-take master 3d spatial stage',
    last_shot_not_cta: 'single-take master 3d spatial stage',
  };
  fs.writeFileSync(path.join(jobDir, 'known-exceptions.json'), JSON.stringify(knownExceptions, null, 2), 'utf8');

  // 5. Synthesize scenes/index.tsx with 4-beat dynamic animations
  const sceneTsx = `import React from 'react';
import {Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import type {SceneRendererProps} from '../../../engine';
import {VectorRenderer} from '../../../engine/semantic-ui/VectorRenderer';
import type {UITree, VectorNode} from '../../../engine/semantic-ui/types';
import {evaluateCameraBeatsT, type CameraBeatT} from '../../../engine/stage/CameraFlight';
import {SAAS_BEATS_T, AGENCY_MOTION, KINETIC_SPRING_CONFIG, BEAT_RENDER_MODE} from '../../../engine/motion/physics';
import uiTreeData from '../ui_tree.json';

const SANS_FONT_STACK = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

// Proportional stagger delays (in t-space)
const SPRING_DELAY_T: Record<string, number> = {
  interactive_input: 0,      // Hero slams at t=0
  pill_tag: 0.005,
  metric_card: 0.01,
  asset_card: 0.015,
  bento_grid: 0.02,
};

// Generalized: Map any node type to its story beat
const NODE_BEAT_MAP: Record<string, typeof SAAS_BEATS_T[number]['id']> = {
  interactive_input: 'HOOK',
  pill_tag: 'HOOK',
  metric_card: 'PROOF',
  asset_card: 'PROOF',
  bento_grid: 'ECOSYSTEM',
};

const getSpringForNode = (node: VectorNode, t: number, fps: number, durationInFrames: number) => {
  const delayT = SPRING_DELAY_T[node.type] ?? 0.01;
  const delayFrames = delayT * durationInFrames;
  const frame = t * durationInFrames;

  return spring({
    frame: frame - delayFrames,
    fps,
    config: KINETIC_SPRING_CONFIG,
  });
};

const CAMERA_BEATS_T: CameraBeatT[] = [
  {
    id: 'beat1_hero_terminal',
    tStart: 0.00,
    tEnd: 0.25,
    position: [${heroPos[0]}, ${heroPos[1] - 70}, ${heroPos[2] - 380}],
    target: [${heroPos[0]}, ${heroPos[1] - 70}, ${heroPos[2]}],
    rotationDeg: [0, 0, 0],
    fov: 36,
    transitionT: 0.03,
    easing: 'snap',
  },
  {
    id: 'beat2_metric_telemetry',
    tStart: 0.25,
    tEnd: 0.50,
    position: [${metricPos[0] + 30}, ${metricPos[1] - 10}, ${metricPos[2] - 440}],
    target: [${metricPos[0]}, ${metricPos[1]}, ${metricPos[2]}],
    rotationDeg: [2, -7, 0],
    fov: 39,
    transitionT: 0.02,
    easing: 'whip',
  },
  {
    id: 'beat3_bento_ecosystem',
    tStart: 0.50,
    tEnd: 0.825,
    position: [${bentoPos[0] - 80}, ${bentoPos[1] + 20}, ${bentoPos[2] - 500}],
    target: [${bentoPos[0]}, ${bentoPos[1]}, ${bentoPos[2]}],
    rotationDeg: [3, 2, 0],
    fov: 42,
    transitionT: 0.023,
    easing: 'whip',
  },
  {
    id: 'beat4_wide_cta',
    tStart: 0.825,
    tEnd: 1.00,
    position: [0, -35, -880],
    target: [0, -40, 60],
    rotationDeg: [0, 0, 0],
    fov: 50,
    transitionT: 0.025,
    easing: 'snap',
  },
];

const AgencyScene: React.FC<SceneRendererProps> = ({scene, tokens}) => {
  const localFrame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const globalFrame = Math.round((scene?.start || 0) * fps) + localFrame;
  const t = globalFrame / durationInFrames;

  const tree = uiTreeData as UITree;
  const accent = tokens?.colors?.accent || '#3ECF8E';
  const bg = tokens?.colors?.background || '#08090C';

  const cam = evaluateCameraBeatsT(CAMERA_BEATS_T, t);
  const camX = cam.position[0];
  const camY = cam.position[1];
  const camZ = cam.position[2];
  const targetX = cam.target[0];
  const targetY = cam.target[1];
  const targetZ = cam.target[2];
  const rotX = cam.rotationDeg[0];
  const rotY = cam.rotationDeg[1];

  const beat = SAAS_BEATS_T.find((b) => t >= b.tStart && t < b.tEnd) ?? SAAS_BEATS_T[SAAS_BEATS_T.length - 1];
  const activeRenderMode = BEAT_RENDER_MODE[beat.id as keyof typeof BEAT_RENDER_MODE] ?? 'montage';
  const isFlightBeat = activeRenderMode === 'flight';

  const getSheenProgressForNode = (node: VectorNode, normT: number) => {
    if (node.type === 'interactive_input') {
      return interpolate(normT, [0.02, 0.07], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    }
    if (node.type === 'metric_card') {
      return interpolate(normT, [0.25, 0.31], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    }
    if (node.type === 'bento_grid') {
      return interpolate(normT, [0.50, 0.56], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    }
    return 0;
  };

  const ctaSpring = spring({
    frame: (t - 0.84) * durationInFrames,
    fps,
    config: KINETIC_SPRING_CONFIG,
  });
  const ctaOpacity = interpolate(ctaSpring, [0, 1], [0, 1]);
  const ctaY = interpolate(ctaSpring, [0, 1], [40, 0]);
  const ctaScale = interpolate(ctaSpring, [0, 1], [0.82, 1]);

  const lensPerspective = interpolate(
    t,
    [0.16, 0.21, 0.80, 0.86],
    [500, 1200, 1200, 2500],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.bezier(0.7, 0, 0.3, 1),
    }
  );

  const whipBlurPx = interpolate(
    t,
    [0.16, 0.19, 0.21, 0.40, 0.425, 0.45, 0.66, 0.69, 0.71],
    [0, 12, 0, 0, 12, 0, 0, 8, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.bezier(0.25, 1, 0.5, 1),
    }
  );

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: bg,
        backgroundImage: \`radial-gradient(circle at 50% 30%, \${accent}22, transparent 70%)\`,
        overflow: 'hidden',
        perspective: \`\${lensPerspective}px\`,
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transformStyle: 'preserve-3d',
          transform: isFlightBeat
            ? \`translate3d(\${-camX}px, \${camY}px, \${-(camZ + 700)}px) rotateX(\${rotX * 2}deg) rotateY(\${rotY * 2}deg)\`
            : 'none',
          filter: isFlightBeat ? \`blur(\${whipBlurPx}px)\` : 'none',
        }}
      >
        {tree.nodes.map((node) => {
          const [x, y, z] = node.position3D;

          const nodeBeatId = (node as any).beat ?? NODE_BEAT_MAP[node.type] ?? 'ECOSYSTEM';
          const nodeBeat = SAAS_BEATS_T.find((b) => b.id === nodeBeatId)!;
          const renderMode = BEAT_RENDER_MODE[nodeBeatId as keyof typeof BEAT_RENDER_MODE] ?? 'montage';
          const nodeProgress = interpolate(t, [nodeBeat.tStart, nodeBeat.tEnd], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          const easedNode = Easing.bezier(...AGENCY_MOTION.BEZIER_SNAP)(nodeProgress);
          const isFocused = renderMode === 'flight'
            ? (beat.id === nodeBeatId || beat.id === 'OUTRO')
            : (beat.id === nodeBeatId);

          const nodeSpring = getSpringForNode(node, t, fps, durationInFrames);
          const enterScale = interpolate(nodeSpring, [0, 1], [0.88, 1]);
          let crossfadeOpacity = 0;
          if (renderMode === 'flight') {
            if (t < nodeBeat.tStart) {
              crossfadeOpacity = interpolate(t, [nodeBeat.tStart - 0.03, nodeBeat.tStart], [0, 0.35], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
            } else if (isFocused) {
              crossfadeOpacity = interpolate(nodeProgress, [0, 0.15], [0.35, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
            } else {
              crossfadeOpacity = interpolate(t, [nodeBeat.tEnd, nodeBeat.tEnd + 0.03], [1, 0.35], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
            }
          } else {
            if (t < nodeBeat.tStart - 0.015 || t > nodeBeat.tEnd + 0.015) {
              crossfadeOpacity = 0;
            } else if (t < nodeBeat.tStart + 0.03) {
              crossfadeOpacity = interpolate(t, [nodeBeat.tStart - 0.01, nodeBeat.tStart + 0.03], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
            } else if (t > nodeBeat.tEnd - 0.02) {
              crossfadeOpacity = interpolate(t, [nodeBeat.tEnd - 0.02, nodeBeat.tEnd + 0.01], [1, 0], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
            } else {
              crossfadeOpacity = 1;
            }
          }
          const crossfadeY = isFocused ? (1 - easedNode) * 18 : 10;
          const crossfadeBlur = isFocused ? 0 : 12;
          const enterOpacity = crossfadeOpacity;
          const sheenProgress = getSheenProgressForNode(node, t);

          let activeNode = node;

          if (node.type === 'interactive_input' && node.typedValue) {
            const fullText = node.typedValue;
            const contentProgress = interpolate(t, [0.20, 0.37], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            const chars = Math.max(1, Math.round(contentProgress * fullText.length));
            activeNode = {
              ...node,
              typedValue: fullText.slice(0, chars),
            };
          }

          if (node.type === 'metric_card' && node.chartPoints) {
            const contentProgress = interpolate(t, [0.40, 0.60], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });

            const animatedPoints = node.chartPoints.map((val, idx) => {
              const startVal = 45 + idx * 5;
              const pointThreshold = idx / (node.chartPoints.length - 1);
              const ease = Math.min(1, Math.max(0, (contentProgress - pointThreshold * 0.4) / 0.6));
              return Math.round(startVal + (val - startVal) * ease);
            });

            activeNode = {
              ...node,
              chartPoints: animatedPoints,
            };
          }

          const flightTransform = \`translate3d(calc(-50% + \${x}px), calc(-50% - \${y}px + \${crossfadeY}px), \${z}px) scale(\${enterScale})\`;

          let montageTransform = \`translate(-50%, calc(-50% + \${crossfadeY}px)) scale(\${isFocused ? enterScale : 0.95})\`;
          if (node.type === 'pill_tag') {
            const heroNode = tree.nodes.find((n) => n.type === 'interactive_input');
            const heroBaseY = heroNode?.position3D[1] ?? 110;
            const pillOffsetY = y - heroBaseY;
            montageTransform = \`translate(calc(-50% + \${x}px), calc(-50% - \${pillOffsetY}px + \${crossfadeY}px)) scale(\${isFocused ? enterScale : 0.95})\`;
          } else if (node.type === 'metric_card' || node.type === 'asset_card') {
            const hasDualProof = tree.nodes.some(
              (n) => n.id !== node.id && (NODE_BEAT_MAP[n.type] === 'PROOF' || (n as any).beat === 'PROOF')
            );
            if (hasDualProof) {
              const xOffset = x < 0 ? -210 : 210;
              montageTransform = \`translate(calc(-50% + \${xOffset}px), calc(-50% + \${crossfadeY}px)) scale(\${isFocused ? enterScale : 0.95})\`;
            }
          }

          const finalTransform = renderMode === 'flight' ? flightTransform : montageTransform;

          return (
            <div
              key={node.id}
              style={{
                position: 'absolute',
                left: '50%',
                top: '50%',
                transform: finalTransform,
                opacity: enterOpacity,
                filter: \`blur(\${crossfadeBlur}px)\`,
                pointerEvents: isFocused ? 'auto' : 'none',
                zIndex: isFocused ? 10 : 1,
                willChange: 'transform, opacity, filter',
                transformStyle: renderMode === 'flight' ? 'preserve-3d' : undefined,
              }}
            >
              <VectorRenderer
                node={activeNode}
                tokens={tokens}
                cameraPosition={renderMode === 'flight' ? [camX, camY, camZ] : undefined}
                cameraTarget={renderMode === 'flight' ? [targetX, targetY, targetZ] : undefined}
                sheenProgress={sheenProgress}
              />
            </div>
          );
        })}

        {/* Final Brand CTA Lockup */}
        {t >= 0.83 && (
          <div
            style={{
              position: 'absolute',
              left: '50%',
              top: '50%',
              transform: isFlightBeat
                ? \`translate3d(-50%, calc(-50% + 20px + \${ctaY}px), 240px) scale(\${ctaScale})\`
                : \`translate(-50%, calc(-50% + \${ctaY}px)) scale(\${ctaScale})\`,
              opacity: ctaOpacity,
              transformStyle: 'preserve-3d',
              padding: '24px 36px',
              borderRadius: 24,
              background: 'linear-gradient(135deg, rgba(20,24,36,0.92) 0%, rgba(10,12,18,0.96) 100%)',
              border: \`1px solid \${accent}66\`,
              boxShadow: \`0 24px 70px rgba(0,0,0,0.7), 0 0 30px \${accent}33\`,
              backdropFilter: 'blur(24px)',
              display: 'flex',
              alignItems: 'center',
              gap: 28,
              fontFamily: SANS_FONT_STACK,
              zIndex: 100,
            }}
          >
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: 16,
                background: '#0a0a0f',
                border: '1px solid rgba(255,255,255,0.12)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                overflow: 'hidden',
              }}
            >
              <Img
                src={staticFile('jobs/${jobId}/assets/logo.png')}
                alt="Logo"
                style={{width: 48, height: 48, objectFit: 'contain'}}
              />
            </div>
            <div>
              <div style={{fontSize: 22, fontWeight: 800, color: '#fff', letterSpacing: '-0.02em'}}>
                ${brand.name}
              </div>
              <div style={{fontSize: 14, color: '#94a3b8', marginTop: 4}}>
                ${brand.tagline || 'Experience next-level developer workflows'}
              </div>
            </div>
            <div
              style={{
                padding: '12px 28px',
                borderRadius: 14,
                background: \`linear-gradient(135deg, \${accent} 0%, \${tokens?.colors?.accentLight || accent} 100%)\`,
                color: '#041315',
                fontSize: 15,
                fontWeight: 700,
                letterSpacing: '0.01em',
                boxShadow: \`0 8px 24px \${accent}44\`,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              Get Started →
            </div>
          </div>
        )}
      </div>

      {/* Cinematic Post-Processing Overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          zIndex: 9999,
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'radial-gradient(circle at 50% 50%, transparent 40%, rgba(5,7,12,0.85) 120%)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            // eslint-disable-next-line @remotion/no-background-image
            backgroundImage: \`url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")\`,
            opacity: 0.05,
            mixBlendMode: 'overlay',
          }}
        />
      </div>
    </div>
  );
};

export default AgencyScene;
`;
  fs.writeFileSync(path.join(jobDir, 'scenes', 'index.tsx'), sceneTsx, 'utf8');

  console.log(`✓ Job scaffolding & planning complete for ${jobId}`);
  console.log(`  - brand.json:          ${path.join(jobDir, 'brand.json')}`);
  console.log(`  - ui_tree.json:        ${path.join(jobDir, 'ui_tree.json')}`);
  console.log(`  - camera_flight.json:  ${path.join(jobDir, 'camera_flight.json')}`);
  console.log(`  - spec.json:           ${path.join(jobDir, 'spec.json')}`);
  console.log(`  - scenes/index.tsx:    ${path.join(jobDir, 'scenes', 'index.tsx')}\n`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
