const cp = require('child_process');
const fs = require('fs');

const jobs = ['swiggy-001', 'skillme-003', 'test-brand-002'];

for (const j of jobs) {
  try {
    cp.execSync(`npm run qa:job ${j}`, { stdio: 'inherit' });
    const r = require(`./jobs/${j}/out/qa-report.json`);
    console.log(`\n=== QA SUMMARY FOR ${j} ===`);
    console.log(`Integrated LUFS: ${r.audio.integratedLufs}`);
    console.log(`RMS Gate Passed: ${r.audio.rmsGate}`);
    console.log(`Clicks:`, r.audio.clicks);
  } catch(e) {
    console.error(`QA Failed for ${j}`);
  }
}
