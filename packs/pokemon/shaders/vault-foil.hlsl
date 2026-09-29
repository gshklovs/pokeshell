// ============================================================================
// Skin: VAULT FOIL
// Imitates: the Hidden Fates Shiny Vault Rare Shiny (Charmander SV6) - the
//   bright-silver vault foil (the signed-off look): brushed bright silver
//   with the vault's printed sparkle stars as a raised silver relief on a
//   lattice, fine glitter that flashes one grain at a time, and a narrow
//   white specular band with thin cyan / pink prismatic fringes that crosses
//   the card and makes the stars catch the light. Chrome silver frame. The
//   pokeshell Rare Shiny card animation.
//
// Tuning:
//   STRENGTH   how strongly the foil shows through the background (0.15-0.35)
//   SPEED      global motion speed multiplier
//   BORDER_PX  frame width in pixels at 100% scaling
//   SWEEP_S    seconds for the specular band to cross the terminal once
//   STAR_PX    spacing of the printed star lattice in pixels at 100% scaling
// ============================================================================

#define STRENGTH  0.22
#define SPEED     1.0
#define BORDER_PX 12.0
#define CORNER_PX 0.0   // frame corner radius in px: 0 = square corners
#define SWEEP_S   12.0
#define STAR_PX   86.0
#define GLITTER   0.05
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
  return lerp(lerp(hash21(i), hash21(i + float2(1, 0)), u.x), lerp(hash21(i + float2(0, 1)), hash21(i + 1.0), u.x), u.y);
}

float cardEdge(float2 px, float radius)
{
  float2 h = Resolution * 0.5;
  float2 q = abs(px - h) - (h - radius);
  float sd = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;
  return -sd;
}

// the printed vault star: a four-point star (thin arms + core) at the lattice cell centre, jittered.
// returns (star intensity, its top-left-lit emboss)
float2 vaultStar(float2 p, float cell)
{
  float2 id = floor(p / cell);
  float h = hash21(id + 3.1);
  float2 ctr = (id + 0.3 + 0.4 * float2(hash21(id + 7.7), hash21(id + 1.3))) * cell;
  float2 d = p - ctr;
  float L = cell * (0.16 + 0.12 * h);
  float2 a = abs(d);
  float star = exp(-a.x / (L * 0.28)) * exp(-a.y * a.y / 3.0) + exp(-a.y / (L * 0.28)) * exp(-a.x * a.x / 3.0)
             + exp(-dot(d, d) / (L * L * 0.05));
  star = saturate(star) * step(0.25, h);
  // emboss: brighter on the side facing the top-left light, darker opposite
  float lit = saturate(0.5 - 0.5 * dot(normalize(d + 0.001), float2(0.6, 0.8)));
  return float2(star, star * (lit - 0.5));
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

  // --- brushed bright silver: horizontal streaks
  float brush = vnoise(float2(p.x * 0.02, p.y * 0.9)) * 0.6 + vnoise(float2(p.x * 0.05, p.y * 2.3)) * 0.4;
  float3 metal = float3(0.70, 0.73, 0.78) * (0.86 + 0.24 * brush);

  // --- the specular band with its prismatic fringes (cyan ahead, pink behind)
  float band = 0.05 * span;
  float ph = frac(t / SWEEP_S);
  float dd = (p.x + p.y) - (-3.0 * band + ph * (span + 6.0 * band));
  float k = exp(-(dd / band) * (dd / band));
  float fc = exp(-((dd + 1.6 * band) / (0.6 * band)) * ((dd + 1.6 * band) / (0.6 * band)));
  float fp = exp(-((dd - 1.6 * band) / (0.6 * band)) * ((dd - 1.6 * band) / (0.6 * band)));

  // --- the printed stars, a raised relief in the silver (a shade darker, lit top-left), catching the band
  float2 st = vaultStar(p, STAR_PX);
  float3 starCol = float3(-0.20, -0.19, -0.16) * st.x * (1.0 - 0.8 * k) + st.y * 0.5 + 0.25 * k * st.x;

  // --- glitter: sparse grains, each flashing once per ~5 s on its own phase
  float2 gc = floor(p / 3.0);
  float gh = hash21(gc + 0.7);
  float gl = pow(saturate(cos(6.28318 * (t / 5.0 + hash21(gc + 5.9)))), 24.0);
  float2 gf = frac(p / 3.0) - 0.5;
  float grain = gl * step(gh, GLITTER) * exp(-dot(gf, gf) * 6.0);

  float3 foil = metal + starCol + float3(1.0, 1.0, 1.0) * k * 0.3
              + float3(0.35, 0.85, 1.0) * fc * 0.2 + float3(1.0, 0.5, 0.85) * fp * 0.16;
  float2 tx = float2(6.0 * s / Resolution.x, 0.0);
  float near = max(distance(TermSample(tex + tx).rgb, Background.rgb),
                   distance(TermSample(tex - tx).rgb, Background.rgb));
  float calm = 1.0 - 0.8 * smoothstep(0.05, 0.12, near);
  float amt = STRENGTH * (0.7 + 0.8 * k);
  float3 bg = lerp(c.rgb, foil, amt * calm) + float3(1.0, 1.0, 1.0) * grain * STRENGTH * 1.6 * calm;

  float3 txt = lerp(c.rgb, float3(1.0, 1.0, 1.0), TEXT_TINT * k);
  float3 rgb = lerp(bg, txt, textMask);

  // --- chrome silver frame -------------------------------------------------
  float B = BORDER_PX * s;
  float edge = cardEdge(px, CORNER_PX * Scale);
  float frameMask = 1.0 - smoothstep(B - 0.75 * s, B + 0.75 * s, edge);
  float depth = saturate(edge / B);
  float bevel = 1.0 - smoothstep(0.0, 1.1 * s, abs(edge - (B - 1.8 * s)));
  float outerLine = 1.0 - smoothstep(0.0, 1.0 * s, abs(edge - 0.8 * s));
  float innerShadow = (1.0 - smoothstep(0.0, 3.0 * s, edge - B)) * step(B, edge);

  float3 frameCol = float3(0.74, 0.77, 0.83) * (0.5 + 0.35 * sin(depth * 3.14159) + 0.12 * brush);
  frameCol = lerp(frameCol, float3(1.0, 1.0, 1.0), 0.55 * k);
  frameCol += float3(0.35, 0.85, 1.0) * fc * 0.15 + float3(1.0, 0.5, 0.85) * fp * 0.12 + grain * 0.5;
  frameCol += bevel * 0.35;
  frameCol *= 1.0 - 0.45 * outerLine;

  rgb *= 1.0 - 0.35 * innerShadow * (1.0 - textMask);
  rgb = lerp(rgb, frameCol, frameMask * (1.0 - textMask));
  rgb = lerp(rgb, float3(0.01, 0.01, 0.012), step(edge, 0.0));

  return float4(saturate(rgb), 1.0);
}
