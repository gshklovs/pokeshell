// =====================================================================
// Skin: CROSSHATCH HOLO
// Imitates: the crosshatch holofoil used on Pokemon TCG holo rares of
//   the Sun & Moon / Sword & Shield era (and the "cross-hatch" promos):
//   two sets of fine diagonal lines crossing into a reflective diamond
//   grid; each line direction catches a different colour, and a
//   shimmer runs along the lines as the card tilts.
// On the terminal: a faint diamond lattice behind the text with slow
//   travelling glints; a gold crosshatched border frame.
// Tuning:
//   STRENGTH   background foil amount (0.15 - 0.35)
//   SPEED      animation speed multiplier
//   BORDER_PX  frame width in pixels at 100% DPI
//   HATCH_PX   line spacing in pixels at 100% DPI
// =====================================================================
#define STRENGTH  0.26
#define SPEED     1.0
#define BORDER_PX 12.0
#define HATCH_PX  8.0

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

// anti-aliased thin line at every integer + 0.5 of u; hw = half width in cells
float hatch(float u, float hw)
{
    float d  = abs(frac(u) - 0.5);
    float aa = fwidth(u) * 1.2;
    return 1.0 - smoothstep(hw, hw + aa, d);
}

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

    // ---- background crosshatch ----
    float sp = HATCH_PX * s * 1.41421;
    float u1 = (px.x + px.y) / sp;          // lines of set 1 run along u2
    float u2 = (px.x - px.y) / sp;          // lines of set 2 run along u1
    float l1 = hatch(u1, 0.07);
    float l2 = hatch(u2, 0.07);

    // each direction reflects its own hue; hue depends on the fake tilt
    float  h  = dot(uv, float2(0.35, 0.25)) + t * 0.05;
    float3 c1 = spectrum(h + dot(toL, float2(0.6, 0.6)));
    float3 c2 = spectrum(h + 0.33 + dot(toL, float2(0.6, -0.6)));

    // glints travelling slowly along each set of lines (~7-9 s period)
    float w1 = 0.35 + 0.65 * sq(0.5 + 0.5 * sin(u2 * 0.30 - t * 0.85));
    float w2 = 0.35 + 0.65 * sq(0.5 + 0.5 * sin(u1 * 0.27 + t * 0.70));

    float  grain = vnoise(px / (2.0 * s));
    float3 sheen = spectrum(h * 1.3 - 0.1) * (0.20 + 0.15 * grain);   // faint base between lines
    float3 foil  = sheen + l1 * c1 * w1 + l2 * c2 * w2 + l1 * l2 * (0.5 + 0.8 * glare);
    foil *= 0.40 + 0.60 * glare;
    foil += glare * 0.08;

    float  amt   = STRENGTH;
    float3 bgOut = c.rgb + foil * amt * (1.0 - c.rgb);
    float  shadow = exp(-sq((edge - bw - 2.0 * s) / (2.0 * s)));
    bgOut *= 1.0 - 0.45 * shadow;

    float3 textOut = lerp(c.rgb, c1, 0.05);
    float3 rgb = lerp(bgOut, textOut, textM);

    // ---- frame: gold with a finer crosshatch ----
    float fsp = 3.5 * s * 1.41421;
    float f1  = hatch((px.x + px.y) / fsp, 0.12);
    float f2  = hatch((px.x - px.y) / fsp, 0.12);
    float3 gold = float3(0.86, 0.68, 0.30);
    float  fh   = h * 2.0 + (px.x - px.y) / Resolution.y * 0.7;
    float3 fcol = gold * (0.55 + 0.35 * glare);
    fcol += (f1 * spectrum(fh) + f2 * spectrum(fh + 0.4)) * (0.18 + 0.30 * glare);
    fcol += f1 * f2 * 0.25;
    float sweep = exp(-sq(frac((px.x + px.y) / (Resolution.x + Resolution.y) - t * 0.06) - 0.5) * 60.0);
    fcol += sweep * float3(0.25, 0.20, 0.10);
    float bevelIn  = exp(-sq((edge - (bw - 1.6 * s)) / (0.7 * s)));
    float bevelOut = smoothstep(0.0, 1.5 * s, edge);
    fcol += bevelIn * float3(0.45, 0.40, 0.25);
    fcol *= 0.35 + 0.65 * bevelOut;

    rgb = lerp(rgb, lerp(fcol, textOut, textM), frameM);
    return float4(saturate(rgb), 1.0);
}
