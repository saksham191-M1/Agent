import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {SceneRendererProps} from '../../../engine';
import {BrandLockup, BrowserMockup, CTAButton, Cursor, GlassCard, Glyph, PhoneMockup, SceneFrame, StatCounter} from '../../../engine';
import type {BrowserCard, PhoneItem} from '../../../engine';

const visual = <T,>(scene: SceneRendererProps['scene']) => scene.visual as T;

const SkillmeScene: React.FC<SceneRendererProps> = ({scene, tokens}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (scene.layout === 'hero-type') {
    const data = visual<{kicker: string; pulseText: string}>(scene);
    const slam = spring({frame, fps, config: {damping: 12, stiffness: 170}});
    const ring = interpolate(Math.min(1, frame / 36), [0, 1], [0.7, 1.08]);
    return <SceneFrame scene={scene} tokens={tokens}><div style={{position: 'absolute', top: 700, left: tokens.safe, right: tokens.safe, display: 'grid', placeItems: 'center'}}><div style={{position: 'relative', width: 520, height: 520, display: 'grid', placeItems: 'center', transform: `scale(${.72 + slam * .28}) rotate(${(1 - slam) * -8}deg)`}}><div style={{position: 'absolute', inset: 0, borderRadius: '50%', border: `2px solid ${tokens.colors.accent}66`, transform: `scale(${ring})`, opacity: Math.max(0, 1 - (ring - .7) * 2)}} /><div style={{position: 'absolute', inset: 48, borderRadius: '50%', border: `1px solid ${tokens.colors.accentLight}66`, transform: `scale(${1.18 - (ring - .7) * .5})`}} /><div style={{width: 300, height: 300, borderRadius: '50%', display: 'grid', placeItems: 'center', background: `radial-gradient(circle at 30% 25%, ${tokens.colors.accentLight}, ${tokens.colors.accent})`, boxShadow: `0 0 110px ${tokens.colors.accent}80`}}><BrandLockup tokens={tokens} large /></div></div><div style={{marginTop: 14, color: tokens.colors.accentLight, fontSize: 20, letterSpacing: '.16em', textTransform: 'uppercase'}}>{data.kicker}</div><div style={{marginTop: 24, color: tokens.colors.muted, fontSize: 27}}>{data.pulseText}</div></div></SceneFrame>;
  }
  if (scene.layout === 'browser') {
    const data = visual<{title: string; detail: string; location: string; cards: BrowserCard[]}>(scene);
    return <SceneFrame scene={scene} tokens={tokens}><div style={{position: 'absolute', top: 790, left: tokens.safe, right: tokens.safe}}><BrowserMockup tokens={tokens} {...data} showCursor /></div></SceneFrame>;
  }
  if (scene.layout === 'list') {
    const data = visual<{items: Array<{label: string; detail: string; icon: string}>}>(scene);
    return <SceneFrame scene={scene} tokens={tokens}><div style={{position: 'absolute', top: 760, left: tokens.safe, right: tokens.safe, display: 'grid', gap: 14}}>{data.items.map((item, index) => { const enter = spring({frame: frame - index * 6, fps, config: {damping: 14, stiffness: 150}}); return <GlassCard key={item.label} tokens={tokens} style={{height: 126, padding: 24, display: 'flex', alignItems: 'center', gap: 18, opacity: enter, transform: `translateX(${(1 - enter) * (index % 2 ? 70 : -70)}px)`}}><Glyph label={item.icon} tokens={tokens} size={52} /><div><div style={{fontSize: 25, fontWeight: 800}}>{item.label}</div><div style={{marginTop: 6, color: tokens.colors.muted, fontSize: 18}}>{item.detail}</div></div><div style={{marginLeft: 'auto', color: tokens.colors.accent, fontSize: 30}}>→</div></GlassCard>; })}</div></SceneFrame>;
  }
  if (scene.layout === 'phone') {
    const data = visual<{greeting: string; prompt: string; search: string; items: PhoneItem[]}>(scene);
    return <SceneFrame scene={scene} tokens={tokens}><div style={{position: 'absolute', top: 760, left: tokens.safe, right: tokens.safe, display: 'flex', justifyContent: 'center'}}><PhoneMockup tokens={tokens} {...data} /></div></SceneFrame>;
  }
  if (scene.layout === 'big-number') {
    const data = visual<{eyebrow: string; label: string; stats: Array<{value: number; suffix: string; label: string}>; progress: number; detail: string}>(scene);
    return <SceneFrame scene={scene} tokens={tokens}><GlassCard tokens={tokens} style={{position: 'absolute', left: tokens.safe, right: tokens.safe, top: 810, height: 520, padding: 40}}><div style={{display: 'flex', justifyContent: 'space-between', borderBottom: `1px solid ${tokens.colors.hairline}`, paddingBottom: 24, fontSize: 18, color: tokens.colors.accentLight, letterSpacing: '.08em', textTransform: 'uppercase'}}><span>{data.eyebrow}</span><span>{data.label}</span></div><div style={{display: 'flex', gap: 24, marginTop: 62}}>{data.stats.map((stat, index) => <StatCounter key={stat.label} tokens={tokens} {...stat} index={index} />)}</div><div style={{height: 12, background: tokens.colors.glass, borderRadius: 20, marginTop: 68, overflow: 'hidden'}}><div style={{height: '100%', width: `${data.progress}%`, borderRadius: 20, background: `linear-gradient(90deg, ${tokens.colors.accent}, ${tokens.colors.accentLight})`}} /></div><div style={{marginTop: 20, color: tokens.colors.muted, fontSize: 18}}>{data.detail}</div></GlassCard></SceneFrame>;
  }
  if (scene.layout === 'split') {
    const data = visual<{title: string; detail: string; location: string; cards: BrowserCard[]; sideLabel: string}>(scene);
    return <SceneFrame scene={scene} tokens={tokens}><div style={{position: 'absolute', top: 790, left: tokens.safe, right: tokens.safe, display: 'flex', gap: 20}}><BrowserMockup tokens={tokens} title={data.title} detail={data.detail} location={data.location} cards={data.cards} showCursor style={{width: 720, height: 620}} /><GlassCard tokens={tokens} style={{width: 220, minHeight: 620, padding: 22, display: 'flex', flexDirection: 'column', justifyContent: 'space-between'}}><div><Glyph tokens={tokens} label={data.sideLabel} size={54} /><div style={{marginTop: 20, fontSize: 25, fontWeight: 800}}>{data.sideLabel}</div></div><div style={{height: 180, borderRadius: 18, background: `${tokens.colors.accent}18`, display: 'grid', placeItems: 'center', color: tokens.colors.accent, fontSize: 70}}>✓</div></GlassCard></div></SceneFrame>;
  }
  const data = visual<{button: string; domain: string}>(scene);
  return <SceneFrame scene={scene} tokens={tokens}><div style={{position: 'absolute', top: 760, left: tokens.safe, right: tokens.safe, display: 'flex', flexDirection: 'column', alignItems: 'center'}}><div style={{width: 600, height: 250, borderRadius: 28, border: `1px solid ${tokens.colors.hairline}`, background: `linear-gradient(145deg, ${tokens.colors.glass}, ${tokens.colors.glass}55)`, display: 'flex', alignItems: 'center', justifyContent: 'center'}}><BrandLockup tokens={tokens} large /></div><div style={{position: 'relative', marginTop: 88}}><CTAButton tokens={tokens} label={data.button} clickFrame={30} width={480} /><Cursor tokens={tokens} from={[4, 30]} to={[77, 48]} start={14} clickAt={30} /></div><div style={{marginTop: 30, fontSize: 24, color: tokens.colors.muted}}>{data.domain}</div></div></SceneFrame>;
};

export default SkillmeScene;
