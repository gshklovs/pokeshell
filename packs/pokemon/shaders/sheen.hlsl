// =====================================================================
//  Skin: SHEEN
//  Imitates: the XY era "sheen" holofoil -- a smooth, glossy surface with
//  broad diagonal bands of rainbow light that slide slowly across the
//  card as it tilts, plus one soft white glare stripe.
//  Windows Terminal pixel shader (ps_4_0).
//
//  Tuning:
//    STRENGTH  - how strongly the foil shows on background pixels (0.15-0.35)
//    SPEED     - global motion speed multiplier (1.0 = slow, 0.5 = slower)
//    BORDER_PX - card frame width in pixels (at 100% DPI)
//    BANDS     - how many rainbow bands span the diagonal
// =====================================================================

#define STRENGTH  0.24
#define SPEED     1.0
#define BORDER_PX 12.0
#define BANDS     1.6

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

float3 rainbow(float h)
{
  return 0.5 + 0.5 * cos(6.28318 * (h + float3(0.0, 0.333, 0.667)));
}

float edgeDist(float2 px)
{
  return min(min(px.x, px.y), min(Resolution.x - px.x, Resolution.y - px.y));
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

  // diagonal coordinate (aspect-corrected, normalised to ~0..1 across the card)
  float2 q = float2(tex.x * aspect, tex.y);
  float2 dir = normalize(float2(1.0, 0.75));
  float span = dot(float2(aspect, 1.0), dir);
  float diag = dot(q, dir) / span;
  float lightDiag = dot(float2(light.x * aspect, light.y), dir) / span;

  // gentle large-scale warp so bands are not ruler-straight (glossy film)
  float warp = (vnoise(px / (260.0 * s) + t * 0.01) - 0.5) * 0.08;

  // ---- background foil: broad rainbow bands
  float bandCoord = (diag + warp) * BANDS - t * 0.035 - lightDiag * 0.9;
  float bands = 0.5 + 0.5 * cos(6.28318 * bandCoord);
  bands = bands * bands * (3.0 - 2.0 * bands);
  float hue = (diag + warp) * 0.9 - t * 0.02 + lightDiag * 0.7;
  float3 col = rainbow(hue);
  float g = (diag - lightDiag) * 3.2;
  float glare = exp(-g * g);
  float grain = (vnoise(px / (2.5 * s)) - 0.5) * 0.06;     // faint gloss grain
  float3 foil = col * (0.25 + 0.75 * bands) * (0.6 + 0.4 * glare) + glare * 0.28 + grain;
  foil = saturate(foil);

  // ---- frame: polished gold with a sliding highlight
  float bw = BORDER_PX * s;
  float d = edgeDist(px);
  float frameMask = 1.0 - smoothstep(bw - 0.75 * s, bw + 0.25 * s, d);
  float bevelT = saturate(d / bw);
  float prof = 0.55 + 0.45 * sin(bevelT * 3.14159);

  float3 gold = float3(0.88, 0.70, 0.30);
  float fg = (diag - lightDiag) * 7.0;
  float sweep = exp(-fg * fg);
  float3 frameCol = gold * prof * (0.65 + 0.35 * bands)
                  + col * bands * 0.18
                  + sweep * float3(0.45, 0.42, 0.35);
  float hiLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(d - (bw - 2.0 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(d - 0.5 * s));
  frameCol += hiLine * float3(0.4, 0.34, 0.2) - outerLine * 0.25;
  frameCol = saturate(frameCol);
  float shadow = (1.0 - smoothstep(0.0, 2.0 * s, abs(d - (bw + 1.5 * s)))) * (1.0 - frameMask);

  // ---- composite
  float3 surface = lerp(c.rgb, foil, STRENGTH);
  surface *= 1.0 - 0.45 * shadow;
  surface = lerp(surface, frameCol, frameMask);

  float textMask = smoothstep(0.04, 0.12, distance(c.rgb, Background.rgb));
  float3 textCol = lerp(c.rgb, col, 0.05);
  float3 rgb = lerp(surface, textCol, textMask);
  return float4(rgb, 1.0);
}
