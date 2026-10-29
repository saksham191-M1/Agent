const cp = require('child_process');
const fs = require('fs');

const jobs = process.argv.slice(2).length > 0
  ? process.argv.slice(2)
  : fs.readdirSync('./jobs', {withFileTypes: true}).filter(d => d.isDirectory() && !d.name.startsWith('_')).map(d => d.name);

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
