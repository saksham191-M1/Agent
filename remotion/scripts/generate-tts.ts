import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import https from 'https';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.join(__dirname, '..');

// Basic .env parser
const envContent = fs.readFileSync(path.join(root, '..', '.env'), 'utf8');
const env: Record<string, string> = {};
for (const line of envContent.split('\n')) {
  if (line.includes('=')) {
    const [k, v] = line.split('=');
    env[k.trim()] = v.trim().replace(/^"|"$/g, '');
  }
}

const API_KEY = env['ELEVENLABS_API_KEY'];
const VOICE_ID = env['ELEVENLABS_VOICE_ID'] || 'EXAVITQu4vr4xnSDxMaL'; // fallback

if (!API_KEY) {
  console.error("No ELEVENLABS_API_KEY found in ../.env");
  process.exit(1);
}

const jobId = process.argv[2];
if (!jobId) {
  console.error("Usage: tsx generate-tts.ts <jobId>");
  process.exit(1);
}

const storyboardPath = path.join(root, 'jobs', jobId, 'storyboard.json');
const outDir = path.join(root, 'jobs', jobId, 'assets', 'audio');

if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

const storyboard = JSON.parse(fs.readFileSync(storyboardPath, 'utf8'));

async function generateSpeech(text: string, outputPath: string) {
  return new Promise<void>((resolve, reject) => {
    const data = JSON.stringify({
      text: text,
      model_id: "eleven_multilingual_v2",
      voice_settings: {
        stability: 0.5,
        similarity_boost: 0.75
      }
    });

    const options = {
      hostname: 'api.elevenlabs.io',
      port: 443,
      path: `/v1/text-to-speech/${VOICE_ID}`,
      method: 'POST',
      headers: {
        'Accept': 'audio/mpeg',
        'xi-api-key': API_KEY,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
      }
    };

    const req = https.request(options, (res) => {
      if (res.statusCode !== 200) {
        console.error(`Failed to generate TTS for text: "${text}". Status code: ${res.statusCode}`);
        res.resume();
        return reject(new Error('API request failed'));
      }
      const stream = fs.createWriteStream(outputPath);
      res.pipe(stream);
      stream.on('finish', () => resolve());
    });

    req.on('error', (e) => reject(e));
    req.write(data);
    req.end();
  });
}

async function main() {
  console.log(`Generating TTS for ${jobId}...`);
  for (const shot of storyboard.shots) {
    if (shot.dialogue) {
      const fileName = `vo-s${shot.n}.mp3`;
      const filePath = path.join(outDir, fileName);
      if (!fs.existsSync(filePath)) {
        console.log(`Generating ${fileName}...`);
        try {
          await generateSpeech(shot.dialogue, filePath);
          console.log(`Saved ${fileName}`);
        } catch (e) {
          console.error(e);
        }
      } else {
        console.log(`Skipping ${fileName} (already exists)`);
      }
    }
  }
  console.log('TTS generation complete.');
}

main();
