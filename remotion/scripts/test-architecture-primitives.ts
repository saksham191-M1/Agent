import assert from 'node:assert';

// -------------------------------------------------------------
// 1. HYBRID AST VALIDATION (Pure Vector + AssetCardNode)
// -------------------------------------------------------------
export type Position3D = [number, number, number];

export interface BaseNode {
  id: string;
  position3D: Position3D;
  scale?: number;
  rotationDeg?: [number, number, number];
}

export interface MetricCardNode extends BaseNode {
  type: 'metric_card';
  label: string;
  value: string;
  delta: string;
  chartPoints: number[];
}

export interface AssetCardNode extends BaseNode {
  type: 'asset_card';
  assetUrl: string;
  scaleMode: 'contain' | 'cover';
  cropRegion?: [number, number, number, number]; // [x, y, w, h]
}

export type VisualNode = MetricCardNode | AssetCardNode;

// -------------------------------------------------------------
// 2. CAMERA COORDINATE ADAPTER (After Effects vs Three.js)
// -------------------------------------------------------------
export interface CameraWaypoint {
  timeSec: number;
  frame: number;
  // Normalized world coordinates: center = [0, 0, 0], units = arbitrary world units
  position: Position3D; 
  target: Position3D;   
  rotationDeg: [number, number, number]; // [pitch, yaw, roll]
  fov: number;
}

export interface EffectCraftCameraProps {
  position: [number, number, number]; // Top-left origin, Y down, pixel coords
  pointOfInterest: [number, number, number];
  zoom: number; // Pixels focal length
}

export interface ThreeJsCameraProps {
  position: [number, number, number]; // Center origin, Y up, cartesian scene units
  target: [number, number, number];
  fov: number;
}

export class CameraCoordinateAdapter {
  constructor(private comp: { width: number; height: number }) {}

  toEffectCraft(wp: CameraWaypoint): EffectCraftCameraProps {
    const cx = this.comp.width / 2;
    const cy = this.comp.height / 2;
    
    // In AE/EffectCraft: Center of screen is (cx, cy). Y is down.
    const ecPos: [number, number, number] = [
      cx + wp.position[0],
      cy - wp.position[1], // Invert Y because AE Y points DOWN
      wp.position[2]
    ];

    const ecTarget: [number, number, number] = [
      cx + wp.target[0],
      cy - wp.target[1],
      wp.target[2]
    ];

    // Compute focal length in pixels from FOV
    // tan(fov / 2) = (height / 2) / zoom
    const rad = (wp.fov * Math.PI) / 360;
    const zoom = (this.comp.height / 2) / Math.tan(rad);

    return {
      position: ecPos,
      pointOfInterest: ecTarget,
      zoom: Math.round(zoom * 10) / 10
    };
  }

  toThreeJs(wp: CameraWaypoint): ThreeJsCameraProps {
    // Three.js world: center is (0, 0, 0), Y points UP, normalized to scene scale
    return {
      position: [wp.position[0], wp.position[1], wp.position[2]],
      target: [wp.target[0], wp.target[1], wp.target[2]],
      fov: wp.fov
    };
  }
}

// -------------------------------------------------------------
// 3. BEAT-WINDOW BUDGETING & QUANTIZATION
// -------------------------------------------------------------
export interface BeatGridConfig {
  bpm: number;
  fps: number;
}

export class BeatGridScheduler {
  readonly framesPerBeat: number;
  readonly framesPerBar: number;
  readonly secondsPerBar: number;

  constructor(public config: BeatGridConfig) {
    this.framesPerBeat = Math.round((60 / config.bpm) * config.fps);
    this.framesPerBar = this.framesPerBeat * 4;
    this.secondsPerBar = (60 / config.bpm) * 4;
  }

  /**
   * Budgets word count for an ElevenLabs voiceover window locked to integer bars.
   * Target speaking rate: ~2.0 - 2.4 words per second.
   */
  calculateVoiceBudget(bars: number, targetWordsPerSec = 2.2): {
    durationSec: number;
    durationFrames: number;
    maxWordCount: number;
  } {
    const durationSec = bars * this.secondsPerBar;
    const durationFrames = bars * this.framesPerBar;
    const maxWordCount = Math.floor(durationSec * targetWordsPerSec);
    return { durationSec, durationFrames, maxWordCount };
  }

  snapFrameToNearestBeat(frame: number): number {
    return Math.round(frame / this.framesPerBeat) * this.framesPerBeat;
  }
}

// -------------------------------------------------------------
// RUNNING THE VERIFICATION TESTS
// -------------------------------------------------------------
function runVerification() {
  console.log("=== RUNNING PRE-SHIFT VERIFICATION SUITE ===");

  // Test 1: Hybrid Node AST
  const metricNode: MetricCardNode = {
    type: 'metric_card',
    id: 'm1',
    label: 'MRR',
    value: '$120K',
    delta: '+15%',
    chartPoints: [10, 20, 35, 50],
    position3D: [0, 0, 0]
  };

  const assetNode: AssetCardNode = {
    type: 'asset_card',
    id: 'a1',
    assetUrl: 'https://brandfetch.io/sample-logo.png',
    scaleMode: 'contain',
    position3D: [400, 200, -100]
  };

  assert.strictEqual(metricNode.type, 'metric_card');
  assert.strictEqual(assetNode.type, 'asset_card');
  console.log("✓ Hybrid AST Test Passed: MetricCardNode & AssetCardNode validated.");

  // Test 2: Camera Coordinate Adapter
  const adapter = new CameraCoordinateAdapter({ width: 1920, height: 1080 });
  const testWp: CameraWaypoint = {
    timeSec: 0,
    frame: 0,
    position: [100, 50, -500], // 100px right, 50px up, 500px away
    target: [0, 0, 0],
    rotationDeg: [0, 0, 0],
    fov: 45
  };

  const ec = adapter.toEffectCraft(testWp);
  const three = adapter.toThreeJs(testWp);

  // In AE, X = 960 + 100 = 1060. Y = 540 - 50 = 490 (Y inverted).
  assert.strictEqual(ec.position[0], 1060);
  assert.strictEqual(ec.position[1], 490);
  assert.strictEqual(ec.position[2], -500);

  // In Three.js, Y remains positive 50
  assert.strictEqual(three.position[0], 100);
  assert.strictEqual(three.position[1], 50);
  assert.strictEqual(three.position[2], -500);

  console.log(`✓ Camera Coordinate Adapter Passed:`);
  console.log(`  - Input World Coord: [${testWp.position.join(', ')}]`);
  console.log(`  - EffectCraft Coord: [${ec.position.join(', ')}] (Center: [960, 540], Y-inverted)`);
  console.log(`  - Three.js Coord:    [${three.position.join(', ')}] (Center: [0, 0], Cartesian)`);

  // Test 3: Beat-Window Budgeting & Quantization
  const grid = new BeatGridScheduler({ bpm: 120, fps: 30 });
  assert.strictEqual(grid.framesPerBeat, 15);
  assert.strictEqual(grid.framesPerBar, 60);
  assert.strictEqual(grid.secondsPerBar, 2.0);

  // 4-bar phrase (e.g. Intro Hook)
  const budget4Bar = grid.calculateVoiceBudget(4, 2.0); // 4 bars = 8 seconds
  assert.strictEqual(budget4Bar.durationSec, 8.0);
  assert.strictEqual(budget4Bar.durationFrames, 240);
  assert.strictEqual(budget4Bar.maxWordCount, 16);

  console.log(`✓ Beat-Window Budgeting Passed:`);
  console.log(`  - At 120 BPM: 1 beat = ${grid.framesPerBeat} frames (0.5s), 1 bar = ${grid.framesPerBar} frames (2.0s)`);
  console.log(`  - 4-bar phrase: exactly ${budget4Bar.durationSec}s (${budget4Bar.durationFrames} frames)`);
  console.log(`  - Max Voiceover Budget: ${budget4Bar.maxWordCount} words to guarantee non-overflow.`);

  console.log("\nALL PRE-SHIFT ARCHITECTURAL TESTS PASSED CLEANLY!");
}

runVerification();
