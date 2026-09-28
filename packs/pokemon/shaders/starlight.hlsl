// ============================================================================
//  STARLIGHT  -  Windows Terminal holofoil skin
//
//  Imitates: the vintage WOTC "starlight" holo of Base Set, Jungle and Fossil
//  (1999-2000) holo rares - a dense spray of tiny star speckles in the foil,
//  with broad diagonal rainbow bands that roll across the card as you tilt
//  it. The frame is the classic yellow card border with a soft metallic sheen.
//
//  Tuning:
//    STRENGTH   how much foil shows through empty background (0.15 .. 0.45)
//    SPEED      global motion speed (1.0 default, 0.5 = even calmer)
//    BORDER_PX  card frame width in DPI-independent pixels
//    SPECKLE    density of the fine star speckle (0 .. 1)
// ============================================================================

Texture2D shaderTexture;
SamplerState samplerState;
cbuffer PixelShaderSettings {
  float  Time;
  float  Scale;
  float2 Resolution;
  float4 Background;
};

#define STRENGTH  0.28
#define SPEED     1.0
#define BORDER_PX 12.0
#define SPECKLE   0.45


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

static const float TAU = 6.28318531;
static const float PI  = 3.14159265;

float sq(float x) { return x * x; }

float3 hash32(float2 p)
{
  float3 p3 = frac(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
  p3 += dot(p3, p3.yxz + 33.33);
  return frac((p3.xxy + p3.yzz) * p3.zyx);
}

float3 spectrum(float h)
{
  float3 c = 0.5 + 0.5 * cos(TAU * (h + float3(0.0, 0.333, 0.667)));
  return lerp(c, float3(1.0, 1.0, 1.0), 0.12);
}

float textAt(float2 uv)
{
  float3 s = TermSample(uv).rgb;
  return smoothstep(0.04, 0.12, distance(s, Background.rgb));
}

// One grid of star speckles. Returns (brightness, hue offset).
//   p      DPI-independent px   cell  grid size (px)
//   dens   occupancy            r     star radius (px)
//   cross  1 = give the star tiny 4-point arms
float2 speckle(float2 p, float cell, float seed, float dens, float r, float cross,
               float2 lightP, float t)
{
  float2 id = floor(p / cell);
  float2 f  = frac(p / cell);
  float3 h  = hash32(id + seed);
  float3 k  = hash32(id * 1.61 + seed + 19.7);

  float  m   = 0.25;
  float2 ctr = m + (1.0 - 2.0 * m) * h.xy;
  float2 d   = (f - ctr) * cell;
  float  rr  = r * (0.6 + 0.8 * k.x);

  float core = exp(-dot(d, d) / sq(rr));
  float arms = exp(-abs(d.x) / (rr * 1.6)) * exp(-sq(d.y / (rr * 0.35)))
             + exp(-abs(d.y) / (rr * 1.6)) * exp(-sq(d.x / (rr * 0.35)));
  float shape = core + arms * 0.5 * cross;

  // each speckle faces its own way: it lights when the light is "right"
  float2 C     = (id + ctr) * cell;
  float2 toL   = lightP - C;
  float  ang   = atan2(toL.y, toL.x + 1e-4);
  float  glint = pow(saturate(0.5 + 0.5 * cos(k.y * TAU + ang * 3.0 + length(toL) * 0.006)), 5.0);
  float  tw    = 0.75 + 0.25 * sin(t * (0.4 + 0.3 * k.z) + h.z * TAU);

  float on = step(h.z, dens);
  return float2(shape * (0.22 + 1.2 * glint) * tw * on, k.z);
}

float4 main(float4 pos : SV_POSITION, float2 tex : TEXCOORD) : SV_TARGET
{
  float4 c = TermSample(tex);

  float  S   = max(Scale, 0.5);
  float  t   = Time * SPEED;
  float2 res = max(Resolution, float2(1.0, 1.0));
  float2 px  = tex * res;
  float2 p   = px / S;
  float  aspect = res.x / res.y;
  float2 uvA = float2(tex.x * aspect, tex.y);

  float2 lightUV = float2(0.5 + 0.35 * sin(t * 0.42), 0.5 + 0.25 * cos(t * 0.33));
  float2 lightA  = float2(lightUV.x * aspect, lightUV.y);
  float2 lightP  = lightUV * res / S;
  float2 rel     = uvA - lightA;

  float tmask = smoothstep(0.04, 0.12, distance(c.rgb, Background.rgb));

  // ---- diagonal rainbow bands rolling slowly across (~14 s per band)
  float  s        = dot(uvA, float2(0.8, 0.6));
  float  bandHue  = (s * 1.8 - t * 0.07) * 1.6 + dot(rel, float2(0.35, 0.25));  // full rainbow across each band
  float  bandMask = pow(saturate(0.5 + 0.5 * cos(TAU * (s * 1.8 - t * 0.07))), 2.0);
  float  glare    = exp(-sq(dot(rel, float2(0.6, -0.8)) * 2.6)) * 0.6
                  + exp(-dot(rel, rel) * 3.0) * 0.4;
  float3 bands    = spectrum(bandHue) * (0.25 + 0.75 * bandMask) * (0.35 + 0.65 * glare);

  // faint brushed-foil grain so the surface doesn't look like flat paint
  float grain = hash32(floor(p * float2(0.5, 0.08))).x;
  float3 foilBase = float3(0.045, 0.045, 0.06) * (0.85 + 0.3 * grain) + bands * 0.60;

  // ---- star speckle: fine dense layer + sparser tiny crosses
  float2 s1 = speckle(p,        4.0, 3.0,  SPECKLE,       0.55, 0.0, lightP, t);
  float2 s2 = speckle(p + 5.0, 11.0, 29.0, SPECKLE * 0.5, 0.80, 1.0, lightP, t);
  float3 spk = (spectrum(bandHue + s1.y * 0.25) * 0.6 + 0.4) * s1.x
             + (spectrum(bandHue + s2.y * 0.25) * 0.5 + 0.5) * s2.x * 1.2;
  spk *= 0.45 + 0.9 * bandMask + 0.6 * glare;       // speckle blazes inside the bands

  // ---- calm zone around glyphs
  float2 tx = S / res;
  float near = 0.0;
  near = max(near, textAt(tex + float2( 6.0,  0.0) * tx));
  near = max(near, textAt(tex + float2(-6.0,  0.0) * tx));
  near = max(near, textAt(tex + float2( 0.0,  7.0) * tx));
  near = max(near, textAt(tex + float2( 0.0, -7.0) * tx));
  spk *= 1.0 - 0.7 * near;

  float3 bgOut   = lerp(c.rgb, foilBase, STRENGTH) + spk * STRENGTH * 2.4;
  float3 textOut = lerp(c.rgb, c.rgb * (0.8 + 0.4 * spectrum(bandHue)), 0.07);
  float3 outc    = lerp(bgOut, textOut, tmask);

  // ---- yellow card border ------------------------------------------------
  float bw   = BORDER_PX * S;
  float edge = min(min(px.x, res.x - px.x), min(px.y, res.y - px.y));
  float inFrame = 1.0 - smoothstep(bw - 0.75, bw + 0.75, edge);

  float  sweep = exp(-sq((uvA.x + uvA.y) - (lightA.x + lightA.y)) * 5.0);
  float  along = (px.x - px.y) / S;
  float3 yellow = float3(0.93, 0.76, 0.16);
  float3 fcol = yellow * (0.68 + 0.08 * sin(along * 0.03 + t * 0.25));
  fcol = lerp(fcol, float3(1.0, 0.95, 0.72), sweep * 0.45);           // light sweep
  fcol += spectrum(bandHue) * sweep * 0.08;                           // hint of foil

  float u = saturate(edge / bw);
  fcol *= 0.80 + 0.28 * sin(u * PI);
  fcol *= lerp(0.5, 1.0, smoothstep(0.0, 1.2 * S, edge));
  float hiL = 1.0 - smoothstep(0.5 * S, 1.0 * S, abs(edge - (bw - 2.4 * S)));
  fcol += hiL * 0.18;
  float groove = 1.0 - smoothstep(0.4 * S, 0.9 * S, abs(edge - (bw - 0.8 * S)));
  fcol *= 1.0 - groove * 0.55;

  float shadow = exp(-max(edge - bw, 0.0) / (2.0 * S)) * (1.0 - inFrame);
  outc *= 1.0 - shadow * 0.35 * (1.0 - tmask);

  outc = lerp(outc, saturate(fcol), inFrame * (1.0 - tmask * 0.85));
  return float4(saturate(outc), 1.0);
}
