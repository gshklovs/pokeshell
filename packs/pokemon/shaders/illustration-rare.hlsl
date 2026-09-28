// =====================================================================
// Skin: ILLUSTRATION RARE (etched texture)
// Imitates: the Scarlet & Violet Illustration Rare / Special
//   Illustration Rare finish: full-art cards with a fine, swirling,
//   fingerprint-like etched texture that only catches the light at
//   certain angles, plus a soft pearlescent sheen. Classy, understated.
// On the terminal: static etched ridges whose highlights slide slowly
//   with the fake light; sparse, gently twinkling specks; a pearl-silver
//   etched frame.
// Tuning:
//   STRENGTH   background foil amount (0.10 - 0.30; keep it low)
//   SPEED      animation speed multiplier
//   BORDER_PX  frame width in pixels at 100% DPI
//   RIDGES     ridge density of the fingerprint etch
// =====================================================================
#define STRENGTH  0.20
#define SPEED     1.0
#define BORDER_PX 12.0
#define RIDGES    120.0

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
static const float2x2 ROT = float2x2(0.80, 0.60, -0.60, 0.80);

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

float fbm(float2 p)
{
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < 4; i++)
    {
        v += a * vnoise(p);
        p = mul(ROT, p) * 2.03 + 17.1;
        a *= 0.5;
    }
    return v;
}

float3 spectrum(float h)
{
    return 0.5 + 0.5 * cos(TAU * (h + float3(0.0, 0.33, 0.67)));
}

// soft pearl: mostly white with a pastel rainbow
float3 pearl(float h) { return lerp(float3(0.86, 0.86, 0.90), spectrum(h), 0.35); }

// swirling fingerprint field (static; etched into the card)
float etchField(float2 q)
{
    float2 w = float2(fbm(q + float2(0.0, 0.0)), fbm(q + float2(5.2, 1.3)));
    return fbm(q + 1.8 * w);
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
    float  glare = exp(-sq(dot(toL, gdir) * 2.6));

    // ---- etched ridges ----
    // scale the field in physical pixels so ridge spacing is DPI-stable
    float2 q  = px / (520.0 * s);
    float  f  = etchField(q);
    float  k  = f * RIDGES;
    float  kw = fwidth(k);
    float  ridge = sq(0.5 + 0.5 * cos(k * TAU));
    ridge = lerp(0.25, ridge, saturate(1.5 - kw * 2.0));      // fade to average if too dense

    // a ridge "catches" light depending on its slope vs. the light direction
    float2 grad  = float2(ddx(f), ddy(f));
    float2 n     = grad / (length(grad) + 1e-5);
    float2 ldir  = normalize(float2(sin(t * 0.23), cos(t * 0.19)) + 1e-4);
    float  catchL = sq(dot(n, ldir));
    float  etch  = ridge * (0.25 + 0.75 * catchL);

    float  h    = f * 2.5 + dot(toL, float2(0.35, -0.25)) + t * 0.04;
    float3 foil = pearl(h) * etch * (0.30 + 0.70 * glare);
    foil += pearl(h + 0.3) * glare * 0.06;                     // soft sheen

    // sparse, slow twinkling specks (period ~4-9 s)
    float2 sc   = px / (14.0 * s);
    float2 sid  = floor(sc);
    float  sh   = hash21(sid + 3.7);
    float2 sp   = frac(sc) - 0.5 - (float2(hash21(sid + 1.1), hash21(sid + 2.3)) - 0.5) * 0.6;
    float  star = exp(-dot(sp, sp) * 180.0) * step(0.94, sh);
    float  tw   = sq(0.5 + 0.5 * sin(t * (0.7 + sh * 0.7) + sh * TAU));
    foil += star * tw * (0.4 + 0.8 * glare) * float3(0.95, 0.95, 1.0);

    float  amt   = STRENGTH;
    float3 bgOut = c.rgb + foil * amt * (1.0 - c.rgb);
    float  shadow = exp(-sq((edge - bw - 2.0 * s) / (2.0 * s)));
    bgOut *= 1.0 - 0.40 * shadow;

    float3 textOut = lerp(c.rgb, pearl(h), 0.04);
    float3 rgb = lerp(bgOut, textOut, textM);

    // ---- frame: pearl silver with a finer etch ----
    float  ff   = etchField(px / (160.0 * s));
    float  fr   = sq(0.5 + 0.5 * cos(ff * RIDGES * TAU));
    fr = lerp(0.3, fr, saturate(1.5 - fwidth(ff * RIDGES) * 2.0));
    float3 fcol = pearl(h * 1.3 + (px.x - px.y) / Resolution.y * 0.6);
    fcol *= 0.42 + 0.18 * fr + 0.35 * glare;
    float sweep = exp(-sq(frac((px.x + px.y) / (Resolution.x + Resolution.y) - t * 0.05) - 0.5) * 60.0);
    fcol += sweep * 0.15;
    float bevelIn  = exp(-sq((edge - (bw - 1.6 * s)) / (0.7 * s)));
    float bevelOut = smoothstep(0.0, 1.5 * s, edge);
    fcol += bevelIn * 0.40;
    fcol *= 0.35 + 0.65 * bevelOut;

    rgb = lerp(rgb, lerp(fcol, textOut, textM), frameM);
    return float4(saturate(rgb), 1.0);
}
