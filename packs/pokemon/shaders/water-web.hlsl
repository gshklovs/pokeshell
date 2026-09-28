// =====================================================================
//  Skin: WATER WEB
//  Imitates: the Sun & Moon era "water web" holofoil -- a mesh of wavy,
//  rippling interference lines, like sunlight caustics on a pool floor,
//  with rainbow colour flowing along the web as the card tilts.
//  Windows Terminal pixel shader (ps_4_0).
//
//  Tuning:
//    STRENGTH  - how strongly the foil shows on background pixels (0.15-0.35)
//    SPEED     - global motion speed multiplier (1.0 = slow, 0.5 = slower)
//    BORDER_PX - card frame width in pixels (at 100% DPI)
//    WEB_PX    - size of the web cells in pixels
// =====================================================================

#define STRENGTH  0.27
#define SPEED     1.0
#define BORDER_PX 12.0
#define WEB_PX    64.0

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
float3 rainbow(float h)
{
  return 0.5 + 0.5 * cos(6.28318 * (h + float3(0.0, 0.333, 0.667)));
}

float edgeDist(float2 px)
{
  return min(min(px.x, px.y), min(Resolution.x - px.x, Resolution.y - px.y));
}

// thin anti-aliased line where f crosses zero (width ~ w pixels)
float zline(float f, float w)
{
  float fw = fwidth(f) + 1e-4;
  return saturate(1.0 - abs(f) / (fw * w));
}

// Three wavy line families crossing each other -> a rippling web.
// .x = sharp web lines, .y = soft glow around them, .z = caustic cell brightness
float3 web(float2 q, float tt)
{
  // slow domain warp = water surface
  q += 0.45 * float2(sin(q.y * 0.9 + tt), sin(q.x * 0.8 - tt * 0.8));
  q += 0.20 * float2(sin(q.y * 2.1 - tt * 0.6), sin(q.x * 1.9 + tt * 0.7));

  float f1 = sin(q.x * 1.6 + 1.3 * sin(q.y * 0.9 + tt));
  float f2 = sin(q.y * 1.8 + 1.3 * sin(q.x * 1.1 - tt * 0.7));
  float f3 = sin((q.x + q.y) * 1.2 + 1.1 * sin((q.x - q.y) * 0.8 + tt * 0.6));

  float lines = max(max(zline(f1, 1.3), zline(f2, 1.3)), zline(f3, 1.1) * 0.8);
  float glow = saturate(1.0 - abs(f1) * 3.0) + saturate(1.0 - abs(f2) * 3.0)
             + 0.8 * saturate(1.0 - abs(f3) * 3.0);
  float caustic = 0.5 + 0.5 * f1 * f2;
  return float3(lines, glow * 0.33, caustic);
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
  float glare = exp(-dot(dd, dd) * 4.5);
  float tt = t * 0.25;

  // ---- background foil
  float3 w = web(px / (WEB_PX * s), tt);
  float hue = dot(tex - light, float2(0.8, 0.6)) * 0.9 + w.z * 0.25 + t * 0.015;
  float3 col = rainbow(hue);
  float3 foil = col * (0.12 + 0.35 * w.y + 0.75 * w.x) * (0.55 + 0.45 * glare)
              + w.x * glare * 0.25 + col * w.z * 0.08;
  foil = saturate(foil);

  // ---- frame: silver-blue edge with a finer ripple web
  float bw = BORDER_PX * s;
  float d = edgeDist(px);
  float frameMask = 1.0 - smoothstep(bw - 0.75 * s, bw + 0.25 * s, d);
  float bevelT = saturate(d / bw);
  float prof = 0.6 + 0.4 * sin(bevelT * 3.14159);

  float3 fw = web(px / (18.0 * s), tt * 1.3);
  float3 silver = float3(0.70, 0.76, 0.84);
  float3 frameCol = silver * prof * (0.6 + 0.25 * fw.z + 0.2 * fw.y)
                  + rainbow(hue + 0.2) * fw.x * 0.35
                  + glare * 0.15;
  float hiLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(d - (bw - 2.0 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(d - 0.5 * s));
  frameCol += hiLine * 0.35 - outerLine * 0.25;
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
