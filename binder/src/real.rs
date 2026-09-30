//! `p`: the real printed card beside ours (docs/BINDER_SPEC.md "The printed card").
//!
//! The scan is pokemontcg.io's image of the card (`images.large` in packs/<pack>/cards/<id>.json, else
//! images.pokemontcg.io/<set>/<number>_hires.png from the card id). Scans are never shipped with pokeshell: they are
//! fetched on demand (curl, on a background thread with a hard timeout, so the UI never waits on the network) and
//! cached under the state folder, `<state>/cache/realcards/<set>/<file>.png`.
//!
//! Drawn two ways:
//!   - sixel (Windows Terminal 1.22+, and other sixel terminals): the scan itself, crisp, written straight to the
//!     terminal after the frame, over a blank area the frame keeps for it;
//!   - half blocks: the scan downsampled into the cells, two pixels per cell, like our own art.
//!
//! Which one: `POKESHELL_SIXEL=on|off|auto` (environment), else `sixel=on|off|auto` in <state>/config.txt, else auto:
//! the terminal is asked for its primary device attributes (DA1, `ESC [ c`) the first time a printed card is shown;
//! sixel when the reply lists attribute 4 (Windows Terminal 1.22+ does), half blocks when it doesn't or no reply
//! comes within PROBE_MS.

use crate::color::Rgb;
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::rc::Rc;
use std::sync::mpsc::{Receiver, Sender, channel};

/// A printed card's width / height (63 x 88 mm).
pub const ASPECT: f32 = 63.0 / 88.0;
/// Columns between our card and the printed one.
pub const GAP: u16 = 2;
/// Our card shrinks to make room for the printed one beside it, but not below this many rows: then the printed
/// card takes its place instead (the toggle swaps them).
pub const MIN_BESIDE_ROWS: u16 = 12;
/// How long to wait for the terminal's DA1 reply.
pub const PROBE_MS: u64 = 300;
/// The sixel "virtual" cell: Windows Terminal scales sixel images as if every cell were 10 x 20 pixels (the VT340's
/// cell), whatever the font. Other terminals: POKESHELL_CELL_PX=WxH.
pub const WT_CELL: (u16, u16) = (10, 20);

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Gfx {
    Sixel,
    Blocks,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Setting {
    Auto,
    On,
    Off,
}

/// POKESHELL_SIXEL wins over config.txt `sixel`; anything unrecognised is auto.
pub fn setting(env: Option<&str>, config: Option<&str>) -> Setting {
    let parse = |s: &str| match s.trim().to_ascii_lowercase().as_str() {
        "1" | "on" | "yes" | "true" | "sixel" => Some(Setting::On),
        "0" | "off" | "no" | "false" | "blocks" => Some(Setting::Off),
        "auto" => Some(Setting::Auto),
        _ => None,
    };
    env.and_then(parse).or_else(|| config.and_then(parse)).unwrap_or(Setting::Auto)
}

/// A DA1 reply (`ESC [ ? 61 ; 4 ; 6 ... c`): Some(true) when it lists 4 (sixel graphics), None when it isn't one.
pub fn da1_has_sixel(reply: &str) -> Option<bool> {
    let i = reply.find("[?")?;
    let body = &reply[i + 2..];
    let end = body.find('c')?;
    let params = &body[..end];
    if !params.bytes().all(|b| b.is_ascii_digit() || b == b';') {
        return None;
    }
    Some(params.split(';').any(|p| p == "4"))
}

/// POKESHELL_CELL_PX="10x20" (a sixel terminal that doesn't scale images like Windows Terminal does).
pub fn cell_px(env: Option<&str>) -> (u16, u16) {
    env.and_then(|s| {
        let (w, h) = s.trim().split_once(['x', 'X'])?;
        let (w, h) = (w.trim().parse::<u16>().ok()?, h.trim().parse::<u16>().ok()?);
        (w >= 2 && h >= 2 && w <= 200 && h <= 400).then_some((w, h))
    })
    .unwrap_or(WT_CELL)
}

/// The printed card's width in cells for a height in rows (cell = its pixel size; half blocks: 1 x 2).
pub fn real_w(rows: u16, cell: (u16, u16)) -> u16 {
    ((rows as f32 * cell.1 as f32 * ASPECT) / cell.0 as f32).round().max(1.0) as u16
}

/// Where the printed card goes: beside ours when both fit in `avail` columns, else in its place.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Place {
    Beside,
    Swap,
}

pub fn place(avail: u16, our_w: u16, rows: u16, cell: (u16, u16)) -> Place {
    if our_w + GAP + real_w(rows, cell) <= avail { Place::Beside } else { Place::Swap }
}

/// The scan's URLs for a card: (hires, small). `large` is the card data's images.large when it has one.
pub fn urls(card_id: &str, large: Option<&str>) -> Option<(String, String)> {
    if let Some(l) = large.map(str::trim).filter(|l| !l.is_empty()) {
        let small = l.strip_suffix("_hires.png").map(|s| format!("{s}.png")).unwrap_or_else(|| l.to_string());
        return Some((l.to_string(), small));
    }
    let (set, num) = card_id.split_once('-')?;
    let ok = |s: &str| !s.is_empty() && s.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_');
    if !ok(set) || !ok(num) {
        return None;
    }
    Some((format!("https://images.pokemontcg.io/{set}/{num}_hires.png"), format!("https://images.pokemontcg.io/{set}/{num}.png")))
}

/// Where a URL's scan is cached: <dir>/<set>/<file> from the URL's last two path segments (sanitised).
pub fn cache_path(dir: &Path, url: &str) -> PathBuf {
    let path = url.split_once("://").map(|(_, r)| r).unwrap_or(url);
    let path = path.split(['?', '#']).next().unwrap_or("");
    let segs: Vec<String> = path
        .split(['/', '\\'])
        .filter(|s| !s.is_empty() && *s != "." && *s != "..")
        .map(|s| s.chars().map(|c| if c.is_ascii_alphanumeric() || "._-".contains(c) { c } else { '_' }).collect())
        .collect();
    let n = segs.len();
    let (a, b) = match n {
        0 => ("misc".to_string(), "scan.png".to_string()),
        1 => ("misc".to_string(), segs[0].clone()),
        _ => (segs[n - 2].clone(), segs[n - 1].clone()),
    };
    dir.join(a).join(b)
}

/// A decoded scan, RGBA.
pub struct Scan {
    pub w: usize,
    pub h: usize,
    pub px: Vec<[u8; 4]>,
}

pub fn decode_png(bytes: &[u8]) -> Result<Scan, String> {
    let mut d = png::Decoder::new(std::io::Cursor::new(bytes));
    d.set_transformations(png::Transformations::normalize_to_color8());
    let mut r = d.read_info().map_err(|e| format!("not a PNG ({e})"))?;
    let size = r.output_buffer_size().ok_or("PNG too big")?;
    if size > 64 << 20 {
        return Err("PNG too big".into());
    }
    let mut buf = vec![0; size];
    let info = r.next_frame(&mut buf).map_err(|e| format!("bad PNG ({e})"))?;
    let (w, h) = (info.width as usize, info.height as usize);
    let data = &buf[..info.buffer_size()];
    let px: Vec<[u8; 4]> = match info.color_type {
        png::ColorType::Rgba => data.chunks_exact(4).map(|c| [c[0], c[1], c[2], c[3]]).collect(),
        png::ColorType::Rgb => data.chunks_exact(3).map(|c| [c[0], c[1], c[2], 255]).collect(),
        png::ColorType::GrayscaleAlpha => data.chunks_exact(2).map(|c| [c[0], c[0], c[0], c[1]]).collect(),
        png::ColorType::Grayscale => data.iter().map(|&g| [g, g, g, 255]).collect(),
        png::ColorType::Indexed => return Err("unexpanded palette PNG".into()),
    };
    if w == 0 || h == 0 || px.len() < w * h {
        return Err("empty PNG".into());
    }
    Ok(Scan { w, h, px })
}

/// Area-average resample to w x h (alpha-weighted, so transparent corners don't darken the edge).
pub fn resize(s: &Scan, w: usize, h: usize) -> Vec<[u8; 4]> {
    let (w, h) = (w.max(1), h.max(1));
    let mut out = vec![[0u8; 4]; w * h];
    let (sx, sy) = (s.w as f32 / w as f32, s.h as f32 / h as f32);
    for y in 0..h {
        let y0 = (y as f32 * sy) as usize;
        let y1 = (((y + 1) as f32 * sy).ceil() as usize).clamp(y0 + 1, s.h);
        for x in 0..w {
            let x0 = (x as f32 * sx) as usize;
            let x1 = (((x + 1) as f32 * sx).ceil() as usize).clamp(x0 + 1, s.w);
            let (mut r, mut g, mut b, mut a, mut n) = (0u32, 0u32, 0u32, 0u32, 0u32);
            for yy in y0..y1 {
                for p in &s.px[yy * s.w + x0..yy * s.w + x1] {
                    let pa = p[3] as u32;
                    r += p[0] as u32 * pa;
                    g += p[1] as u32 * pa;
                    b += p[2] as u32 * pa;
                    a += pa;
                    n += 1;
                }
            }
            out[y * w + x] = if a == 0 { [0, 0, 0, 0] } else { [(r / a) as u8, (g / a) as u8, (b / a) as u8, (a / n.max(1)) as u8] };
        }
    }
    out
}

/// One cell of a half-block rendering: the glyph, its fg and bg (None = the panel's background shows).
pub type Cell = (&'static str, Option<Rgb>, Option<Rgb>);

/// The scan as w x rows half-block cells, fitted inside (letterboxed on the panel background).
pub fn blocks(s: &Scan, w: u16, rows: u16) -> Vec<Cell> {
    let (w, h) = (w as usize, rows as usize * 2);
    let (fw, fh) = fit(s.w, s.h, w, h);
    let img = resize(s, fw, fh);
    let (ox, oy) = ((w - fw) / 2, (h - fh) / 2);
    let at = |x: usize, y: usize| -> Option<Rgb> {
        if x < ox || y < oy || x >= ox + fw || y >= oy + fh {
            return None;
        }
        let p = img[(y - oy) * fw + (x - ox)];
        (p[3] >= 128).then_some([p[0], p[1], p[2]])
    };
    let mut out = Vec::with_capacity(w * rows as usize);
    for r in 0..rows as usize {
        for x in 0..w {
            out.push(match (at(x, 2 * r), at(x, 2 * r + 1)) {
                (Some(t), Some(b)) => ("▀", Some(t), Some(b)),
                (Some(t), None) => ("▀", Some(t), None),
                (None, Some(b)) => ("▄", Some(b), None),
                (None, None) => (" ", None, None),
            });
        }
    }
    out
}

/// The largest w x h inside (bw, bh) with the scan's aspect ratio.
fn fit(sw: usize, sh: usize, bw: usize, bh: usize) -> (usize, usize) {
    let (bw, bh) = (bw.max(1), bh.max(1));
    let w_at_h = (bh as f32 * sw as f32 / sh.max(1) as f32).round() as usize;
    if w_at_h <= bw { (w_at_h.max(1), bh) } else { (bw, ((bw as f32 * sh as f32 / sw.max(1) as f32).round() as usize).clamp(1, bh)) }
}

/// The scan as a sixel image exactly w x h pixels (fitted and centred; the rest is left transparent), up to 255
/// colours (median cut). Starts with DCS and ends with ST.
pub fn sixel(s: &Scan, w: usize, h: usize) -> String {
    let (fw, fh) = fit(s.w, s.h, w, h);
    let img = resize(s, fw, fh);
    let (ox, oy) = ((w - fw) / 2, (h - fh) / 2);
    // pixel -> palette index, 255 = transparent
    let opaque: Vec<[u8; 3]> = img.iter().filter(|p| p[3] >= 128).map(|p| [p[0], p[1], p[2]]).collect();
    let pal = median_cut(&opaque, 255);
    let mut near: HashMap<u16, u8> = HashMap::new();
    let mut idx = vec![255u8; w * h];
    for y in 0..fh {
        for x in 0..fw {
            let p = img[y * fw + x];
            if p[3] < 128 {
                continue;
            }
            let q = ((p[0] as u16 >> 3) << 10) | ((p[1] as u16 >> 3) << 5) | (p[2] as u16 >> 3);
            let i = *near.entry(q).or_insert_with(|| nearest(&pal, [p[0], p[1], p[2]]));
            idx[(y + oy) * w + x + ox] = i;
        }
    }
    let mut out = String::with_capacity(w * h / 2);
    // P2 = 1: pixels we don't set keep what is under them (the blank cells); "1;1: square pixels
    out.push_str(&format!("\x1bP0;1;0q\"1;1;{w};{h}"));
    for (i, c) in pal.iter().enumerate() {
        let pc = |v: u8| (v as u32 * 100 + 127) / 255;
        out.push_str(&format!("#{i};2;{};{};{}", pc(c[0]), pc(c[1]), pc(c[2])));
    }
    let mut row: Vec<u8> = vec![0; w];
    for band in (0..h).step_by(6) {
        let rows = (h - band).min(6);
        let mut used = vec![false; 256];
        for y in band..band + rows {
            for &i in &idx[y * w..(y + 1) * w] {
                used[i as usize] = true;
            }
        }
        for c in 0..pal.len() {
            if !used[c] {
                continue;
            }
            for x in 0..w {
                let mut bits = 0u8;
                for dy in 0..rows {
                    if idx[(band + dy) * w + x] == c as u8 {
                        bits |= 1 << dy;
                    }
                }
                row[x] = bits;
            }
            let end = row.iter().rposition(|&b| b != 0).map(|e| e + 1).unwrap_or(0);
            out.push_str(&format!("#{c}"));
            let mut x = 0;
            while x < end {
                let b = row[x];
                let mut n = 1;
                while x + n < end && row[x + n] == b {
                    n += 1;
                }
                let ch = (63 + b) as char;
                if n >= 4 {
                    out.push_str(&format!("!{n}{ch}"));
                } else {
                    for _ in 0..n {
                        out.push(ch);
                    }
                }
                x += n;
            }
            out.push('$');
        }
        out.push('-');
    }
    out.push_str("\x1b\\");
    out
}

fn nearest(pal: &[[u8; 3]], c: [u8; 3]) -> u8 {
    let d = |p: &[u8; 3]| {
        let (r, g, b) = (p[0] as i32 - c[0] as i32, p[1] as i32 - c[1] as i32, p[2] as i32 - c[2] as i32);
        2 * r * r + 4 * g * g + 3 * b * b
    };
    pal.iter().enumerate().min_by_key(|(_, p)| d(p)).map(|(i, _)| i as u8).unwrap_or(0)
}

/// Median-cut palette of at most n colours.
pub fn median_cut(px: &[[u8; 3]], n: usize) -> Vec<[u8; 3]> {
    if px.is_empty() {
        return vec![[0, 0, 0]];
    }
    let mut boxes: Vec<Vec<[u8; 3]>> = vec![px.to_vec()];
    let range = |b: &Vec<[u8; 3]>| -> (usize, u8) {
        let mut lo = [255u8; 3];
        let mut hi = [0u8; 3];
        for p in b {
            for k in 0..3 {
                lo[k] = lo[k].min(p[k]);
                hi[k] = hi[k].max(p[k]);
            }
        }
        let r = [hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]];
        let k = (0..3).max_by_key(|&k| r[k]).unwrap_or(0);
        (k, r[k])
    };
    while boxes.len() < n {
        // split the box with the most spread (weighted by its size)
        let pick = boxes
            .iter()
            .enumerate()
            .map(|(i, b)| (i, range(b), b.len()))
            .filter(|(_, (_, r), len)| *r > 0 && *len > 1)
            .max_by_key(|(_, (_, r), len)| *r as u64 * (*len as f64).sqrt() as u64);
        let Some((i, (k, _), _)) = pick else { break };
        let mut b = boxes.swap_remove(i);
        b.sort_unstable_by_key(|p| p[k]);
        let hi = b.split_off(b.len() / 2);
        boxes.push(b);
        boxes.push(hi);
    }
    boxes
        .iter()
        .map(|b| {
            let n = b.len().max(1) as u64;
            let s = b.iter().fold([0u64; 3], |a, p| [a[0] + p[0] as u64, a[1] + p[1] as u64, a[2] + p[2] as u64]);
            [(s[0] / n) as u8, (s[1] / n) as u8, (s[2] / n) as u8]
        })
        .collect()
}

/// What the card panel can show for a scan right now.
pub enum Status {
    Loading,
    Ready(Rc<Scan>),
    Failed(String),
}

/// A fetch's result, from the fetch thread.
type Done = (String, Result<Scan, String>);

/// The scans: cached on disk, decoded in memory, fetched in the background.
pub struct RealCards {
    pub dir: PathBuf,
    /// false: never touch the network (headless runs: snapshots, the selftest, the bench)
    pub fetch: bool,
    pub setting: Setting,
    /// None until decided (auto: the DA1 probe runs the first time a printed card is shown)
    pub gfx: Option<Gfx>,
    pub cell: (u16, u16),
    scans: HashMap<String, Rc<Scan>>,
    failed: HashMap<String, String>,
    pending: HashMap<String, ()>,
    blocks: HashMap<(String, u16, u16), Rc<Vec<Cell>>>,
    sixels: HashMap<(String, usize, usize), Rc<String>>,
    tx: Sender<Done>,
    rx: Receiver<Done>,
}

impl RealCards {
    pub fn new(dir: PathBuf, fetch: bool, setting: Setting, cell: (u16, u16)) -> RealCards {
        let (tx, rx) = channel();
        let gfx = match setting {
            Setting::On => Some(Gfx::Sixel),
            Setting::Off => Some(Gfx::Blocks),
            Setting::Auto if !fetch => Some(Gfx::Blocks),
            Setting::Auto => None,
        };
        RealCards { dir, fetch, setting, gfx, cell, scans: HashMap::new(), failed: HashMap::new(), pending: HashMap::new(), blocks: HashMap::new(), sixels: HashMap::new(), tx, rx }
    }

    /// The graphics in use; Blocks until the probe decides.
    pub fn gfx(&self) -> Gfx {
        self.gfx.unwrap_or(Gfx::Blocks)
    }

    /// Put a scan in memory (tests, snapshots: a fixture instead of the network).
    pub fn insert(&mut self, url: &str, scan: Scan) {
        self.scans.insert(url.to_string(), Rc::new(scan));
        self.failed.remove(url);
    }

    /// Forget failures, so the next look fetches again (toggling `p` back on retries).
    pub fn retry(&mut self) {
        self.failed.clear();
    }

    /// A fetch is running (the event loop polls sooner meanwhile).
    pub fn busy(&self) -> bool {
        !self.pending.is_empty()
    }

    /// Collect finished fetches; true when one finished (the frame should be redrawn).
    pub fn poll(&mut self) -> bool {
        let mut any = false;
        while let Ok((url, r)) = self.rx.try_recv() {
            self.pending.remove(&url);
            match r {
                Ok(s) => {
                    self.scans.insert(url, Rc::new(s));
                }
                Err(e) => {
                    self.failed.insert(url, e);
                }
            }
            any = true;
        }
        any
    }

    /// The scan for a URL: in memory, else from the disk cache (decoded now), else fetched in the background.
    pub fn status(&mut self, url: &str) -> Status {
        if let Some(s) = self.scans.get(url) {
            return Status::Ready(s.clone());
        }
        if let Some(e) = self.failed.get(url) {
            return Status::Failed(e.clone());
        }
        if self.pending.contains_key(url) {
            return Status::Loading;
        }
        let path = cache_path(&self.dir, url);
        if let Ok(b) = std::fs::read(&path) {
            match decode_png(&b) {
                Ok(s) => {
                    let s = Rc::new(s);
                    self.scans.insert(url.to_string(), s.clone());
                    return Status::Ready(s);
                }
                Err(_) => {
                    let _ = std::fs::remove_file(&path); // a broken cache file: fetch it again
                }
            }
        }
        if !self.fetch {
            let e = "not downloaded yet".to_string();
            self.failed.insert(url.to_string(), e.clone());
            return Status::Failed(e);
        }
        self.pending.insert(url.to_string(), ());
        let (tx, url_s) = (self.tx.clone(), url.to_string());
        let spawned = std::thread::Builder::new().name("realcard-fetch".into()).spawn(move || {
            let r = fetch(&url_s, &path).and_then(|b| decode_png(&b));
            let _ = tx.send((url_s, r));
        });
        if spawned.is_err() {
            self.pending.remove(url);
            let e = "couldn't start the download".to_string();
            self.failed.insert(url.to_string(), e.clone());
            return Status::Failed(e);
        }
        Status::Loading
    }

    /// Half-block cells for a scan (cached per size).
    pub fn blocks_for(&mut self, url: &str, s: &Scan, w: u16, rows: u16) -> Rc<Vec<Cell>> {
        let k = (url.to_string(), w, rows);
        if self.blocks.len() > 48 {
            self.blocks.clear();
        }
        self.blocks.entry(k).or_insert_with(|| Rc::new(blocks(s, w, rows))).clone()
    }

    /// The sixel image for a scan over `cols` x `rows` cells (cached per size); None when it isn't loaded.
    pub fn sixel_for(&mut self, url: &str, cols: u16, rows: u16) -> Option<Rc<String>> {
        let s = self.scans.get(url)?.clone();
        let (w, h) = (cols as usize * self.cell.0 as usize, rows as usize * self.cell.1 as usize);
        let k = (url.to_string(), w, h);
        if self.sixels.len() > 24 {
            self.sixels.clear();
        }
        Some(self.sixels.entry(k).or_insert_with(|| Rc::new(sixel(&s, w, h))).clone())
    }
}

/// Download a URL to `dst` (via a .part file, renamed when complete) and return its bytes. curl, with a connect
/// timeout and an overall one, so a dead network ends the thread in seconds; its errors become a short message.
pub fn fetch(url: &str, dst: &Path) -> Result<Vec<u8>, String> {
    use std::process::{Command, Stdio};
    if let Some(d) = dst.parent() {
        std::fs::create_dir_all(d).map_err(|e| format!("can't write the cache ({e})"))?;
    }
    let part = dst.with_extension("part");
    let mut cmd = Command::new(curl());
    cmd.args(["-sSL", "--connect-timeout", "5", "--max-time", "20", "-A", "pokeshell-binder", "-w", "%{http_code}", "-o"])
        .arg(&part)
        .arg(url)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::null());
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        cmd.creation_flags(0x0800_0000); // CREATE_NO_WINDOW
    }
    let out = cmd.output().map_err(|_| "no curl to download it with".to_string())?;
    let code: u32 = String::from_utf8_lossy(&out.stdout).trim().parse().unwrap_or(0);
    let fail = |m: String| {
        let _ = std::fs::remove_file(&part);
        Err(m)
    };
    if !out.status.success() {
        return fail(match out.status.code() {
            Some(6) | Some(7) => "offline: couldn't reach the scan server".into(),
            Some(28) => "the download timed out".into(),
            Some(37) => "no scan file there".into(),
            Some(c) => format!("download failed (curl {c})"),
            None => "download failed".into(),
        });
    }
    if code == 404 {
        return fail("no scan of this card online (404)".into());
    }
    if code >= 400 {
        return fail(format!("the scan server said HTTP {code}"));
    }
    let b = std::fs::read(&part).map_err(|e| format!("can't read the download ({e})"))?;
    if !b.starts_with(b"\x89PNG") {
        return fail("the download isn't a PNG".into());
    }
    std::fs::rename(&part, dst).or_else(|_| std::fs::copy(&part, dst).map(|_| ())).map_err(|e| format!("can't write the cache ({e})"))?;
    let _ = std::fs::remove_file(&part);
    Ok(b)
}

/// Windows' own curl.exe (System32) when it's there, else whatever `curl` is on PATH.
fn curl() -> PathBuf {
    if let Ok(root) = std::env::var("SystemRoot") {
        let p = Path::new(&root).join("System32").join("curl.exe");
        if p.is_file() {
            return p;
        }
    }
    PathBuf::from("curl")
}

/// A test pattern shaped like a card (NOT a scan): a coloured border, a gradient "art box" and text-ish bars, with
/// transparent rounded corners. Tests and the snapshot scene use it instead of the network.
pub fn fixture(w: usize, h: usize) -> Scan {
    let mut px = vec![[0u8; 4]; w * h];
    let r = (w.min(h) / 18).max(2) as i64;
    for y in 0..h {
        for x in 0..w {
            let (xi, yi, wi, hi) = (x as i64, y as i64, w as i64, h as i64);
            let cx = if xi < r { r - xi } else if xi >= wi - r { xi - (wi - r - 1) } else { 0 };
            let cy = if yi < r { r - yi } else if yi >= hi - r { yi - (hi - r - 1) } else { 0 };
            if cx * cx + cy * cy > r * r {
                continue; // a rounded corner: transparent
            }
            let border = x < w / 22 || y < w / 22 || x >= w - w / 22 || y >= h - w / 22;
            let art = y > h / 9 && y < h * 11 / 20 && x > w / 11 && x < w * 10 / 11;
            let bar = y > h * 12 / 20 && (y / (h / 24).max(1)) % 2 == 0 && x > w / 9 && x < w * 8 / 9;
            px[y * w + x] = if border {
                [0xf0, 0xc8, 0x50, 255]
            } else if art {
                [(x * 255 / w) as u8, (y * 255 / h) as u8, 0xc0, 255]
            } else if bar {
                [0x50, 0x50, 0x58, 255]
            } else {
                [0xe8, 0xe4, 0xd8, 255]
            };
        }
    }
    Scan { w, h, px }
}

/// The fixture as a PNG file's bytes.
#[cfg(test)]
pub fn fixture_png(w: usize, h: usize) -> Vec<u8> {
    let s = fixture(w, h);
    let mut out = Vec::new();
    {
        let mut e = png::Encoder::new(&mut out, w as u32, h as u32);
        e.set_color(png::ColorType::Rgba);
        e.set_depth(png::BitDepth::Eight);
        let mut wr = e.write_header().expect("png header");
        let data: Vec<u8> = s.px.iter().flat_map(|p| p.iter().copied()).collect();
        wr.write_image_data(&data).expect("png data");
    }
    out
}

/// Swallows a late DA1 reply that arrives as keystrokes ([ESC] [ ? 6 1 ; 4 ... c; on Windows without the ESC) so it
/// can't act as binder keys. Feed it every key event after a probe that got no reply; it holds an ESC or "[" for
/// a moment to see whether "[?" follows, and gives them back when not.
#[derive(Default)]
pub struct ReplyFilter {
    held: Vec<char>,
    pub armed: bool,
}

/// What to do with a key event.
#[derive(Debug, PartialEq, Eq)]
pub enum Filtered {
    /// deliver these (a held ESC comes back with the event after it)
    Pass(Vec<char>),
    /// part of a reply (or held): drop for now
    Drop,
    /// a reply ended
    End,
}

impl ReplyFilter {
    /// `c`: the key as a char ('\x1b' for Esc); None: any other key (it ends a held ESC too).
    pub fn feed(&mut self, c: Option<char>) -> Filtered {
        if !self.armed {
            return Filtered::Pass(c.into_iter().collect());
        }
        let inside = self.held.contains(&'?');
        match c {
            Some('\x1b') if self.held.is_empty() => self.held.push('\x1b'),
            Some('[') if self.held.is_empty() || self.held == ['\x1b'] => self.held.push('['),
            Some('?') if self.held.last() == Some(&'[') => self.held.push('?'),
            Some('c') if inside => {
                self.held.clear();
                self.armed = false;
                return Filtered::End;
            }
            Some(ch) if inside && (ch.is_ascii_digit() || ch == ';') => {}
            x => {
                // not a reply: what was held were keys (a broken-off reply is dropped)
                let mut out = std::mem::take(&mut self.held);
                if inside {
                    out.clear();
                }
                out.extend(x);
                return Filtered::Pass(out);
            }
        }
        Filtered::Drop
    }

    /// Input went quiet: an ESC or "[" still held was a key press (a reply half-way through stays held).
    pub fn flush(&mut self) -> Vec<char> {
        if self.held.contains(&'?') { vec![] } else { std::mem::take(&mut self.held) }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tmp(name: &str) -> PathBuf {
        let d = std::env::temp_dir().join(format!("binder-real-{name}-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&d);
        std::fs::create_dir_all(&d).unwrap();
        d
    }

    #[test]
    fn settings_and_da1() {
        assert_eq!(setting(None, None), Setting::Auto);
        assert_eq!(setting(Some("off"), Some("on")), Setting::Off, "the environment wins");
        assert_eq!(setting(Some("bogus"), Some("on")), Setting::On);
        assert_eq!(setting(None, Some(" 0 ")), Setting::Off);
        assert_eq!(da1_has_sixel("\x1b[?61;4;6;7;14;21;22;23;24;28;32;42c"), Some(true), "Windows Terminal 1.22+");
        assert_eq!(da1_has_sixel("\x1b[?1;0c"), Some(false), "a VT100: no sixel");
        assert_eq!(da1_has_sixel("[?61;6;7;21;22;23;24;28;32;42c"), Some(false), "Windows 11's own console (no ESC, as crossterm sees it)");
        assert_eq!(da1_has_sixel("\x1b[?62;14;22c"), Some(false), "14 is not 4");
        assert_eq!(da1_has_sixel("garbage"), None);
        assert_eq!(cell_px(Some("9x18")), (9, 18));
        assert_eq!(cell_px(Some("nope")), WT_CELL);
        assert_eq!(cell_px(None), WT_CELL);
    }

    #[test]
    fn urls_and_cache_paths() {
        assert_eq!(urls("swsh7-215", None), Some(("https://images.pokemontcg.io/swsh7/215_hires.png".into(), "https://images.pokemontcg.io/swsh7/215.png".into())));
        assert_eq!(urls("swsh12pt5gg-GG36", None).unwrap().1, "https://images.pokemontcg.io/swsh12pt5gg/GG36.png");
        assert_eq!(urls("base1-44", Some("https://images.pokemontcg.io/base1/44_hires.png")).unwrap().1, "https://images.pokemontcg.io/base1/44.png");
        assert_eq!(urls("x-1", Some("https://example.com/a.jpg")).unwrap(), ("https://example.com/a.jpg".into(), "https://example.com/a.jpg".into()));
        assert_eq!(urls("pikachu", None), None, "not a card id");
        assert_eq!(urls("a-b/../c", None), None);
        let d = Path::new("C:/state/cache/realcards");
        assert_eq!(cache_path(d, "https://images.pokemontcg.io/swsh7/215_hires.png"), d.join("swsh7").join("215_hires.png"));
        assert_eq!(cache_path(d, "https://h/../../evil/x?.png"), d.join("evil").join("x"), "no .. escapes");
    }

    #[test]
    fn layout_beside_or_swap() {
        // the printed card is as tall as ours; half blocks and WT's sixel cell agree on its width
        assert_eq!(real_w(28, (1, 2)), 40);
        assert_eq!(real_w(28, WT_CELL), 40);
        assert_eq!(real_w(28, (8, 20)), 50, "narrower cells: more columns");
        assert_eq!(place(100, 40, 28, WT_CELL), Place::Beside);
        assert_eq!(place(81, 40, 28, WT_CELL), Place::Swap);
        assert_eq!(place(82, 40, 28, WT_CELL), Place::Beside, "exactly ours + gap + the printed card");
    }

    #[test]
    fn decode_resize_blocks_sixel() {
        let png = fixture_png(61, 85);
        let s = decode_png(&png).unwrap();
        assert_eq!((s.w, s.h), (61, 85));
        assert_eq!(s.px[0][3], 0, "rounded corner is transparent");
        assert!(decode_png(b"not a png").is_err());
        let r = resize(&s, 20, 28);
        assert_eq!(r.len(), 20 * 28);
        let cells = blocks(&s, 20, 14);
        assert_eq!(cells.len(), 20 * 14);
        assert!(cells.iter().any(|c| c.0 == "▀" && c.1.is_some() && c.2.is_some()));
        let six = sixel(&s, 100, 140);
        assert!(six.starts_with("\x1bP0;1;0q\"1;1;100;140"));
        assert!(six.ends_with("\x1b\\"));
        assert_eq!(six.matches('-').count(), 140usize.div_ceil(6), "one graphics newline per 6-pixel band");
        assert!(six.bytes().all(|b| b == 0x1b || (0x20..0x7f).contains(&b)), "7-bit sixel data only");
        let pal = median_cut(&[[0, 0, 0], [255, 255, 255], [250, 250, 250], [5, 5, 5]], 2);
        assert_eq!(pal.len(), 2);
    }

    #[test]
    fn cache_then_memory_no_network() {
        let d = tmp("cache");
        let url = "https://images.pokemontcg.io/swsh7/215_hires.png";
        let mut rc = RealCards::new(d.clone(), false, Setting::Auto, WT_CELL);
        assert_eq!(rc.gfx(), Gfx::Blocks, "headless auto: half blocks, no probe");
        assert!(matches!(rc.status(url), Status::Failed(_)), "not cached and no fetching: a message, not a hang");
        std::fs::create_dir_all(d.join("swsh7")).unwrap();
        std::fs::write(d.join("swsh7").join("215_hires.png"), fixture_png(40, 56)).unwrap();
        rc.retry();
        assert!(matches!(rc.status(url), Status::Ready(_)), "from the disk cache");
        assert!(rc.sixel_for(url, 4, 3).is_some());
        // a broken cache file is dropped, not shown
        std::fs::write(d.join("swsh7").join("1_hires.png"), b"junk").unwrap();
        assert!(matches!(rc.status("https://images.pokemontcg.io/swsh7/1_hires.png"), Status::Failed(_)));
        assert!(!d.join("swsh7").join("1_hires.png").exists());
        let _ = std::fs::remove_dir_all(&d);
    }

    /// The download path end to end with a file:// URL (curl reads it: no network), then a missing file.
    #[test]
    fn fetch_in_background_from_a_local_file() {
        let d = tmp("fetch");
        let src = d.join("fixture.png");
        std::fs::write(&src, fixture_png(30, 42)).unwrap();
        let url = format!("file:///{}", src.display().to_string().replace('\\', "/").trim_start_matches('/'));
        let mut rc = RealCards::new(d.join("cache"), true, Setting::Off, WT_CELL);
        assert_eq!(rc.gfx(), Gfx::Blocks);
        assert!(matches!(rc.status(&url), Status::Loading));
        let t = std::time::Instant::now();
        while rc.busy() && t.elapsed().as_secs() < 30 {
            rc.poll();
            std::thread::sleep(std::time::Duration::from_millis(20));
        }
        match rc.status(&url) {
            Status::Ready(s) => assert_eq!((s.w, s.h), (30, 42)),
            Status::Failed(e) => panic!("fetch failed: {e}"),
            Status::Loading => panic!("still loading"),
        }
        assert!(cache_path(&d.join("cache"), &url).is_file(), "cached for next time");
        let bad = format!("{url}.missing.png");
        assert!(matches!(rc.status(&bad), Status::Loading));
        let t = std::time::Instant::now();
        while rc.busy() && t.elapsed().as_secs() < 30 {
            rc.poll();
            std::thread::sleep(std::time::Duration::from_millis(20));
        }
        assert!(matches!(rc.status(&bad), Status::Failed(_)));
        let _ = std::fs::remove_dir_all(&d);
    }

    #[test]
    fn late_da1_reply_is_swallowed() {
        let mut f = ReplyFilter { armed: true, ..Default::default() };
        let mut passed = vec![];
        for c in "\x1b[?61;4;6c".chars() {
            if let Filtered::Pass(v) = f.feed(Some(c)) {
                passed.extend(v);
            }
        }
        assert!(passed.is_empty());
        assert!(!f.armed, "one reply, then the filter is off");
        assert_eq!(f.feed(Some('q')), Filtered::Pass(vec!['q']));
        // a real Esc press while armed: held, then given back
        let mut f = ReplyFilter { armed: true, ..Default::default() };
        assert_eq!(f.feed(Some('\x1b')), Filtered::Drop);
        assert_eq!(f.flush(), vec!['\x1b']);
        assert_eq!(f.feed(Some('\x1b')), Filtered::Drop);
        assert_eq!(f.feed(Some('j')), Filtered::Pass(vec!['\x1b', 'j']));
        // Windows: the console hands the reply over without its ESC
        let mut f = ReplyFilter { armed: true, ..Default::default() };
        assert!("[?61;6;7;21;22;23;24;28;32;42c".chars().all(|c| !matches!(f.feed(Some(c)), Filtered::Pass(_))));
        assert!(!f.armed);
        // "[" pressed on its own (previous pack) while armed: given back with the next key, or when input goes quiet
        let mut f = ReplyFilter { armed: true, ..Default::default() };
        assert_eq!(f.feed(Some('[')), Filtered::Drop);
        assert_eq!(f.feed(Some('[')), Filtered::Pass(vec!['[', '[']));
        assert_eq!(f.feed(Some('[')), Filtered::Drop);
        assert_eq!(f.flush(), vec!['[']);
        assert_eq!(f.feed(None), Filtered::Pass(vec![]), "an arrow key passes (the caller hands the event on)");
    }
}
