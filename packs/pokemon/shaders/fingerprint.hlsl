// ============================================================================
// Skin: FINGERPRINT
// Imitates: the Sword & Shield Rare Ultra full art (Evolving Skies Glaceon V
//   174) - the whole card is etched with fingerprint-like whorl lines, and
//   under a raking light they light up in a slow rainbow wave that runs
//   outward along the contours. No beam. The pokeshell Rare Ultra card
//   animation, with the etched whorls carried onto a silver full-art frame.
//
// Tuning:
//   STRENGTH   how strongly the lit etch shows through the background (0.15-0.4)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling
//   LINE_PX    spacing of the etched whorl lines in pixels
//   WAVE_S     seconds for one rainbow wave to travel its spacing
// ============================================================================

#define STRENGTH  0.30
#define SPEED     1.0
#define BORDER_PX 12.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners
#define LINE_PX   9.0
#define WAVE_S    16.0
#define TEXT_TINT 0.04

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

// the fingerprint field: weighted distance to three whorl centres, bent by slow waves (px units)
float whorl(float2 p, float2 res)
{
  float2 c1 = res * float2(0.28, 0.32);
  float2 c2 = res * float2(0.76, 0.62);
  float2 c3 = res * float2(0.50, 1.15);
  float f = 1.0 * length((p - c1) * float2(1.0, 1.15))
          + 0.8 * length((p - c2) * float2(1.0, 1.15))
          + 0.5 * length((p - c3) * float2(1.0, 1.15));
  f /= 2.3;
  f += 16.0 * sin(p.x / 70.0) * cos(p.y / 90.0) + 8.0 * sin((p.x + p.y) / 48.0);
  return f;
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

  float textMask = smoothstep(0.05, 0.12, distance(c.rgb, Background.rgb));

  // --- the etched whorl lines (1-px-ish, even width via fwidth)
  float f = whorl(p, res) / LINE_PX;
  float ld = abs(frac(f + 0.5) - 0.5) / max(fwidth(f), 1e-4);      // 0 on a line
  float eline = 1.0 - smoothstep(0.6, 1.6, ld);
  float idx = floor(f + 0.5);                                // contour index

  // --- the rainbow wave: fronts travel outward over the contour index, one every 40 lines
  float dd = frac((idx - t / WAVE_S * 40.0) / 40.0) - 0.5;  // -0.5..0.5 contour spacings
  float k = exp(-(dd * 40.0 / 4.5) * (dd * 40.0 / 4.5));    // lit lines near the front, soft trail
  float3 wave = pastel(idx / 14.0 - t / 30.0, 0.3);

  // a dim silver etch everywhere, the wave lights lines strongly and the gaps a little
  float3 foil = float3(0.55, 0.58, 0.66) * 0.18 + wave * 0.12 * k;
  foil = lerp(foil, lerp(float3(0.5, 0.52, 0.6) * 0.5, wave, k), eline);
  float amt = STRENGTH * (0.35 + 0.65 * k) * lerp(0.45, 1.0, eline);
  float3 bg = lerp(c.rgb, foil, amt);

  float3 txt = lerp(c.rgb, wave, TEXT_TINT * k);
  float3 rgb = lerp(bg, txt, textMask);

  // --- silver full-art frame, the same whorls etched in it -------------------
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float bevel = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 1.8 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 3.0 * s, edge - B)) * step(B, edge);

  float3 frameCol = float3(0.78, 0.79, 0.86) * (0.55 + 0.3 * sin(depth * 3.14159));
  frameCol = lerp(frameCol, wave, 0.25 + 0.45 * k * eline);
  frameCol *= 0.85 + 0.2 * eline;
  frameCol += bevel * 0.4 * float3(1.0, 1.0, 1.0);
  frameCol *= 1.0 - 0.45 * outerLine;

  rgb *= 1.0 - 0.35 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
