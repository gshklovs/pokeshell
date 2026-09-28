// =====================================================================
// Skin: REVERSE HOLO
// Imitates: the classic Pokemon TCG reverse holofoil (Legendary
//   Collection / e-Card era onward, still printed today). The art box
//   stays matte; the card body around it and the border carry a
//   rainbow foil sheen with a fine metallic grain.
// On the terminal: the centre of the window stays nearly plain, the
//   outer margin shimmers, and the frame is the star.
// Tuning:
//   STRENGTH   background foil amount (0.15 - 0.35)
//   SPEED      animation speed multiplier (1.0 = ~16 s hue drift)
//   BORDER_PX  frame width in pixels at 100% DPI
// =====================================================================
#define STRENGTH  0.28
#define SPEED     1.0
#define BORDER_PX 12.0

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


static const float TAU = 6.2831853;

float sq(float x) { return x * x; }

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
    float d = hash21(i + float2(0.0, 1.0));
    float e = hash21(i + float2(1.0, 1.0));
    return lerp(lerp(a, b, u.x), lerp(d, e, u.x), u.y);
}

float3 spectrum(float h)
{
    return 0.5 + 0.5 * cos(TAU * (h + float3(0.0, 0.33, 0.67)));
}

float4 main(float4 pos : SV_POSITION, float2 tex : TEXCOORD) : SV_TARGET
{
    float4 c = TermSample(tex);

    float  s      = max(Scale, 1.0);
    float  t      = Time * SPEED;
    float2 px     = tex * Resolution;
    float2 uv     = px / Resolution.y;               // isotropic, y in 0..1
    float  aspect = Resolution.x / Resolution.y;

    // slowly wandering "light" = fake tilt of the card
    float2 lightPos = float2(aspect * (0.5 + 0.35 * sin(t * 0.33)),
                             0.5 + 0.25 * cos(t * 0.41));
    float2 toL = uv - lightPos;

    // text detection: anything that is not the background colour
    float textM = smoothstep(0.05, 0.15, distance(c.rgb, Background.rgb));

    // frame geometry
    float edge   = min(min(px.x, px.y), min(Resolution.x - px.x, Resolution.y - px.y));
    float bw     = BORDER_PX * s;
    float frameM = 1.0 - smoothstep(bw - s, bw, edge);

    // matte "art box" in the centre, foil grows toward the margins
    float2 q     = abs(tex - 0.5) * 2.0;
    float  box   = max(q.x, q.y);
    float  shine = lerp(0.10, 1.0, smoothstep(0.45, 0.95, box));

    // rainbow foil: diagonal bands, hue driven by light position + drift
    float  hue   = dot(uv, float2(0.55, 0.35)) * 1.1 + dot(toL, float2(0.45, -0.30)) + t * 0.06;
    float3 foil  = spectrum(hue);
    float  grain = vnoise(px / (1.6 * s));
    foil *= 0.70 + 0.40 * grain;

    // soft glare band that follows the light
    float2 gdir  = normalize(float2(1.0, -0.65));
    float  glare = exp(-sq(dot(toL, gdir) * 3.2));
    foil = foil * (0.45 + 0.55 * glare) + glare * 0.20;

    // background composite (screen-style, stays dark)
    float  amt   = STRENGTH * shine;
    float3 bgOut = c.rgb + foil * amt * (1.0 - c.rgb);
    float  shadow = exp(-sq((edge - bw - 2.0 * s) / (2.0 * s)));
    bgOut *= 1.0 - 0.45 * shadow;                     // inner shadow under the frame

    float3 textOut = lerp(c.rgb, foil, 0.06);
    float3 rgb = lerp(bgOut, textOut, textM);

    // ---- frame: bright rainbow metallic, the star of a reverse holo ----
    float  fh   = hue * 1.4 + (px.x - px.y) / Resolution.y * 0.9 - t * 0.05;
    float3 fcol = lerp(float3(0.78, 0.80, 0.84), spectrum(fh), 0.65);
    float  fgr  = vnoise(px / (1.1 * s));
    fcol *= 0.50 + 0.20 * fgr + 0.40 * glare;
    // metal sweep along the frame
    float sweep = exp(-sq(frac((px.x + px.y) / (Resolution.x + Resolution.y) - t * 0.06) - 0.5) * 60.0);
    fcol += sweep * 0.18;
    // bevels: bright inner line, dark outer lip
    float bevelIn  = exp(-sq((edge - (bw - 1.6 * s)) / (0.7 * s)));
    float bevelOut = smoothstep(0.0, 1.5 * s, edge);
    fcol += bevelIn * 0.45;
    fcol *= 0.35 + 0.65 * bevelOut;

    rgb = lerp(rgb, lerp(fcol, textOut, textM), frameM);
    return float4(saturate(rgb), 1.0);
}
