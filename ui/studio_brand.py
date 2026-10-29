"""Presentation for public discovery evidence and local campaign history."""
import html
import re
from urllib.parse import urlsplit


def esc(value):
    return html.escape(str(value), quote=True)


def source_link(value):
    try:
        parsed = urlsplit(str(value))
        if parsed.scheme == "https" and parsed.hostname and not parsed.username:
            return f'<a href="{esc(value)}" target="_blank" rel="noopener noreferrer">{esc(parsed.hostname)}</a>'
    except ValueError:
        pass
    return esc(value)


def brand_report(product=None):
    if not product:
        return '<div class="studio-status"><strong>Bring your product once.</strong>Import a public website or fill in the brief below, then save a reusable product profile.</div>'
    discovery = product.get("pending_discovery") or product.get("discovery") or {}
    state = "Saved product · ready for daily ads" if product.get("approved") else "Imported candidate · review once before saving"
    brief = product.get("brief", {})
    required = [k for k in ("name", "description", "audience", "benefits") if not brief.get(k)]
    details = [f'<strong>{esc(state)}</strong>', f'<p>{esc(product["name"])} · revision {product["revision"]} · <code>{esc(product["id"])}</code></p>']
    if required:
        details.append(f'<p>Still needed in the brief: <b>{esc(", ".join(required))}</b>. Unknown details are not invented.</p>')
    if product.get("refresh_notice"):
        details.append(f'<p>{esc(product["refresh_notice"])}</p>')
    assets = product.get("assets", {})
    captures = (discovery.get("captures") or {}).get("captures", [])
    if (discovery.get("captures") or {}).get("tour"):
        details.append('<p>Visual evidence: recorded walkthrough of the actual public product page, plus four source-backed images.</p>')
    elif assets.get("demo"):
        details.append('<p>Visual evidence: real uploaded product recording.</p>')
    elif captures:
        details.append(f'<p>Visual evidence: {len(captures)} actual public-page captures. Inspect the images in Brand &amp; assets before saving.</p>')
    elif assets.get("screenshot"):
        details.append('<p>Visual evidence: public marketing image. Upload a real screen recording to show clicks or tasks.</p>')
    else:
        details.append('<p><b>Product visuals are missing.</b> Recheck with page capture enabled or upload product images/a real recording. Text-only graphics cannot show the product in use.</p>')
    colors = discovery.get("brand", {}).get("colors", [])
    colors = [c for c in colors if isinstance(c, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", c)]
    if colors:
        details.append('<p>Detected colors: ' + ' '.join(f'<span style="display:inline-block;border:1px solid #888;border-radius:4px;padding:2px 6px"><i style="display:inline-block;width:10px;height:10px;background:{c}"></i> {esc(c)}</span>' for c in colors[:5]) + '</p>')
    fonts = discovery.get("brand", {}).get("fonts", [])
    if fonts:
        details.append('<p>Detected fonts (not downloaded/licensed automatically): ' + esc(', '.join(map(str, fonts[:4]))) + '</p>')
    evidence = discovery.get("evidence", [])
    if evidence:
        details.append('<details><summary>View source evidence and confidence</summary><div style="overflow:auto"><table style="width:100%;font-size:12px"><thead><tr><th>Field</th><th>Candidate</th><th>Source</th><th>Confidence</th></tr></thead><tbody>')
        for item in evidence[:20]:
            value = item.get("value", "")
            if isinstance(value, list):
                value = "; ".join(map(str, value))
            details.append(f'<tr><td>{esc(item.get("field", ""))}</td><td>{esc(str(value)[:240])}</td><td>{source_link(item.get("source", ""))}</td><td>{esc(item.get("confidence", "unknown"))}</td></tr>')
        details.append('</tbody></table></div></details>')
    warnings = discovery.get("warnings", [])
    if warnings:
        details.append('<ul>' + ''.join(f'<li>{esc(w)}</li>' for w in warnings) + '</ul>')
    details.append('<p>Public page claims are evidence, not independent verification. Private application screens are never inferred.</p>')
    return '<div class="studio-status">' + ''.join(details) + '</div>'


def campaign_report(projects):
    if not projects:
        return '<div class="studio-hint">No ads for this product yet. The first daily run starts its variation history.</div>'
    rows = []
    for p in reversed(projects[-7:]):
        campaign, creative = p.get("campaign", {}), p.get("creative", {})
        rows.append('<tr>' + ''.join(f'<td>{esc(value)}</td>' for value in (
            f"{campaign.get('date', '')} / take {campaign.get('take', 1)}", creative.get("label", ""),
            creative.get("lead_benefit", ""), creative.get("look", ""), p.get("status", ""))) + '</tr>')
    return '<div style="overflow:auto"><table class="campaign-table"><thead><tr><th>Date</th><th>Angle</th><th>Lead benefit</th><th>Look</th><th>Status</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'
