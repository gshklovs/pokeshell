// ============================================================================
// Skin: LIQUID CHROME
// Imitates: the Scarlet & Violet Futuristic Rare (30th Celebration Mewtwo ex
//   157) - liquid chrome: platinum metal with rolling reflections, cyan on
//   the crests and magenta in the troughs, a hard specular line crossing,
//   a faint red-black pulse and a few star flares, in a violet-edged chrome
//   frame. The pokeshell Futuristic Rare card animation.
//
// Tuning:
//   STRENGTH   how strongly the chrome shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling
//   ROLL_S     seconds for the reflections to roll one wavelength
//   PULSE      strength of the red-black pulse (0 = off)
// ============================================================================

#define STRENGTH  0.24
#define SPEED     1.0
#define BORDER_PX 12.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners
#define ROLL_S    9.0
#define SPEC_S    11.0
#define PULSE_S   8.0
#define PULSE     0.6
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

float cardEdge(float2 px, float radius)
{
  float2 h = Resolution * 0.5;
  float2 q = abs(px - h) - (h - radius);
  float sd = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;
  return -sd;
}

// the platinum ramp: violet-black -> steel -> white, x in 0..1
float3 platinum(float x)
{
  float3 a = float3(0.10, 0.09, 0.14);
  float3 b = float3(0.37, 0.35, 0.45);
  float3 c = float3(0.72, 0.71, 0.79);
  float3 d = float3(1.0, 1.0, 1.0);
  float3 col = lerp(a, b, saturate(x * 3.0));
  col = lerp(col, c, saturate(x * 3.0 - 1.0));
  return lerp(col, d, saturate(x * 3.0 - 2.0));
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

  // --- the metal: a smooth "scene" luminance under rolling liquid reflections
  float l = vnoise(p / 320.0) * 0.65 + vnoise(p / 130.0 + 4.0) * 0.35;
  float refl = sin(p.y / 30.0 + 2.2 * sin(p.x / 78.0) + 4.0 * l + 6.28318 * t / ROLL_S);
  float lv = saturate(0.1 + 0.5 * l + 0.3 * refl);
  float3 metal = platinum(lv);
  float3 tint = refl > 0.0 ? float3(0.35, 0.95, 1.0) : float3(1.0, 0.35, 0.9);   // cyan crests, magenta troughs
  metal = lerp(metal, tint * (0.35 + 0.65 * lv), 0.45 * abs(refl));

  // the red-black pulse: a slow deep-red cast that swells through the troughs
  float pulse = (0.5 + 0.5 * cos(6.28318 * t / PULSE_S)) * (0.5 - 0.5 * refl);
  metal = lerp(metal, float3(0.45, 0.03, 0.08) * (0.3 + lv), PULSE * 0.6 * pulse);

  // --- the hard specular line crossing on the diagonal, with a soft halo
  float d = (p.x + p.y) - (-0.1 * span + frac(t / SPEC_S) * 1.2 * span);
  float spec = exp(-d * d / 3.0) * 0.65 + exp(-d * d / 160.0) * 0.25;

  // --- star flares: a few four-point glints, twinkling slowly
  float2 sc = floor(p / 170.0);
  float sh = hash21(sc + 23.0);
  float2 sd = abs(p - (sc + 0.2 + 0.6 * float2(hash21(sc + 1.0), hash21(sc + 2.0))) * 170.0);
  float star = (exp(-dot(sd, sd) / 3.0) + 0.7 * exp(-sd.x / 7.0) * exp(-sd.y * sd.y / 0.5)
             + 0.7 * exp(-sd.y / 7.0) * exp(-sd.x * sd.x / 0.5))
             * pow(saturate(sin(t * (0.3 + 0.25 * sh) + sh * 40.0)), 5.0) * step(sh, 0.45);

  float3 foil = metal + float3(0.85, 1.0, 1.0) * spec;
  float amt = STRENGTH * (0.75 + 0.25 * abs(refl) + 0.9 * spec);
  float3 bg = lerp(c.rgb, foil, saturate(amt)) + float3(0.9, 1.0, 1.0) * star * 0.45;

  float3 txt = lerp(c.rgb, tint, TEXT_TINT * abs(refl));
  float3 rgb = lerp(bg, txt, textMask);

  // --- chrome frame with a violet edge, the same reflections rolling along it ---
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float bevel = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 1.8 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 3.0 * s, edge - B)) * step(B, edge);

  float fr = sin((p.x - p.y) / 40.0 + depth * 3.0 + 6.28318 * t / ROLL_S);
  float3 frameCol = platinum(saturate(0.35 + 0.35 * sin(depth * 3.14159) + 0.25 * fr));
  frameCol = lerp(frameCol, fr > 0.0 ? float3(0.35, 0.95, 1.0) : float3(1.0, 0.35, 0.9), 0.18 * abs(fr));
  frameCol = lerp(frameCol, float3(0.75, 0.49, 1.0), 0.45 * (1.0 - smoothstep(0.0, 0.35, depth)));   // violet edge (#c07cff)
  frameCol += float3(1.0, 1.0, 1.0) * (spec * 0.8 + bevel * 0.35);
  frameCol *= 1.0 - 0.45 * outerLine;

  rgb *= 1.0 - 0.35 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
