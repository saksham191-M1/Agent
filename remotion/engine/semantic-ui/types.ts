export type Position3D = [number, number, number]; // [x, y, z]

export interface BaseVectorNode {
  id: string;
  position3D: Position3D;
  scale?: number;
  rotationDeg?: [number, number, number]; // [pitch, yaw, roll]
  opacity?: number;
}

export interface MetricCardNode extends BaseVectorNode {
  type: 'metric_card';
  label: string;
  value: string;
  delta: string;
  chartPoints: number[];
  accentColor?: string;
}

export interface AssetCardNode extends BaseVectorNode {
  type: 'asset_card';
  assetUrl: string;
  scaleMode: 'contain' | 'cover';
  cropRegion?: [number, number, number, number]; // [x, y, w, h]
  title?: string;
  subtitle?: string;
}

export interface BentoGridItem {
  id: string;
  title: string;
  subtitle: string;
  icon?: string;
  metric?: string;
  colSpan?: number;
  rowSpan?: number;
  accent?: string;
}

export interface BentoGridNode extends BaseVectorNode {
  type: 'bento_grid';
  columns: number;
  cards: BentoGridItem[];
  gap?: number;
}

export interface ToggleSwitchNode extends BaseVectorNode {
  type: 'toggle_switch';
  label: string;
  state: 'active' | 'inactive';
  activeColor?: string;
}

export interface PillTagNode extends BaseVectorNode {
  type: 'pill_tag';
  text: string;
  icon?: string;
  variant: 'glass' | 'solid' | 'outline';
  accent?: string;
}

export interface InteractiveInputNode extends BaseVectorNode {
  type: 'interactive_input';
  placeholder: string;
  typedValue: string;
  cursorPosition: number;
  buttonLabel?: string;
}

export interface NotificationToastNode extends BaseVectorNode {
  type: 'notification_toast';
  title: string;
  description: string;
  timeAgo: string;
  avatarUrl?: string;
}

export interface ChartSkillNode extends BaseVectorNode {
  type: 'chart';
  chartType: 'bar' | 'line' | 'area';
  title: string;
  data: { label: string; value: number }[];
  accentColor?: string;
  showAxis?: boolean;
}

export interface TypographySkillNode extends BaseVectorNode {
  type: 'kinetic_typography';
  effect: 'typewriter' | 'word_carousel' | 'phrase_flash';
  words?: string[];
  text?: string;
  subtext?: string;
  fontSize?: number;
}

export interface MessagingSkillNode extends BaseVectorNode {
  type: 'chat_messaging';
  messages: { id: string; sender: 'user' | 'agent' | 'system'; text: string; time?: string; avatar?: string }[];
  typingIndicator?: boolean;
}

export interface CinematicAppFrameNode extends BaseVectorNode {
  type: 'app_frame';
  appName: string;
  sidebarItems: { id: string; label: string; icon?: string; active?: boolean }[];
  topbarTitle: string;
  badgeText?: string;
  activePane?: 'dashboard' | 'editor' | 'analytics';
}

export interface PhoneMockupNode extends BaseVectorNode {
  type: 'phone_mockup';
  greeting: string;
  prompt: string;
  search: string;
  items: { label: string; icon: string }[];
  navTabs?: string[];
  headerBg?: string;
  headerColor?: string;
  badges?: string[];
  priceInfo?: {currentPrice: string; originalPrice?: string; discount?: string};
  screenType?: 'grid' | 'product_detail' | 'checkout' | 'feed';
}

export interface EcommerceProductCardNode extends BaseVectorNode {
  type: 'ecommerce_product_card';
  title: string;
  category?: string;
  currentPrice: string;
  originalPrice?: string;
  discountPct?: string;
  rating?: number;
  ratingCount?: string;
  trustBadge?: string;
  deliveryTag?: string;
  accentColor?: string;
  cardBg?: string;
  features?: string[];
}

export interface BrowserMockupNode extends BaseVectorNode {
  type: 'browser_mockup';
  title: string;
  detail: string;
  location: string;
  cards: { label: string; detail: string; action: string; icon: string }[];
  showCursor?: boolean;
}

export interface SmartCursorNode extends BaseVectorNode {
  type: 'smart_cursor';
  waypoints?: Array<{frame: number; x: number; y: number; click?: boolean}>;
  accentColor?: string;
}

export interface CTAButtonNode extends BaseVectorNode {
  type: 'cta_button';
  label: string;
  clickFrame?: number;
  width?: number;
}

export interface StatCounterNode extends BaseVectorNode {
  type: 'stat_counter';
  value: number;
  suffix?: string;
  label: string;
  index?: number;
}

export type VectorNode =
  | MetricCardNode
  | AssetCardNode
  | BentoGridNode
  | ToggleSwitchNode
  | PillTagNode
  | InteractiveInputNode
  | NotificationToastNode
  | ChartSkillNode
  | TypographySkillNode
  | MessagingSkillNode
  | CinematicAppFrameNode
  | PhoneMockupNode
  | BrowserMockupNode
  | SmartCursorNode
  | CTAButtonNode
  | StatCounterNode
  | EcommerceProductCardNode;

export interface UITree {
  brandId: string;
  worldBounds: { width: number; height: number; depth: number };
  nodes: VectorNode[];
}
