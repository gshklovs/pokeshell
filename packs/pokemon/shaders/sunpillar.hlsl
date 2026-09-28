// ============================================================================
// Skin: SUNPILLAR
// Imitates: Sword & Shield V / VMAX / VSTAR full-art cards - tall rainbow
//   "sun pillar" bands that slide as the card tilts, crossed by fine diagonal
//   etched lines (poke-holo's "sunpillar" effect: a repeating 6-colour pastel
//   gradient + a 133deg scanline gradient, blended with colour-dodge).
//
// Tuning:
//   STRENGTH   how strongly the foil shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling
//   LINE_PX    spacing of the diagonal etched lines in pixels
// ============================================================================

#define STRENGTH  0.24
#define SPEED     1.0
#define BORDER_PX 12.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners (rounded was ~BORDER_PX * 1.2)
#define LINE_PX   5.0
#define TEXT_TINT 0.06

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

float vnoise(float2 p)
{
  float2 i = floor(p);
  float2 f = frac(p);
  float2 u = f * f * (3.0 - 2.0 * f);
  float a = hash21(i);
  float b = hash21(i + float2(1.0, 0.0));
  float c = hash21(i + float2(0.0, 1.0));
  float d = hash21(i + float2(1.0, 1.0));
  return lerp(lerp(a, b, u.x), lerp(c, d, u.x), u.y);
}

float3 hue(float h)
{
  return saturate(abs(frac(h + float3(1.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0) - 1.0);
}

// poke-holo sunpillar palette: light pastel rainbow (hsl ~73% lightness)
float3 sunpillar(float h)
{
  return lerp(hue(h), float3(1.0, 1.0, 1.0), 0.4);
}

float glare(float2 uv, float2 light, float aspect, float k)
{
  float2 d = (uv - light) * float2(aspect, 1.0);
  return exp(-dot(d, d) * k);
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
  float aspect = Resolution.x / max(Resolution.y, 1.0);
  float2 uvA = tex * float2(aspect, 1.0);

  float2 light = float2(0.5 + 0.35 * sin(t * 0.21), 0.5 + 0.25 * cos(t * 0.17));
  float g = glare(tex, light, aspect, 2.2);

  float textMask = smoothstep(0.05, 0.12, distance(c.rgb, Background.rgb));

  // --- rainbow bands: the gradient runs vertically (CSS 0deg) and repeats a
  //     few times; tilting (light.y) slides the colours up/down, plus a slow
  //     drift of one cycle per ~18 s
  float h = tex.y * 2.2 + uvA.x * 0.12
          + (light.y - 0.5) * 1.6 + (light.x - 0.5) * 0.4
          + t / 18.0;
  float3 bands = sunpillar(h);

  // --- the "pillars": tall soft vertical columns of light that shift sideways
  //     with the tilt, so the rainbow reads as standing shafts
  float pillarPhase = uvA.x * 4.5 - (light.x - 0.5) * 5.0;
  float pillar = 0.55 + 0.45 * sin(pillarPhase + 0.6 * vnoise(float2(uvA.x * 3.0, t * 0.03)));

  // --- fine diagonal etched lines at 133deg (poke-holo scanlines)
  float2 ldir = float2(-0.682, 0.731);
  float lp = frac(dot(px / s, ldir) / LINE_PX);
  float lines = smoothstep(0.0, 0.25, lp) * (1.0 - smoothstep(0.55, 0.8, lp)); // light stripe
  float etch = 0.55 + 0.45 * lines;

  // colour-dodge-ish: bright bands get brighter where the lines are lit
  float3 foil = bands * etch * (0.3 + 0.45 * pillar + 0.5 * g);
  foil += float3(1.0, 1.0, 1.0) * lines * g * 0.18;
  float amt = STRENGTH * (0.5 + 0.3 * pillar + 0.3 * g);
  float3 bg = lerp(c.rgb, foil, amt);

  float3 txt = lerp(c.rgb, bands, TEXT_TINT);
  float3 rgb = lerp(bg, txt, textMask);

  // --- frame: silver-rainbow edge with the same pillars, brighter ---------
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float bevel = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 1.8 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 3.0 * s, edge - B)) * step(B, edge);

  float3 silver = float3(0.78, 0.80, 0.85);
  float3 frameCol = lerp(silver, sunpillar(h + 0.15), 0.55);
  frameCol *= (0.5 + 0.35 * sin(depth * 3.14159) + 0.3 * pillar + 0.3 * g) * etch;
  frameCol += bevel * 0.45 * float3(1.0, 1.0, 1.0);
  frameCol *= 1.0 - 0.45 * outerLine;

  rgb *= 1.0 - 0.35 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
