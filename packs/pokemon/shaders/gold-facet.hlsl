// ============================================================================
// Skin: GOLD FACET
// Imitates: the Sword & Shield Rare Secret gold card (Evolving Skies
//   Froslass 226) - the whole card engraved in faceted, crystalline gold
//   whose facets catch the light one by one, a 45deg metallic sheen sweeping
//   across with a trailing echo, fine glitter and a few four-point star
//   flares, in a heavy gold frame. The pokeshell Rare Secret card animation.
//
// Tuning:
//   STRENGTH   how strongly the gold shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling (gold gets a heavy frame)
//   FACET_PX   rough size of one crystal facet in pixels
//   SHEEN_S    seconds for the sheen to cross the terminal once
// ============================================================================

#define STRENGTH  0.22
#define SPEED     1.0
#define BORDER_PX 16.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners
#define FACET_PX  80.0
#define SHEEN_S   11.0
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

float2 hash22(float2 p)
{
  return float2(hash21(p), hash21(p + 17.31));
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

// crystal facets: returns (facet shade 0..1, seam 0..1) for a Voronoi cell grid in px
float2 facets(float2 p, float2 lightDir)
{
  float2 g = p / FACET_PX;
  float2 ig = floor(g);
  float d1 = 9.0;
  float d2 = 9.0;
  float2 best = float2(0.0, 0.0);
  float2 bestOff = float2(0.0, 0.0);
  for (int j = -1; j <= 1; j++)
  {
    for (int i = -1; i <= 1; i++)
    {
      float2 cell = ig + float2(i, j);
      float2 o = cell + 0.15 + 0.7 * hash22(cell) - g;
      float d = dot(o, o);
      if (d < d1) { d2 = d1; d1 = d; best = cell; bestOff = o; }
      else if (d < d2) { d2 = d; }
    }
  }
  // each facet is a tilted plane: its normal decides how it catches the light
  float2 n = hash22(best + 3.7) * 2.0 - 1.0;
  float lit = 0.5 + 0.5 * dot(normalize(n + float2(1e-3, 0.0)), lightDir);
  lit += 0.18 * dot(-bestOff, n);                        // a gradient across the facet
  float seam = 1.0 - smoothstep(0.0, 0.12, sqrt(d2) - sqrt(d1));
  return float2(saturate(lit), seam);
}

// a four-point star flare (long axial arms, short diagonal ones), in px
float flare(float2 d, float len)
{
  float2 a = abs(d);
  float core = exp(-dot(d, d) / 3.0);
  float arms = exp(-a.x / len) * exp(-a.y * a.y / 0.6) + exp(-a.y / len) * exp(-a.x * a.x / 0.6);
  float2 r = float2(d.x + d.y, d.x - d.y) * 0.7071;
  float2 ra = abs(r);
  float diag = exp(-ra.x / (len * 0.35)) * exp(-ra.y * ra.y / 0.4) + exp(-ra.y / (len * 0.35)) * exp(-ra.x * ra.x / 0.4);
  return core + arms * 0.8 + diag * 0.35;
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
  float span = res.x + res.y;

  float textMask = smoothstep(0.05, 0.12, distance(c.rgb, Background.rgb));

  // --- faceted gold: the light direction circles slowly, so facets light up in turn
  float la = t * 0.35;
  float2 lightDir = float2(cos(la), sin(la));
  float2 fs = facets(p, lightDir);
  float fine = 0.5 + 0.5 * sin(dot(p, float2(0.7071, 0.7071)) * 2.1);   // fine engraved hatching
  float3 goldCol = goldRamp(0.2 + 0.55 * fs.x);

  // --- the 45deg sheen: a hot core, a stepped falloff and a trailing echo
  float ph = frac(t / SHEEN_S);
  float d = (p.x + p.y) - (-0.1 * span + ph * 1.2 * span);
  float sheen = exp(-d * d / 40.0) * 0.9 + exp(-d * d / 900.0) * 0.35 + exp(-(d + 70.0) * (d + 70.0) / 150.0) * 0.3;

  // --- glitter: sparse sparks flashing briefly
  float2 gc = floor(p / 5.0);
  float gh = hash21(gc + 9.1);
  float2 gd = frac(p / 5.0) - float2(0.5, 0.5);
  float glit = exp(-dot(gd, gd) * 30.0) * pow(saturate(sin(t * (0.45 + 0.4 * gh) + gh * 70.0)), 14.0) * step(gh, 0.035);

  // --- star flares: one in some 150 px cells, twinkling slowly
  float2 sc = floor(p / 150.0);
  float sh = hash21(sc + 41.0);
  float2 sp = (sc + 0.2 + 0.6 * hash22(sc + 5.0)) * 150.0;
  float fl = flare(p - sp, 9.0) * pow(saturate(sin(t * (0.3 + 0.2 * sh) + sh * 30.0)), 4.0) * step(sh, 0.5);

  float3 foil = goldCol * (0.6 + 0.2 * fine) * (1.0 - 0.35 * fs.y) + float3(1.0, 0.96, 0.8) * sheen * 0.7;
  float amt = STRENGTH * (0.55 + 0.35 * fs.x + 0.8 * sheen);
  float3 bg = lerp(c.rgb, foil, saturate(amt));
  float spark = glit * 0.55 + fl * 0.5;
  // sparks live in the background only (text pixels take txt below)
  bg += float3(1.0, 0.95, 0.78) * spark;

  float3 txt = lerp(c.rgb, goldCol, TEXT_TINT);
  float3 rgb = lerp(bg, txt, textMask);

  // --- heavy gold frame, faceted too ---------------------------------------
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float bevel1 = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - 3.0 * s));
  float bevel2 = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 2.0 * s)));
  float groove = 1.0 - smoothstep(0.0, 1.3 * s, abs(edge - B * 0.55));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 4.0 * s, edge - B)) * step(B, edge);

  float fRefl = saturate(0.25 + 0.5 * sin(depth * 3.14159) + 0.25 * fs.x + 0.5 * sheen);
  float3 frameCol = goldRamp(fRefl) * (0.85 + 0.15 * fine) * (1.0 - 0.25 * fs.y);
  frameCol += float3(1.0, 0.95, 0.75) * (bevel1 + bevel2) * 0.4;
  frameCol += float3(1.0, 0.97, 0.85) * fl * 0.6;
  frameCol *= 1.0 - 0.45 * groove;
  frameCol *= 1.0 - 0.5 * outerLine;

  rgb *= 1.0 - 0.4 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.012, 0.01, 0.006), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
