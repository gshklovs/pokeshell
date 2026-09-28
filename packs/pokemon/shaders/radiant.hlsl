// ============================================================================
// Skin: RADIANT
// Imitates: Radiant Rare (Sword & Shield: Astral Radiance onward) - a
//   silvery crosshatch of diamond / X shapes over the whole card, with star
//   glints at the crossings that catch the light as the card tilts.
//
// Tuning:
//   STRENGTH   how strongly the foil shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling
//   CELL_PX    size of one diamond of the crosshatch in pixels
// ============================================================================

#define STRENGTH  0.24
#define SPEED     1.0
#define BORDER_PX 12.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners (rounded was ~BORDER_PX * 1.2)
#define CELL_PX   18.0
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

// 4-point star in the 45deg-rotated frame -> reads as an "X" glint on screen.
// v = offset from the star centre in pixels (already rotated)
float xstar(float2 v, float s)
{
  float2 a = abs(v) / s;
  float arms = max(exp(-a.x * 1.1 - a.y * 0.22), exp(-a.y * 1.1 - a.x * 0.22));
  float core = exp(-dot(a, a) * 0.35);
  return saturate(arms * 0.8 + core);
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

  // --- diamond lattice: rotate 45deg so the cell edges become X lines
  float cell = CELL_PX * s;
  float2 r = float2(px.x + px.y, px.x - px.y) * 0.70711;   // rotated px
  float2 q = r / cell;
  float2 f = frac(q) - 0.5;
  float2 e = (0.5 - abs(f)) * cell;                        // px to cell edges
  float hatch = 1.0 - smoothstep(0.35 * s, 1.3 * s, min(e.x, e.y));

  // finer secondary crosshatch inside each diamond (1/3 period, faint)
  float2 f3 = frac(q * 3.0) - 0.5;
  float2 e3 = (0.5 - abs(f3)) * (cell / 3.0);
  float fine = 1.0 - smoothstep(0.2 * s, 0.9 * s, min(e3.x, e3.y));

  // alternate diamonds catch light differently (checker facets)
  float2 id = floor(q);
  float facet = frac((id.x + id.y) * 0.5) * 2.0;          // 0 or 1
  float facetShade = lerp(0.75, 1.0, facet * (0.5 + 0.5 * sin(t * 0.35 + (light.x - light.y) * 4.0)));

  // --- glints at lattice crossings: X stars that light up near the moving
  //     light and twinkle gently (<0.2 Hz)
  float2 vtx = floor(q + 0.5);
  float2 vOff = (q - vtx) * cell;
  float hv = hash21(vtx);
  float twinkle = 0.5 + 0.5 * sin(t * 1.1 + hv * 31.0);
  float2 vuv = float2(vtx.x + vtx.y, vtx.x - vtx.y) * 0.70711 * cell / Resolution;  // crossing in tex space
  float gv = glare(vuv, light, aspect, 4.0);
  float glint = xstar(vOff, s) * smoothstep(0.35, 1.0, hv) * twinkle * gv;

  // silver with a faint spectral sheen that drifts (period ~20 s)
  float3 silver = float3(0.74, 0.77, 0.83);
  float3 sheen = hue(dot(tex, float2(0.6, 0.4)) + (light.x - 0.5) * 0.7 + t / 20.0);
  float3 metal = lerp(silver, silver * (0.6 + 0.6 * sheen), 0.3);

  float3 foil = metal * facetShade * (0.2 + 0.45 * hatch + 0.12 * fine) * (0.45 + 0.75 * g)
              + float3(1.0, 1.0, 1.0) * glint;
  float amt = STRENGTH * (0.6 + 0.4 * g);
  float3 bg = lerp(c.rgb, foil, amt) + float3(0.9, 0.93, 1.0) * glint * 0.12;

  float3 txt = lerp(c.rgb, metal, TEXT_TINT);
  float3 rgb = lerp(bg, txt, textMask);

  // --- frame: polished silver bar with the same X hatch and glints --------
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float bevel = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 1.8 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 3.0 * s, edge - B)) * step(B, edge);

  float fh = 1.0 - smoothstep(0.3 * s, 1.0 * s, min(e3.x, e3.y));
  float3 frameCol = metal * (0.5 + 0.35 * sin(depth * 3.14159) + 0.45 * g) * (0.8 + 0.25 * fh);
  frameCol += float3(1.0, 1.0, 1.0) * glint * 0.8;
  frameCol += bevel * 0.45 * float3(1.0, 1.0, 1.0);
  frameCol *= 1.0 - 0.45 * outerLine;

  rgb *= 1.0 - 0.35 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
