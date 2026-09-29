// ============================================================================
// Skin: IR GLOW
// Imitates: the Scarlet & Violet Illustration Rare (30th Celebration Lapras
//   131) - a full-bleed painting with a soft painterly glow (washes of colour
//   and brushwork drifting under a slow light) and a very subtle etch of fine
//   lines that follow the painting, catching a faint rainbow wave as it
//   passes, inside a pale aqua frame. The pokeshell Illustration Rare card
//   animation.
//
// Tuning:
//   STRENGTH   how strongly the painted glow shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling
//   ETCH       strength of the art-following etch wave (0 = off, keep it subtle)
//   WAVE_S     seconds for one etch wave to cross the terminal
// ============================================================================

#define STRENGTH  0.28
#define SPEED     1.0
#define BORDER_PX 12.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners
#define ETCH      0.5
#define WAVE_S    15.0
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

  // --- the painting: soft washes of sea / sky colour that drift very slowly
  float2 q = p / 260.0;
  float w1 = vnoise(q + float2(t * 0.012, 0.0));
  float w2 = vnoise(q * 1.7 + float2(5.2, t * 0.009));
  float3 wash = lerp(float3(0.30, 0.62, 0.78), float3(0.62, 0.52, 0.86), w1);   // aqua -> lilac
  wash = lerp(wash, float3(0.95, 0.80, 0.62), smoothstep(0.55, 0.9, w2) * 0.6); // warm light patches

  // brushwork: short stretched strokes whose direction swings across the canvas
  float ang = vnoise(p / 400.0 + 11.0) * 3.0;
  float2 dir = float2(cos(ang), sin(ang));
  float2 bp = float2(dot(p, dir), dot(p, float2(-dir.y, dir.x)));
  float stroke = vnoise(bp * float2(0.03, 0.22));
  float lum = w1 * 0.6 + stroke * 0.4;

  // a soft glow that follows the slow light position
  float2 light = float2(0.5 + 0.35 * sin(t * 0.13), 0.45 + 0.25 * cos(t * 0.11));
  float2 dl = (tex - light) * float2(res.x / res.y, 1.0);
  float glow = exp(-dot(dl, dl) * 2.2);

  // --- the subtle art-following etch: fine lines of (diagonal + 9 * painting), lit by a wave
  float f = (p.x + p.y) / 4.0 / 2.0 + 9.0 * lum;
  float ld = abs(frac(f + 0.5) - 0.5) / max(fwidth(f), 1e-4);
  float eline = 1.0 - smoothstep(0.5, 1.4, ld);
  float wd = ((p.x - p.y * 0.4) - (-0.2 * span + frac(t / WAVE_S) * 1.4 * span)) / (0.12 * span);
  float wave = exp(-wd * wd);
  float3 rain = lerp(hue(f / 30.0 - t / 25.0), float3(1.0, 1.0, 1.0), 0.35);

  float3 paint = wash * (0.55 + 0.45 * stroke) * (0.5 + 0.7 * glow);
  paint = lerp(paint, rain, eline * wave * ETCH);
  float amt = STRENGTH * (0.55 + 0.45 * glow + 0.5 * eline * wave * ETCH);
  float3 bg = lerp(c.rgb, paint, amt);

  float3 txt = lerp(c.rgb, wash, TEXT_TINT);
  float3 rgb = lerp(bg, txt, textMask);

  // --- pale aqua frame, glowing where the light sits -------------------------
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float bevel = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 1.8 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 3.0 * s, edge - B)) * step(B, edge);

  float3 aqua = float3(0.50, 0.84, 0.90);
  float3 frameCol = lerp(aqua, wash, 0.35) * (0.55 + 0.3 * sin(depth * 3.14159) + 0.35 * glow);
  frameCol = lerp(frameCol, rain, 0.35 * wave);
  frameCol += bevel * 0.3 * float3(1.0, 1.0, 1.0);
  frameCol *= 1.0 - 0.45 * outerLine;

  rgb *= 1.0 - 0.35 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
