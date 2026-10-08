import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {SceneRendererProps} from '../../../engine';
import {BrandLockup, BrowserMockup, CTAButton, Cursor, GlassCard, Glyph, PhoneMockup, SceneFrame, StatCounter} from '../../../engine';
import type {BrowserCard, PhoneItem} from '../../../engine';

const visual = <T,>(scene: SceneRendererProps['scene']) => scene.visual as T;

const PulseHero: React.FC<{scene: SceneRendererProps['scene']; tokens: SceneRendererProps['tokens']; data: {kicker: string; pulseText: string}}> = ({scene, tokens, data}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const slam = spring({frame, fps, config: {damping: 12, stiffness: 170}});
  const ring = interpolate(Math.min(1, frame / 36), [0, 1], [0.7, 1.08]);
  return <SceneFrame scene={scene} tokens={tokens}>
    <div style={{position: 'absolute', top: 700, left: tokens.safe, right: tokens.safe, display: 'grid', placeItems: 'center'}}>
      <div style={{position: 'relative', width: 520, height: 520, display: 'grid', placeItems: 'center', transform: `scale(${.72 + slam * .28}) rotate(${(1 - slam) * -9}deg)`}}>
        <div style={{position: 'absolute', inset: 0, borderRadius: '50%', border: `2px solid ${tokens.colors.accent}66`, transform: `scale(${ring})`, opacity: Math.max(0, 1 - (ring - .7) * 2)}} />
        <div style={{position: 'absolute', inset: 48, borderRadius: '50%', border: `1px solid ${tokens.colors.accentLight}66`, transform: `scale(${1.18 - (ring - .7) * .5})`}} />
        <div style={{width: 300, height: 300, borderRadius: '50%', display: 'grid', placeItems: 'center', background: `radial-gradient(circle at 30% 25%, ${tokens.colors.accentLight}, ${tokens.colors.accent})`, color: tokens.colors.surfaceText, boxShadow: `0 0 110px ${tokens.colors.accent}99`}}><BrandLockup tokens={tokens} large /></div>
      </div>
      <div style={{marginTop: 14, color: tokens.colors.accentLight, fontSize: 20, letterSpacing: '.16em', textTransform: 'uppercase'}}>{data.kicker}</div>
      <div style={{marginTop: 24, color: tokens.colors.muted, fontSize: 27}}>{data.pulseText}</div>
    </div>
  </SceneFrame>;
};

const SwiggyScene: React.FC<SceneRendererProps> = ({scene, tokens}) => {
  if (scene.layout === 'hero-type') {
    const data = visual<{kicker: string; pulseText: string}>(scene);
    return <PulseHero scene={scene} tokens={tokens} data={data} />;
  }
  if (scene.layout === 'phone') {
    const data = visual<{greeting: string; prompt: string; search: string; items: PhoneItem[]}>(scene);
    return <SceneFrame scene={scene} tokens={tokens}><div style={{position: 'absolute', left: tokens.safe, right: tokens.safe, top: 760, height: 720, display: 'flex', alignItems: 'center', justifyContent: 'center'}}><PhoneMockup tokens={tokens} greeting={data.greeting} prompt={data.prompt} search={data.search} items={data.items} style={{position: 'absolute', right: 80, top: 0}} /></div></SceneFrame>;
  }
  if (scene.layout === 'browser') {
    const data = visual<{title: string; detail: string; location: string; cards: BrowserCard[]}>(scene);
    return <SceneFrame scene={scene} tokens={tokens}><div style={{position: 'absolute', top: 790, left: tokens.safe, right: tokens.safe}}><BrowserMockup tokens={tokens} {...data} showCursor /></div></SceneFrame>;
  }
  if (scene.layout === 'split') {
    const data = visual<{title: string; detail: string; location: string; cards: BrowserCard[]; sideLabel: string}>(scene);
    return <SceneFrame scene={scene} tokens={tokens}><div style={{position: 'absolute', top: 790, left: tokens.safe, right: tokens.safe, display: 'flex', gap: 22, alignItems: 'stretch'}}><BrowserMockup tokens={tokens} title={data.title} detail={data.detail} location={data.location} cards={data.cards} showCursor style={{width: 720, height: 620}} /><GlassCard tokens={tokens} style={{width: 220, minHeight: 620, padding: 24, display: 'flex', flexDirection: 'column', justifyContent: 'space-between'}}><div><Glyph tokens={tokens} label={data.sideLabel} size={54} /><div style={{marginTop: 24, fontSize: 26, fontWeight: 800}}>{data.sideLabel}</div></div><div style={{height: 180, borderRadius: 18, background: `${tokens.colors.accent}18`, display: 'grid', placeItems: 'center', color: tokens.colors.accent, fontSize: 74}}>↗</div></GlassCard></div></SceneFrame>;
  }
  if (scene.layout === 'list') {
    const data = visual<{items: Array<{label: string; detail: string; icon: string}>}>(scene);
    const frame = useCurrentFrame();
    const {fps} = useVideoConfig();
    return <SceneFrame scene={scene} tokens={tokens}><div style={{position: 'absolute', top: 800, left: tokens.safe, right: tokens.safe, display: 'grid', gap: 18}}>{data.items.map((item, index) => { const enter = spring({frame: frame - index * 6, fps, config: {damping: 14, stiffness: 150}}); return <GlassCard key={item.label} tokens={tokens} style={{height: 150, padding: 30, display: 'flex', alignItems: 'center', gap: 22, opacity: enter, transform: `translateX(${(1 - enter) * (index % 2 ? 80 : -80)}px) rotate(${(1 - enter) * (index % 2 ? 2 : -2)}deg)`}}><Glyph label={item.icon} tokens={tokens} size={58} /><div><div style={{fontSize: 28, fontWeight: 800}}>{item.label}</div><div style={{marginTop: 8, color: tokens.colors.muted, fontSize: 20}}>{item.detail}</div></div><div style={{marginLeft: 'auto', color: tokens.colors.accent, fontSize: 32}}>→</div></GlassCard>; })}</div></SceneFrame>;
  }
  if (scene.layout === 'big-number') {
    const data = visual<{eyebrow: string; label: string; stats: Array<{value: number; suffix: string; label: string}>; progress: number; detail: string}>(scene);
    return <SceneFrame scene={scene} tokens={tokens}><GlassCard tokens={tokens} style={{position: 'absolute', left: tokens.safe, right: tokens.safe, top: 810, height: 520, padding: 40}}><div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: `1px solid ${tokens.colors.hairline}`, paddingBottom: 26}}><div style={{fontSize: 23, fontWeight: 700}}>{data.eyebrow}</div><div style={{fontSize: 17, color: tokens.colors.accent}}>{data.label}</div></div><div style={{display: 'flex', gap: 26, marginTop: 62}}>{data.stats.map((stat, index) => <StatCounter key={stat.label} tokens={tokens} {...stat} index={index} />)}</div><div style={{height: 12, background: tokens.colors.glass, borderRadius: 20, marginTop: 70, overflow: 'hidden'}}><div style={{height: '100%', width: `${data.progress}%`, borderRadius: 20, background: `linear-gradient(90deg, ${tokens.colors.accent}, ${tokens.colors.accentLight})`}} /></div><div style={{marginTop: 20, color: tokens.colors.muted, fontSize: 18}}>{data.detail}</div></GlassCard></SceneFrame>;
  }
  const data = visual<{button: string; domain: string}>(scene);
  return <SceneFrame scene={scene} tokens={tokens}><div style={{position: 'absolute', top: 760, left: tokens.safe, right: tokens.safe, display: 'flex', flexDirection: 'column', alignItems: 'center'}}><div style={{width: 600, height: 250, borderRadius: 28, border: `1px solid ${tokens.colors.hairline}`, background: `linear-gradient(145deg, ${tokens.colors.glass}, ${tokens.colors.glass}55)`, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: `0 25px 75px ${tokens.colors.background}4d`}}><BrandLockup tokens={tokens} large /></div><div style={{position: 'relative', marginTop: 92}}><CTAButton tokens={tokens} label={data.button} clickFrame={28} width={480} /><Cursor tokens={tokens} from={[4, 30]} to={[77, 48]} start={12} clickAt={28} /></div><div style={{fontSize: 24, color: tokens.colors.muted, marginTop: 32}}>{data.domain}</div></div></SceneFrame>;
};

export default SwiggyScene;
