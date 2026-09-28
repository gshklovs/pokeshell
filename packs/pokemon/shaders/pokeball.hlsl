// =====================================================================
// Skin: POKE BALL REVERSE HOLO
// Imitates: the Scarlet & Violet era "Poke Ball" pattern reverse
//   holofoil (151 and later sets): a staggered field of Poke Ball
//   icons stamped in a silvery rainbow foil.
// On the terminal: faint silver Poke Balls behind the text with a
//   slow rainbow drift and a silver foil frame.
//   Icon: circle, thick horizontal band, centre button ring + dot.
// Tuning:
//   STRENGTH   background foil amount (0.15 - 0.35)
//   SPEED      animation speed multiplier
//   BORDER_PX  frame width in pixels at 100% DPI
//   TILE_PX    size of one ball tile in pixels at 100% DPI
// =====================================================================
#define STRENGTH  0.25
#define SPEED     1.0
#define BORDER_PX 12.0
#define TILE_PX   42.0

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


static const float TAU = 6.2831853;

float sq(float x) { return x * x; }

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
    float d = hash21(i + float2(0.0, 1.0));
    float e = hash21(i + float2(1.0, 1.0));
    return lerp(lerp(a, b, u.x), lerp(d, e, u.x), u.y);
}

float3 spectrum(float h)
{
    return 0.5 + 0.5 * cos(TAU * (h + float3(0.0, 0.33, 0.67)));
}

// silver with a rainbow sheen
float3 silverFoil(float h, float rainbow)
{
    return lerp(float3(0.80, 0.82, 0.87), spectrum(h), rainbow);
}

float fill(float d, float aa) { return 1.0 - smoothstep(-aa, aa, d); }   // d < 0 inside

float4 main(float4 pos : SV_POSITION, float2 tex : TEXCOORD) : SV_TARGET
{
    float4 c = TermSample(tex);

    float  s      = max(Scale, 1.0);
    float  t      = Time * SPEED;
    float2 px     = tex * Resolution;
    float2 uv     = px / Resolution.y;
    float  aspect = Resolution.x / Resolution.y;

    float2 lightPos = float2(aspect * (0.5 + 0.35 * sin(t * 0.33)),
                             0.5 + 0.25 * cos(t * 0.41));
    float2 toL = uv - lightPos;

    float textM = smoothstep(0.05, 0.15, distance(c.rgb, Background.rgb));

    float edge   = min(min(px.x, px.y), min(Resolution.x - px.x, Resolution.y - px.y));
    float bw     = BORDER_PX * s;
    float frameM = 1.0 - smoothstep(bw - s, bw, edge);

    float2 gdir  = normalize(float2(1.0, -0.65));
    float  glare = exp(-sq(dot(toL, gdir) * 3.0));

    // ---- Poke Ball tiling (staggered rows) ----
    float2 g   = px / (TILE_PX * s);
    float  row = floor(g.y);
    g.x += 0.5 * (row - 2.0 * floor(row * 0.5));
    float2 id  = floor(g);
    float2 p   = frac(g) - 0.5;
    p.y = -p.y;
    float  aa  = fwidth(g.x) * 1.0;

    float r    = 0.33;
    float d    = length(p);
    float disc = fill(d - r, aa);
    float ring = fill(abs(d - r) - 0.022, aa);
    float gap  = smoothstep(0.125 - aa, 0.125 + aa, d);
    float band = fill(abs(p.y) - 0.038, aa) * disc * gap;
    float btnR = fill(abs(d - 0.090) - 0.020, aa);
    float btnD = fill(d - 0.040, aa);
    float top  = disc * smoothstep(-aa, aa, p.y - 0.04) * gap;
    float bot  = disc * smoothstep(-aa, aa, -p.y - 0.04) * gap;

    float lineArt = max(max(ring, band), max(btnR, btnD));
    float motif   = max(lineArt, max(top * 0.45, bot * 0.20));
    motif = max(motif, 0.06);

    float  tileSeed = hash21(id);
    float  hBase    = dot(uv, float2(0.40, 0.30)) + dot(toL, float2(0.45, -0.30)) + t * 0.06;
    // top half reflects more rainbow, bottom half stays silver
    float  rainbow  = lerp(0.35, 0.60, top) * (0.6 + 0.4 * glare);
    float3 foil     = silverFoil(hBase + tileSeed * 0.15 + p.y * 0.4, rainbow);
    float  grain    = vnoise(px / (1.5 * s));
    foil *= 0.65 + 0.40 * grain;
    foil  = foil * motif * (0.40 + 0.60 * glare) + lineArt * glare * 0.12;

    float2 q     = abs(tex - 0.5) * 2.0;
    float  shine = lerp(0.60, 1.0, smoothstep(0.55, 1.0, max(q.x, q.y)));

    float  amt   = STRENGTH * shine;
    float3 bgOut = c.rgb + foil * amt * (1.0 - c.rgb);
    float  shadow = exp(-sq((edge - bw - 2.0 * s) / (2.0 * s)));
    bgOut *= 1.0 - 0.45 * shadow;

    float3 textOut = lerp(c.rgb, silverFoil(hBase, 0.5), 0.05);
    float3 rgb = lerp(bgOut, textOut, textM);

    // ---- frame: polished silver with a rainbow sheen ----
    float  fh   = hBase * 1.5 + (px.x - px.y) / Resolution.y * 0.9 - t * 0.04;
    float3 fcol = silverFoil(fh, 0.45);
    float  fgr  = vnoise(px / (1.1 * s));
    fcol *= 0.48 + 0.18 * fgr + 0.40 * glare;
    float sweep = exp(-sq(frac((px.x + px.y) / (Resolution.x + Resolution.y) - t * 0.06) - 0.5) * 60.0);
    fcol += sweep * 0.22;
    float bevelIn  = exp(-sq((edge - (bw - 1.6 * s)) / (0.7 * s)));
    float bevelOut = smoothstep(0.0, 1.5 * s, edge);
    fcol += bevelIn * 0.45;
    fcol *= 0.35 + 0.65 * bevelOut;

    rgb = lerp(rgb, lerp(fcol, textOut, textM), frameM);
    return float4(saturate(rgb), 1.0);
}
