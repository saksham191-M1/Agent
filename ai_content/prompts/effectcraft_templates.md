# EffectCraft Templates

Contains 4 copy-paste JSONs for reference.

#### Template 1: `template_title_card.json` - Kinetic Title + Camera Push
```json
{
  "version": "1.0",
  "composition": {
    "width": 1920,
    "height": 1080,
    "fps": 24,
    "duration": 4.0,
    "backgroundColor": "#0A0A12"
  },
  "layers": [
    {
      "id": "bg_solid",
      "type": "solid",
      "name": "Background Mesh",
      "track": 1,
      "startTime": 0,
      "duration": 4.0,
      "properties": {
        "color": "#0A0A12",
        "gradient": {
          "type": "mesh",
          "colors": ["#0A0A12", "#1A1033"],
          "animated": true
        }
      },
      "keyframes": {}
    },
    {
      "id": "title_main",
      "type": "text",
      "name": "Main Title",
      "track": 2,
      "startTime": 0.3,
      "duration": 3.7,
      "properties": {
        "text": "{{title}}",
        "fontFamily": "Inter Bold",
        "fontSize": 110,
        "fill": "#FFFFFF",
        "align": "center",
        "position": [960, 540],
        "letterSpacing": -2
      },
      "keyframes": {
        "scale": [
          {"time": 0.3, "value": [85, 85], "easing": "easeOut"},
          {"time": 1.1, "value": [100, 100], "easing": "easeOut"}
        ],
        "opacity": [
          {"time": 0.3, "value": 0, "easing": "easeOut"},
          {"time": 0.8, "value": 1, "easing": "easeOut"}
        ],
        "blur": [
          {"time": 0.3, "value": 12, "easing": "easeOut"},
          {"time": 1.0, "value": 0, "easing": "easeOut"}
        ]
      }
    },
    {
      "id": "camera_main",
      "type": "camera",
      "name": "Camera Push-In",
      "track": 3,
      "startTime": 0,
      "duration": 4.0,
      "properties": {
        "fov": 50,
        "position": [960, 540, 1000],
        "target": [960, 540, 0]
      },
      "keyframes": {
        "position_z": [
          {"time": 0, "value": 1000, "easing": "easeInOut"},
          {"time": 4.0, "value": 750, "easeInOut": true}
        ],
        "rotation_y": [
          {"time": 0, "value": -1.5, "easing": "easeInOut"},
          {"time": 4.0, "value": 0, "easing": "easeInOut"}
        ]
      }
    },
    {
      "id": "adjust_vignette",
      "type": "adjustment",
      "name": "Vignette + Grade",
      "track": 4,
      "startTime": 0,
      "duration": 4.0,
      "properties": {
        "effects": [
          {"type": "vignette", "amount": 0.35},
          {"type": "lumetri", "preset": "teal_orange_cinematic"}
        ]
      },
      "keyframes": {}
    }
  ]
}
```

#### Template 2: `template_video_overlay.json` - Veo Footage + Lower Third
```json
{
  "version": "1.0",
  "composition": {
    "width": 1920,
    "height": 1080,
    "fps": 24,
    "duration": 5.0,
    "backgroundColor": "#000000"
  },
  "layers": [
    {
      "id": "veo_footage",
      "type": "footage",
      "name": "Veo Raw Clip",
      "track": 1,
      "startTime": 0,
      "duration": 5.0,
      "properties": {
        "source": "{{veo_clip_path}}",
        "scale": [100, 100],
        "position": [960, 540],
        "objectFit": "cover"
      },
      "keyframes": {
        "scale": [
          {"time": 0, "value": [105, 105], "easing": "linear"},
          {"time": 5.0, "value": [100, 100], "easing": "linear"}
        ]
      }
    },
    {
      "id": "lower_third",
      "type": "text",
      "name": "Lower Third Title",
      "track": 2,
      "startTime": 0.5,
      "duration": 4.0,
      "properties": {
        "text": "{{title}}",
        "subtitle": "{{subtitle}}",
        "fontFamily": "Inter SemiBold",
        "fontSize": 64,
        "fill": "#FFFFFF",
        "background": {"color": "#000000", "opacity": 0.45, "padding": 24, "radius": 12},
        "position": [120, 880],
        "align": "left"
      },
      "keyframes": {
        "position_x": [
          {"time": 0.5, "value": 80, "easing": "easeOut"},
          {"time": 1.2, "value": 120, "easing": "easeOut"}
        ],
        "opacity": [
          {"time": 0.5, "value": 0, "easing": "easeOut"},
          {"time": 0.9, "value": 1, "easing": "easeOut"}
        ]
      }
    },
    {
      "id": "camera_subtle",
      "type": "camera",
      "name": "Subtle Drift",
      "track": 3,
      "startTime": 0,
      "duration": 5.0,
      "properties": {
        "position": [960, 540, 900],
        "fov": 55
      },
      "keyframes": {
        "position_x": [
          {"time": 0, "value": 960, "easing": "linear"},
          {"time": 5.0, "value": 970, "easing": "linear"}
        ]
      }
    },
    {
      "id": "adjust_grade",
      "type": "adjustment",
      "name": "Color Grade",
      "track": 4,
      "startTime": 0,
      "duration": 5.0,
      "properties": {
        "effects": [
          {"type": "lumetri", "preset": "{{color_grade}}"},
          {"type": "sharpen", "amount": 0.15}
        ]
      },
      "keyframes": {}
    }
  ]
}
```

#### Template 3: `template_3d_text.json` - 3D Extruded Text + Lighting
```json
{
  "version": "1.0",
  "composition": {
    "width": 1920,
    "height": 1080,
    "fps": 24,
    "duration": 4.5,
    "backgroundColor": "#0E0E14"
  },
  "layers": [
    {
      "id": "bg_gradient",
      "type": "solid",
      "name": "Gradient Mesh BG",
      "track": 1,
      "startTime": 0,
      "duration": 4.5,
      "properties": {
        "gradient": {
          "type": "radial",
          "colors": ["#2A1A6B", "#0E0E14"],
          "position": [960, 540]
        }
      },
      "keyframes": {}
    },
    {
      "id": "text_3d",
      "type": "text",
      "name": "3D Title",
      "track": 2,
      "startTime": 0.2,
      "duration": 4.3,
      "properties": {
        "text": "{{title}}",
        "fontFamily": "Inter ExtraBold",
        "fontSize": 140,
        "fill": "#FFFFFF",
        "extrusion": 22,
        "bevel": true,
        "lighting": {"type": "spot", "intensity": 1.2, "position": [400, -300, 800]},
        "material": {"metalness": 0.3, "roughness": 0.4},
        "position": [960, 540],
        "align": "center"
      },
      "keyframes": {
        "rotation_y": [
          {"time": 0.2, "value": -15, "easing": "easeOut"},
          {"time": 2.0, "value": 0, "easing": "easeOut"}
        ],
        "scale": [
          {"time": 0.2, "value": [90, 90], "easing": "easeOut"},
          {"time": 1.0, "value": [100, 100], "easing": "easeOut"}
        ],
        "opacity": [
          {"time": 0.2, "value": 0, "easing": "easeOut"},
          {"time": 0.7, "value": 1, "easing": "easeOut"}
        ]
      }
    },
    {
      "id": "camera_orbit",
      "type": "camera",
      "name": "Orbit Camera",
      "track": 3,
      "startTime": 0,
      "duration": 4.5,
      "properties": {
        "fov": 45,
        "position": [960, 540, 1100],
        "target": [960, 540, 0]
      },
      "keyframes": {
        "position_z": [
          {"time": 0, "value": 1100, "easing": "easeInOut"},
          {"time": 4.5, "value": 850, "easing": "easeInOut"}
        ],
        "rotation_y": [
          {"time": 0, "value": -8, "easing": "easeInOut"},
          {"time": 4.5, "value": 6, "easing": "easeInOut"}
        ]
      }
    },
    {
      "id": "adjust_glow",
      "type": "adjustment",
      "name": "Glow + Vignette",
      "track": 4,
      "startTime": 0,
      "duration": 4.5,
      "properties": {
        "effects": [
          {"type": "glow", "radius": 40, "intensity": 0.6, "color": "{{primary_color}}"},
          {"type": "vignette", "amount": 0.4}
        ]
      },
      "keyframes": {}
    }
  ]
}
```

#### Template 4: `template_cta_sting.json` - Logo + CTA Punch + Particles
```json
{
  "version": "1.0",
  "composition": {
    "width": 1920,
    "height": 1080,
    "fps": 24,
    "duration": 3.5,
    "backgroundColor": "{{primary_color}}"
  },
  "layers": [
    {
      "id": "bg_brand",
      "type": "solid",
      "name": "Brand Solid",
      "track": 1,
      "startTime": 0,
      "duration": 3.5,
      "properties": {
        "color": "{{primary_color}}",
        "gradient": {"type": "linear", "colors": ["{{primary_color}}", "{{secondary_color}}"], "angle": 135}
      },
      "keyframes": {}
    },
    {
      "id": "cta_group",
      "type": "text",
      "name": "Logo + CTA",
      "track": 2,
      "startTime": 0.2,
      "duration": 3.3,
      "properties": {
        "logo": "{{logo_path}}",
        "logoSize": 160,
        "text": "{{title}}",
        "cta_text": "{{cta_text}}",
        "cta_style": {"background": "#FFFFFF", "color": "#000000", "padding": [28, 48], "radius": 999},
        "fontFamily": "Inter Bold",
        "fontSize": 72,
        "fill": "#FFFFFF",
        "position": [960, 540],
        "align": "center",
        "gap": 32
      },
      "keyframes": {
        "scale": [
          {"time": 0.2, "value": [92, 92], "easing": "easeOut"},
          {"time": 0.6, "value": [104, 104], "easing": "easeOut"},
          {"time": 0.85, "value": [100, 100], "easing": "easeInOut"}
        ],
        "opacity": [
          {"time": 0.2, "value": 0, "easing": "easeOut"},
          {"time": 0.5, "value": 1, "easing": "easeOut"}
        ]
      }
    },
    {
      "id": "camera_punch",
      "type": "camera",
      "name": "Punch Camera",
      "track": 3,
      "startTime": 0,
      "duration": 3.5,
      "properties": {
        "fov": 50,
        "position": [960, 540, 1000],
        "shake": 2
      },
      "keyframes": {
        "position_z": [
          {"time": 0.4, "value": 1000, "easing": "easeOut"},
          {"time": 0.6, "value": 980, "easing": "easeOut"},
          {"time": 0.85, "value": 1000, "easing": "easeInOut"}
        ]
      }
    },
    {
      "id": "particles",
      "type": "adjustment",
      "name": "Particle Burst",
      "track": 4,
      "startTime": 0.5,
      "duration": 1.5,
      "properties": {
        "effects": [
          {"type": "particles", "emitter": "center", "count": 80, "speed": 600, "life": 1.2, "color": "#FFFFFF"},
          {"type": "glow", "radius": 30, "intensity": 0.8}
        ]
      },
      "keyframes": {
        "opacity": [
          {"time": 0.5, "value": 1, "easing": "linear"},
          {"time": 2.0, "value": 0, "easing": "easeOut"}
        ]
      }
    }
  ]
}
```
