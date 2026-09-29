//! A card: pixel art inside its tier frame. The same code draws binder thumbnails and the big
//! detail card, a port of the rounded gradient frame and the wanted poster in scripts/lib/Pokeshell.cs.

use crate::art::Img;
use crate::color::{Rgb, darken, desat, grad, hex, lighten, mix, noise, rainbow, rgb, str_seed};
use crate::data::{FrameSpec, Pack, SlotState};
use crate::draw::{fill, image, put, putc, trunc, width};
use crate::theme::Theme;
use ratatui::buffer::Buffer;
use ratatui::layout::Rect;

pub struct Card<'a> {
    pub pack: &'a Pack,
    pub ch: usize,
    pub tier: usize,
    pub shiny: bool,
    pub state: SlotState,
    pub selected: bool,
    pub count: usize,
    /// Thumbnail (binder slot) vs the big detail card.
    pub thumb: bool,
    /// An earned pull not viewed yet: the NEW sticker.
    pub new: bool,
}

/// How much room the frame takes around the art: (cols, rows).
pub fn frame_pad(frame: &FrameSpec, thumb: bool) -> (usize, usize) {
    match (frame, thumb) {
        (FrameSpec::Box(_), false) => (4, 2),
        (FrameSpec::Box(_), true) => (2, 2),
        (FrameSpec::Wanted(_), false) => (4, 3),
        (FrameSpec::Wanted(_), true) => (2, 2),
    }
}

/// Big-card size for an art image (the frame grows to fit its edge texts).
pub fn card_size(c: &Card, img_w: usize, img_rows: usize) -> (u16, u16) {
    let t = &c.pack.tiers[c.tier];
    let (pw, ph) = frame_pad(&t.frame, false);
    let ch = &c.pack.chars[c.ch];
    let min_w = match &t.frame {
        FrameSpec::Box(_) => {
            let title = width(&c.pack.slot_name(c.ch, c.tier)) + if c.shiny { 2 } else { 0 };
            let tag = width(&c.pack.slot_tag(c.ch, c.tier));
            (title + 2 + if tag > 0 { tag + 2 } else { 0 } + 3).max(width(&t.label) + 5)
        }
        FrameSpec::Wanted(_) => {
            let poster = width(&c.pack.poster_of(ch)) + 6;
            let bounty = c.pack.bounty_of(ch);
            let bot = if bounty.is_empty() { 0 } else { width(bounty) + 3 } + width(&t.label) + 4;
            poster.max(bot).max(17)
        }
    };
    (((img_w + pw).max(min_w)) as u16, (img_rows + ph) as u16)
}

fn stops_of(frame: &FrameSpec) -> Vec<Rgb> {
    match frame {
        FrameSpec::Box(s) => s.clone(),
        FrameSpec::Wanted(p) => match p.as_str() {
            "secret-rare" => GOLD_LEAF.iter().map(|&v| rgb(v)).collect(),
            _ => vec![wanted_pal(p).0, wanted_pal(p).1],
        },
    }
}

/// Is this card a foil (gets the shimmer)?
pub fn is_foil(pack: &Pack, tier: usize, shiny: bool) -> bool {
    pack.foil_tier(tier) || shiny
}

/// The interior color behind transparent art pixels.
fn interior(theme: &Theme, frame: &FrameSpec, tier: usize, x: f32, y: f32) -> Rgb {
    if tier == 0 {
        return theme.card_bg;
    }
    let stops = stops_of(frame);
    let t = (x * 0.7 + y * 0.3).clamp(0.0, 1.0);
    mix(theme.card_bg, darken(grad(&stops, t), 0.35), 0.16)
}

pub fn draw(buf: &mut Buffer, r: Rect, c: &Card, img: Option<&Img>, theme: &Theme) {
    if r.width < 4 || r.height < 3 {
        return;
    }
    let t = &c.pack.tiers[c.tier];
    match (&t.frame, c.state) {
        (_, SlotState::Empty) => draw_empty(buf, r, c, img, theme),
        (FrameSpec::Box(stops), _) => draw_box(buf, r, c, img, stops, theme),
        (FrameSpec::Wanted(pal), _) => draw_wanted(buf, r, c, img, pal, theme),
    }
    if c.new && c.state == SlotState::Owned {
        sticker(buf, r, c.thumb);
    }
}

/// The NEW sticker: a bright tab on the card's top-right edge (earned, not viewed yet).
pub fn sticker(buf: &mut Buffer, r: Rect, thumb: bool) {
    let label = if thumb || r.width < 14 { "NEW" } else { " NEW " };
    if (r.width as usize) < width(label) + 4 {
        return;
    }
    let x = (r.x + r.width) as i32 - 2 - width(label) as i32;
    for (i, ch) in label.chars().enumerate() {
        putc(buf, x + i as i32, r.y as i32, ch, Some(rgb(0x1a1020)), Some(rgb(0xff5fa2)), true);
    }
}

fn art_origin(r: Rect, img: &Img, px: usize, py: usize, top_pad: usize) -> (i32, i32) {
    let iw = r.width as usize - px;
    let ih = r.height as usize - py;
    let x = r.x as usize + px / 2 + iw.saturating_sub(img.w) / 2;
    let y = r.y as usize + top_pad + ih.saturating_sub(img.rows()) / 2;
    (x as i32, y as i32)
}

// ---------------------------------------------------------------- empty slot

fn draw_empty(buf: &mut Buffer, r: Rect, c: &Card, img: Option<&Img>, theme: &Theme) {
    let (x0, y0, x1, y1) = (r.x as i32, r.y as i32, (r.x + r.width - 1) as i32, (r.y + r.height - 1) as i32);
    let line = if c.selected { mix(theme.slot_line, theme.hi, 0.7) } else { theme.slot_line };
    fill(buf, r, theme.bg);
    for x in x0 + 1..x1 {
        put(buf, x, y0, "┄", Some(line), None, false);
        put(buf, x, y1, "┄", Some(line), None, false);
    }
    for y in y0 + 1..y1 {
        put(buf, x0, y, "┆", Some(line), None, false);
        put(buf, x1, y, "┆", Some(line), None, false);
    }
    put(buf, x0, y0, "╭", Some(line), None, false);
    put(buf, x1, y0, "╮", Some(line), None, false);
    put(buf, x0, y1, "╰", Some(line), None, false);
    put(buf, x1, y1, "╯", Some(line), None, false);
    let bg = theme.bg.unwrap_or(theme.bg_guess);
    let sil = if c.selected { mix(theme.silhouette, theme.hi, 0.12) } else { theme.silhouette };
    if let Some(img) = img {
        let (ax, ay) = art_origin(r, img, 2, 2, 1);
        image(buf, ax, ay, img, bg, &|_| sil);
    }
    let q = "?";
    let (cx, cy) = (x0 + (r.width as i32 - 1) / 2, y0 + (r.height as i32 - 1) / 2);
    if img.is_none() {
        put(buf, cx, cy, q, Some(theme.faint), None, true);
    }
    let _ch = &c.pack.chars[c.ch];
    let tag = c.pack.slot_tag(c.ch, c.tier);
    let dim = if c.selected { theme.dim } else { theme.faint };
    let label = if !tag.is_empty() { tag.to_string() } else { "???".into() };
    let w = r.width as usize;
    let l = trunc(&label, w.saturating_sub(4));
    crate::draw::puts(buf, x0 + 2, y1, &l, dim, None, false, w.saturating_sub(4));
    if w > 12 {
        let tl = trunc(&c.pack.tiers[c.tier].label, w.saturating_sub(width(&l) + 7));
        let tx = x1 - 1 - width(&tl) as i32;
        crate::draw::puts(buf, tx, y1, &tl, dim, None, false, 40);
    }
    if c.selected {
        let name = trunc(&c.pack.slot_name(c.ch, c.tier), w.saturating_sub(4));
        crate::draw::puts(buf, x0 + 2, y0, &name, theme.dim, None, false, w - 4);
    }
}

// ---------------------------------------------------------------- rounded gradient frame

fn draw_box(buf: &mut Buffer, r: Rect, c: &Card, img: Option<&Img>, stops: &[Rgb], theme: &Theme) {
    let (x0, y0, x1, y1) = (r.x as i32, r.y as i32, (r.x + r.width - 1) as i32, (r.y + r.height - 1) as i32);
    let (w, h) = (r.width as f32, r.height as f32);
    let pending = c.state == SlotState::Pending;
    let tone = |col: Rgb| -> Rgb {
        let col = if pending { darken(desat(col, 0.75), 0.35) } else { col };
        if c.selected { mix(col, theme.hi, 0.0) } else { col }
    };
    let edge = |t: f32| -> Rgb {
        let e = grad(stops, t);
        let e = if c.thumb && !c.selected { darken(e, 0.12) } else { e };
        tone(e)
    };
    // interior
    for y in y0 + 1..y1 {
        for x in x0 + 1..x1 {
            let bg = interior(theme, &c.pack.tiers[c.tier].frame, c.tier, (x - x0) as f32 / w, (y - y0) as f32 / h);
            put(buf, x, y, " ", None, Some(tone(bg)), false);
        }
    }
    let (hz, vt) = if pending { ("┄", "┆") } else { ("─", "│") };
    for x in x0..=x1 {
        let u = (x - x0) as f32 / (w - 1.0).max(1.0);
        put(buf, x, y0, hz, Some(edge(0.5 * u)), Some(theme_bg(theme)), false);
        put(buf, x, y1, hz, Some(edge(0.5 + 0.5 * u)), Some(theme_bg(theme)), false);
    }
    for y in y0..=y1 {
        let v = (y - y0) as f32 / (h - 1.0).max(1.0);
        put(buf, x0, y, vt, Some(edge(0.5 * v)), Some(theme_bg(theme)), false);
        put(buf, x1, y, vt, Some(edge(0.5 * v + 0.5)), Some(theme_bg(theme)), false);
    }
    put(buf, x0, y0, "╭", Some(edge(0.0)), None, false);
    put(buf, x1, y0, "╮", Some(edge(0.5)), None, false);
    put(buf, x0, y1, "╰", Some(edge(0.5)), None, false);
    put(buf, x1, y1, "╯", Some(edge(1.0)), None, false);

    if let Some(img) = img {
        let (pw, ph) = frame_pad(&c.pack.tiers[c.tier].frame, c.thumb);
        let (ax, ay) = art_origin(r, img, pw, ph, 1);
        // interior color at the art's own cells, so transparent pixels blend into the tinted card stock
        for row in 0..img.rows() {
            for cx in 0..img.w {
                let (x, y) = (ax + cx as i32, ay + row as i32);
                let bg = tone(interior(theme, &c.pack.tiers[c.tier].frame, c.tier, (x - x0) as f32 / w, (y - y0) as f32 / h));
                let t = img.get(cx, row * 2).map(tone);
                let b = img.get(cx, row * 2 + 1).map(tone);
                let (sym, fg, bgc) = match (t, b) {
                    (None, None) => continue,
                    (Some(t), None) => ("▀", t, bg),
                    (None, Some(b)) => ("▄", b, bg),
                    (Some(t), Some(b)) if t == b => ("█", t, bg),
                    (Some(t), Some(b)) => ("▀", t, b),
                };
                put(buf, x, y, sym, Some(fg), Some(bgc), false);
            }
        }
    }

    // edge texts
    let _ch = &c.pack.chars[c.ch];
    let rw = r.width as usize;
    let text_col = |t: f32, bold: bool| -> Rgb {
        let e = grad(stops, t);
        if bold { lighten(e, 0.45) } else { lighten(e, 0.15) }
    };
    let tier = &c.pack.tiers[c.tier];
    if c.thumb {
        // top: name; bottom: ×count left, tier label right
        let name = c.pack.slot_name(c.ch, c.tier);
        let room = rw.saturating_sub(4 + if c.shiny { 2 } else { 0 } + if c.new && !pending { 4 } else { 0 });
        let name = trunc(&name, room);
        let mut tx = x0 + 1;
        let (nfg, nbg) = if c.selected { (theme_bg(theme), Some(theme.hi)) } else { (tone(text_col(0.2, true)), None) };
        put(buf, tx, y0, " ", None, nbg, false);
        tx += 1;
        if c.shiny {
            put(buf, tx, y0, "✦", Some(if c.selected { nfg } else { theme.hi }), nbg, true);
            tx += 1;
            put(buf, tx, y0, " ", None, nbg, false);
            tx += 1;
        }
        tx += crate::draw::puts(buf, tx, y0, &name, nfg, nbg, true, room) as i32;
        put(buf, tx, y0, " ", None, nbg, false);
        let left = if pending { "◌ pending".to_string() } else if c.count > 1 { format!("×{}", c.count) } else { String::new() };
        let mut used = 0;
        if !left.is_empty() && rw > 8 {
            let l = trunc(&left, rw - 4);
            put(buf, x0 + 1, y1, " ", None, None, false);
            used = crate::draw::puts(buf, x0 + 2, y1, &l, if pending { theme.warn } else { theme.fg }, None, !pending, rw - 4) + 2;
            put(buf, x0 + 2 + used as i32 - 2, y1, " ", None, None, false);
        }
        let room = rw.saturating_sub(used + 5);
        if room >= 4 && !pending {
            let lab = trunc(&tier.label, room);
            let lx = x1 - 2 - width(&lab) as i32;
            put(buf, lx - 1, y1, " ", None, None, false);
            crate::draw::puts(buf, lx, y1, &lab, tone(text_col(0.9, false)), None, false, room);
            put(buf, x1 - 2, y1, " ", None, None, false);
        }
    } else {
        let title = format!("{}{}", if c.shiny { "✦ " } else { "" }, c.pack.slot_name(c.ch, c.tier));
        let tag = c.pack.slot_tag(c.ch, c.tier);
        edge_text(buf, x0 + 2, y0, &format!(" {title} "), tone(text_col(0.15, true)), true);
        if !tag.is_empty() {
            let s = format!(" {tag} ");
            edge_text(buf, x1 - 1 - width(&s) as i32, y0, &s, tone(text_col(0.45, false)), false);
        }
        let bottom = format!(" {}{} ", tier.label, if c.shiny { " ✦ shiny" } else { "" });
        edge_text(buf, x1 - 1 - width(&bottom) as i32, y1, &bottom, tone(text_col(0.95, true)), true);
        if pending {
            edge_text(buf, x0 + 2, y1, " ◌ pending ", theme.warn, true);
        }
    }
}

fn theme_bg(theme: &Theme) -> Rgb {
    theme.bg.unwrap_or(theme.bg_guess)
}

fn edge_text(buf: &mut Buffer, x: i32, y: i32, s: &str, fg: Rgb, bold: bool) {
    for (i, ch) in s.chars().enumerate() {
        putc(buf, x + i as i32, y, ch, Some(fg), None, bold);
    }
}

// ---------------------------------------------------------------- wanted poster

const GOLD_LEAF: [u32; 6] = [0xc8952e, 0xf6dc7a, 0xfff3c4, 0xe2b24a, 0xf8e08a, 0xc8952e];

/// paper, stain, ink, accent ("" paper = gold leaf)
fn wanted_pal(p: &str) -> (Rgb, Rgb, Rgb, Rgb) {
    let h = |s: &str| hex(s).unwrap();
    match p {
        "super-rare" => (h("#cfa467"), h("#9c7040"), h("#2a170a"), h("#8e1b12")),
        "secret-rare" => (h("#e2b24a"), h("#b07a22"), h("#3a2408"), h("#7a1a10")),
        "manga" => (h("#ecebe4"), h("#c9c8c0"), h("#111111"), h("#c8281e")),
        _ => (h("#e6d3a3"), h("#cfb57c"), h("#3b2616"), h("#3b2616")),
    }
}

struct Paper {
    pal: String,
    seed: u32,
    w: i32,
    h: i32,
    paper: Rgb,
    stain: Rgb,
}

impl Paper {
    fn at(&self, x: i32, y: i32) -> Rgb {
        if self.pal == "secret-rare" {
            let stops: Vec<Rgb> = GOLD_LEAF.iter().map(|&v| rgb(v)).collect();
            let t = (x as f32 / self.w as f32 * 0.8 + y as f32 / self.h as f32 * 0.35).rem_euclid(1.0);
            let b = grad(&stops, t);
            return if noise(x, y, self.seed ^ 7) > 0.93 { mix(b, rgb(0xb07a22), 0.35) } else { b };
        }
        let n = noise(x, y, self.seed);
        if self.pal == "manga" {
            return if n > 0.9 { mix(self.paper, self.stain, 0.55) } else { self.paper };
        }
        let edge = (x.min(self.w - 1 - x)).min((y * 2).min((self.h - 1 - y) * 2)) as f32 / 6.0;
        let k = (0.85 - edge).max(0.0) * 0.8 + if n > 0.93 { 0.35 } else { 0.0 } + 0.12 * noise(x / 3, y, self.seed ^ 0x51);
        mix(self.paper, self.stain, k.min(1.0))
    }
    fn nib(&self, x: i32, y: i32, p: f32) -> bool {
        noise(x, y, self.seed ^ 0xabc) < p
    }
}

fn draw_wanted(buf: &mut Buffer, r: Rect, c: &Card, img: Option<&Img>, pal: &str, theme: &Theme) {
    let (x0, y0) = (r.x as i32, r.y as i32);
    let (w, h) = (r.width as i32, r.height as i32);
    let (paper, stain, ink, acc) = wanted_pal(pal);
    let pending = c.state == SlotState::Pending;
    let tone = |col: Rgb| if pending { darken(desat(col, 0.75), 0.4) } else { col };
    let ch = &c.pack.chars[c.ch];
    let pp = Paper { pal: pal.to_string(), seed: str_seed(ch) ^ str_seed(&c.pack.tiers[c.tier].id), w, h, paper, stain };
    let bg = theme_bg(theme);
    let side = if c.thumb { 1 } else { 2 };
    let (ink, acc) = (tone(ink), tone(acc));
    let sel = if c.selected { Some(theme.hi) } else { None };
    // paper everywhere, then cut out the photo window
    for y in 0..h {
        for x in 0..w {
            let p = tone(pp.at(x, y));
            let (ax, ay) = (x0 + x, y0 + y);
            let corner = (x == 0 || x == w - 1) && (y == 0 || y == h - 1);
            if corner {
                let s = match (x == 0, y == 0) {
                    (true, true) => "▗",
                    (false, true) => "▖",
                    (true, false) => "▝",
                    (false, false) => "▘",
                };
                put(buf, ax, ay, s, Some(sel.unwrap_or(p)), Some(bg), false);
            } else if (x == 0 || x == w - 1) && y > 0 && y < h - 1 && pp.nib(x, y, 0.12) {
                put(buf, ax, ay, if x == 0 { "▐" } else { "▌" }, Some(p), Some(sel.unwrap_or(bg)), false);
            } else if y == 0 && pp.nib(x, y, 0.10) && !c.thumb {
                put(buf, ax, ay, "▄", Some(p), Some(bg), false);
            } else if y == h - 1 && pp.nib(x, y, 0.12) && !c.thumb {
                put(buf, ax, ay, "▀", Some(p), Some(bg), false);
            } else {
                put(buf, ax, ay, " ", None, Some(p), false);
            }
        }
    }
    // photo window
    let (wx0, wy0, wx1, wy1) = (x0 + side, y0 + 1, x0 + w - 1 - side, y0 + h - if c.thumb { 2 } else { 3 });
    let photo = tone(if pal == "manga" { rgb(0x1a1a1a) } else { darken(paper, 0.82) });
    for y in wy0..=wy1 {
        for x in wx0..=wx1 {
            put(buf, x, y, " ", None, Some(photo), false);
        }
    }
    if let Some(img) = img {
        let iw = (wx1 - wx0 + 1) as usize;
        let ih = (wy1 - wy0 + 1) as usize;
        let ax = wx0 + (iw.saturating_sub(img.w) / 2) as i32;
        let ay = wy0 + (ih.saturating_sub(img.rows()) / 2) as i32;
        image(buf, ax, ay, img, photo, &|p| tone(p));
    }
    // texts
    let center = |buf: &mut Buffer, y: i32, s: &str, fg: Rgb, bold: bool| {
        let s = trunc(s, (w - 2).max(0) as usize);
        let sx = x0 + (w - width(&s) as i32) / 2;
        for (i, chr) in s.chars().enumerate() {
            let px = sx + i as i32;
            let p = tone(pp.at(px - x0, y - y0));
            putc(buf, px, y, chr, Some(fg), Some(p), bold);
        }
    };
    let tier = &c.pack.tiers[c.tier];
    if c.thumb {
        center(buf, y0, if w >= 13 { "W A N T E D" } else { "WANTED" }, ink, true);
        let mut name = c.pack.name_of(ch).to_uppercase();
        if c.count > 1 {
            name = format!("{name} ×{}", c.count);
        }
        if pending {
            name = format!("◌ {name}");
        }
        center(buf, y0 + h - 1, &name, if c.selected { acc } else { ink }, true);
        if c.selected {
            // selection marks on the torn corners
            put(buf, x0, y0, "▗", Some(theme.hi), Some(bg), false);
        }
    } else {
        center(buf, y0, "W A N T E D", ink, true);
        center(buf, y0 + h - 2, &c.pack.poster_of(ch), ink, true);
        let bounty = c.pack.bounty_of(ch);
        let y = y0 + h - 1;
        if !bounty.is_empty() {
            let s = format!("฿ {bounty}-");
            for (i, chr) in s.chars().enumerate() {
                let px = x0 + 2 + i as i32;
                putc(buf, px, y, chr, Some(ink), Some(tone(pp.at(px - x0, h - 1))), true);
            }
        }
        let lab = format!("{}{}", tier.label.to_uppercase(), if c.shiny { " ✦" } else { "" });
        let lx = x0 + w - 2 - width(&lab) as i32;
        for (i, chr) in lab.chars().enumerate() {
            let px = lx + i as i32;
            putc(buf, px, y, chr, Some(acc), Some(tone(pp.at(px - x0, h - 1))), pal != "common");
        }
        if pending {
            center(buf, y0 + 1, "◌ pending", theme.warn, true);
        }
    }
}

// ---------------------------------------------------------------- foil shimmer

/// Where the shimmer band is at `phase` (0..1 over one cycle), or None while resting between sweeps.
pub const SWEEP: f32 = 0.55; // fraction of the cycle spent sweeping
pub const CYCLE_SECS: f32 = 3.4;

pub fn shimmer(buf: &mut Buffer, r: Rect, frame: &FrameSpec, shiny: bool, phase: f32) {
    if phase >= SWEEP {
        return;
    }
    let p = phase / SWEEP;
    let center = -0.25 + p * 1.5;
    let (w, h) = (r.width.max(1) as f32, r.height.max(1) as f32);
    let (irid, tint): (f32, Rgb) = match frame {
        FrameSpec::Box(stops) => {
            let warm = stops.iter().any(|s| s[0] > 0xb0 && s[2] < 0x60);
            if stops.len() >= 6 {
                (0.85, rgb(0xffffff))
            } else if warm {
                (0.0, rgb(0xfff3c4))
            } else if stops.iter().any(|s| s[2] > s[0] + 30) {
                (0.55, rgb(0xf4f8ff))
            } else {
                (0.15, rgb(0xffffff))
            }
        }
        FrameSpec::Wanted(p) if p == "secret-rare" => (0.0, rgb(0xfff6d0)),
        FrameSpec::Wanted(_) => (0.35, rgb(0xffffff)),
    };
    let irid = if shiny { irid.max(0.5) } else { irid };
    let (rx, ry) = (r.x as i32, r.y as i32);
    let (x1, y1) = (rx + r.width as i32 - 1, ry + r.height as i32 - 1);
    let area = r.intersection(buf.area);
    for y in area.y..area.y + area.height {
        for x in area.x..area.x + area.width {
            let (xi, yi) = (x as i32, y as i32);
            let u = (xi - rx) as f32 / w * 0.72 + (yi - ry) as f32 / h * 0.28;
            let d = (u - center) / 0.085;
            let k = (-d * d).exp();
            if k < 0.02 {
                continue;
            }
            let tc = mix(tint, rainbow(u * 1.6 + p * 0.8), irid);
            let edge = xi == rx || xi == x1 || yi == ry || yi == y1;
            let cell = &mut buf[(x, y)];
            if let ratatui::style::Color::Rgb(a, b, c) = cell.fg {
                cell.fg = crate::color::col(mix([a, b, c], tc, k * if edge { 0.6 } else { 0.42 }));
            }
            // the frame row/column keeps the panel background: the light stays on the card
            if !edge {
                if let ratatui::style::Color::Rgb(a, b, c) = cell.bg {
                    cell.bg = crate::color::col(mix([a, b, c], tc, k * 0.42));
                }
            }
        }
    }
}
