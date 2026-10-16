import type {BrandJson} from '../types';
import type {UITree, VectorNode} from '../semantic-ui/types';
import type {CameraFlightPath} from '../stage/types';
import {CameraCoordinateAdapter} from '../stage/CameraCoordinateAdapter';

export interface ProjectBuildConfig {
  compName: string;
  width: number;
  height: number;
  fps: number;
  durationSec: number;
  brand: BrandJson;
  uiTree: UITree;
  cameraFlight: CameraFlightPath;
  outputEcprojPath: string;
}

function hexToRgb(hex?: string): [number, number, number] {
  if (!hex || !/^#[0-9a-f]{6}$/i.test(hex)) return [0.24, 0.81, 0.56];
  const clean = hex.replace('#', '');
  const r = parseInt(clean.substring(0, 2), 16) / 255;
  const g = parseInt(clean.substring(2, 4), 16) / 255;
  const b = parseInt(clean.substring(4, 6), 16) / 255;
  return [
    Math.round(r * 100) / 100,
    Math.round(g * 100) / 100,
    Math.round(b * 100) / 100,
  ];
}

/**
 * Emits an agency-tier Bento Card Shape Layer in ExtendScript:
 * - Rounded rectangle vector path (radius: 18px)
 * - Dark frosted glass fill (hex #0E1017, 92% opacity)
 * - 1.5px subtle hairline stroke (14% white highlight)
 * - Micro-pill badge with tracked monospace category
 * - Primary typography with Inter / Geist hierarchy
 */
export function buildBentoCardExtendScript(
  node: {
    id: string;
    title: string;
    subtitle?: string;
    tag?: string;
    width: number;
    height: number;
    position3D: [number, number, number];
  }
): string {
  const [posX, posY, posZ] = node.position3D;
  const halfW = node.width / 2;
  const halfH = node.height / 2;
  const safeId = node.id.replace(/[^a-zA-Z0-9_]/g, '_');

  const safeTitle = (node.title || '').replace(/'/g, "\\'");
  const safeSubtitle = (node.subtitle || '').replace(/'/g, "\\'");
  const safeTag = (node.tag || '').replace(/'/g, "\\'");

  return `
  // ── Bento Card Container: ${node.id} ─────────────────────────────
  var cardShape_${safeId} = comp.layers.addShape();
  cardShape_${safeId}.name = "BentoCard_${safeId}";
  cardShape_${safeId}.threeDLayer = true;
  cardShape_${safeId}.transform.position.setValue([${posX}, ${posY}, ${posZ}]);

  // Card Shape Group
  var shapeContents_${safeId} = cardShape_${safeId}.property("Contents");
  var rectGroup_${safeId} = shapeContents_${safeId}.addProperty("ADBE Vector Group");
  var groupContents_${safeId} = rectGroup_${safeId}.property("Contents");

  // Rounded Rectangle Geometry
  var rect_${safeId} = groupContents_${safeId}.addProperty("ADBE Vector Shape - Rect");
  rect_${safeId}.property("Size").setValue([${node.width}, ${node.height}]);
  rect_${safeId}.property("Roundness").setValue(18); // 18px smooth corners

  // Dark Surface Fill (#0E1017)
  var fill_${safeId} = groupContents_${safeId}.addProperty("ADBE Vector Graphic - Fill");
  fill_${safeId}.property("Color").setValue([0.055, 0.063, 0.090]);
  fill_${safeId}.property("Opacity").setValue(94);

  // 1px Hairline Stroke (15% white catching camera light)
  var stroke_${safeId} = groupContents_${safeId}.addProperty("ADBE Vector Graphic - Stroke");
  stroke_${safeId}.property("Color").setValue([0.35, 0.40, 0.50]);
  stroke_${safeId}.property("Stroke Width").setValue(1.5);
  stroke_${safeId}.property("Opacity").setValue(28);

  // ── Category Pill Badge (Uppercase Mono) ──────────────────────────
  ${safeTag ? `
  var tagText_${safeId} = comp.layers.addText("${safeTag.toUpperCase()}");
  tagText_${safeId}.threeDLayer = true;
  var tagDoc_${safeId} = tagText_${safeId}.text.sourceText.value;
  tagDoc_${safeId}.fontSize = 11;
  tagDoc_${safeId}.font = "JetBrainsMono-Bold";
  tagDoc_${safeId}.fillColor = [0.38, 0.55, 0.95]; // Brand accent blue
  tagDoc_${safeId}.tracking = 100; // Wide letter spacing
  tagDoc_${safeId}.justification = ParagraphJustification.LEFT_JUSTIFY;
  tagText_${safeId}.text.sourceText.setValue(tagDoc_${safeId});
  tagText_${safeId}.transform.position.setValue([${posX - halfW + 32}, ${posY - halfH + 38}, ${posZ - 2}]);
  ` : ''}

  // ── Primary Header Typography ────────────────────────────────────
  var titleText_${safeId} = comp.layers.addText("${safeTitle}");
  titleText_${safeId}.threeDLayer = true;
  var titleDoc_${safeId} = titleText_${safeId}.text.sourceText.value;
  titleDoc_${safeId}.fontSize = 26;
  titleDoc_${safeId}.font = "Inter-Bold";
  titleDoc_${safeId}.fillColor = [0.96, 0.97, 0.99]; // Crisp off-white
  titleDoc_${safeId}.tracking = -25; // Tight modern tracking
  titleDoc_${safeId}.justification = ParagraphJustification.LEFT_JUSTIFY;
  titleText_${safeId}.text.sourceText.setValue(titleDoc_${safeId});
  titleText_${safeId}.transform.position.setValue([${posX - halfW + 32}, ${posY - halfH + (safeTag ? 76 : 48)}, ${posZ - 2}]);

  // ── Secondary Subtitle / Value ───────────────────────────────────
  ${safeSubtitle ? `
  var subText_${safeId} = comp.layers.addText("${safeSubtitle}");
  subText_${safeId}.threeDLayer = true;
  var subDoc_${safeId} = subText_${safeId}.text.sourceText.value;
  subDoc_${safeId}.fontSize = 15;
  subDoc_${safeId}.font = "Inter-Regular";
  subDoc_${safeId}.fillColor = [0.55, 0.58, 0.65]; // Muted secondary text
  subDoc_${safeId}.justification = ParagraphJustification.LEFT_JUSTIFY;
  subText_${safeId}.text.sourceText.setValue(subDoc_${safeId});
  subText_${safeId}.transform.position.setValue([${posX - halfW + 32}, ${posY - halfH + (safeTag ? 112 : 84)}, ${posZ - 2}]);
  ` : ''}
  `;
}

export class EcprojBuilder {
  /**
   * Generates an After Effects ExtendScript JSX file that constructs the entire
   * 3D continuous camera stage, cards, typography, and bezier keyframes in EffectCraft.
   */
  static generateJsxScript(config: ProjectBuildConfig): string {
    const {compName, width, height, fps, durationSec, brand, uiTree, cameraFlight} = config;
    const adapter = new CameraCoordinateAdapter({width, height});
    const accentRgb = hexToRgb(brand.colors.accent);

    const lines: string[] = [];
    lines.push(`// Generated by EcprojBuilder for EffectCraft (Agency-Tier Motion Engine)`);
    lines.push(`var comp = app.project.items.addComp('${compName}', ${width}, ${height}, 1.0, ${durationSec}, ${fps});`);
    lines.push(`comp.bgColor = [0.03, 0.04, 0.07];`);

    // Helper text styler function inside ExtendScript
    lines.push(`function styleText(txtLayer, size, r, g, b, justify) {`);
    lines.push(`  var doc = txtLayer.text.sourceText.value;`);
    lines.push(`  doc.fontSize = size;`);
    lines.push(`  doc.fillColor = [r, g, b];`);
    lines.push(`  doc.font = 'Inter';`);
    lines.push(`  if (justify) doc.justification = justify;`);
    lines.push(`  txtLayer.text.sourceText.setValue(doc);`);
    lines.push(`}`);

    // 1. Ambient Background Light Plate & Vignette Depth Accent
    lines.push(`// 1. Ambient Background Light Plate (Placed at Z = +400 behind all 3D cards)`);
    lines.push(`var bgPlate = comp.layers.addSolid([0.025, 0.030, 0.045], 'Background Environment', ${width * 2}, ${height * 2}, 1.0);`);
    lines.push(`bgPlate.threeDLayer = true;`);
    lines.push(`bgPlate.transform.position.setValue([${width / 2}, ${height / 2}, 400]);`);

    lines.push(`// Vignette / Depth Accent`);
    lines.push(`var ambientGlow = comp.layers.addSolid([0.10, 0.15, 0.30], 'Ambient Core Glow', 1600, 1000, 1.0);`);
    lines.push(`ambientGlow.threeDLayer = true;`);
    lines.push(`ambientGlow.transform.position.setValue([${width / 2}, ${height / 2}, 390]);`);
    lines.push(`ambientGlow.transform.opacity.setValue(22);`);

    // 2. Add 3D Camera Rig with direct property keyframing
    lines.push(`// 2. Active 3D Production Camera`);
    lines.push(`var camera = comp.layers.addCamera('Main Camera', [${width / 2}, ${height / 2}]);`);

    if (cameraFlight.waypoints.length > 0) {
      lines.push(`// Keyframing 3D Camera Flight Path`);
      cameraFlight.waypoints.forEach((wp) => {
        const ec = adapter.toEffectCraft(wp);
        lines.push(`camera.transform.position.setValueAtTime(${wp.timeSec}, [${ec.position[0]}, ${ec.position[1]}, ${ec.position[2]}]);`);
        lines.push(`camera.transform.pointOfInterest.setValueAtTime(${wp.timeSec}, [${ec.pointOfInterest[0]}, ${ec.pointOfInterest[1]}, ${ec.pointOfInterest[2]}]);`);
      });
    }

    // 3. Instantiate Vector & Shape Nodes as 3D Layers
    lines.push(`// 3. Spatial Stage Vector Nodes`);
    uiTree.nodes.forEach((node: VectorNode, index: number) => {
      const posX = width / 2 + node.position3D[0];
      const posY = height / 2 - node.position3D[1]; // Y-inverted for After Effects coordinates
      const posZ = node.position3D[2];
      const safeId = node.id.replace(/[^a-zA-Z0-9_]/g, '_');

      if (node.type === 'interactive_input') {
        const cardW = 860;
        const cardH = 110;
        lines.push(`// Node [${index}]: Interactive Input (${node.id})`);

        // Rounded vector shape container
        lines.push(`var inputShape_${safeId} = comp.layers.addShape();`);
        lines.push(`inputShape_${safeId}.name = "InputCard_${safeId}";`);
        lines.push(`inputShape_${safeId}.threeDLayer = true;`);
        lines.push(`inputShape_${safeId}.transform.position.setValue([${posX}, ${posY}, ${posZ}]);`);

        lines.push(`var inContents_${safeId} = inputShape_${safeId}.property("Contents");`);
        lines.push(`var inGroup_${safeId} = inContents_${safeId}.addProperty("ADBE Vector Group");`);
        lines.push(`var inGrpCont_${safeId} = inGroup_${safeId}.property("Contents");`);

        lines.push(`var inRect_${safeId} = inGrpCont_${safeId}.addProperty("ADBE Vector Shape - Rect");`);
        lines.push(`inRect_${safeId}.property("Size").setValue([${cardW}, ${cardH}]);`);
        lines.push(`inRect_${safeId}.property("Roundness").setValue(14);`);

        lines.push(`var inFill_${safeId} = inGrpCont_${safeId}.addProperty("ADBE Vector Graphic - Fill");`);
        lines.push(`inFill_${safeId}.property("Color").setValue([0.055, 0.065, 0.095]);`);
        lines.push(`inFill_${safeId}.property("Opacity").setValue(94);`);

        lines.push(`var inStroke_${safeId} = inGrpCont_${safeId}.addProperty("ADBE Vector Graphic - Stroke");`);
        lines.push(`inStroke_${safeId}.property("Color").setValue([0.35, 0.40, 0.50]);`);
        lines.push(`inStroke_${safeId}.property("Stroke Width").setValue(1.5);`);
        lines.push(`inStroke_${safeId}.property("Opacity").setValue(28);`);

        const promptText = (node.typedValue || node.placeholder).replace(/'/g, "\\'");
        lines.push(`var txt_${index} = comp.layers.addText('${promptText}');`);
        lines.push(`txt_${index}.threeDLayer = true;`);
        lines.push(`txt_${index}.transform.position.setValue([${posX - cardW / 2 + 36}, ${posY + 6}, ${posZ - 5}]);`);
        lines.push(`styleText(txt_${index}, 22, 0.93, 0.93, 0.93, ParagraphJustification.LEFT_JUSTIFY);`);

        // Button pill on the right side
        const btnLabel = (node.buttonLabel || 'RUN').replace(/'/g, "\\'");
        const btnW = 140;
        const btnH = 46;

        lines.push(`var btnShape_${safeId} = comp.layers.addShape();`);
        lines.push(`btnShape_${safeId}.name = "Button_${safeId}";`);
        lines.push(`btnShape_${safeId}.threeDLayer = true;`);
        lines.push(`btnShape_${safeId}.transform.position.setValue([${posX + cardW / 2 - btnW / 2 - 20}, ${posY}, ${posZ - 6}]);`);

        lines.push(`var btnCont_${safeId} = btnShape_${safeId}.property("Contents");`);
        lines.push(`var btnGrp_${safeId} = btnCont_${safeId}.addProperty("ADBE Vector Group");`);
        lines.push(`var btnGrpCont_${safeId} = btnGrp_${safeId}.property("Contents");`);

        lines.push(`var btnRect_${safeId} = btnGrpCont_${safeId}.addProperty("ADBE Vector Shape - Rect");`);
        lines.push(`btnRect_${safeId}.property("Size").setValue([${btnW}, ${btnH}]);`);
        lines.push(`btnRect_${safeId}.property("Roundness").setValue(10);`);

        lines.push(`var btnFill_${safeId} = btnGrpCont_${safeId}.addProperty("ADBE Vector Graphic - Fill");`);
        lines.push(`btnFill_${safeId}.property("Color").setValue([${accentRgb.join(', ')}]);`);

        lines.push(`var btnTxt_${index} = comp.layers.addText('${btnLabel}');`);
        lines.push(`btnTxt_${index}.threeDLayer = true;`);
        lines.push(`btnTxt_${index}.transform.position.setValue([${posX + cardW / 2 - btnW / 2 - 20}, ${posY + 5}, ${posZ - 10}]);`);
        lines.push(`styleText(btnTxt_${index}, 16, 0.04, 0.06, 0.05, ParagraphJustification.CENTER_JUSTIFY);`);
      } else if (node.type === 'pill_tag') {
        const pillW = 280;
        const pillH = 50;
        const nodeAccent = hexToRgb(node.accent);
        lines.push(`// Node [${index}]: Pill Tag (${node.id})`);

        lines.push(`var pillShape_${safeId} = comp.layers.addShape();`);
        lines.push(`pillShape_${safeId}.name = "Pill_${safeId}";`);
        lines.push(`pillShape_${safeId}.threeDLayer = true;`);
        lines.push(`pillShape_${safeId}.transform.position.setValue([${posX}, ${posY}, ${posZ}]);`);

        lines.push(`var pillCont_${safeId} = pillShape_${safeId}.property("Contents");`);
        lines.push(`var pillGrp_${safeId} = pillCont_${safeId}.addProperty("ADBE Vector Group");`);
        lines.push(`var pillGrpCont_${safeId} = pillGrp_${safeId}.property("Contents");`);

        lines.push(`var pillRect_${safeId} = pillGrpCont_${safeId}.addProperty("ADBE Vector Shape - Rect");`);
        lines.push(`pillRect_${safeId}.property("Size").setValue([${pillW}, ${pillH}]);`);
        lines.push(`pillRect_${safeId}.property("Roundness").setValue(25);`);

        lines.push(`var pillFill_${safeId} = pillGrpCont_${safeId}.addProperty("ADBE Vector Graphic - Fill");`);
        lines.push(`pillFill_${safeId}.property("Color").setValue([${nodeAccent[0] * 0.25}, ${nodeAccent[1] * 0.25}, ${nodeAccent[2] * 0.25}]);`);
        lines.push(`pillFill_${safeId}.property("Opacity").setValue(85);`);

        lines.push(`var pillStroke_${safeId} = pillGrpCont_${safeId}.addProperty("ADBE Vector Graphic - Stroke");`);
        lines.push(`pillStroke_${safeId}.property("Color").setValue([${nodeAccent.join(', ')}]);`);
        lines.push(`pillStroke_${safeId}.property("Stroke Width").setValue(1.5);`);
        lines.push(`pillStroke_${safeId}.property("Opacity").setValue(50);`);

        const pillText = node.text.replace(/'/g, "\\'");
        lines.push(`var pillTxt_${index} = comp.layers.addText('${pillText}');`);
        lines.push(`pillTxt_${index}.threeDLayer = true;`);
        lines.push(`pillTxt_${index}.transform.position.setValue([${posX}, ${posY + 5}, ${posZ - 5}]);`);
        lines.push(`styleText(pillTxt_${index}, 18, 0.88, 0.94, 0.92, ParagraphJustification.CENTER_JUSTIFY);`);
      } else if (node.type === 'metric_card') {
        const metricBento = buildBentoCardExtendScript({
          id: node.id,
          title: node.value,
          subtitle: node.label + (node.delta ? ' • ' + node.delta : ''),
          tag: 'METRIC',
          width: 480,
          height: 220,
          position3D: [posX, posY, posZ],
        });
        lines.push(metricBento);
      } else if (node.type === 'asset_card') {
        const assetBento = buildBentoCardExtendScript({
          id: node.id,
          title: node.title || 'Feature API',
          subtitle: node.subtitle,
          tag: 'FEATURE',
          width: 480,
          height: 220,
          position3D: [posX, posY, posZ],
        });
        lines.push(assetBento);
      } else if (node.type === 'bento_grid') {
        const colW = 340;
        const colH = 170;
        const totalW = node.cards.length * colW + (node.cards.length - 1) * 30;
        const startX = posX - totalW / 2 + colW / 2;

        lines.push(`// Node [${index}]: Bento Grid (${node.id})`);
        node.cards.forEach((card, cIdx) => {
          const cardX = startX + cIdx * (colW + 30);
          const gridBento = buildBentoCardExtendScript({
            id: `${node.id}_${card.id}`,
            title: card.title,
            subtitle: card.subtitle,
            tag: 'CORE',
            width: colW,
            height: colH,
            position3D: [cardX, posY, posZ],
          });
          lines.push(gridBento);
        });
      }
    });

    // 4. Final Brand Hero Stage Card
    lines.push(`// 4. Final Brand Hero Lockup`);
    const heroBrand = brand.name.toUpperCase();
    const heroBento = buildBentoCardExtendScript({
      id: 'brand_hero',
      title: heroBrand,
      subtitle: 'Engineered for Modern Engineering Teams',
      tag: 'OFFICIAL',
      width: 580,
      height: 140,
      position3D: [width / 2, height / 2 + 380, 280],
    });
    lines.push(heroBento);

    return lines.join('\n');
  }

  static writeJsxScript(config: ProjectBuildConfig, outputJsxPath: string): void {
    const code = this.generateJsxScript(config);
    if (typeof process !== 'undefined' && process.versions?.node) {
      const nodeFs = eval('require')('fs');
      nodeFs.writeFileSync(outputJsxPath, code, 'utf8');
    }
  }
}
