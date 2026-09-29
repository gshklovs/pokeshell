//! Pixel art: JSON grids (packs/<pack>/art/<id>.json) or pre-built half-block ANSI (dist/<pack>/*.ans,
//! the pokedex colorscripts). Loaded lazily per card and cached, thumbnails cached per size.

use crate::color::{Rgb, hex};
use crate::data::{Pack, SlotKey};
use serde_json::Value;
use std::cell::RefCell;
use std::collections::HashMap;
use std::rc::Rc;

#[derive(Clone, Debug)]
pub struct Img {
    pub w: usize,
    pub h: usize,
    pub px: Vec<Option<Rgb>>,
}

impl Img {
    #[inline]
    pub fn get(&self, x: usize, y: usize) -> Option<Rgb> {
        if x < self.w && y < self.h { self.px[y * self.w + x] } else { None }
    }

    /// Cut out a sub-rectangle.
    pub fn crop(&self, x0: usize, y0: usize, w: usize, h: usize) -> Img {
        let mut px = Vec::with_capacity(w * h);
        for y in y0..y0 + h {
            for x in x0..x0 + w {
                px.push(self.get(x, y));
            }
        }
        Img { w, h, px }
    }

    /// Thumbnail framing: trim transparent margins; a full-bleed image (a full-art scene) is
    /// center-cropped toward the box's aspect (at most 40% of its width) so the character stays big.
    pub fn frame_for(&self, box_w: usize, box_h_px: usize) -> Img {
        let rows: Vec<usize> = (0..self.h).filter(|&y| (0..self.w).any(|x| self.get(x, y).is_some())).collect();
        let cols: Vec<usize> = (0..self.w).filter(|&x| (0..self.h).any(|y| self.get(x, y).is_some())).collect();
        let (Some(&y0), Some(&y1), Some(&x0), Some(&x1)) = (rows.first(), rows.last(), cols.first(), cols.last()) else {
            return self.clone();
        };
        let t = self.crop(x0, y0, x1 - x0 + 1, y1 - y0 + 1);
        let opaque = t.px.iter().filter(|p| p.is_some()).count() as f32 / t.px.len().max(1) as f32;
        let a = box_w as f32 / box_h_px.max(1) as f32;
        if opaque < 0.85 || (t.w as f32 / t.h as f32) <= a {
            return t;
        }
        let cw = ((t.h as f32 * a).round() as usize).max((t.w as f32 * 0.6) as usize).min(t.w);
        t.crop((t.w - cw) / 2, 0, cw, t.h)
    }

    /// Rows of cells (half-blocks) this image takes.
    pub fn rows(&self) -> usize {
        self.h.div_ceil(2)
    }

    /// Downscale so it fits `max_w` cells x `max_h` cell rows (never upscales).
    /// Mild reductions sample nearest-neighbour (stays crisp); strong ones use an
    /// outline-preserving box filter: a block that holds enough of a much darker color
    /// (the 1px pixel-art outline) takes that color instead of the muddy average.
    pub fn fit(&self, max_w: usize, max_h: usize) -> Img {
        if max_w == 0 || max_h == 0 || self.w == 0 || self.h == 0 {
            return Img { w: 0, h: 0, px: vec![] };
        }
        let s = (max_w as f32 / self.w as f32).min((max_h * 2) as f32 / self.h as f32).min(1.0);
        if s >= 1.0 {
            return self.clone();
        }
        let tw = ((self.w as f32 * s).round() as usize).clamp(1, max_w);
        let th = ((self.h as f32 * s).round() as usize).clamp(1, max_h * 2);
        let (sx, sy) = (self.w as f32 / tw as f32, self.h as f32 / th as f32);
        let mut px = Vec::with_capacity(tw * th);
        if s >= 0.6 {
            for ty in 0..th {
                let y = (((ty as f32 + 0.5) * sy) as usize).min(self.h - 1);
                for tx in 0..tw {
                    let x = (((tx as f32 + 0.5) * sx) as usize).min(self.w - 1);
                    px.push(self.px[y * self.w + x]);
                }
            }
            return Img { w: tw, h: th, px };
        }
        let luma = crate::color::luma;
        for ty in 0..th {
            let (y0, y1) = (ty as f32 * sy, (ty + 1) as f32 * sy);
            for tx in 0..tw {
                let (x0, x1) = (tx as f32 * sx, (tx + 1) as f32 * sx);
                let mut samples: Vec<(Rgb, f32)> = Vec::with_capacity(16);
                let mut area = 0f32;
                let mut yy = y0.floor() as usize;
                while (yy as f32) < y1 && yy < self.h {
                    let wy = (y1.min(yy as f32 + 1.0) - y0.max(yy as f32)).max(0.0);
                    let mut xx = x0.floor() as usize;
                    while (xx as f32) < x1 && xx < self.w {
                        let wx = (x1.min(xx as f32 + 1.0) - x0.max(xx as f32)).max(0.0);
                        let a = wx * wy;
                        area += a;
                        if let Some(c) = self.px[yy * self.w + xx] {
                            samples.push((c, a));
                        }
                        xx += 1;
                    }
                    yy += 1;
                }
                let cov: f32 = samples.iter().map(|s| s.1).sum();
                if area <= 0.0 || cov / area < 0.4 {
                    px.push(None);
                    continue;
                }
                let mut acc = [0f32; 3];
                let mut lsum = 0f32;
                for (c, a) in &samples {
                    for k in 0..3 {
                        acc[k] += c[k] as f32 * a;
                    }
                    lsum += luma(*c) * a;
                }
                let avg = [(acc[0] / cov) as u8, (acc[1] / cov) as u8, (acc[2] / cov) as u8];
                let lavg = lsum / cov;
                // the dark share of this block: pixels well below the block's mean brightness
                let (mut dark_a, mut dacc) = (0f32, [0f32; 3]);
                for (c, a) in &samples {
                    if luma(*c) < lavg - 0.18 {
                        dark_a += a;
                        for k in 0..3 {
                            dacc[k] += c[k] as f32 * a;
                        }
                    }
                }
                let p = if dark_a / area >= 0.28 {
                    [(dacc[0] / dark_a) as u8, (dacc[1] / dark_a) as u8, (dacc[2] / dark_a) as u8]
                } else {
                    avg
                };
                px.push(Some(p));
            }
        }
        Img { w: tw, h: th, px }
    }
}

// ---------------------------------------------------------------- JSON grids

fn palette_of(v: Option<&Value>, into: &mut HashMap<char, Rgb>) {
    if let Some(o) = v.and_then(|p| p.as_object()) {
        for (k, c) in o {
            if let (Some(ch), Some(rgb)) = (k.chars().next(), c.as_str().and_then(hex)) {
                into.insert(ch, rgb);
            }
        }
    }
}

fn from_json(doc: &Value, variant: &str, shiny: bool) -> Option<Img> {
    let vars = doc.get("variants")?.as_object()?;
    let var = vars.get(variant).or_else(|| vars.get("common")).or_else(|| vars.values().next())?;
    let mut pal = HashMap::new();
    palette_of(doc.get("palette"), &mut pal);
    palette_of(var.get("palette"), &mut pal);
    if shiny {
        palette_of(doc.get("shiny"), &mut pal);
        palette_of(var.get("shiny"), &mut pal);
    }
    let rows: Vec<&str> = var.get("rows")?.as_array()?.iter().filter_map(|r| r.as_str()).collect();
    let w = rows.iter().map(|r| r.chars().count()).max()?;
    let h = rows.len();
    let mut px = vec![None; w * h];
    for (y, r) in rows.iter().enumerate() {
        for (x, c) in r.chars().enumerate() {
            if c != '.' {
                px[y * w + x] = pal.get(&c).copied();
            }
        }
    }
    Some(Img { w, h, px })
}

// ---------------------------------------------------------------- half-block ANSI

/// Port of packs/pokedex/build.py `parse`: colorscript text -> pixel grid, 2 pixel rows per text line.
pub fn from_ansi(text: &str) -> Img {
    let mut grid: Vec<Vec<Option<Rgb>>> = Vec::new();
    for line in text.split('\n') {
        let line = line.trim_end_matches('\r');
        let (mut top, mut bot) = (Vec::new(), Vec::new());
        let (mut fg, mut bg): (Option<Rgb>, Option<Rgb>) = (None, None);
        let mut it = line.chars().peekable();
        while let Some(c) = it.next() {
            if c == '\x1b' && it.peek() == Some(&'[') {
                it.next();
                let mut params = String::new();
                for d in it.by_ref() {
                    if d == 'm' {
                        break;
                    }
                    params.push(d);
                }
                let p: Vec<i32> = if params.is_empty() { vec![0] } else { params.split(';').map(|x| x.parse().unwrap_or(0)).collect() };
                let mut i = 0;
                while i < p.len() {
                    match p[i] {
                        0 => {
                            fg = None;
                            bg = None;
                            i += 1
                        }
                        38 | 48 if i + 4 < p.len() && p[i + 1] == 2 => {
                            let c = Some([p[i + 2] as u8, p[i + 3] as u8, p[i + 4] as u8]);
                            if p[i] == 38 { fg = c } else { bg = c }
                            i += 5
                        }
                        39 => {
                            fg = None;
                            i += 1
                        }
                        49 => {
                            bg = None;
                            i += 1
                        }
                        _ => i += 1,
                    }
                }
                continue;
            }
            match c {
                '▀' => {
                    top.push(fg);
                    bot.push(bg)
                }
                '▄' => {
                    top.push(bg);
                    bot.push(fg)
                }
                '█' => {
                    top.push(fg);
                    bot.push(fg)
                }
                _ => {
                    top.push(bg);
                    bot.push(bg)
                }
            }
        }
        grid.push(top);
        grid.push(bot);
    }
    // trim empty rows / columns
    while grid.last().is_some_and(|r| r.iter().all(|p| p.is_none())) {
        grid.pop();
    }
    while grid.first().is_some_and(|r| r.iter().all(|p| p.is_none())) {
        grid.remove(0);
    }
    let w0 = grid.iter().map(|r| r.len()).max().unwrap_or(0);
    let used: Vec<usize> = (0..w0).filter(|&x| grid.iter().any(|r| r.get(x).copied().flatten().is_some())).collect();
    if used.is_empty() {
        return Img { w: 1, h: 1, px: vec![None] };
    }
    let (x0, x1) = (used[0], *used.last().unwrap());
    let w = x1 - x0 + 1;
    let h = grid.len();
    let mut px = Vec::with_capacity(w * h);
    for r in &grid {
        for x in x0..=x1 {
            px.push(r.get(x).copied().flatten());
        }
    }
    Img { w, h, px }
}

// ---------------------------------------------------------------- store

#[derive(Default)]
pub struct ArtStore {
    docs: RefCell<HashMap<String, Option<Rc<Value>>>>,
    imgs: RefCell<HashMap<String, Option<Rc<Img>>>>,
    thumbs: RefCell<HashMap<(String, usize, usize), Rc<Img>>>,
}

impl ArtStore {
    fn doc(&self, pack: &Pack, ch: &str) -> Option<Rc<Value>> {
        let key = format!("{}/{}", pack.id, ch);
        if let Some(d) = self.docs.borrow().get(&key) {
            return d.clone();
        }
        let d = std::fs::read(pack.dir.join("art").join(format!("{ch}.json")))
            .ok()
            .and_then(|b| serde_json::from_slice::<Value>(&b).ok())
            .map(Rc::new);
        self.docs.borrow_mut().insert(key, d.clone());
        d
    }

    /// The art for a card, full size.
    pub fn get(&self, pack: &Pack, ch: &str, art: &str, shiny: bool) -> Option<Rc<Img>> {
        let key = format!("{}/{}/{}/{}", pack.id, ch, art, shiny as u8);
        if let Some(i) = self.imgs.borrow().get(&key) {
            return i.clone();
        }
        let img = self
            .doc(pack, ch)
            .and_then(|d| from_json(&d, art, shiny))
            .or_else(|| {
                let sfx = if shiny { "-shiny" } else { "" };
                [format!("{ch}-{art}{sfx}.ans"), format!("{ch}-{art}.ans"), format!("{ch}-common{sfx}.ans"), format!("{ch}-common.ans")]
                    .iter()
                    .find_map(|f| std::fs::read_to_string(pack.dist.join(f)).ok())
                    .map(|t| from_ansi(&t))
            })
            .map(Rc::new);
        self.imgs.borrow_mut().insert(key.clone(), img.clone());
        img
    }

    /// Downscaled to fit (cached per size).
    pub fn fitted(&self, pack: &Pack, ch: &str, art: &str, shiny: bool, w: usize, h: usize) -> Option<Rc<Img>> {
        let full = self.get(pack, ch, art, shiny)?;
        if full.w <= w && full.rows() <= h {
            return Some(full);
        }
        let key = (format!("{}/{}/{}/{}", pack.id, ch, art, shiny as u8), w, h);
        if let Some(t) = self.thumbs.borrow().get(&key) {
            return Some(t.clone());
        }
        let t = Rc::new(full.fit(w, h));
        self.thumbs.borrow_mut().insert(key, t.clone());
        Some(t)
    }

    /// The shape of a seen card (docs/BINDER_SPEC.md "Empty, seen, caught"): an image whose opaque pixels are the
    /// silhouette (their colours don't matter: the card draws them in the theme's flat shadow colour). The sprite's
    /// alpha, never a scene's background, found in this order:
    ///   1. packs without real cards: the character's base (tier 0) art;
    ///   2. a real card whose art is the plain sprite (it has transparent pixels, is_sprite: the commons): its own art;
    ///   3. a scene card: the character's plain sprite, from one of its commons in the pack (the shipped art);
    ///   4. else the colorscripts sprite itself: vendor/pokemon-colorscripts (or $POKESHELL_VENDOR), then the pokedex
    ///      pack's dist/pokedex/<character>-common.ans (checkouts that build the art have these);
    ///   5. else the card art's sprite layer: the pixels its shiny art recolours (the sprite sits pixel-exact over the
    ///      scene, docs/ART_METHOD.md, and only it changes with shiny), plus the dark outline around them, holes filled.
    /// None when nothing gives a shape (the seen card then shows a "?").
    pub fn silhouette(&self, pack: &Pack, k: SlotKey) -> Option<Rc<Img>> {
        let key = format!("sil/{}/{}/{}/{}", pack.id, k.ch, k.tier, k.card);
        if let Some(i) = self.imgs.borrow().get(&key) {
            return i.clone();
        }
        let ch = &pack.chars[k.ch];
        let img = match pack.card_at(k.card) {
            None => self.get(pack, ch, &pack.tiers[0].art, false),
            Some(c) => {
                let own = self.get(pack, ch, &c.id, false);
                if own.as_deref().is_some_and(is_sprite) {
                    own
                } else {
                    pack.char_cards[k.ch]
                        .iter()
                        .filter_map(|&i| self.get(pack, ch, &pack.card_list[i].id, false))
                        .find(|i| is_sprite(i))
                        .or_else(|| sprite_file(pack, ch).map(Rc::new))
                        .or_else(|| {
                            let b = self.get(pack, ch, &c.id, true)?;
                            sprite_layer(own.as_deref()?, &b).map(Rc::new)
                        })
                }
            }
        };
        self.imgs.borrow_mut().insert(key, img.clone());
        img
    }

    /// The silhouette fitted to a box (cached per size): a thumbnail is trimmed first, like the art.
    pub fn silhouette_fit(&self, pack: &Pack, k: SlotKey, w: usize, h: usize, thumb: bool) -> Option<Rc<Img>> {
        let key = (format!("sil/{}/{}/{}/{}/{}", pack.id, k.ch, k.tier, k.card, thumb as u8), w, h);
        if let Some(t) = self.thumbs.borrow().get(&key) {
            return Some(t.clone());
        }
        let full = self.silhouette(pack, k)?;
        let t = Rc::new(if thumb { full.frame_for(w, h * 2).fit(w, h) } else { full.fit(w, h) });
        self.thumbs.borrow_mut().insert(key, t.clone());
        Some(t)
    }

    /// Thumbnail: trimmed / cropped toward the box, then downscaled (cached per size).
    pub fn thumb(&self, pack: &Pack, ch: &str, art: &str, shiny: bool, w: usize, h: usize) -> Option<Rc<Img>> {
        let key = (format!("t/{}/{}/{}/{}", pack.id, ch, art, shiny as u8), w, h);
        if let Some(t) = self.thumbs.borrow().get(&key) {
            return Some(t.clone());
        }
        let full = self.get(pack, ch, art, shiny)?;
        let t = Rc::new(full.frame_for(w, h * 2).fit(w, h));
        self.thumbs.borrow_mut().insert(key, t.clone());
        Some(t)
    }

}

// ---------------------------------------------------------------- silhouettes

/// Is this card art a plain sprite (a common)? It has transparent pixels around the Pokemon; a scene is full-bleed.
pub fn is_sprite(img: &Img) -> bool {
    img.px.iter().filter(|p| p.is_none()).count() * 10 >= img.px.len().max(1)
}

/// The character's plain colorscripts sprite, when this checkout has it: vendor/pokemon-colorscripts (large, the
/// size the commons are built at; $POKESHELL_VENDOR points at another vendor folder), else the pokedex pack's art.
fn sprite_file(pack: &Pack, ch: &str) -> Option<Img> {
    let root = pack.dir.parent()?.parent()?;
    let vendor = std::env::var_os("POKESHELL_VENDOR").map(std::path::PathBuf::from).unwrap_or_else(|| root.join("vendor"));
    [vendor.join("pokemon-colorscripts").join("colorscripts").join("large").join("regular").join(ch), root.join("dist").join("pokedex").join(format!("{ch}-common.ans"))]
        .iter()
        .find_map(|f| std::fs::read_to_string(f).ok())
        .map(|t| from_ansi(&t))
        .filter(|i| i.px.iter().any(|p| p.is_some()))
}

/// A scene card's sprite layer from its normal and shiny art: the pixels that differ, grown twice into the dark
/// pixels touching them (8 neighbours) (the black outline and eyes, the same in both), then with enclosed holes filled. None when the
/// two don't line up or too little differs to be a sprite.
pub fn sprite_layer(a: &Img, b: &Img) -> Option<Img> {
    if a.w != b.w || a.h != b.h || a.w == 0 {
        return None;
    }
    let (w, h) = (a.w, a.h);
    let mut m: Vec<bool> = (0..w * h).map(|i| a.px[i].is_some() && a.px[i] != b.px[i]).collect();
    if m.iter().filter(|&&x| x).count() * 100 < w * h {
        return None;
    }
    let dark = |i: usize| a.px[i].is_some_and(|c| crate::color::luma(c) < 0.16);
    for _ in 0..2 {
        let prev = m.clone();
        for y in 0..h {
            for x in 0..w {
                let i = y * w + x;
                if prev[i] || !dark(i) {
                    continue;
                }
                // 8 neighbours: the outline's corners too
                let near = (y.saturating_sub(1)..(y + 2).min(h)).any(|yy| (x.saturating_sub(1)..(x + 2).min(w)).any(|xx| prev[yy * w + xx]));
                if near {
                    m[i] = true;
                }
            }
        }
    }
    // holes: what the border can't reach without crossing the mask
    let mut out = vec![false; w * h];
    let mut stack: Vec<usize> = (0..w).flat_map(|x| [x, (h - 1) * w + x]).chain((0..h).flat_map(|y| [y * w, y * w + w - 1])).filter(|&i| !m[i]).collect();
    while let Some(i) = stack.pop() {
        if out[i] || m[i] {
            continue;
        }
        out[i] = true;
        let (x, y) = (i % w, i / w);
        if x > 0 {
            stack.push(i - 1);
        }
        if x + 1 < w {
            stack.push(i + 1);
        }
        if y > 0 {
            stack.push(i - w);
        }
        if y + 1 < h {
            stack.push(i + w);
        }
    }
    Some(Img { w, h, px: (0..w * h).map(|i| if out[i] { None } else { Some([0, 0, 0]) }).collect() })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sprite_layer_fills_the_outline() {
        // a 8x6 scene; the "sprite" is a 4x4 block with a dark outline and a light eye that shiny doesn't change
        let (w, h) = (8, 6);
        let scene = [90u8, 140, 60];
        let mut a = Img { w, h, px: vec![Some(scene); w * h] };
        for y in 1..5 {
            for x in 2..6 {
                let edge = x == 2 || x == 5 || y == 1 || y == 4;
                a.px[y * w + x] = Some(if edge { [5, 5, 5] } else { [200, 60, 60] });
            }
        }
        a.px[2 * w + 3] = Some([250, 250, 250]); // the eye: the same in both
        let mut b = a.clone();
        for y in 2..4 {
            for x in 3..5 {
                if (x, y) != (3, 2) {
                    b.px[y * w + x] = Some([60, 60, 200]);
                }
            }
        }
        let m = sprite_layer(&a, &b).unwrap();
        let on = |x: usize, y: usize| m.get(x, y).is_some();
        assert!((2..6).all(|x| (1..5).all(|y| on(x, y))), "outline, body and eye");
        assert!(!on(0, 0) && !on(7, 5) && !on(1, 2) && !on(6, 3), "the scene stays out");
        assert!(sprite_layer(&a, &a).is_none(), "nothing differs: no sprite layer");
    }
}
