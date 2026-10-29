/**
 * ui-description-to-node.ts
 * ─────────────────────────
 * Translates structured UIDescription (from Playwright DOM crawl + Vision API)
 * into rich, brand-authentic VectorNodes for Remotion scenes.
 *
 * Prevents generic toy mockups by injecting:
 *  - Authentic brand header colors (e.g. Flipkart blue, Swiggy orange)
 *  - Real brand nav tabs (e.g. Home, Categories, Notifications, Account)
 *  - Real search placeholders
 *  - Real trust badges (e.g. 'Flipkart Assured', 'Free Delivery')
 *  - Scene 2 vs Scene 3 differentiation (Browse Phone Mockup -> Cinematic Product Deal Card)
 */

import fs from 'node:fs';
import path from 'node:path';
import type {UIDescription} from './scrape-brand';
import type {BrandJson} from '../engine/types';
import type {VectorNode, PhoneMockupNode, EcommerceProductCardNode} from '../engine/semantic-ui/types';

export function loadUIDescription(jobDir: string): UIDescription | null {
  const filePath = path.join(jobDir, 'ui_description.json');
  if (!fs.existsSync(filePath)) return null;
  try {
    const raw = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(raw);
  } catch (err) {
    console.warn(`[UI Desc] Failed reading ${filePath}:`, err);
    return null;
  }
}

export function hasUIDescription(jobDir: string): boolean {
  return fs.existsSync(path.join(jobDir, 'ui_description.json'));
}

export function buildNodeFromUIDescription(
  desc: UIDescription,
  brand: BrandJson,
  scene: any,
  sceneIdx: number,
  _totalScenes: number = 4
): VectorNode {
  const vo = (scene.voiceover || '').toLowerCase();
  const isEcommerce = desc.layout_type === 'ecommerce_grid' || /shop|buy|store|order|cart|discount|offer|deal|price|deliver/.test(`${brand.domain} ${brand.description} ${vo}`);
  const isCheckoutOrCart = /checkout|cart|payment|order summary|pay now|buy now/.test(vo);

  // If this is an ecommerce brand
  if (isEcommerce) {
    // If scene is middle/detail scene (e.g. Scene 3) and not explicitly a phone overview,
    // render a full authentic EcommerceProductCard instead of repeating the phone!
    const isProductHighlightScene = sceneIdx === 2 || /deal|price|discount|offer|save|assured|quality|choice|50%|off|rupee|₹|\$/.test(vo);

    if (isProductHighlightScene && !isCheckoutOrCart && sceneIdx !== 1) {
      const topBadge = desc.trust_badges?.[0] || '100% Genuine';
      const currentPrice = desc.price_style?.color ? '₹1,499' : '₹2,499';
      const originalPrice = '₹4,999';
      const discountPct = '70%';

      const productNode: EcommerceProductCardNode = {
        id: `node_ecommerce_card_${sceneIdx}`,
        type: 'ecommerce_product_card',
        position3D: [0, 0, 0],
        title: brand.products?.[0] || `${brand.name} Top Pick`,
        category: desc.brand_distinguishers?.[0] || 'Trending Now',
        currentPrice,
        originalPrice,
        discountPct,
        rating: 4.8,
        ratingCount: '48,200+ verified ratings',
        trustBadge: topBadge,
        deliveryTag: 'Free Express Delivery',
        accentColor: brand.colors.accent,
        cardBg: desc.card_style?.bg || brand.colors.surface,
        features: [
          `${topBadge} guaranteed`,
          '7 Days easy replacement policy',
          'Fast doorstep delivery & secure checkout',
        ],
      };
      return productNode;
    }

    // Phone mockup screen (Scene 2: browse feed or checkout)
    const brandTabs = desc.header.navLinks.length >= 3
      ? desc.header.navLinks.slice(0, 4)
      : ['Home', 'Categories', 'Orders', 'Account'];

    const items = (desc.brand_distinguishers.length >= 2
      ? desc.brand_distinguishers
      : brand.products.length >= 2
      ? brand.products
      : ['Top Deals', 'Best Sellers', 'New Launches', 'Discounts']
    ).slice(0, 4).map((label, i) => ({
      label,
      icon: ['⚡', '🎯', '✨', '🔥'][i] || '•',
    }));

    const phoneNode: PhoneMockupNode = {
      id: `node_phone_${sceneIdx}`,
      type: 'phone_mockup',
      position3D: [0, 0, 0],
      greeting: isCheckoutOrCart ? `Checkout • ${brand.name}` : `Welcome to ${brand.name}`,
      prompt: scene.voiceover?.slice(0, 60) || brand.tagline,
      search: desc.searchBar.placeholder || `Search ${brand.name}...`,
      items,
      navTabs: brandTabs,
      headerBg: desc.header.bg || brand.colors.accent,
      headerColor: '#FFFFFF',
      badges: desc.trust_badges,
      screenType: isCheckoutOrCart ? 'checkout' : 'grid',
      priceInfo: isCheckoutOrCart ? {currentPrice: '₹1,499', originalPrice: '₹4,999', discount: '70% OFF'} : undefined,
    };
    return phoneNode;
  }

  // Dashboard / SaaS motion
  if (desc.layout_type === 'dashboard') {
    return {
      id: `node_appframe_${sceneIdx}`,
      type: 'app_frame',
      position3D: [0, 0, 0],
      appName: brand.name,
      topbarTitle: scene.voiceover?.split('.')[0] || `${brand.name} Studio`,
      badgeText: '● Live',
      activePane: 'dashboard',
      sidebarItems: (desc.header.navLinks.length > 0 ? desc.header.navLinks : ['Overview', 'Analytics', 'Settings']).slice(0, 4).map(
        (p, i) => ({id: `s${i}`, label: p, active: i === 0})
      ),
    } as VectorNode;
  }

  // Default fallback to standard phone mockup with authentic brand tabs and header
  return {
    id: `node_phone_${sceneIdx}`,
    type: 'phone_mockup',
    position3D: [0, 0, 0],
    greeting: `Welcome to ${brand.name}`,
    prompt: scene.voiceover?.slice(0, 60) || brand.tagline,
    search: desc.searchBar.placeholder || `Search ${brand.name}...`,
    items: brand.products.slice(0, 4).map((p, i) => ({
      label: p,
      icon: ['🚀', '⚡', '🎯', '✨'][i] || '•',
    })),
    navTabs: desc.header.navLinks.length > 0 ? desc.header.navLinks.slice(0, 4) : ['Home', 'Orders', 'Account'],
    headerBg: desc.header.bg,
    headerColor: '#FFFFFF',
    badges: desc.trust_badges,
  } as VectorNode;
}
