import Ajv from 'ajv';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

const root = process.cwd();
const ajv = new Ajv();
const schema = JSON.parse(readFileSync(resolve(root, 'engine/tools.schema.json'), 'utf8'));
const validate = ajv.compile(schema);

const data = JSON.parse(readFileSync(resolve(root, 'engine/tools.json'), 'utf8'));
if (!validate(data)) {
  console.error(validate.errors);
  process.exit(1);
}
console.log('Tools config valid.');
