//! The web binder export (`binder --export-web <out>`; `pokeshell binder --web` runs it, then opens the page):
//! pulls.log + pack.json -> data.json, art PNGs and a baked single-file page. Nothing stays running, and it needs no
//! Python (it replaced tools/binder_web.py, whose output it keeps: the same data.json, byte for byte, and the same
//! PNGs, pixel for pixel).
//!
//!   binder --export-web <out> [--root <checkout>] [--state <dir>] [--log <pulls.log>] [--owner <name>] [--no-art]
//!                           [--only <card id>,<card id>...]
//!
//! --only (`pokeshell pack open --export`): incremental. Only the named cards' images (and their shiny forms) are checked
//! and rendered; every other image the art cache already has is kept as it is (its source isn't even looked at) and
//! nothing is pruned. data.json and binder.html are rewritten in full as always. A card the cache doesn't know yet is
//! rendered either way, so --only never leaves a hole.
//!
//! Reads
//!   <state>/pulls.log                       TSV: time, pack, character, tier, art, skin, shiny(0/1), flags, [key=value...]
//!                                           (read lossily: a line with bytes that aren't UTF-8 or a bad time is skipped)
//!   <state>/viewed.txt                      pull ids the binder has shown (no NEW sticker)
//!   <state>/config.txt                      pack= (active packs), best_since=
//!   packs/<pack>/pack.json                  characters, names, tags, tiers, skins + weights, odds (+ cards, retired)
//!   packs/<pack>/cards/<id>.json            a real card's text half (docs/CARD_FORMAT.md): HP, attacks, weakness...
//!   packs/<pack>/art/<id>.json              pixel grids (onepiece; falls back to ../opshell)
//!   dist/<pack>/<character>-<card id>[-shiny].ans   a real card's art (half-block ANSI -> pixels)
//!   dist/pokedex/<id>-common[-shiny].ans    pokedex sprites (half-block ANSI -> pixels)
//!   packs/<pack>/shaders/<skin>.hlsl        the header comment becomes the skin's description
//!   tools/binder-web/index.html             the page (a module install has no tools\: the copy built into binder.exe)
//!
//! Writes (into <out>; every file is written to a temp name and swapped in)
//!   data.json                               everything the page needs
//!   img/<pack>/<character>/<tier or card id>[-shiny].png   1 px per art pixel: every built card, shiny forms that were pulled
//!   img/<pack>/<character>/_seen.png, <card id>-seen.png   a seen card's silhouette, when no exported art gives it (below)
//!   img/pokedex/_silhouettes.png            atlas of all 905 pokedex silhouettes (alpha only): the dex characters' tints
//!   img/.cache.json                         decoded-art cache (source mtime + size -> PNG size, tint): reruns skip decoding.
//!                                           Sources are keyed by their path relative to --root, so a copy of the
//!                                           checkout / module (a module install's <state>\current, a new module version,
//!                                           a copied state folder) keeps the cache; entries of older caches that named
//!                                           an absolute path still match on the same relative path, mtime and size
//!   img/.meta.json                          card-text cache: each real card's display fields and text half, keyed by
//!                                           its cards/<id>.json (relative path, mtime, size) and its pack.json entry
//!   binder.html                             the page with data.json inlined (with the img/ folder)
//! PNGs that no current card needs are pruned from img/ (not with --no-art, which leaves img/ alone).
//!
//! Swapping art: drop a PNG into tools/binder-web/art-override/<pack>/<character>/<tier>[-shiny].png and it is copied
//! instead of rendered.
//!
//! The earned rule (docs/BINDER_SPEC.md, the same as Pokeshell.cs ReadPulls): a pull line with an id and the
//! "pending" flag is pending until an `earned:<id>` line; it expires on an `expired:<id>` line, after 24 h, or when its
//! boot session (boot=) is over. Earned pulls export as status "collected" (caught), with "new" when viewed.txt doesn't
//! list them; the others as "pending" (its tab can still catch it) or "expired": both are seen, never counted, and the
//! page shows a seen card as its silhouette. Lines without an id are earned. Pulls that don't resolve to a current card
//! (unknown or `retired` in pack.json) are left out; pulls.log is never rewritten. An empty or seen card's text half and
//! printed-card scan (the page's `p`) are left out of data.json: caught cards only.
//!
//! A seen card's silhouette (docs/BINDER_SPEC.md "Empty, seen, caught"; the same order as ArtStore::silhouette): a
//! real card whose art is the plain sprite (it has transparent pixels, the commons; "sprite" on the card) is its own; a
//! scene card takes one of its character's commons ("seen" on the character: that image), else the colorscripts sprite
//! (vendor/pokemon-colorscripts large, or dist/pokedex/<character>-common.ans: _seen.png), else its own art's sprite
//! layer (the pixels its shiny art recolours, plus the dark outline, holes filled: <card id>-seen.png). Other packs use
//! their base art (grid) or the pulled sprite (dex). The page draws any of them as a flat shadow.
//!
//! Compatibility notes: the JSON is written the way Python's json.dumps(ensure_ascii=False, separators=(",", ":"))
//! writes it (floats as Python's repr, keys in insertion order), and the rules below keep Python's semantics where they
//! show in the output (truthiness, str.title, splitlines, round).

use serde_json::{Map, Number, Value, json};
use std::cell::RefCell;
use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::rc::Rc;
use std::time::Instant;

type Obj = Map<String, Value>;
type Rgb = [u8; 3];
type Grid = Vec<Vec<Option<Rgb>>>;

/// The page, built in: a module install ships no tools\ folder (a checkout's tools/binder-web/index.html wins).
const PAGE: &str = include_str!("../../tools/binder-web/index.html");
const MARKER: &str = "/*__INLINE_DATA__*/null";
const PACK_ORDER: [&str; 3] = ["pokemon", "onepiece", "pokedex"];
const EXPIRE_SECS: f64 = 24.0 * 3600.0; // Pokeshell.cs ExpireSec
const BOOT_SLACK_SECS: i64 = 120; // Pokeshell.cs BootSlackSec
const CROCKFORD: &str = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";
const DEFAULT_TINT: &str = "#9aa4b0";
/// a card art with at least this share of transparent pixels is a plain sprite (a scene has none)
const SPRITE_CLEAR: f64 = 0.1;
const CACHE_VERSION: i64 = 3;

// frame presets from scripts/lib/Pokeshell.cs (FramePresets) and the wanted-poster palettes (WantedPalettes)
const FRAME_PRESETS: [(&str, &[&str]); 5] = [
    ("plain", &["#c9a93a", "#f4dc6a", "#c9a93a"]),
    ("silver", &["#8d97a5", "#eef3f8", "#9aa6b4", "#f7fafc", "#8d97a5"]),
    ("holo", &["#7fa7d9", "#e6f0ff", "#b59ce0", "#e8fbff", "#7fd3c9"]),
    ("rainbow", &["#ff6b8b", "#ffb86b", "#ffe66b", "#7df09a", "#6bd5ff", "#9a8bff", "#ff6bd6"]),
    ("gold", &["#b8862b", "#fff1b0", "#d4a43a", "#fff7d6", "#c8952e"]),
];
// paper, stain, ink, accent; "" paper = gold leaf
const WANTED_PALETTES: [(&str, &[&str]); 4] = [
    ("common", &["#e6d3a3", "#cfb57c", "#3b2616", "#3b2616"]),
    ("super-rare", &["#cfa467", "#9c7040", "#2a170a", "#8e1b12"]),
    ("secret-rare", &["", "", "#3a2408", "#7a1a10"]),
    ("manga", &["#ecebe4", "#c9c8c0", "#111111", "#c8281e"]),
];
const SUFFIX_WORDS: [&str; 12] = ["V", "VMAX", "VSTAR", "GX", "EX", "ex", "BREAK", "LV.X", "Prime", "δ", "◇", "☆"];
const SUFFIX_WORDS2: [&str; 2] = ["Star", "Radiant"];

fn preset(name: &str) -> Option<Value> {
    FRAME_PRESETS.iter().find(|(n, _)| *n == name).map(|(_, c)| json!(c))
}

fn wanted(name: Option<&str>) -> Value {
    let f = |n: &str| WANTED_PALETTES.iter().find(|(k, _)| *k == n).map(|(_, c)| json!(c));
    name.and_then(f).unwrap_or_else(|| f("common").unwrap())
}

// ---------------------------------------------------------------- Python semantics

fn truthy(v: &Value) -> bool {
    match v {
        Value::Null => false,
        Value::Bool(b) => *b,
        Value::Number(n) => n.as_f64().is_some_and(|f| f != 0.0),
        Value::String(s) => !s.is_empty(),
        Value::Array(a) => !a.is_empty(),
        Value::Object(o) => !o.is_empty(),
    }
}

/// `o.get(k) or default`
fn get_or(o: &Value, k: &str, default: Value) -> Value {
    match o.get(k) {
        Some(v) if truthy(v) => v.clone(),
        _ => default,
    }
}

/// `o.get(k, default)` (a present null stays null)
fn get_default(o: &Value, k: &str, default: Value) -> Value {
    o.get(k).cloned().unwrap_or(default)
}

/// int(v): a number (truncated), a numeric string, a bool; anything else 0
fn py_int(v: &Value) -> i64 {
    match v {
        Value::Number(n) => n.as_i64().unwrap_or_else(|| n.as_f64().map(|f| f.trunc() as i64).unwrap_or(0)),
        Value::String(s) => s.trim().replace('_', "").parse::<i64>().unwrap_or(0),
        Value::Bool(b) => *b as i64,
        _ => 0,
    }
}

/// float(v)
fn py_float(v: &Value) -> f64 {
    match v {
        Value::Number(n) => n.as_f64().unwrap_or(0.0),
        Value::String(s) => s.trim().parse::<f64>().unwrap_or(0.0),
        Value::Bool(b) => *b as i64 as f64,
        _ => 0.0,
    }
}

/// str(v) for the scalars card data holds
fn py_str(v: &Value) -> String {
    match v {
        Value::String(s) => s.clone(),
        Value::Number(n) if n.is_f64() => py_repr_f64(n.as_f64().unwrap_or(0.0)),
        Value::Number(n) => n.to_string(),
        Value::Bool(true) => "True".into(),
        Value::Bool(false) => "False".into(),
        Value::Null => "None".into(),
        other => other.to_string(),
    }
}

fn fnum(f: f64) -> Value {
    Number::from_f64(f).map(Value::Number).unwrap_or(Value::Null)
}

fn s(v: &str) -> Value {
    Value::String(v.to_string())
}

/// str.title(): a letter after a cased letter is lower case, any other letter upper case
fn title(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    let mut prev_cased = false;
    for c in s.chars() {
        let cased = c.is_lowercase() || c.is_uppercase();
        if prev_cased {
            out.extend(c.to_lowercase());
        } else {
            out.extend(c.to_uppercase());
        }
        prev_cased = cased;
    }
    out
}

/// str.splitlines()
fn splitlines(s: &str) -> Vec<&str> {
    let mut out = vec![];
    let mut start = 0;
    let mut it = s.char_indices().peekable();
    while let Some((i, c)) = it.next() {
        let brk = matches!(c, '\n' | '\r' | '\x0b' | '\x0c' | '\x1c' | '\x1d' | '\x1e' | '\u{85}' | '\u{2028}' | '\u{2029}');
        if brk {
            out.push(&s[start..i]);
            let mut end = i + c.len_utf8();
            if c == '\r' {
                if let Some(&(_, '\n')) = it.peek() {
                    it.next();
                    end += 1;
                }
            }
            start = end;
        }
    }
    if start < s.len() {
        out.push(&s[start..]);
    }
    out
}

fn py_strip(s: &str) -> &str {
    s.trim_matches(|c: char| c.is_whitespace() || ('\x1c'..='\x1f').contains(&c))
}

/// Python's repr of a float (what json.dumps writes): the shortest round-trip digits, fixed notation for exponents
/// -4..16, else d.ddde+XX
fn py_repr_f64(f: f64) -> String {
    if f.is_nan() {
        return "NaN".into();
    }
    if f.is_infinite() {
        return if f > 0.0 { "Infinity" } else { "-Infinity" }.into();
    }
    if f == 0.0 {
        return if f.is_sign_negative() { "-0.0" } else { "0.0" }.into();
    }
    let e = format!("{:e}", f.abs());
    let (mant, exp) = e.split_once('e').unwrap_or((&e, "0"));
    let exp: i32 = exp.parse().unwrap_or(0);
    let digits: String = mant.chars().filter(|c| *c != '.').collect();
    let body = if (-4..16).contains(&exp) {
        if exp >= 0 {
            let k = exp as usize + 1;
            if digits.len() <= k { format!("{}{}.0", digits, "0".repeat(k - digits.len())) } else { format!("{}.{}", &digits[..k], &digits[k..]) }
        } else {
            format!("0.{}{}", "0".repeat((-exp - 1) as usize), digits)
        }
    } else {
        let m = if digits.len() > 1 { format!("{}.{}", &digits[..1], &digits[1..]) } else { digits.clone() };
        format!("{}e{}{:02}", m, if exp < 0 { '-' } else { '+' }, exp.abs())
    };
    if f < 0.0 { format!("-{body}") } else { body }
}

/// round(x, 3), correctly rounded, ties to even (Python's)
fn round3(x: f64) -> f64 {
    let y = x * 1000.0;
    let t = x * 16.0;
    if t.fract() == 0.0 && (t as i64) % 2 != 0 && y.fract().abs() == 0.5 {
        return y.round_ties_even() / 1000.0; // an exact tie (x = odd/16)
    }
    format!("{x:.3}").parse().unwrap_or(x)
}

/// json.dumps(v, separators=(",", ":"), ensure_ascii=ascii)
fn dumps(v: &Value, ascii: bool) -> String {
    let mut out = String::with_capacity(1 << 16);
    write_json(v, &mut out, ascii);
    out
}

fn write_json(v: &Value, out: &mut String, ascii: bool) {
    match v {
        Value::Null => out.push_str("null"),
        Value::Bool(b) => out.push_str(if *b { "true" } else { "false" }),
        Value::Number(n) => {
            if n.is_f64() {
                out.push_str(&py_repr_f64(n.as_f64().unwrap_or(0.0)))
            } else {
                out.push_str(&n.to_string())
            }
        }
        Value::String(s) => write_str(s, out, ascii),
        Value::Array(a) => {
            out.push('[');
            for (i, x) in a.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                write_json(x, out, ascii);
            }
            out.push(']');
        }
        Value::Object(o) => {
            out.push('{');
            for (i, (k, x)) in o.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                write_str(k, out, ascii);
                out.push(':');
                write_json(x, out, ascii);
            }
            out.push('}');
        }
    }
}

fn write_str(s: &str, out: &mut String, ascii: bool) {
    use std::fmt::Write;
    out.push('"');
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            '\x08' => out.push_str("\\b"),
            '\x0c' => out.push_str("\\f"),
            c if (c as u32) < 0x20 => {
                let _ = write!(out, "\\u{:04x}", c as u32);
            }
            c if ascii && (c as u32) > 0x7e => {
                let mut buf = [0u16; 2];
                for u in c.encode_utf16(&mut buf) {
                    let _ = write!(out, "\\u{:04x}", u);
                }
            }
            c => out.push(c),
        }
    }
    out.push('"');
}

// ---------------------------------------------------------------- files

/// a text file, read lossily (a stray ANSI byte from PowerShell 5 becomes U+FFFD instead of a crash), BOM dropped
fn read_text(path: &Path) -> Option<String> {
    let b = fs::read(path).ok()?;
    let t = String::from_utf8_lossy(&b).into_owned();
    Some(t.strip_prefix('\u{feff}').map(str::to_string).unwrap_or(t))
}

/// Python's text-mode read (universal newlines: \r\n and \r become \n), lossy, the BOM kept
fn read_universal(path: &Path) -> Option<String> {
    let b = fs::read(path).ok()?;
    Some(String::from_utf8_lossy(&b).replace("\r\n", "\n").replace('\r', "\n"))
}

/// write to a temp file next to path, then swap it in (a browser never reads half a file)
fn write_atomic(path: &Path, data: &[u8]) -> std::io::Result<()> {
    if let Some(d) = path.parent() {
        fs::create_dir_all(d)?;
    }
    let name = path.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
    let tmp = path.with_file_name(format!(".{}.{}.tmp", name, std::process::id()));
    fs::write(&tmp, data)?;
    fs::rename(&tmp, path)
}

/// text as Python's write_text writes it (\n becomes \r\n on Windows)
fn text_bytes(s: &str) -> Vec<u8> {
    if cfg!(windows) { s.replace('\n', "\r\n").into_bytes() } else { s.as_bytes().to_vec() }
}

fn path_str(p: &Path) -> String {
    let s = p.to_string_lossy().into_owned();
    if cfg!(windows) { s.replace('/', "\\") } else { s }
}

fn warn(msg: &str) {
    eprintln!("warning: {msg}");
}

// ---------------------------------------------------------------- pulls

#[derive(Clone, Debug)]
struct Pull {
    id: usize,
    pull: String,
    card: String,
    time: String,
    pack: String,
    ch: String,
    tier: String,
    art: String,
    skin: String,
    shiny: bool,
    flags: Vec<String>,
    status: &'static str,
    new: bool,
}

impl Pull {
    fn to_value(&self) -> Value {
        let opt = |s: &str| if s.is_empty() { Value::Null } else { Value::String(s.to_string()) };
        json!({
            "id": self.id, "pull": opt(&self.pull), "card": opt(&self.card), "time": self.time, "pack": self.pack,
            "char": self.ch, "tier": self.tier, "art": self.art, "skin": opt(&self.skin), "shiny": self.shiny,
            "flags": self.flags, "status": self.status, "new": self.new,
        })
    }
}

/// unix seconds in a ULID pull id, or None
fn ulid_secs(pid: &str) -> Option<f64> {
    if pid.chars().count() != 26 {
        return None;
    }
    let mut ms: i64 = 0;
    for ch in pid.chars().take(10) {
        let v = CROCKFORD.find(ch.to_ascii_uppercase())? as i64;
        ms = ms * 32 + v;
    }
    Some(ms as f64 / 1000.0)
}

/// `\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?([+-]\d{2}:?\d{2}|Z)?` in full
fn is_time(s: &str) -> bool {
    let b = s.as_bytes();
    let mut i = 0;
    let digits = |i: &mut usize, n: usize| -> bool {
        for _ in 0..n {
            if *i < b.len() && b[*i].is_ascii_digit() {
                *i += 1;
            } else {
                return false;
            }
        }
        true
    };
    let lit = |i: &mut usize, c: u8| -> bool {
        if *i < b.len() && b[*i] == c {
            *i += 1;
            true
        } else {
            false
        }
    };
    if !(digits(&mut i, 4) && lit(&mut i, b'-') && digits(&mut i, 2) && lit(&mut i, b'-') && digits(&mut i, 2)) {
        return false;
    }
    if !(lit(&mut i, b'T') || lit(&mut i, b' ')) {
        return false;
    }
    if !(digits(&mut i, 2) && lit(&mut i, b':') && digits(&mut i, 2)) {
        return false;
    }
    if i + 2 < b.len() && b[i] == b':' && b[i + 1].is_ascii_digit() && b.get(i + 2).is_some_and(|c| c.is_ascii_digit()) {
        i += 3;
        if i + 1 < b.len() && b[i] == b'.' && b[i + 1].is_ascii_digit() {
            i += 1;
            while i < b.len() && b[i].is_ascii_digit() {
                i += 1;
            }
        }
    }
    if i < b.len() && b[i] == b'Z' {
        i += 1;
    } else if i < b.len() && (b[i] == b'+' || b[i] == b'-') {
        i += 1;
        if !digits(&mut i, 2) {
            return false;
        }
        let save = i;
        if !(lit(&mut i, b':') && digits(&mut i, 2)) {
            i = save;
            if !digits(&mut i, 2) {
                return false;
            }
        }
    }
    i == b.len()
}

/// pulls.log with the earned rule applied (see the module doc). Lines that can't be read (bytes that aren't UTF-8, a
/// time that isn't ISO) are skipped and counted in `bad`.
fn read_pulls(log: &Path, viewed: &HashSet<String>, now: f64, boot: i64, bad: &mut usize) -> Vec<Pull> {
    let mut pulls = vec![];
    if !log.exists() {
        warn(&format!("no pulls log at {}", path_str(log)));
        return pulls;
    }
    let text = read_text(log).unwrap_or_default();
    let lines = splitlines(&text);
    let (mut earned, mut expired) = (HashSet::new(), HashSet::new());
    for line in &lines {
        let f: Vec<&str> = line.split('\t').collect();
        if (2..7).contains(&f.len()) {
            let ev = py_strip(f[1]);
            if let Some(x) = ev.strip_prefix("earned:") {
                earned.insert(x.to_string());
            } else if let Some(x) = ev.strip_prefix("expired:") {
                expired.insert(x.to_string());
            }
        }
    }
    for (n, line) in lines.iter().enumerate() {
        let f: Vec<&str> = line.split('\t').collect();
        if f.len() < 7 {
            continue;
        }
        let flags = if f.len() >= 8 { py_strip(f[7]) } else { "" };
        if flags.contains("dryrun") {
            continue; // same rule as Read-Pulls in scripts/pokeshell.ps1
        }
        if line.contains('\u{fffd}') || !is_time(py_strip(f[0])) {
            *bad += 1; // mangled bytes or a corrupt time: not a pull we can show
            continue;
        }
        let mut kv: HashMap<&str, &str> = HashMap::new();
        for x in &f[8..] {
            if let Some((k, v)) = x.split_once('=') {
                kv.insert(k, v);
            }
        }
        let pid = py_strip(kv.get("id").copied().unwrap_or("")).to_string();
        let card = py_strip(kv.get("card").copied().unwrap_or("")).to_string();
        let pboot: i64 = kv.get("boot").map(|b| py_strip(b).parse().unwrap_or(0)).unwrap_or(0);
        let pending = flags.split(',').any(|x| py_strip(x) == "pending");
        let status = if pid.is_empty() || !pending || earned.contains(&pid) {
            "collected"
        } else if expired.contains(&pid) {
            "expired" // seen, not caught (docs/BINDER_SPEC.md "Empty, seen, caught")
        } else {
            let t = ulid_secs(&pid);
            let old = t.is_some_and(|t| now - t > EXPIRE_SECS) || (pboot != 0 && boot != 0 && (pboot - boot).abs() > BOOT_SLACK_SECS);
            if old { "expired" } else { "pending" } // expired: the tab was never used
        };
        pulls.push(Pull {
            id: n + 1,
            pull: pid.clone(),
            card,
            time: py_strip(f[0]).replace(' ', "T"),
            pack: f[1].to_string(),
            ch: f[2].to_string(),
            tier: f[3].to_string(),
            art: f[4].to_string(),
            skin: f[5].to_string(),
            shiny: py_strip(f[6]) == "1",
            flags: flags.split([',', ';', ' ']).filter(|x| !x.is_empty()).map(str::to_string).collect(),
            status,
            new: status == "collected" && !pid.is_empty() && !viewed.contains(&pid),
        });
    }
    pulls
}

// ---------------------------------------------------------------- packs

/// Directory listings, read once each: a file's existence, mtime and size come from its folder's listing (on Windows
/// read_dir returns them with every entry, so one listing replaces a stat per file: the export looks at every card's
/// art several times, thousands of files). Names are matched case-insensitively on Windows, like the file system.
#[derive(Default)]
struct DirCache {
    dirs: RefCell<HashMap<PathBuf, Rc<HashMap<String, (u64, u64, bool)>>>>,
}

impl DirCache {
    fn key(name: &str) -> String {
        if cfg!(windows) { name.to_lowercase() } else { name.to_string() }
    }

    fn listing(&self, dir: &Path) -> Rc<HashMap<String, (u64, u64, bool)>> {
        if let Some(l) = self.dirs.borrow().get(dir) {
            return l.clone();
        }
        let mut m = HashMap::new();
        if let Ok(rd) = fs::read_dir(dir) {
            for e in rd.flatten() {
                let name = e.file_name().to_string_lossy().into_owned();
                // DirEntry::metadata doesn't follow a link: a link (a symlinked file, a junction) is stat'ed
                let md = match e.metadata() {
                    Ok(md) if md.file_type().is_symlink() => fs::metadata(e.path()).ok(),
                    Ok(md) => Some(md),
                    Err(_) => fs::metadata(e.path()).ok(),
                };
                if let Some(md) = md {
                    m.insert(Self::key(&name), (mtime_ns(&md), md.len(), md.is_file()));
                }
            }
        }
        let l = Rc::new(m);
        self.dirs.borrow_mut().insert(dir.to_path_buf(), l.clone());
        l
    }

    /// (mtime ns, size) of a file, None when it isn't there (or is a folder)
    fn file(&self, p: &Path) -> Option<(u64, u64)> {
        let (Some(dir), Some(name)) = (p.parent(), p.file_name()) else { return None };
        self.listing(dir).get(&Self::key(&name.to_string_lossy())).filter(|e| e.2).map(|e| (e.0, e.1))
    }

    fn is_file(&self, p: &Path) -> bool {
        self.file(p).is_some()
    }

    /// a file is about to be written: forget its folder's listing
    fn touched(&self, p: &Path) {
        if let Some(dir) = p.parent() {
            self.dirs.borrow_mut().remove(dir);
        }
    }
}

struct Ctx {
    root: PathBuf,
    opshell: PathBuf,
    dirs: Rc<DirCache>,
    meta: RefCell<MetaCache>,
}

/// img/.meta.json: card_meta's result per real card, so a rerun doesn't read and parse every packs/<pack>/cards/<id>.json
/// (about 1,500 files). An entry is used while its key (the card file's relative path, mtime and size, and the card's
/// pack.json entry) is unchanged.
struct MetaCache {
    file: PathBuf,
    old: Obj,
    new: Obj,
    changed: bool,
}

const META_VERSION: i64 = 1;

impl MetaCache {
    fn new(file: PathBuf) -> MetaCache {
        let old = read_text(&file)
            .and_then(|t| serde_json::from_str::<Value>(&t).ok())
            .filter(|d| d.get("v") == Some(&json!(META_VERSION)))
            .and_then(|d| d.get("cards").and_then(|c| c.as_object()).cloned())
            .unwrap_or_default();
        MetaCache { file, old, new: Obj::new(), changed: false }
    }

    fn get(&mut self, id: &str, key: &str) -> Option<Obj> {
        let e = self.old.get(id)?;
        if e.get("k").and_then(|k| k.as_str()) != Some(key) {
            return None;
        }
        let m = e.get("m")?.as_object()?.clone();
        self.new.insert(id.to_string(), e.clone());
        Some(m)
    }

    fn put(&mut self, id: &str, key: &str, m: &Obj) {
        self.new.insert(id.to_string(), json!({"k": key, "m": m}));
        self.changed = true;
    }

    fn save(&self) {
        if !self.changed && self.new.len() == self.old.len() {
            return;
        }
        let doc = json!({"v": META_VERSION, "cards": self.new});
        if let Err(err) = write_atomic(&self.file, &text_bytes(&dumps(&doc, true))) {
            warn(&format!("can't write {}: {err}", path_str(&self.file)));
        }
    }
}

impl Ctx {
    /// a real card's art is built: dist/<pack>/<character>-<card id>.ans exists (the roll's test,
    /// Test-PokeshellCardBuilt in scripts/lib/common.ps1). Cards without it never roll.
    fn card_built(&self, pid: &str, ch: &str, cid: &str) -> bool {
        self.dirs.is_file(&self.root.join("dist").join(pid).join(format!("{ch}-{cid}.ans")))
    }

    /// pack.json with unbuilt cards muted (a real-card pack keeps only its built cards: an unbuilt card is no binder
    /// slot and pulls that resolve to it are hidden until its art is built), or None (missing, or not valid JSON:
    /// warned about unless quiet)
    fn load_pack_json(&self, pid: &str, quiet: bool) -> Option<Value> {
        let f = self.root.join("packs").join(pid).join("pack.json");
        if !f.exists() {
            return None;
        }
        let mut pk: Value = match read_text(&f).and_then(|t| serde_json::from_str(&t).map_err(|e| e.to_string()).ok().or_else(|| {
            if !quiet {
                let e = serde_json::from_str::<Value>(&t).err().map(|e| e.to_string()).unwrap_or_default();
                warn(&format!("{} is not valid JSON ({e}); pack left out", path_str(&f)));
            }
            None
        })) {
            Some(v) => v,
            None => return None,
        };
        if let Some(cards) = pk.get("cards").and_then(|c| c.as_object()) {
            let mut built = Obj::new();
            let mut unbuilt = vec![];
            for (cid, c) in cards {
                let ch = c.get("character").filter(|v| truthy(v)).map(py_str).unwrap_or_default();
                if self.card_built(pid, &ch, cid) {
                    built.insert(cid.clone(), c.clone());
                } else {
                    unbuilt.push(Value::String(cid.clone()));
                }
            }
            if let Some(o) = pk.as_object_mut() {
                o.insert("_unbuilt".into(), Value::Array(unbuilt));
                o.insert("cards".into(), Value::Object(built));
            }
        }
        Some(pk)
    }
}

/// the real card a pull line names itself (its card= or art column, same character), else None
fn logged_card(pk: &Value, ch: &str, art: &str, card: &str) -> Option<String> {
    let cards = pk.get("cards")?.as_object()?;
    [card, art].into_iter().find(|cid| !cid.is_empty() && cards.get(*cid).and_then(|c| c.get("character")).and_then(|v| v.as_str()) == Some(ch)).map(str::to_string)
}

/// what a pull shows today: (character, tier id, card id or ""), or None to hide it. The rule of
/// Resolve-PokeshellPull (scripts/lib/common.ps1, docs/PACK_FORMAT.md "retired"):
///   packs without "cards": as logged (tier by id, or by label);
///   real-card packs: the art column (or a card= column) is a card id of the pack whose character matches -> that
///   card; else retired["<character>/<tier>"] names a card -> that card; else hidden.
/// pk comes from load_pack_json: unbuilt cards are left out, so a pull resolving to one is hidden too
fn resolve_pull(pk: &Value, ch: &str, tier: &str, art: &str, card: &str) -> Option<(String, String, String)> {
    let Some(cards) = pk.get("cards").and_then(|c| c.as_object()) else {
        let empty = vec![];
        let tiers = pk.get("tiers").and_then(|t| t.as_array()).unwrap_or(&empty);
        let by_id = tiers.iter().find_map(|t| t.get("id").and_then(|v| v.as_str()).filter(|id| *id == tier));
        let t = by_id.or_else(|| {
            let want = tier.to_lowercase();
            tiers.iter().find(|x| x.get("label").and_then(|l| l.as_str()).unwrap_or("").to_lowercase() == want).and_then(|x| x.get("id")).and_then(|v| v.as_str())
        })?;
        let chars = pk.get("characters").and_then(|c| c.as_array());
        let known = chars.is_some_and(|a| a.iter().any(|c| c.as_str() == Some(ch)));
        return if !t.is_empty() && known { Some((ch.to_string(), t.to_string(), String::new())) } else { None };
    };
    if let Some(cid) = logged_card(pk, ch, art, card) {
        let t = cards[&cid].get("tier").map(py_str).unwrap_or_default();
        return Some((ch.to_string(), t, cid));
    }
    let now = pk.get("retired").and_then(|r| r.as_object()).and_then(|r| r.get(&format!("{ch}/{tier}"))).filter(|v| truthy(v))?;
    let now = now.as_str()?;
    let c = cards.get(now).filter(|c| truthy(c))?;
    Some((c.get("character").map(py_str).unwrap_or_default(), c.get("tier").map(py_str).unwrap_or_default(), now.to_string()))
}

/// each pull as the card it shows today; the ones that don't resolve (retired art, an unbuilt card) are left out and
/// counted. Also returns when the real cards went live: the time of the first shown pull whose line names a built real
/// card itself (the default best_since)
fn resolve_pulls(ctx: &Ctx, pulls: Vec<Pull>) -> (Vec<Pull>, usize, Option<String>) {
    let mut cache: HashMap<String, Option<Value>> = HashMap::new();
    let (mut out, mut hidden, mut real_since): (Vec<Pull>, usize, Option<String>) = (vec![], 0, None);
    for p in pulls {
        let pk = cache.entry(p.pack.clone()).or_insert_with(|| ctx.load_pack_json(&p.pack, true));
        let r = pk.as_ref().and_then(|pk| resolve_pull(pk, &p.ch, &p.tier, &p.art, &p.card));
        let Some((ch, tier, card)) = r else {
            hidden += 1;
            continue;
        };
        let pk = pk.as_ref().unwrap();
        if logged_card(pk, &p.ch, &p.art, &p.card).is_some() && real_since.as_ref().is_none_or(|r| p.time < *r) {
            real_since = Some(p.time.clone());
        }
        let card = if card.is_empty() { p.card.clone() } else { card };
        out.push(Pull { ch, tier, card, ..p });
    }
    (out, hidden, real_since)
}

/// config.txt best_since: "all" -> None (every pull); "YYYY-MM-DD[THH:MM[:SS]]" -> that local time (pull times compare
/// as ISO strings); anything else (unset) -> default, when the real cards went live
fn best_since(setting: Option<&str>, default: Option<String>) -> Option<String> {
    let v = py_strip(setting.unwrap_or(""));
    if v.to_lowercase() == "all" {
        return None;
    }
    let v = v.replace(' ', "T");
    let b = v.as_bytes();
    let d = |r: std::ops::Range<usize>| r.clone().all(|i| b.get(i).is_some_and(|c| c.is_ascii_digit()));
    let date = b.len() >= 10 && d(0..4) && b[4] == b'-' && d(5..7) && b[7] == b'-' && d(8..10);
    let ok = date
        && match b.len() {
            10 => true,
            16 => b[10] == b'T' && d(11..13) && b[13] == b':' && d(14..16),
            19 => b[10] == b'T' && d(11..13) && b[13] == b':' && d(14..16) && b[16] == b':' && d(17..19),
            _ => false,
        };
    if ok { Some(v) } else { default }
}

// ---------------------------------------------------------------- packs + odds

/// The shader's header comment: 'Imitates: ...' paragraph, flattened to one or two sentences.
fn skin_blurb(path: &Path) -> (Option<String>, Option<String>) {
    let Some(text) = read_universal(path) else {
        return (None, None);
    };
    let mut lines = vec![];
    for raw in splitlines(&text).into_iter().take(40) {
        let st = py_strip(raw);
        if !st.starts_with("//") {
            break;
        }
        lines.push(py_strip(st.trim_start_matches('/')).to_string());
    }
    let text = lines.iter().filter(|l| !l.is_empty() && !l.chars().all(|c| c == '=' || c == '-')).cloned().collect::<Vec<_>>().join(" ");
    let mut title_s: Option<String> = None;
    // Skin:\s*([^\n]+?)(?:\s+Imitates:|$)
    if let Some(i) = text.find("Skin:") {
        let after = &text[i + 5..];
        let rest = after.trim_start_matches(char::is_whitespace);
        if !rest.is_empty() {
            let mut cut = rest.len();
            for (j, c) in rest.char_indices() {
                if j > 0 && c.is_whitespace() && rest[j..].trim_start_matches(char::is_whitespace).starts_with("Imitates:") {
                    cut = j;
                    break;
                }
            }
            title_s = Some(py_strip(&rest[..cut]).to_string());
        } else if !after.is_empty() {
            title_s = Some(String::new());
        }
    }
    if title_s.is_none() {
        // ([A-Z0-9' .-]+?)\s+-\s+Windows Terminal, at the start
        let inclass = |c: char| c.is_ascii_uppercase() || c.is_ascii_digit() || matches!(c, '\'' | ' ' | '.' | '-');
        for (k, c) in text.char_indices() {
            if !inclass(c) {
                break;
            }
            let k = k + c.len_utf8();
            let rest = &text[k..];
            let r1 = rest.trim_start_matches(char::is_whitespace);
            if r1.len() < rest.len() {
                if let Some(r2) = r1.strip_prefix('-') {
                    let r3 = r2.trim_start_matches(char::is_whitespace);
                    if r3.len() < r2.len() && r3.starts_with("Windows Terminal") {
                        title_s = Some(py_strip(&text[..k]).to_string());
                        break;
                    }
                }
            }
        }
    }
    let title_s = title_s.filter(|t| !t.is_empty()).map(|t| {
        // "Shiny-Vault", "X (etched texture)": \s*\([^)]*\) removed, dashes to spaces
        let mut out = String::new();
        let mut i = 0;
        while i < t.len() {
            let rest = &t[i..];
            let ws = rest.len() - rest.trim_start_matches(char::is_whitespace).len();
            if rest[ws..].starts_with('(') {
                if let Some(close) = rest[ws..].find(')') {
                    i += ws + close + 1;
                    continue;
                }
            }
            let c = rest.chars().next().unwrap();
            out.push(c);
            i += c.len_utf8();
        }
        let out = py_strip(&out.replace('-', " ")).to_string();
        if out.is_empty() { t } else { out }
    });
    let desc = match text.find("Imitates:") {
        Some(i) if i + 9 < text.len() => text[i + 9..].to_string(),
        _ => text.clone(),
    };
    let desc = desc.split_whitespace().collect::<Vec<_>>().join(" ");
    // split after . ! ? before an upper-case letter
    let mut parts: Vec<&str> = vec![];
    let b = desc.as_bytes();
    let mut start = 0;
    for i in 1..b.len() {
        if b[i] == b' ' && matches!(b[i - 1], b'.' | b'!' | b'?') && b.get(i + 1).is_some_and(|c| c.is_ascii_uppercase()) {
            parts.push(&desc[start..i]);
            start = i + 1;
        }
    }
    parts.push(&desc[start..]);
    let mut out = String::new();
    for p in parts.into_iter().filter(|p| !p.contains("Windows Terminal") && !p.contains("ps_4") && !p.to_lowercase().contains("shader")) {
        if out.chars().count() + p.chars().count() > 260 && !out.is_empty() {
            break;
        }
        out = py_strip(&format!("{out} {p}")).to_string();
    }
    (title_s, Some(out.chars().take(320).collect()))
}

/// a card name without its mechanic words: "Rayquaza VMAX" -> "Rayquaza", "Radiant Charizard" -> "Charizard"
fn base_name(name: &str) -> String {
    let words: Vec<&str> = name.split_whitespace().filter(|w| !SUFFIX_WORDS.contains(w) && !SUFFIX_WORDS2.contains(w)).collect();
    if words.is_empty() { name.to_string() } else { words.join(" ") }
}

/// checklist order (as the app's): the numbered main run first (1, 2, ... 215; "215/203" -> 215, "25a" after "25"),
/// then each prefixed group in numeric order inside it (GG01..GG70, SV1..SV94, TG01..TG30), then letters alone (B, G,
/// R), then cards without a number
pub fn number_key(n: &str) -> (u8, String, i128, String, String) {
    let head = py_strip(n.split('/').next().unwrap_or(""));
    if head.is_empty() {
        return (3, String::new(), 0, String::new(), String::new());
    }
    let (prefix, digits, rest) = if head.contains('\n') {
        ("", "", head)
    } else {
        let p = head.len() - head.trim_start_matches(|c: char| c.is_ascii_alphabetic()).len();
        let d = head[p..].len() - head[p..].trim_start_matches(|c: char| c.is_ascii_digit()).len();
        (&head[..p], &head[p..p + d], &head[p + d..])
    };
    let num = if digits.is_empty() { -1 } else { digits.parse::<i128>().unwrap_or(i128::MAX) };
    let group = if prefix.is_empty() { 0 } else if !digits.is_empty() { 1 } else { 2 };
    (group, prefix.to_uppercase(), num, rest.to_lowercase(), head.to_string())
}

/// [x for x in (xs or []) if isinstance(x, str)]
fn energy(xs: Option<&Value>) -> Vec<Value> {
    match xs {
        Some(Value::Array(a)) => a.iter().filter(|x| x.is_string()).cloned().collect(),
        Some(Value::String(t)) => t.chars().map(|c| Value::String(c.to_string())).collect(),
        _ => vec![],
    }
}

/// the printed card's scan (the page's `p` toggle shows it beside ours, caught cards only): its card data's
/// images.large, else pokemontcg.io's image for the card id (<set>-<number>); None when the id isn't one. Only the URL
/// goes into data.json: the browser fetches the scan itself, nothing is downloaded or shipped here.
fn scan_url(cid: &str, large: Option<&Value>) -> Value {
    if let Some(l) = large.and_then(|v| v.as_str()) {
        let t = py_strip(l);
        if t.starts_with("https://") || t.starts_with("http://") {
            return s(t);
        }
    }
    let (a, b) = cid.split_once('-').unwrap_or((cid, ""));
    let ok = |x: &str| !x.is_empty() && x.bytes().all(|c| c.is_ascii_alphanumeric() || c == b'_');
    if ok(a) && ok(b) { s(&format!("https://images.pokemontcg.io/{a}/{b}_hires.png")) } else { Value::Null }
}

/// a real card's display fields and tags: pack.json's card entry, completed from packs/<pack>/cards/<id>.json
/// (docs/CARD_FORMAT.md) when it exists: set, printed rarity, subtypes, types, artist, and the text half ("text": HP,
/// stage, abilities, attacks with their energy cost, weakness / resistance / retreat, rules, flavor)
fn card_meta(ctx: &Ctx, pid: &str, cid: &str, c: &Value) -> Obj {
    let f = ctx.root.join("packs").join(pid).join("cards").join(format!("{cid}.json"));
    let st = ctx.dirs.file(&f);
    let key = format!("{}|{}|{}|{}", rel_str(&ctx.root, &f), st.map(|x| x.0).unwrap_or(0), st.map(|x| x.1).unwrap_or(0), dumps(c, true));
    let id = format!("{pid}/{cid}");
    if let Some(m) = ctx.meta.borrow_mut().get(&id, &key) {
        return m;
    }
    let m = card_meta_read(ctx, pid, cid, c, st.is_some());
    ctx.meta.borrow_mut().put(&id, &key, &m);
    m
}

fn card_meta_read(ctx: &Ctx, pid: &str, cid: &str, c: &Value, has_file: bool) -> Obj {
    let number = get_or(c, "number", s(""));
    let mut m = Obj::new();
    m.insert("id".into(), s(cid));
    m.insert("character".into(), c.get("character").cloned().unwrap_or(Value::Null));
    m.insert("tier".into(), c.get("tier").cloned().unwrap_or(Value::Null));
    m.insert("name".into(), get_or(c, "name", s("")));
    m.insert("number".into(), number);
    m.insert("rarity".into(), get_or(c, "rarity", s("")));
    m.insert("set_id".into(), s(if cid.contains('-') { cid.rsplit_once('-').map(|x| x.0).unwrap_or("") } else { "" }));
    m.insert("set_name".into(), get_or(c, "set", s("")));
    m.insert("subtypes".into(), json!([]));
    m.insert("types".into(), json!([]));
    m.insert("artist".into(), s(""));
    m.insert("scan".into(), scan_url(cid, None));
    let f = ctx.root.join("packs").join(pid).join("cards").join(format!("{cid}.json"));
    if !has_file {
        return m;
    }
    let Some(d) = read_text(&f).and_then(|t| serde_json::from_str::<Value>(&t).ok()) else {
        warn(&format!("{} is not valid JSON; card text left out", path_str(&f)));
        return m;
    };
    m.insert("scan".into(), scan_url(cid, d.get("images").filter(|v| truthy(v)).and_then(|i| i.get("large"))));
    let st = get_or(&d, "set", json!({}));
    let set_id = get_or(&st, "id", m["set_id"].clone());
    m.insert("set_id".into(), set_id);
    let set_name = get_or(&st, "name", m["set_name"].clone());
    m.insert("set_name".into(), set_name);
    let printed = st.get("printedTotal").filter(|v| truthy(v)).map(py_int).unwrap_or(0);
    m.insert("printed".into(), json!(printed));
    let rarity = get_or(&d, "rarity", m["rarity"].clone());
    m.insert("rarity".into(), rarity);
    if !truthy(&m["name"]) {
        m.insert("name".into(), get_or(&d, "name", s("")));
    }
    m.insert("subtypes".into(), Value::Array(d.get("subtypes").filter(|v| truthy(v)).and_then(|v| v.as_array()).map(|a| a.iter().filter(|x| x.is_string()).cloned().collect()).unwrap_or_default()));
    m.insert("types".into(), Value::Array(energy(d.get("types").filter(|v| truthy(v)))));
    m.insert("artist".into(), get_or(&d, "artist", s("")));
    if !truthy(&m["number"]) {
        if let Some(num) = d.get("number").filter(|v| truthy(v)) {
            let n = py_str(num);
            m.insert("number".into(), s(&if printed != 0 { format!("{n}/{printed}") } else { n }));
        }
    }
    let list = |k: &str| -> Vec<Value> { d.get(k).filter(|v| truthy(v)).and_then(|v| v.as_array()).cloned().unwrap_or_default() };
    let abilities: Vec<Value> = list("abilities").iter().filter(|a| a.is_object()).map(|a| json!({"name": get_or(a, "name", s("")), "type": get_or(a, "type", s("Ability")), "text": get_or(a, "text", s(""))})).collect();
    let attacks: Vec<Value> = list("attacks")
        .iter()
        .filter(|a| a.is_object())
        .map(|a| json!({"name": get_or(a, "name", s("")), "cost": energy(a.get("cost").filter(|v| truthy(v))), "damage": get_or(a, "damage", s("")), "text": get_or(a, "text", s(""))}))
        .collect();
    let wr = |k: &str| -> Vec<Value> { list(k).iter().filter(|w| w.is_object()).map(|w| json!({"type": get_or(w, "type", s("")), "value": get_or(w, "value", s(""))})).collect() };
    let rules: Vec<Value> = list("rules").into_iter().filter(|r| r.as_str().is_some_and(|t| !py_strip(t).is_empty())).collect();
    let txt: Vec<(&str, Value)> = vec![
        ("supertype", get_or(&d, "supertype", s(""))),
        ("hp", s(&d.get("hp").filter(|v| truthy(v)).map(py_str).unwrap_or_default())),
        ("evolves", get_or(&d, "evolvesFrom", s(""))),
        ("abilities", Value::Array(abilities)),
        ("attacks", Value::Array(attacks)),
        ("weak", Value::Array(wr("weaknesses"))),
        ("resist", Value::Array(wr("resistances"))),
        ("retreat", json!(energy(d.get("retreatCost").filter(|v| truthy(v))).len())),
        ("rules", Value::Array(rules)),
        ("flavor", get_or(&d, "flavorText", s(""))),
    ];
    let mut text = Obj::new();
    for (k, v) in txt {
        if truthy(&v) || k == "retreat" || k == "supertype" {
            text.insert(k.into(), v);
        }
    }
    m.insert("text".into(), Value::Object(text));
    m
}

fn weight(v: Option<&Value>) -> i64 {
    v.map(py_int).unwrap_or(0)
}

/// a real-card pack (pack.json "cards", docs/PACK_FORMAT.md). The odds are the game's (Show-CardOdds /
/// Add-PokeshellCardRows): a tier rolls by its weight among the tiers that have a weight and at least one built card
/// (p comes muted: unbuilt cards are gone), then one of its built cards uniformly. Tiers that can't drop are left out.
fn card_pack_info(ctx: &Ctx, pid: &str, p: &Value, n_active: usize) -> Value {
    let empty = Obj::new();
    let cards = p.get("cards").and_then(|c| c.as_object()).unwrap_or(&empty);
    let unbuilt: Vec<String> = p.get("_unbuilt").and_then(|u| u.as_array()).map(|a| a.iter().map(py_str).collect()).unwrap_or_default();
    if !unbuilt.is_empty() {
        warn(&format!(
            "{pid}: {} cards in pack.json have no built art (they never drop and get no slot): {}{}",
            unbuilt.len(),
            unbuilt.iter().take(12).cloned().collect::<Vec<_>>().join(", "),
            if unbuilt.len() > 12 { " ..." } else { "" }
        ));
    }
    let no_tiers = vec![];
    let tiers = p.get("tiers").and_then(|t| t.as_array()).unwrap_or(&no_tiers);
    let tier_of = |c: &Value| c.get("tier").cloned().unwrap_or(Value::Null);
    let live: Vec<&Value> = tiers.iter().filter(|t| weight(t.get("weight")) > 0 && cards.values().any(|c| tier_of(c) == t["id"])).collect();
    let total = match live.iter().map(|t| weight(t.get("weight"))).sum::<i64>() {
        0 => 1,
        x => x,
    };
    let mut out_tiers = vec![];
    for t in &live {
        let pr = weight(t.get("weight")) as f64 / total as f64;
        let n = cards.values().filter(|c| tier_of(c) == t["id"]).count();
        let skins = t.get("skins").and_then(|s| s.as_object()).cloned().unwrap_or_default();
        let sw = match skins.values().map(py_int).sum::<i64>() {
            0 => 1,
            x => x,
        };
        let fr = match t.get("frame") {
            Some(Value::Array(a)) => json!({"style": "card", "preset": "custom", "colors": a}),
            f => {
                let name = f.and_then(|f| f.as_str()).filter(|n| preset(n).is_some()).unwrap_or("plain");
                json!({"style": "card", "preset": name, "colors": preset(name)})
            }
        };
        let skin_list: Vec<Value> = skins.iter().map(|(sid, w)| json!({"id": sid, "weight": py_int(w), "odds": fnum(pr * py_int(w) as f64 / sw as f64)})).collect();
        out_tiers.push(json!({
            "id": t["id"], "label": get_default(t, "label", t["id"].clone()), "art": t["id"], "frame": fr,
            "family": get_or(t, "family", s("")), "rarity": get_or(t, "rarity", s("")),
            "shiny": get_or(t, "shiny", s("")), // "printed": the cards print the shiny Pokemon, never rolled shiny
            "odds": fnum(pr), "card_odds": if n > 0 { fnum(pr / n as f64) } else { json!(0) }, "cards": n,
            "skins": skin_list,
        }));
    }
    let live_ids: Vec<&Value> = live.iter().map(|t| &t["id"]).collect();
    // every droppable card with its tags and text half (docs/BINDER_SPEC.md "Tags and search", CARD_FORMAT.md), set
    // by set in checklist (printed number) order
    let (mut card_list, mut no_text): (Vec<Obj>, Vec<String>) = (vec![], vec![]);
    for (cid, c) in cards {
        if !live_ids.contains(&&tier_of(c)) || !c.get("character").is_some_and(truthy) {
            continue;
        }
        let m = card_meta(ctx, pid, cid, c);
        if !m.get("text").is_some_and(truthy) {
            no_text.push(cid.clone());
        }
        card_list.push(m);
    }
    if !no_text.is_empty() {
        warn(&format!(
            "{pid}: {} cards have no card text (packs/{pid}/cards/<id>.json; tools/fetch_cards.py): {}{}",
            no_text.len(),
            no_text.iter().take(12).cloned().collect::<Vec<_>>().join(", "),
            if no_text.len() > 12 { " ..." } else { "" }
        ));
    }
    // characters, named after their cards ("moltres-galar" -> "Galarian Moltres", "rayquaza" -> "Rayquaza")
    let mut order: Vec<String> = vec![];
    let mut names: HashMap<String, String> = HashMap::new();
    for c in &card_list {
        let ch = py_str(&c["character"]);
        if !order.contains(&ch) {
            order.push(ch.clone());
        }
        let b = base_name(c["name"].as_str().unwrap_or(""));
        if !b.is_empty() && names.get(&ch).is_none_or(|n| b.chars().count() < n.chars().count()) {
            names.insert(ch, b);
        }
    }
    let given = get_or(p, "names", json!({}));
    let chars: Vec<Value> = order
        .iter()
        .enumerate()
        .map(|(i, ch)| {
            let name = given.get(ch.as_str()).filter(|v| truthy(v)).cloned().unwrap_or_else(|| s(&names.get(ch).cloned().unwrap_or_else(|| title(&ch.replace('-', " ")))));
            json!({"id": ch, "no": i + 1, "name": name, "tag": "", "poster": null, "bounty": null})
        })
        .collect();
    let mut sets: Vec<(Value, Value)> = vec![];
    for c in &card_list {
        if truthy(&c["set_id"]) && !sets.iter().any(|x| x.0 == c["set_id"]) {
            let name = if truthy(&c["set_name"]) { c["set_name"].clone() } else { c["set_id"].clone() };
            sets.push((c["set_id"].clone(), name));
        }
    }
    let set_ix = |id: &Value| sets.iter().position(|x| x.0 == *id).unwrap_or(1 << 30);
    let mut keyed: Vec<_> = card_list.into_iter().map(|c| ((set_ix(&c["set_id"]), number_key(&py_str(&c["number"])), py_str(&c["id"])), c)).collect();
    keyed.sort_by(|a, b| a.0.cmp(&b.0));
    let mut card_list: Vec<Obj> = keyed.into_iter().map(|x| x.1).collect();
    let set_vals: Vec<Value> = sets
        .iter()
        .map(|(id, name)| {
            let total = card_list.iter().filter(|c| c["set_id"] == *id).count();
            let printed = card_list.iter().filter(|c| c["set_id"] == *id).map(|c| c.get("printed").map(py_int).unwrap_or(0)).max().unwrap_or(0).max(0);
            json!({"id": id, "name": name, "total": total, "printed": printed})
        })
        .collect();
    for c in card_list.iter_mut() {
        c.shift_remove("printed");
    }
    json!({
        "id": pid, "name": get_default(p, "name", s(pid)), "about": get_default(p, "about", Value::Null), "foil_chance": 0,
        "shiny_chance": fnum(py_float(&get_default(p, "shiny_chance", json!(0)))), "layout": "cards", "tiers": out_tiers,
        "characters": chars, "active_packs": n_active, "cards": card_list, "sets": set_vals, "unbuilt": unbuilt.len(),
    })
}

fn pack_info(ctx: &Ctx, pid: &str, n_active: usize) -> Option<Value> {
    let p = ctx.load_pack_json(pid, false)?;
    if p.get("cards").is_some_and(|c| c.is_object()) {
        return Some(card_pack_info(ctx, pid, &p, n_active));
    }
    let no = vec![];
    let tiers = p.get("tiers").and_then(|t| t.as_array()).unwrap_or(&no);
    let foil = py_float(&get_default(&p, "foil_chance", json!(0)));
    let skin_sum = |t: &Value| t.get("skins").filter(|v| truthy(v)).and_then(|s| s.as_object()).map(|o| o.values().map(py_int).sum::<i64>()).unwrap_or(0);
    let total: i64 = tiers.iter().skip(1).map(skin_sum).sum();
    let chars_in = p.get("characters").and_then(|c| c.as_array()).cloned().unwrap_or_default();
    let n = chars_in.len();
    let mut out_tiers = vec![];
    for (i, t) in tiers.iter().enumerate() {
        let skins = t.get("skins").filter(|v| truthy(v)).and_then(|s| s.as_object()).cloned().unwrap_or_default();
        let w = skin_sum(t);
        // Python: (1 - foil) or foil * w / total, an int 0 without skins
        let pr: Option<f64> = if i == 0 { Some(1.0 - foil) } else if total != 0 { Some(foil * w as f64 / total as f64) } else { None };
        let fr = match t.get("frame") {
            Some(Value::Object(f)) => {
                let pal = f.get("palette").cloned().unwrap_or(Value::Null);
                json!({"style": f.get("style").cloned().unwrap_or(Value::Null), "palette": pal, "colors": wanted(pal.as_str())})
            }
            f => {
                let name = match f {
                    Some(v) if truthy(v) => v.clone(),
                    _ => s(if t.get("id").and_then(|v| v.as_str()) == Some("secret-rare") { "gold" } else { "plain" }),
                };
                let colors = name.as_str().and_then(preset).unwrap_or_else(|| preset("plain").unwrap());
                json!({"style": "card", "preset": name, "colors": colors})
            }
        };
        let skin_list: Vec<Value> = skins
            .iter()
            .map(|(sid, wt)| json!({"id": sid, "weight": py_int(wt), "odds": if total != 0 { fnum(foil * py_int(wt) as f64 / total as f64) } else { json!(0) }}))
            .collect();
        out_tiers.push(json!({
            "id": t.get("id").cloned().unwrap_or(Value::Null), "label": t.get("label").cloned().unwrap_or(Value::Null),
            "art": t.get("art").cloned().unwrap_or(Value::Null), "frame": fr,
            "odds": pr.map(fnum).unwrap_or(json!(0)),                       // per pull of this pack
            "card_odds": if n > 0 { fnum(pr.unwrap_or(0.0) / n as f64) } else { json!(0) },   // this exact character in this tier
            "skins": skin_list,
        }));
    }
    let names = get_or(&p, "names", json!({}));
    let tags = get_or(&p, "tags", json!({}));
    let posters = get_or(&p, "poster_names", json!({}));
    let bounties = get_or(&p, "bounties", json!({}));
    let chars: Vec<Value> = chars_in
        .iter()
        .enumerate()
        .map(|(i, c)| {
            let id = py_str(c);
            json!({
                "id": c, "no": i + 1,
                "name": names.get(&id).filter(|v| truthy(v)).cloned().unwrap_or_else(|| s(&title(&id.replace('-', " ")))),
                "tag": tags.get(&id).cloned().unwrap_or(s("")),
                "poster": posters.get(&id).cloned().unwrap_or(Value::Null),
                "bounty": bounties.get(&id).cloned().unwrap_or(Value::Null),
            })
        })
        .collect();
    Some(json!({
        "id": pid, "name": get_default(&p, "name", s(pid)), "about": get_default(&p, "about", Value::Null),
        "foil_chance": fnum(foil), "shiny_chance": fnum(py_float(&get_default(&p, "shiny_chance", json!(0)))),
        "layout": if n > 60 { "dex" } else { "grid" },
        "tiers": out_tiers, "characters": chars,
        "active_packs": n_active,
    }))
}

// ---------------------------------------------------------------- art: decoding

fn hex_rgb(h: &str) -> Option<Rgb> {
    let h = h.trim_start_matches('#');
    let p = |i: usize| h.get(i..i + 2).and_then(|x| u8::from_str_radix(x, 16).ok());
    Some([p(0)?, p(2)?, p(4)?])
}

fn palette_into(v: Option<&Value>, pal: &mut HashMap<char, Option<Rgb>>) {
    if let Some(o) = v.filter(|v| truthy(v)).and_then(|v| v.as_object()) {
        for (k, c) in o {
            if let Some(ch) = k.chars().next() {
                if k.chars().count() == 1 {
                    pal.insert(ch, c.as_str().and_then(hex_rgb));
                }
            }
        }
    }
}

fn grid_from_json(d: &Value, variant: &str, shiny: bool) -> Grid {
    let v = &d["variants"][variant];
    let mut pal = HashMap::new();
    palette_into(d.get("palette"), &mut pal);
    palette_into(v.get("palette"), &mut pal);
    if shiny {
        palette_into(d.get("shiny"), &mut pal);
        palette_into(v.get("shiny"), &mut pal);
    }
    let rows = v.get("rows").and_then(|r| r.as_array()).cloned().unwrap_or_default();
    let g: Grid = rows.iter().map(|r| r.as_str().unwrap_or("").chars().map(|ch| if ch == '.' { None } else { pal.get(&ch).copied().flatten() }).collect()).collect();
    if g.is_empty() { vec![vec![None]] } else { g }
}

fn has_shiny(d: &Value, variant: &str) -> bool {
    d.get("shiny").is_some_and(truthy) || d["variants"][variant].get("shiny").is_some_and(truthy)
}

/// SGR parameters -> the fg / bg they leave
fn sgr(ps: &[i64], fg: &mut Option<Rgb>, bg: &mut Option<Rgb>) {
    let mut k = 0;
    while k < ps.len() {
        let v = ps[k];
        if v == 0 {
            *fg = None;
            *bg = None;
            k += 1;
        } else if (v == 38 || v == 48) && k + 4 < ps.len() && ps[k + 1] == 2 {
            let c = Some([ps[k + 2] as u8, ps[k + 3] as u8, ps[k + 4] as u8]);
            if v == 38 { *fg = c } else { *bg = c }
            k += 5;
        } else {
            if v == 39 {
                *fg = None;
            } else if v == 49 {
                *bg = None;
            }
            k += 1;
        }
    }
}

fn cell(ch: char, fg: Option<Rgb>, bg: Option<Rgb>, top: &mut Vec<Option<Rgb>>, bot: &mut Vec<Option<Rgb>>) {
    let (t, b) = match ch {
        '▀' => (fg, bg),
        '▄' => (bg, fg),
        '█' => (fg, fg),
        _ => (bg, bg),
    };
    top.push(t);
    bot.push(b);
}

/// a half-block truecolor .ans (dist/) back to pixels: two pixel rows per text row, None = transparent (the
/// exporter's own decoder: leading blank lines and trailing empty rows dropped, no column trim)
fn ansi_grid(text: &str) -> Grid {
    let mut rows: Grid = vec![];
    for line in text.replace("\r\n", "\n").split('\n') {
        if py_strip(line).is_empty() && rows.is_empty() {
            continue;
        }
        let (mut top, mut bot) = (vec![], vec![]);
        let (mut fg, mut bg) = (None, None);
        let cs: Vec<char> = line.chars().collect();
        let mut i = 0;
        while i < cs.len() {
            let ch = cs[i];
            if ch == '\x1b' && i + 1 < cs.len() && cs[i + 1] == '[' {
                let mut j = i + 2;
                while j < cs.len() && !('@'..='~').contains(&cs[j]) {
                    j += 1;
                }
                if j < cs.len() && cs[j] == 'm' {
                    let params: String = cs[i + 2..j].iter().collect();
                    let ps: Vec<i64> = params.split(';').map(|x| if !x.is_empty() && x.chars().all(|c| c.is_ascii_digit()) { x.parse().unwrap_or(0) } else { 0 }).collect();
                    sgr(&ps, &mut fg, &mut bg);
                }
                i = j + 1;
                continue;
            }
            cell(ch, fg, bg, &mut top, &mut bot);
            i += 1;
        }
        rows.push(top);
        rows.push(bot);
    }
    while rows.last().is_some_and(|r| r.iter().all(|p| p.is_none())) {
        rows.pop();
    }
    let w = rows.iter().map(|r| r.len()).max().unwrap_or(1);
    for r in rows.iter_mut() {
        r.resize(w, None);
    }
    if rows.is_empty() { vec![vec![None]] } else { rows }
}

/// packs/pokedex/build.py trim(parse(text)): the colorscripts' decoder (every line, then trimmed to the sprite)
fn dex_grid(text: &str) -> Grid {
    let mut grid: Grid = vec![];
    for line in text.replace("\r\n", "\n").split('\n') {
        let (mut top, mut bot) = (vec![], vec![]);
        let (mut fg, mut bg) = (None, None);
        let cs: Vec<char> = line.chars().collect();
        let mut i = 0;
        while i < cs.len() {
            // \x1b\[([0-9;]*)m
            if cs[i] == '\x1b' && cs.get(i + 1) == Some(&'[') {
                let mut j = i + 2;
                while j < cs.len() && (cs[j].is_ascii_digit() || cs[j] == ';') {
                    j += 1;
                }
                if cs.get(j) == Some(&'m') {
                    let params: String = cs[i + 2..j].iter().collect();
                    let ps: Vec<i64> = if params.is_empty() { vec![0] } else { params.split(';').map(|x| x.parse().unwrap_or(0)).collect() };
                    sgr(&ps, &mut fg, &mut bg);
                    i = j + 1;
                    continue;
                }
            }
            cell(cs[i], fg, bg, &mut top, &mut bot);
            i += 1;
        }
        grid.push(top);
        grid.push(bot);
    }
    let w = grid.iter().map(|r| r.len()).max().unwrap_or(0);
    for r in grid.iter_mut() {
        r.resize(w, None);
    }
    let rows: Vec<usize> = (0..grid.len()).filter(|&i| grid[i].iter().any(|p| p.is_some())).collect();
    let (Some(&r0), Some(&r1)) = (rows.first(), rows.last()) else {
        return vec![vec![None]];
    };
    let cols: Vec<usize> = (0..w).filter(|&j| rows.iter().any(|&i| grid[i][j].is_some())).collect();
    let (c0, c1) = (cols[0], *cols.last().unwrap());
    (r0..=r1).map(|i| grid[i][c0..=c1].to_vec()).collect()
}

/// a scene card's sprite layer from its normal and shiny art (pixel grids): the pixels that differ, grown twice into
/// the dark pixels touching them (8 neighbours: the outline and eyes, the same in both), with enclosed holes filled.
/// None when they don't line up or too little differs (the app's art::sprite_layer)
fn sprite_layer(a: &Grid, b: &Grid) -> Option<Grid> {
    let h = a.len();
    let w = a.first().map(|r| r.len()).unwrap_or(0);
    if w == 0 || b.len() != h || b.iter().any(|r| r.len() != w) || a.iter().any(|r| r.len() != w) {
        return None;
    }
    let mut m: Vec<Vec<bool>> = (0..h).map(|y| (0..w).map(|x| a[y][x].is_some() && a[y][x] != b[y][x]).collect()).collect();
    if m.iter().map(|r| r.iter().filter(|x| **x).count()).sum::<usize>() * 100 < w * h {
        return None;
    }
    let dark = |c: Option<Rgb>| c.is_some_and(|c| (0.2126 * c[0] as f64 + 0.7152 * c[1] as f64 + 0.0722 * c[2] as f64) / 255.0 < 0.16);
    for _ in 0..2 {
        let prev = m.clone();
        for y in 0..h {
            for x in 0..w {
                if !prev[y][x] && dark(a[y][x]) && (y.saturating_sub(1)..(y + 2).min(h)).any(|yy| (x.saturating_sub(1)..(x + 2).min(w)).any(|xx| prev[yy][xx])) {
                    m[y][x] = true;
                }
            }
        }
    }
    let mut out = vec![vec![false; w]; h];
    let mut stack: Vec<(usize, usize)> = (0..w).flat_map(|x| [(x, 0), (x, h - 1)]).chain((0..h).flat_map(|y| [(0, y), (w - 1, y)])).collect();
    while let Some((x, y)) = stack.pop() {
        if out[y][x] || m[y][x] {
            continue;
        }
        out[y][x] = true;
        if x + 1 < w {
            stack.push((x + 1, y));
        }
        if x > 0 {
            stack.push((x - 1, y));
        }
        if y + 1 < h {
            stack.push((x, y + 1));
        }
        if y > 0 {
            stack.push((x, y - 1));
        }
    }
    Some(out.iter().map(|r| r.iter().map(|&o| if o { None } else { Some([0, 0, 0]) }).collect()).collect())
}

/// colorsys.rgb_to_hls
fn rgb_to_hls(r: f64, g: f64, b: f64) -> (f64, f64, f64) {
    let maxc = r.max(g).max(b);
    let minc = r.min(g).min(b);
    let sumc = maxc + minc;
    let rangec = maxc - minc;
    let l = sumc / 2.0;
    if minc == maxc {
        return (0.0, l, 0.0);
    }
    let s = if l <= 0.5 { rangec / sumc } else { rangec / (2.0 - maxc - minc) };
    let rc = (maxc - r) / rangec;
    let gc = (maxc - g) / rangec;
    let bc = (maxc - b) / rangec;
    let h = if r == maxc {
        bc - gc
    } else if g == maxc {
        2.0 + rc - bc
    } else {
        4.0 + gc - rc
    };
    (py_mod(h / 6.0, 1.0), l, s)
}

/// Python's float %: the sign of the divisor
fn py_mod(x: f64, y: f64) -> f64 {
    let m = x % y;
    if m != 0.0 {
        if (y < 0.0) != (m < 0.0) { m + y } else { m }
    } else {
        0.0f64.copysign(y)
    }
}

/// a representative, saturated body color of the art: the art window's backdrop tint
fn tint_of(grid: &Grid) -> String {
    let mut order: Vec<i64> = vec![];
    let mut buckets: HashMap<i64, Vec<Rgb>> = HashMap::new();
    for row in grid {
        for c in row.iter().flatten() {
            let (hh, ll, ss) = rgb_to_hls(c[0] as f64 / 255.0, c[1] as f64 / 255.0, c[2] as f64 / 255.0);
            if ss < 0.25 || ll < 0.2 || ll > 0.85 {
                continue;
            }
            let k = ((hh * 12.0).trunc() as i64).rem_euclid(12);
            buckets
                .entry(k)
                .or_insert_with(|| {
                    order.push(k);
                    vec![]
                })
                .push(*c);
        }
    }
    let mut best: Option<&Vec<Rgb>> = None;
    for k in &order {
        let b = &buckets[k];
        if best.is_none_or(|x| b.len() > x.len()) {
            best = Some(b);
        }
    }
    let Some(best) = best else {
        return DEFAULT_TINT.into();
    };
    let avg = |i: usize| (best.iter().map(|c| c[i] as u64).sum::<u64>() as f64 / best.len() as f64) as u64;
    format!("#{:02x}{:02x}{:02x}", avg(0), avg(1), avg(2))
}

fn encode_png(w: usize, h: usize, color: png::ColorType, data: &[u8]) -> Vec<u8> {
    let mut out = vec![];
    {
        let mut e = png::Encoder::new(&mut out, w as u32, h as u32);
        e.set_color(color);
        e.set_depth(png::BitDepth::Eight);
        e.set_compression(png::Compression::Balanced);
        match e.write_header().and_then(|mut wr| wr.write_image_data(data)) {
            Ok(()) => {}
            Err(err) => warn(&format!("PNG encoding failed: {err}")),
        }
    }
    out
}

/// 1 px per art pixel, RGBA; returns [w, h]
fn save_grid(grid: &Grid, path: &Path) -> std::io::Result<(usize, usize)> {
    let (h, w) = (grid.len(), grid[0].len());
    let mut px = vec![0u8; w * h * 4];
    for (y, row) in grid.iter().enumerate() {
        for (x, c) in row.iter().enumerate().take(w) {
            if let Some(c) = c {
                px[(y * w + x) * 4..(y * w + x) * 4 + 4].copy_from_slice(&[c[0], c[1], c[2], 255]);
            }
        }
    }
    write_atomic(path, &encode_png(w.max(1), h.max(1), png::ColorType::Rgba, &px))?;
    Ok((w, h))
}

fn png_size(path: &Path) -> Option<(usize, usize)> {
    let f = fs::File::open(path).ok()?;
    let r = png::Decoder::new(std::io::BufReader::new(f)).read_info().ok()?;
    let i = r.info();
    Some((i.width as usize, i.height as usize))
}

// ---------------------------------------------------------------- art: the cache

/// where a PNG's pixels come from
enum Src {
    Ansi(PathBuf),
    Dex(PathBuf),
    Json(Rc<Value>, String, bool),
    /// a scene card's sprite layer from its art and shiny art
    Layer(PathBuf, PathBuf),
}

fn decode(src: &Src) -> Grid {
    match src {
        Src::Ansi(p) => ansi_grid(&read_universal(p).unwrap_or_default()),
        Src::Dex(p) => dex_grid(&read_universal(p).unwrap_or_default()),
        Src::Json(d, v, shiny) => grid_from_json(d, v, *shiny),
        Src::Layer(a, b) => sprite_layer(&ansi_grid(&read_universal(a).unwrap_or_default()), &ansi_grid(&read_universal(b).unwrap_or_default())).unwrap_or_else(|| vec![vec![None]]),
    }
}

fn mtime_ns(m: &fs::Metadata) -> u64 {
    m.modified().ok().and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok()).map(|d| d.as_nanos() as u64).unwrap_or(0)
}

/// a source's stamp: [its path relative to root (absolute when it is outside), mtime ns, size]
fn stamp(dirs: &DirCache, root: &Path, p: &Path) -> Vec<Value> {
    let m = dirs.file(p);
    vec![s(&rel_str(root, p)), json!(m.map(|m| m.0).unwrap_or(0)), json!(m.map(|m| m.1).unwrap_or(0))]
}

fn rel_str(root: &Path, p: &Path) -> String {
    p.strip_prefix(root).map(path_str).unwrap_or_else(|_| path_str(p))
}

/// a cached entry's source stamp is this one: equal, or (a cache written before sources were keyed relative to the
/// root, or under another root) each path in it ends with the relative path here, with the same mtimes and sizes
fn same_src(old: Option<&Value>, new: &Value) -> bool {
    let (Some(old), Some(new)) = (old.and_then(|v| v.as_array()), new.as_array()) else { return false };
    if old == new {
        return true;
    }
    if old.len() != new.len() {
        return false;
    }
    let norm = |x: &str| x.replace('/', "\\").to_lowercase();
    let tail = |o: &str, n: &str| {
        let (o, n) = (norm(o), norm(n));
        o == n || (!n.is_empty() && !Path::new(&n).is_absolute() && o.ends_with(&format!("\\{n}")))
    };
    old.iter().zip(new.iter()).all(|(o, n)| match (o.as_str(), n.as_str()) {
        (Some(o), Some(n)) => o.split('|').count() == n.split('|').count() && o.split('|').zip(n.split('|')).all(|(o, n)| tail(o, n)),
        _ => o == n,
    })
}

/// decoded art, cached by source file: img/.cache.json maps each PNG (relative to img/) to the source it was made from
/// (path, mtime, size) plus its pixel size and tint. A PNG whose source is unchanged isn't decoded again. kept collects
/// every PNG this export uses; prune() removes the rest (retired / renamed cards, old shiny forms). Each entry also
/// keeps the art's transparent share ("clear"): a card's plain sprite has one, a scene none.
struct ArtCache {
    img: PathBuf,
    over: PathBuf,
    root: PathBuf,
    dirs: Rc<DirCache>,
    /// --only: the cards whose images are checked; every other cached image is kept as it is
    only: Option<HashSet<String>>,
    do_art: bool,
    kept: HashSet<String>,
    decoded: usize,
    reused: usize,
    file: PathBuf,
    entries: Obj,
    extra: Obj,
}

impl ArtCache {
    fn new(img: &Path, over: &Path, root: &Path, dirs: Rc<DirCache>, only: Option<HashSet<String>>, do_art: bool) -> ArtCache {
        let file = img.join(".cache.json");
        let d = read_text(&file).and_then(|t| serde_json::from_str::<Value>(&t).ok()).filter(|d| d.get("v") == Some(&json!(CACHE_VERSION)));
        let part = |k: &str| d.as_ref().and_then(|d| d.get(k)).and_then(|v| v.as_object()).cloned().unwrap_or_default();
        ArtCache { img: img.to_path_buf(), over: over.to_path_buf(), root: root.to_path_buf(), dirs, only, do_art, kept: HashSet::new(), decoded: 0, reused: 0, entries: part("entries"), extra: part("extra"), file }
    }

    /// (size [w, h] or null, tint) of the PNG img/<rel> made from src (and `also`, a second source it depends on).
    /// --no-art: nothing is decoded or written; a cached entry still gives the size and tint.
    /// --only: is img/<rel> one of the named cards' images ("<pack>/<character>/<card id>[-shiny|-seen].png")?
    fn wanted(&self, rel: &str) -> bool {
        let Some(only) = &self.only else { return true };
        let stem = rel.rsplit('/').next().unwrap_or(rel).trim_end_matches(".png");
        let id = stem.strip_suffix("-shiny").or_else(|| stem.strip_suffix("-seen")).unwrap_or(stem);
        only.contains(id)
    }

    fn get(&mut self, rel: &str, src: &Path, how: Src, also: Option<&Path>) -> (Value, Option<String>) {
        let dst = self.img.join(rel);
        let e = self.entries.get(rel).cloned();
        let tint_of_e = |e: &Option<Value>| e.as_ref().and_then(|e| e.get("tint")).and_then(|t| t.as_str()).map(str::to_string);
        let size_of_e = |e: &Option<Value>| e.as_ref().and_then(|e| e.get("size")).cloned().unwrap_or(Value::Null);
        // --only: another card's image that the cache has is kept as it is
        if e.is_some() && !self.wanted(rel) {
            self.kept.insert(rel.to_string());
            self.reused += 1;
            return (size_of_e(&e), tint_of_e(&e));
        }
        let ov = self.over.join(rel);
        let mut st = stamp(&self.dirs, &self.root, src);
        if let Some(a) = also {
            st.extend(stamp(&self.dirs, &self.root, a));
        }
        if let Some(om) = self.dirs.file(&ov) {
            st[0] = s(&format!("{}|{}", st[0].as_str().unwrap_or(""), rel_str(&self.root, &ov)));
            st[1] = json!(st[1].as_u64().unwrap_or(0).max(om.0));
        }
        let st = Value::Array(st);
        if e.as_ref().is_some_and(|e| same_src(e.get("src"), &st)) && (!self.do_art || self.dirs.is_file(&dst)) {
            if let Some(Value::Object(o)) = self.entries.get_mut(rel) {
                o.insert("src".into(), st); // an old absolute stamp becomes the relative one
            }
            self.kept.insert(rel.to_string());
            self.reused += 1;
            return (size_of_e(&e), tint_of_e(&e));
        }
        if !self.do_art {
            return (size_of_e(&e), tint_of_e(&e));
        }
        let grid = decode(&how);
        self.decoded += 1;
        let tint = tint_of(&grid);
        let n: usize = grid.iter().map(|r| r.len()).sum();
        let clear = if n > 0 { fnum(round3(grid.iter().map(|r| r.iter().filter(|p| p.is_none()).count()).sum::<usize>() as f64 / n as f64)) } else { json!(0) };
        self.dirs.touched(&dst);
        let size = if self.dirs.is_file(&ov) {
            let copied = fs::read(&ov).and_then(|b| write_atomic(&dst, &b));
            if let Err(err) = copied {
                warn(&format!("can't copy {}: {err}", path_str(&ov)));
            }
            png_size(&dst).map(|(w, h)| json!([w, h])).unwrap_or(Value::Null)
        } else {
            match save_grid(&grid, &dst) {
                Ok((w, h)) => json!([w, h]),
                Err(err) => {
                    warn(&format!("can't write {}: {err}", path_str(&dst)));
                    Value::Null
                }
            }
        };
        self.entries.insert(rel.to_string(), json!({"src": st, "size": size, "tint": tint, "clear": clear}));
        self.kept.insert(rel.to_string());
        (size, Some(tint))
    }

    /// the transparent share of img/<rel>'s art (None when it isn't known)
    fn clear(&self, rel: &str) -> Option<f64> {
        self.entries.get(rel).and_then(|e| e.get("clear")).and_then(|c| c.as_f64())
    }

    fn save(&self) {
        if !self.do_art {
            return;
        }
        // --only: nothing is pruned, so every entry stays (the next full export sorts them out)
        let live: Obj = self.entries.iter().filter(|(k, _)| self.only.is_some() || self.kept.contains(*k)).map(|(k, v)| (k.clone(), v.clone())).collect();
        let doc = json!({"v": CACHE_VERSION, "entries": live, "extra": self.extra});
        if let Err(err) = write_atomic(&self.file, &text_bytes(&dumps(&doc, true))) {
            warn(&format!("can't write {}: {err}", path_str(&self.file)));
        }
    }

    /// remove PNGs no card uses any more (and folders left empty); only after a full art export
    fn prune(&self) -> usize {
        if !self.do_art || self.only.is_some() || !self.img.exists() {
            return 0;
        }
        let mut files = vec![];
        let mut dirs = vec![];
        let mut stack = vec![self.img.clone()];
        while let Some(d) = stack.pop() {
            let Ok(rd) = fs::read_dir(&d) else { continue };
            for e in rd.flatten() {
                let p = e.path();
                if e.file_type().is_ok_and(|t| t.is_dir()) {
                    dirs.push(p.clone());
                    stack.push(p);
                } else if p.extension().is_some_and(|x| x.eq_ignore_ascii_case("png")) {
                    files.push(p);
                }
            }
        }
        let mut n = 0;
        for f in files {
            let rel = f.strip_prefix(&self.img).map(|r| r.components().map(|c| c.as_os_str().to_string_lossy().into_owned()).collect::<Vec<_>>().join("/")).unwrap_or_default();
            if !self.kept.contains(&rel) && fs::remove_file(&f).is_ok() {
                n += 1;
            }
        }
        dirs.sort_by_key(|d| std::cmp::Reverse(d.components().count()));
        for d in dirs {
            let _ = fs::remove_dir(&d); // only succeeds when empty
        }
        n
    }
}

// ---------------------------------------------------------------- art: the export

struct ArtOut {
    tint: Value,
    img: Obj,
    seen: Option<String>,
}

/// the character's plain colorscripts sprite in this checkout (vendor/ or $POKESHELL_VENDOR, else the pokedex pack's
/// art), or None
fn sprite_source(ctx: &Ctx, ch: &str) -> Option<PathBuf> {
    let vendor = std::env::var("POKESHELL_VENDOR").ok().filter(|v| !v.is_empty()).map(PathBuf::from).unwrap_or_else(|| ctx.root.join("vendor"));
    [vendor.join("pokemon-colorscripts").join("colorscripts").join("large").join("regular").join(ch), ctx.root.join("dist").join("pokedex").join(format!("{ch}-common.ans"))].into_iter().find(|f| f.is_file())
}

fn art_json_path(ctx: &Ctx, pack: &str, ch: &str) -> Option<PathBuf> {
    [ctx.root.join("packs").join(pack).join("art"), ctx.opshell.join("packs").join(pack).join("art")].into_iter().map(|b| b.join(format!("{ch}.json"))).find(|f| f.exists())
}

type ArtMap = HashMap<String, HashMap<String, ArtOut>>;

/// every pack's art: {pack: {char: tint, img {"tier[-shiny]" or "card id[-shiny]": [w,h] or null}, seen}}, per-card
/// tints {pack: {card id: tint}} and the pokedex atlas info; marks cards "sprite" / "seen" in place
fn export_art(ctx: &Ctx, packs: &mut [Value], pulls: &[Pull], cache: &mut ArtCache) -> (ArtMap, HashMap<String, HashMap<String, String>>, Value) {
    let mut art: ArtMap = HashMap::new();
    let mut card_tints: HashMap<String, HashMap<String, String>> = HashMap::new();
    let mut atlas = Value::Null;
    let shiny_pulled: HashSet<(String, String, String)> =
        pulls.iter().filter(|p| p.shiny).map(|p| (p.pack.clone(), if p.card.is_empty() { p.ch.clone() } else { p.card.clone() }, p.tier.clone())).collect();
    for pk in packs.iter_mut() {
        let pid = py_str(&pk["id"]);
        let layout = pk["layout"].as_str().unwrap_or("").to_string();
        let mut out: HashMap<String, ArtOut> = HashMap::new();
        let char_ids: Vec<String> = pk["characters"].as_array().map(|a| a.iter().map(|c| py_str(&c["id"])).collect()).unwrap_or_default();
        if layout == "dex" {
            let dex = ctx.root.join("dist").join("pokedex");
            let mut pulled: HashMap<&str, Vec<(String, bool)>> = HashMap::new();
            for p in pulls.iter().filter(|p| p.pack == pid) {
                let v = pulled.entry(p.ch.as_str()).or_default();
                if !v.contains(&(p.tier.clone(), p.shiny)) {
                    v.push((p.tier.clone(), p.shiny));
                }
            }
            // the silhouette atlas (every sprite) is rebuilt only when a sprite changed; tints come from the cache
            let srcs: Vec<PathBuf> = char_ids.iter().map(|c| dex.join(format!("{c}-common.ans"))).collect();
            let sig: Vec<Value> = srcs
                .iter()
                .map(|p| {
                    let name = s(&p.file_name().unwrap_or_default().to_string_lossy());
                    match ctx.dirs.file(p) {
                        Some(m) => json!([name, m.0, m.1]),
                        None => json!([name]),
                    }
                })
                .collect();
            let sig = Value::Array(sig);
            let meta = cache.extra.get("dex").filter(|v| truthy(v)).cloned().unwrap_or(json!({}));
            let atlas_file = cache.img.join(&pid).join("_silhouettes.png");
            let mut tints: Option<Vec<Value>> = None;
            let mut geo: Option<(Value, Value, Value)> = None; // cell, cols, rows
            if meta.get("sig") == Some(&sig) && (ctx.dirs.is_file(&atlas_file) || !cache.do_art) {
                tints = meta.get("tints").and_then(|t| t.as_array()).cloned();
                geo = Some((meta.get("cell").cloned().unwrap_or(Value::Null), meta.get("cols").cloned().unwrap_or(Value::Null), meta.get("rows").cloned().unwrap_or(Value::Null)));
            } else if cache.do_art {
                let sils: Vec<Grid> = srcs.iter().map(|p| if ctx.dirs.is_file(p) { dex_grid(&read_universal(p).unwrap_or_default()) } else { vec![vec![None]] }).collect();
                let t: Vec<Value> = sils.iter().map(|g| s(&tint_of(g))).collect();
                let cw = sils.iter().map(|g| g[0].len()).max().unwrap_or(1);
                let chh = sils.iter().map(|g| g.len()).max().unwrap_or(1);
                let cols = 32usize;
                let rows = sils.len().div_ceil(cols);
                let (iw, ih) = (cols * cw, rows * chh);
                let mut px = vec![0u8; iw * ih * 2];
                for (i, g) in sils.iter().enumerate() {
                    let ox = (i % cols) * cw + (cw - g[0].len()) / 2;
                    let oy = (i / cols) * chh + (chh - g.len());
                    for (y, row) in g.iter().enumerate() {
                        for (x, c) in row.iter().enumerate() {
                            if c.is_some() {
                                px[((oy + y) * iw + ox + x) * 2 + 1] = 255;
                            }
                        }
                    }
                }
                if let Err(err) = write_atomic(&atlas_file, &encode_png(iw.max(1), ih.max(1), png::ColorType::GrayscaleAlpha, &px)) {
                    warn(&format!("can't write {}: {err}", path_str(&atlas_file)));
                }
                let cell = json!([cw, chh]);
                cache.extra.insert("dex".into(), json!({"sig": sig, "tints": t, "cell": cell, "cols": cols, "rows": rows}));
                tints = Some(t);
                geo = Some((cell, json!(cols), json!(rows)));
            } // else: --no-art on a first run: no atlas, default tints
            if let Some((cell, cols, rows)) = geo.filter(|g| truthy(&g.0)) {
                atlas = json!({"file": format!("img/{pid}/_silhouettes.png"), "cell": cell, "cols": cols, "rows": rows});
                cache.kept.insert(format!("{pid}/_silhouettes.png"));
            }
            for (i, c) in char_ids.iter().enumerate() {
                let tint = tints.as_ref().and_then(|t| t.get(i)).cloned().unwrap_or_else(|| s(DEFAULT_TINT));
                let mut img = Obj::new();
                let mut forms = pulled.get(c.as_str()).cloned().unwrap_or_default();
                forms.sort();
                for (tier, shiny) in forms {
                    let mut src = dex.join(format!("{c}-common{}.ans", if shiny { "-shiny" } else { "" }));
                    if !ctx.dirs.is_file(&src) {
                        src = dex.join(format!("{c}-common.ans"));
                    }
                    if !ctx.dirs.is_file(&src) {
                        continue;
                    }
                    let key = format!("{tier}{}", if shiny { "-shiny" } else { "" });
                    let (size, _) = cache.get(&format!("{pid}/{c}/{key}.png"), &src, Src::Dex(src.clone()), None);
                    img.insert(key, size);
                }
                out.insert(c.clone(), ArtOut { tint, img, seen: None });
            }
        } else if layout == "cards" {
            // real cards: one image per card, from its prebuilt art dist/<pack>/<character>-<card id>.ans converted
            // back to pixels; keyed by card id (img/<pack>/<character>/<card id>[-shiny].png). Every card's normal
            // form (a deep link or search can open any card), shiny forms only once pulled (caught or seen).
            let tints = card_tints.entry(pid.clone()).or_default();
            let seen_cards: HashSet<&str> = pulls.iter().filter(|p| p.pack == pid && p.status != "collected" && !p.card.is_empty()).map(|p| p.card.as_str()).collect();
            let dist = ctx.root.join("dist").join(&pid);
            let cards = pk["cards"].as_array_mut().map(std::mem::take).unwrap_or_default();
            let mut cards = cards;
            for c in &char_ids {
                let mut tint: Option<String> = None;
                let mut img = Obj::new();
                let mine: Vec<usize> = (0..cards.len()).filter(|&i| cards[i]["character"].as_str() == Some(c.as_str())).collect();
                for &i in &mine {
                    let cid = py_str(&cards[i]["id"]);
                    let ctier = py_str(&cards[i]["tier"]);
                    for shiny in [false, true] {
                        if shiny && !shiny_pulled.contains(&(pid.clone(), cid.clone(), ctier.clone())) {
                            continue;
                        }
                        let src = dist.join(format!("{c}-{cid}{}.ans", if shiny { "-shiny" } else { "" }));
                        if !ctx.dirs.is_file(&src) {
                            continue;
                        }
                        let key = format!("{cid}{}", if shiny { "-shiny" } else { "" });
                        let (size, t) = cache.get(&format!("{pid}/{c}/{key}.png"), &src, Src::Ansi(src.clone()), None);
                        img.insert(key, size);
                        if let (false, Some(t)) = (shiny, t) {
                            tints.insert(cid.clone(), t.clone());
                            tint = tint.or(Some(t));
                        }
                    }
                }
                let tint = s(&tint.unwrap_or_else(|| DEFAULT_TINT.into()));
                let mut seen = None;
                // a seen card's silhouette (the module doc). A card whose art has transparent pixels is the plain
                // sprite (a common; a scene is full-bleed): its own image is its shape, and a scene card of the same
                // character takes it; else the colorscripts sprite; else the scene card's own sprite layer
                for &i in &mine {
                    let cid = py_str(&cards[i]["id"]);
                    if cache.clear(&format!("{pid}/{c}/{cid}.png")).unwrap_or(0.0) >= SPRITE_CLEAR {
                        if let Some(o) = cards[i].as_object_mut() {
                            o.insert("sprite".into(), json!(true));
                        }
                    }
                }
                let is_sprite = |v: &Value| v.get("sprite").is_some_and(truthy);
                let scenes: Vec<usize> = mine.iter().copied().filter(|&i| seen_cards.contains(cards[i]["id"].as_str().unwrap_or("")) && !is_sprite(&cards[i])).collect();
                if !scenes.is_empty() {
                    let common = mine.iter().find(|&&i| is_sprite(&cards[i])).map(|&i| py_str(&cards[i]["id"]));
                    let src = if common.is_some() { None } else { sprite_source(ctx, c) };
                    if let Some(common) = common {
                        seen = Some(common);
                    } else if let Some(src) = src {
                        let (size, _) = cache.get(&format!("{pid}/{c}/_seen.png"), &src, Src::Ansi(src.clone()), None);
                        if truthy(&size) {
                            img.insert("_seen".into(), size);
                            seen = Some("_seen".into());
                        }
                    } else {
                        for &i in &scenes {
                            let cid = py_str(&cards[i]["id"]);
                            let a = dist.join(format!("{c}-{cid}.ans"));
                            let b = dist.join(format!("{c}-{cid}-shiny.ans"));
                            if !(ctx.dirs.is_file(&a) && ctx.dirs.is_file(&b)) {
                                continue;
                            }
                            let (size, _) = cache.get(&format!("{pid}/{c}/{cid}-seen.png"), &a, Src::Layer(a.clone(), b.clone()), Some(&b));
                            if truthy(&size) && size != json!([1, 1]) {
                                img.insert(format!("{cid}-seen"), size);
                                if let Some(o) = cards[i].as_object_mut() {
                                    o.insert("seen".into(), s(&format!("{cid}-seen")));
                                }
                            }
                        }
                    }
                }
                out.insert(c.clone(), ArtOut { tint, img, seen });
            }
            pk["cards"] = Value::Array(cards);
        } else {
            let tiers: Vec<(String, String)> = pk["tiers"].as_array().map(|a| a.iter().map(|t| (py_str(&t["id"]), py_str(&t["art"]))).collect()).unwrap_or_default();
            let shiny_chance = pk["shiny_chance"].as_f64().unwrap_or(0.0);
            for c in &char_ids {
                let mut entry = ArtOut { tint: s(DEFAULT_TINT), img: Obj::new(), seen: None };
                let Some(f) = art_json_path(ctx, &pid, c) else {
                    warn(&format!("no art for {pid}/{c}"));
                    out.insert(c.clone(), entry);
                    continue;
                };
                let Some(d) = read_text(&f).and_then(|t| serde_json::from_str::<Value>(&t).ok()) else {
                    warn(&format!("{} is not valid JSON; no art for {pid}/{c}", path_str(&f)));
                    out.insert(c.clone(), entry);
                    continue;
                };
                let d = Rc::new(d);
                for (i, (tid, v)) in tiers.iter().enumerate() {
                    if d.get("variants").and_then(|x| x.get(v)).is_none() {
                        continue;
                    }
                    let forms: &[bool] = if has_shiny(&d, v) && shiny_chance > 0.0 { &[false, true] } else { &[false] };
                    for &shiny in forms {
                        let key = format!("{tid}{}", if shiny { "-shiny" } else { "" });
                        let (size, tint) = cache.get(&format!("{pid}/{c}/{key}.png"), &f, Src::Json(d.clone(), v.clone(), shiny), None);
                        entry.img.insert(key, size);
                        if let (0, false, Some(t)) = (i, shiny, tint) {
                            entry.tint = s(&t);
                        }
                    }
                }
                out.insert(c.clone(), entry);
            }
        }
        art.insert(pid, out);
    }
    (art, card_tints, atlas)
}

// ---------------------------------------------------------------- main

pub struct Opts {
    pub root: PathBuf,
    pub state: PathBuf,
    pub log: Option<PathBuf>,
    pub out: PathBuf,
    pub owner: Option<String>,
    pub no_art: bool,
    /// --only: the card ids whose images are (re)rendered (incremental: pack open --export)
    pub only: Option<Vec<String>>,
}

/// the export; returns the process exit code
pub fn run(o: Opts) -> i32 {
    let t0 = Instant::now();
    let root = std::path::absolute(&o.root).unwrap_or(o.root.clone());
    let dirs = Rc::new(DirCache::default());
    let img = o.out.join("img");
    let meta = RefCell::new(MetaCache::new(img.join(".meta.json")));
    let ctx = Ctx { opshell: root.parent().map(|p| p.join("opshell")).unwrap_or_else(|| root.join("opshell")), root: root.clone(), dirs: dirs.clone(), meta };
    let out = o.out.clone();
    if let Err(e) = fs::create_dir_all(&out) {
        eprintln!("binder: can't create {}: {e}", path_str(&out));
        return 1;
    }
    let log = o.log.clone().unwrap_or_else(|| o.state.join("pulls.log"));
    let base = log.parent().map(Path::to_path_buf).unwrap_or_else(|| o.state.clone());
    let viewed: HashSet<String> = read_text(&base.join("viewed.txt")).map(|t| splitlines(&t).iter().map(|l| py_strip(l).to_string()).filter(|l| !l.is_empty()).collect()).unwrap_or_default();
    let now = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map(|d| d.as_secs_f64()).unwrap_or(0.0);
    let mut bad = 0;
    let raw = read_pulls(&log, &viewed, now, crate::data::boot_id(), &mut bad);
    let (pulls, hidden, real_since) = resolve_pulls(&ctx, raw);
    let log_name = log.file_name().map(|n| n.to_string_lossy().into_owned()).unwrap_or_default();
    if bad > 0 {
        warn(&format!("{bad} lines of {log_name} couldn't be read (not UTF-8, or a bad time) and were skipped"));
    }
    let mut cfg: HashMap<String, String> = HashMap::new();
    if let Some(t) = read_text(&base.join("config.txt")) {
        for line in splitlines(&t) {
            if line.contains('=') && !line.trim_start().starts_with('#') {
                let (k, v) = line.split_once('=').unwrap();
                cfg.insert(py_strip(k).to_string(), py_strip(v).to_string());
            }
        }
    }
    let packs_dir = root.join("packs");
    let mut pack_ids: Vec<String> = PACK_ORDER.iter().filter(|p| packs_dir.join(p).join("pack.json").exists()).map(|p| p.to_string()).collect();
    let mut rest: Vec<String> = fs::read_dir(&packs_dir)
        .map(|rd| rd.flatten().filter(|e| e.path().is_dir() && e.path().join("pack.json").exists()).map(|e| e.file_name().to_string_lossy().into_owned()).filter(|n| !pack_ids.contains(n)).collect())
        .unwrap_or_default();
    rest.sort();
    pack_ids.extend(rest);
    let pack_setting = cfg.get("pack").cloned().unwrap_or_else(|| "all".into());
    let n_active = if pack_setting == "all" { pack_ids.len() } else { 1 };
    let mut packs: Vec<Value> = pack_ids.iter().filter_map(|p| pack_info(&ctx, p, n_active)).collect();

    let mut skins = Obj::new();
    for pk in &packs {
        let pid = py_str(&pk["id"]);
        for t in pk["tiers"].as_array().into_iter().flatten() {
            for sk in t["skins"].as_array().into_iter().flatten() {
                let sid = py_str(&sk["id"]);
                if skins.contains_key(&sid) {
                    continue;
                }
                let (title_s, desc) = skin_blurb(&packs_dir.join(&pid).join("shaders").join(format!("{sid}.hlsl")));
                let t = title_s.filter(|t| !t.is_empty()).unwrap_or_else(|| title(&sid.replace('-', " ")));
                skins.insert(sid, json!({"title": t, "desc": desc}));
            }
        }
    }

    let over = root.join("tools").join("binder-web").join("art-override");
    let only: Option<HashSet<String>> = o.only.as_ref().map(|v| v.iter().cloned().collect());
    let mut cache = ArtCache::new(&img, &over, &root, dirs.clone(), only, !o.no_art);
    let (mut art, card_tints, atlas) = export_art(&ctx, &mut packs, &pulls, &mut cache);
    for pk in packs.iter_mut() {
        let pid = py_str(&pk["id"]);
        let mut pa = art.remove(&pid).unwrap_or_default();
        for ch in pk["characters"].as_array_mut().into_iter().flatten() {
            let e = pa.remove(&py_str(&ch["id"]));
            let o = ch.as_object_mut().unwrap();
            o.insert("tint".into(), e.as_ref().map(|e| e.tint.clone()).unwrap_or(Value::Null));
            o.insert("img".into(), Value::Object(e.as_ref().map(|e| e.img.clone()).unwrap_or_default()));
            if let Some(seen) = e.and_then(|e| e.seen) {
                o.insert("seen".into(), s(&seen)); // a seen card's silhouette: this image key (the module doc)
            }
        }
        let ct = card_tints.get(&pid);
        if let Some(cards) = pk.get_mut("cards").and_then(|c| c.as_array_mut()) {
            for c in cards.iter_mut() {
                let t = ct.and_then(|m| m.get(c["id"].as_str().unwrap_or(""))).map(|t| s(t)).unwrap_or(Value::Null);
                c.as_object_mut().unwrap().insert("tint".into(), t);
            }
        }
        if pk["layout"] == "dex" {
            pk.as_object_mut().unwrap().insert("atlas".into(), atlas.clone());
        }
    }
    cache.save();
    let pruned = cache.prune();
    if !o.no_art {
        ctx.meta.borrow().save(); // (--no-art leaves img/ alone)
    }

    // slots (the page's: a real card, a character in a tier, or a pokedex character), caught vs only seen
    let layout: HashMap<String, String> = packs.iter().map(|p| (py_str(&p["id"]), py_str(&p["layout"]))).collect();
    let slot = |p: &Pull| -> (String, Option<String>, Option<String>) {
        let l = layout.get(&p.pack).map(String::as_str);
        let opt = |x: &str| if x.is_empty() { None } else { Some(x.to_string()) };
        let what = if l == Some("cards") { opt(&p.card) } else { Some(p.ch.clone()) };
        let tier = if matches!(l, Some("cards") | Some("dex")) { None } else { Some(p.tier.clone()) };
        (p.pack.clone(), what, tier)
    };
    let caught_slots: HashSet<_> = pulls.iter().filter(|p| p.status == "collected").map(slot).collect();
    let seen_slots: HashSet<_> = pulls.iter().map(slot).filter(|s| !caught_slots.contains(s)).collect();
    // the text half (HP, abilities, attacks ...) is for caught cards only (docs/BINDER_SPEC.md "Empty, seen, caught"): an
    // empty or seen card's text isn't even in data.json, so neither the page nor its search can show it; nor is its
    // printed card's scan (the `p` toggle)
    for pk in packs.iter_mut() {
        let pid = py_str(&pk["id"]);
        if let Some(cards) = pk.get_mut("cards").and_then(|c| c.as_array_mut()) {
            for c in cards.iter_mut() {
                let key = (pid.clone(), Some(py_str(&c["id"])), None);
                let o = c.as_object_mut().unwrap();
                if !caught_slots.contains(&key) {
                    o.shift_remove("text");
                    o.shift_remove("scan");
                } else if !o.get("scan").is_some_and(truthy) {
                    o.shift_remove("scan");
                }
            }
        }
    }
    let n_got = pulls.iter().filter(|p| p.status == "collected").count();
    let n_new = pulls.iter().filter(|p| p.new).count();
    let home = std::env::var("USERPROFILE").unwrap_or_else(|_| "~".into());
    let log_s = path_str(&log);
    let owner = o.owner.clone().unwrap_or_else(|| {
        std::env::var("POKESHELL_OWNER").ok().filter(|v| !v.is_empty()).unwrap_or_else(|| std::env::var("USERNAME").unwrap_or_else(|_| "you".into()))
    });
    let data = json!({
        "owner": owner,
        "generated": chrono::Local::now().format("%Y-%m-%dT%H:%M:%S").to_string(),
        "source": {"log": if home.is_empty() { log_s } else { log_s.replace(&home, "~") }, "pack_setting": pack_setting},
        "earned": {"enforced": true,
                   "note": "A card is caught once you use the tab it was pulled in: its first command earns it (docs/BINDER_SPEC.md). Until then (or if the tab closed unused) it is only seen: its silhouette."},
        // what the header counts: caught pulls and cards; seen cards (pulled, never caught) apart, never counted
        "counts": {"pulls": n_got, "caught": caught_slots.len(), "seen": seen_slots.len(),
                   "shiny": pulls.iter().filter(|p| p.status == "collected" && p.shiny).count(), "new": n_new},
        "hidden": hidden,      // pulls that no longer resolve to a current built card (retired art, unbuilt; still in pulls.log)
        "bad_lines": bad,      // pulls.log lines that couldn't be read (skipped)
        "best_since": best_since(cfg.get("best_since").map(String::as_str), real_since),   // best pulls start here (local ISO time); null: all
        "packs": packs, "skins": skins, "pulls": pulls.iter().map(Pull::to_value).collect::<Vec<_>>(),
    });
    let blob = dumps(&data, false);
    if let Err(e) = write_atomic(&out.join("data.json"), &text_bytes(&blob)) {
        eprintln!("binder: can't write data.json: {e}");
        return 1;
    }

    // bake: index.html with the data inlined
    let page = read_universal(&root.join("tools").join("binder-web").join("index.html")).unwrap_or_else(|| PAGE.replace("\r\n", "\n"));
    if !page.contains(MARKER) {
        eprintln!("index.html has no inline-data marker");
        return 1;
    }
    let baked = page.replacen(MARKER, &blob.replace("</", "<\\/"), 1);
    if let Err(e) = write_atomic(&out.join("binder.html"), &text_bytes(&baked)) {
        eprintln!("binder: can't write binder.html: {e}");
        return 1;
    }

    let art_note = if o.no_art {
        "art skipped (--no-art)".to_string()
    } else {
        format!("{} images ({} decoded, {} cached{})", cache.kept.len(), cache.decoded, cache.reused, if pruned > 0 { format!(", {pruned} stale removed") } else { String::new() })
    };
    println!(
        "{n_got} pulls caught ({} cards), {} seen, {n_new} new{}; {} packs, {} skins, {art_note} -> {} ({:.1} s)",
        caught_slots.len(),
        seen_slots.len(),
        if hidden > 0 { format!(", {hidden} retired (not shown)") } else { String::new() },
        data["packs"].as_array().map(|a| a.len()).unwrap_or(0),
        data["skins"].as_object().map(|o| o.len()).unwrap_or(0),
        path_str(&out),
        t0.elapsed().as_secs_f64()
    );
    0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn python_floats() {
        for (f, want) in [(0.1, "0.1"), (1.0, "1.0"), (1e-5, "1e-05"), (0.0001, "0.0001"), (1e16, "1e+16"), (123456789012345.6, "123456789012345.6"), (0.3333333333333333, "0.3333333333333333"), (2.5e-7, "2.5e-07"), (-0.5, "-0.5"), (0.0, "0.0")] {
            assert_eq!(py_repr_f64(f), want);
        }
        assert_eq!(round3(0.0625), 0.062);
        assert_eq!(round3(0.1875), 0.188);
        assert_eq!(round3(2.0 / 3.0), 0.667);
    }

    #[test]
    fn json_like_python() {
        let v = json!({"a": "é\u{1b}\n\"</", "b": [1, 2.0, null, true]});
        assert_eq!(dumps(&v, false), "{\"a\":\"é\\u001b\\n\\\"</\",\"b\":[1,2.0,null,true]}");
        assert_eq!(dumps(&json!("é😀\u{7f}"), true), "\"\\u00e9\\ud83d\\ude00\\u007f\"");
    }

    #[test]
    fn checklist_order() {
        let mut v = vec!["TG10", "B/128", "2", "SV6a", "100", "", "GG01", "25a", "215/203", "SV10", "1/203", "TG01", "SV6", "25", "GG10", "9", "10"];
        v.sort_by_key(|n| number_key(n));
        assert_eq!(v.join(","), "1/203,2,9,10,25,25a,100,215/203,GG01,GG10,SV6,SV6a,SV10,TG01,TG10,B/128,");
    }

    #[test]
    fn python_strings() {
        assert_eq!(title("mr mime"), "Mr Mime");
        assert_eq!(title("farfetch'd porygon2 2x"), "Farfetch'D Porygon2 2X");
        assert_eq!(splitlines("a\r\nb\rc\n\nd\n"), vec!["a", "b", "c", "", "d"]);
        assert!(is_time("2026-09-29T18:53:00") && is_time("2026-09-29 18:53") && is_time("2026-09-29T18:53:00.123+02:00") && is_time("2026-09-29T18:53Z"));
        assert!(!is_time("not-a-time") && !is_time("2026-09-29T18:53:") && !is_time("2026-09-29"));
        assert_eq!(best_since(Some("2026-01-02 10:00"), None), Some("2026-01-02T10:00".into()));
        assert_eq!(best_since(Some("all"), Some("x".into())), None);
        assert_eq!(best_since(Some("junk"), Some("x".into())), Some("x".into()));
    }

    #[test]
    fn decoders() {
        let t = "\n\x1b[0;38;2;10;20;30m▀\x1b[0m \n\n";
        let g = ansi_grid(t);
        assert_eq!(g, vec![vec![Some([10, 20, 30]), None]]);
        let d = dex_grid("  \n \x1b[38;2;1;2;3m▄\x1b[0m\n");
        assert_eq!(d, vec![vec![Some([1, 2, 3])]]);
        assert_eq!(tint_of(&vec![vec![Some([200, 40, 40]), Some([10, 10, 10])]]), "#c82828");
        assert_eq!(tint_of(&vec![vec![None]]), DEFAULT_TINT);
    }
}
