// ============================================================================
//  COSMOS  -  Windows Terminal holofoil skin
//
//  Imitates: the "Cosmos holo" (galaxy foil) of Pokemon TCG Sun & Moon /
//  Sword & Shield Black Star promos, theme-deck and Build & Battle holos, and
//  the modern "cosmos" reverse holos. On the real card the foil is stamped
//  with scattered dots, thin rings and larger planet-like discs of mixed
//  sizes; as you tilt the card each one flashes a different rainbow colour
//  at a different moment, over a soft milky nebula sheen.
//
//  Here a slowly wandering fake light plays the role of the tilt: every
//  feature has its own "facet angle", so it lights up (and shifts hue) when
//  the light passes the right direction. Text pixels are left alone.
//
//  Tuning:
//    STRENGTH   how much foil shows through empty background (0.15 .. 0.45)
//    SPEED      global motion speed (1.0 default, 0.5 = even calmer)
//    BORDER_PX  card frame width in DPI-independent pixels
//    DENSITY    fraction of grid cells holding a cosmos feature (0 .. 1)
// ============================================================================

Texture2D shaderTexture;
SamplerState samplerState;
cbuffer PixelShaderSettings {
  float  Time;
  float  Scale;
  float2 Resolution;
  float4 Background;
};

#define STRENGTH  0.30
#define SPEED     1.0
#define BORDER_PX 12.0
#define DENSITY   0.55


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

// ---------------------------------------------------------------- utilities
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
  float2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);   // quintic: no blocky seams
  float a = hash12(i);
  float b = hash12(i + float2(1.0, 0.0));
  float c = hash12(i + float2(0.0, 1.0));
  float d = hash12(i + float2(1.0, 1.0));
  return lerp(lerp(a, b, u.x), lerp(c, d, u.x), u.y);
}

float fbm(float2 p)
{
  float v = 0.0;
  float a = 0.5;
  for (int i = 0; i < 4; i++)
  {
    v += a * vnoise(p);
    p = p * 2.03 + float2(17.1, 9.7);
    a *= 0.5;
  }
  return v;
}

// holographic rainbow: slightly pastel, like light split by a foil grating
float3 spectrum(float h)
{
  float3 c = 0.5 + 0.5 * cos(TAU * (h + float3(0.0, 0.333, 0.667)));
  return lerp(c, float3(1.0, 1.0, 1.0), 0.12);
}

float2 rot(float2 v, float a)
{
  float s = sin(a);
  float c = cos(a);
  return float2(c * v.x + s * v.y, -s * v.x + c * v.y);
}

// 1 where the terminal frame has text/foreground at uv, else 0
float textAt(float2 uv)
{
  float3 s = TermSample(uv).rgb;
  return smoothstep(0.04, 0.12, distance(s, Background.rgb));
}

// ------------------------------------------------------------ cosmos layer
// One jittered grid of cosmos features.
//   p       DPI-independent pixel position
//   cell    grid cell size (px)
//   rMin/rMax feature radius range, in cell units (rMax <= 0.24)
//   ringP   probability a feature is a thin ring
//   planetP probability a feature is a shaded planet with an orbit ring
//   lightP  light position (same space as p)
// Returns lit rgb (premultiplied by coverage).
float3 cosmosLayer(float2 p, float cell, float seed, float rMin, float rMax,
                   float ringP, float planetP, float2 lightP, float t)
{
  float2 g  = p / cell;
  float2 id = floor(g);
  float2 f  = frac(g);
  float3 h  = hash32(id + seed);
  float3 k  = hash32(id * 1.37 + seed + 71.3);

  float occupied = step(h.z, DENSITY);

  float radN   = lerp(rMin, rMax, k.x * k.x);   // skewed toward small
  float margin = radN * 1.8 + 0.03;             // room for planet orbits
  float2 ctr   = margin + (1.0 - 2.0 * margin) * h.xy;
  float2 d     = (f - ctr) * cell;              // px from feature centre
  float  R     = max(radN * cell, 0.9);
  float  dist  = length(d);

  float isRing   = step(k.y, ringP);
  float isPlanet = step(1.0 - planetP, k.y);
  float isDisc   = saturate(1.0 - isRing - isPlanet);

  // --- shapes (antialiased) ---
  float disc = 1.0 - smoothstep(R - 0.8, R + 0.8, dist);
  float w    = max(1.1, R * 0.16);
  float ring = 1.0 - smoothstep(w * 0.5 - 0.5, w * 0.5 + 0.5, abs(dist - R));

  float  Rb     = R * 0.72;                      // planet body radius
  float  body   = 1.0 - smoothstep(Rb - 0.8, Rb + 0.8, dist);
  float2 q      = rot(d, k.z * TAU);
  float  ell    = length(q * float2(1.0, 3.2));
  float  orbit  = 1.0 - smoothstep(w * 0.9 - 0.5, w * 0.9 + 0.5, abs(ell - R * 1.55));
  orbit *= 1.0 - body * step(q.y, 0.0);          // back half hides behind planet

  // --- how this feature catches the light ---
  float2 C       = (id + ctr) * cell;            // feature centre, px
  float2 toL     = lightP - C;
  float  lenL    = length(toL) + 1e-3;
  float2 dirL    = toL / lenL;
  float  ang     = atan2(toL.y, toL.x + 1e-4);
  float  facet   = k.z * TAU;
  float  glint   = pow(saturate(0.5 + 0.5 * cos(facet + ang * 2.0 + lenL * 0.004)), 3.0);
  float  twinkle = 0.72 + 0.28 * sin(t * (0.35 + 0.3 * h.x) + h.y * TAU);

  // each feature shows its own mini spectrum across its face
  float hue = h.x * 0.35 + ang / TAU + lenL * 0.0012
            + dot(d, dirL) / R * 0.12 + t * 0.03;
  float3 rainbow = spectrum(hue);
  float3 silver  = float3(0.78, 0.80, 0.88);
  float3 col = lerp(silver, rainbow, 0.55 + 0.45 * glint) * (0.28 + 1.05 * glint) * twinkle;

  // planet: sphere shading from the light + faint gas bands + specular dot
  float2 n2    = d / max(Rb, 0.5);
  float3 nrm   = float3(n2, sqrt(saturate(1.0 - dot(n2, n2))));
  float3 L3    = normalize(float3(dirL * 0.8, 0.6));
  float  lam   = saturate(dot(nrm, L3));
  float  bands = 0.85 + 0.15 * sin(q.y / max(Rb, 0.5) * 9.0 + h.y * 6.0);
  float3 planetCol = spectrum(hue + q.y / max(Rb, 0.5) * 0.18)
                   * (0.18 + 0.95 * lam) * bands * (0.55 + 0.6 * glint)
                   + pow(lam, 28.0) * 0.8;
  float3 orbitCol  = col * 1.1;

  float3 rgb = isDisc   * col * disc
             + isRing   * col * 0.85 * ring
             + isPlanet * (planetCol * body * (1.0 - orbit) + orbitCol * orbit);

  // soft halo around brightly glinting small dots
  // (windowed to the cell so it never shows a square edge)
  float2 win = smoothstep(0.0, 0.18, f) * smoothstep(0.0, 0.18, 1.0 - f);
  float haloR = min(R * 2.6, margin * cell);
  float halo = exp(-sq(dist / haloR) * 2.5) * glint * 0.26 * isDisc * win.x * win.y;
  rgb += rainbow * halo * twinkle;

  return rgb * occupied;
}

// ------------------------------------------------------------------ main
float4 main(float4 pos : SV_POSITION, float2 tex : TEXCOORD) : SV_TARGET
{
  float4 c = TermSample(tex);

  float  S   = max(Scale, 0.5);
  float  t   = Time * SPEED;
  float2 res = max(Resolution, float2(1.0, 1.0));
  float2 px  = tex * res;                 // device pixels
  float2 p   = px / S;                    // DPI-independent pixels
  float  aspect = res.x / res.y;
  float2 uvA = float2(tex.x * aspect, tex.y);

  // slowly wandering light = the card tilting in your hand (~15 s / ~19 s)
  float2 lightUV = float2(0.5 + 0.35 * sin(t * 0.42), 0.5 + 0.25 * cos(t * 0.33));
  float2 lightA  = float2(lightUV.x * aspect, lightUV.y);
  float2 lightP  = lightUV * res / S;

  // text mask: anything that differs from the terminal background
  float tmask = smoothstep(0.04, 0.12, distance(c.rgb, Background.rgb));

  // ---- glare: a soft diagonal band through the light plus a broad spot
  float2 rel   = uvA - lightA;
  float  glare = exp(-sq(dot(rel, float2(0.8, -0.6)) * 3.2)) * 0.7
               + exp(-dot(rel, rel) * 2.5) * 0.3;

  // ---- nebula: domain-warped fbm, drifting very slowly
  float n1 = fbm(uvA * 2.2 + float2(t * 0.010, -t * 0.007));
  float n2 = fbm(uvA * 4.1 + float2(-t * 0.012, t * 0.009) + n1 * 1.6);
  float nebHue = n2 * 0.9 + dot(rel, float2(0.6, 0.4)) * 0.7 + t * 0.05;
  float3 nebula = spectrum(nebHue) * smoothstep(0.35, 0.85, n2) * 0.30;
  float3 deep   = float3(0.035, 0.025, 0.085);
  float3 foilBase = deep + nebula * (0.6 + 0.8 * glare) + glare * 0.035;

  // ---- starfield: planets, rings/discs, fine dots
  float3 stars = 0;
  stars += cosmosLayer(p, 96.0, 11.0, 0.10, 0.22, 0.25, 0.45, lightP, t);
  stars += cosmosLayer(p + 31.0, 38.0, 37.0, 0.08, 0.22, 0.40, 0.00, lightP, t);
  stars += cosmosLayer(p + 7.0, 13.0, 83.0, 0.06, 0.14, 0.00, 0.00, lightP, t) * 0.9;
  float3 starsLit = stars * (0.75 + 1.3 * glare);

  // ---- calm zone around glyphs: stars dim near text so it never competes
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
  starsLit *= 1.0 - 0.75 * near;

  // ---- background pixels: foil at STRENGTH, stars ride on top
  float3 bgOut = lerp(c.rgb, foilBase, STRENGTH * (1.0 - 0.3 * near))
               + starsLit * STRENGTH * 1.5;

  // ---- text pixels: keep colour, whisper of foil tint (<= 8%)
  float3 textOut = lerp(c.rgb, c.rgb * (0.8 + 0.4 * spectrum(nebHue)), 0.08);

  float3 outc = lerp(bgOut, textOut, tmask);

  // ---- card frame --------------------------------------------------------
  float bw   = BORDER_PX * S;
  float edge = min(min(px.x, res.x - px.x), min(px.y, res.y - px.y));
  float inFrame = 1.0 - smoothstep(bw - 0.75, bw + 0.75, edge);

  // rainbow chrome with a light sweep running around the frame
  float  along  = (px.x - px.y) / S;
  float  metal  = 0.62 + 0.18 * sin(along * 0.021 + t * 0.30)
                       + 0.10 * sin(along * 0.057 - t * 0.21);
  float  fHue   = along * 0.0016 + dot(rel, float2(0.5, 0.5)) * 0.9 + t * 0.05;
  float  sweep  = exp(-sq((uvA.x + uvA.y) - (lightA.x + lightA.y)) * 4.0);
  float3 fcol   = lerp(float3(0.66, 0.64, 0.76) * metal, spectrum(fHue), 0.55);
  fcol *= 0.55 + 0.55 * sweep + 0.35 * glare;
  fcol += stars * (1.1 + 1.4 * sweep);           // cosmos dots glint in the frame

  // raised-rim cross-section + bevel lines
  float u    = saturate(edge / bw);
  fcol *= 0.78 + 0.32 * sin(u * PI);
  fcol *= lerp(0.45, 1.0, smoothstep(0.0, 1.2 * S, edge));             // outer dark lip
  float hiL  = 1.0 - smoothstep(0.5 * S, 1.0 * S, abs(edge - (bw - 2.4 * S)));
  fcol += hiL * 0.30 * (0.6 + 0.6 * sweep);                            // inner highlight
  float groove = 1.0 - smoothstep(0.4 * S, 0.9 * S, abs(edge - (bw - 0.8 * S)));
  fcol *= 1.0 - groove * 0.6;                                          // inner dark groove

  // shadow the frame casts onto the "card" just inside it
  float shadow = exp(-max(edge - bw, 0.0) / (2.0 * S)) * (1.0 - inFrame);
  outc *= 1.0 - shadow * 0.35 * (1.0 - tmask);

  outc = lerp(outc, saturate(fcol), inFrame * (1.0 - tmask * 0.85));

  return float4(saturate(outc), 1.0);
}
