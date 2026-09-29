// ============================================================================
// Skin: FIREWORKS
// Imitates: the 30th Celebration Pikachu Rare (Pikachu 23) - a yellow bevel
//   border and a fireworks foil: a staggered lattice of little bursts over
//   the art and the border that go off in turn (spark, burst, full bloom,
//   fade), each its own colour, while a soft vertical light bar sweeps
//   across. The pokeshell Pikachu Rare card animation.
//
// Tuning:
//   STRENGTH   how strongly the bursts show through the background (0.15-0.4)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling
//   CELL_PX    spacing of the firework lattice in pixels
//   LIFE_S     seconds between two launches of the same burst
// ============================================================================

#define STRENGTH  0.34
#define SPEED     1.0
#define BORDER_PX 12.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners
#define CELL_PX   120.0
#define LIFE_S    7.0
#define BAR_S     9.0
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

float hash21(float2 p)
{
  p = frac(p * float2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return frac(p.x * p.y);
}

float3 hue(float h)
{
  return saturate(abs(frac(h + float3(1.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0) - 1.0);
}

float cardEdge(float2 px, float radius)
{
  float2 h = Resolution * 0.5;
  float2 q = abs(px - h) - (h - radius);
  float sd = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;
  return -sd;
}

// the burst in this pixel's lattice cell: rgb light (already coloured)
float3 burst(float2 p, float t)
{
  float cy = CELL_PX * 0.8;
  float j = floor(p.y / cy);
  float off = frac(j * 0.5) * CELL_PX;                 // odd rows shifted half a cell (staggered)
  float i = floor((p.x - off) / CELL_PX);
  float2 id = float2(i, j);
  float2 ctr = float2((i + 0.5) * CELL_PX + off, (j + 0.5) * cy)
             + (float2(hash21(id), hash21(id + 4.1)) - 0.5) * CELL_PX * 0.2;
  float2 d = p - ctr;
  float r = length(d);

  // launch order: golden-ratio phases, so neighbours go off one after another
  float ph = frac((i * 3.0 + j * 7.0) * 0.618 + 0.15 * hash21(id + 9.0));
  float u = frac(t / LIFE_S + ph);                     // 0..1 over one life
  float live = step(u, 0.55);
  float grow = saturate(u / 0.3);
  grow = 1.0 - (1.0 - grow) * (1.0 - grow);            // ease-out: fast launch, slow bloom
  float fade = 1.0 - smoothstep(0.3, 0.55, u);
  float R = CELL_PX * 0.36 * grow;

  float a = atan2(d.y, d.x + 1e-4);
  float rays = pow(abs(cos(a * 4.0)), 24.0);           // 8 long rays
  float rays2 = pow(abs(cos(a * 4.0 + 0.785)), 24.0);  // 8 short diagonal ones
  float tip = exp(-(r - R) * (r - R) / 10.0);
  float tip2 = exp(-(r - R * 0.6) * (r - R * 0.6) / 8.0);
  float trail = smoothstep(R * 0.3, R, r) * step(r, R) * 0.35;
  float core = exp(-r * r / 12.0) * (1.0 - smoothstep(0.0, 0.25, u)) * 1.5;   // the launch spark
  float glow = exp(-r * r / (R * R * 0.25 + 1.0)) * 0.12;

  float k = (rays * (tip + trail) + rays2 * tip2 * 0.8 + core + glow) * fade * live;
  float3 col = lerp(hue(hash21(id + 2.2)), float3(1.0, 1.0, 1.0), 0.3);
  return col * k;
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

  float3 fw = burst(p, t);

  // --- the soft vertical light bar sweeping left to right, faintly rainbow
  float bx = -0.1 * res.x + frac(t / BAR_S) * 1.2 * res.x;
  float bar = exp(-(p.x - bx) * (p.x - bx) / (res.x * res.x * 0.004));
  float3 barCol = lerp(hue(p.x / res.x * 1.5 + t / 20.0), float3(1.0, 1.0, 1.0), 0.5);

  float3 ground = float3(0.9, 0.78, 0.35) * 0.05;       // a warm hint of the yellow card
  float3 bg = c.rgb + ground * STRENGTH + fw * STRENGTH;
  bg = lerp(bg, barCol, 0.08 * bar);

  float3 txt = lerp(c.rgb, barCol, TEXT_TINT * bar);
  float3 rgb = lerp(bg, txt, textMask);

  // --- yellow bevel border (light / mid / dark), with bursts over it too ------
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 3.0 * s, edge - B)) * step(B, edge);

  float3 yLight = float3(1.0, 0.953, 0.690);
  float3 yMid   = float3(0.965, 0.816, 0.173);
  float3 yDark  = float3(0.722, 0.549, 0.078);
  // bevel profile: dark outer lip -> mid body -> light ridge -> dark inner step
  float3 frameCol = lerp(yDark, yMid, smoothstep(0.05, 0.3, depth));
  frameCol = lerp(frameCol, yLight, smoothstep(0.45, 0.7, depth) * (1.0 - smoothstep(0.75, 0.88, depth)));
  frameCol = lerp(frameCol, yDark, smoothstep(0.88, 1.0, depth));
  frameCol *= 0.8 + 0.2 * bar;
  frameCol = lerp(frameCol, float3(1.0, 1.0, 1.0), saturate(dot(fw, float3(0.33, 0.33, 0.33))) * 0.35);
  frameCol += fw * 0.25;
  frameCol *= 1.0 - 0.45 * outerLine;

  rgb *= 1.0 - 0.35 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.012, 0.01, 0.006), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
