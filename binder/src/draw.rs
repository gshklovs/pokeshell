//! Low-level cell painting: btop-style panels, gradient meters, braille graphs, half-block images.
//! Text is measured in terminal cells (unicode-width), not chars: a wide glyph takes two cells, a combining accent none.

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

/// Split a string into terminal cells: (grapheme-ish cluster, cells). A cluster is a base character plus the
/// zero-width characters after it (combining accents, the emoji variation selector, a zero-width joiner and the
/// character it joins), measured with unicode-width: "Flabe\u{301}be\u{301}" is 7 cells, "\u{2640}\u{fe0f}" 2, and
/// "\u{2640}", "●", "✦", "◌" one each (their East Asian width is ambiguous: one cell, as Windows Terminal draws them).
/// Control characters are dropped (they would move the terminal's cursor).
pub fn clusters(s: &str) -> Vec<(&str, usize)> {
    use unicode_width::{UnicodeWidthChar, UnicodeWidthStr};
    let mut out: Vec<(&str, usize)> = Vec::new();
    let mut it = s.char_indices().peekable();
    while let Some((i, c)) = it.next() {
        if c.is_control() {
            continue;
        }
        let mut end = i + c.len_utf8();
        let mut join = c == '\u{200d}';
        while let Some(&(j, d)) = it.peek() {
            let zero = !d.is_control() && UnicodeWidthChar::width(d) == Some(0);
            if zero || join {
                join = d == '\u{200d}';
                end = j + d.len_utf8();
                it.next();
            } else {
                break;
            }
        }
        let g = &s[i..end];
        let w = UnicodeWidthStr::width(g).min(2);
        if w == 0 {
            // a lone combining mark: it rides on the previous cluster, if any
            if let Some(last) = out.last_mut() {
                let start = last.0.as_ptr() as usize - s.as_ptr() as usize;
                *last = (&s[start..end], last.1);
            }
            continue;
        }
        out.push((g, w));
    }
    out
}

/// Write a string, clipped to `max` cells (a wide character that would straddle the limit is left out). Returns the
/// cells written. A wide character's second cell is blanked, as ratatui does (the terminal draws the glyph over it).
pub fn puts(buf: &mut Buffer, x: i32, y: i32, s: &str, fg: Rgb, bg: Option<Rgb>, bold: bool, max: usize) -> usize {
    let mut n = 0;
    for (g, w) in clusters(s) {
        if n + w > max {
            break;
        }
        put(buf, x + n as i32, y, g, Some(fg), bg, bold);
        if w == 2 {
            put(buf, x + n as i32 + 1, y, " ", Some(fg), bg, bold);
        }
        n += w;
    }
    n
}

/// Width in terminal cells.
pub fn width(s: &str) -> usize {
    clusters(s).iter().map(|c| c.1).sum()
}

/// Truncate to `max` cells with an ellipsis.
pub fn trunc(s: &str, max: usize) -> String {
    if width(s) <= max {
        return s.to_string();
    }
    if max == 0 {
        return String::new();
    }
    let mut t = take_cells(s, max - 1);
    // "Evolving…", not "Evolving …"
    while t.ends_with(' ') {
        t.pop();
    }
    t + "…"
}

/// The first `max` cells of a string (no ellipsis).
pub fn take_cells(s: &str, max: usize) -> String {
    let mut t = String::new();
    let mut n = 0;
    for (g, w) in clusters(s) {
        if n + w > max {
            break;
        }
        t.push_str(g);
        n += w;
    }
    t
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

pub fn segs_w(g: &[Seg]) -> usize {
    g.iter().map(|s| width(&s.text)).sum()
}

/// Cells a row of title groups takes: `┐group┌` each, one cell between groups.
pub fn groups_w(groups: &[Vec<Seg>]) -> usize {
    groups.iter().map(|g| segs_w(g) + 2).sum::<usize>() + groups.len().saturating_sub(1)
}

/// The groups that fit in `avail` cells, in priority order (the first group matters most): the group that doesn't fit
/// is cut with an ellipsis (`cut`, when the first, or when 8+ cells are left for it), the ones after it dropped.
fn fit_groups(groups: &[Vec<Seg>], avail: usize, cut: bool) -> Vec<Vec<Seg>> {
    let mut out: Vec<Vec<Seg>> = Vec::new();
    for g in groups {
        let mut try_ = out.clone();
        try_.push(g.clone());
        if groups_w(&try_) <= avail {
            out = try_;
        } else {
            let left = if out.is_empty() { avail } else { avail.saturating_sub(groups_w(&out) + 1) };
            if cut && ((out.is_empty() && avail >= 5) || left >= 8) {
                // cut the group's text from its end
                let mut room = left - 2;
                let mut cut: Vec<Seg> = Vec::new();
                for s in g {
                    if room == 0 {
                        break;
                    }
                    let w = width(&s.text);
                    if w <= room {
                        room -= w;
                        cut.push(s.clone());
                    } else {
                        cut.push(Seg { text: trunc(&s.text, room), ..s.clone() });
                        room = 0;
                    }
                }
                out.push(cut);
            }
            break;
        }
    }
    out
}

/// Draw title groups into a border row: `┐group┌` pieces (btop style), inside [x0, x1). Returns each drawn group's
/// text range.
fn edge_groups(buf: &mut Buffer, y: i32, x0: i32, groups: &[Vec<Seg>], line: Rgb, top: bool) -> Vec<(i32, i32)> {
    let (l, r) = if top { ("┐", "┌") } else { ("┘", "└") };
    let mut out = Vec::new();
    let mut x = x0;
    for (gi, g) in groups.iter().enumerate() {
        if gi > 0 {
            x += 1;
        }
        put(buf, x, y, l, Some(line), None, false);
        let start = x + 1;
        let mut cx = start;
        for s in g {
            cx += puts(buf, cx, y, &s.text, s.fg, s.bg, s.bold, usize::MAX) as i32;
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

/// Rounded panel with titles embedded in the border. The left groups have priority: the right ones get the room
/// that is left (never overlapping), and groups that don't fit are dropped from the end. Returns the x-ranges of the
/// drawn top-left groups (mouse hit-testing of the pack and set tabs), the x-range of the drawn bottom-right groups
/// (the page arrows) and the inner rect.
pub fn panel(buf: &mut Buffer, r: Rect, line: Rgb, bg: Option<Rgb>, t: &Titles) -> (Vec<(i32, i32)>, Rect) {
    panel_ex(buf, r, line, bg, t).0
}

pub fn panel_ex(buf: &mut Buffer, r: Rect, line: Rgb, bg: Option<Rgb>, t: &Titles) -> ((Vec<(i32, i32)>, Rect), Option<(i32, i32)>) {
    if r.width < 2 || r.height < 2 {
        return ((vec![], Rect::default()), None);
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
    // the border row between the corners, one cell kept free next to each corner
    let span = (x1 - x0 - 1).max(0) as usize;
    let (tl, _) = draw_row(buf, span, x0, x1, y0, &t.tl, &t.tr, line, true);
    let (_, brr) = draw_row(buf, span, x0, x1, y1, &t.bl, &t.br, line, false);
    ((tl, Rect::new(r.x + 1, r.y + 1, r.width - 2, r.height - 2)), brr)
}

/// One border row: the left groups from x0 + 1, the right ones ending at x1 - 1 with whatever room is left (one
/// cell apart from the left ones), never overlapping.
#[allow(clippy::too_many_arguments)]
fn draw_row(buf: &mut Buffer, span: usize, x0: i32, x1: i32, y: i32, left: &[Vec<Seg>], right: &[Vec<Seg>], line: Rgb, top: bool) -> (Vec<(i32, i32)>, Option<(i32, i32)>) {
    let l = fit_groups(left, span.saturating_sub(1), true);
    let lw = if l.is_empty() { 0 } else { groups_w(&l) + 1 };
    let ravail = span.saturating_sub(lw + 1 + usize::from(lw > 0));
    let rg = fit_groups(right, ravail, false);
    let lr = edge_groups(buf, y, x0 + 1, &l, line, top);
    let rr = if rg.is_empty() {
        None
    } else {
        let rx = x1 - 1 - groups_w(&rg) as i32;
        let v = edge_groups(buf, y, rx, &rg, line, top);
        Some((v.first().map(|a| a.0).unwrap_or(rx), v.last().map(|a| a.1).unwrap_or(rx)))
    };
    (lr, rr)
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

/// A meter as title segments (the set tab and the binder's completion line live in borders).
pub fn meter_segs(w: usize, frac: f32, stops: &[Rgb], empty: Rgb) -> Vec<Seg> {
    let filled = frac.clamp(0.0, 1.0) * w as f32;
    (0..w)
        .map(|i| {
            let t = if w > 1 { i as f32 / (w - 1) as f32 } else { 1.0 };
            let c = grad(stops, t);
            let f = filled - i as f32;
            let fg = if f >= 0.75 || (i == 0 && frac > 0.0) {
                c
            } else if f > 0.25 {
                mix(empty, c, 0.5)
            } else {
                empty
            };
            seg("■", fg)
        })
        .collect()
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cell_widths() {
        assert_eq!(width("Pikachu"), 7);
        assert_eq!(width("Nidoran ♀"), 9, "♀ is one cell (ambiguous width, as Windows Terminal draws it)");
        assert_eq!(width("●✦◌"), 3);
        assert_eq!(width("Flabe\u{301}be\u{301}"), 7, "combining accents take no cell");
        assert_eq!(width("ピカチュウ"), 10, "CJK is two cells each");
        assert_eq!(width("\u{2640}\u{fe0f}"), 2, "emoji presentation");
        assert_eq!(width("a\tb"), 2, "control characters are dropped");
        assert_eq!(trunc("ピカチュウ", 5), "ピカ…");
        assert_eq!(width(&trunc("ピカチュウ", 6)), 5, "a wide char never straddles the limit");
        assert_eq!(trunc("Evolving Skies", 10), "Evolving…");
        assert_eq!(trunc("abc", 3), "abc");
    }

    #[test]
    fn puts_wide() {
        let mut b = Buffer::empty(Rect::new(0, 0, 8, 1));
        let n = puts(&mut b, 0, 0, "ピカa", [255, 255, 255], None, false, 8);
        assert_eq!(n, 5);
        assert_eq!(b[(0, 0)].symbol(), "ピ");
        assert_eq!(b[(2, 0)].symbol(), "カ");
        assert_eq!(b[(4, 0)].symbol(), "a");
        let n = puts(&mut b, 0, 0, "ピカ", [255, 255, 255], None, false, 3);
        assert_eq!(n, 2, "the second wide char would straddle the limit");
    }

    #[test]
    fn titles_never_overlap() {
        let mut b = Buffer::empty(Rect::new(0, 0, 44, 3));
        let mut t = Titles::new();
        t.tl.push(vec![seg("¹pokemon", [1, 1, 1])]);
        t.tl.push(vec![seg("S Evolving Skies", [1, 1, 1])]);
        t.tr.push(vec![seg("cards", [1, 1, 1])]);
        let (tabs, _) = panel(&mut b, Rect::new(0, 0, 44, 3), [9, 9, 9], None, &t);
        let top: String = (0..44).map(|x| b[(x, 0)].symbol().to_string()).collect();
        assert_eq!(tabs.len(), 2);
        assert!(top.contains("cards"), "{top}");
        assert!(!top.contains("┌┐") && !top.contains("┌┌"), "{top}");
        // too narrow for the right group: it is dropped, the left ones stay whole
        let mut b = Buffer::empty(Rect::new(0, 0, 30, 3));
        let (tabs, _) = panel(&mut b, Rect::new(0, 0, 30, 3), [9, 9, 9], None, &t);
        let top: String = (0..30).map(|x| b[(x, 0)].symbol().to_string()).collect();
        assert_eq!(tabs.len(), 2, "{top}");
        assert!(!top.contains("cards"), "{top}");
    }
}
