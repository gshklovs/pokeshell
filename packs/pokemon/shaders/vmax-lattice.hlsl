// ============================================================================
// Skin: VMAX LATTICE
// Imitates: the Sword & Shield Rare Holo VMAX (Evolving Skies Vaporeon VMAX
//   30) - a heavier, grooved gunmetal frame and a bold etched lattice of
//   contour grooves cut into the foil, which light up in rainbow as the
//   45deg sunpillar beam sweeps across. The pokeshell Rare Holo VMAX card
//   animation.
//
// Tuning:
//   STRENGTH   how strongly the foil shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling (VMAX gets a heavy frame)
//   BEAM_S     seconds for the beam to cross the terminal once
//   CELL_PX    rough size of the etched lattice cells in pixels
// ============================================================================

#define STRENGTH  0.26
#define SPEED     1.0
#define BORDER_PX 16.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners
#define BEAM_S    12.0
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

// gunmetal: dark steel -> pale steel, x in 0..1
float3 gunmetal(float x)
{
  float3 lo = float3(0.23, 0.25, 0.28);
  float3 mid = float3(0.46, 0.51, 0.55);
  float3 hi = float3(0.93, 0.95, 0.96);
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

  // --- the beam: 45deg, sweeping once per BEAM_S (plus the faint counter beam)
  float band = 0.16 * span;
  float ph = frac(t / BEAM_S);
  float u1 = ((p.x + p.y) - (-band + ph * (span + 2.0 * band))) / band;
  float k1 = tent(u1);
  float u2 = ((p.x - p.y) - (res.x + band - ph * (span + 2.0 * band) * 0.9)) / (band * 0.7);
  float k2 = tent(u2) * 0.35;
  float3 beam = pastel(u1 * 0.9 + 0.3 + p.x / span, 0.3);

  // --- the etched lattice: two families of contour grooves of a slow swirl field
  float2 q = p / CELL_PX;
  float nA = vnoise(q) * 0.65 + vnoise(q * 2.3 + 7.0) * 0.35;
  float nB = vnoise(q * 0.8 + 31.0) * 0.6 + vnoise(q * 1.9 + 13.0) * 0.4;
  float gA = groove(nA, 0.12, 2.2);
  float gB = groove(nB + 0.35 * (q.x - q.y), 0.14, 2.2);
  float lattice = max(gA, gB);

  float3 ground = gunmetal(0.35 + 0.25 * nA) * 0.22;
  float3 foil = ground + beam * k1 * 0.55 + pastel(-u2 + 0.7, 0.45) * k2 * 0.5;
  // the grooves catch the beam hard (the card's etched contours flare rainbow)
  float3 cut = lerp(gunmetal(0.5) * 0.45, saturate(beam * 1.1), saturate(1.1 * k1 + 0.6 * k2));
  foil = lerp(foil, cut, lattice);
  float amt = STRENGTH * (0.55 + 0.8 * k1 + 0.4 * k2) + lattice * STRENGTH * (0.2 + 0.45 * k1);
  float3 bg = lerp(c.rgb, foil, saturate(amt));

  float3 txt = lerp(c.rgb, beam, TEXT_TINT * k1);
  float3 rgb = lerp(bg, txt, textMask);

  // --- heavy gunmetal frame with a groove, lit by the beam ----------------
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float bevel1 = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - 2.5 * s));
  float bevel2 = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 2.0 * s)));
  float fgroove = 1.0 - smoothstep(0.0, 1.3 * s, abs(edge - B * 0.55));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 4.0 * s, edge - B)) * step(B, edge);

  float fl = saturate(0.2 + 0.45 * sin(depth * 3.14159) + 0.1 * sin((p.x - p.y) * 0.01 + t * 0.3));
  float3 frameCol = gunmetal(fl);
  frameCol = lerp(frameCol, saturate(beam * 1.1), 0.55 * k1);
  frameCol += (bevel1 + bevel2) * 0.3 * float3(1.0, 1.0, 1.0);
  frameCol *= 1.0 - 0.55 * fgroove;
  frameCol *= 1.0 - 0.5 * outerLine;

  rgb *= 1.0 - 0.4 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
