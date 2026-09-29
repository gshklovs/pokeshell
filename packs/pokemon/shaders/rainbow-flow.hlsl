// ============================================================================
// Skin: RAINBOW FLOW
// Imitates: the Sword & Shield Rare Rainbow (Evolving Skies Leafeon VMAX
//   204) - a pastel rainbow wash flowing along the diagonal, dense diagonal
//   etched lines that flash white as a sheen crosses them, and a fine glitter
//   that sparks here and there, inside a pastel rainbow frame. The pokeshell
//   Rare Rainbow card animation.
//
// Tuning:
//   STRENGTH   how strongly the rainbow shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling
//   FLOW_S     seconds for the rainbow to flow one full cycle
//   ETCH_PX    spacing of the dense diagonal etched lines in pixels
// ============================================================================

#define STRENGTH  0.24
#define SPEED     1.0
#define BORDER_PX 12.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners
#define FLOW_S    18.0
#define SHEEN_S   10.0
#define ETCH_PX   3.0
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

// the rainbow-rare palette: very light pastel (hsl ~82% lightness)
float3 pastel(float h)
{
  return lerp(hue(h), float3(1.0, 1.0, 1.0), 0.5);
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
  float span = res.x + res.y;

  float textMask = smoothstep(0.05, 0.12, distance(c.rgb, Background.rgb));

  // --- the rainbow wash, flowing along the diagonal (with a gentle hue wobble)
  float diag = (p.x + p.y) / span;
  float h = diag * 1.6 - t / FLOW_S + 0.05 * sin(6.28318 * (t / FLOW_S - diag));
  float3 rain = pastel(h);

  // --- dense diagonal etched lines with a slow wave in them (one light line every ETCH_PX)
  float u = (p.x - p.y * 0.8) + 4.0 * sin(p.y / 18.0) + 3.0 * sin(p.x / 33.0);
  float lp = frac(u / ETCH_PX);
  float etch = smoothstep(0.0, 0.2, lp) * (1.0 - smoothstep(0.35, 0.55, lp));

  // --- the sheen: a narrow band crossing on the diagonal, the etched lines flash as it passes
  float ph = frac(t / SHEEN_S);
  float dd = ((p.x + p.y) - (-0.1 * span + ph * 1.2 * span)) / (0.035 * span);
  float k = exp(-dd * dd);

  // --- glitter: sparse single-px sparks, each flashing briefly every few seconds
  float2 gc = floor(p / 4.0);
  float gh = hash21(gc);
  float2 gd = frac(p / 4.0) - float2(0.5, 0.5);
  float gdot = exp(-dot(gd, gd) * 28.0);
  float flash = pow(saturate(sin(t * (0.5 + 0.4 * gh) + gh * 90.0)), 16.0);
  float glit = gdot * flash * step(gh, 0.04);

  float3 foil = rain * (0.55 + 0.25 * etch);
  foil = lerp(foil, float3(1.0, 1.0, 1.0), etch * 0.55 * k + 0.18 * k);
  float amt = STRENGTH * (0.75 + 0.2 * etch + 0.8 * k);
  float3 bg = lerp(c.rgb, foil, amt) + float3(1.0, 1.0, 1.0) * glit * 0.5;

  float3 txt = lerp(c.rgb, rain, TEXT_TINT);
  float3 rgb = lerp(bg, txt, textMask);

  // --- pastel rainbow frame, flowing with the wash ---------------------------
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float bevel = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 1.8 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 3.0 * s, edge - B)) * step(B, edge);

  float3 frameCol = pastel(h + 0.1) * (0.62 + 0.3 * sin(depth * 3.14159)) * (0.9 + 0.12 * etch);
  frameCol = lerp(frameCol, float3(1.0, 1.0, 1.0), 0.5 * k);
  frameCol += bevel * 0.35 * float3(1.0, 1.0, 1.0);
  frameCol *= 1.0 - 0.45 * outerLine;

  rgb *= 1.0 - 0.35 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
