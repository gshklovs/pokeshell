//! Tiny truecolor helpers: everything is `[u8; 3]` until it reaches a ratatui `Color`.

use ratatui::style::Color;

pub type Rgb = [u8; 3];

pub fn hex(s: &str) -> Option<Rgb> {
    let s = s.trim().trim_start_matches('#');
    // (a byte-length check alone would let a non-ASCII string through, and slicing it could split a character)
    if s.len() != 6 || !s.bytes().all(|b| b.is_ascii_hexdigit()) {
        return None;
    }
    let p = |i: usize| u8::from_str_radix(s.get(i..i + 2)?, 16).ok();
    Some([p(0)?, p(2)?, p(4)?])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hex_colors() {
        assert_eq!(hex("#ff5fa2"), Some([0xff, 0x5f, 0xa2]));
        assert_eq!(hex(" 0c0e16 "), Some([0x0c, 0x0e, 0x16]));
        assert_eq!(hex("#ff5fa"), None);
        assert_eq!(hex("#gg0000"), None);
        assert_eq!(hex("ééé"), None, "6 bytes of non-ASCII: no panic on a char boundary");
        assert_eq!(hex("+12345"), None, "from_str_radix would take a sign");
    }
}

/// `hex` for string literals we own (panics are compile-time-obvious typos).
pub const fn rgb(v: u32) -> Rgb {
    [(v >> 16) as u8, (v >> 8) as u8, v as u8]
}

#[inline]
pub fn col(c: Rgb) -> Color {
    Color::Rgb(c[0], c[1], c[2])
}

#[inline]
pub fn mix(a: Rgb, b: Rgb, t: f32) -> Rgb {
    let t = t.clamp(0.0, 1.0);
    let f = |x: u8, y: u8| (x as f32 + (y as f32 - x as f32) * t + 0.5) as u8;
    [f(a[0], b[0]), f(a[1], b[1]), f(a[2], b[2])]
}

/// Sample a multi-stop gradient at t in 0..=1.
pub fn grad(stops: &[Rgb], t: f32) -> Rgb {
    match stops.len() {
        0 => [200, 200, 200],
        1 => stops[0],
        n => {
            let t = t.clamp(0.0, 1.0) * (n - 1) as f32;
            let i = (t as usize).min(n - 2);
            mix(stops[i], stops[i + 1], t - i as f32)
        }
    }
}

pub fn lighten(c: Rgb, t: f32) -> Rgb {
    mix(c, [255, 255, 255], t)
}

pub fn darken(c: Rgb, t: f32) -> Rgb {
    mix(c, [0, 0, 0], t)
}

pub fn luma(c: Rgb) -> f32 {
    (0.2126 * c[0] as f32 + 0.7152 * c[1] as f32 + 0.0722 * c[2] as f32) / 255.0
}

/// Desaturate toward grey by t.
pub fn desat(c: Rgb, t: f32) -> Rgb {
    let l = (luma(c) * 255.0) as u8;
    mix(c, [l, l, l], t)
}

/// Hue rotation-ish rainbow for iridescent sheens (t wraps).
pub fn rainbow(t: f32) -> Rgb {
    const R: [Rgb; 7] = [
        rgb(0xff6b8b),
        rgb(0xffb86b),
        rgb(0xffe66b),
        rgb(0x7df09a),
        rgb(0x6bd5ff),
        rgb(0x9a8bff),
        rgb(0xff6bd6),
    ];
    let t = t.rem_euclid(1.0);
    let n = R.len() as f32;
    let x = t * n;
    let i = x as usize % R.len();
    mix(R[i], R[(i + 1) % R.len()], x - x.floor())
}

/// Deterministic 0..1 noise from integer coordinates and a seed.
pub fn noise(x: i32, y: i32, seed: u32) -> f32 {
    let mut h = (x as u32).wrapping_mul(0x27d4_eb2d) ^ (y as u32).wrapping_mul(0x1656_67b1) ^ seed.wrapping_mul(0x9e37_79b9);
    h ^= h >> 15;
    h = h.wrapping_mul(0x85eb_ca6b);
    h ^= h >> 13;
    h = h.wrapping_mul(0xc2b2_ae35);
    h ^= h >> 16;
    (h & 0xffff) as f32 / 65535.0
}

pub fn str_seed(s: &str) -> u32 {
    s.bytes().fold(2166136261u32, |h, b| (h ^ b as u32).wrapping_mul(16777619))
}
