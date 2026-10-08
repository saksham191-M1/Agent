import {generateJobRegistry} from './job-discovery';

const ids = generateJobRegistry();
process.stdout.write(`Discovered ${ids.length} job(s): ${ids.join(', ')}\n`);
