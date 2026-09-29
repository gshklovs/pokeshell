//! pulls.log + pack.json: the collection model.

use crate::color::{Rgb, hex, rgb};
use serde_json::Value;
use std::collections::HashMap;
use std::path::{Path, PathBuf};

// ---------------------------------------------------------------- time

/// "YYYY-MM-DDTHH:MM:SS" (local, naive) -> seconds since 1970-01-01 in the same naive clock.
pub fn parse_ts(s: &str) -> Option<i64> {
    let b = s.as_bytes();
    if b.len() < 19 {
        return None;
    }
    let n = |a: usize, z: usize| s.get(a..z)?.parse::<i64>().ok();
    let (y, mo, d) = (n(0, 4)?, n(5, 7)?, n(8, 10)?);
    let (h, mi, se) = (n(11, 13)?, n(14, 16)?, n(17, 19)?);
    Some(days_from_civil(y, mo, d) * 86400 + h * 3600 + mi * 60 + se)
}

/// config.txt `best_since`: "all" -> None (every pull); "YYYY-MM-DD[THH:MM[:SS]]" (local) -> Some(that time);
/// anything else (unset, unreadable) -> the default, when the real cards went live (Collection::real_since).
pub fn best_since(setting: Option<&str>, default: Option<i64>) -> Option<i64> {
    let v = setting.map(str::trim).unwrap_or("");
    if v.eq_ignore_ascii_case("all") {
        return None;
    }
    let v = v.replace(' ', "T");
    let full = match v.len() {
        10 => format!("{v}T00:00:00"),
        16 => format!("{v}:00"),
        _ => v,
    };
    parse_ts(&full).or(default)
}

/// A key of <state>/config.txt (`key=value` lines, the file the PowerShell side reads; the last one wins)
pub fn read_config(dir: &Path, key: &str) -> Option<String> {
    let text = std::fs::read_to_string(dir.join("config.txt")).ok()?;
    text.lines()
        .filter(|l| !l.starts_with('#'))
        .filter_map(|l| l.split_once('='))
        .filter(|(k, _)| k.trim().trim_start_matches('\u{feff}').eq_ignore_ascii_case(key))
        .last()
        .map(|(_, v)| v.trim().to_string())
}

pub fn days_from_civil(y: i64, m: i64, d: i64) -> i64 {
    let y = if m <= 2 { y - 1 } else { y };
    let era = y.div_euclid(400);
    let yoe = y - era * 400;
    let mp = (m + 9) % 12;
    let doy = (153 * mp + 2) / 5 + d - 1;
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    era * 146097 + doe - 719468
}

pub fn civil_from_days(z: i64) -> (i64, i64, i64) {
    let z = z + 719468;
    let era = z.div_euclid(146097);
    let doe = z - era * 146097;
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    (if m <= 2 { y + 1 } else { y }, m, d)
}

pub fn now_local() -> i64 {
    if let Ok(v) = std::env::var("BINDER_NOW") {
        if let Some(t) = parse_ts(&v) {
            return t;
        }
    }
    let n = chrono::Local::now().naive_local();
    n.and_utc().timestamp()
}

pub fn hhmm(ts: i64) -> String {
    let s = ts.rem_euclid(86400);
    format!("{:02}:{:02}", s / 3600, s / 60 % 60)
}

pub fn date_short(ts: i64) -> String {
    const M: [&str; 12] = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    let (_, m, d) = civil_from_days(ts.div_euclid(86400));
    format!("{} {}", M[(m - 1) as usize], d)
}

pub fn weekday(ts: i64) -> &'static str {
    const W: [&str; 7] = ["Thu", "Fri", "Sat", "Sun", "Mon", "Tue", "Wed"];
    W[ts.div_euclid(86400).rem_euclid(7) as usize]
}

/// "16:52" today, "Sep 27 16:52" otherwise.
pub fn when(ts: i64, now: i64) -> String {
    if ts.div_euclid(86400) == now.div_euclid(86400) {
        hhmm(ts)
    } else {
        format!("{} {}", date_short(ts), hhmm(ts))
    }
}

pub fn ago(secs: i64) -> String {
    let s = secs.max(0);
    if s < 60 {
        "just now".into()
    } else if s < 3600 {
        format!("{}m ago", s / 60)
    } else if s < 86400 {
        format!("{}h {}m ago", s / 3600, s / 60 % 60)
    } else {
        format!("{}d ago", s / 86400)
    }
}

// ---------------------------------------------------------------- pulls

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Status {
    /// Earned: its tab was used (or an older log line without an id).
    Collected,
    /// Pulled, but its tab has not been used yet (docs/BINDER_SPEC.md "Earning a card").
    Pending,
}

#[derive(Clone, Debug)]
pub struct Pull {
    pub ts: i64,
    pub pack: String,
    pub ch: String,
    pub tier: String,
    pub skin: String,
    pub shiny: bool,
    #[allow(dead_code)] // notes like "denied:rate"
    pub flags: String,
    pub status: Status,
    /// the pull id (a ULID; "" in logs from before the earned rule)
    pub id: String,
    /// the art column: for a real-card pack, the card id
    pub art: String,
    /// the real card this pull shows (a `card=` column in the log; set to the resolved card by Collection::build)
    pub card: String,
    /// earned and not viewed in the binder yet (the NEW sticker)
    pub new: bool,
}

/// A pending pull older than this is expired (Pokeshell.cs ExpireSec).
pub const EXPIRE_SECS: i64 = 24 * 3600;
/// Boot ids of one boot session differ by clock jitter only (Pokeshell.cs BootSlackSec).
pub const BOOT_SLACK_SECS: i64 = 120;
const CROCKFORD: &[u8] = b"0123456789ABCDEFGHJKMNPQRSTVWXYZ";

/// Unix milliseconds in a ULID pull id (None if it isn't one).
pub fn ulid_ms(id: &str) -> Option<i64> {
    let b = id.as_bytes();
    if b.len() != 26 {
        return None;
    }
    let mut ms: i64 = 0;
    for &c in &b[..10] {
        let v = CROCKFORD.iter().position(|&x| x == c.to_ascii_uppercase())? as i64;
        ms = ms * 32 + v;
    }
    Some(ms)
}

pub fn is_pull_id(s: &str) -> bool {
    s.len() == 26 && s.bytes().all(|c| CROCKFORD.contains(&c.to_ascii_uppercase()))
}

/// This boot session: unix seconds of the last boot (0 when unknown; then boot sessions aren't compared).
pub fn boot_id() -> i64 {
    #[cfg(windows)]
    {
        unsafe extern "system" {
            fn GetTickCount64() -> u64;
        }
        let up = unsafe { GetTickCount64() } as i64 / 1000;
        let now = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map(|d| d.as_secs() as i64).unwrap_or(0);
        now - up
    }
    #[cfg(not(windows))]
    {
        0
    }
}

pub fn now_utc() -> i64 {
    std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map(|d| d.as_secs() as i64).unwrap_or(0)
}

/// Ids the binder has already shown (viewed.txt, one per line): they don't get the NEW sticker.
pub fn read_viewed(path: &Path) -> std::collections::HashSet<String> {
    std::fs::read_to_string(path).map(|t| t.lines().map(|l| l.trim().to_string()).filter(|l| !l.is_empty()).collect()).unwrap_or_default()
}

/// Append ids to viewed.txt (append-only; duplicates are harmless).
pub fn mark_viewed(path: &Path, ids: &[String]) {
    if ids.is_empty() {
        return;
    }
    use std::io::Write;
    if let Ok(mut f) = std::fs::OpenOptions::new().create(true).append(true).open(path) {
        let mut s = String::new();
        for id in ids {
            s.push_str(id);
            s.push_str("\r\n");
        }
        let _ = f.write_all(s.as_bytes());
    }
}

/// The earned rule's inputs besides the log: the clock, this boot session, what was already viewed.
pub struct ReadCtx<'a> {
    pub now_utc: i64,
    pub boot: i64,
    pub viewed: &'a std::collections::HashSet<String>,
}

/// Parse pulls.log (docs/BINDER_SPEC.md; the same rules as Pokeshell.cs ReadPulls):
///   pull   time pack character tier art skin shiny flags [id=<ulid> boot=<s> card=<id> ...]
///   event  time earned:<id> | time expired:<id>
/// Dry runs are skipped; so are expired pulls (an `expired:` line, or pending for over 24 h, or from an earlier
/// boot session). A line without an id is earned. `demo_pending` marks the N most recent pulls pending (preview).
pub fn read_pulls(path: &Path, demo_pending: usize, ctx: &ReadCtx) -> Vec<Pull> {
    let Ok(text) = std::fs::read_to_string(path) else { return Vec::new() };
    let text = text.strip_prefix('\u{feff}').unwrap_or(&text);
    let mut earned = std::collections::HashSet::new();
    let mut expired = std::collections::HashSet::new();
    for line in text.lines() {
        let f: Vec<&str> = line.split('\t').collect();
        if f.len() < 2 || f.len() >= 7 {
            continue;
        }
        let ev = f[1].trim();
        if let Some(id) = ev.strip_prefix("earned:") {
            earned.insert(id.to_string());
        } else if let Some(id) = ev.strip_prefix("expired:") {
            expired.insert(id.to_string());
        }
    }
    let mut out = Vec::with_capacity(text.len() / 60);
    for line in text.lines() {
        let f: Vec<&str> = line.split('\t').collect();
        if f.len() < 7 {
            continue;
        }
        let flags = f.get(7).copied().unwrap_or("").trim();
        if flags.contains("dryrun") {
            continue;
        }
        let Some(ts) = parse_ts(f[0]) else { continue };
        let (mut id, mut boot, mut card) = (String::new(), 0i64, String::new());
        for kv in f.iter().skip(8) {
            if let Some((k, v)) = kv.split_once('=') {
                match k.trim() {
                    "id" => id = v.trim().to_string(),
                    "boot" => boot = v.trim().parse().unwrap_or(0),
                    "card" => card = v.trim().to_string(),
                    _ => {}
                }
            }
        }
        let pending_flag = flags.split(',').any(|x| x.trim() == "pending");
        let status = if id.is_empty() || !pending_flag || earned.contains(&id) {
            Status::Collected
        } else if expired.contains(&id) {
            continue;
        } else {
            let old = ulid_ms(&id).is_some_and(|ms| ctx.now_utc - ms / 1000 > EXPIRE_SECS);
            let other_boot = boot != 0 && ctx.boot != 0 && (boot - ctx.boot).abs() > BOOT_SLACK_SECS;
            if old || other_boot {
                continue;
            }
            Status::Pending
        };
        let new = status == Status::Collected && !id.is_empty() && !ctx.viewed.contains(&id);
        out.push(Pull {
            ts,
            pack: f[1].to_string(),
            ch: f[2].to_string(),
            tier: f[3].to_string(),
            art: f[4].to_string(),
            skin: f[5].to_string(),
            shiny: f[6].trim() == "1",
            flags: flags.to_string(),
            status,
            id,
            card,
            new,
        });
    }
    let n = out.len();
    for p in out.iter_mut().skip(n.saturating_sub(demo_pending)) {
        p.status = Status::Pending;
        p.new = false;
    }
    out
}

// ---------------------------------------------------------------- packs

#[derive(Clone, Debug)]
pub enum FrameSpec {
    /// Rounded box with a gradient border (preset name or explicit stops).
    Box(Vec<Rgb>),
    /// One Piece wanted poster; the palette name.
    Wanted(String),
}

#[derive(Clone, Debug)]
pub struct Tier {
    pub id: String,
    pub label: String,
    pub art: String,
    pub skins: Vec<(String, u32)>,
    pub weight: u32,
    pub frame: FrameSpec,
    /// Badge / bar color for this tier.
    pub color: Rgb,
    /// Real-card packs: the tier's odds weight (pack.json tier "weight") and display family ("non-foil", "holo", ...).
    pub odds_weight: u32,
    pub family: String,
}

/// A real card of a real-card pack (pack.json "cards"; docs/PACK_FORMAT.md).
#[derive(Clone, Debug)]
pub struct CardDef {
    pub id: String,
    pub ch: usize,
    pub tier: usize,
    pub name: String,
    pub number: String,
    /// from packs/<pack>/cards/<id>.json (docs/CARD_FORMAT.md) when it exists, else pack.json's card fields
    pub set_id: String,
    pub set_name: String,
    pub rarity: String,
    pub subtypes: Vec<String>,
    pub types: Vec<String>,
    pub artist: String,
}

impl CardDef {
    /// The number within its set, for checklist order ("215/203" -> 215; "SV6" -> 6).
    pub fn number_key(&self) -> (u32, String) {
        let n = self.number.split('/').next().unwrap_or("");
        let digits: String = n.chars().filter(|c| c.is_ascii_digit()).collect();
        (digits.parse().unwrap_or(u32::MAX), n.to_string())
    }
}

/// A set of a real-card pack, in the order its first card appears in pack.json.
#[derive(Clone, Debug)]
pub struct SetDef {
    pub id: String,
    pub name: String,
}

#[derive(Debug)]
pub struct Pack {
    pub id: String,
    pub name: String,
    pub dir: PathBuf,
    pub dist: PathBuf,
    pub foil: f64,
    pub shiny: f64,
    pub chars: Vec<String>,
    pub char_ix: HashMap<String, usize>,
    names: HashMap<String, String>,
    tags: HashMap<String, String>,
    posters: HashMap<String, String>,
    bounties: HashMap<String, String>,
    pub tiers: Vec<Tier>,
    pub total_weight: u32,
    /// A real-card pack (pack.json has "cards"): every slot is a real printed card keyed by its pokemontcg.io id.
    pub is_cards: bool,
    /// pack.json `cards` in file order (real-card packs only), built ones only (card_built): a card whose art isn't
    /// built is muted (it never rolls), so it is no binder slot and pulls that resolve to it are hidden
    pub card_list: Vec<CardDef>,
    card_ix: HashMap<String, usize>,
    /// (character, tier) -> indices into card_list
    slot_cards: HashMap<(usize, usize), Vec<usize>>,
    /// pack.json `retired`: an old "character/tier" -> the card it shows now, or None (hidden)
    pub retired: HashMap<String, Option<String>>,
    /// real-card packs: the sets their cards come from
    pub sets: Vec<SetDef>,
}

const PRESETS: &[(&str, &[u32])] = &[
    ("plain", &[0xc9a93a, 0xf4dc6a, 0xc9a93a]),
    ("silver", &[0x8d97a5, 0xeef3f8, 0x9aa6b4, 0xf7fafc, 0x8d97a5]),
    ("holo", &[0x7fa7d9, 0xe6f0ff, 0xb59ce0, 0xe8fbff, 0x7fd3c9]),
    ("rainbow", &[0xff6b8b, 0xffb86b, 0xffe66b, 0x7df09a, 0x6bd5ff, 0x9a8bff, 0xff6bd6]),
    ("gold", &[0xb8862b, 0xfff1b0, 0xd4a43a, 0xfff7d6, 0xc8952e]),
];

fn preset(name: &str) -> Option<Vec<Rgb>> {
    PRESETS
        .iter()
        .find(|(n, _)| n.eq_ignore_ascii_case(name))
        .map(|(_, s)| s.iter().map(|&v| rgb(v)).collect())
}

fn parse_frame(v: Option<&Value>, ti: usize, ntiers: usize) -> FrameSpec {
    match v {
        Some(Value::String(s)) => {
            if let Some(p) = preset(s) {
                return FrameSpec::Box(p);
            }
            let stops: Vec<Rgb> = s.split(',').filter_map(hex).collect();
            if !stops.is_empty() {
                return FrameSpec::Box(stops);
            }
        }
        Some(Value::Array(a)) => {
            let stops: Vec<Rgb> = a.iter().filter_map(|x| x.as_str().and_then(hex)).collect();
            if !stops.is_empty() {
                return FrameSpec::Box(stops);
            }
        }
        Some(Value::Object(o)) => {
            if o.get("style").and_then(|s| s.as_str()) == Some("wanted") {
                let pal = o.get("palette").and_then(|s| s.as_str()).unwrap_or("common");
                return FrameSpec::Wanted(if pal == "manga-rare" { "manga".into() } else { pal.to_string() });
            }
        }
        _ => {}
    }
    // Frameless tier: pick a preset by rarity rank so every card in the binder still gets a frame.
    let order = ["plain", "silver", "holo", "rainbow", "gold"];
    let k = if ntiers <= 1 { 0 } else { (ti * (order.len() - 1) + (ntiers - 2) / 2) / (ntiers - 1) };
    FrameSpec::Box(preset(order[k.min(order.len() - 1)]).unwrap())
}

fn tier_color(frame: &FrameSpec, ti: usize, ntiers: usize) -> Rgb {
    match frame {
        FrameSpec::Wanted(p) => match p.as_str() {
            "super-rare" => rgb(0xe8744f),
            "secret-rare" => rgb(0xf5c542),
            "manga" => rgb(0xff5d6c),
            _ => rgb(0xd9c08a),
        },
        FrameSpec::Box(_) => {
            // the banner colors of Pokeshell.cs, stretched over the tier count
            const C: [u32; 5] = [0x9aa0aa, 0xb9d7eb, 0x6ea5ff, 0xe178e6, 0xf0c850];
            let k = if ntiers <= 1 { 0 } else { (ti * 4 + (ntiers - 2) / 2) / (ntiers - 1) };
            rgb(C[k.min(4)])
        }
    }
}

/// The card's tag fields from its card-data JSON (docs/CARD_FORMAT.md), when the file exists.
fn read_card_text(path: &Path, c: &mut CardDef) {
    let Ok(b) = std::fs::read(path) else { return };
    let Ok(v) = serde_json::from_slice::<Value>(b.strip_prefix(b"\xef\xbb\xbf".as_slice()).unwrap_or(&b)) else { return };
    let s = |x: Option<&Value>| x.and_then(|x| x.as_str()).unwrap_or("").to_string();
    let list = |k: &str| v.get(k).and_then(|x| x.as_array()).map(|a| a.iter().filter_map(|x| x.as_str().map(String::from)).collect()).unwrap_or_default();
    if let Some(set) = v.get("set") {
        if !s(set.get("id")).is_empty() {
            c.set_id = s(set.get("id"));
        }
        if !s(set.get("name")).is_empty() {
            c.set_name = s(set.get("name"));
        }
    }
    if !s(v.get("rarity")).is_empty() {
        c.rarity = s(v.get("rarity"));
    }
    if c.name.is_empty() {
        c.name = s(v.get("name"));
    }
    c.subtypes = list("subtypes");
    c.types = list("types");
    c.artist = s(v.get("artist"));
}

fn str_map(v: &Value, key: &str) -> HashMap<String, String> {
    v.get(key)
        .and_then(|m| m.as_object())
        .map(|o| o.iter().filter_map(|(k, v)| Some((k.clone(), v.as_str()?.to_string()))).collect())
        .unwrap_or_default()
}

/// Is a real card's art built? dist/<pack>/<character>-<card id>.ans exists: the test the roll uses
/// (Test-PokeshellCardBuilt in scripts/lib/common.ps1). Checked when the pack loads, so a card built later shows up
/// (with its old pulls) the next time the binder starts; pulls.log is never rewritten.
pub fn card_built(dist: &Path, ch: &str, id: &str) -> bool {
    dist.join(format!("{ch}-{id}.ans")).is_file()
}

impl Pack {
    pub fn load(root: &Path, id: &str) -> Option<Pack> {
        let dir = root.join("packs").join(id);
        let bytes = std::fs::read(dir.join("pack.json")).ok()?;
        let v: Value = serde_json::from_slice(bytes.strip_prefix(b"\xef\xbb\xbf".as_slice()).unwrap_or(&bytes)).ok()?;
        let cards_v = v.get("cards").and_then(|x| x.as_object());
        let is_cards = cards_v.is_some();
        // characters: pack.json's list, else (real-card packs) the cards' characters in file order
        let mut chars: Vec<String> = v
            .get("characters")
            .and_then(|x| x.as_array())
            .map(|a| a.iter().filter_map(|c| c.as_str().map(String::from)).collect())
            .unwrap_or_default();
        let dist = root.join("dist").join(id);
        if let Some(cm) = cards_v {
            for (cid, c) in cm {
                if let Some(ch) = c.get("character").and_then(|x| x.as_str()) {
                    if card_built(&dist, ch, cid) && !chars.iter().any(|x| x == ch) {
                        chars.push(ch.to_string());
                    }
                }
            }
        }
        if chars.is_empty() && !is_cards {
            return None;
        }
        let tv = v.get("tiers")?.as_array()?;
        let n = tv.len();
        let tiers: Vec<Tier> = tv
            .iter()
            .enumerate()
            .map(|(i, t)| {
                let s = |k: &str| t.get(k).and_then(|x| x.as_str()).unwrap_or("").to_string();
                let skins: Vec<(String, u32)> = t
                    .get("skins")
                    .and_then(|x| x.as_object())
                    .map(|o| o.iter().map(|(k, w)| (k.clone(), w.as_u64().unwrap_or(0) as u32)).collect())
                    .unwrap_or_default();
                let frame = parse_frame(t.get("frame"), i, n);
                let color = tier_color(&frame, i, n);
                let id = s("id");
                let label = if s("label").is_empty() { id.clone() } else { s("label") };
                let odds_weight = t.get("weight").and_then(|x| x.as_u64()).unwrap_or(0) as u32;
                Tier { weight: skins.iter().map(|s| s.1).sum(), id, label, art: s("art"), skins, frame, color, odds_weight, family: s("family") }
            })
            .collect();
        let total_weight = tiers.iter().skip(1).map(|t| t.weight).sum();
        let char_ix: HashMap<String, usize> = chars.iter().enumerate().map(|(i, c)| (c.clone(), i)).collect();
        let tier_of = |id: &str| tiers.iter().position(|t| t.id == id);
        let mut card_list = Vec::new();
        if let Some(cm) = cards_v {
            for (cid, c) in cm {
                let s = |k: &str| c.get(k).and_then(|x| x.as_str()).unwrap_or("").to_string();
                let (Some(&ch), Some(tier)) = (char_ix.get(&s("character")), tier_of(&s("tier"))) else { continue };
                if !card_built(&dist, &s("character"), cid) {
                    continue; // muted: no art built yet (its pulls are hidden until it is)
                }
                let mut card = CardDef {
                    id: cid.clone(),
                    ch,
                    tier,
                    name: s("name"),
                    number: s("number"),
                    set_id: cid.rsplit_once('-').map(|(a, _)| a.to_string()).unwrap_or_default(),
                    set_name: s("set"),
                    rarity: s("rarity"),
                    subtypes: vec![],
                    types: vec![],
                    artist: String::new(),
                };
                read_card_text(&dir.join("cards").join(format!("{cid}.json")), &mut card);
                card_list.push(card);
            }
        }
        let mut sets: Vec<SetDef> = Vec::new();
        for c in &card_list {
            if !c.set_id.is_empty() && !sets.iter().any(|s| s.id == c.set_id) {
                let name = if c.set_name.is_empty() { c.set_id.clone() } else { c.set_name.clone() };
                sets.push(SetDef { id: c.set_id.clone(), name });
            }
        }
        let card_ix = card_list.iter().enumerate().map(|(i, c)| (c.id.clone(), i)).collect();
        let mut slot_cards: HashMap<(usize, usize), Vec<usize>> = HashMap::new();
        for (i, c) in card_list.iter().enumerate() {
            slot_cards.entry((c.ch, c.tier)).or_default().push(i);
        }
        // retired: { "<character>/<tier>": "<card id>" | null } (docs/PACK_FORMAT.md); a plain list hides its entries
        let retired = match v.get("retired") {
            Some(Value::Object(o)) => o.iter().map(|(k, x)| (k.clone(), x.as_str().map(String::from))).collect(),
            Some(Value::Array(a)) => a.iter().filter_map(|x| x.as_str().map(|s| (s.to_string(), None))).collect(),
            _ => HashMap::new(),
        };
        Some(Pack {
            id: id.to_string(),
            name: v.get("name").and_then(|x| x.as_str()).unwrap_or(id).to_string(),
            dist,
            dir,
            foil: v.get("foil_chance").and_then(|x| x.as_f64()).unwrap_or(0.2),
            shiny: v.get("shiny_chance").and_then(|x| x.as_f64()).unwrap_or(0.0),
            char_ix,
            chars,
            names: str_map(&v, "names"),
            tags: str_map(&v, "tags"),
            posters: str_map(&v, "poster_names"),
            bounties: str_map(&v, "bounties"),
            tiers,
            total_weight,
            is_cards,
            card_list,
            card_ix,
            slot_cards,
            retired,
            sets,
        })
    }

    /// What a logged pull shows today (the same rule as Resolve-PokeshellPull in scripts/lib/common.ps1 and
    /// docs/PACK_FORMAT.md "retired"): (character index, tier index, card id), or None to hide it.
    ///   - packs without "cards": as logged (tier by id, or by label);
    ///   - real-card packs: the art column (or a `card=` column) is a card id of this pack whose character matches:
    ///     that card, in its tier; else retired["<character>/<tier>"] names a card: that card; else hidden.
    ///     A card whose art isn't built is not in card_list, so a pull resolving to it is hidden too.
    pub fn resolve(&self, ch: &str, tier: &str, art: &str, card: &str) -> Option<(usize, usize, Option<String>)> {
        if !self.is_cards {
            let ci = *self.char_ix.get(ch)?;
            let ti = self.tier_ix(tier).or_else(|| self.tiers.iter().position(|t| t.label.eq_ignore_ascii_case(tier)))?;
            return Some((ci, ti, None));
        }
        if let Some(c) = self.logged_card(ch, art, card) {
            return Some((c.ch, c.tier, Some(c.id.clone())));
        }
        let now = self.retired.get(&format!("{ch}/{tier}"))?.as_deref()?;
        let c = self.card(now)?;
        Some((c.ch, c.tier, Some(c.id.clone())))
    }

    /// The (built) real card a pull line names itself: its `card=` or art column is a card id of this pack, of the
    /// same character. None for older lines (resolved through `retired`, if at all) and packs without cards.
    pub fn logged_card(&self, ch: &str, art: &str, card: &str) -> Option<&CardDef> {
        [card, art].into_iter().filter_map(|cid| self.card(cid)).find(|c| self.chars[c.ch] == ch)
    }

    pub fn card(&self, id: &str) -> Option<&CardDef> {
        if id.is_empty() {
            return None;
        }
        self.card_ix.get(id).map(|&i| &self.card_list[i])
    }

    /// Is there a card in this slot? (always, outside real-card packs)
    pub fn has_slot(&self, ch: usize, tier: usize) -> bool {
        !self.is_cards || self.slot_cards.contains_key(&(ch, tier))
    }

    /// Tiers that hold at least one card (real-card packs); every tier otherwise.
    pub fn live_tiers(&self) -> Vec<usize> {
        (0..self.tiers.len()).filter(|&t| !self.is_cards || (0..self.chars.len()).any(|c| self.has_slot(c, t))).collect()
    }

    /// Slots in the full set: characters x tiers, or (real-card packs) one per card (a character can have several
    /// cards in one rarity: each is its own slot).
    pub fn slot_count(&self) -> usize {
        if self.is_cards { self.card_list.len() } else { self.chars.len() * self.tiers.len() }
    }

    /// The card of a slot (real-card packs: SlotKey.card), if any.
    pub fn card_at(&self, card: u32) -> Option<&CardDef> {
        if card == NO_CARD { None } else { self.card_list.get(card as usize) }
    }

    /// The name on a slot's frame: the card's printed name (e.g. "Pikachu V"), else the character's.
    pub fn name_for(&self, ch: usize, card: u32) -> String {
        match self.card_at(card) {
            Some(c) if !c.name.is_empty() => c.name.clone(),
            _ => self.name_of(&self.chars[ch]),
        }
    }

    /// The tag on a slot's frame: the card's printed number (e.g. "170/185"), else the character's tag.
    pub fn tag_for(&self, ch: usize, card: u32) -> String {
        match self.card_at(card) {
            Some(c) => c.number.clone(),
            None => self.tag_of(&self.chars[ch]).to_string(),
        }
    }

    /// The art variant a slot draws: its card id (dist/<pack>/<character>-<card id>.ans), else the tier's art.
    pub fn art_at(&self, k: SlotKey) -> String {
        match self.card_at(k.card) {
            Some(c) => c.id.clone(),
            None => self.tiers[k.tier].art.clone(),
        }
    }

    /// Every tag of a slot (search, the card panel): (key, value). Keys: pack, char, name, tier, rarity, set, setname,
    /// subtype, type, artist, number, id. The state tags (shiny, foil, new, pending, owned) come from the collection.
    pub fn slot_tags(&self, k: SlotKey) -> Vec<(&'static str, String)> {
        let mut v: Vec<(&'static str, String)> = vec![
            ("pack", self.id.clone()),
            ("pack", self.name.clone()),
            ("char", self.chars[k.ch].clone()),
            ("name", self.name_for(k.ch, k.card)),
            ("tier", self.tiers[k.tier].id.clone()),
            ("tier", self.tiers[k.tier].label.clone()),
        ];
        match self.card_at(k.card) {
            Some(c) => {
                v.push(("id", c.id.clone()));
                v.push(("number", c.number.clone()));
                if !c.rarity.is_empty() {
                    v.push(("rarity", c.rarity.clone()));
                }
                if !c.set_id.is_empty() {
                    v.push(("set", c.set_id.clone()));
                }
                if !c.set_name.is_empty() {
                    v.push(("set", c.set_name.clone()));
                }
                v.extend(c.subtypes.iter().map(|s| ("subtype", s.clone())));
                v.extend(c.types.iter().map(|s| ("type", s.clone())));
                if !c.artist.is_empty() {
                    v.push(("artist", c.artist.clone()));
                }
            }
            None => {
                v.push(("rarity", self.tiers[k.tier].label.clone()));
                let tag = self.tag_of(&self.chars[k.ch]);
                if !tag.is_empty() {
                    v.push(("number", tag.to_string()));
                }
            }
        }
        v
    }

    /// Is this tier a foil (gets the shimmer; counts as a foil pull)? Real-card packs: a tier with skins or a foil
    /// family; other packs: every tier above the first.
    pub fn foil_tier(&self, tier: usize) -> bool {
        if !self.is_cards {
            return tier > 0;
        }
        let t = &self.tiers[tier];
        !t.skins.is_empty() || !(t.family.is_empty() || t.family == "non-foil")
    }

    /// The card-data file (docs/CARD_FORMAT.md) for a slot: packs/<pack>/cards/<card id>.json; packs without real
    /// cards: <character>-<tier>.json or <character>.json there.
    pub fn card_file(&self, k: SlotKey) -> Option<PathBuf> {
        let dir = self.dir.join("cards");
        let mut ids: Vec<String> = Vec::new();
        if let Some(c) = self.card_at(k.card) {
            ids.push(c.id.clone());
        }
        let (cid, tid) = (&self.chars[k.ch], &self.tiers[k.tier].id);
        ids.push(format!("{cid}-{tid}"));
        ids.push(cid.clone());
        ids.into_iter().map(|id| dir.join(format!("{id}.json"))).find(|p| p.is_file())
    }
    pub fn name_of(&self, ch: &str) -> String {
        if let Some(n) = self.names.get(ch) {
            return n.clone();
        }
        ch.split('-')
            .map(|p| {
                let mut c = p.chars();
                c.next().map(|f| f.to_uppercase().collect::<String>() + c.as_str()).unwrap_or_default()
            })
            .collect::<Vec<_>>()
            .join(" ")
    }
    pub fn tag_of(&self, ch: &str) -> &str {
        self.tags.get(ch).map(|s| s.as_str()).unwrap_or("")
    }
    pub fn poster_of(&self, ch: &str) -> String {
        self.posters.get(ch).cloned().unwrap_or_else(|| self.name_of(ch).to_uppercase())
    }
    pub fn bounty_of(&self, ch: &str) -> &str {
        self.bounties.get(ch).map(|s| s.as_str()).unwrap_or("")
    }
    pub fn tier_ix(&self, id: &str) -> Option<usize> {
        self.tiers.iter().position(|t| t.id == id)
    }
    /// Odds a pull from this pack lands in tier `ti`.
    pub fn tier_p(&self, ti: usize) -> f64 {
        if self.is_cards {
            // a tier by its weight among the tiers that have cards
            let live = self.live_tiers();
            let tot: u64 = live.iter().map(|&t| self.tiers[t].odds_weight as u64).sum();
            return if tot == 0 || !live.contains(&ti) { 0.0 } else { self.tiers[ti].odds_weight as f64 / tot as f64 };
        }
        if ti == 0 {
            if self.total_weight == 0 { 1.0 } else { 1.0 - self.foil }
        } else if self.total_weight == 0 {
            0.0
        } else {
            self.foil * self.tiers[ti].weight as f64 / self.total_weight as f64
        }
    }
    /// Odds of one exact card (character x tier [x shiny]).
    pub fn card_p(&self, ti: usize, shiny: bool) -> f64 {
        let n = if self.is_cards { self.card_list.iter().filter(|c| c.tier == ti).count() } else { self.chars.len() };
        let p = self.tier_p(ti) / n.max(1) as f64;
        if shiny { p * self.shiny } else { p }
    }
    /// Big packs (the 905-mon pokedex) default to one binder slot per character.
    pub fn is_big(&self) -> bool {
        self.chars.len() > 40
    }
}

/// packs/*/pack.json, ordered by first appearance in the log, then by id.
pub fn load_packs(root: &Path, pulls: &[Pull]) -> Vec<Pack> {
    let mut ids: Vec<String> = std::fs::read_dir(root.join("packs"))
        .map(|rd| {
            rd.filter_map(|e| e.ok())
                .filter(|e| e.path().join("pack.json").is_file())
                .filter_map(|e| e.file_name().into_string().ok())
                .collect()
        })
        .unwrap_or_default();
    let first = |id: &str| pulls.iter().position(|p| p.pack == id).unwrap_or(usize::MAX);
    ids.sort_by(|a, b| first(a).cmp(&first(b)).then(a.cmp(b)));
    ids.iter().filter_map(|id| Pack::load(root, id)).collect()
}

// ---------------------------------------------------------------- collection index

/// A binder slot: one character in one tier.
#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
pub struct SlotKey {
    pub pack: usize,
    pub ch: usize,
    pub tier: usize,
    /// real-card packs: the card (an index into Pack::card_list); NO_CARD for other packs
    pub card: u32,
}

/// SlotKey.card of a pack without real cards
pub const NO_CARD: u32 = u32::MAX;

impl SlotKey {
    pub fn legacy(pack: usize, ch: usize, tier: usize) -> SlotKey {
        SlotKey { pack, ch, tier, card: NO_CARD }
    }
}

pub struct Collection {
    pub pulls: Vec<Pull>,
    pub packs: Vec<Pack>,
    /// slot -> indices into `pulls` (chronological)
    pub by_slot: HashMap<SlotKey, Vec<usize>>,
    /// pull index -> its slot (None: pack/character/tier unknown to the current pack.json)
    pub slot_of: Vec<Option<SlotKey>>,
    /// pulls left out because they no longer resolve (retired art, a card whose art isn't built, a pack or character
    /// that is gone)
    pub hidden: usize,
    /// when the real cards went live: the first shown pull whose line names a built real card itself (not through
    /// `retired`); the default start of the best pulls (best_since)
    pub real_since: Option<i64>,
}

impl Collection {
    /// Pulls that don't resolve to a current card (Pack::resolve: a pack, character or tier that is gone, a
    /// real-card pack's retired art, or a card whose art isn't built) are left out of the binder; pulls.log itself is never rewritten.
    pub fn build(pulls: Vec<Pull>, packs: Vec<Pack>) -> Collection {
        let mut by_slot: HashMap<SlotKey, Vec<usize>> = HashMap::new();
        let pack_ix: HashMap<&str, usize> = packs.iter().enumerate().map(|(i, p)| (p.id.as_str(), i)).collect();
        let mut kept = Vec::with_capacity(pulls.len());
        let mut slot_of = Vec::with_capacity(pulls.len());
        let mut hidden = 0;
        let mut real_since: Option<i64> = None;
        for mut p in pulls {
            let key = pack_ix.get(p.pack.as_str()).and_then(|&pi| {
                let (ch, tier, card) = packs[pi].resolve(&p.ch, &p.tier, &p.art, &p.card)?;
                let ci = card.as_deref().and_then(|c| packs[pi].card_ix.get(c)).map(|&i| i as u32).unwrap_or(NO_CARD);
                Some((SlotKey { pack: pi, ch, tier, card: ci }, card))
            });
            let Some((k, card)) = key else {
                hidden += 1;
                continue;
            };
            if packs[k.pack].logged_card(&p.ch, &p.art, &p.card).is_some() {
                real_since = Some(real_since.map_or(p.ts, |t| t.min(p.ts)));
            }
            if let Some(c) = card {
                p.card = c;
            }
            by_slot.entry(k).or_default().push(kept.len());
            slot_of.push(Some(k));
            kept.push(p);
        }
        Collection { pulls: kept, packs, by_slot, slot_of, hidden, real_since }
    }

    /// Does this slot hold an earned pull that hasn't been viewed yet?
    pub fn slot_new(&self, k: SlotKey, shiny_only: bool) -> bool {
        self.slot_pulls(k).iter().any(|&i| self.pulls[i].new && (!shiny_only || self.pulls[i].shiny))
    }

    pub fn new_count(&self) -> usize {
        self.pulls.iter().filter(|p| p.new).count()
    }

    pub fn slot_pulls(&self, k: SlotKey) -> &[usize] {
        self.by_slot.get(&k).map(|v| v.as_slice()).unwrap_or(&[])
    }

    /// Owned = at least one collected pull (optionally shiny only). Pending-only slots are "pending".
    pub fn slot_state(&self, k: SlotKey, shiny_only: bool) -> SlotState {
        let mut pend = false;
        for &i in self.slot_pulls(k) {
            let p = &self.pulls[i];
            if shiny_only && !p.shiny {
                continue;
            }
            match p.status {
                Status::Collected => return SlotState::Owned,
                Status::Pending => pend = true,
            }
        }
        if pend { SlotState::Pending } else { SlotState::Empty }
    }

    /// The highest-tier slot this character is owned (or pending) in: the one-slot-per-character "dex" view.
    pub fn best_slot(&self, pack: usize, ch: usize, shiny_only: bool) -> Option<SlotKey> {
        self.by_slot
            .keys()
            .filter(|k| k.pack == pack && k.ch == ch && self.slot_state(**k, shiny_only) != SlotState::Empty)
            .max_by_key(|k| (k.tier, std::cmp::Reverse(k.card)))
            .copied()
    }
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum SlotState {
    Owned,
    Pending,
    Empty,
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    fn ulid_at(secs: i64, tail: &str) -> String {
        let mut ms = secs * 1000;
        let mut s = vec![b'0'; 10];
        for i in (0..10).rev() {
            s[i] = CROCKFORD[(ms % 32) as usize];
            ms /= 32;
        }
        String::from_utf8(s).unwrap() + tail
    }

    fn tmp(name: &str) -> PathBuf {
        let d = std::env::temp_dir().join(format!("binder-test-{name}-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&d);
        std::fs::create_dir_all(&d).unwrap();
        d
    }

    #[test]
    fn earned_pending_expired() {
        let now = 1_790_000_000i64;
        let boot = now - 3600;
        let (e, p, old, ob, v) = (
            ulid_at(now - 600, "EEEEEEEEEEEEEEEE"),
            ulid_at(now - 60, "PPPPPPPPPPPPPPPP"),
            ulid_at(now - 30 * 3600, "0000000000000000"),
            ulid_at(now - 60, "BBBBBBBBBBBBBBBB"),
            ulid_at(now - 900, "VVVVVVVVVVVVVVVV"),
        );
        let t = "2026-09-28T10:00:00";
        let log = [
            format!("{t}\tpokemon\tsquirtle\tcommon\tcommon\t\t0\t"),
            format!("{t}\tpokemon\tpikachu\tcommon\tcommon\t\t0\tpending\tid={e}\tboot={boot}"),
            format!("{t}\tearned:{e}"),
            format!("{t}\tpokemon\tpikachu\tholo\tholo\tsheen\t0\tdenied:rate,pending\tid={p}\tboot={boot}"),
            format!("{t}\tpokemon\tbulbasaur\tholo\tholo\tsheen\t0\tpending\tid={old}\tboot={boot}"),
            format!("{t}\tpokemon\tbulbasaur\tcommon\tcommon\t\t0\tpending\tid={ob}\tboot={}", boot - 86400),
            format!("{t}\tpokemon\tbulbasaur\tcommon\tcommon\t\t0\tdryrun,pending\tid=x\tboot={boot}"),
            format!("{t}\tpokemon\tcharmander\tcommon\tcommon\t\t0\tpending\tid={v}\tboot={boot}\tcard=base1-46"),
            format!("{t}\tearned:{v}"),
        ];
        let d = tmp("earned");
        std::fs::write(d.join("pulls.log"), log.join("\r\n")).unwrap();
        let viewed: HashSet<String> = [v.clone()].into_iter().collect();
        let pulls = read_pulls(&d.join("pulls.log"), 0, &ReadCtx { now_utc: now, boot, viewed: &viewed });
        let got: Vec<(&str, Status, bool)> = pulls.iter().map(|p| (p.ch.as_str(), p.status, p.new)).collect();
        assert_eq!(
            got,
            vec![
                ("squirtle", Status::Collected, false), // no id: earned, never NEW
                ("pikachu", Status::Collected, true),   // earned, not viewed
                ("pikachu", Status::Pending, false),    // pending, fresh, this boot
                ("charmander", Status::Collected, false),
            ]
        );
        assert_eq!(pulls[3].card, "base1-46");
        let _ = std::fs::remove_dir_all(&d);
    }

    #[test]
    fn resolve_real_cards_and_retired() {
        // docs/PACK_FORMAT.md "retired", the rule of Resolve-PokeshellPull
        let d = tmp("resolve");
        std::fs::create_dir_all(d.join("packs/p/cards")).unwrap();
        std::fs::write(
            d.join("packs/p/pack.json"),
            r#"{ "id": "p",
                 "tiers": [ { "id": "common", "label": "common", "family": "non-foil", "weight": 50000, "skins": {} },
                            { "id": "rare-holo", "label": "rare holo", "family": "holo", "weight": 5000, "skins": { "cosmos": 1 } },
                            { "id": "rare-ultra", "label": "rare ultra", "family": "full-art", "weight": 650, "skins": {} } ],
                 "cards": { "base1-58": { "character": "pikachu", "tier": "common", "name": "Pikachu", "number": "58/102" },
                            "swsh4-170": { "character": "pikachu", "tier": "rare-ultra", "name": "Pikachu V", "number": "170/185" },
                            "base1-44": { "character": "bulbasaur", "tier": "common", "name": "Bulbasaur", "number": "44/102" } },
                 "retired": { "pikachu/common": "base1-58", "pikachu/holo": null } }"#,
        )
        .unwrap();
        std::fs::write(
            d.join("packs/p/cards/swsh4-170.json"),
            r#"{ "id": "swsh4-170", "name": "Pikachu V", "subtypes": ["Basic", "V"], "types": ["Lightning"],
                 "set": { "id": "swsh4", "name": "Vivid Voltage" }, "rarity": "Rare Ultra", "artist": "Ryota Murayama" }"#,
        )
        .unwrap();
        std::fs::create_dir_all(d.join("dist/p")).unwrap();
        for f in ["pikachu-base1-58", "pikachu-swsh4-170", "bulbasaur-base1-44"] {
            std::fs::write(d.join(format!("dist/p/{f}.ans")), "x").unwrap();
        }
        let p = Pack::load(&d, "p").unwrap();
        assert!(p.is_cards);
        assert_eq!(p.chars, vec!["pikachu".to_string(), "bulbasaur".to_string()], "characters come from the cards");
        let pk = p.char_ix["pikachu"];
        assert_eq!(p.resolve("pikachu", "rare-ultra", "swsh4-170", ""), Some((pk, 2, Some("swsh4-170".into()))), "the art column is the card id");
        assert_eq!(p.resolve("pikachu", "common", "common", ""), Some((pk, 0, Some("base1-58".into()))), "an old common -> its base-set common");
        assert_eq!(p.resolve("pikachu", "holo", "holo", ""), None, "retired to null: hidden");
        assert_eq!(p.resolve("pikachu", "secret-rare", "gold", ""), None, "not listed: hidden");
        assert_eq!(p.resolve("bulbasaur", "rare-ultra", "swsh4-170", ""), None, "a card of another character doesn't count");
        assert!(p.has_slot(pk, 2) && !p.has_slot(pk, 1) && p.slot_count() == 3);
        assert_eq!(p.live_tiers(), vec![0, 2]);
        let v = p.card_list.iter().position(|c| c.id == "swsh4-170").unwrap() as u32;
        let kv = SlotKey { pack: 0, ch: pk, tier: 2, card: v };
        assert_eq!(p.name_for(pk, v), "Pikachu V");
        assert_eq!(p.tag_for(pk, v), "170/185");
        assert_eq!(p.art_at(kv), "swsh4-170");
        assert!(!p.foil_tier(0) && p.foil_tier(1) && p.foil_tier(2));
        assert!((p.tier_p(2) - 650.0 / 50650.0).abs() < 1e-9, "odds among the tiers that have cards");
        assert!(p.card_file(kv).unwrap().ends_with("swsh4-170.json"));
        let base = p.card_list.iter().position(|c| c.id == "base1-58").unwrap() as u32;
        assert!(p.card_file(SlotKey { pack: 0, ch: pk, tier: 0, card: base }).is_none());
        // tags: from cards/<id>.json (set, rarity, subtypes, types, artist) and pack.json
        let c = &p.card_list[v as usize];
        assert_eq!((c.set_id.as_str(), c.set_name.as_str(), c.rarity.as_str(), c.artist.as_str()), ("swsh4", "Vivid Voltage", "Rare Ultra", "Ryota Murayama"));
        assert_eq!(c.types, vec!["Lightning".to_string()]);
        let tags = p.slot_tags(kv);
        for want in [("set", "swsh4"), ("set", "Vivid Voltage"), ("subtype", "V"), ("type", "Lightning"), ("char", "pikachu"), ("tier", "rare-ultra"), ("pack", "p")] {
            assert!(tags.iter().any(|(k, x)| *k == want.0 && x == want.1), "tag {want:?}");
        }
        use crate::query::{Flags, matches, parse};
        assert!(matches(&parse(r#"set:swsh4 type:lightning "pikachu v""#), &tags, Flags::default()));
        assert!(!matches(&parse("set:swsh7"), &tags, Flags::default()));
        // without card text: the set id comes from the card id, the set name from pack.json
        assert_eq!(p.card_list[base as usize].set_id, "base1");
        assert_eq!(p.sets.iter().map(|s| s.id.as_str()).collect::<Vec<_>>(), vec!["base1", "swsh4"]);
        // a pack without cards: pulls show as logged (tier by id or label)
        std::fs::create_dir_all(d.join("packs/l")).unwrap();
        std::fs::write(d.join("packs/l/pack.json"), r#"{ "id": "l", "characters": ["a"], "tiers": [ { "id": "common" }, { "id": "rare-holo", "label": "rare holo" } ] }"#).unwrap();
        let l = Pack::load(&d, "l").unwrap();
        assert_eq!(l.resolve("a", "rare holo", "holo", ""), Some((0, 1, None)));
        assert!(l.slot_tags(SlotKey::legacy(0, 0, 1)).iter().any(|(k, v)| *k == "tier" && v == "rare holo"));
        assert_eq!(l.resolve("b", "common", "common", ""), None);
        let _ = std::fs::remove_dir_all(&d);
    }
    fn pull(ts: i64, ch: &str, tier: &str, art: &str, shiny: bool) -> Pull {
        Pull {
            ts,
            pack: "p".into(),
            ch: ch.into(),
            tier: tier.into(),
            skin: String::new(),
            shiny,
            flags: String::new(),
            status: Status::Collected,
            id: String::new(),
            art: art.into(),
            card: String::new(),
            new: false,
        }
    }

    #[test]
    fn unbuilt_cards_are_muted() {
        // a card whose art isn't built (dist/<pack>/<character>-<card id>.ans) is no slot, and pulls resolving to it
        // are hidden like retired ones; building it brings them back (derived at load, pulls.log untouched)
        let d = tmp("muted");
        std::fs::create_dir_all(d.join("packs/p")).unwrap();
        std::fs::create_dir_all(d.join("dist/p")).unwrap();
        std::fs::write(
            d.join("packs/p/pack.json"),
            r#"{ "id": "p",
                 "tiers": [ { "id": "common", "label": "common", "weight": 50000, "skins": {} },
                            { "id": "rare-holo-v", "label": "rare holo V", "family": "holo", "weight": 900, "skins": {} },
                            { "id": "rare-holo-vmax", "label": "rare holo VMAX", "family": "holo", "weight": 500, "skins": {} } ],
                 "cards": { "base1-44": { "character": "bulbasaur", "tier": "common", "name": "Bulbasaur" },
                            "swsh7-40": { "character": "glaceon", "tier": "rare-holo-v", "name": "Glaceon V" },
                            "swsh7-174": { "character": "glaceon", "tier": "rare-holo-v", "name": "Glaceon V" },
                            "swsh7-41": { "character": "glaceon", "tier": "rare-holo-vmax", "name": "Glaceon VMAX" } },
                 "retired": { "bulbasaur/common": "base1-44" } }"#,
        )
        .unwrap();
        for f in ["glaceon-swsh7-40", "glaceon-swsh7-174", "glaceon-swsh7-41"] {
            std::fs::write(d.join(format!("dist/p/{f}.ans")), "x").unwrap();
        }
        let log = || {
            vec![
                pull(100, "bulbasaur", "common", "common", false),   // an old common -> base1-44 (not built)
                pull(200, "bulbasaur", "common", "base1-44", false), // names the unbuilt card itself
                pull(300, "glaceon", "rare-holo-v", "swsh7-40", false),
                pull(400, "glaceon", "rare-holo-v", "swsh7-174", true),
                pull(500, "glaceon", "rare-holo-vmax", "swsh7-41", false),
            ]
        };
        let p = Pack::load(&d, "p").unwrap();
        assert!(card_built(&p.dist, "glaceon", "swsh7-40") && !card_built(&p.dist, "bulbasaur", "base1-44"));
        assert_eq!(p.chars, vec!["glaceon".to_string()], "a character with no built card is not in the binder");
        assert_eq!(p.card_list.len(), 3);
        assert_eq!(p.slot_count(), 3, "every built card is a slot; the unbuilt one is not");
        assert_eq!(p.resolve("bulbasaur", "common", "common", ""), None, "retired -> an unbuilt card: hidden");
        assert_eq!(p.resolve("bulbasaur", "common", "base1-44", ""), None, "an unbuilt card: hidden");
        let c = Collection::build(log(), vec![p]);
        assert_eq!((c.pulls.len(), c.hidden), (3, 2), "shown / hidden (the header's retired count)");
        // two Glaceon V cards of one rarity and a VMAX: three slots, not one per character
        let keys: HashSet<SlotKey> = c.by_slot.keys().copied().collect();
        assert_eq!(keys.len(), 3);
        assert!(keys.iter().all(|k| k.card != NO_CARD && k.ch == 0));
        let ids: HashSet<&str> = keys.iter().map(|k| c.packs[0].card_list[k.card as usize].id.as_str()).collect();
        assert_eq!(ids, ["swsh7-40", "swsh7-174", "swsh7-41"].into_iter().collect());
        // the per-character (dex) view still groups them: its best card is the VMAX
        let best = c.best_slot(0, 0, false).unwrap();
        assert_eq!(c.packs[0].card_list[best.card as usize].id, "swsh7-41");
        // best pulls start when the real cards went live (the first line naming a built card), unless config says
        assert_eq!(c.real_since, Some(300));
        assert_eq!(best_since(None, c.real_since), Some(300));
        assert_eq!(best_since(Some("all"), c.real_since), None);
        assert_eq!(best_since(Some("2026-09-29"), c.real_since), parse_ts("2026-09-29T00:00:00"));
        assert_eq!(best_since(Some("2026-09-29 00:40"), c.real_since), parse_ts("2026-09-29T00:40:00"));
        assert_eq!(best_since(Some("soon"), c.real_since), Some(300));
        std::fs::write(d.join("config.txt"), "pack=p
best_since = all
").unwrap();
        assert_eq!(read_config(&d, "best_since").as_deref(), Some("all"));
        assert_eq!(read_config(&d, "nope"), None);
        // unmuted: its art gets built -> the pulls come back
        std::fs::write(d.join("dist/p/bulbasaur-base1-44.ans"), "x").unwrap();
        let c = Collection::build(log(), vec![Pack::load(&d, "p").unwrap()]);
        assert_eq!((c.pulls.len(), c.hidden, c.packs[0].slot_count()), (5, 0, 4));
        assert_eq!(c.real_since, Some(200), "the line naming base1-44 counts now; the old common never does");
        let _ = std::fs::remove_dir_all(&d);
    }

    #[test]
    fn ulid_roundtrip() {
        let id = ulid_at(1_790_000_000, "ABCDEFGHJKMNPQRS");
        assert!(is_pull_id(&id));
        assert_eq!(ulid_ms(&id), Some(1_790_000_000_000));
        assert!(!is_pull_id("01M3NZHEB37XPA8TAG8Z9MZ8C3;nt"));
    }
}