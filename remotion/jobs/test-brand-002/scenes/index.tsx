import React from 'react';
import type {SceneRendererProps} from '../../../engine';
import {BrandLockup, CTAButton, Cursor, GlassCard, Glyph, PhoneMockup, SceneFrame, StatCounter} from '../../../engine';
import type {PhoneItem} from '../../../engine';

const visual = <T,>(scene: SceneRendererProps['scene']) => scene.visual as T;

const AsterScene: React.FC<SceneRendererProps> = ({scene, tokens}) => {
  if (scene.layout === 'hero-type') {
    const data = visual<{orbLabel: string; kicker: string}>(scene);
    return <SceneFrame scene={scene} tokens={tokens}><div style={{position: 'absolute', top: 780, left: tokens.safe, right: tokens.safe, display: 'grid', placeItems: 'center'}}><div style={{width: 410, height: 410, borderRadius: '50%', display: 'grid', placeItems: 'center', background: `radial-gradient(circle at 30% 25%, ${tokens.colors.accentLight}, ${tokens.colors.accent})`, color: tokens.colors.surfaceText, fontFamily: tokens.displayFontFamily, fontSize: 180, fontWeight: 800, boxShadow: `0 0 100px ${tokens.colors.accent}80`}}>{data.orbLabel}</div><div style={{marginTop: 38, color: tokens.colors.accentLight, fontSize: 20, letterSpacing: '.18em', textTransform: 'uppercase'}}>{data.kicker}</div></div></SceneFrame>;
  }
  if (scene.layout === 'list') {
    const data = visual<{items: Array<{label: string; detail: string; icon: string}>}>(scene);
    return <SceneFrame scene={scene} tokens={tokens}><div style={{position: 'absolute', top: 800, left: tokens.safe, right: tokens.safe, display: 'grid', gap: 18}}>{data.items.map((item, index) => <GlassCard key={item.label} tokens={tokens} style={{height: 150, padding: 30, display: 'flex', alignItems: 'center', gap: 22, transform: `translateX(${index % 2 ? 18 : -18}px)`}}><Glyph label={item.icon} tokens={tokens} size={58} /><div><div style={{fontSize: 28, fontWeight: 800}}>{item.label}</div><div style={{marginTop: 8, color: tokens.colors.muted, fontSize: 20}}>{item.detail}</div></div><div style={{marginLeft: 'auto', color: tokens.colors.accent, fontSize: 28}}>→</div></GlassCard>)}</div></SceneFrame>;
  }
  if (scene.layout === 'phone') {
    const data = visual<{greeting: string; prompt: string; search: string; items: PhoneItem[]}>(scene);
    return <SceneFrame scene={scene} tokens={tokens}><div style={{position: 'absolute', top: 760, left: tokens.safe, right: tokens.safe, display: 'flex', justifyContent: 'center'}}><PhoneMockup tokens={tokens} {...data} /></div></SceneFrame>;
  }
  if (scene.layout === 'big-number') {
    const data = visual<{eyebrow: string; label: string; stats: Array<{value: number; suffix: string; label: string}>; progress: number; detail: string}>(scene);
    return <SceneFrame scene={scene} tokens={tokens}><GlassCard tokens={tokens} style={{position: 'absolute', top: 820, left: tokens.safe, right: tokens.safe, padding: 42}}><div style={{display: 'flex', justifyContent: 'space-between', color: tokens.colors.accentLight, fontSize: 20, letterSpacing: '.1em', textTransform: 'uppercase'}}><span>{data.eyebrow}</span><span>{data.label}</span></div><div style={{display: 'flex', gap: 26, marginTop: 72}}>{data.stats.map((stat, index) => <StatCounter key={stat.label} tokens={tokens} {...stat} index={index} />)}</div><div style={{height: 12, background: tokens.colors.glass, borderRadius: 20, marginTop: 72, overflow: 'hidden'}}><div style={{height: '100%', width: `${data.progress}%`, background: tokens.colors.accent, borderRadius: 20}} /></div><div style={{marginTop: 24, color: tokens.colors.muted, fontSize: 20}}>{data.detail}</div></GlassCard></SceneFrame>;
  }
  const data = visual<{button: string; domain: string}>(scene);
  return <SceneFrame scene={scene} tokens={tokens}><div style={{position: 'absolute', top: 800, left: tokens.safe, right: tokens.safe, display: 'flex', flexDirection: 'column', alignItems: 'center'}}><BrandLockup tokens={tokens} large /><div style={{position: 'relative', marginTop: 100}}><CTAButton tokens={tokens} label={data.button} clickFrame={36} width={480} /><Cursor tokens={tokens} from={[4, 30]} to={[77, 48]} start={16} clickAt={36} /></div><div style={{marginTop: 34, fontSize: 24, color: tokens.colors.muted}}>{data.domain}</div></div></SceneFrame>;
};

export default AsterScene;
