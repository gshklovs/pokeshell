// ============================================================================
// Skin: AMAZING RARE
// Imitates: Amazing Rare (Sword & Shield: Vivid Voltage era) - a splashy
//   rainbow burst exploding out of one corner of the card, with paint-splash
//   shaped bright regions over rainbow rays whose hue slowly rotates.
//
// Tuning:
//   STRENGTH   how strongly the foil shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling
//   ORIGIN     corner the burst radiates from, in 0..1 terminal coords
//              (0,1 = bottom-left, 1,0 = top-right)
// ============================================================================

#define STRENGTH  0.24
#define SPEED     1.0
#define BORDER_PX 12.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners (rounded was ~BORDER_PX * 1.2)
#define ORIGIN    float2(0.0, 1.0)
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

// 4-octave fractal noise, unrolled
float fbm(float2 p)
{
  float v = 0.5 * vnoise(p);
  p = p * 2.03 + float2(17.1, 3.7);
  v += 0.25 * vnoise(p);
  p = p * 2.01 + float2(5.3, 11.9);
  v += 0.125 * vnoise(p);
  p = p * 2.02 + float2(9.2, 1.4);
  v += 0.0625 * vnoise(p);
  return v / 0.9375;
}

float3 hue(float h)
{
  return saturate(abs(frac(h + float3(1.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0) - 1.0);
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

// ---- main ------------------------------------------------------------------

float4 main(float4 pos : SV_POSITION, float2 tex : TEXCOORD) : SV_TARGET
{
  float4 c = TermSample(tex);
  float2 px = tex * Resolution;
  float s = max(Scale, 0.5);
  float t = Time * SPEED;
  float aspect = Resolution.x / max(Resolution.y, 1.0);

  float2 light = float2(0.5 + 0.35 * sin(t * 0.21), 0.5 + 0.25 * cos(t * 0.17));
  float g = glare(tex, light, aspect, 2.2);

  float textMask = smoothstep(0.05, 0.12, distance(c.rgb, Background.rgb));

  // --- polar coords around the burst corner
  float2 d = (tex - ORIGIN) * float2(aspect, 1.0);
  float r = length(d);
  float rMax = length(float2(aspect, 1.0));
  float rn = saturate(r / rMax);                          // 0 at corner .. 1 far corner
  float ang = atan2(d.y, d.x);                            // radians

  // rays: angular streaks that stretch outward, drifting very slowly
  float ray = vnoise(float2(ang * 14.0, r * 1.2 - t * 0.04));
  ray = smoothstep(0.35, 0.85, ray);

  // paint splashes: domain-warped fbm thresholded into blobs; splashes are
  // denser near the burst corner and are pulled outward along the rays
  float2 sp = float2(ang * 2.2, r * 2.4 - t * 0.02);
  float warp = fbm(d * 2.0 + float2(t * 0.012, -t * 0.009));
  float field = fbm(sp * 1.6 + warp * 1.4) + 0.28 * (1.0 - rn) - 0.1;
  float splash = smoothstep(0.52, 0.58, field);
  float splashCore = smoothstep(0.62, 0.72, field);
  // tiny satellite droplets
  float drops = smoothstep(0.78, 0.82, fbm(d * 11.0 + 3.0)) * (1.0 - rn * 0.6);

  // hue: follows the angle (rainbow fan) + radius, rotates a full turn per ~20 s,
  // and shifts with the fake tilt
  float h = ang * 0.35 + r * 0.25 + t / 20.0 + (light.x - 0.5) * 0.5 + (light.y - 0.5) * 0.25;
  float3 burst = lerp(hue(h), float3(1.0, 1.0, 1.0), 0.18);
  float3 splashCol = lerp(hue(h + 0.12 + warp * 0.3), float3(1.0, 1.0, 1.0), 0.25);

  float falloff = 1.15 - 0.6 * rn;
  float intensity = (0.18 + 0.35 * ray) * falloff;
  float3 foil = burst * intensity * (0.6 + 0.6 * g);
  float spl = saturate(splash * 0.75 + splashCore * 0.35 + drops * 0.6);
  foil = lerp(foil, splashCol * (0.75 + 0.35 * g), spl);

  float amt = STRENGTH * (0.55 + 0.25 * g + 0.35 * spl);
  float3 bg = lerp(c.rgb, foil, amt);

  float3 txt = lerp(c.rgb, burst, TEXT_TINT);
  float3 rgb = lerp(bg, txt, textMask);

  // --- frame: vivid rainbow following the burst, splashes carry onto it ----
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float bevel = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 1.8 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 3.0 * s, edge - B)) * step(B, edge);

  float3 frameCol = lerp(hue(h + 0.05), float3(1.0, 1.0, 1.0), 0.22);
  frameCol *= 0.5 + 0.35 * sin(depth * 3.14159) + 0.3 * g + 0.25 * ray;
  frameCol = lerp(frameCol, splashCol, spl * 0.5);
  frameCol += bevel * 0.45 * float3(1.0, 1.0, 1.0);
  frameCol *= 1.0 - 0.45 * outerLine;

  rgb *= 1.0 - 0.35 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
