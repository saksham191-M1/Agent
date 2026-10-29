"""Local, video-first Gradio 6 frontend for the product-ad studio.

No chat or voice engines are imported here. Providers are used only through an
explicit StudioService action. CSS/THEME are public for local smoke servers;
Gradio 6 expects them on ``launch()``, not on ``Blocks()``.
"""
from __future__ import annotations

import html
import math
import os
from pathlib import Path

import gradio as gr

from ui.studio_brand import brand_report, campaign_report


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output" / "studio"
BRIEF_KEYS = (
    "name", "description", "audience", "problem", "benefits", "cta", "url", "color",
    "template", "aspect", "duration", "tone", "language",
)
DEFAULT_BRIEF = {
    "name": "", "description": "", "audience": "", "problem": "", "benefits": "",
    "cta": "Explore the product", "url": "", "color": "#a78bfa",
    "template": "spotlight", "aspect": "9:16", "duration": 20,
    "tone": "Confident", "language": "English",
}
SAMPLE_BRIEF = {
    "name": "Forma",
    "description": "A fictional planning app that brings personal tasks and project notes into one workspace.",
    "audience": "Independent designers and creative freelancers",
    "problem": "Tasks and notes are spread across separate tools.",
    "benefits": "Keep tasks and notes together\nOrganize work by project\nChoose a focused daily task list",
    "cta": "Find your focus", "url": "example.com", "color": "#a78bfa",
    "template": "spotlight", "aspect": "9:16", "duration": 20,
    "tone": "Confident", "language": "English",
}

# System fonts only: the interface works without a font CDN or remote images.
THEME = gr.themes.Base(
    primary_hue="cyan", secondary_hue="violet", neutral_hue="slate",
    font=("Inter", "Segoe UI", "Arial", "sans-serif"),
    font_mono=("Consolas", "ui-monospace", "monospace"),
    radius_size="lg", spacing_size="md",
)
_THEME_COLORS = {
    "body_background_fill": "#080b10", "body_text_color": "#f3f7fa",
    "body_text_color_subdued": "#93a1b1", "background_fill_primary": "#0e131a",
    "background_fill_secondary": "#151b24", "border_color_primary": "#25303b",
    "border_color_accent": "#69e5ff", "border_color_accent_subdued": "#294b58",
    "block_background_fill": "#0e131a", "block_border_color": "#25303b",
    "block_label_background_fill": "#0e131a", "block_label_text_color": "#c8d4dd",
    "block_title_text_color": "#f0f6f9", "block_info_text_color": "#93a1b1",
    "panel_background_fill": "#0e131a", "panel_border_color": "#25303b",
    "input_background_fill": "#090d12", "input_background_fill_focus": "#0c141b",
    "input_border_color": "#2a3945", "input_border_color_focus": "#69e5ff",
    "input_placeholder_color": "#647484", "input_shadow": "none",
    "button_primary_background_fill": "#69e5ff", "button_primary_background_fill_hover": "#9af0ff",
    "button_primary_border_color": "#69e5ff", "button_primary_text_color": "#071116",
    "button_secondary_background_fill": "#151d27", "button_secondary_background_fill_hover": "#202d39",
    "button_secondary_border_color": "#2d3d49", "button_secondary_text_color": "#e1edf2",
    "button_cancel_background_fill": "#24171d", "button_cancel_text_color": "#ffb6c2",
    "button_cancel_border_color": "#633541", "accordion_text_color": "#e1edf2",
    "checkbox_background_color": "#0b1117", "checkbox_border_color": "#53616d",
    "checkbox_background_color_selected": "#69e5ff", "checkbox_border_color_selected": "#69e5ff",
    "checkbox_label_background_fill": "#0e131a", "checkbox_label_text_color": "#c8d4dd",
    "checkbox_label_background_fill_selected": "#17333d", "checkbox_label_text_color_selected": "#e5fbff",
    "table_text_color": "#e1edf2", "table_border_color": "#2a3945",
    "table_even_background_fill": "#101820", "table_odd_background_fill": "#131d26",
    "table_row_focus": "#17333d", "loader_color": "#69e5ff",
    "link_text_color": "#8deeff", "error_background_fill": "#291a22",
    "error_border_color": "#633541", "error_text_color": "#ffc4ce",
}
THEME.set(
    **{key: value for name, value in _THEME_COLORS.items() for key in (name, name + "_dark")},
    block_border_width="1px", block_shadow="none", block_shadow_dark="none",
    block_radius="12px", input_radius="9px", button_large_radius="10px",
    button_large_text_weight="600", layout_gap="18px", body_text_size="14px",
)

CSS = """
:root { color-scheme: dark; }
body { background: #0b0c10 !important; }
.gradio-container { width: 100% !important; min-width: 0 !important;
    max-width: 1480px !important; margin: auto !important; box-sizing: border-box;
    padding: 0 38px 30px !important; background: #0b0c10 !important; color: #f1f0f7; }
.gradio-container .main { padding: 0 !important; width: 100%; min-width: 0 !important; }
.gradio-container .main > .wrap, .gradio-container .contain { width: 100%; min-width: 0 !important; }
.gradio-container * { scrollbar-color: #454055 #11121a; }
.gradio-container :is(button, input, textarea, select):focus-visible {
    outline: 2px solid #c3afff !important; outline-offset: 3px; }
.gradio-container button { transition: background 140ms ease, border-color 140ms ease; }
.gradio-container button:disabled { opacity: .42; }
.gradio-container textarea { line-height: 1.55 !important; }
.gradio-container .prose { color: #a2a2b6; }
.gradio-container footer { display: none !important; }
#studio-header { margin-bottom: 0; }
.studio-nav { display: flex; align-items: center; justify-content: space-between;
    gap: 20px; border-bottom: 1px solid #262732; padding: 26px 0 22px; }
.studio-brand { display: flex; align-items: center; gap: 13px; font-size: 14px;
    font-weight: 700; letter-spacing: .18em; }
.studio-brand .brand-mark { display: grid; place-items: center; width: 33px; height: 33px;
    background: #d5f792; color: #171c11; border-radius: 10px; letter-spacing: -.08em;
    font-size: 19px; font-weight: 800; transform: rotate(-5deg); }
.studio-brand .slash { color: #565360; font-weight: 400; }
.studio-brand .muted { color: #aaa6b9; font-weight: 500; }
.local-badge { display: flex; align-items: center; gap: 8px; color: #a5a7b6;
    font-size: 10px; letter-spacing: .13em; font-weight: 600; }
.local-badge .dot { width: 6px; height: 6px; background: #d5f792; border-radius: 50%; }
.studio-hero { display: flex; justify-content: space-between; align-items: flex-end;
    gap: 32px; padding: 34px 0 20px; }
.eyebrow { color: #afa0d5; font-size: 10px; letter-spacing: .19em; font-weight: 700; }
.studio-hero h1 { font-size: clamp(30px, 3.4vw, 46px); letter-spacing: -.045em;
    line-height: 1.1; font-weight: 650; margin: 12px 0 13px; color: #f4f1fc; }
.studio-hero h1 em { color: #b7a0f4; font-style: normal; }
.studio-hero p { color: #a2a2b6; max-width: 600px; line-height: 1.7;
    font-size: 13px; margin: 0; }
.workflow { display: flex; gap: 8px; align-items: center; white-space: nowrap;
    color: #a5a1b4; font-size: 11px; padding-bottom: 6px; }
.workflow b { display: inline-grid; place-items: center; height: 21px; width: 21px;
    border-radius: 50%; border: 1px solid #383242; color: #c7b8e9; font-size: 10px; margin-right: 4px; }
.workflow .arrow { color: #595462; margin: 0 3px; }
#studio-workspace { align-items: flex-start; gap: 24px; }
.studio-panel { background: #12131b !important; border: 1px solid #292a38 !important;
    border-radius: 18px !important; padding: 23px !important; gap: 17px !important; }
.section-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }
.section-head h2 { font-size: 19px; color: #f0edf8; font-weight: 600;
    letter-spacing: -.025em; margin: 6px 0 0; }
.section-head p { margin: 7px 0 0; font-size: 12px; line-height: 1.6; color: #9594aa; }
.section-number { display: inline-block; margin-right: 6px; color: #d5f792; }
.small-tag { border: 1px solid #393143; border-radius: 6px; padding: 5px 8px;
    color: #b9a6e2; font-size: 9px; letter-spacing: .12em; white-space: nowrap; }
#studio-example { min-height: 33px; font-size: 11px; border-style: dashed; }
#studio-brief .block { border: 0; }
#studio-brief .form { background: transparent; border: 0; }
#studio-brief .label-wrap { background: transparent; }
#studio-brief .accordion { background: #101119; border: 1px solid #292a38; }
.studio-hint { font-size: 11px !important; line-height: 1.6 !important; color: #8f8fa5 !important; }
#studio-preview-column { gap: 17px; }
#studio-preview { border: 1px solid #30303f; border-radius: 15px; background: #08090f; }
#studio-preview video { object-fit: contain !important; max-height: 470px; background: #08090f; }
.preview-empty { min-height: 365px; display: flex; flex-direction: column; align-items: center;
    justify-content: center; text-align: center; border: 1px solid #30303f;
    border-radius: 15px; overflow: hidden; position: relative; padding: 36px;
    background: radial-gradient(ellipse at 49% 35%, #272038 0%, #10111a 52%, #0b0c12 100%); }
.preview-empty::before { content: ''; position: absolute; inset: 0; opacity: .22;
    background-image: linear-gradient(#505064 1px, transparent 1px), linear-gradient(90deg, #505064 1px, transparent 1px);
    background-size: 38px 38px; mask-image: radial-gradient(ellipse, black, transparent 70%); pointer-events: none; }
.frame-art { width: 82px; height: 105px; border: 1px solid #9075c4; border-radius: 12px;
    box-shadow: -15px 8px 0 -1px #171322, -15px 8px 0 0 #4c3d67, 15px -8px 0 -1px #171322, 15px -8px 0 0 #4c3d67;
    display: grid; place-items: center; transform: rotate(-7deg); margin: 0 0 31px;
    background: linear-gradient(145deg, #302242, #14121d); position: relative; }
.frame-art svg { width: 29px; height: 29px; color: #d5f792; transform: rotate(7deg); }
.preview-empty h3 { position: relative; font-size: 18px; font-weight: 500; color: #ddd6ef;
    letter-spacing: -.025em; margin: 0 0 9px; }
.preview-empty p { position: relative; font-size: 12px; line-height: 1.65;
    color: #9790aa; max-width: 310px; margin: 0; }
.preview-empty .preview-note { margin-top: 28px; font: 9px Consolas, monospace;
    letter-spacing: .14em; color: #777185; text-transform: uppercase; }
.project-meta { display: flex; align-items: center; justify-content: space-between;
    gap: 12px; font-size: 11px; color: #9691a8; }
.project-meta strong { font-size: 12px; font-weight: 500; color: #dbd5e9; }
.project-meta code { font-size: 10px; color: #aaa0c1; }
.studio-status { border: 1px solid #343043; border-radius: 10px; padding: 13px 15px;
    background: #191622; font-size: 12px; line-height: 1.65; color: #bfb3d7; }
.studio-status strong { display: block; font-weight: 600; color: #e4dbf6; }
.studio-status.good { border-color: #374329; background: #181d15; color: #afbd9d; }
.studio-status.good strong { color: #d5f792; }
.studio-status.error { border-color: #673c49; background: #25171e; color: #f6afbf; }
.studio-status.error strong { color: #ffd4de; }
.studio-status.warn { border-color: #5b4934; background: #211c15; color: #d5bc96; }
.studio-status ul { margin: 6px 0 0; padding-left: 17px; }
#render-final { background: #d5f792 !important; border-color: #d5f792 !important; color: #1b2311 !important; }
#render-final:hover:not(:disabled) { background: #e1ffaf !important; }
#cancel-render { min-height: 32px; font-size: 11px; }
.scene-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 9px; }
.scene-card { min-width: 0; min-height: 90px; border: 1px solid #302b3f; border-radius: 10px;
    padding: 12px 10px; background: linear-gradient(155deg, #231c31, #15151f); }
.scene-card:nth-child(even) { background: linear-gradient(155deg, #1d2420, #15151f); border-color: #2d3830; }
.scene-card .scene-index { font: 9px Consolas, monospace; color: #a497be; letter-spacing: .06em; }
.scene-card .scene-title { font-size: 11px; color: #d4cce5; line-height: 1.45;
    margin-top: 10px; overflow-wrap: anywhere; display: -webkit-box; -webkit-line-clamp: 2;
    -webkit-box-orient: vertical; overflow: hidden; }
#studio-storyboard { margin-top: 6px; }
#studio-storyboard .label-wrap { font-weight: 600; }
#storyboard-table { border-radius: 12px; overflow: hidden; }
#storyboard-table table { font-size: 12px; min-width: 780px; }
#storyboard-table .table-wrap { overflow: auto; max-width: 100%; }
#storyboard-table th { color: #b7a3df; font-size: 11px; }
.duration-note { font: 11px Consolas, monospace; color: #b6bcab; padding: 9px 0; }
.duration-note.invalid { color: #efb790; }
#studio-library { margin-top: 5px; }
#studio-product-source { margin-bottom: 20px; }
.campaign-table { width:100%; min-width:640px; border-collapse:collapse; font-size:12px; }
.campaign-table :is(th,td) { padding:9px; text-align:left; border-bottom:1px solid #30303f; }
.campaign-table th { color:#b7a3df; }
#daily-controls { margin-top:10px; border:1px solid #454035; border-radius:10px; }
#studio-library .form { border: 0; }
#studio-exports { border-left: 1px solid #2a2b36; padding-left: 22px; }
.capabilities { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 20px;
    border-top: 1px solid #262732; padding-top: 19px; color: #8c899e; font-size: 10px; }
.capabilities span { display: flex; align-items: center; gap: 6px; }
.capabilities i { height: 5px; width: 5px; border-radius: 50%; background: #737080; }
.capabilities i.ready { background: #b8d788; }
.capabilities .cap-label { color: #b1abbe; }
.studio-footer { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px;
    padding-top: 3px; font-size: 10px; color: #6f6d80; }
@media (min-width: 1120px) { #studio-preview-column { position: sticky; top: 18px; } }
@media (max-width: 1000px) {
    .workflow { display: none; }
    .gradio-container { padding: 0 22px 24px !important; }
    .studio-panel { padding: 19px !important; }
}
@media (max-width: 680px) {
    .gradio-container { padding: 0 14px 20px !important; }
    .studio-nav { padding: 20px 0; }
    .studio-brand { font-size: 11px; gap: 9px; }
    .local-badge { font-size: 8px; letter-spacing: .06em; }
    .studio-hero { padding: 24px 0 12px; }
    .studio-hero p { font-size: 12px; }
    .studio-panel { padding: 16px !important; }
    .preview-empty { min-height: 285px; padding: 22px; }
    #studio-exports { border-left: 0; padding-left: 0; }
    .scene-strip { gap: 8px; grid-template-columns: repeat(2, 1fr); }
    .scene-card { padding: 10px 7px; }
    .project-meta { align-items: flex-start; flex-direction: column; gap: 5px; }
}
@media (prefers-reduced-motion: reduce) { .gradio-container * { transition: none !important; } }

/* Jarvis Studio visual layer: Watermelon workspace density + Cult/Skiper
   status surfaces + Motion-Primitives-inspired restrained state motion. */
:root {
    color-scheme: dark;
    --jarvis-canvas: #080b10;
    --jarvis-surface: #0e131a;
    --jarvis-elevated: #151d27;
    --jarvis-line: #25303b;
    --jarvis-line-strong: #334754;
    --jarvis-ink: #f3f7fa;
    --jarvis-muted: #93a1b1;
    --jarvis-cyan: #69e5ff;
    --jarvis-violet: #a992ff;
    --jarvis-green: #75e5a5;
    --jarvis-amber: #f4c76a;
    --jarvis-ease: cubic-bezier(.16, 1, .3, 1);
}
body { background: var(--jarvis-canvas) !important; }
.gradio-container {
    max-width: 1600px !important;
    padding: 0 30px 36px !important;
    background: var(--jarvis-canvas) !important;
    color: var(--jarvis-ink);
}
.gradio-container * { scrollbar-color: #344754 #0a0f14; }
.gradio-container :is(button, input, textarea, select):focus-visible {
    outline: 2px solid #9af0ff !important;
    outline-offset: 3px;
}
.gradio-container button {
    transition: transform 180ms var(--jarvis-ease), background 180ms ease,
        border-color 180ms ease, box-shadow 180ms ease !important;
}
.gradio-container button:hover:not(:disabled) { transform: translateY(-1px); }
.gradio-container .prose { color: var(--jarvis-muted); }

#studio-header { margin-bottom: 0; }
.studio-nav {
    position: sticky;
    top: 0;
    z-index: 20;
    padding: 17px 0 15px;
    border-bottom: 1px solid #1c2932;
    background: rgba(8, 11, 16, .88);
    backdrop-filter: blur(16px);
}
.studio-brand .brand-mark {
    background: var(--jarvis-cyan);
    color: #071116;
    border: 1px solid #b5f6ff;
    box-shadow: 0 0 28px rgba(105, 229, 255, .14);
}
.studio-brand .slash { color: #42515c; }
.studio-brand .muted { color: #a5b4bf; }
.studio-nav-actions { display: flex; align-items: center; gap: 10px; }
.studio-route,
.command-trigger {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 31px;
    padding: 0 10px;
    border: 1px solid #263640;
    border-radius: 8px;
    background: #0c1218;
    color: #a8b8c3;
    font-size: 10px;
    letter-spacing: .08em;
    text-transform: uppercase;
}
.studio-route .route-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--jarvis-violet);
    box-shadow: 0 0 10px rgba(169, 146, 255, .72);
}
.command-trigger { color: #7f929f; text-transform: none; letter-spacing: 0; }
.command-trigger kbd {
    padding: 2px 5px;
    border: 1px solid #344754;
    border-radius: 4px;
    color: #c8d5dd;
    font: 10px Consolas, ui-monospace, monospace;
}
.local-badge .dot {
    background: var(--jarvis-green);
    box-shadow: 0 0 10px rgba(117, 229, 165, .7);
}

.studio-hero {
    padding: 42px 0 24px;
    border-bottom: 1px solid #1c2932;
}
.eyebrow {
    color: #83b9c7;
    font: 650 10px/1.2 Consolas, ui-monospace, monospace;
    letter-spacing: .17em;
    text-transform: uppercase;
}
.studio-hero h1 {
    color: #f2f8fa;
    font-weight: 680;
    letter-spacing: -.055em;
    line-height: 1.04;
}
.studio-hero h1 em { color: var(--jarvis-cyan); }
.studio-hero p { color: #91a2ae; }
.hero-aside { display: flex; flex-direction: column; align-items: flex-end; gap: 13px; }
.hero-status { display: flex; align-items: center; gap: 8px; color: #b4c2ca; font-size: 11px; }
.hero-status .status-beacon {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--jarvis-cyan);
    box-shadow: 0 0 14px rgba(105, 229, 255, .8);
    animation: jarvis-beacon 2.8s ease-in-out infinite;
}
.workflow b { border-color: #38505d; color: #b8e8f1; }
.workflow span:first-child b { border-color: var(--jarvis-cyan); color: var(--jarvis-cyan); }
.workflow .arrow { color: #4a5c67; }

.studio-metrics {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    padding: 18px 0 21px;
}
.studio-metric {
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 7px;
    min-height: 65px;
    padding: 11px 13px;
    border: 1px solid #1e2b34;
    border-radius: 9px;
    background: #0b1117;
}
.studio-metric .metric-label {
    color: #718491;
    font: 9px Consolas, ui-monospace, monospace;
    letter-spacing: .12em;
    text-transform: uppercase;
}
.studio-metric .metric-value { color: #dcebf0; font-size: 13px; font-weight: 600; }
.studio-metric .metric-value.accent { color: var(--jarvis-cyan); }

.studio-panel {
    background: var(--jarvis-surface) !important;
    border: 1px solid var(--jarvis-line) !important;
    border-radius: 14px !important;
    box-shadow: 0 18px 45px rgba(0, 0, 0, .12);
}
.section-head h2 { color: #eaf4f7; font-weight: 620; letter-spacing: -.03em; }
.section-head p { color: #8da0ab; }
.section-number { color: var(--jarvis-cyan); }
.small-tag { border-color: #315362; color: #8deeff; font-family: Consolas, ui-monospace, monospace; }
#studio-brief .accordion { background: #0b1117; border-color: #263640; }
.studio-hint { color: #81939f !important; }
.studio-hint strong { color: #bdcbd2; }
#studio-product-source { position: relative; overflow: hidden; }
#studio-product-source::before {
    content: '';
    position: absolute;
    inset: 0 auto 0 0;
    width: 2px;
    background: var(--jarvis-cyan);
    opacity: .75;
}
#studio-preview-column { gap: 17px; }
#studio-preview { border-color: #30434f; border-radius: 12px; background: #070b0f; }
#studio-preview video { background: #070b0f; }
.preview-empty {
    border-color: #30434f;
    border-radius: 12px;
    background: #0a1117;
}
.preview-empty::before {
    background-image: linear-gradient(#37505d 1px, transparent 1px), linear-gradient(90deg, #37505d 1px, transparent 1px);
}
.preview-empty::after {
    content: '';
    position: absolute;
    width: 170px;
    height: 170px;
    border: 1px solid rgba(105, 229, 255, .15);
    border-radius: 50%;
    box-shadow: 0 0 70px rgba(105, 229, 255, .08);
    pointer-events: none;
}
.frame-art {
    z-index: 1;
    border-color: #4b8897;
    background: #101e27;
    box-shadow: -15px 8px 0 -1px #0c141b, -15px 8px 0 0 #294653,
        15px -8px 0 -1px #0c141b, 15px -8px 0 0 #294653;
}
.frame-art svg { color: var(--jarvis-cyan); }
.preview-empty h3, .preview-empty p, .preview-empty .preview-note { z-index: 1; }
.preview-empty h3 { color: #dcebf0; }
.preview-empty p { color: #8ea2ad; }
.preview-empty .preview-note { color: #6f838e; }
.project-meta { color: #8ba0ac; }
.project-meta strong { color: #dcebf0; }
.project-meta code { color: #82acb8; }
.studio-status { border-color: #2b414d; background: #0c151c; color: #a4b8c2; }
.studio-status strong { color: #dcebf0; }
.studio-status.good { border-color: #315442; background: #0d1a16; color: #a7cdb8; }
.studio-status.good strong { color: var(--jarvis-green); }
.studio-status.warn strong { color: var(--jarvis-amber); }
#render-final { background: var(--jarvis-cyan) !important; border-color: var(--jarvis-cyan) !important; color: #071116 !important; }
#render-final:hover:not(:disabled) { background: #a4f2ff !important; box-shadow: 0 8px 25px rgba(105, 229, 255, .16); }
.scene-card { border-color: #29404b; background: #101b23; transition: border-color 180ms ease, transform 180ms var(--jarvis-ease); }
.scene-card:hover { border-color: #528a99; transform: translateY(-2px); }
.scene-card:nth-child(even) { background: #121b25; border-color: #3e3b61; }
.scene-card .scene-index { color: #82acb8; }
.scene-card .scene-title { color: #d6e5ea; }
#storyboard-table th, .campaign-table th { color: #8deeff; }
.duration-note { color: #a9c7cf; }
.campaign-table :is(th, td) { border-color: #2a3945; }
#studio-exports { border-color: #263640; }
.capabilities { border-color: #1c2932; color: #778b97; }
.capabilities .cap-label { color: #a8bac3; }
.capabilities i.ready { background: var(--jarvis-green); box-shadow: 0 0 8px rgba(117, 229, 165, .5); }
.studio-footer { color: #617581; }
@keyframes jarvis-beacon {
    0%, 100% { opacity: .55; transform: scale(.88); }
    50% { opacity: 1; transform: scale(1.08); }
}
@media (min-width: 1120px) { #studio-preview-column { top: 78px; } }
@media (max-width: 1000px) { .hero-aside { align-items: flex-start; } }
@media (max-width: 680px) {
    .gradio-container { padding: 0 14px 20px !important; }
    .studio-nav { padding: 14px 0; }
    .studio-brand .brand-mark { width: 30px; height: 30px; font-size: 16px; }
    .studio-nav-actions { gap: 6px; }
    .studio-route, .command-trigger { padding: 0 7px; font-size: 8px; }
    .command-trigger { display: none; }
    .studio-hero { flex-direction: column; align-items: flex-start; padding: 27px 0 17px; }
    .studio-metrics { grid-template-columns: repeat(2, 1fr); gap: 8px; }
    .studio-metric { min-height: 58px; }
}
@media (prefers-reduced-motion: reduce) {
    .gradio-container *, .hero-status .status-beacon { transition: none !important; animation: none !important; }
}
"""
STUDIO_CSS = CSS
STUDIO_THEME = THEME


def _escape(value) -> str:
    return html.escape(str(value), quote=True)


def _notice(title: str, message: str, kind: str = "neutral", warnings=()) -> str:
    details = "".join(f"<li>{_escape(item)}</li>" for item in warnings)
    return (
        f'<div class="studio-status {kind}" role="status" aria-live="polite">'
        f"<strong>{_escape(title)}</strong>{_escape(message)}"
        + (f"<ul>{details}</ul>" if details else "") + "</div>"
    )


def _placeholder(title="Your first frame starts here.", message=None) -> str:
    message = message or "Add a product brief, shape your four scenes, then render a real video preview."
    return (
        '<div class="preview-empty"><div class="frame-art" aria-hidden="true">'
        '<svg viewBox="0 0 32 32" fill="none"><path d="M12 7L25 16L12 25V7Z" '
        'stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg></div>'
        f"<h3>{_escape(title)}</h3><p>{_escape(message)}</p>"
        '<div class="preview-note">Motion graphics · not generative footage</div></div>'
    )


def _scene_cards(rows=None) -> str:
    rows = rows or [[kind, "Your copy goes here", "", "", None] for kind in
                    ("Hook", "Benefit", "Product", "Call to action")]
    cards = []
    for index, row in enumerate(rows, 1):
        timing = f" · {_escape(row[4])}s" if row[4] is not None else ""
        cards.append(
            f'<div class="scene-card"><div class="scene-index">0{index}{timing}</div>'
            f'<div class="scene-title" title="{_escape(row[1])}">{_escape(row[1] or row[0])}</div></div>'
        )
    return '<div class="scene-strip">' + "".join(cards) + "</div>"


def _duration_note(rows, expected) -> str:
    if not expected:
        return '<div class="duration-note">Four scenes. One clear story. Create a storyboard to begin.</div>'
    try:
        durations = [float(row[4]) for row in rows]
        total = sum(durations)
        valid = len(rows) == 4 and all(math.isfinite(x) and 2 <= x <= 12 for x in durations)
        valid = valid and abs(total - float(expected)) <= 0.005
        timing = f"{total:g}s / {float(expected):g}s" if math.isfinite(total) else f"— / {expected}s"
    except (TypeError, ValueError, IndexError):
        valid, timing = False, f"— / {expected}s"
    label = "Timing matches the saved brief" if valid else "Each scene needs 2–12s; total must match the saved brief"
    return f'<div class="duration-note{"" if valid else " invalid"}">{_escape(timing)} · {label}</div>'


def _capability_html(caps: dict) -> str:
    missing = [name for key, name in (("ffmpeg", "FFmpeg"), ("ffprobe", "ffprobe"), ("browser", "browser")) if not caps.get(key)]
    statuses = [
        (not missing or bool(caps.get("remotion")), "Renderer", "available" if not missing or caps.get("remotion") else "missing " + ", ".join(missing)),
        (bool(caps.get("remotion")) or not missing, "Render backend", str(caps.get("renderer", "python"))),
        (caps.get("ai_ready"), "Gemini copy", "configured" if caps.get("ai_ready") else "not configured"),
        (caps.get("groq_ready"), "Groq brief fill", "configured" if caps.get("groq_ready") else "not configured"),
        (caps.get("voice_ready"), "ElevenLabs", "configured" if caps.get("voice_ready") else "not configured"),
    ]
    parts = [f'<span><i class="{"ready" if ready else ""}"></i><b class="cap-label">{label}</b> {_escape(value)}</span>'
             for ready, label, value in statuses]
    return '<div class="capabilities">' + "".join(parts) + "</div>"


def _existing_file(value):
    if not value:
        return None
    path = Path(value)
    return str(path) if path.is_file() else None


def build_ui(service=None) -> gr.Blocks:
    """Build an isolated studio session; constructing the UI makes no paid calls."""
    from studio.service import RenderCancelled, StudioError, StudioService, project_rows

    service = service if service is not None else StudioService()
    with gr.Blocks(title="JARVIS / STUDIO", analytics_enabled=False, fill_width=True) as app:
        project_id = gr.State(None)
        project_duration = gr.State(None)
        product_id = gr.State(None)
        gr.HTML(
            '<nav class="studio-nav" aria-label="Studio"><div class="studio-brand">'
            '<span class="brand-mark" aria-hidden="true">J</span> JARVIS '
            '<span class="slash">/</span><span class="muted">STUDIO</span></div>'
            '<div class="studio-nav-actions">'
            '<div class="studio-route"><span class="route-dot"></span> LOCAL BUILD</div>'
            '<div class="command-trigger" aria-label="Command palette hint">Search workspace <kbd>⌘ K</kbd></div>'
            '<div class="local-badge"><span class="dot"></span> LOCAL WORKSPACE</div>'
            '</div></nav>',
            elem_id="studio-header",
        )
        gr.HTML(
            '<header class="studio-hero"><div><div class="eyebrow">PRODUCT STORIES, BEAUTIFULLY IN MOTION</div>'
            '<h1>A little brief.<br>A <em>big first impression.</em></h1>'
            '<p>Create motion-graphics product ads from your copy and assets. '
            'Four editable scenes, a real video preview, and a final 1080p MP4.</p></div>'
            '<div class="hero-aside"><div class="hero-status"><span class="status-beacon"></span>'
            'Render lane ready · local-first</div><div class="workflow" aria-label="Workflow">'
            '<span><b>1</b> Brief</span><span class="arrow">→</span>'
            '<span><b>2</b> Storyboard</span><span class="arrow">→</span>'
            '<span><b>3</b> Render & export</span></div></div></header>'
        )
        gr.HTML(
            '<section class="studio-metrics" aria-label="Studio capabilities">'
            '<div class="studio-metric"><span class="metric-label">Canvas system</span>'
            '<span class="metric-value accent">9:16 · 16:9 · 1:1</span></div>'
            '<div class="studio-metric"><span class="metric-label">Story structure</span>'
            '<span class="metric-value">4 editable scenes</span></div>'
            '<div class="studio-metric"><span class="metric-label">Output quality</span>'
            '<span class="metric-value">Native 1080p export</span></div>'
            '<div class="studio-metric"><span class="metric-label">Workspace mode</span>'
            '<span class="metric-value">Local · reviewable</span></div>'
            '</section>'
        )
        with gr.Column(elem_id="studio-product-source", elem_classes="studio-panel"):
            gr.HTML('<div class="section-head"><div><div class="eyebrow">YOUR PRODUCT, REMEMBERED</div><h2>Start with a public website.</h2><p>Collect branding and source-backed details once. Reuse a reviewed profile for fresh daily ads.</p></div></div>')
            with gr.Row():
                source_website = gr.Textbox(label="Public product website", placeholder="https://yourproduct.com", scale=5)
                import_button = gr.Button("Import website", scale=1, min_width=140)
            refresh_sources = gr.Checkbox(label="Recheck the website instead of using its cached profile", value=False,
                                           info="Reviewed facts are never overwritten by a refresh. Public pages only; no login, cookies, or private app access.")
            capture_visuals = gr.Checkbox(label="Capture real public-page visuals for the video", value=True,
                                          info="Captures four views of the actual website. For a click/task demo, upload a real product recording below.")
            record_tour = gr.Checkbox(label="Record a moving product-page walkthrough", value=True,
                                      info="Adds a 24-second recording of the actual public page scrolling. Allow about 30 seconds for capture. Authenticated app tasks require your own recording.")
            with gr.Row():
                product_library = gr.Dropdown(label="Saved product profiles", choices=[], interactive=True, scale=5,
                                              info="Select a product here for daily generation. Opening restores its saved brief and assets.")
                open_product_button = gr.Button("Open product profile", scale=1, min_width=160)
            brand_summary = gr.HTML(brand_report())
        with gr.Row(elem_id="studio-workspace"):
            with gr.Column(scale=5, min_width=330, elem_id="studio-brief", elem_classes="studio-panel"):
                gr.HTML('<div class="section-head"><div><div class="eyebrow"><span class="section-number">01 /</span> THE BRIEF</div>'
                        '<h2>Start with your product.</h2><p>Your product facts. Your creative direction.</p></div></div>')
                ad_prompt = gr.Textbox(
                    label="Describe the ad in one request",
                    placeholder=("Create a 20-second vertical ad for SkillMe.\n"
                                 "Product: SkillMe\nDescription: ...\nAudience: ...\n"
                                 "Benefits: ...; ...\nCTA: Apply to SkillMe"),
                    lines=5,
                    max_length=4000,
                    info="Template mode extracts only the facts you provide. Missing facts stop before a project is created.",
                )
                prompt_button = gr.Button("Generate ad from prompt →", variant="primary", elem_id="prompt-generate")
                gr.Markdown("Use **Product**, **Description**, **Audience**, and **Benefits** labels for the most reliable no-AI intake. You can review the storyboard before downloading the MP4.", elem_classes="studio-hint")
                example_button = gr.Button("Try a fictional sample brief ↗", size="sm", elem_id="studio-example")
                name = gr.Textbox(label="Product / project name", placeholder="What are we introducing?", max_length=40)
                description = gr.Textbox(label="Product description *", placeholder="What does your product do? Keep it specific and factual.", lines=3, max_length=800)
                audience = gr.Textbox(label="Who is it for? *", placeholder="e.g. Independent designers", max_length=100)
                with gr.Row():
                    fill_brief_button = gr.Button("✦  Fill problem & benefits with Groq", size="sm", min_width=220,
                                                    elem_id="fill-brief-groq")
                replace_brief = gr.Checkbox(label="Replace existing problem & benefits", value=False,
                                            info="Off: fill empty fields only. Review AI suggestions before saving.")
                brief_fill_status = gr.HTML(
                    '<div class="studio-hint">Add a name, description, and audience first. Groq fills the two fields below '
                    'for your review; this action does not use Gemini credits or save a project.</div>',
                    elem_id="brief-fill-status",
                )
                problem = gr.Textbox(label="Customer problem", placeholder="What is frustrating or difficult for your customer?",
                                     max_length=180, info="Required for the Problem → solution direction. Use a real pain point.")
                benefits = gr.Textbox(label="Real product benefits *", placeholder="One benefit per line\nOnly include claims you can support", lines=3,
                                      info="1–6 benefits. Your facts stay the source of truth.")
                with gr.Accordion("Brand & assets", open=False):
                    with gr.Row():
                        cta = gr.Textbox(label="Call to action", value=DEFAULT_BRIEF["cta"], max_length=40)
                        color = gr.ColorPicker(label="Brand accent", value=DEFAULT_BRIEF["color"], min_width=110, scale=0)
                    url = gr.Textbox(label="Website (optional)", placeholder="yourproduct.com", max_length=120)
                    with gr.Row():
                        logo = gr.File(label="Logo (optional)", file_types=[".png", ".jpg", ".jpeg", ".webp"], type="filepath", height=110, min_width=130)
                        screenshot = gr.File(label="Product image (optional)", file_types=[".png", ".jpg", ".jpeg", ".webp"], type="filepath", height=110, min_width=130)
                    scene_images = gr.File(label="Four scene images (optional, in storyboard order)", file_count="multiple",
                                           file_types=[".png", ".jpg", ".jpeg", ".webp"], type="filepath", height=130)
                    demo = gr.File(label="Real product screen recording / demo (optional)",
                                   file_types=[".mp4", ".mov", ".webm"], type="filepath", height=110)
                    gr.Markdown("Import the actual website or upload product images. A real recording shows your cursor, clicks and task results; it plays at its original speed. 2–120s, under 80 MB. Recording audio is muted; select SFX/narration separately.", elem_classes="studio-hint")
                with gr.Accordion("Direction & format", open=True):
                    template = gr.Dropdown(choices=[("Product spotlight", "spotlight"), ("Problem → solution", "problem_solution")], value="spotlight", label="Story direction")
                    with gr.Row():
                        aspect = gr.Dropdown(choices=[("Vertical · 9:16", "9:16"), ("Widescreen · 16:9", "16:9"), ("Square · 1:1", "1:1")], value="9:16", label="Canvas", min_width=145)
                        duration = gr.Dropdown(choices=[("15 seconds", 15), ("20 seconds", 20), ("30 seconds", 30)], value=20, label="Length", min_width=120)
                    with gr.Row():
                        tone = gr.Dropdown(choices=["Confident", "Friendly", "Bold"], value="Confident", label="Tone", min_width=120)
                        language = gr.Dropdown(choices=["English", "Hindi", "Hinglish"], value="English", label="Language", min_width=120)
                copy_mode = gr.Dropdown(choices=[("Template copy (no AI)", "template"), ("Gemini copy (uses configured API)", "gemini")],
                                        value="template", label="Copy source", info="Template uses your words. Gemini runs a strategist pass, then a copywriter pass; it needs GEMINI_API_KEY and GEMINI_MODEL.")
                with gr.Row():
                    create_button = gr.Button("Create storyboard →", variant="primary")
                    save_profile_button = gr.Button("Save product profile")
                gr.Markdown("**Save product profile** confirms this brief for reuse. Review imported claims and asset rights once; unknown details are not invented.", elem_classes="studio-hint")
                gr.Markdown("Creating a storyboard makes a **new project**. Brief or asset changes do not modify an existing one. No provider is called by loading a sample.", elem_classes="studio-hint")
            with gr.Column(scale=7, min_width=340, elem_id="studio-preview-column", elem_classes="studio-panel"):
                gr.HTML('<div class="section-head"><div><div class="eyebrow">THE VIEWFINDER</div><h2>See your story take shape.</h2></div>'
                        '<span class="small-tag">VIDEO FIRST</span></div>')
                project_meta = gr.HTML('<div class="project-meta"><strong>No project selected</strong><span>Your preview appears after rendering</span></div>')
                placeholder = gr.HTML(_placeholder())
                preview = gr.Video(label="Rendered preview", interactive=False, autoplay=False, visible=False,
                                   height=430, buttons=["download"], elem_id="studio-preview")
                status = gr.HTML(_notice("Ready for your brief", "Start on the left. Template copy works without an AI provider."))
                with gr.Row():
                    draft_button = gr.Button("▷  Render draft", interactive=False, min_width=145)
                    final_button = gr.Button("Render final · 1080p ↗", variant="primary", interactive=False, elem_id="render-final", min_width=175)
                narration = gr.Checkbox(label="ElevenLabs narration (uses credits)", value=False,
                                        info="Off by default. When on, rendering sends the edited narration to ElevenLabs.")
                motion_sfx = gr.Checkbox(label="Motion sound design (SFX + optional music bed)", value=True,
                                         info="Works with narration off: local whooshes, cut/click accents and a finish cue. Add a licensed track to assets/music for a music bed. No voice-provider credits.")
                cancel_button = gr.Button("Cancel active render", variant="stop", size="sm", interactive=False, elem_id="cancel-render")
                gr.Markdown("**Draft** for reviewing motion. **Final** for your 1080p export. Both save your current scene edits first. Renders use the selected project's saved brief.", elem_classes="studio-hint")
                scene_strip = gr.HTML(_scene_cards())
                with gr.Accordion("Daily ads · generate a finished video", open=True, elem_id="daily-controls"):
                    campaign_goal = gr.Textbox(label="Today's creative focus (optional)", placeholder="e.g. Focus on the scheduling benefit", max_length=300)
                    with gr.Row():
                        campaign_date = gr.Textbox(label="Campaign date (optional)", placeholder="YYYY-MM-DD · blank means today UTC")
                        daily_quality = gr.Dropdown(label="Daily output", choices=[("Final · native 1080p", "final"), ("Draft preview", "draft")], value="final")
                    new_take = gr.Checkbox(label="Make another take for this date", value=False,
                                          info="Off: reuse/resume the day's ad. On: a new creative; configured AI/narration may incur charges.")
                    daily_button = gr.Button("Generate daily ad →", variant="primary")
                    gr.Markdown("Uses the **selected saved product**, the copy source on the left, and the narration setting above. Gemini creates a creative strategy before writing the script; then Jarvis validates, narrates, renders, and verifies the export. Save brief changes first. This button does not install a scheduler or publish ads.", elem_classes="studio-hint")
                    campaign_history = gr.HTML(campaign_report([]))
        with gr.Accordion("02 / STORYBOARD — make every scene yours", open=True, elem_id="studio-storyboard", elem_classes="studio-panel"):
            gr.Markdown("Edit headlines, supporting copy, narration and seconds. Scene types stay fixed. **Durations must add up to the saved project's length** (2–12 seconds per scene). Review every claim before rendering. On small screens, scroll the table sideways or use fullscreen.", elem_classes="studio-hint")
            storyboard = gr.Dataframe(
                value=[[kind, "", "", "", 5] for kind in ("Hook", "Benefit", "Product", "Call to action")],
                headers=["Scene", "Headline", "Supporting copy", "Narration", "Seconds"],
                datatype=["str", "str", "str", "str", "number"], type="array",
                # Gradio 6.28 still ignores row_limits; its frontend honors this legacy fixed count.
                row_count=(4, "fixed"), column_count=5,
                interactive=True, static_columns=[0], wrap=True, max_height=360,
                column_widths=["13%", "23%", "27%", "27%", "10%"], show_row_numbers=True,
                buttons=["fullscreen"], show_label=False, elem_id="storyboard-table",
            )
            with gr.Row():
                duration_note = gr.HTML(_duration_note(None, None), scale=5)
                save_button = gr.Button("Save scene edits", size="sm", interactive=False, scale=1, min_width=145)
        with gr.Column(elem_classes="studio-panel", elem_id="studio-library"):
            gr.HTML('<div class="section-head"><div><div class="eyebrow"><span class="section-number">03 /</span> YOUR WORKSPACE</div>'
                    '<h2>Keep the good takes.</h2><p>Reopen a saved project, or take the finished files with you.</p></div></div>')
            with gr.Row():
                with gr.Column(scale=6, min_width=270):
                    history = gr.Dropdown(choices=[], value=None, label="Saved projects · name / status", interactive=True,
                                          info="Saved locally. Opening a project replaces unsaved scene edits.")
                    with gr.Row():
                        refresh_button = gr.Button("↻  Refresh history", size="sm")
                        open_button = gr.Button("Open selected project", size="sm")
                with gr.Column(scale=5, min_width=250, elem_id="studio-exports"):
                    final_download = gr.File(label="Final MP4 · available after final render", interactive=False, type="filepath", height=90)
                    project_download = gr.File(label="Project JSON · brief & storyboard", interactive=False, type="filepath", height=90)
                    support_downloads = gr.File(label="Voiceover script, captions & audio", file_count="multiple",
                                                interactive=False, type="filepath", height=110)
                    gr.Markdown("Draft clips can be downloaded from the video player. Project JSON includes your brief and scene text—not credentials.", elem_classes="studio-hint")
        capabilities = gr.HTML('<div class="capabilities">Checking local capabilities when this workspace opens…</div>')
        gr.HTML('<div class="studio-footer"><span>JARVIS / STUDIO · Built around your product.</span>'
                '<span>Local workspace · Optional paid providers · No generative footage</span></div>')

        brief_inputs = [name, description, audience, problem, benefits, cta, url, color, template, aspect, duration, tone, language]
        controls = [create_button, example_button, prompt_button, save_button, draft_button, final_button, open_button, cancel_button,
                    import_button, open_product_button, save_profile_button, daily_button, fill_brief_button]
        project_outputs = [project_id, project_duration, storyboard, status, preview, placeholder, project_meta, support_downloads,
                           scene_strip, final_download, project_download, duration_note, history, campaign_history, *controls]
        product_outputs = [*project_outputs, product_id, product_library, brand_summary, *brief_inputs, logo, screenshot, scene_images, demo, source_website, brief_fill_status]

        def control_updates(current_id, busy=False, rendering=False):
            return {
                create_button: gr.update(interactive=not busy), example_button: gr.update(interactive=not busy),
                prompt_button: gr.update(interactive=not busy),
                save_button: gr.update(interactive=bool(current_id) and not busy),
                draft_button: gr.update(interactive=bool(current_id) and not busy),
                final_button: gr.update(interactive=bool(current_id) and not busy),
                open_button: gr.update(interactive=not busy),
                cancel_button: gr.update(interactive=bool(current_id) and rendering),
                import_button: gr.update(interactive=not busy), open_product_button: gr.update(interactive=not busy),
                save_profile_button: gr.update(interactive=not busy), daily_button: gr.update(interactive=not busy),
                fill_brief_button: gr.update(interactive=not busy),
            }

        def history_update(selected_id=None):
            projects = service.list_projects()
            choices = [(f"{p['name']} / {p['status']} · {p['id'][:8]}", p["id"]) for p in projects]
            return gr.update(choices=choices, value=selected_id if any(p["id"] == selected_id for p in projects) else None)

        def busy_view(message, current_id, rendering=False):
            return {
                **control_updates(current_id, busy=True, rendering=rendering),
                preview: gr.update(value=None, visible=False), final_download: None, project_download: None,
                support_downloads: None,
                placeholder: gr.update(value=_placeholder("Your story is in the making.", message), visible=True),
                status: _notice("Rendering" if rendering else "Working on your project", message),
            }

        def failed_view(exc, current_id):
            # StudioError is explicitly safe for display. Do not leak arbitrary SDK errors or credentials.
            message = str(exc) if isinstance(exc, (StudioError, gr.Error)) else (
                f"{type(exc).__name__}: the operation could not complete. No new video was published. "
                "Check the local backend configuration and try again."
            )
            return {
                **control_updates(current_id), status: _notice("Action could not complete", message, "error"),
                preview: gr.update(value=None, visible=False), final_download: None, project_download: None,
                support_downloads: None,
                placeholder: gr.update(value=_placeholder("No new preview was published.", "Resolve the message below, then try again. Your scene edits remain in the editor."), visible=True),
            }

        def project_view(project, note=None, quality=None, show_media=True):
            rows = project_rows(project)
            brief = project["brief"]
            state = project.get("status", "draft")
            selected_path = project.get(f"{quality}_path") if quality else project.get("final_path") or project.get("draft_path")
            media = _existing_file(selected_path) if show_media and state == "ready" else None
            final_path = _existing_file(project.get("final_path")) if show_media and state == "ready" else None
            exported = next((r for r in reversed(project.get("renders", [])) if r.get("video") == media
                             and r.get("revision") == project.get("revision")), {}) if media else {}
            supporting = [path for key in ("script", "captions", "audio") if (path := _existing_file(exported.get(key)))]
            if quality and state not in ("ready", "failed", "cancelled"):
                title, message, kind = "Render did not complete", "The backend did not return a finished video. Check the project status and try again.", "error"
            elif state == "failed":
                title, message, kind = "Render failed", project.get("error") or "The renderer did not finish. Try a draft after checking the local setup.", "error"
            elif state == "cancelled":
                title, message, kind = "Render cancelled", "No new video was published. Your storyboard is saved and ready to try again.", "warn"
            elif state == "rendering":
                title, message, kind = "Render in progress", "This project is still rendering. Refresh and reopen it when the render finishes.", "neutral"
            elif media:
                label = "Final 1080p" if (quality == "final" or not quality and project.get("final_path")) else "Draft"
                title, message, kind = f"{label} ready", note or "This is a rendered video, not a mock preview. Play it back before sharing.", "good"
            elif state == "ready" and show_media:
                title, message, kind = "Preview file unavailable", "The saved video is missing. Render again to create a new file.", "warn"
            else:
                title, message, kind = "Storyboard ready", note or "Review your four scenes below, then render a draft or final video.", "neutral"
            try:
                refreshed_history = history_update(project["id"])
            except Exception:
                # A successful render must not become a failure merely because history could not refresh.
                refreshed_history = gr.skip()
            creative = project.get("creative", {})
            campaign = project.get("campaign", {})
            creative_note = (f"{creative.get('label', '')} · {creative.get('look', '')} · {campaign.get('date', '')} / take {campaign.get('take', 1)}") if creative else ""
            assets = project.get("assets", {})
            visual_note = "Real product recording" if assets.get("demo") else "Product images / website captures" if any(
                key == "screenshot" or key.startswith("scene_") for key in assets) else "Text-only · add product visuals for a demo"
            audio_note = ("Voice + SFX" if exported.get("narrated") and exported.get("sfx") else
                          "Voice" if exported.get("narrated") else "SFX" if exported.get("sfx") else "Silent") if media else ""
            return {
                **control_updates(project["id"], rendering=state == "rendering"),
                project_id: project["id"], project_duration: brief["duration"], storyboard: rows,
                preview: gr.update(value=media, visible=bool(media)),
                placeholder: gr.update(value=_placeholder("Your scenes are ready for motion." if state not in ("failed", "cancelled") else "Let's try another take.",
                                                         "Render your saved storyboard to see a real video here."), visible=not bool(media)),
                status: _notice(title, message, kind, project.get("warnings") or []),
                project_meta: '<div class="project-meta"><strong>' + _escape(project["name"]) + '</strong><span>'
                              + _escape(f"{brief['aspect']} · {brief['duration']}s · revision {project.get('revision', 1)}")
                              + f' · <code>{_escape(project["id"][:8])}</code></span><span>{_escape(visual_note)} · {_escape(audio_note)}</span><span>{_escape(creative_note)}</span></div>',
                scene_strip: _scene_cards(rows), final_download: final_path,
                project_download: _existing_file(project.get("project_path")),
                support_downloads: supporting or None,
                duration_note: _duration_note(rows, brief["duration"]), history: refreshed_history,
            }

        def products_update(selected=None):
            products = service.list_products()
            choices = [(f"{p['name']} / {'ready' if p.get('approved') else 'review needed'} · {p['id'][:8]}", p["id"]) for p in products]
            return gr.update(choices=choices, value=selected if any(p["id"] == selected for p in products) else None)

        def product_view(product):
            brief = {**DEFAULT_BRIEF, **product["brief"]}
            if isinstance(brief["benefits"], list):
                brief["benefits"] = "\n".join(brief["benefits"])
            candidate_assets = (product.get("pending_discovery") or {}).get("assets", {})
            staged_assets = {**product.get("assets", {}), **{k: v for k, v in candidate_assets.items() if k.startswith("scene_") or k == "demo"}}
            result = {
                **control_updates(None), product_id: product["id"], product_library: products_update(product["id"]),
                brand_summary: brand_report(product), campaign_history: campaign_report(service.list_product_ads(product["id"])),
                source_website: product.get("source_url", ""), project_id: None, project_duration: None,
                preview: gr.update(value=None, visible=False), final_download: None, project_download: None,
                support_downloads: None,
                placeholder: gr.update(value=_placeholder("Your product is ready for a new story.", "Use Generate daily ad for an automatic script-to-video run, or create a storyboard to edit manually."), visible=True),
                project_meta: '<div class="project-meta"><strong>' + _escape(product["name"]) + '</strong><span>Saved product profile</span></div>',
                scene_strip: _scene_cards(), duration_note: _duration_note(None, None),
                storyboard: [[kind, "", "", "", 5] for kind in ("Hook", "Benefit", "Product", "Call to action")],
                status: _notice("Product profile ready" if product.get("approved") else "Website imported — review the brief",
                                "Daily ads reuse these saved facts and assets." if product.get("approved") else "Complete any missing product details below and Save product profile once before daily generation."),
                logo: _existing_file(product.get("assets", {}).get("logo")),
                screenshot: _existing_file(product.get("assets", {}).get("screenshot")),
                scene_images: ([staged_assets[f"scene_{i}"] for i in range(1, 5)]
                               if all(_existing_file(staged_assets.get(f"scene_{i}")) for i in range(1, 5)) else None),
                demo: _existing_file(staged_assets.get("demo")),
                brief_fill_status: _notice("Brief assistance", "Fill empty fields with Groq, then review the suggestions before saving."),
            }
            result.update({component: brief[key] for key, component in zip(BRIEF_KEYS, brief_inputs)})
            return result

        def import_website(address, refresh, capture, tour, current_id, progress=gr.Progress()):
            yield busy_view("Reading a bounded set of public pages and assets. No private dashboard or login access.", current_id)
            try:
                product = service.import_product(address, refresh=bool(refresh), capture_visuals=bool(capture),
                                                 record_tour=bool(tour),
                                                 progress=lambda fraction, message: progress(fraction, desc=message))
                yield product_view(product)
            except Exception as exc:
                yield failed_view(exc, current_id)

        def open_product(selected, current_id):
            try:
                if not selected:
                    raise StudioError("Choose a saved product profile first.")
                return product_view(service.load_product(selected))
            except Exception as exc:
                return failed_view(exc, current_id)

        def save_profile(current_product, *values):
            # Ordered input contract: brief fields, logo, screenshot, scene images, demo, project ID.
            current_id = values[-1]
            yield busy_view("Saving your reviewed product facts and reusable brand assets.", current_id)
            try:
                brief = dict(zip(BRIEF_KEYS, values[:len(BRIEF_KEYS)]))
                product = service.save_product(current_product, brief, logo_path=values[-5], screenshot_path=values[-4],
                                               scene_image_paths=values[-3], demo_path=values[-2])
                yield product_view(product)
            except Exception as exc:
                yield failed_view(exc, current_id)

        def generate_daily(selected_product, goal, day, mode, use_narration, use_sfx, another_take, quality, current_id,
                           progress=gr.Progress()):
            yield busy_view("Preparing a dated, non-repeating ad from your saved product profile.", current_id)
            try:
                if not selected_product:
                    raise StudioError("Import or fill in a product brief, then Save product profile once before daily generation.")
                if mode == "gemini" and not service.capabilities().get("ai_ready"):
                    raise StudioError("Configure Gemini or select Template copy (no AI) before generating a daily ad.")
                if use_narration and not service.capabilities().get("voice_ready"):
                    raise StudioError("Configure ElevenLabs or turn narration off. Local cloned narration is not integrated yet.")
                product = service.load_product(selected_product)
                current_id = None
                yield product_view(product)
                yield busy_view("Choosing a fresh angle, lead benefit, and visual direction.", None)
                callback = lambda fraction, message: progress(fraction, desc=message)
                project = service.create_daily_project(selected_product, campaign_date=day, goal=goal,
                                                       copy_mode=mode, new_take=bool(another_take), progress=callback)
                current_id = project["id"]
                # Publish the actual project ID before rendering so Cancel reaches the real job.
                yield project_view(project, show_media=False)
                yield busy_view("Rendering the daily ad; an existing compatible export will be reused.", current_id, rendering=True)
                project = service.complete_daily_ad(current_id, quality=quality, narration=bool(use_narration),
                                                    include_sfx=bool(use_sfx), progress=callback)
                result = project_view(project, quality=quality)
                result[campaign_history] = campaign_report(service.list_product_ads(selected_product))
                yield result
            except RenderCancelled:
                result = project_view(service.load_project(current_id))
                result[campaign_history] = campaign_report(service.list_product_ads(selected_product))
                yield result
            except Exception as exc:
                yield failed_view(exc, current_id)

        def create_storyboard(product_name, product_description, target_audience, customer_problem, product_benefits, action, website,
                              brand_color, story_template, canvas, length, copy_tone, copy_language, mode,
                              logo_path, screenshot_path, scene_paths, demo_path, current_id, progress=gr.Progress()):
            yield busy_view("Building four editable scenes from your supplied facts.", current_id)
            try:
                if mode == "gemini" and not service.capabilities().get("ai_ready"):
                    raise StudioError("Gemini is not configured. Choose 'Template copy (no AI)' or configure the backend before using Gemini.")
                brief = dict(zip(BRIEF_KEYS, [product_name, product_description, target_audience, customer_problem, product_benefits, action,
                                             website, brand_color, story_template, canvas, length, copy_tone, copy_language]))
                project = service.create_project(brief, copy_mode=mode, logo_path=logo_path, screenshot_path=screenshot_path,
                                                  scene_image_paths=scene_paths, demo_path=demo_path,
                                                 progress=lambda fraction, message: progress(fraction, desc=message))
                yield project_view(project, show_media=False)
            except Exception as exc:
                yield failed_view(exc, current_id)

        def generate_from_prompt(prompt_text, mode, logo_path, screenshot_path, scene_paths, demo_path,
                                 quality, use_narration, use_sfx, current_id, progress=gr.Progress()):
            yield busy_view("Reading the product facts in your ad request; no project is saved until the brief is complete.", current_id)
            try:
                if mode == "gemini" and not service.capabilities().get("ai_ready"):
                    raise StudioError("Gemini is not configured. Choose Template copy (no AI) or configure the backend before using this prompt.")
                if use_narration and not service.capabilities().get("voice_ready"):
                    raise StudioError("ElevenLabs is not configured. Turn narration off to render with local SFX.")
                callback = lambda fraction, message: progress(fraction, desc=message)
                project = service.create_prompt_project(
                    prompt_text,
                    copy_mode=mode,
                    logo_path=logo_path,
                    screenshot_path=screenshot_path,
                    scene_image_paths=scene_paths,
                    demo_path=demo_path,
                    progress=callback,
                )
                current_id = project["id"]
                # Publish the generated project's ID before rendering so the
                # existing Cancel action can reach the active render.
                yield project_view(project, show_media=False)
                yield busy_view("Rendering your prompt-based ad; the storyboard remains editable in project history.", current_id, rendering=True)
                project = service.render_project(
                    current_id,
                    quality=quality,
                    narration=bool(use_narration),
                    include_sfx=bool(use_sfx),
                    progress=callback,
                )
                yield project_view(project, quality=quality)
            except RenderCancelled:
                yield project_view(service.load_project(current_id))
            except Exception as exc:
                yield failed_view(exc, current_id)

        def save_storyboard(current_id, rows):
            yield busy_view("Saving your scene edits. Render again to preview this revision.", current_id)
            try:
                if not current_id:
                    raise StudioError("Create or open a project before saving scene edits.")
                project = service.update_storyboard(current_id, rows)
                yield project_view(project, note="Scene edits saved. Render a fresh preview for this revision.", show_media=False)
            except Exception as exc:
                yield failed_view(exc, current_id)

        def render(current_id, rows, use_narration, use_sfx, quality, progress):
            yield busy_view("Saving your current scene edits, then rendering a " + ("1080p final." if quality == "final" else "draft preview."), current_id, rendering=True)
            try:
                if not current_id:
                    raise StudioError("Create or open a project before rendering.")
                if use_narration and not service.capabilities().get("voice_ready"):
                    raise StudioError("ElevenLabs is not configured. Turn narration off to use local SFX, or configure the backend first.")
                # Always persist the editor contents immediately before a render.
                service.update_storyboard(current_id, rows)
                project = service.render_project(current_id, quality=quality, narration=bool(use_narration),
                                                 include_sfx=bool(use_sfx),
                                                 progress=lambda fraction, message: progress(fraction, desc=message))
                yield project_view(project, quality=quality)
            except RenderCancelled:
                yield project_view(service.load_project(current_id))
            except Exception as exc:
                yield failed_view(exc, current_id)

        def render_draft(current_id, rows, use_narration, use_sfx, progress=gr.Progress()):
            yield from render(current_id, rows, use_narration, use_sfx, "draft", progress)

        def render_final(current_id, rows, use_narration, use_sfx, progress=gr.Progress()):
            yield from render(current_id, rows, use_narration, use_sfx, "final", progress)

        def cancel_render(current_id):
            if not current_id:
                return _notice("Nothing to cancel", "Create or open a project first.")
            try:
                if service.cancel(current_id):
                    return _notice("Cancellation requested", "The backend is stopping the active render. Wait for it to finish before starting another take.", "warn")
                return _notice("No active render to cancel", "The project is not currently rendering. A queued action may not have started yet.")
            except Exception as exc:
                return failed_view(exc, current_id)[status]

        def open_project(selected_id, current_id):
            yield busy_view("Loading the saved brief, storyboard and available exports.", current_id)
            try:
                if not selected_id:
                    raise StudioError("Choose a saved project from history first.")
                project = service.load_project(selected_id)
                result = project_view(project)
                restored_brief = {**DEFAULT_BRIEF, **project["brief"]}
                if isinstance(restored_brief["benefits"], list):
                    restored_brief["benefits"] = "\n".join(restored_brief["benefits"])
                result.update({component: restored_brief[key] for key, component in zip(BRIEF_KEYS, brief_inputs)})
                # Restore saved product evidence without opting into paid providers.
                result.update({logo: _existing_file(project.get("assets", {}).get("logo")),
                               screenshot: _existing_file(project.get("assets", {}).get("screenshot")),
                               scene_images: ([project["assets"][f"scene_{i}"] for i in range(1, 5)]
                                              if all(_existing_file(project.get("assets", {}).get(f"scene_{i}")) for i in range(1, 5)) else None),
                               demo: _existing_file(project.get("assets", {}).get("demo")), copy_mode: "template",
                                narration: False, motion_sfx: True})
                yield result
            except Exception as exc:
                yield failed_view(exc, current_id)

        def refresh_history(current_id, current_product=None):
            try:
                return {history: history_update(current_id), capabilities: _capability_html(service.capabilities()),
                        status: gr.skip(), product_library: products_update(current_product)}
            except Exception as exc:
                return {status: failed_view(exc, current_id)[status]}

        def editor_changed(rows, expected, current_id):
            result = {duration_note: _duration_note(rows, expected)}
            if current_id:
                result.update({status: _notice("Unsaved scene edits", "Save your changes or render a new take. Rendering saves the current storyboard first.", "warn"),
                               preview: gr.update(value=None, visible=False), final_download: None, project_download: None,
                               support_downloads: None,
                               placeholder: gr.update(value=_placeholder("Your storyboard has changes.", "Render again to preview the edited scenes. Previous exports remain in local project history."), visible=True)})
            return result

        fill_fields = [name, description, audience, language, problem, benefits, replace_brief]

        def fill_brief(product_name, product_description, target_audience, copy_language,
                       current_problem, current_benefits, replace, current_id):
            fill_problem = bool(replace) or not (current_problem or "").strip()
            fill_benefits = bool(replace) or not (current_benefits or "").strip()
            if not fill_problem and not fill_benefits:
                yield {brief_fill_status: _notice("Your fields are already filled", "Enable Replace existing problem & benefits if you want a new suggestion. No API request was made.")}
                return
            yield {**control_updates(current_id, busy=True),
                   **{field: gr.update(interactive=False) for field in fill_fields},
                   brief_fill_status: _notice("Drafting with Groq", "Preparing problem and benefit suggestions for your review…")}
            result = {**control_updates(current_id), **{field: gr.update(interactive=True) for field in fill_fields}}
            try:
                suggestion = service.suggest_brief_fields(product_name, product_description, target_audience, copy_language,
                                                         current_problem or "", current_benefits or "")
                if fill_problem:
                    result[problem] = gr.update(value=suggestion["problem"], interactive=True)
                if fill_benefits:
                    result[benefits] = gr.update(value=suggestion["benefits"], interactive=True)
                result[brief_fill_status] = _notice("Suggestions ready — review the facts", "Edit anything inaccurate before saving. Groq was used; no Gemini call or project save was made.", "good")
            except Exception as exc:
                message = str(exc) if isinstance(exc, StudioError) else "Brief assistance could not complete. Check Groq configuration and retry."
                result[brief_fill_status] = _notice("Groq fill could not complete", message + " Your existing text is preserved.", "error")
            yield result

        event_options = dict(api_visibility="private", concurrency_id="studio-render", concurrency_limit=1, show_progress="minimal")
        fill_brief_button.click(fill_brief, [*fill_fields, project_id], [*fill_fields, brief_fill_status, *controls],
                                show_progress_on=brief_fill_status, trigger_mode="once", **event_options)
        prompt_button.click(generate_from_prompt,
                            [ad_prompt, copy_mode, logo, screenshot, scene_images, demo, daily_quality, narration, motion_sfx, project_id],
                            project_outputs, show_progress_on=status, **event_options)
        create_button.click(create_storyboard, [*brief_inputs, copy_mode, logo, screenshot, scene_images, demo, project_id], project_outputs,
                            show_progress_on=status, **event_options)
        save_button.click(save_storyboard, [project_id, storyboard], project_outputs, **event_options)
        draft_button.click(render_draft, [project_id, storyboard, narration, motion_sfx], project_outputs, show_progress_on=preview, **event_options)
        final_button.click(render_final, [project_id, storyboard, narration, motion_sfx], project_outputs, show_progress_on=preview, **event_options)
        # Do not merely cancel a Gradio event: the renderer must receive the cancellation signal.
        cancel_button.click(cancel_render, [project_id], [status], queue=False, api_visibility="private", show_progress="hidden")
        open_button.click(open_project, [history, project_id], [*project_outputs, *brief_inputs, logo, screenshot, scene_images, demo, copy_mode, narration, motion_sfx], **event_options)
        example_button.click(lambda: [SAMPLE_BRIEF[key] for key in BRIEF_KEYS] + [None, None, None, None, "template", False, True, None,
                             gr.update(value=None), brand_report(), campaign_report([]), ""],
                              outputs=[*brief_inputs, logo, screenshot, scene_images, demo, copy_mode, narration, motion_sfx, product_id, product_library,
                                      brand_summary, campaign_history, source_website], **event_options)
        import_button.click(import_website, [source_website, refresh_sources, capture_visuals, record_tour, project_id], product_outputs, **event_options)
        open_product_button.click(open_product, [product_library, project_id], product_outputs, **event_options)
        save_profile_button.click(save_profile, [product_id, *brief_inputs, logo, screenshot, scene_images, demo, project_id], product_outputs, **event_options)
        daily_button.click(generate_daily, [product_library, campaign_goal, campaign_date, copy_mode, narration, motion_sfx, new_take,
                                           daily_quality, project_id], product_outputs, **event_options)
        refresh_button.click(refresh_history, [project_id, product_id], [history, capabilities, status, product_library], queue=False,
                             api_visibility="private", show_progress="hidden")
        app.load(refresh_history, [project_id, product_id], [history, capabilities, status, product_library], queue=False,
                 api_visibility="private", show_progress="hidden")
        storyboard.input(editor_changed, [storyboard, project_duration, project_id],
                         [duration_note, status, preview, placeholder, final_download, project_download, support_downloads],
                         queue=False, api_visibility="private", show_progress="hidden")
    return app.queue(default_concurrency_limit=1, api_open=False, max_size=16)


def launch_ui() -> None:
    """Launch locally; configuration loading belongs to StudioService, not the UI."""
    app = build_ui()
    password = os.environ.get("STUDIO_PASSWORD")
    app.launch(
        server_name="127.0.0.1", share=False, inbrowser=True,
        auth=("jarvis", password) if password else None,
        allowed_paths=[str(OUTPUT_DIR)], theme=THEME, css=CSS,
        footer_links=[], enable_monitoring=False, show_error=False, max_file_size="80mb",
    )


if __name__ == "__main__":
    launch_ui()
