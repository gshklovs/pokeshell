# Holo shader spec (Windows Terminal 1.24 pixel shaders)

Each skin is one HLSL file: `packs/<pack>/shaders/<name>.hlsl`.
Windows Terminal runs it every frame over the whole rendered terminal (text + background).

## Required interface (exactly this)

```hlsl
Texture2D shaderTexture;      // the rendered terminal frame
SamplerState samplerState;
cbuffer PixelShaderSettings {
  float  Time;        // seconds, increases continuously (WT redraws every frame when a shader uses Time)
  float  Scale;       // DPI scale (1.0, 1.25, 1.5...)
  float2 Resolution;  // render target size in pixels
  float4 Background;  // the terminal's background color (premultiplied rgba)
};

float4 main(float4 pos : SV_POSITION, float2 tex : TEXCOORD) : SV_TARGET
{
  float4 c = shaderTexture.Sample(samplerState, tex);
  ...
}
```

`tex` is 0..1 across the terminal; pixel coords = `tex * Resolution`. Use `Scale` so pixel sizes (border width, sparkle size) look the same on high-DPI.

## Must compile

```
"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\fxc.exe" /nologo /T ps_4_0 /E main /Fo NUL <file>.hlsl
```
Zero errors and zero warnings. ps_4_0 only: no `[unroll]` over huge loops, keep loops small (<= ~16 iterations), no texture arrays, no doubles. Write your own hash/noise functions (no includes).

## The look: Pokemon TCG holofoil, on a terminal

The user lives in this terminal all day (Claude Code, PowerShell), so:

1. **Text stays fully readable.** Treat a pixel as *text* when it differs from `Background.rgb` (e.g. `distance(c.rgb, Background.rgb) > 0.08`, smoothstep it). Text pixels keep their color, at most a very faint foil tint (<= 10%). The foil lives in the *background* pixels.
2. **Background foil is subtle-to-medium**: blend the foil onto the background at roughly 15-35% so it reads as a shimmering card surface behind dark text-free areas, never a blinding wall. Keep the overall background dark (the user's theme is dark; Background is near-black).
3. **A card border frame**: every skin draws a frame around the terminal edge, ~10-14 px * Scale wide, like the yellow/silver/gold edge of a card, with its own foil treatment matching the skin (reverse holo: the frame is the star). Add a thin inner bevel line so it reads as a frame. The frame may be much brighter than the background foil.
4. **Motion**: slow and smooth. A light sweep / hue drift driven by `Time` (period 6-20 s). Nothing flashing faster than ~1 Hz; sparkles may twinkle gently. This must be comfortable for hours.
5. **View-angle illusion**: real holo changes with tilt. Fake it with a slowly moving "light position" (e.g. `float2 light = float2(0.5 + 0.35*sin(Time*0.21), 0.5 + 0.25*cos(Time*0.17))`) that drives hue shift and a soft glare band.
6. Return premultiplied-looking output: `return float4(rgb, 1.0);` is fine.

Put a header comment at the top of each file: skin name, which real card era/finish it imitates, and 1-2 tuning constants the user can tweak (`#define STRENGTH 0.25`, `#define SPEED 1.0`, `#define BORDER_PX 12.0`).

## Deliverable per skin
- the `.hlsl` file, compiled clean with fxc
- in your final report: skin name, one-line description, compile result

## Inset (required): the frame sits outside the text

Windows Terminal's shader only covers the text area (padding is not shaded), so every skin shrinks the
terminal image inward and draws its frame in the freed edge. Never sample `shaderTexture` directly; put this
right after your `#define`s (it needs `BORDER_PX`) and read the terminal only through `TermSample(uv)`:

```hlsl
#define INSET_PX (BORDER_PX + 4.0)
float4 TermSample(float2 uv)
{
  float2 inset = INSET_PX * Scale / Resolution;
  float2 q = (uv - inset) / (1.0 - 2.0 * inset);
  if (any(q < 0.0) || any(q > 1.0)) return Background;
  return shaderTexture.SampleLevel(samplerState, q, 0);
}
```

## Corners

Square frame corners by default. If a skin rounds them, expose `#define CORNER_PX 0.0` and use it as the radius.

## Compile speed

Windows Terminal compiles the shader every time a skinned tab opens, so keep it lean: aim for fxc under ~150 ms
(time it), avoid large unrolled loops and many texture samples.
