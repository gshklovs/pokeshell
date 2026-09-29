// ============================================================================
// Skin: PEARL
// Imitates: the Scarlet & Violet Special Illustration Rare (30th Celebration
//   Gengar ex 154) - a textured painting whose embossed brushwork catches
//   and loses a swinging light, with a broad pearl lustre (pink shading to
//   cyan) sweeping across it, inside a warm gold frame that takes the same
//   pearl sheen. The pokeshell Special Illustration Rare card animation.
//
// Tuning:
//   STRENGTH   how strongly the textured glow shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling
//   PEARL_S    seconds for the pearl lustre to cross the terminal once
//   RELIEF     depth of the embossed brushwork (0..1)
// ============================================================================

#define STRENGTH  0.26
#define SPEED     1.0
#define BORDER_PX 12.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners
#define PEARL_S   13.0
#define RELIEF    0.55
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

// the brushwork height: short strokes along a slowly turning direction
float brush(float2 p)
{
  float ang = 0.6 + vnoise(p / 500.0 + 3.0) * 2.4;
  float2 dir = float2(cos(ang), sin(ang));
  float2 bp = float2(dot(p, dir), dot(p, float2(-dir.y, dir.x)));
  return vnoise(bp * float2(0.035, 0.2)) * 0.7 + vnoise(p / 90.0) * 0.3;
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

  // --- textured glow: a dusky violet painting, embossed brushwork lit by a swinging light
  float h0 = brush(p);
  float gx = brush(p + float2(2.0, 0.0)) - h0;
  float gy = brush(p + float2(0.0, 2.0)) - h0;
  float th = -2.23 + sin(t * 6.28318 / 16.0) * 1.6;            // light swings left -> right -> back
  float relief = clamp(-(gx * cos(th) + gy * sin(th)) * 14.0, -0.35, 0.35) * RELIEF;

  float wv = vnoise(p / 300.0 + float2(t * 0.01, 0.0));
  float3 paint = lerp(float3(0.30, 0.18, 0.46), float3(0.16, 0.24, 0.52), wv);   // violet -> night blue
  paint = lerp(paint, float3(0.62, 0.36, 0.70), smoothstep(0.6, 0.95, h0) * 0.5);
  paint *= 0.75 + relief * 1.6;
  float2 cv = tex - float2(0.5, 0.5);
  paint *= 1.0 - 0.35 * dot(cv, cv) * 2.0;                     // soft vignette

  // --- the pearl lustre: a broad band on the diagonal, pink on its leading side, cyan behind
  float w = 0.11 * span;
  float dd = ((p.x + p.y) * 0.8 + p.y * 0.2 - (-1.5 * w + frac(t / PEARL_S) * (span + 3.0 * w))) / w;
  float band = exp(-0.5 * dd * dd);
  float ph = lerp(0.83, 0.5, saturate(-dd * 0.5 + 0.5));      // PEARL: pink -> cyan across the band
  float3 pearl = lerp(hue(ph), float3(1.0, 1.0, 1.0), 0.45);

  float3 bg = lerp(c.rgb, paint, STRENGTH);
  bg = lerp(bg, pearl * (0.75 + relief), 0.34 * band);         // the lustre rides over the brushwork

  float3 txt = lerp(c.rgb, pearl, TEXT_TINT * band);
  float3 rgb = lerp(bg, txt, textMask);

  // --- warm gold frame with the pearl sheen --------------------------------
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float bevel = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 1.8 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 3.0 * s, edge - B)) * step(B, edge);

  float3 gold = float3(0.94, 0.78, 0.31);
  float3 frameCol = gold * (0.55 + 0.3 * sin(depth * 3.14159) + relief * 0.12);
  frameCol = lerp(frameCol, pearl, 0.6 * band);
  frameCol += bevel * 0.35 * float3(1.0, 1.0, 1.0);
  frameCol *= 1.0 - 0.45 * outerLine;

  rgb *= 1.0 - 0.35 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
