import type {Tokens} from '../types';
import type {InteractionSpec} from './types';

export function getCategoryInteractionDefaults(
  category: string,
  tokens: Tokens
): InteractionSpec {
  const norm = (category || '').toLowerCase();

  if (norm.includes('fintech') || norm.includes('invest') || norm.includes('trad')) {
    return {
      ticker: {
        from: 0,
        to: 18.4,
        prefix: '+',
        suffix: '%',
        startFrame: 10,
        durationFrames: 40,
        decimals: 1,
      },
      cursor: {
        from: [20, 80],
        to: [30, 60],
        startFrame: 12,
        clickFrame: 52,
      },
      reactiveTarget: {
        targetIndex: 0,
        triggerFrame: 52,
        activeLabel: 'Executed',
        badgeText: '● FILLED',
        glow: true,
      },
      toast: {
        message: 'Order Executed at Market',
        icon: '✓',
        showAtFrame: 56,
        durationFrames: 60,
        type: 'success',
      },
    };
  }

  if (norm.includes('ecom') || norm.includes('food') || norm.includes('quick') || norm.includes('retail')) {
    return {
      typewriter: {
        text: `Search in ${tokens.name}...`,
        startFrame: 12,
        durationFrames: 24,
        showCursor: true,
      },
      cursor: {
        from: [15, 85],
        to: [28, 55],
        startFrame: 12,
        clickFrame: 48,
      },
      reactiveTarget: {
        targetIndex: 0,
        triggerFrame: 48,
        activeLabel: 'Added',
        badgeText: '✓ IN BAG',
        glow: true,
      },
      toast: {
        message: 'Added to Bag',
        icon: '+',
        showAtFrame: 52,
        durationFrames: 55,
        type: 'success',
      },
    };
  }

  // Default: SaaS, Developer Tools, Analytics, Education
  return {
    typewriter: {
      text: `Search ${tokens.name}...`,
      startFrame: 14,
      durationFrames: 24,
      showCursor: true,
    },
    cursor: {
      from: [12, 85],
      to: [22, 58],
      startFrame: 10,
      clickFrame: 54,
    },
    reactiveTarget: {
      targetIndex: 0,
      triggerFrame: 54,
      activeLabel: 'Opening →',
      badgeText: '● ACTIVE',
      glow: true,
    },
    toast: {
      message: 'Workspace Synchronized',
      icon: '✓',
      showAtFrame: 58,
      durationFrames: 60,
      type: 'info',
    },
  };
}
