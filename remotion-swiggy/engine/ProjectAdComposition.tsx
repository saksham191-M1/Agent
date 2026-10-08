import React, {useLayoutEffect, useRef} from 'react';
import {AbsoluteFill, Audio, Freeze, Img, OffthreadVideo, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {loadFontForBrand} from './font-loader';
import type {ProjectManifest, ProjectScene as ManifestScene} from './project-types';

const fontFamily = () => `${loadFontForBrand('Noto Sans')}, ${loadFontForBrand('Noto Sans Devanagari')}, sans-serif`;
const assetUrl = (path: string) => staticFile(path);
const alpha = (color: string, opacity: string) => `${color}${opacity}`;

// Fit real DOM text at native export dimensions; caps on the input do not by
// themselves guarantee that long words or Hindi lines fit into a composition.
const FitText: React.FC<{text: string; size: number; minimum: number; style?: React.CSSProperties; testId?: string}> = ({text, size, minimum, style, testId}) => {
  const ref = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const fit = () => {
      const element = ref.current;
      if (!element) return;
      let current = size;
      element.style.fontSize = `${current}px`;
      while ((element.scrollHeight > element.clientHeight + 1 || element.scrollWidth > element.clientWidth + 1) && current > minimum) {
        current -= 1;
        element.style.fontSize = `${current}px`;
      }
    };
    fit();
    document.fonts.ready.then(fit);
  }, [text, size, minimum]);
  return <div ref={ref} data-layout={testId} style={{fontSize: size, overflowWrap: 'anywhere', whiteSpace: 'pre-wrap', ...style}}>{text}</div>;
};

const Media: React.FC<{manifest: ProjectManifest; scene: ManifestScene; index: number}> = ({manifest, scene, index}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const image = manifest.assets[`scene_${index + 1}`] ?? manifest.assets.screenshot;
  const motion = interpolate(frame, [0, Math.round(scene.duration * fps)], [1, 1.04], {extrapolateRight: 'clamp'});
  const style: React.CSSProperties = {width: '100%', height: '100%', objectFit: 'contain', transform: `scale(${motion})`};
  if (manifest.assets.demo) {
    const last = Math.max(0, Math.floor((manifest.demoDuration ?? manifest.durationSec) * fps) - 1);
    const start = Math.min(last, Math.round(scene.start * fps));
    // Real footage plays at original speed; short footage holds its last frame.
    return <Freeze frame={Math.min(frame, last - start)}><OffthreadVideo src={assetUrl(manifest.assets.demo)} startFrom={start} muted style={style} /></Freeze>;
  }
  return image ? <Img src={assetUrl(image)} alt="Supplied product evidence" style={style} /> : null;
};

const Scene: React.FC<{manifest: ProjectManifest; scene: ManifestScene; index: number}> = ({manifest, scene, index}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const u = Math.min(width, height) / 1080;
  const landscape = width > height;
  const square = width === height;
  const accent = manifest.brief.color;
  const editorial = manifest.look === 'editorial';
  const background = editorial ? '#f3f1ec' : '#0a1018';
  const ink = editorial ? '#132334' : '#f6f8fb';
  const muted = editorial ? '#47576a' : '#aab5c3';
  const enter = spring({frame, fps, config: {damping: 20, stiffness: 120}});
  const hasMedia = Boolean(manifest.assets.demo || manifest.assets[`scene_${index + 1}`] || manifest.assets.screenshot);
  const endCard = index === manifest.scenes.length - 1;
  const pad = width * .07;
  const contentTop = height * (landscape ? .2 : .14);
  const contentBottom = height * (manifest.narrated ? .81 : .86);
  const copyWidth = landscape ? width * .39 : width * .86;
  const copyHeight = landscape ? height * .59 : height * (square ? .26 : .24);
  const visualTop = landscape ? contentTop : height * (square ? .44 : .43);
  const visualLeft = landscape ? width * .52 : pad;
  const visualWidth = landscape ? width * .41 : width * .86;
  const visualHeight = contentBottom - visualTop;
  const captionHeight = height * .09;
  const benefits = manifest.brief.benefits.slice(0, 3);
  const headingHeight = copyHeight * .63;
  const logo = manifest.assets.logo;
  const accentRgb = accent.slice(1).match(/../g)!.map((part) => parseInt(part, 16));
  const accentInk = accentRgb[0] * .299 + accentRgb[1] * .587 + accentRgb[2] * .114 < 145 ? '#ffffff' : '#081016';
  return <AbsoluteFill style={{fontFamily: fontFamily(), color: ink, background, overflow: 'hidden'}}>
    {manifest.look !== 'minimal' && <AbsoluteFill style={{background: `radial-gradient(circle at 85% 15%, ${alpha(accent, '32')}, transparent 45%)`}} />}
    <div style={{position: 'absolute', left: pad, right: pad, top: height * .045, height: height * .045, display: 'flex', alignItems: 'center', gap: 16 * u}}>
      {logo && <Img src={assetUrl(logo)} alt={manifest.name} style={{maxWidth: 160 * u, height: '100%', objectFit: 'contain'}} />}
      <FitText text={manifest.name} size={28 * u} minimum={18 * u} style={{width: width * .6, height: '100%', fontWeight: 750}} testId="brand" />
    </div>
    <div style={{position: 'absolute', left: pad, top: contentTop, width: copyWidth, height: copyHeight, transform: `translateY(${(1 - enter) * 22 * u}px)`, opacity: enter}}>
      <FitText text={scene.headline} size={(square ? 70 : 98) * u} minimum={32 * u} style={{height: headingHeight, lineHeight: 1.05, letterSpacing: '-.055em', fontWeight: 800}} testId="headline" />
      <FitText text={scene.body} size={32 * u} minimum={19 * u} style={{height: copyHeight * .3, marginTop: copyHeight * .055, color: muted, lineHeight: 1.25}} testId="body" />
    </div>
    <div style={{position: 'absolute', left: visualLeft, top: visualTop, width: visualWidth, height: visualHeight}} data-layout="visual">
      {endCard ? <div style={{height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: 22 * u}}>
        {logo && <Img src={assetUrl(logo)} alt={manifest.name} style={{maxWidth: '55%', maxHeight: visualHeight * .32, objectFit: 'contain'}} />}
        <div style={{width: '96%', maxHeight: visualHeight * .26, minHeight: 65 * u, borderRadius: 30 * u, padding: `${14 * u}px ${22 * u}px`, background: accent, color: accentInk, boxSizing: 'border-box'}}>
          <FitText text={`${manifest.brief.cta} ↗`} size={34 * u} minimum={20 * u} style={{height: 76 * u, textAlign: 'center', fontWeight: 800}} testId="cta" />
        </div>
        <FitText text={manifest.brief.url || manifest.name} size={22 * u} minimum={14 * u} style={{height: 48 * u, width: '100%', color: muted, textAlign: 'center'}} testId="url" />
      </div> : hasMedia ? <div style={{width: '100%', height: '100%', borderRadius: 22 * u, background: editorial ? '#e6e7e8' : '#101722', overflow: 'hidden', border: `1px solid ${alpha(accent, '55')}`}}><Media manifest={manifest} scene={scene} index={index} /></div> : <div style={{height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 14 * u}}>
        {benefits.map((benefit, benefitIndex) => {
          const progress = spring({frame: frame - benefitIndex * 5, fps, config: {damping: 20, stiffness: 140}});
          const rowHeight = Math.min(visualHeight / Math.max(1, benefits.length) * .85, 150 * u);
          return <div key={`${benefit}-${benefitIndex}`} style={{height: rowHeight, display: 'flex', alignItems: 'center', gap: 18 * u, padding: `0 ${22 * u}px`, borderRadius: 18 * u, boxSizing: 'border-box', background: alpha(accent, '0c'), border: `1px solid ${alpha(accent, '45')}`, opacity: progress, transform: `translateX(${(1 - progress) * 30 * u}px)`}}>
            <span style={{color: accent, fontSize: 24 * u, fontWeight: 800}}>{String(benefitIndex + 1).padStart(2, '0')}</span>
            <FitText text={benefit} size={29 * u} minimum={18 * u} style={{height: rowHeight * .8, flex: 1, fontWeight: 650, lineHeight: 1.25}} testId="benefit" />
          </div>;
        })}
      </div>}
    </div>
    {manifest.narrated && scene.narration && <div style={{position: 'absolute', left: pad, right: pad, bottom: height * .035, height: captionHeight, padding: `${8 * u}px ${14 * u}px`, boxSizing: 'border-box', borderRadius: 14 * u, background: editorial ? '#ffffff' : '#06101ae8'}}>
      <FitText text={scene.narration} size={27 * u} minimum={17 * u} style={{height: '100%', textAlign: 'center', lineHeight: 1.3}} testId="caption" />
    </div>}
    <div style={{position: 'absolute', bottom: 0, left: 0, width: `${interpolate(frame, [0, scene.duration * fps], [0, 100])}%`, height: 3 * u, background: accent}} />
  </AbsoluteFill>;
};

export const ProjectAdComposition: React.FC<{manifest: ProjectManifest}> = ({manifest}) => {
  const {fps} = useVideoConfig();
  return <AbsoluteFill>
    {manifest.audio && <Audio src={assetUrl(manifest.audio)} volume={1} />}
    {manifest.scenes.map((scene, index) => {
      const from = Math.round(scene.start * fps);
      const end = Math.round(scene.end * fps);
      return <Sequence key={scene.id} from={from} durationInFrames={end - from} name={scene.id}><Scene manifest={manifest} scene={scene} index={index} /></Sequence>;
    })}
  </AbsoluteFill>;
};
