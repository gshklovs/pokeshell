// ============================================================================
// Skin: GX WEB
// Imitates: the Sun & Moon Rare Holo GX (Hidden Fates Charizard-GX 9) - a
//   silver GX frame and the GX holo's cracked "water-web" of foil lines over
//   the art, each web cell with a faint rainbow of its own; a soft rainbow
//   sheen sweeps the card (steeper than the V beam) and the web lines light
//   up in rainbow as it passes, a faint counter-sheen follows. The pokeshell
//   Rare Holo GX card animation.
//
// Tuning:
//   STRENGTH   how strongly the foil shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling
//   SWEEP_S    seconds for the sheen to cross the terminal once
//   CELL_PX    size of a web cell in pixels at 100% scaling
// ============================================================================

#define STRENGTH  0.25
#define SPEED     1.0
#define BORDER_PX 12.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners
#define SWEEP_S   14.0
#define CELL_PX   30.0
#define TEXT_TINT 0.05

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

float2 hash22(float2 p)
{
  float3 p3 = frac(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
  p3 += dot(p3, p3.yzx + 33.33);
  return frac((p3.xx + p3.yz) * p3.zy);
}

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

// the web: distance to the border between the two nearest jittered cell points (3x3 search).
// returns (border distance in px, hue of the nearest cell)
float2 web(float2 p, float cell)
{
  float2 g = floor(p / cell);
  float d1 = 1e5, d2 = 1e5;
  float2 c1 = 0.0;
  for (int j = -1; j <= 1; j++)
  {
    for (int i = -1; i <= 1; i++)
    {
      float2 id = g + float2(i, j);
      float2 c = (id + 0.2 + 0.6 * hash22(id)) * cell;
      float d = distance(p, c);
      if (d < d1) { d2 = d1; d1 = d; c1 = c; }
      else if (d < d2) { d2 = d; }
    }
  }
  return float2(d2 - d1, (c1.x * 0.9 + c1.y * 0.5) / (cell * 9.0));
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
  float span = res.x * 0.8 + res.y;

  float textMask = smoothstep(0.05, 0.12, distance(c.rgb, Background.rgb));

  // --- the sheen: runs along 0.8x + y = const, a fainter counter-sheen the other way
  float band = 0.14 * span;
  float ph = frac(t / SWEEP_S);
  float u = ((p.x * 0.8 + p.y) - (-band + ph * (span + 2.0 * band))) / band;
  float k = exp(-u * u * 2.6);
  float u2 = ((p.x - p.y * 0.6) - (res.x - ph * (res.x + res.y * 0.6))) / (band * 0.8);
  float k2 = exp(-u2 * u2) * 0.35;

  // --- the GX web
  float2 w = web(p, CELL_PX);
  float wline = 1.0 - smoothstep(0.6, 1.8, w.x);
  float3 cellTint = pastel(w.y + t / 60.0, 0.55) * 0.16;
  float3 lineCol = pastel(w.y + 0.25 + ph * 0.8, 0.25);
  float3 sheen = pastel(u * 0.6 + p.x / 900.0 + 0.2, 0.5);

  float3 foil = cellTint + sheen * (0.22 * k + 0.08 * k2) + lineCol * wline * (0.12 + 0.85 * k + 0.3 * k2);
  float amt = STRENGTH * (0.55 + 0.8 * k + 0.3 * k2);
  // calm zone: the web stays quiet right beside glyphs (two extra taps)
  float2 tx = float2(6.0 * s / Resolution.x, 0.0);
  float near = max(distance(TermSample(tex + tx).rgb, Background.rgb),
                   distance(TermSample(tex - tx).rgb, Background.rgb));
  float calm = 1.0 - 0.75 * smoothstep(0.05, 0.12, near);
  float3 bg = lerp(c.rgb, foil, amt * calm);

  float3 txt = lerp(c.rgb, sheen, TEXT_TINT * k);
  float3 rgb = lerp(bg, txt, textMask);

  // --- silver GX frame: the sheen crosses it --------------------------------
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float bevel = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 1.8 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 3.0 * s, edge - B)) * step(B, edge);
  float etch = step(0.8, frac((p.x - p.y) / 5.0));

  float3 silver = float3(0.78, 0.81, 0.85);
  float3 frameCol = silver * (0.55 + 0.35 * sin(depth * 3.14159) - 0.08 * etch);
  frameCol = lerp(frameCol, float3(1.0, 1.0, 1.0), 0.45 * k);
  frameCol = lerp(frameCol, sheen, 0.25 * k + 0.2 * k2);
  frameCol += bevel * 0.4;
  frameCol *= 1.0 - 0.45 * outerLine;

  rgb *= 1.0 - 0.35 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
