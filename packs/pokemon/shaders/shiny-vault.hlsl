// ============================================================================
//  SHINY-VAULT  -  Windows Terminal holofoil skin
//
//  Imitates: the "Shiny Vault" / shiny rare foil (Hidden Fates, Shining
//  Fates, Paldean Fates shiny subsets): a brushed silver metallic surface
//  that brightens as the light crosses it, sprinkled with sparse, bright
//  four-point star glints that bloom and fade slowly one at a time, plus a
//  fine silver micro-glitter. Chrome silver frame.
//
//  Tuning:
//    STRENGTH   how much foil shows through empty background (0.15 .. 0.40)
//    SPEED      global motion speed (1.0 default, 0.5 = even calmer)
//    BORDER_PX  card frame width in DPI-independent pixels
//    GLINTS     fraction of grid cells that own a star glint (0 .. 1)
// ============================================================================

Texture2D shaderTexture;
SamplerState samplerState;
cbuffer PixelShaderSettings {
  float  Time;
  float  Scale;
  float2 Resolution;
  float4 Background;
};

#define STRENGTH  0.24
#define SPEED     1.0
#define BORDER_PX 12.0
#define GLINTS    0.30


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

float hash12(float2 p)
{
  float3 p3 = frac(float3(p.xyx) * 0.1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return frac((p3.x + p3.y) * p3.z);
}

float3 hash32(float2 p)
{
  float3 p3 = frac(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
  p3 += dot(p3, p3.yxz + 33.33);
  return frac((p3.xxy + p3.yzz) * p3.zyx);
}

float vnoise(float2 p)
{
  float2 i = floor(p);
  float2 f = frac(p);
  float2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
  float a = hash12(i);
  float b = hash12(i + float2(1.0, 0.0));
  float c = hash12(i + float2(0.0, 1.0));
  float d = hash12(i + float2(1.0, 1.0));
  return lerp(lerp(a, b, u.x), lerp(c, d, u.x), u.y);
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

// Sparse four-point star glints (plus short diagonal rays).
// Returns rgb.
float3 glints(float2 p, float cell, float seed, float dens, float armLen,
              float2 lightP, float t)
{
  float2 id = floor(p / cell);
  float2 f  = frac(p / cell);
  float3 h  = hash32(id + seed);
  float3 k  = hash32(id * 1.53 + seed + 41.9);

  float2 ctr = 0.3 + 0.4 * h.xy;
  float2 d   = (f - ctr) * cell;
  float  L   = armLen * (0.6 + 0.6 * k.x);

  float core  = exp(-dot(d, d) / sq(L * 0.14));
  float armH  = exp(-abs(d.x) / (L * 0.32)) * exp(-sq(d.y / (L * 0.035 + 0.35)));
  float armV  = exp(-abs(d.y) / (L * 0.32)) * exp(-sq(d.x / (L * 0.035 + 0.35)));
  float2 dd   = float2(d.x + d.y, d.x - d.y) * 0.7071;
  float armD  = exp(-abs(dd.x) / (L * 0.12)) * exp(-sq(dd.y / (L * 0.03 + 0.3)))
              + exp(-abs(dd.y) / (L * 0.12)) * exp(-sq(dd.x / (L * 0.03 + 0.3)));
  float halo  = exp(-dot(d, d) / sq(L * 0.45)) * 0.18;
  float shape = core + armH + armV + armD * 0.35 + halo;

  // keep the rays inside the cell
  float2 win = smoothstep(0.0, 0.2, f) * smoothstep(0.0, 0.2, 1.0 - f);
  shape *= win.x * win.y;

  // slow bloom: each glint swells and fades on its own ~10-20 s cycle
  float rate  = 0.32 + 0.3 * k.y;
  float bloom = pow(saturate(sin(t * rate + h.z * TAU * 7.0)), 4.0);

  // glints near the light burn brighter
  float2 C   = (id + ctr) * cell;
  float  lit = 0.45 + 0.9 * exp(-dot(lightP - C, lightP - C) / sq(cell * 6.0));

  float3 tint = lerp(float3(1.0, 1.0, 1.0), spectrum(k.z + t * 0.02), 0.28);
  return tint * shape * bloom * lit * step(h.z, dens);
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

  // ---- brushed silver: anisotropic streak noise along a shallow diagonal
  float2 bdir  = float2(0.94, 0.34);
  float2 q     = float2(dot(p, bdir), dot(p, float2(-bdir.y, bdir.x)));
  float  brush = vnoise(float2(q.x * 0.012, q.y * 0.9)) * 0.6
               + vnoise(float2(q.x * 0.030, q.y * 2.1)) * 0.4;

  float glare = exp(-sq(dot(rel, float2(0.8, -0.6)) * 2.8)) * 0.65
              + exp(-dot(rel, rel) * 3.0) * 0.35;

  // metal gets a faint oil-slick rainbow where the light hits it
  float  sheenHue = dot(rel, float2(0.7, 0.5)) * 1.2 + brush * 0.3 + t * 0.04;
  float3 silver   = float3(0.70, 0.73, 0.79) * (0.20 + 0.16 * brush + 0.42 * glare);
  float3 foilBase = silver + spectrum(sheenHue) * glare * 0.07;

  // ---- fine micro-glitter in the metal
  float3 mg  = hash32(floor(p / 3.0) + 7.0);
  float2 mgd = (frac(p / 3.0) - 0.5) * 3.0;                 // px from glitter cell centre
  float  mgl = step(0.94, mg.x) * exp(-dot(mgd, mgd) / 0.45) * pow(saturate(0.5 + 0.5 * cos(mg.y * TAU + t * 0.5 + dot(rel, float2(4.0, 3.0)))), 6.0);
  float3 glit = float3(0.9, 0.93, 1.0) * mgl * (0.3 + 0.9 * glare);

  // ---- sparse star glints (two scales)
  float3 stars = glints(p,        90.0, 5.0,  GLINTS,       26.0, lightP, t)
               + glints(p + 43.0, 47.0, 61.0, GLINTS * 0.6, 14.0, lightP, t) * 0.8;

  // ---- calm zone around glyphs
  float2 tx = S / res;
  float near = 0.0;
  near = max(near, textAt(tex + float2( 7.0,  0.0) * tx));
  near = max(near, textAt(tex + float2(-7.0,  0.0) * tx));
  near = max(near, textAt(tex + float2( 0.0,  8.0) * tx));
  near = max(near, textAt(tex + float2( 0.0, -8.0) * tx));
  near = max(near, textAt(tex + float2( 5.0,  5.0) * tx));
  near = max(near, textAt(tex + float2(-5.0,  5.0) * tx));
  near = max(near, textAt(tex + float2( 5.0, -5.0) * tx));
  near = max(near, textAt(tex + float2(-5.0, -5.0) * tx));
  float calm = 1.0 - 0.8 * near;

  float3 bgOut   = lerp(c.rgb, foilBase, STRENGTH)
                 + (glit * STRENGTH * 1.2 + stars * STRENGTH * 3.0) * calm;
  float3 textOut = lerp(c.rgb, c.rgb * (0.9 + 0.2 * glare), 0.06);
  float3 outc    = lerp(bgOut, textOut, tmask);

  // ---- chrome silver frame -------------------------------------------------
  float bw   = BORDER_PX * S;
  float edge = min(min(px.x, res.x - px.x), min(px.y, res.y - px.y));
  float inFrame = 1.0 - smoothstep(bw - 0.75, bw + 0.75, edge);

  float  along = (px.x - px.y) / S;
  float  sweep = exp(-sq((uvA.x + uvA.y) - (lightA.x + lightA.y)) * 4.5);
  float  chrome = 0.50 + 0.12 * sin(along * 0.018 + t * 0.28)
                       + 0.08 * sin(along * 0.051 - t * 0.19) + 0.10 * brush;
  float3 fcol = float3(0.74, 0.77, 0.83) * chrome;
  fcol = lerp(fcol, float3(1.0, 1.0, 1.0), sweep * 0.45);
  fcol += spectrum(sheenHue + along * 0.001) * sweep * 0.10;
  fcol += stars * 1.4 + glit * 0.8;

  float u = saturate(edge / bw);
  fcol *= 0.74 + 0.36 * sin(u * PI);
  fcol *= lerp(0.45, 1.0, smoothstep(0.0, 1.2 * S, edge));
  float hiL = 1.0 - smoothstep(0.5 * S, 1.0 * S, abs(edge - (bw - 2.4 * S)));
  fcol += hiL * 0.22 * (0.6 + 0.6 * sweep);
  float groove = 1.0 - smoothstep(0.4 * S, 0.9 * S, abs(edge - (bw - 0.8 * S)));
  fcol *= 1.0 - groove * 0.6;

  float shadow = exp(-max(edge - bw, 0.0) / (2.0 * S)) * (1.0 - inFrame);
  outc *= 1.0 - shadow * 0.35 * (1.0 - tmask);

  outc = lerp(outc, saturate(fcol), inFrame * (1.0 - tmask * 0.85));
  return float4(saturate(outc), 1.0);
}
