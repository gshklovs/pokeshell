// ============================================================================
// Skin: RAINBOW RARE
// Imitates: Sword & Shield / Scarlet & Violet era Rainbow Rare (secret rare)
//   full-art cards - a pastel rainbow wash over the whole card with a fine
//   glitter texture, and a matching rainbow edge.
//
// Tuning:
//   STRENGTH   how strongly the foil shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier (0.5 = calmer, 1.5 = livelier)
//   BORDER_PX  frame width in pixels at 100% scaling
//   GLITTER    glitter sparkle intensity (0 = off)
// ============================================================================

#define STRENGTH  0.24
#define SPEED     1.0
#define BORDER_PX 12.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners (rounded was ~BORDER_PX * 1.2)
#define GLITTER   0.8
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

// fully saturated rainbow, h wraps every 1.0
float3 hue(float h)
{
  return saturate(abs(frac(h + float3(1.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0) - 1.0);
}

// soft round glare centred on the moving light
float glare(float2 uv, float2 light, float aspect, float k)
{
  float2 d = (uv - light) * float2(aspect, 1.0);
  return exp(-dot(d, d) * k);
}

// signed distance inward from a rounded-rect card edge (px); <0 = outside the card
float cardEdge(float2 px, float radius)
{
  float2 h = Resolution * 0.5;
  float2 q = abs(px - h) - (h - radius);
  float sd = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;
  return -sd;
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

  // slowly wandering "light" = fake card tilt
  float2 light = float2(0.5 + 0.35 * sin(t * 0.21), 0.5 + 0.25 * cos(t * 0.17));
  float g = glare(tex, light, aspect, 2.5);

  // text detection: anything that differs from the background colour
  float textMask = smoothstep(0.05, 0.12, distance(c.rgb, Background.rgb));

  // --- pastel rainbow wash: diagonal gradient, hue slides with the light and
  //     drifts one full cycle every ~16 s
  float h = dot(uvA, float2(0.22, 0.35))
          + (light.x - 0.5) * 0.6 + (light.y - 0.5) * 0.3
          + t / 16.0
          + 0.05 * vnoise(uvA * 3.0 + t * 0.05);
  float3 pastel = lerp(hue(h), float3(1.0, 1.0, 1.0), 0.42);

  // --- fine glitter: 2px cells, ~12% lit, each twinkling slowly (<0.25 Hz)
  float2 gcell = floor(px / (2.0 * s));
  float gh = hash21(gcell);
  float twinkle = 0.5 + 0.5 * sin(t * 1.3 + gh * 40.0);
  float glit = smoothstep(0.88, 1.0, gh) * twinkle * twinkle;
  float3 glitCol = lerp(hue(h + gh * 0.35), float3(1.0, 1.0, 1.0), 0.3);

  // soft grain so the wash is not perfectly smooth
  float grain = 0.85 + 0.15 * vnoise(px / (3.0 * s));

  float3 foil = pastel * (0.35 + 0.65 * g) * grain;
  float amt = STRENGTH * (0.55 + 0.45 * g);
  float3 bg = lerp(c.rgb, foil, amt) + glitCol * glit * GLITTER * 0.22 * (0.35 + 0.65 * g);

  // text keeps its colour, only a whisper of foil tint
  float3 txt = lerp(c.rgb, pastel, TEXT_TINT);
  float3 rgb = lerp(bg, txt, textMask);

  // --- card frame --------------------------------------------------------
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);                         // 0 outer .. 1 inner
  float bevel = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 1.8 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 3.0 * s, edge - B)) * step(B, edge);

  float h2 = (tex.x * aspect + tex.y) * 0.45 + (light.x - 0.5) * 0.8 + t / 12.0;
  float3 frameCol = lerp(hue(h2), float3(1.0, 1.0, 1.0), 0.3);
  frameCol *= 0.55 + 0.35 * sin(depth * 3.14159) + 0.35 * g;   // rounded metal profile
  frameCol += glitCol * glit * 0.5;
  frameCol += bevel * 0.45 * float3(1.0, 1.0, 1.0);
  frameCol *= 1.0 - 0.45 * outerLine;

  rgb *= 1.0 - 0.35 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
