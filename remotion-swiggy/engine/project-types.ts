export type ProjectScene = {
  id: string;
  kind: string;
  start: number;
  end: number;
  duration: number;
  headline: string;
  body: string;
  narration: string;
};

export type ProjectManifest = {
  id: string;
  name: string;
  quality: 'draft' | 'final';
  format: '9:16' | '1:1' | '16:9';
  fps: number;
  durationSec: number;
  narrated?: boolean;
  demoDuration?: number;
  look?: string;
  brief: {
    name: string;
    description: string;
    audience: string;
    problem: string;
    benefits: string[];
    cta: string;
    url: string;
    color: string;
    template: string;
    tone: string;
    language: string;
  };
  scenes: ProjectScene[];
  assets: Record<string, string>;
  audio?: string | null;
};

export const projectDimensions = (format: ProjectManifest['format'], quality: ProjectManifest['quality']) => {
  const full = format === '1:1' ? {width: 1080, height: 1080} : format === '16:9' ? {width: 1920, height: 1080} : {width: 1080, height: 1920};
  return quality === 'draft' ? {width: Math.round(full.width / 3), height: Math.round(full.height / 3)} : full;
};
