// =====================================================================
//  Skin: CRACKED ICE
//  Imitates: the "cracked ice" holofoil (e-Card / EX era promos and
//  many later reprints) -- angular glass-shard facets, each catching the
//  light at its own angle and flashing its own rainbow hue.
//  Windows Terminal pixel shader (ps_4_0).
//
//  Tuning:
//    STRENGTH  - how strongly the foil shows on background pixels (0.15-0.35)
//    SPEED     - global motion speed multiplier (1.0 = slow, 0.5 = slower)
//    BORDER_PX - card frame width in pixels (at 100% DPI)
//    SHARD_PX  - average size of an ice shard in pixels
// =====================================================================

#define STRENGTH  0.28
#define SPEED     1.0
#define BORDER_PX 12.0
#define SHARD_PX  72.0

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

float2 hash22(float2 p)
{
  float n = hash21(p);
  return float2(n, hash21(p + n + 17.17));
}

float3 rainbow(float h)
{
  return 0.5 + 0.5 * cos(6.28318 * (h + float3(0.0, 0.333, 0.667)));
}

// Voronoi: returns the id of the nearest cell and an edge measure (F2-F1).
// The cells are convex polygons, which gives the straight, angular shard look.
void shards(float2 p, out float2 id, out float edge)
{
  float2 ip = floor(p);
  float2 fp = frac(p);
  float d1 = 8.0;
  float d2 = 8.0;
  id = ip;
  for (int j = -1; j <= 1; j++)
  {
    for (int i = -1; i <= 1; i++)
    {
      float2 g = float2((float)i, (float)j);
      float2 o = 0.1 + 0.8 * hash22(ip + g);
      float2 r = g + o - fp;
      float d = dot(r, r);
      if (d < d1) { d2 = d1; d1 = d; id = ip + g; }
      else if (d < d2) { d2 = d; }
    }
  }
  edge = sqrt(d2) - sqrt(d1);
}

// Shade one shard: returns foil color, "flash" amount in .w
float4 shardColor(float2 id, float2 uv, float2 light, float t)
{
  float h  = hash21(id);
  float h2 = hash21(id + 7.31);
  float2 n = hash22(id + 3.17) * 2.0 - 1.0;          // random facet tilt
  float facing = dot(n, (light - 0.5) * 2.4) + (h2 - 0.5) * 0.8;
  float flash  = smoothstep(0.15, 1.15, facing);     // shard catches the light
  float hue = h * 0.6 + 0.45 * dot(uv - light, float2(0.8, 0.6)) + t * 0.015;
  return float4(rainbow(hue), flash);
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

  // slowly wandering "light" = fake card tilt
  float2 light = float2(0.5 + 0.35 * sin(t * 0.21), 0.5 + 0.25 * cos(t * 0.17));
  float2 dd = (tex - light) * float2(aspect, 1.0);
  float glare = exp(-dot(dd, dd) * 5.0);

  // ---- background foil: big ice shards
  float2 id; float edge;
  shards(px / (SHARD_PX * s), id, edge);
  float4 sc = shardColor(id, tex, light, t);
  float shardLum = 0.22 + 0.78 * sc.w;
  float crack = 1.0 - smoothstep(0.0, 0.05, edge);
  float3 foil = sc.rgb * shardLum * (0.55 + 0.45 * glare)
              + crack * (0.25 + 0.35 * glare) * float3(0.85, 0.9, 1.0);
  foil = saturate(foil);

  // ---- frame: silver edge made of small bright shards
  float bw = BORDER_PX * s;
  float d = edgeDist(px);
  float frameMask = 1.0 - smoothstep(bw - 0.75 * s, bw + 0.25 * s, d);
  float bevelT = saturate(d / bw);
  float prof = 0.6 + 0.4 * sin(bevelT * 3.14159);

  float2 fid; float fedge;
  shards(px / (16.0 * s), fid, fedge);
  float4 fc = shardColor(fid, tex, light, t);
  float3 silver = float3(0.72, 0.75, 0.80);
  float3 frameCol = silver * prof * (0.55 + 0.45 * fc.w)
                  + fc.rgb * fc.w * 0.35
                  + glare * 0.15;
  frameCol *= 1.0 - 0.35 * (1.0 - smoothstep(0.0, 0.08, fedge));  // fine cracks
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
  float3 textCol = lerp(c.rgb, sc.rgb, 0.06);
  float3 rgb = lerp(surface, textCol, textMask);
  return float4(rgb, 1.0);
}
