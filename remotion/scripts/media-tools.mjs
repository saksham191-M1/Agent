import {existsSync, readdirSync} from 'node:fs';
import {createRequire} from 'node:module';
import {join} from 'node:path';

const require = createRequire(import.meta.url);
const onPath = (name) => (process.env.PATH ?? '').split(process.platform === 'win32' ? ';' : ':').map((dir) => join(dir, name)).find(existsSync);
export const mediaTools = () => {
  const executable = (tool, bundled) => {
    const configured = process.env[`${tool.toUpperCase()}_PATH`];
    if (configured && !existsSync(configured)) throw new Error(`Invalid ${tool.toUpperCase()}_PATH`);
    const found = configured ?? onPath(process.platform === 'win32' ? `${tool}.exe` : tool) ?? bundled();
    if (!found || !existsSync(found)) throw new Error(`Install ${tool} or set ${tool.toUpperCase()}_PATH for this OS.`);
    return found;
  };
  return {ffmpeg: executable('ffmpeg', () => require('ffmpeg-static')),
    ffprobe: executable('ffprobe', () => require('ffprobe-static').path)};
};

export const installedBrowser = (root) => {
  const configured = process.env.REMOTION_BROWSER_EXECUTABLE;
  if (configured) {
    if (!existsSync(configured)) throw new Error('REMOTION_BROWSER_EXECUTABLE does not exist.');
    return configured;
  }
  const directory = join(root, 'node_modules', '.remotion', 'chrome-headless-shell');
  const walk = (dir) => !existsSync(dir) ? [] : readdirSync(dir, {withFileTypes: true}).flatMap((entry) => entry.isDirectory() ? walk(join(dir, entry.name)) : [join(dir, entry.name)]);
  const expected = process.platform === 'win32' ? 'chrome-headless-shell.exe' : 'chrome-headless-shell';
  const found = walk(directory).find((file) => file.endsWith(`/${expected}`) || file.endsWith(`\\${expected}`));
  if (!found) throw new Error('Install a Remotion browser with npx remotion browser ensure, or set REMOTION_BROWSER_EXECUTABLE.');
  return found;
};
