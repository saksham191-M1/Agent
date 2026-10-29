import {FLAGS} from './flags';

function runTests() {
  const orig = process.env.PIPELINE_V2;

  delete process.env.PIPELINE_V2;
  if (FLAGS.PIPELINE_V2 !== false) {
    throw new Error('Default PIPELINE_V2 should be false');
  }

  process.env.PIPELINE_V2 = '1';
  if (FLAGS.PIPELINE_V2 !== true) {
    throw new Error('PIPELINE_V2=1 should be true');
  }

  process.env.PIPELINE_V2 = 'true';
  if (FLAGS.PIPELINE_V2 !== true) {
    throw new Error('PIPELINE_V2=true should be true');
  }

  process.env.PIPELINE_V2 = '0';
  if (FLAGS.PIPELINE_V2 !== false) {
    throw new Error('PIPELINE_V2=0 should be false');
  }

  if (orig !== undefined) {
    process.env.PIPELINE_V2 = orig;
  } else {
    delete process.env.PIPELINE_V2;
  }

  console.log('✅ flags.ts unit test passed!');
}

runTests();
