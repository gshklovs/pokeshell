// ============================================================================
// Skin: GALLERY
// Imitates: the Trainer Gallery / Galarian Gallery Rare Holo (Crown Zenith
//   Lapras GG05) - a full-bleed painting on a fine linen-textured foil with
//   a soft pastel holo sheen: a vertical pastel band drifts across, the
//   canvas weave glints inside it, the frame is a thin pastel-pearl edge.
//   The pokeshell Trainer Gallery card animation.
//
// Tuning:
//   STRENGTH   how strongly the foil shows through the background (0.12-0.3)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling
//   SWEEP_S    seconds for the pastel band to cross the terminal once
//   WEAVE_PX   size of one linen thread in pixels
// ============================================================================

#define STRENGTH  0.22
#define SPEED     1.0
#define BORDER_PX 11.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners
#define SWEEP_S   14.0
#define WEAVE_PX  3.0
#define TEXT_TINT 0.04

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

float3 pastel(float h, float w)
{
  return lerp(hue(h), float3(1.0, 1.0, 1.0), w);
}

float cardEdge(float2 px, float radius)
{
  float2 h = Resolution * 0.5;
  float2 q = abs(px - h) - (h - radius);
  float sd = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;
  return -sd;
}

float tent(float u)
{
  float k = saturate(1.0 - abs(u * 2.0));
  return k * k * (3.0 - 2.0 * k);
}

// a contour groove of field n every `step` units, ~w px wide (fwidth keeps the width even)
float groove(float n, float stepN, float w)
{
  float f = n / stepN;
  float d = abs(frac(f + 0.5) - 0.5) / max(fwidth(f), 1e-4);
  return 1.0 - smoothstep(w * 0.5, w * 0.5 + 1.0, d);
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

  float textMask = smoothstep(0.05, 0.12, distance(c.rgb, Background.rgb));

  // --- basket-weave linen: 2x2 blocks of threads, alternately horizontal / vertical
  float2 w = floor(p / WEAVE_PX);
  float2 f = frac(p / WEAVE_PX);
  float blk = fmod(floor(w.x * 0.5) + floor(w.y * 0.5), 2.0);
  float thread = lerp(step(0.5, fmod(w.y, 2.0)), step(0.5, fmod(w.x, 2.0)), blk);
  float shade = lerp(0.5 + 0.5 * sin(f.y * 3.14159), 0.5 + 0.5 * sin(f.x * 3.14159), blk);
  float weave = thread * shade;

  // --- a vertical pastel band sweeping left -> right (slightly slanted), a slow light drift
  float ph = frac(t / SWEEP_S);
  float bw = 0.12 * res.x;
  float ctr = -0.2 * res.x + ph * 1.4 * res.x;
  float band = exp(-pow((p.x + 0.25 * p.y - ctr) / bw, 2.0));
  float3 sheen = pastel(p.x / res.x * 0.8 + 0.55 + ph * 0.3, 0.62);
  float2 light = float2(0.5 + 0.35 * sin(t * 0.21), 0.5 + 0.25 * cos(t * 0.17));
  float glow = 1.0 - smoothstep(0.0, 0.8, distance(tex, light));

  float3 ground = float3(0.07, 0.06, 0.08) + pastel(0.8 + 0.1 * tex.y, 0.8) * 0.05 * glow;
  float3 foil = ground + sheen * band * 0.55 + weave * (0.05 + 0.3 * band) * float3(1.0, 0.98, 1.0);
  float amt = STRENGTH * (0.45 + 0.9 * band + 0.3 * weave);
  float3 bg = lerp(c.rgb, foil, saturate(amt));

  float3 txt = lerp(c.rgb, sheen, TEXT_TINT * band);
  float3 rgb = lerp(bg, txt, textMask);

  // --- thin pastel-pearl frame with a bevel; the band lights it as it passes
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float bevel1 = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - 2.0 * s));
  float bevel2 = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 1.5 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 3.0 * s, edge - B)) * step(B, edge);

  float3 pearl = pastel(0.85 + 0.25 * tex.x + 0.1 * sin(t * 0.2), 0.7) * 0.8;
  float3 frameCol = lerp(pearl, saturate(sheen * 1.1), 0.45 * band);
  frameCol += (bevel1 + bevel2) * 0.22;
  frameCol *= 1.0 - 0.5 * outerLine;

  rgb *= 1.0 - 0.35 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, saturate(frameCol), frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
