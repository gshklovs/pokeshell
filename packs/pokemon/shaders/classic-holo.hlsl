// ============================================================================
// Skin: CLASSIC HOLO
// Imitates: the Sword & Shield Rare Holo (Evolving Skies Salamence 109) - a
//   wide rainbow foil band sweeping across the art box with the classic holo
//   bands behind it, and a fine starlight speckle that glitters in the band,
//   inside the yellow card border. The pokeshell Rare Holo card animation.
//
// Tuning:
//   STRENGTH   how strongly the foil shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling
//   SWEEP_S    seconds for the wide rainbow band to cross the terminal once
//   SPECKLE    density of the starlight speckle (0..1)
// ============================================================================

#define STRENGTH  0.26
#define SPEED     1.0
#define BORDER_PX 12.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners
#define SWEEP_S   14.0
#define SPECKLE   0.35
#define TEXT_TINT 0.05

Texture2D shaderTexture;
SamplerState samplerState;
cbuffer PixelShaderSettings {
  float  Time;
  float  Scale;
  float2 Resolution;
  float4 Background;
};

// holo inset: the terminal image is drawn shrunk inward so the whole frame sits outside the text.
// Everything that reads the terminal goes through here; outside the inner area it's plain background.
#define INSET_PX (BORDER_PX + 4.0)
float4 TermSample(float2 uv)
{
  float2 inset = INSET_PX * Scale / Resolution;
  float2 q = (uv - inset) / (1.0 - 2.0 * inset);
  if (any(q < 0.0) || any(q > 1.0)) return Background;
  return shaderTexture.SampleLevel(samplerState, q, 0);
}


// ---- helpers ---------------------------------------------------------------

float hash21(float2 p)
{
  p = frac(p * float2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return frac(p.x * p.y);
}

float3 hue(float h)
{
  return saturate(abs(frac(h + float3(1.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0) - 1.0);
}

float cardEdge(float2 px, float radius)
{
  float2 h = Resolution * 0.5;
  float2 q = abs(px - h) - (h - radius);
  float sd = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;
  return -sd;
}

// ---- main ------------------------------------------------------------------

float4 main(float4 pos : SV_POSITION, float2 tex : TEXCOORD) : SV_TARGET
{
  float4 c = TermSample(tex);
  float2 px = tex * Resolution;
  float s = max(Scale, 0.5);
  float t = Time * SPEED;
  float2 p = px / s;
  float2 res = Resolution / s;

  float2 light = float2(0.5 + 0.35 * sin(t * 0.21), 0.5 + 0.25 * cos(t * 0.17));
  float textMask = smoothstep(0.05, 0.12, distance(c.rgb, Background.rgb));

  // --- classic holo bands: soft diagonal rainbow stripes that drift with the light
  float diag = (p.x + p.y) / (res.x + res.y);                 // 0..1 along the 45deg diagonal
  float bh = diag * 3.0 + (light.x - 0.5) * 0.8 + (light.y - 0.5) * 0.5;
  float3 bands = lerp(hue(bh), float3(1.0, 1.0, 1.0), 0.25);
  float stripe = 0.55 + 0.45 * sin(diag * 38.0 + t * 0.25);

  // --- the wide sweeping band (the card's tilt sweep): brightest in its core
  float ph = frac(t / SWEEP_S);
  float bu = (diag - (-0.2 + ph * 1.4)) / 0.2;               // -1..1 across the band
  float core = saturate(1.0 - abs(bu));
  core = core * core * (3.0 - 2.0 * core);
  float3 bandCol = lerp(hue(bu * 0.6 + tex.x * 0.3 - tex.y * 0.2 + 0.1), float3(1.0, 1.0, 1.0), 0.2);

  // --- starlight speckle: one tiny star per 5 px cell, a fraction lit, glittering in the band
  float2 cell = floor(p / 5.0);
  float2 f = frac(p / 5.0) - 0.5;
  float hs = hash21(cell);
  float2 off = float2(hash21(cell + 7.1), hash21(cell + 3.3)) - 0.5;
  float2 dd = f - off * 0.5;
  float star = exp(-dot(dd, dd) * 60.0) * step(hs, SPECKLE);
  float tw = 0.5 + 0.5 * sin(t * (0.6 + hs) + hs * 40.0);   // gentle twinkle, < 0.3 Hz
  float speck = star * (0.25 + 0.75 * tw) * (0.35 + 1.4 * core);
  // calm zone: no speckle right beside glyphs (two extra taps, left/right)
  float2 tx = float2(6.0 * s / Resolution.x, 0.0);
  float near = max(distance(TermSample(tex + tx).rgb, Background.rgb),
                   distance(TermSample(tex - tx).rgb, Background.rgb));
  speck *= 1.0 - 0.8 * smoothstep(0.05, 0.12, near);

  float3 foil = bands * (0.22 + 0.25 * stripe) + bandCol * core * 0.85;
  float amt = STRENGTH * (0.55 + 0.9 * core);
  float3 bg = lerp(c.rgb, foil, amt) + float3(1.0, 0.98, 0.92) * speck * STRENGTH * 1.3;

  float3 txt = lerp(c.rgb, bandCol, TEXT_TINT * core);
  float3 rgb = lerp(bg, txt, textMask);

  // --- yellow card border, lit by the same sweep ---------------------------
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float bevel = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 2.0 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 3.0 * s, edge - B)) * step(B, edge);

  float3 yellow = float3(0.93, 0.76, 0.16);
  float3 frameCol = yellow * (0.62 + 0.3 * sin(depth * 3.14159));
  frameCol = lerp(frameCol, float3(1.0, 0.95, 0.72), core * 0.5);
  frameCol += bandCol * core * 0.12;
  frameCol += bevel * 0.2 * float3(1.0, 1.0, 1.0);
  frameCol *= 1.0 - 0.45 * outerLine;

  rgb *= 1.0 - 0.35 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
