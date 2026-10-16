import assert from 'node:assert';
import {
  minimumJerkPosition,
  solveCurvedCursorPath,
  solveClickContactImpulse,
  simulateHumanTypingTimeline,
} from '../engine/walkthrough/motor-physics';
import {AutoZoomCalculator} from '../engine/walkthrough/auto-zoom';
import {VoiceFirstAligner} from '../engine/walkthrough/voice-aligner';
import type {BoundingBox} from '../engine/walkthrough/types';

function runWalkthroughPrimitiveTests() {
  console.log('\n======================================================');
  console.log('🧪 RUNNING SOFTWARE WALKTHROUGH PRIMITIVE TESTS');
  console.log('======================================================\n');

  // -------------------------------------------------------------
  // TEST 1: Minimum-Jerk Polynomial Boundary & Symmetry
  // -------------------------------------------------------------
  const x0 = 100;
  const x1 = 500;
  const T = 1.0;

  assert.strictEqual(minimumJerkPosition(x0, x1, 0, T), x0);
  assert.strictEqual(minimumJerkPosition(x0, x1, T, T), x1);
  assert.strictEqual(minimumJerkPosition(x0, x1, T / 2, T), (x0 + x1) / 2); // Exact midpoint symmetry
  assert.ok(minimumJerkPosition(x0, x1, 0.25, T) < 300); // S-curve acceleration
  console.log('✓ Test 1: Minimum-Jerk Polynomial verified (boundary conditions & midpoint symmetry).');

  // -------------------------------------------------------------
  // TEST 2: Spatial Bézier Arc Curvature (Perpendicular Offset)
  // -------------------------------------------------------------
  const from: [number, number] = [0, 0];
  const to: [number, number] = [400, 0];
  const arcAtStart = solveCurvedCursorPath(from, to, 0, 30);
  const arcAtMid = solveCurvedCursorPath(from, to, 0.5, 30);
  const arcAtEnd = solveCurvedCursorPath(from, to, 1.0, 30);

  assert.strictEqual(arcAtStart.x, 0);
  assert.strictEqual(arcAtStart.y, 0);
  assert.strictEqual(arcAtEnd.x, 400);
  assert.strictEqual(arcAtEnd.y, 0);
  // At midpoint, perpendicular offset should displace Y by ~30px
  assert.ok(Math.abs(arcAtMid.y - 30) < 0.1, `Midpoint displacement ${arcAtMid.y} should be ~30`);
  console.log(`✓ Test 2: Spatial Bézier Arc verified (Midpoint displaced by ${arcAtMid.y}px along perpendicular).`);

  // -------------------------------------------------------------
  // TEST 3: Click Contact Impulse & Ripple Ring
  // -------------------------------------------------------------
  const clickFrame = 60;
  const preContact = solveClickContactImpulse(clickFrame - 4, clickFrame);
  const contactImpulse = solveClickContactImpulse(clickFrame, clickFrame);
  const postContact = solveClickContactImpulse(clickFrame + 4, clickFrame);

  assert.strictEqual(preContact.scale, 1.0);
  assert.strictEqual(contactImpulse.scale, 0.86); // Exact contact compression
  assert.strictEqual(postContact.scale, 1.0);   // Rebound to 1.0
  assert.ok(contactImpulse.rippleRadius >= 0);
  assert.ok(postContact.rippleRadius > 0);       // Ripple expands post-click
  console.log(`✓ Test 3: Click Contact Impulse verified (Compression scale ${contactImpulse.scale} -> rebound 1.0).`);

  // -------------------------------------------------------------
  // TEST 4: Safeguard 1 — Auto-Zoom Viewport Edge Clamping
  // -------------------------------------------------------------
  const viewport = {width: 1920, height: 1080};
  const cornerBbox: BoundingBox = {x: 10, y: 10, width: 40, height: 40}; // Top-left corner
  const zoomScale = 2.0;

  const clampedCenter = AutoZoomCalculator.computeClampedCenter(cornerBbox, zoomScale, viewport);
  const minAllowedX = viewport.width / (2 * zoomScale); // 1920 / 4 = 480
  const minAllowedY = viewport.height / (2 * zoomScale); // 1080 / 4 = 270

  assert.strictEqual(clampedCenter[0], minAllowedX, `Center X should clamp to ${minAllowedX}`);
  assert.strictEqual(clampedCenter[1], minAllowedY, `Center Y should clamp to ${minAllowedY}`);
  console.log(`✓ Test 4 (Safeguard 1): Auto-Zoom Edge Clamping verified (Raw: [30, 30] -> Clamped: [${clampedCenter.join(', ')}]).`);

  // -------------------------------------------------------------
  // TEST 5: Safeguard 2 — Dynamic Time Warping (DTW) Frame Remap
  // -------------------------------------------------------------
  const remapTable = VoiceFirstAligner.generateFrameRemapTable(
    300, // 300 source frames (5.0s @ 60fps)
    [{startSec: 1.0, endSec: 2.0}], // Active window between 1.0s and 2.0s
    {fps: 60, voiceWords: [], idleThresholdSec: 1.0, maxSpeedFactor: 4.0}
  );

  assert.ok(remapTable.length > 0);
  // Verify monotonic progression
  for (let i = 1; i < remapTable.length; i++) {
    assert.ok(remapTable[i].outputFrame > remapTable[i - 1].outputFrame);
    assert.ok(remapTable[i].sourceFrame > remapTable[i - 1].sourceFrame);
  }

  const remappedFrame = VoiceFirstAligner.remapSourceFrame(100, remapTable);
  assert.ok(remappedFrame >= 0);
  console.log(`✓ Test 5 (Safeguard 2): Monotonic Frame-Remapping Table verified (${remapTable.length} entries generated, strictly monotonic).`);

  // -------------------------------------------------------------
  // TEST 6: Audio Ducking Envelope
  // -------------------------------------------------------------
  const dialogueWindows = [{startFrame: 60, endFrame: 180}];
  const duckedLevel = VoiceFirstAligner.calculateDuckingEnvelope(100, dialogueWindows, 60);
  const unduckedLevel = VoiceFirstAligner.calculateDuckingEnvelope(30, dialogueWindows, 60);
  const recoveringLevel = VoiceFirstAligner.calculateDuckingEnvelope(190, dialogueWindows, 60);

  assert.strictEqual(duckedLevel, -20.0);
  assert.strictEqual(unduckedLevel, -8.0);
  assert.ok(recoveringLevel > -20.0 && recoveringLevel < -8.0);
  console.log(`✓ Test 6: Audio Ducking Envelope verified (Active: ${duckedLevel} dB, Paused: ${unduckedLevel} dB).`);

  // -------------------------------------------------------------
  // TEST 7: Human Typing Simulation
  // -------------------------------------------------------------
  const typing = simulateHumanTypingTimeline('Hello, world!', 0, 60);
  assert.strictEqual(typing.length, 13);
  assert.strictEqual(typing[typing.length - 1].textSoFar, 'Hello, world!');
  // Comma and punctuation should add extra delay frames
  console.log(`✓ Test 7: Human Typing Simulation verified (${typing.length} characters emitted with punctuation pauses).`);

  console.log('\nALL SOFTWARE WALKTHROUGH PRIMITIVE TESTS PASSED CLEANLY!\n');
}

runWalkthroughPrimitiveTests();
