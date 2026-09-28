// =====================================================================
//  Skin: TINSEL
//  Imitates: the Black & White era "tinsel" holofoil -- a dense field of
//  fine, short metallic streaks (like shredded tinsel) with a glittery
//  rainbow sheen that ripples across the strands as the card tilts.
//  Windows Terminal pixel shader (ps_4_0).
//
//  Tuning:
//    STRENGTH  - how strongly the foil shows on background pixels (0.15-0.35)
//    SPEED     - global motion speed multiplier (1.0 = slow, 0.5 = slower)
//    BORDER_PX - card frame width in pixels (at 100% DPI)
//    STRAND_PX - spacing between tinsel strands in pixels
// =====================================================================

#define STRENGTH  0.26
#define SPEED     1.0
#define BORDER_PX 12.0
#define STRAND_PX 4.0

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


// ---------------------------------------------------------------- helpers
float hash21(float2 p)
{
  p = frac(p * float2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return frac(p.x * p.y);
}

float3 rainbow(float h)
{
  return 0.5 + 0.5 * cos(6.28318 * (h + float3(0.0, 0.333, 0.667)));
}

float edgeDist(float2 px)
{
  return min(min(px.x, px.y), min(Resolution.x - px.x, Resolution.y - px.y));
}

// One layer of tinsel strands running along angle `ang`.
// Returns strand intensity in .x and a per-strand random value in .y.
float2 strands(float2 px, float ang, float spacing, float segLen, float seed, float density)
{
  float sn = sin(ang);
  float cs = cos(ang);
  float2 r = float2(cs * px.x + sn * px.y, -sn * px.x + cs * px.y);
  float rowF = r.y / spacing;
  float row = floor(rowF);
  float fy = frac(rowF);
  float off = hash21(float2(row, seed)) * segLen;
  float segF = (r.x + off) / segLen;
  float seg = floor(segF);
  float fx = frac(segF);
  float hs = hash21(float2(row + seed * 3.7, seg + seed * 13.1));
  float on = step(1.0 - density, hs);
  float center = 0.5 + (frac(hs * 17.3) - 0.5) * 0.4;       // jitter strand within its row
  float core = 1.0 - smoothstep(0.08, 0.3, abs(fy - center));
  float taper = smoothstep(0.0, 0.2, fx) * smoothstep(1.0, 0.8, fx);
  return float2(on * core * taper * (0.45 + 0.55 * frac(hs * 7.7)), hs);
}

// Full tinsel texture: two near-parallel dominant layers plus a sparse cross layer.
// Returns rgb foil (already light-modulated).
float3 tinsel(float2 px, float s, float spacing, float2 tex, float2 light, float t)
{
  float3 acc = 0.0;
  float2 L = (light - 0.5) * 2.0;

  float2 a = strands(px, 1.35, spacing * s, 46.0 * s, 1.0, 0.55);
  float2 b = strands(px, 1.18, spacing * 1.3 * s, 34.0 * s, 2.0, 0.45);
  float2 k = strands(px, -0.35, spacing * 2.2 * s, 22.0 * s, 3.0, 0.25);

  // each strand is a tiny mirror: it lights up when the fake light lines up with it
  float fa = 0.5 + 0.5 * cos(6.28318 * (a.y + dot(L, float2(0.55, 0.35)) + t * 0.01));
  float fb = 0.5 + 0.5 * cos(6.28318 * (b.y + dot(L, float2(-0.4, 0.5)) - t * 0.012));
  float fk = 0.5 + 0.5 * cos(6.28318 * (k.y + dot(L, float2(0.3, -0.6))));

  float baseHue = dot(tex - light, float2(0.7, 0.9)) * 0.8 + t * 0.012;
  acc += rainbow(baseHue + a.y * 0.25) * a.x * (0.25 + 0.75 * fa * fa);
  acc += rainbow(baseHue + 0.15 + b.y * 0.25) * b.x * (0.25 + 0.75 * fb * fb) * 0.8;
  acc += lerp(rainbow(baseHue + 0.4), 1.0, 0.4) * k.x * (0.2 + 0.8 * fk * fk) * 0.6;
  return acc;
}

// Gentle glitter points (twinkle well under 1 Hz)
float glitter(float2 px, float s, float t)
{
  float cell = 7.0 * s;
  float2 g = floor(px / cell);
  float2 f = frac(px / cell) - 0.5;
  float h = hash21(g + 91.7);
  float on = step(0.92, h);
  float2 o = (float2(frac(h * 13.1), frac(h * 29.3)) - 0.5) * 0.6;
  float2 q = f - o;
  float spot = exp(-dot(q, q) * 90.0);
  float tw = 0.5 + 0.5 * sin(t * 0.9 + h * 62.8);
  return on * spot * tw * tw;
}

// ------------------------------------------------------------------- main
float4 main(float4 pos : SV_POSITION, float2 tex : TEXCOORD) : SV_TARGET
{
  float4 c = TermSample(tex);
  float t = Time * SPEED;
  float s = max(Scale, 0.5);
  float2 px = tex * Resolution;
  float aspect = Resolution.x / max(Resolution.y, 1.0);

  float2 light = float2(0.5 + 0.35 * sin(t * 0.21), 0.5 + 0.25 * cos(t * 0.17));
  float2 dd = (tex - light) * float2(aspect, 1.0);
  float glare = exp(-dot(dd, dd) * 4.0);

  // ---- background foil
  float3 tin = tinsel(px, s, STRAND_PX, tex, light, t);
  float gl = glitter(px, s, t);
  float3 haze = rainbow(dot(tex, float2(0.6, 0.8)) + t * 0.01 + light.x * 0.5) * 0.12;
  float3 foil = (tin * 1.1 + haze) * (0.5 + 0.5 * glare) + gl * float3(1.0, 0.97, 0.9) * (0.6 + 0.4 * glare);
  foil = saturate(foil);

  // ---- frame: gold edge with coarser tinsel
  float bw = BORDER_PX * s;
  float d = edgeDist(px);
  float frameMask = 1.0 - smoothstep(bw - 0.75 * s, bw + 0.25 * s, d);
  float bevelT = saturate(d / bw);
  float prof = 0.6 + 0.4 * sin(bevelT * 3.14159);

  float3 gold = float3(0.86, 0.68, 0.28);
  float3 ftin = tinsel(px, s, 3.0, tex, light, t);
  float ftLum = dot(ftin, float3(0.333, 0.333, 0.333));
  float3 frameCol = gold * prof * (0.55 + 0.6 * ftLum) + ftin * 0.3 + glare * 0.18 * gold
                  + glitter(px, s * 0.7, t + 3.0) * 0.5;
  float hiLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(d - (bw - 2.0 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(d - 0.5 * s));
  frameCol += hiLine * float3(0.4, 0.33, 0.18) - outerLine * 0.25;
  frameCol = saturate(frameCol);
  float shadow = (1.0 - smoothstep(0.0, 2.0 * s, abs(d - (bw + 1.5 * s)))) * (1.0 - frameMask);

  // ---- composite
  float3 surface = lerp(c.rgb, foil, STRENGTH);
  surface *= 1.0 - 0.45 * shadow;
  surface = lerp(surface, frameCol, frameMask);

  float textMask = smoothstep(0.04, 0.12, distance(c.rgb, Background.rgb));
  float3 textCol = lerp(c.rgb, rainbow(tex.x + tex.y + t * 0.02), 0.05);
  float3 rgb = lerp(surface, textCol, textMask);
  return float4(rgb, 1.0);
}
