// ============================================================================
// Skin: GOLD
// Imitates: Gold secret rare (Sun & Moon hyper rares onward, Sword & Shield /
//   Scarlet & Violet gold cards) - warm gold metal with fine etched texture
//   lines and a glossy highlight that slides across as the card tilts,
//   inside a heavy gold frame.
//
// Tuning:
//   STRENGTH   how strongly the gold shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling (gold gets a heavy frame)
//   ETCH_PX    period of the etched lines in pixels
// ============================================================================

#define STRENGTH  0.22
#define SPEED     1.0
#define BORDER_PX 16.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners (rounded was ~BORDER_PX * 1.2)
#define ETCH_PX   3.0
#define TEXT_TINT 0.06

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

float glare(float2 uv, float2 light, float aspect, float k)
{
  float2 d = (uv - light) * float2(aspect, 1.0);
  return exp(-dot(d, d) * k);
}

float cardEdge(float2 px, float radius)
{
  float2 h = Resolution * 0.5;
  float2 q = abs(px - h) - (h - radius);
  float sd = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;
  return -sd;
}

// dark bronze -> gold -> pale champagne, x in 0..1
float3 goldRamp(float x)
{
  float3 dark   = float3(0.32, 0.20, 0.05);
  float3 mid    = float3(0.86, 0.62, 0.22);
  float3 bright = float3(1.00, 0.93, 0.66);
  float3 col = lerp(dark, mid, saturate(x * 1.7));
  return lerp(col, bright, saturate(x * 1.7 - 0.7));
}

// ---- main ------------------------------------------------------------------

float4 main(float4 pos : SV_POSITION, float2 tex : TEXCOORD) : SV_TARGET
{
  float4 c = TermSample(tex);
  float2 px = tex * Resolution;
  float s = max(Scale, 0.5);
  float t = Time * SPEED;
  float aspect = Resolution.x / max(Resolution.y, 1.0);
  float2 uvA = tex * float2(aspect, 1.0);

  float2 light = float2(0.5 + 0.35 * sin(t * 0.21), 0.5 + 0.25 * cos(t * 0.17));
  float g = glare(tex, light, aspect, 2.0);

  float textMask = smoothstep(0.05, 0.12, distance(c.rgb, Background.rgb));

  // --- etched texture: fine parallel lines whose direction flips between
  //     noise patches, like the engraved pattern on gold cards
  float2 p = px / s;
  float w = 6.28318 / ETCH_PX;
  float lA = 0.5 + 0.5 * sin(dot(p, float2(0.866, 0.5)) * w);
  float lB = 0.5 + 0.5 * sin(dot(p, float2(-0.5, 0.866)) * w);
  float patchN = vnoise(uvA * 7.0) * 0.7 + vnoise(uvA * 19.0) * 0.3;
  float patchSel = smoothstep(0.46, 0.54, patchN);
  float etch = lerp(lA, lB, patchSel);
  // engraved outline where patches meet
  float seam = 1.0 - smoothstep(0.0, 0.035, abs(patchN - 0.5));

  // --- metal reflection: broad bands that roll with the light (brushed look)
  float refl = 0.5 + 0.5 * sin((uvA.x * 0.8 + tex.y * 1.3) * 3.0
                               - (light.x * 2.0 + light.y) * 3.0);
  refl = saturate(refl * 0.8 + g * 0.35);
  float3 goldCol = goldRamp(refl);

  // --- glossy highlight: a narrow diagonal band passing through the light
  float2 dir = normalize(float2(1.0, -0.6));
  float bd = dot((tex - light) * float2(aspect, 1.0), dir);
  float band = exp(-bd * bd * 22.0);

  float3 foil = goldCol * (0.55 + 0.45 * etch) * (1.0 - 0.35 * seam)
              + float3(1.0, 0.92, 0.7) * band * 0.55;
  float amt = STRENGTH * (0.5 + 0.3 * g + 0.4 * band);
  float3 bg = lerp(c.rgb, foil, amt);

  float3 txt = lerp(c.rgb, goldCol, TEXT_TINT);
  float3 rgb = lerp(bg, txt, textMask);

  // --- heavy gold frame -------------------------------------------------
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  // two raised bevel ridges plus a dark outer lip
  float bevel1 = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - 3.0 * s));
  float bevel2 = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 2.0 * s)));
  float groove = 1.0 - smoothstep(0.0, 1.3 * s, abs(edge - B * 0.55));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 4.0 * s, edge - B)) * step(B, edge);

  // rounded bar profile: bright crest, darker edges, rolling with the light
  float crest = sin(depth * 3.14159);
  float fRefl = saturate(0.25 + 0.55 * crest + 0.45 * g + 0.3 * band
                         + 0.15 * sin((tex.x * aspect + tex.y) * 4.0 - t * 0.4));
  float3 frameCol = goldRamp(fRefl) * (0.8 + 0.2 * etch);
  frameCol += float3(1.0, 0.95, 0.75) * (bevel1 + bevel2) * 0.4;
  frameCol *= 1.0 - 0.45 * groove;
  frameCol *= 1.0 - 0.5 * outerLine;

  rgb *= 1.0 - 0.4 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.012, 0.01, 0.006), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
