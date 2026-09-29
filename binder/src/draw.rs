//! Low-level cell painting: btop-style panels, gradient meters, braille graphs, half-block images.

use crate::art::Img;
use crate::color::{Rgb, col, grad, mix};
use ratatui::buffer::Buffer;
use ratatui::layout::Rect;
use ratatui::style::{Color, Modifier};

#[inline]
pub fn put(buf: &mut Buffer, x: i32, y: i32, sym: &str, fg: Option<Rgb>, bg: Option<Rgb>, bold: bool) {
    if x < 0 || y < 0 {
        return;
    }
    let a = buf.area;
    let (x, y) = (x as u16, y as u16);
    if x < a.x || y < a.y || x >= a.x + a.width || y >= a.y + a.height {
        return;
    }
    let c = &mut buf[(x, y)];
    c.set_symbol(sym);
    if let Some(f) = fg {
        c.fg = col(f);
    }
    if let Some(b) = bg {
        c.bg = col(b);
    }
    if bold {
        c.modifier.insert(Modifier::BOLD);
    } else {
        c.modifier.remove(Modifier::BOLD);
    }
}

#[inline]
pub fn putc(buf: &mut Buffer, x: i32, y: i32, ch: char, fg: Option<Rgb>, bg: Option<Rgb>, bold: bool) {
    let mut t = [0u8; 4];
    put(buf, x, y, ch.encode_utf8(&mut t), fg, bg, bold);
}

/// Write a string (one cell per char), clipped to `max` cells. Returns cells written.
pub fn puts(buf: &mut Buffer, x: i32, y: i32, s: &str, fg: Rgb, bg: Option<Rgb>, bold: bool, max: usize) -> usize {
    let mut n = 0;
    for ch in s.chars() {
        if n >= max {
            break;
        }
        putc(buf, x + n as i32, y, ch, Some(fg), bg, bold);
        n += 1;
    }
    n
}

pub fn width(s: &str) -> usize {
    s.chars().count()
}

/// Truncate to `max` cells with an ellipsis.
pub fn trunc(s: &str, max: usize) -> String {
    if width(s) <= max {
        s.to_string()
    } else if max == 0 {
        String::new()
    } else {
        let mut t: String = s.chars().take(max - 1).collect();
        t.push('…');
        t
    }
}

pub fn fill(buf: &mut Buffer, r: Rect, bg: Option<Rgb>) {
    let r = r.intersection(buf.area);
    for y in r.y..r.y + r.height {
        for x in r.x..r.x + r.width {
            let c = &mut buf[(x, y)];
            c.set_symbol(" ");
            c.modifier = Modifier::empty();
            c.bg = bg.map(col).unwrap_or(Color::Reset);
        }
    }
}

/// A styled run of text inside a border title.
#[derive(Clone)]
pub struct Seg {
    pub text: String,
    pub fg: Rgb,
    pub bold: bool,
    pub bg: Option<Rgb>,
}

pub fn seg(text: impl Into<String>, fg: Rgb) -> Seg {
    Seg { text: text.into(), fg, bold: false, bg: None }
}
pub fn segb(text: impl Into<String>, fg: Rgb) -> Seg {
    Seg { text: text.into(), fg, bold: true, bg: None }
}

fn segs_w(g: &[Seg]) -> usize {
    g.iter().map(|s| width(&s.text)).sum()
}

/// Draw title groups into a border row: `┐group┌` pieces (btop style). Returns the x range of each group.
fn edge_groups(buf: &mut Buffer, y: i32, x0: i32, x1: i32, groups: &[Vec<Seg>], line: Rgb, top: bool, right: bool) -> Vec<(i32, i32)> {
    let (l, r) = if top { ("┐", "┌") } else { ("┘", "└") };
    let mut out = Vec::new();
    let total: i32 = groups.iter().map(|g| segs_w(g) as i32 + 2).sum::<i32>() + groups.len().saturating_sub(1) as i32;
    let mut x = if right { x1 - total } else { x0 };
    if x < x0 {
        x = x0;
    }
    for (gi, g) in groups.iter().enumerate() {
        if gi > 0 {
            x += 1;
        }
        if x + 2 > x1 {
            break;
        }
        put(buf, x, y, l, Some(line), None, false);
        let start = x + 1;
        let mut cx = start;
        for s in g {
            for ch in s.text.chars() {
                if cx >= x1 - 1 {
                    break;
                }
                putc(buf, cx, y, ch, Some(s.fg), s.bg, s.bold);
                cx += 1;
            }
        }
        put(buf, cx, y, r, Some(line), None, false);
        out.push((start, cx));
        x = cx + 1;
    }
    out
}

pub struct Titles {
    pub tl: Vec<Vec<Seg>>,
    pub tr: Vec<Vec<Seg>>,
    pub bl: Vec<Vec<Seg>>,
    pub br: Vec<Vec<Seg>>,
}

impl Titles {
    pub fn new() -> Self {
        Titles { tl: vec![], tr: vec![], bl: vec![], br: vec![] }
    }
}

/// Rounded panel with titles embedded in the border. Returns the x-ranges of the top-left groups
/// (for mouse hit-testing of the pack tabs) and the inner rect.
pub fn panel(buf: &mut Buffer, r: Rect, line: Rgb, bg: Option<Rgb>, t: &Titles) -> (Vec<(i32, i32)>, Rect) {
    if r.width < 2 || r.height < 2 {
        return (vec![], Rect::default());
    }
    let (x0, y0, x1, y1) = (r.x as i32, r.y as i32, (r.x + r.width - 1) as i32, (r.y + r.height - 1) as i32);
    fill(buf, r, bg);
    for x in x0 + 1..x1 {
        put(buf, x, y0, "─", Some(line), None, false);
        put(buf, x, y1, "─", Some(line), None, false);
    }
    for y in y0 + 1..y1 {
        put(buf, x0, y, "│", Some(line), None, false);
        put(buf, x1, y, "│", Some(line), None, false);
    }
    put(buf, x0, y0, "╭", Some(line), None, false);
    put(buf, x1, y0, "╮", Some(line), None, false);
    put(buf, x0, y1, "╰", Some(line), None, false);
    put(buf, x1, y1, "╯", Some(line), None, false);
    let tabs = edge_groups(buf, y0, x0 + 1, x1, &t.tl, line, true, false);
    edge_groups(buf, y0, x0 + 1, x1 - 1, &t.tr, line, true, true);
    edge_groups(buf, y1, x0 + 1, x1, &t.bl, line, false, false);
    edge_groups(buf, y1, x0 + 1, x1 - 1, &t.br, line, false, true);
    (tabs, Rect::new(r.x + 1, r.y + 1, r.width - 2, r.height - 2))
}

/// btop meter: a row of ■ colored along the gradient; the unfilled rest in `empty`.
pub fn meter(buf: &mut Buffer, x: i32, y: i32, w: usize, frac: f32, stops: &[Rgb], empty: Rgb) {
    if w == 0 {
        return;
    }
    let filled = frac.clamp(0.0, 1.0) * w as f32;
    for i in 0..w {
        let t = if w > 1 { i as f32 / (w - 1) as f32 } else { 1.0 };
        let c = grad(stops, t);
        let f = filled - i as f32;
        if f >= 0.75 || (i == 0 && frac > 0.0) {
            put(buf, x + i as i32, y, "■", Some(c), None, false);
        } else if f > 0.25 {
            put(buf, x + i as i32, y, "■", Some(mix(empty, c, 0.5)), None, false);
        } else {
            put(buf, x + i as i32, y, "■", Some(empty), None, false);
        }
    }
}

/// Braille area graph: `vals` in 0..=1, two samples per cell column, filled from the bottom,
/// each row colored from the gradient (bottom = stops[0]).
pub fn braille(buf: &mut Buffer, r: Rect, vals: &[f32], stops: &[Rgb], base: Option<Rgb>) {
    let rows = r.height as usize;
    if rows == 0 {
        return;
    }
    const L: [u32; 4] = [0x40, 0x04, 0x02, 0x01]; // bottom -> top, left column (dots 7,3,2,1)
    const R: [u32; 4] = [0x80, 0x20, 0x10, 0x08]; // right column (dots 8,6,5,4)
    let dots = |v: f32| -> usize {
        let d = (v.clamp(0.0, 1.0) * (rows * 4) as f32).round() as usize;
        if v > 0.0 { d.max(1) } else { 0 }
    };
    for cx in 0..r.width as usize {
        let hl = dots(vals.get(cx * 2).copied().unwrap_or(0.0));
        let hr = dots(vals.get(cx * 2 + 1).copied().unwrap_or(0.0));
        for row in 0..rows {
            let (nl, nr) = (hl.saturating_sub(row * 4).min(4), hr.saturating_sub(row * 4).min(4));
            let y = r.y as i32 + (rows - 1 - row) as i32;
            let x = r.x as i32 + cx as i32;
            if nl == 0 && nr == 0 {
                if row == 0 {
                    if let Some(b) = base {
                        put(buf, x, y, "⣀", Some(b), None, false);
                    }
                }
                continue;
            }
            let mut code = 0x2800u32;
            for k in 0..nl {
                code |= L[k];
            }
            for k in 0..nr {
                code |= R[k];
            }
            let t = if rows > 1 { row as f32 / (rows - 1) as f32 } else { 0.5 };
            let ch = char::from_u32(code).unwrap_or(' ');
            putc(buf, x, y, ch, Some(grad(stops, t)), None, false);
        }
    }
}

/// Paint a pixel image with half-blocks at (x, y). `map` can recolor each pixel (silhouettes,
/// pending desaturation). Transparent pixels show `bg`.
pub fn image(buf: &mut Buffer, x: i32, y: i32, img: &Img, bg: Rgb, map: &dyn Fn(Rgb) -> Rgb) {
    for row in 0..img.rows() {
        for cx in 0..img.w {
            let t = img.get(cx, row * 2).map(map);
            let b = img.get(cx, row * 2 + 1).map(map);
            let (sym, fg, bgc) = match (t, b) {
                (None, None) => continue,
                (Some(t), None) => ("▀", t, bg),
                (None, Some(b)) => ("▄", b, bg),
                (Some(t), Some(b)) if t == b => ("█", t, bg),
                (Some(t), Some(b)) => ("▀", t, b),
            };
            put(buf, x + cx as i32, y + row as i32, sym, Some(fg), Some(bgc), false);
        }
    }
}

/// Recolor every cell of a rect (fg and bg) — used for foil shimmer sweeps and dimming under overlays.
pub fn recolor(buf: &mut Buffer, r: Rect, f: &dyn Fn(i32, i32, Rgb) -> Rgb) {
    let r = r.intersection(buf.area);
    for y in r.y..r.y + r.height {
        for x in r.x..r.x + r.width {
            let c = &mut buf[(x, y)];
            if let Color::Rgb(a, b, d) = c.fg {
                let n = f(x as i32, y as i32, [a, b, d]);
                c.fg = col(n);
            }
            if let Color::Rgb(a, b, d) = c.bg {
                let n = f(x as i32, y as i32, [a, b, d]);
                c.bg = col(n);
            }
        }
    }
}
