// ============================================================================
// Skin: VSTAR CREST
// Imitates: the Sword & Shield Rare Holo VSTAR (Crown Zenith Leafeon VSTAR
//   14) - one step above VMAX: the grooved etched foil and the 45deg
//   sunpillar beam, in a heavy platinum-into-gold frame, with a gold star
//   crest of fine rays radiating from the centre that a pulse of gold light
//   runs out along. The pokeshell Rare Holo VSTAR card animation.
//
// Tuning:
//   STRENGTH   how strongly the foil shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling (VSTAR: the heaviest frame)
//   BEAM_S     seconds for the beam to cross the terminal once
//   RAYS       number of star-crest rays
// ============================================================================

#define STRENGTH  0.26
#define SPEED     1.0
#define BORDER_PX 16.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners
#define BEAM_S    12.0
#define PULSE_S   7.0
#define RAYS      24.0
#define CELL_PX   240.0
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

// platinum -> gold, x in 0..1 (the VSTAR crest's silver-gold)
float3 platgold(float x)
{
  float3 lo = float3(0.31, 0.28, 0.23);
  float3 mid = float3(0.63, 0.59, 0.47);
  float3 hi = float3(1.0, 0.97, 0.85);
  return lerp(lerp(lo, mid, saturate(x * 2.0)), hi, saturate(x * 2.0 - 1.0));
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

  // --- the beam pair, as VMAX
  float band = 0.16 * span;
  float ph = frac(t / BEAM_S);
  float u1 = ((p.x + p.y) - (-band + ph * (span + 2.0 * band))) / band;
  float k1 = tent(u1);
  float u2 = ((p.x - p.y) - (res.x + band - ph * (span + 2.0 * band) * 0.9)) / (band * 0.7);
  float k2 = tent(u2) * 0.35;
  float3 beam = pastel(u1 * 0.9 + 0.3 + p.x / span, 0.3);

  // --- etched contour grooves (one family: lighter than VMAX, the crest carries the texture)
  float2 q = p / CELL_PX;
  float nA = vnoise(q) * 0.65 + vnoise(q * 2.3 + 7.0) * 0.35;
  float gA = groove(nA, 0.12, 2.0);

  // --- the star crest: fine rays from the centre, alternating long / short; a gold pulse runs outward
  float2 d = p - res * 0.5;
  float r = length(d);
  float ang = atan2(d.y, d.x);
  float stepA = 6.28318 / RAYS;
  float ai = floor(ang / stepA + 0.5);
  float da = abs(ang - ai * stepA) * r;
  float longRay = step(0.5, frac(ai * 0.5));
  float reach = lerp(0.45, 1.2, longRay) * 0.5 * length(res);
  float ray = (1.0 - smoothstep(0.6, 1.6, da)) * step(12.0, r) * (1.0 - smoothstep(reach * 0.8, reach, r));
  float rmax = 0.5 * length(res);
  float front = frac(t / PULSE_S) * (rmax + 60.0) - 30.0;
  float pulse = exp(-pow((r - front) / 26.0, 2.0));
  float3 gold = float3(1.0, 0.83, 0.42);

  float3 ground = platgold(0.35 + 0.25 * nA) * 0.2;
  float3 foil = ground + beam * k1 * 0.55 + pastel(-u2 + 0.7, 0.45) * k2 * 0.5;
  float3 cut = lerp(platgold(0.5) * 0.4, saturate(beam * 1.1), saturate(1.1 * k1 + 0.6 * k2));
  foil = lerp(foil, cut, gA * 0.8);
  foil = lerp(foil, gold * (0.55 + 0.9 * pulse), ray * (0.35 + 0.6 * pulse));
  float amt = STRENGTH * (0.55 + 0.8 * k1 + 0.4 * k2) + (gA * 0.3 + ray * (0.3 + 0.7 * pulse)) * STRENGTH;
  float3 bg = lerp(c.rgb, foil, saturate(amt));

  float3 txt = lerp(c.rgb, beam, TEXT_TINT * k1);
  float3 rgb = lerp(bg, txt, textMask);

  // --- heavy platinum-gold frame with a groove, lit by the beam
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float bevel1 = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - 2.5 * s));
  float bevel2 = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 2.0 * s)));
  float fgroove = 1.0 - smoothstep(0.0, 1.3 * s, abs(edge - B * 0.55));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 4.0 * s, edge - B)) * step(B, edge);

  // platinum at the top-left, shading into gold toward the bottom-right
  float diag = saturate((p.x + p.y) / span);
  float fl = saturate(0.25 + 0.45 * sin(depth * 3.14159) + 0.1 * sin((p.x - p.y) * 0.01 + t * 0.3));
  float3 frameCol = lerp(platgold(fl) * float3(0.95, 0.97, 1.0), platgold(fl) * float3(1.08, 0.95, 0.62), diag);
  frameCol = lerp(frameCol, saturate(beam * 1.1), 0.5 * k1);
  frameCol += (bevel1 + bevel2) * 0.3 * float3(1.0, 0.97, 0.88);
  frameCol *= 1.0 - 0.55 * fgroove;
  frameCol *= 1.0 - 0.5 * outerLine;

  rgb *= 1.0 - 0.4 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, saturate(frameCol), frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
