// ============================================================================
// Skin: VAULT GX
// Imitates: the Hidden Fates Shiny Vault Rare Shiny GX (Charizard-GX SV49) -
//   the step above the Shiny Vault foil: black-and-silver vault metal cut with
//   an etched fingerprint texture, a silver beam pair (a main beam and a
//   fainter counter beam, a whisper of prism in the silver) that makes the
//   etched lines flash as it passes, glitter, and big four-point star flares
//   that bloom slowly. A heavier bevelled silver frame. The pokeshell Rare
//   Shiny GX card animation.
//
// Tuning:
//   STRENGTH   how strongly the foil shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling
//   BEAM_S     seconds for the beam to cross the terminal once
//   ETCH_PX    spacing of the etched lines in pixels at 100% scaling
// ============================================================================

#define STRENGTH  0.27
#define SPEED     1.0
#define BORDER_PX 13.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners
#define BEAM_S    13.0
#define ETCH_PX   7.0
#define FLARES    0.35
#define GLITTER   0.06
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

float cardEdge(float2 px, float radius)
{
  float2 h = Resolution * 0.5;
  float2 q = abs(px - h) - (h - radius);
  float sd = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;
  return -sd;
}

float tent(float u)
{
  float k = saturate(1.0 - abs(u * 1.6));
  return k * k * (3.0 - 2.0 * k);
}

// a big four-point flare in a sparse grid, blooming slowly
float flare(float2 p, float cell, float seed, float dens, float t)
{
  float2 id = floor(p / cell);
  float h = hash21(id + seed);
  float2 ctr = (id + 0.3 + 0.4 * float2(hash21(id + seed + 1.7), hash21(id + seed + 5.3))) * cell;
  float2 d = abs(p - ctr);
  float shape = exp(-dot(d, d) / 3.0)
              + 0.8 * exp(-d.x / 9.0) * exp(-d.y * d.y / 0.8)
              + 0.8 * exp(-d.y / 9.0) * exp(-d.x * d.x / 0.8);
  float bloom = pow(saturate(sin(t * (0.3 + 0.25 * h) + h * 40.0)), 5.0);
  return shape * bloom * step(h, dens);
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

  // --- the etched fingerprint: contours of two whorls bent by a slow wave
  float2 w1 = p - res * float2(0.2, 0.25);
  float2 w2 = p - res * float2(0.8, 0.7);
  float f = (length(w1 * float2(1.0, 1.15)) + 0.8 * length(w2 * float2(1.0, 1.15))) / 1.8
          + 9.0 * sin(p.x / 40.0) * cos(p.y / 52.0);
  float lp = frac(f / ETCH_PX);
  float etch = smoothstep(0.0, 0.15, lp) * (1.0 - smoothstep(0.3, 0.45, lp));

  // --- the beam pair
  float band = 0.14 * span;
  float ph = frac(t / BEAM_S);
  float u1 = ((p.x + p.y) - (-band + ph * (span + 2.0 * band))) / band;
  float k1 = tent(u1);
  float u2 = ((p.x - p.y) - (res.x + band - ph * (span + 2.0 * band) * 0.9)) / (band * 0.7);
  float k2 = tent(u2) * 0.4;
  float3 prism = lerp(hue(u1 * 0.5 + 0.55), float3(1.0, 1.0, 1.0), 0.72);

  // --- black-and-silver metal, the etch raised in silver
  float3 metal = float3(0.11, 0.12, 0.15) + float3(0.30, 0.32, 0.36) * etch * 0.5;

  float2 gc = floor(p / 3.0);
  float gl = pow(saturate(cos(6.28318 * (t / 5.0 + hash21(gc + 5.9)))), 24.0);
  float2 gf = frac(p / 3.0) - 0.5;
  float grain = gl * step(hash21(gc + 0.7), GLITTER) * exp(-dot(gf, gf) * 6.0);

  float fl = flare(p, 120.0, 11.0, FLARES, t) + 0.7 * flare(p + 57.0, 70.0, 23.0, FLARES * 0.6, t);

  float3 foil = metal + prism * (0.42 * k1 + 0.25 * k2) + float3(1.0, 1.0, 1.0) * etch * 0.75 * k1;
  float2 tx = float2(6.0 * s / Resolution.x, 0.0);
  float near = max(distance(TermSample(tex + tx).rgb, Background.rgb),
                   distance(TermSample(tex - tx).rgb, Background.rgb));
  float calm = 1.0 - 0.8 * smoothstep(0.05, 0.12, near);
  float amt = STRENGTH * (0.65 + 0.8 * k1 + 0.3 * k2);
  float3 bg = lerp(c.rgb, foil, amt * calm)
            + float3(0.95, 0.97, 1.0) * (grain * 1.5 + fl * 1.3) * STRENGTH * calm;

  float3 txt = lerp(c.rgb, prism, TEXT_TINT * k1);
  float3 rgb = lerp(bg, txt, textMask);

  // --- heavier bevelled silver frame ----------------------------------------
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float bevel = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 1.8 * s)));
  float groove = 1.0 - smoothstep(0.3 * s, 0.9 * s, abs(edge - B * 0.5));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 3.0 * s, edge - B)) * step(B, edge);

  float3 frameCol = float3(0.76, 0.79, 0.84) * (0.5 + 0.38 * sin(depth * 3.14159) + 0.1 * etch);
  frameCol = lerp(frameCol, prism, 0.6 * k1);
  frameCol = lerp(frameCol, prism, 0.4 * k2);
  frameCol += bevel * 0.4 + grain * 0.4 + fl * 0.5;
  frameCol *= (1.0 - 0.45 * outerLine) * (1.0 - 0.4 * groove);

  rgb *= 1.0 - 0.35 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
