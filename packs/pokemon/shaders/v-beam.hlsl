// ============================================================================
// Skin: V BEAM
// Imitates: the Sword & Shield Rare Holo V (Evolving Skies Sylveon V 74) - a
//   silver frame and a 45deg "sunpillar" rainbow beam that sweeps the whole
//   card, frame included, with a fainter beam crossing the other way and a
//   few sparkles, over fine diagonal etched lines. The pokeshell Rare Holo V
//   card animation.
//
// Tuning:
//   STRENGTH   how strongly the foil shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling
//   BEAM_S     seconds for the beam to cross the terminal once
//   LINE_PX    spacing of the fine etched lines in pixels
// ============================================================================

#define STRENGTH  0.26
#define SPEED     1.0
#define BORDER_PX 12.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners
#define BEAM_S    12.0
#define LINE_PX   5.0
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

// 0..1 tent across a band: u = distance from the band centre in band widths
float tent(float u)
{
  float k = saturate(1.0 - abs(u * 2.0));
  return k * k * (3.0 - 2.0 * k);
}

// a four-point sparkle in a sparse grid, twinkling slowly
float sparkle(float2 p, float cell, float seed, float dens, float t)
{
  float2 id = floor(p / cell);
  float h = hash21(id + seed);
  float2 ctr = (id + 0.25 + 0.5 * float2(hash21(id + seed + 1.7), hash21(id + seed + 5.3))) * cell;
  float2 d = abs(p - ctr);
  float r = 1.2;
  float shape = exp(-dot(d, d) / (r * r))
              + 0.6 * exp(-d.x / 4.0) * exp(-d.y * d.y / 0.5)
              + 0.6 * exp(-d.y / 4.0) * exp(-d.x * d.x / 0.5);
  float tw = pow(saturate(sin(t * (0.35 + 0.3 * h) + h * 50.0)), 6.0);
  return shape * tw * step(h, dens);
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

  // --- the beam pair: the main beam runs along x + y = const, the counter beam along x - y
  float band = 0.16 * span;
  float ph = frac(t / BEAM_S);
  float u1 = ((p.x + p.y) - (-band + ph * (span + 2.0 * band))) / band;
  float k1 = tent(u1);
  float u2 = ((p.x - p.y) - (res.x + band - ph * (span + 2.0 * band) * 0.9)) / (band * 0.7);
  float k2 = tent(u2) * 0.45;
  float3 beam1 = pastel(u1 * 0.9 + 0.3 + p.x / span, 0.35);
  float3 beam2 = pastel(-u2 * 0.9 + 0.7, 0.45);

  // --- fine diagonal etched lines (the V foil texture), lit mostly inside the beam
  float lp = frac(dot(p, float2(-0.682, 0.731)) / LINE_PX);
  float lines = smoothstep(0.0, 0.25, lp) * (1.0 - smoothstep(0.55, 0.8, lp));

  // quiet silver-pastel ground so the card never goes flat between sweeps
  float3 ground = pastel((p.x + p.y) / span * 1.5 + t / 40.0, 0.55) * 0.18;
  float3 foil = ground * (0.7 + 0.3 * lines)
              + beam1 * k1 * (0.55 + 0.45 * lines)
              + beam2 * k2 * (0.6 + 0.4 * lines);
  float amt = STRENGTH * (0.5 + 0.9 * k1 + 0.5 * k2);
  float spk = sparkle(p, 80.0, 3.0, 0.4, t) + sparkle(p + 31.0, 53.0, 11.0, 0.2, t * 1.3);
  spk *= 0.4 + 0.8 * k1;                           // they flare as the beam passes
  float3 bg = lerp(c.rgb, foil, amt) + float3(1.0, 0.95, 1.0) * spk * STRENGTH * 1.4;

  float3 txt = lerp(c.rgb, beam1, TEXT_TINT * k1);
  float3 rgb = lerp(bg, txt, textMask);

  // --- silver frame: the beam sweeps across it too -------------------------
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float bevel = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 1.8 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 3.0 * s, edge - B)) * step(B, edge);

  float3 silver = float3(0.74, 0.77, 0.82);
  float3 frameCol = silver * (0.55 + 0.35 * sin(depth * 3.14159) + 0.08 * lines);
  frameCol = lerp(frameCol, beam1 * 1.1, 0.6 * k1);
  frameCol = lerp(frameCol, beam2, 0.5 * k2);
  frameCol += bevel * 0.4 * float3(1.0, 1.0, 1.0);
  frameCol *= 1.0 - 0.45 * outerLine;

  rgb *= 1.0 - 0.35 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
