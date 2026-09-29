//! App state: which pack/page/card is selected, filters, focus, and input handling.

use crate::art::ArtStore;
use crate::data::{Collection, NO_CARD, Pull, ReadCtx, SlotKey, SlotState, boot_id, load_packs, mark_viewed, now_local, now_utc, read_pulls, read_viewed};
use crate::query;
use crossterm::event::{Event, KeyCode, KeyEvent, KeyEventKind, KeyModifiers, MouseButton, MouseEvent, MouseEventKind};
use ratatui::layout::{Position, Rect};
use serde_json::Value;
use std::cell::RefCell;
use std::collections::{HashMap, HashSet};
use std::path::PathBuf;
use std::rc::Rc;
use std::time::{Instant, SystemTime};

pub const PER_PAGE: usize = 9;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Focus {
    Binder,
    Card,
    Stats,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug, Hash)]
pub enum View {
    /// Every card (real-card packs: one slot per card, set by set in printed-number order; others: every character x
    /// every tier, tier by tier): the full set, the checklist.
    Set,
    /// One slot per character showing its best card (the 905-mon pokedex).
    Dex,
}

/// `o` / `m`: every slot, the caught ones, or the ones not caught yet (empty or seen).
#[derive(Clone, Copy, PartialEq, Eq, Debug, Hash)]
pub enum Own {
    All,
    Caught,
    Missing,
}

/// A clickable tab on the binder's top border.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Tab {
    Pack(usize),
    Set,
}

#[derive(Default)]
pub struct Hits {
    pub slots: Vec<(Rect, usize)>,
    pub tabs: Vec<(i32, i32, i32, Tab)>, // x0, x1, y, tab
    pub best: Vec<(Rect, usize)>,        // pull index
    pub binder: Rect,
    pub card: Rect,
    pub stats: Rect,
    pub prev_page: Option<Rect>,
    pub next_page: Option<Rect>,
    /// the big card's rect (animated region)
    pub card_art: Rect,
    /// the art box the big card was fitted to (reused by animation frames)
    pub card_fit: (usize, usize),
    /// the text half (v) and how many rows of it are hidden (scrollable)
    pub text: Rect,
    pub text_more: usize,
    /// the set picker: its box and its rows (row index into App::set_rows)
    pub picker: Rect,
    pub picker_rows: Vec<(Rect, usize)>,
    /// the help overlay and how many rows it can scroll
    pub help: Rect,
    pub help_more: usize,
}

/// Where the binder opens: the last card you caught (default; never a seen one), a pull id (--pull, the card's link)
/// or a card (--card): those two land on their slot even when it is only seen (it shows its silhouette).
#[derive(Clone, Debug, PartialEq)]
pub enum Start {
    Latest,
    Pull(String),
    Card(String),
}

#[derive(Clone)]
pub struct Opts {
    pub root: PathBuf,
    pub log: PathBuf,
    /// viewed.txt (the ids whose NEW sticker is cleared)
    pub viewed: PathBuf,
    pub demo_pending: usize,
    pub start: Start,
    /// never write viewed.txt (snapshots, bench, selftest)
    pub readonly: bool,
    /// start with this search (--search) / on this set's checklist (--set: an id or a name, fuzzy)
    pub search: String,
    pub set: String,
}

/// The set picker (`S`): a filter typed into it and the highlighted row.
#[derive(Clone, Default)]
pub struct Picker {
    pub filter: String,
    pub sel: usize,
}

/// A row of the set picker: every set (ix 0) or pack.sets[ix - 1], with its completion.
#[derive(Clone, Debug)]
pub struct SetRow {
    pub ix: usize,
    pub id: String,
    pub name: String,
    pub done: Completion,
    /// with a search on: the matching cards in this set (rows without any are left out)
    pub hits: Option<usize>,
}

/// Where you were when a search started (`/`): Esc, or clearing the search, goes back there.
#[derive(Clone, Debug)]
pub struct Before {
    pack: usize,
    sel: usize,
    set: usize,
    view: View,
    own: Own,
    focus: Option<SlotKey>,
    hist: Option<(SlotKey, usize)>,
}

/// The matching cards per pack (all its sets) and per set of the current pack, for the tabs and the set picker.
#[derive(Clone, Debug, Default)]
pub struct SearchCounts {
    pub packs: Vec<usize>,
    /// index 0: every set; i + 1: pack.sets[i]
    pub sets: Vec<usize>,
}

/// How long an opened search result glows on its real page.
pub const FLASH_SECS: f32 = 1.6;

/// Completion of a checklist: caught, seen (pulled, never earned: not counted as done), total.
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Completion {
    pub caught: usize,
    pub seen: usize,
    pub total: usize,
}

impl Completion {
    pub fn frac(&self) -> f32 {
        self.caught as f32 / self.total.max(1) as f32
    }
}

/// One row of the tiers panel: a rarity, its cards caught / seen / in the checklist, and its (caught) pulls.
#[derive(Clone, Debug)]
pub struct TierRow {
    pub tier: usize,
    pub caught: usize,
    pub seen: usize,
    pub of: usize,
    pub pulls: usize,
}

/// The header's totals (docs/BINDER_SPEC.md): everything counts caught pulls only (pulls, cards caught, foils,
/// shinies, the last pull, streak, drought); `seen` is the slots seen but not caught.
#[derive(Clone, Default)]
pub struct Stats {
    pub total: usize,
    pub foils: usize,
    pub shinies: usize,
    pub unique: usize,
    pub seen: usize,
    pub last: Option<usize>,
    pub streak: i64,
    pub drought: usize,
    pub first_ts: Option<i64>,
}

/// Per-collection results that every frame needs and that only change when pulls.log is reloaded (P-01).
#[derive(Default)]
struct Memo {
    ver: u64,
    best: Option<Rc<Vec<(usize, f64)>>>,
    stats: Option<(i64, Rc<Stats>)>,
    done: HashMap<(usize, usize, bool, bool), Completion>,
    tiers: HashMap<(usize, usize, bool), Rc<Vec<TierRow>>>,
    /// each slot's tags, prepared for the search (query::Hay): built on first use, so a keystroke only matches
    hay: HashMap<SlotKey, Rc<query::Hay>>,
    counts: Option<((String, usize, Own, bool), Rc<SearchCounts>)>,
}

#[derive(Clone, PartialEq)]
struct SlotsKey {
    ver: u64,
    pack: usize,
    view: View,
    shiny: bool,
    own: Own,
    search: String,
    set: usize,
    focus: Option<SlotKey>,
}

pub struct App {
    pub opts: Opts,
    pub coll: Collection,
    pub art: ArtStore,
    pub theme: usize,
    pub pack: usize,
    pub views: Vec<View>,
    pub sel: Vec<usize>,
    pub shiny_only: bool,
    pub own: Own,
    /// `/`: free text and tag filters (query.rs); the cursor is a char index into it
    pub search: String,
    pub searching: bool,
    pub cursor: usize,
    /// per pack: 0 = every set, i + 1 = pack.sets[i] (the set's checklist)
    pub set_sel: Vec<usize>,
    /// `S`: the set picker, when open
    pub picker: Option<Picker>,
    /// where you were before the search (Esc goes back)
    pub before: Option<Before>,
    /// a search result just opened on its real page: it glows for FLASH_SECS
    pub flash: Option<(SlotKey, Instant)>,
    /// `#`: the jump-to-number prompt, when open
    pub number: Option<String>,
    /// per pack, dex view: the card a character's slot shows when you jumped to it (--card, --pull, the newest pull,
    /// a best pull), instead of its best one: landing is always on the exact card
    pub dex_focus: Vec<Option<SlotKey>>,
    pub focus: Focus,
    pub help: bool,
    pub help_scroll: usize,
    /// the card panel's history cursor: which pull of which slot (None: the newest pull of whatever is selected)
    pub hist: Option<(SlotKey, usize)>,
    pub best_sel: usize,
    /// best pulls start here (config.txt `best_since`, default: when the real cards went live); None = every pull
    pub best_since: Option<i64>,
    pub now: i64,
    pub anim_t0: Instant,
    /// Fixed shimmer phase (snapshots); None = real time.
    pub phase_override: Option<f32>,
    pub hits: Hits,
    pub quit: bool,
    pub log_mtime: Option<SystemTime>,
    last_poll: Instant,
    /// bumped whenever the collection is rebuilt (pulls.log reloaded): keys every cache
    pub ver: u64,
    slots_key: Option<SlotsKey>,
    slots: Vec<SlotKey>,
    memo: RefCell<Memo>,
    /// Set when anything but the animation changed: the next draw repaints everything.
    pub dirty: bool,
    pub compact_right: Focus,
    /// `v`: the card's text half (docs/CARD_FORMAT.md) stacked under the art, and how far it is scrolled
    pub show_text: bool,
    pub text_scroll: usize,
    text_for: Option<SlotKey>,
    text_cache: HashMap<PathBuf, Option<Rc<Value>>>,
    viewed: HashSet<String>,
    /// the slot whose NEW pulls were last shown in the card panel (they lose the sticker once you move on), and those
    /// pulls' ids (a reload keeps their sticker until then)
    seen_slot: Option<SlotKey>,
    sticky: HashSet<String>,
    /// a one-line message (an unknown --set, a pull that isn't in the binder, ...), cleared by the next key
    pub notice: Option<String>,
}

fn mtime(p: &PathBuf) -> Option<SystemTime> {
    std::fs::metadata(p).and_then(|m| m.modified()).ok()
}

impl App {
    fn load_pulls(opts: &Opts, viewed: &HashSet<String>) -> Vec<Pull> {
        read_pulls(&opts.log, opts.demo_pending, &ReadCtx { now_utc: now_utc(), boot: boot_id(), viewed })
    }

    pub fn new(opts: Opts, theme: usize) -> App {
        let viewed = read_viewed(&opts.viewed);
        let pulls = Self::load_pulls(&opts, &viewed);
        let packs = load_packs(&opts.root, &pulls);
        let coll = Collection::build(pulls, packs);
        let views = coll.packs.iter().map(|p| if p.is_big() { View::Dex } else { View::Set }).collect();
        let n = coll.packs.len();
        let mut app = App {
            log_mtime: mtime(&opts.log),
            opts,
            coll,
            art: ArtStore::default(),
            theme,
            pack: 0,
            views,
            sel: vec![0; n],
            shiny_only: false,
            own: Own::All,
            search: String::new(),
            searching: false,
            cursor: 0,
            set_sel: vec![0; n],
            picker: None,
            before: None,
            flash: None,
            number: None,
            dex_focus: vec![None; n],
            focus: Focus::Binder,
            help: false,
            help_scroll: 0,
            hist: None,
            best_sel: 0,
            best_since: None,
            now: now_local(),
            anim_t0: Instant::now(),
            phase_override: None,
            hits: Hits::default(),
            quit: false,
            last_poll: Instant::now(),
            ver: 0,
            slots_key: None,
            slots: Vec::new(),
            memo: RefCell::new(Memo::default()),
            dirty: true,
            compact_right: Focus::Card,
            show_text: false,
            text_scroll: 0,
            text_for: None,
            text_cache: HashMap::new(),
            viewed,
            seen_slot: None,
            sticky: HashSet::new(),
            notice: None,
        };
        app.best_since = app.best_since_setting();
        if app.coll.packs.is_empty() {
            return app;
        }
        // --set: that set's checklist (in its pack); fuzzy (set_score), a clear notice when it names none
        let set = app.opts.set.trim().to_string();
        if !set.is_empty() {
            app.open_set_arg(&set);
        }
        app.search = app.opts.search.clone();
        app.cursor = app.search.chars().count();
        // where to land: the pull / card asked for (it clears filters that hide it; a seen one shows its silhouette),
        // else the last caught card that the set and search show, else the last caught card (never a seen one)
        let start = app.opts.start.clone();
        let landed = match &start {
            Start::Latest => false,
            Start::Pull(id) => app.select_pull(id) || {
                app.notice = Some(format!("pull {id} isn't in the binder (hidden or not in pulls.log): showing the last card you caught"));
                false
            },
            Start::Card(c) => app.select_card(c) || {
                app.notice = Some(format!("no card {c}: showing the last card you caught"));
                false
            },
        };
        if !landed {
            let filtered = !set.is_empty() || !app.search.is_empty();
            if !filtered || !app.select_latest_visible() {
                if !filtered {
                    app.select_latest();
                }
            }
        }
        app
    }

    /// --set <query>: the best-matching set across the packs (query::set_score), its checklist.
    fn open_set_arg(&mut self, q: &str) {
        let all: Vec<(usize, usize, i32)> = self
            .coll
            .packs
            .iter()
            .enumerate()
            .flat_map(|(pi, p)| p.sets.iter().enumerate().map(move |(si, s)| (pi, si, query::set_score(s, q))))
            .filter(|x| x.2 > 0)
            .collect();
        let top = all.iter().map(|x| x.2).max().unwrap_or(0);
        let best: Vec<&(usize, usize, i32)> = all.iter().filter(|x| x.2 == top).collect();
        let Some(&&(pi, si, _)) = best.first() else {
            let names: Vec<String> = self.coll.packs.iter().flat_map(|p| p.sets.iter().map(|s| format!("{} ({})", s.name, s.id))).collect();
            self.notice = Some(if names.is_empty() {
                format!("no set matches “{q}”: no pack here has sets")
            } else {
                format!("no set matches “{q}” · sets: {} · S picks one", names.join(", "))
            });
            return;
        };
        self.pack = pi;
        self.set_sel[pi] = si + 1;
        self.views[pi] = View::Set;
        if best.len() > 1 {
            let others: Vec<String> = best[1..].iter().map(|&&(p, s, _)| self.coll.packs[p].sets[s].name.clone()).collect();
            self.notice = Some(format!("“{q}” also matches {} · S picks another", others.join(", ")));
        }
    }

    /// Open on a pull by id (the card's pokeshell://binder?pull=<id> link). False if it isn't in the binder.
    pub fn select_pull(&mut self, id: &str) -> bool {
        let hit = (0..self.coll.pulls.len()).rev().find(|&i| self.coll.pulls[i].id.eq_ignore_ascii_case(id));
        match hit.and_then(|i| self.coll.slot_of[i].map(|k| (i, k))) {
            Some((i, k)) => {
                self.jump_to(k, Some(i));
                true
            }
            None => false,
        }
    }

    /// Open on a card: "pack/<card id>" or "pack/character/tier" (tier by id or label; none: its lowest tier with a
    /// card). A character with several cards in that tier: the one pulled last, else the first in checklist order.
    pub fn select_card(&mut self, spec: &str) -> bool {
        let parts: Vec<&str> = spec.split('/').map(|s| s.trim()).collect();
        let (pack, ch, tier) = match parts.as_slice() {
            [p, c, t] => (*p, *c, *t),
            [p, c] => (*p, *c, ""),
            _ => return false,
        };
        let Some(pi) = self.coll.packs.iter().position(|p| p.id.eq_ignore_ascii_case(pack)) else { return false };
        let pk = &self.coll.packs[pi];
        let k = if let Some(ix) = pk.card_list.iter().position(|c| c.id.eq_ignore_ascii_case(ch)) {
            pk.key_of(pi, ix)
        } else {
            let Some(&ci) = pk.char_ix.get(ch) else { return false };
            let ti = if tier.is_empty() {
                (0..pk.tiers.len()).find(|&t| pk.has_slot(ci, t))
            } else {
                pk.tier_ix(tier).or_else(|| pk.tiers.iter().position(|t| t.label.eq_ignore_ascii_case(tier)))
            };
            let Some(ti) = ti else { return false };
            if pk.is_cards {
                let cards: Vec<usize> = pk.char_cards[ci].iter().copied().filter(|&i| pk.card_list[i].tier == ti).collect();
                let pulled = cards.iter().copied().filter_map(|i| self.coll.slot_pulls(pk.key_of(pi, i)).last().map(|&p| (p, i))).max();
                match pulled.map(|x| x.1).or(cards.first().copied()) {
                    Some(i) => pk.key_of(pi, i),
                    None => return false,
                }
            } else {
                SlotKey { pack: pi, ch: ci, tier: ti, card: NO_CARD }
            }
        };
        let newest = self.coll.slot_pulls(k).last().copied();
        self.jump_to(k, newest);
        true
    }

    /// The card-data JSON for a slot (cached; None when the pack has no card text for it).
    pub fn card_text(&mut self, k: SlotKey) -> Option<Rc<Value>> {
        let path = self.coll.packs[k.pack].card_file(k)?;
        self.text_cache
            .entry(path.clone())
            .or_insert_with(|| {
                let b = std::fs::read(&path).ok()?;
                let b = b.strip_prefix(b"\xef\xbb\xbf".as_slice()).unwrap_or(&b); // PowerShell writes UTF-8 with a BOM
                serde_json::from_slice::<Value>(b).ok().map(Rc::new)
            })
            .clone()
    }

    /// Record that the selected card was shown in the card panel: its NEW pulls go to viewed.txt; the sticker stays
    /// until you move on. Called after a full draw, only when the card panel was on screen (D-15).
    pub fn mark_seen(&mut self) {
        let cur = self.selected();
        if cur == self.seen_slot {
            return;
        }
        if let Some(old) = self.seen_slot {
            for i in self.coll.slot_pulls(old).to_vec() {
                self.coll.pulls[i].new = false;
            }
        }
        self.sticky.clear();
        self.seen_slot = cur;
        let Some(k) = cur else { return };
        let ids: Vec<String> = self.coll.slot_pulls(k).iter().map(|&i| &self.coll.pulls[i]).filter(|p| p.new).map(|p| p.id.clone()).collect();
        let fresh: Vec<String> = ids.iter().filter(|id| !self.viewed.contains(*id)).cloned().collect();
        if !self.opts.readonly {
            mark_viewed(&self.opts.viewed, &fresh);
        }
        self.viewed.extend(fresh);
        self.sticky.extend(ids);
    }

    /// Start on the card you caught most recently (the exact card, in any view). Never a seen card: a pull that is
    /// pending or expired isn't in the binder yet. Nothing caught: the selection stays where it is.
    pub fn select_latest(&mut self) {
        if let Some((i, k)) = self.coll.last_caught() {
            self.jump_to(k, Some(i));
        }
    }

    /// Land on the last caught card the current filters (set, search, caught/missing) show, without clearing them.
    /// False if they show none (the selection stays on the first slot).
    pub fn select_latest_visible(&mut self) -> bool {
        let terms = self.terms();
        let hit = (0..self.coll.pulls.len())
            .rev()
            .filter(|&i| self.coll.pulls[i].status.caught())
            .find_map(|i| self.coll.slot_of[i].filter(|k| self.visible_with(&terms, *k)).map(|k| (i, k)));
        match hit {
            Some((i, k)) => {
                self.select_key(k);
                self.hist = self.coll.slot_pulls(k).iter().position(|&x| x == i).map(|h| (k, h));
                true
            }
            None => {
                self.sel[self.pack] = 0;
                false
            }
        }
    }

    /// Re-read pulls.log if it changed (checked every couple of seconds and on focus). The selected card, the pull
    /// the card panel shows, and the NEW sticker of the card on screen survive the reload (D-10).
    pub fn reload_if_changed(&mut self) -> bool {
        let m = mtime(&self.opts.log);
        if m == self.log_mtime {
            return false;
        }
        self.log_mtime = m;
        let cur = self.selected();
        let shown = cur.and_then(|k| self.shown_pull(k).1.map(|i| self.coll.pulls[i].id.clone()));
        let pulls = Self::load_pulls(&self.opts, &self.viewed);
        let packs = std::mem::take(&mut self.coll.packs);
        self.coll = Collection::build(pulls, packs);
        for p in self.coll.pulls.iter_mut() {
            if !p.id.is_empty() && self.sticky.contains(&p.id) {
                p.new = true;
            }
        }
        self.ver += 1;
        self.best_since = self.best_since_setting();
        if let Some(k) = cur {
            self.select_key(k);
            let list = self.coll.slot_pulls(k).to_vec();
            self.hist = shown.filter(|s| !s.is_empty()).and_then(|id| list.iter().position(|&i| self.coll.pulls[i].id == id)).map(|h| (k, h));
        }
        self.dirty = true;
        true
    }

    /// Poll pulls.log's mtime at most every 2 s (the event loop calls this on every wake-up).
    pub fn poll_reload(&mut self) -> bool {
        if self.last_poll.elapsed().as_millis() < 2000 {
            return false;
        }
        self.last_poll = Instant::now();
        self.reload_if_changed()
    }

    // ------------------------------------------------------------ slots

    /// The slots of the current pack after filters (cached).
    pub fn slots(&mut self) -> &[SlotKey] {
        if self.coll.packs.is_empty() {
            self.slots.clear();
            return &self.slots;
        }
        let key = SlotsKey {
            ver: self.ver,
            pack: self.pack,
            view: self.views[self.pack],
            shiny: self.shiny_only,
            own: self.own,
            search: self.search.clone(),
            set: self.set_sel[self.pack],
            focus: self.dex_focus[self.pack],
        };
        if self.slots_key.as_ref() != Some(&key) {
            self.slots = self.compute_slots();
            self.slots_key = Some(key);
        }
        &self.slots
    }

    /// The set the current pack's binder is showing (None: every set).
    pub fn current_set(&self) -> Option<&crate::data::SetDef> {
        let s = *self.set_sel.get(self.pack)?;
        if s == 0 { None } else { self.coll.packs.get(self.pack)?.sets.get(s - 1) }
    }

    /// Is a card in the selected set (always, with every set selected or in a pack without sets)?
    fn in_set(&self, k: SlotKey) -> bool {
        let s = self.set_sel.get(k.pack).copied().unwrap_or(0);
        s == 0 || self.coll.packs[k.pack].set_of(k.card) == Some(s - 1)
    }

    /// The search terms, with `set:` resolved against the current pack's sets.
    pub fn terms(&self) -> Vec<query::Term> {
        let mut t = query::parse(&self.search);
        if let Some(p) = self.coll.packs.get(self.pack) {
            query::resolve_terms(&mut t, &p.sets);
        }
        t
    }

    /// The state words of a slot for the search (query.rs).
    pub fn slot_flags(&self, k: SlotKey) -> query::Flags {
        let st = self.coll.slot_state(k, false);
        query::Flags {
            shiny: self.coll.caught_pulls(k).any(|i| self.coll.pulls[i].shiny),
            foil: self.coll.packs[k.pack].foil_tier(k.tier),
            new: self.coll.slot_new(k, false),
            seen: st == SlotState::Seen,
            caught: st == SlotState::Caught,
        }
    }

    fn own_ok(&self, k: SlotKey) -> bool {
        match self.own {
            Own::All => true,
            Own::Caught => self.coll.slot_state(k, self.shiny_only) == SlotState::Caught,
            Own::Missing => self.coll.slot_state(k, self.shiny_only) != SlotState::Caught,
        }
    }

    /// Would this card be in the binder with the current set, search and caught/missing filters (in the dex view: if its
    /// character's slot showed it)?
    pub fn visible(&self, k: SlotKey) -> bool {
        self.visible_with(&self.terms(), k)
    }

    fn visible_with(&self, terms: &[query::Term], k: SlotKey) -> bool {
        k.pack == self.pack && self.in_set(k) && self.own_ok(k) && self.term_ok(terms, k)
    }

    /// A slot's tags, prepared for matching (cached per collection version).
    fn hay(&self, k: SlotKey) -> Rc<query::Hay> {
        if let Some(h) = self.memo().hay.get(&k) {
            return h.clone();
        }
        let h = Rc::new(query::prepare(&self.coll.packs[k.pack].slot_tags(k)));
        self.memo().hay.insert(k, h.clone());
        h
    }

    /// Does a slot pass the search terms? (true without any)
    fn term_ok(&self, terms: &[query::Term], k: SlotKey) -> bool {
        if terms.is_empty() {
            return true;
        }
        let states = terms.iter().any(|t| t.key.is_none() && query::STATES.contains(&t.value.as_str()));
        let flags = if states { self.slot_flags(k) } else { query::Flags::default() };
        query::matches_hay(terms, &self.hay(k), flags)
    }

    /// With a search on: how many cards match in each pack (every set) and in each set of the current pack (with the
    /// caught / missing / shiny filters). None without a search.
    pub fn search_counts(&self) -> Option<Rc<SearchCounts>> {
        if query::parse(&self.search).is_empty() || self.coll.packs.is_empty() {
            return None;
        }
        let key = (self.search.clone(), self.pack, self.own, self.shiny_only);
        if let Some((k, c)) = &self.memo().counts {
            if *k == key {
                return Some(c.clone());
            }
        }
        let mut out = SearchCounts { packs: vec![0; self.coll.packs.len()], sets: vec![] };
        for (pi, p) in self.coll.packs.iter().enumerate() {
            let mut terms = query::parse(&self.search);
            query::resolve_terms(&mut terms, &p.sets);
            let keys: Vec<SlotKey> = if p.is_cards {
                (0..p.card_list.len()).map(|i| p.key_of(pi, i)).collect()
            } else {
                (0..p.tiers.len()).flat_map(|t| (0..p.chars.len()).map(move |c| SlotKey::legacy(pi, c, t))).collect()
            };
            if pi == self.pack {
                out.sets = vec![0; p.sets.len() + 1];
            }
            for k in keys {
                if self.own_ok(k) && self.term_ok(&terms, k) {
                    out.packs[pi] += 1;
                    if pi == self.pack {
                        out.sets[0] += 1;
                        if let Some(si) = p.set_of(k.card) {
                            out.sets[si + 1] += 1;
                        }
                    }
                }
            }
        }
        let c = Rc::new(out);
        self.memo().counts = Some((key, c.clone()));
        Some(c)
    }

    fn here(&self) -> Before {
        let pi = self.pack;
        Before { pack: pi, sel: self.sel[pi], set: self.set_sel[pi], view: self.views[pi], own: self.own, focus: self.dex_focus[pi], hist: self.hist }
    }

    /// Back to where you were before the search (the search itself is left as it is).
    fn go_back(&mut self, b: &Before) {
        self.pack = b.pack;
        self.set_sel[b.pack] = b.set;
        self.views[b.pack] = b.view;
        self.own = b.own;
        self.dex_focus[b.pack] = b.focus;
        self.sel[b.pack] = b.sel;
        self.hist = b.hist;
        self.dirty = true;
    }

    /// Esc on a search: clear it and go back to where you were before it.
    fn clear_search(&mut self) {
        self.searching = false;
        self.cursor = 0;
        match self.before.take() {
            Some(b) => {
                self.search.clear();
                self.go_back(&b);
            }
            None => self.keeping_selection(|a| a.search.clear()),
        }
    }

    /// Enter (or a click on the selected card) during a search: clear it and show the card on its real binder page,
    /// the unfiltered one with its neighbours, selected and glowing for a moment.
    pub fn open_result(&mut self) {
        let Some(k) = self.selected() else {
            self.searching = false;
            return;
        };
        self.search.clear();
        self.cursor = 0;
        self.searching = false;
        self.before = None;
        self.own = Own::All;
        self.jump_to(k, None);
        self.flash = Some((k, Instant::now()));
        self.focus = Focus::Binder;
        self.dirty = true;
    }

    /// The glow of an opened result (1 fading to 0), if this slot has it.
    pub fn flash_level(&self, k: SlotKey) -> f32 {
        match self.flash {
            Some((f, t0)) if f == k => (1.0 - t0.elapsed().as_secs_f32() / FLASH_SECS).max(0.0),
            _ => 0.0,
        }
    }

    /// The event loop's tick: true while the glow needs frames (and once more when it ends).
    pub fn flash_tick(&mut self) -> bool {
        match self.flash {
            Some((_, t0)) if t0.elapsed().as_secs_f32() >= FLASH_SECS => {
                self.flash = None;
                true
            }
            Some(_) => true,
            None => false,
        }
    }

    fn compute_slots(&self) -> Vec<SlotKey> {
        let pi = self.pack;
        let Some(p) = self.coll.packs.get(pi) else { return vec![] };
        let terms = self.terms();
        let shiny = self.shiny_only;
        let term_ok = |k: SlotKey| self.term_ok(&terms, k);
        let st = |k: SlotKey| self.coll.slot_state(k, shiny);
        let mut out = Vec::new();
        match self.views[pi] {
            // real cards: one slot per card, set by set in checklist (printed number) order; a set picked with `S`
            // is that set's whole checklist, pulled or not
            View::Set if p.is_cards => {
                for &i in &p.checklist {
                    let k = p.key_of(pi, i);
                    if self.in_set(k) && self.own_ok(k) && term_ok(k) {
                        out.push(k);
                    }
                }
            }
            View::Set => {
                for tier in 0..p.tiers.len() {
                    for ch in 0..p.chars.len() {
                        let k = SlotKey::legacy(pi, ch, tier);
                        if self.own_ok(k) && term_ok(k) {
                            out.push(k);
                        }
                    }
                }
            }
            // one slot per character. A character is in if any of its cards (in the selected set) passes the search
            // and the caught/missing filter, and its slot shows the card you jumped to (dex_focus) if that one
            // passes, else its best caught card, else a seen one, else its first card
            View::Dex => {
                let focus = self.dex_focus[pi].filter(|k| k.pack == pi);
                for ch in 0..p.chars.len() {
                    let cands: Vec<SlotKey> = if p.is_cards {
                        p.char_cards[ch].iter().map(|&i| p.key_of(pi, i)).filter(|&k| self.in_set(k)).collect()
                    } else {
                        (0..p.tiers.len()).map(|t| SlotKey::legacy(pi, ch, t)).collect()
                    };
                    if cands.is_empty() {
                        continue;
                    }
                    let matching: Vec<SlotKey> = cands.iter().copied().filter(|&k| term_ok(k)).collect();
                    let pool: Vec<SlotKey> = match self.own {
                        Own::All => matching,
                        Own::Caught => matching.into_iter().filter(|&k| st(k) == SlotState::Caught).collect(),
                        // missing: characters with none of these cards caught
                        Own::Missing if matching.iter().any(|&k| st(k) == SlotState::Caught) => continue,
                        Own::Missing => matching,
                    };
                    if pool.is_empty() {
                        continue;
                    }
                    let rank = |k: &SlotKey| (k.tier, self.coll.slot_pulls(*k).last().copied());
                    let pick = focus
                        .filter(|f| f.ch == ch && pool.contains(f))
                        .or_else(|| pool.iter().copied().filter(|&k| st(k) == SlotState::Caught).max_by_key(rank))
                        .or_else(|| pool.iter().copied().filter(|&k| st(k) == SlotState::Seen).max_by_key(rank))
                        .unwrap_or(pool[0]);
                    out.push(pick);
                }
            }
        }
        out
    }

    pub fn sel_ix(&mut self) -> usize {
        if self.coll.packs.is_empty() {
            return 0;
        }
        let n = self.slots().len();
        let s = &mut self.sel[self.pack];
        if n == 0 {
            *s = 0;
        } else if *s >= n {
            *s = n - 1;
        }
        *s
    }

    pub fn selected(&mut self) -> Option<SlotKey> {
        let i = self.sel_ix();
        self.slots().get(i).copied()
    }

    pub fn page(&mut self) -> usize {
        self.sel_ix() / PER_PAGE
    }

    pub fn pages(&mut self) -> usize {
        self.slots().len().div_ceil(PER_PAGE).max(1)
    }

    /// Select a card if the current filters show it (in the dex view its character's slot is made to show it).
    /// False if it is filtered out.
    fn select_key(&mut self, k: SlotKey) -> bool {
        if k.pack >= self.coll.packs.len() {
            return false;
        }
        self.pack = k.pack;
        if self.views[k.pack] == View::Dex {
            self.dex_focus[k.pack] = Some(k);
        }
        match self.slots().iter().position(|s| *s == k) {
            Some(p) => {
                self.sel[k.pack] = p;
                self.dirty = true;
                true
            }
            None => false,
        }
    }

    /// Select exactly this card, clearing the filters that hide it, and show `pull` in the card panel.
    pub fn jump_to(&mut self, k: SlotKey, pull: Option<usize>) {
        if !self.select_key(k) {
            // filtered out: clear what hides it and retry
            self.search.clear();
            self.cursor = 0;
            self.searching = false;
            self.own = Own::All;
            if !self.in_set(k) {
                self.set_sel[k.pack] = 0;
            }
            if self.shiny_only && !pull.is_some_and(|i| self.coll.pulls[i].shiny) {
                self.shiny_only = false;
            }
            self.select_key(k);
        }
        self.hist = pull.and_then(|pi| self.coll.slot_pulls(k).iter().position(|&x| x == pi)).map(|h| (k, h));
        self.dirty = true;
    }

    /// Run `f` (a filter or view change) and keep the selected card selected when it is still shown (K-06, D-11).
    fn keeping_selection(&mut self, f: impl FnOnce(&mut Self)) {
        let prev = self.selected();
        f(self);
        if let Some(k) = prev {
            if !self.select_key(k) && self.views[self.pack] == View::Dex {
                // the dex view shows another card of that character: stay on the character
                if let Some(p) = self.slots().iter().position(|s| s.ch == k.ch) {
                    self.sel[self.pack] = p;
                }
            }
        }
        self.dirty = true;
    }

    fn move_sel(&mut self, d: isize) {
        let n = self.slots().len() as isize;
        if n == 0 {
            return;
        }
        let s = self.sel_ix() as isize;
        self.sel[self.pack] = (s + d).clamp(0, n - 1) as usize;
    }

    fn flip(&mut self, d: isize) {
        let n = self.slots().len();
        if n == 0 {
            return;
        }
        let pages = n.div_ceil(PER_PAGE) as isize;
        let s = self.sel_ix();
        let page = (s / PER_PAGE) as isize;
        let np = (page + d).rem_euclid(pages) as usize;
        let within = s % PER_PAGE;
        self.sel[self.pack] = (np * PER_PAGE + within).min(n - 1);
    }

    fn move_grid(&mut self, dx: isize, dy: isize) {
        let n = self.slots().len();
        if n == 0 {
            return;
        }
        let pages = self.pages();
        let s = self.sel_ix();
        let (page, within) = (s / PER_PAGE, s % PER_PAGE);
        let (col, row) = ((within % 3) as isize, (within / 3) as isize);
        let (nc, nr) = (col + dx, row + dy);
        if nc < 0 {
            // off the left edge: previous page, rightmost column (one page: stay)
            if pages > 1 {
                self.flip(-1);
                let p = self.sel_ix() / PER_PAGE;
                self.sel[self.pack] = (p * PER_PAGE + row as usize * 3 + 2).min(n - 1);
            }
        } else if nc > 2 || (dx > 0 && s + 1 >= n) {
            // off the right edge (or past the last card): next page, leftmost column (one page: stay)
            if pages > 1 {
                self.flip(1);
                let p = self.sel_ix() / PER_PAGE;
                self.sel[self.pack] = (p * PER_PAGE + row as usize * 3).min(n - 1);
            }
        } else if nr < 0 {
            // above the top row: the previous page's bottom row; the first row of the first page stays (D-13)
            if s >= 3 {
                self.move_sel(-3);
            }
        } else if nr > 2 {
            // below the last row: next page, same column
            if pages > 1 {
                self.flip(1);
                let p = self.sel_ix() / PER_PAGE;
                self.sel[self.pack] = (p * PER_PAGE + col as usize).min(n - 1);
            }
        } else {
            let t = page * PER_PAGE + nr as usize * 3 + nc as usize;
            if t < n {
                self.sel[self.pack] = t;
            } else if dy > 0 && pages > 1 {
                self.flip(1);
                let p = self.sel_ix() / PER_PAGE;
                self.sel[self.pack] = (p * PER_PAGE + col as usize).min(n - 1);
            }
        }
    }

    pub fn set_pack(&mut self, p: usize) {
        if p < self.coll.packs.len() && p != self.pack {
            self.pack = p;
            self.dirty = true;
        }
    }

    /// config.txt (next to pulls.log) `best_since`, else when the real cards went live
    fn best_since_setting(&self) -> Option<i64> {
        let dir = self.opts.log.parent().map(|d| d.to_path_buf()).unwrap_or_default();
        crate::data::best_since(crate::data::read_config(&dir, "best_since").as_deref(), self.coll.real_since)
    }

    // ------------------------------------------------------------ derived (cached per collection version)

    fn memo(&self) -> std::cell::RefMut<'_, Memo> {
        let mut m = self.memo.borrow_mut();
        if m.ver != self.ver {
            *m = Memo { ver: self.ver, ..Memo::default() };
        }
        m
    }

    /// Ranked best pulls across all packs, since best_since: earned foils and shinies, rarest odds first.
    pub fn best_pulls(&self) -> Rc<Vec<(usize, f64)>> {
        if let Some(b) = &self.memo().best {
            return b.clone();
        }
        let mut v: Vec<(usize, f64)> = (0..self.coll.pulls.len())
            .filter_map(|i| {
                let k = self.coll.slot_of[i]?;
                let p = &self.coll.pulls[i];
                if !p.status.caught() || self.best_since.is_some_and(|t| p.ts < t) {
                    return None;
                }
                if !self.coll.packs[k.pack].foil_tier(k.tier) && !p.shiny {
                    return None;
                }
                Some((i, self.coll.packs[k.pack].card_p(k.tier, p.shiny)))
            })
            .collect();
        v.sort_by(|a, b| a.1.total_cmp(&b.1).then(b.0.cmp(&a.0)));
        let v = Rc::new(v);
        self.memo().best = Some(v.clone());
        v
    }

    /// The header's totals (cached per collection and minute).
    pub fn stats(&self) -> Rc<Stats> {
        let minute = self.now.div_euclid(60);
        if let Some((m, s)) = &self.memo().stats {
            if *m == minute {
                return s.clone();
            }
        }
        let c = &self.coll;
        let foil = |i: usize| c.slot_of[i].is_some_and(|k| c.packs[k.pack].foil_tier(k.tier));
        // caught pulls only (a seen card isn't in the binder yet)
        let got: Vec<usize> = (0..c.pulls.len()).filter(|&i| c.pulls[i].status.caught()).collect();
        let (mut unique, mut seen) = (0, 0);
        for k in c.by_slot.keys() {
            match c.slot_state(*k, false) {
                SlotState::Caught => unique += 1,
                SlotState::Seen => seen += 1,
                SlotState::Empty => {}
            }
        }
        let days: std::collections::BTreeSet<i64> = got.iter().map(|&i| c.pulls[i].ts.div_euclid(86400)).collect();
        let today = self.now.div_euclid(86400);
        let mut d = if days.contains(&today) { today } else { today - 1 };
        let mut streak = 0;
        while days.contains(&d) {
            streak += 1;
            d -= 1;
        }
        let s = Rc::new(Stats {
            total: got.len(),
            foils: got.iter().filter(|&&i| foil(i)).count(),
            shinies: got.iter().filter(|&&i| c.pulls[i].shiny).count(),
            unique,
            seen,
            last: got.last().copied(),
            streak,
            drought: got.iter().rev().take_while(|&&i| !foil(i)).count(),
            first_ts: got.iter().map(|&i| c.pulls[i].ts).min(),
        });
        self.memo().stats = Some((minute, s.clone()));
        s
    }

    /// Completion of a pack's checklist: `set` 0 = every set, else pack.sets[set - 1]; `dex`: characters caught
    /// instead of cards (slots). Caught only: a seen card is counted apart (S-06).
    pub fn completion(&self, pi: usize, set: usize, shiny: bool, dex: bool) -> Completion {
        if let Some(c) = self.memo().done.get(&(pi, set, shiny, dex)) {
            return *c;
        }
        let c = &self.coll;
        let p = &c.packs[pi];
        let in_set = |k: SlotKey| set == 0 || p.set_of(k.card) == Some(set - 1);
        let mut out = Completion::default();
        let mut add = |states: &mut dyn Iterator<Item = SlotState>| {
            let mut any = false;
            let (mut caught, mut seen) = (false, false);
            for s in states {
                any = true;
                caught |= s == SlotState::Caught;
                seen |= s == SlotState::Seen;
            }
            if any {
                out.total += 1;
                if caught {
                    out.caught += 1;
                } else if seen {
                    out.seen += 1;
                }
            }
        };
        if p.is_cards {
            if dex {
                for ch in 0..p.chars.len() {
                    add(&mut p.char_cards[ch].iter().map(|&i| p.key_of(pi, i)).filter(|&k| in_set(k)).map(|k| c.slot_state(k, shiny)));
                }
            } else {
                for &i in &p.checklist {
                    let k = p.key_of(pi, i);
                    if in_set(k) {
                        add(&mut std::iter::once(c.slot_state(k, shiny)));
                    }
                }
            }
        } else if dex {
            for ch in 0..p.chars.len() {
                add(&mut (0..p.tiers.len()).map(|t| c.slot_state(SlotKey::legacy(pi, ch, t), shiny)));
            }
        } else {
            for t in 0..p.tiers.len() {
                for ch in 0..p.chars.len() {
                    add(&mut std::iter::once(c.slot_state(SlotKey::legacy(pi, ch, t), shiny)));
                }
            }
        }
        self.memo().done.insert((pi, set, shiny, dex), out);
        out
    }

    /// A pack's completion as its header meter shows it: cards (real-card packs), characters (big packs), slots.
    pub fn pack_completion(&self, pi: usize) -> Completion {
        self.completion(pi, 0, false, self.coll.packs[pi].is_big())
    }

    /// The binder's completion line: the view and set on screen (dex: characters), shiny-only aware.
    pub fn view_completion(&self) -> Completion {
        let pi = self.pack;
        self.completion(pi, self.set_sel[pi], self.shiny_only, self.views[pi] == View::Dex)
    }

    /// The tiers panel: the rarities of the selected set (or the pack), each caught / of, and its pulls (S-08).
    pub fn tier_rows(&self) -> Rc<Vec<TierRow>> {
        let (pi, set, shiny) = (self.pack, self.set_sel.get(self.pack).copied().unwrap_or(0), self.shiny_only);
        if let Some(r) = self.memo().tiers.get(&(pi, set, shiny)) {
            return r.clone();
        }
        let c = &self.coll;
        let Some(p) = c.packs.get(pi) else { return Rc::new(vec![]) };
        let in_set = |k: SlotKey| set == 0 || p.set_of(k.card) == Some(set - 1);
        let mut rows: Vec<TierRow> = (0..p.tiers.len()).map(|tier| TierRow { tier, caught: 0, seen: 0, of: 0, pulls: 0 }).collect();
        let mut count = |k: SlotKey| {
            let r = &mut rows[k.tier];
            r.of += 1;
            match c.slot_state(k, shiny) {
                SlotState::Caught => r.caught += 1,
                SlotState::Seen => r.seen += 1,
                SlotState::Empty => {}
            }
        };
        if p.is_cards {
            for &i in &p.checklist {
                let k = p.key_of(pi, i);
                if in_set(k) {
                    count(k);
                }
            }
        } else {
            for t in 0..p.tiers.len() {
                for ch in 0..p.chars.len() {
                    count(SlotKey::legacy(pi, ch, t));
                }
            }
        }
        for (i, k) in c.slot_of.iter().enumerate() {
            if let Some(k) = k.filter(|k| k.pack == pi && in_set(*k) && c.pulls[i].status.caught()) {
                rows[k.tier].pulls += 1;
            }
        }
        let live: HashSet<usize> = p.live_tiers().iter().copied().collect();
        let rows: Vec<TierRow> = rows.into_iter().filter(|r| if p.is_cards { r.of > 0 } else { live.contains(&r.tier) }).collect();
        let rows = Rc::new(rows);
        self.memo().tiers.insert((pi, set, shiny), rows.clone());
        rows
    }

    /// The set picker's rows: every set first, then the pack's sets, the ones you collect most first (then the
    /// biggest). With a filter typed: the sets it names (query::set_score), best first. With a search on: only the
    /// sets with matching cards, with their counts.
    pub fn set_rows(&self) -> Vec<SetRow> {
        let Some(p) = self.coll.packs.get(self.pack) else { return vec![] };
        let f = self.picker.as_ref().map(|p| p.filter.trim().to_string()).unwrap_or_default();
        let counts = self.search_counts();
        let mut rows: Vec<(i32, SetRow)> = p
            .sets
            .iter()
            .enumerate()
            .map(|(i, s)| {
                let hits = counts.as_ref().map(|c| c.sets.get(i + 1).copied().unwrap_or(0));
                (if f.is_empty() { 1 } else { query::set_score(s, &f) }, SetRow { ix: i + 1, id: s.id.clone(), name: s.name.clone(), done: self.completion(self.pack, i + 1, false, false), hits })
            })
            .filter(|r| r.0 > 0 && r.1.hits != Some(0))
            .collect();
        rows.sort_by(|a, b| b.0.cmp(&a.0).then(b.1.done.caught.cmp(&a.1.done.caught)).then(b.1.done.total.cmp(&a.1.done.total)).then(a.1.ix.cmp(&b.1.ix)));
        let mut out: Vec<SetRow> = Vec::new();
        if f.is_empty() || "all sets".starts_with(&query::fold(&f)) {
            out.push(SetRow { ix: 0, id: String::new(), name: "every set".into(), done: self.completion(self.pack, 0, false, false), hits: counts.as_ref().map(|c| c.sets[0]) });
        }
        out.extend(rows.into_iter().map(|r| r.1));
        out
    }

    /// Show a set's checklist (0: every set). A picked set is always the checklist (the card view); the selection
    /// stays on the card you are on if the set has it, else goes to the last caught card in the set, else its first card.
    pub fn choose_set(&mut self, ix: usize) {
        let pi = self.pack;
        let Some(p) = self.coll.packs.get(pi) else { return };
        if ix > p.sets.len() {
            return;
        }
        let prev = self.selected();
        self.set_sel[pi] = ix;
        if ix > 0 {
            self.views[pi] = View::Set;
        }
        self.dex_focus[pi] = None;
        self.picker = None;
        self.dirty = true;
        if prev.is_some_and(|k| self.select_key(k)) {
            return;
        }
        if !self.select_latest_visible() {
            self.sel[pi] = 0;
        }
    }

    pub fn open_picker(&mut self) {
        let Some(p) = self.coll.packs.get(self.pack) else { return };
        if p.sets.is_empty() {
            self.notice = Some(format!("{} has no sets: its binder is every character x every tier", p.name));
            return;
        }
        self.picker = Some(Picker::default());
        let cur = self.set_sel[self.pack];
        let sel = self.set_rows().iter().position(|r| r.ix == cur).unwrap_or(0);
        if let Some(pk) = self.picker.as_mut() {
            pk.sel = sel;
        }
        self.searching = false;
        self.dirty = true;
    }

    /// `#`: select the card with this printed number (numerator: "17", "TG05", "B") in the selected set (or the
    /// pack), clearing a search or filter that hides it.
    pub fn jump_number(&mut self, q: &str) {
        let pi = self.pack;
        let Some(p) = self.coll.packs.get(pi) else { return };
        let want = crate::data::numerator(q.trim().trim_start_matches('#'));
        if want.is_empty() {
            return;
        }
        if !p.is_cards {
            self.notice = Some(format!("{} has no printed numbers", p.name));
            return;
        }
        let hit = p.checklist.iter().copied().map(|i| p.key_of(pi, i)).find(|&k| self.in_set(k) && p.card_list[k.card as usize].numerator() == want);
        match hit {
            Some(k) => {
                let newest = self.coll.slot_pulls(k).last().copied();
                self.jump_to(k, newest);
            }
            None => {
                let where_ = self.current_set().map(|s| s.name.clone()).unwrap_or_else(|| p.name.clone());
                self.notice = Some(format!("no card #{} in {where_}", q.trim().trim_start_matches('#')));
            }
        }
    }

    /// Which pulls of a slot the card panel steps through (its caught ones; shiny-only: its caught shinies) and which
    /// one it shows: the history cursor if it belongs to this slot, else the newest. A seen card has none.
    pub fn shown_pull(&self, k: SlotKey) -> (Vec<usize>, Option<usize>) {
        let shiny = self.shiny_only;
        let list: Vec<usize> = self.coll.caught_pulls(k).filter(|&i| !shiny || self.coll.pulls[i].shiny).collect();
        if list.is_empty() {
            return (list, None);
        }
        let h = match self.hist {
            Some((hk, h)) if hk == k && h < list.len() => h,
            _ => list.len() - 1,
        };
        let shown = list[h];
        (list, Some(shown))
    }

    /// The history cursor's position in the shown list.
    pub fn hist_pos(&self, k: SlotKey) -> Option<(usize, usize)> {
        let (list, shown) = self.shown_pull(k);
        let i = shown?;
        Some((list.iter().position(|&x| x == i)?, list.len()))
    }

    fn step_hist(&mut self, d: isize) {
        let Some(k) = self.selected() else { return };
        let Some((h, n)) = self.hist_pos(k) else { return };
        self.hist = Some((k, (h as isize + d).clamp(0, n as isize - 1) as usize));
    }

    pub fn anim_phase(&self) -> f32 {
        if let Some(p) = self.phase_override {
            return p;
        }
        let t = self.anim_t0.elapsed().as_secs_f32();
        (t / crate::card::CYCLE_SECS).fract()
    }

    /// Should the selected card be shimmering right now (visible foil that you own)?
    pub fn animating(&mut self) -> bool {
        if self.help || self.picker.is_some() || self.hits.card_art.width == 0 {
            return false;
        }
        let Some(k) = self.selected() else { return false };
        let shiny = self.shiny_only;
        let st = self.coll.slot_state(k, shiny);
        st == SlotState::Caught && crate::card::is_foil(&self.coll.packs[k.pack], k.tier, shiny)
    }

    /// Keep the text half's scroll for the card it was scrolled on.
    pub fn text_scroll_for(&mut self, k: SlotKey) -> usize {
        if self.text_for != Some(k) {
            self.text_for = Some(k);
            self.text_scroll = 0;
        }
        self.text_scroll
    }

    // ------------------------------------------------------------ input

    pub fn on_event(&mut self, ev: Event) {
        match ev {
            Event::Key(k) if k.kind != KeyEventKind::Release => {
                self.notice = None;
                self.on_key(k)
            }
            Event::Mouse(m) => self.on_mouse(m),
            Event::Resize(..) => self.dirty = true,
            Event::FocusGained => {
                self.now = now_local();
                self.reload_if_changed();
                self.dirty = true;
            }
            _ => {}
        }
    }

    fn on_key(&mut self, k: KeyEvent) {
        self.dirty = true;
        // AltGr arrives as Ctrl+Alt: a character typed with it ([ ] / # on many layouts) is the plain character
        let altgr = k.modifiers.contains(KeyModifiers::CONTROL) && k.modifiers.contains(KeyModifiers::ALT);
        let ctrl = k.modifiers.contains(KeyModifiers::CONTROL) && !altgr;
        let alt = k.modifiers.contains(KeyModifiers::ALT) && !altgr;
        if ctrl && matches!(k.code, KeyCode::Char('c')) {
            self.quit = true;
            return;
        }
        if self.help {
            match k.code {
                KeyCode::Up | KeyCode::Char('k') => self.help_scroll = self.help_scroll.saturating_sub(1),
                KeyCode::Down | KeyCode::Char('j') => self.help_scroll += 1,
                KeyCode::PageUp => self.help_scroll = self.help_scroll.saturating_sub(10),
                KeyCode::PageDown | KeyCode::Char(' ') => self.help_scroll += 10,
                _ => self.help = false,
            }
            return;
        }
        if self.picker.is_some() {
            self.on_picker_key(k, ctrl || alt);
            return;
        }
        if let Some(q) = self.number.as_mut() {
            match k.code {
                KeyCode::Esc => self.number = None,
                KeyCode::Enter => {
                    let q = std::mem::take(q);
                    self.number = None;
                    self.jump_number(&q);
                }
                KeyCode::Backspace => {
                    if q.pop().is_none() {
                        self.number = None;
                    }
                }
                KeyCode::Char(c) if !ctrl && !alt && (c.is_ascii_alphanumeric() || c == '/') && q.len() < 12 => q.push(c),
                _ => {}
            }
            return;
        }
        if self.searching {
            self.on_search_key(k, ctrl, alt);
            return;
        }
        if ctrl || alt {
            return; // Ctrl/Alt + a letter is not the bare key (K-01)
        }
        match k.code {
            KeyCode::Char('q') => self.quit = true,
            KeyCode::Esc => {
                if !self.search.is_empty() {
                    self.clear_search();
                } else {
                    self.quit = true;
                }
            }
            KeyCode::Char('?') | KeyCode::F(1) => {
                self.help = true;
                self.help_scroll = 0;
            }
            KeyCode::Char('/') => {
                if self.search.is_empty() && !self.coll.packs.is_empty() {
                    self.before = Some(self.here());
                }
                self.searching = true;
                self.cursor = self.search.chars().count();
                self.focus = Focus::Binder;
            }
            KeyCode::Char('#') => self.number = Some(String::new()),
            KeyCode::Char('s') => self.toggle_shiny(),
            KeyCode::Char('o') => self.keeping_selection(|a| a.own = if a.own == Own::Caught { Own::All } else { Own::Caught }),
            KeyCode::Char('m') => self.keeping_selection(|a| a.own = if a.own == Own::Missing { Own::All } else { Own::Missing }),
            KeyCode::Char('v') => self.show_text = !self.show_text,
            KeyCode::Char('S') => self.open_picker(),
            KeyCode::Char('d') => {
                if self.coll.packs.is_empty() {
                    return;
                }
                self.keeping_selection(|a| {
                    let v = &mut a.views[a.pack];
                    *v = if *v == View::Set { View::Dex } else { View::Set };
                });
            }
            KeyCode::Char('t') => self.theme = (self.theme + 1) % crate::theme::THEMES.len(),
            KeyCode::Char('r') => {
                self.log_mtime = None;
                self.reload_if_changed();
            }
            KeyCode::Char('L') => self.select_latest(),
            KeyCode::Tab => {
                self.focus = match self.focus {
                    Focus::Binder => Focus::Card,
                    Focus::Card => Focus::Stats,
                    Focus::Stats => Focus::Binder,
                };
                if self.focus != Focus::Binder {
                    self.compact_right = self.focus;
                }
            }
            KeyCode::BackTab => {
                self.focus = match self.focus {
                    Focus::Binder => Focus::Stats,
                    Focus::Card => Focus::Binder,
                    Focus::Stats => Focus::Card,
                };
                if self.focus != Focus::Binder {
                    self.compact_right = self.focus;
                }
            }
            KeyCode::Char(c @ '1'..='9') => self.set_pack(c as usize - '1' as usize),
            KeyCode::Char(']') | KeyCode::Char('n') => {
                let n = self.coll.packs.len();
                self.set_pack((self.pack + 1) % n.max(1));
            }
            KeyCode::Char('[') | KeyCode::Char('N') => {
                let n = self.coll.packs.len();
                self.set_pack((self.pack + n.max(1) - 1) % n.max(1));
            }
            KeyCode::PageDown | KeyCode::Char(' ') => self.flip(1),
            KeyCode::PageUp => self.flip(-1),
            KeyCode::Home | KeyCode::Char('g') => {
                if !self.coll.packs.is_empty() {
                    self.sel[self.pack] = 0;
                }
            }
            KeyCode::End | KeyCode::Char('G') => {
                let n = self.slots().len();
                if !self.coll.packs.is_empty() {
                    self.sel[self.pack] = n.saturating_sub(1);
                }
            }
            _ => match self.focus {
                Focus::Binder => match k.code {
                    KeyCode::Left | KeyCode::Char('h') => self.move_grid(-1, 0),
                    KeyCode::Right | KeyCode::Char('l') => self.move_grid(1, 0),
                    KeyCode::Up | KeyCode::Char('k') => self.move_grid(0, -1),
                    KeyCode::Down | KeyCode::Char('j') => self.move_grid(0, 1),
                    KeyCode::Enter if !self.search.is_empty() => self.open_result(),
                    KeyCode::Enter => {
                        self.focus = Focus::Card;
                        self.compact_right = Focus::Card;
                    }
                    _ => {}
                },
                Focus::Card => match k.code {
                    KeyCode::Left | KeyCode::Char('h') => self.step_hist(-1),
                    KeyCode::Right | KeyCode::Char('l') => self.step_hist(1),
                    // with the text half cut off, up/down scroll it; otherwise they step pulls too
                    KeyCode::Up | KeyCode::Char('k') if self.show_text && (self.text_scroll > 0 || self.hits.text_more > 0) => {
                        self.text_scroll = self.text_scroll.saturating_sub(1)
                    }
                    KeyCode::Down | KeyCode::Char('j') if self.show_text && self.hits.text_more > 0 => self.text_scroll += 1,
                    KeyCode::Up | KeyCode::Char('k') => self.step_hist(-1),
                    KeyCode::Down | KeyCode::Char('j') => self.step_hist(1),
                    _ => {}
                },
                Focus::Stats => {
                    let n = self.best_pulls().len();
                    self.best_sel = self.best_sel.min(n.saturating_sub(1));
                    match k.code {
                        KeyCode::Up | KeyCode::Char('k') => self.best_sel = self.best_sel.saturating_sub(1),
                        KeyCode::Down | KeyCode::Char('j') => self.best_sel = (self.best_sel + 1).min(n.saturating_sub(1)),
                        KeyCode::Enter => self.open_best(self.best_sel),
                        _ => {}
                    }
                }
            },
        }
    }

    fn on_picker_key(&mut self, k: KeyEvent, modded: bool) {
        let rows = self.set_rows();
        let n = rows.len();
        let Some(pk) = self.picker.as_mut() else { return };
        match k.code {
            KeyCode::Esc => {
                if pk.filter.is_empty() {
                    self.picker = None;
                } else {
                    pk.filter.clear();
                    pk.sel = 0;
                }
            }
            KeyCode::Enter => {
                if let Some(r) = rows.get(pk.sel.min(n.saturating_sub(1))) {
                    let ix = r.ix;
                    self.choose_set(ix);
                } else {
                    self.picker = None;
                }
            }
            KeyCode::Up | KeyCode::BackTab => pk.sel = pk.sel.checked_sub(1).unwrap_or(n.saturating_sub(1)),
            KeyCode::Down | KeyCode::Tab => pk.sel = if pk.sel + 1 >= n { 0 } else { pk.sel + 1 },
            KeyCode::Char('S') if pk.filter.is_empty() => pk.sel = if pk.sel + 1 >= n { 0 } else { pk.sel + 1 },
            KeyCode::PageUp | KeyCode::Home => pk.sel = 0,
            KeyCode::PageDown | KeyCode::End => pk.sel = n.saturating_sub(1),
            KeyCode::Backspace => {
                pk.filter.pop();
                pk.sel = 0;
            }
            KeyCode::Char('u') if modded => {
                pk.filter.clear();
                pk.sel = 0;
            }
            KeyCode::Char(c) if !modded => {
                pk.filter.push(c);
                pk.sel = 0;
            }
            _ => {}
        }
    }

    fn on_search_key(&mut self, k: KeyEvent, ctrl: bool, alt: bool) {
        let mut cs: Vec<char> = self.search.chars().collect();
        let cur = self.cursor.min(cs.len());
        let before = self.search.clone();
        match k.code {
            KeyCode::Esc => {
                self.clear_search();
                return;
            }
            KeyCode::Enter if !self.search.trim().is_empty() => {
                self.open_result();
                return;
            }
            KeyCode::Enter => self.searching = false,
            KeyCode::Backspace if cur > 0 => {
                cs.remove(cur - 1);
                self.cursor = cur - 1;
            }
            KeyCode::Delete if cur < cs.len() => {
                cs.remove(cur);
            }
            KeyCode::Left => self.cursor = cur.saturating_sub(1),
            KeyCode::Right => self.cursor = (cur + 1).min(cs.len()),
            KeyCode::Home => self.cursor = 0,
            KeyCode::End => self.cursor = cs.len(),
            KeyCode::Char('a') if ctrl => self.cursor = 0,
            KeyCode::Char('e') if ctrl => self.cursor = cs.len(),
            KeyCode::Char('u') if ctrl => {
                cs.drain(..cur);
                self.cursor = 0;
            }
            KeyCode::Char('w') if ctrl => {
                let mut i = cur;
                while i > 0 && cs[i - 1].is_whitespace() {
                    i -= 1;
                }
                while i > 0 && !cs[i - 1].is_whitespace() {
                    i -= 1;
                }
                cs.drain(i..cur);
                self.cursor = i;
            }
            KeyCode::Tab => {
                if let Some((a, b, text)) = self.complete(&cs, cur) {
                    cs.splice(a..b, text.chars());
                    self.cursor = a + text.chars().count();
                }
            }
            KeyCode::Up | KeyCode::Down => {
                self.searching = false;
                self.on_key(k);
                return;
            }
            KeyCode::Char(c) if !ctrl && !alt => {
                cs.insert(cur, c);
                self.cursor = cur + 1;
            }
            _ => {}
        }
        let now: String = cs.into_iter().collect();
        if now != before {
            self.search = now;
            self.hist = None;
            if self.search.trim().is_empty() {
                // cleared by editing: back where the search started (still typing; the next word starts afresh)
                if let Some(b) = self.before.clone() {
                    self.go_back(&b);
                }
            } else if !self.coll.packs.is_empty() {
                self.sel[self.pack] = 0;
            }
        }
    }

    /// Tab in the search: complete the word under the cursor. `set:evo` -> the set's id; `ra` -> `rarity:`.
    fn complete(&self, cs: &[char], cur: usize) -> Option<(usize, usize, String)> {
        let mut a = cur;
        while a > 0 && !cs[a - 1].is_whitespace() {
            a -= 1;
        }
        let word: String = cs[a..cur].iter().collect();
        let lw = word.to_lowercase();
        if let Some(v) = lw.strip_prefix("set:").filter(|v| !v.is_empty() && !v.starts_with('"')) {
            let p = self.coll.packs.get(self.pack)?;
            let s = query::resolve_sets(&p.sets, v).into_iter().next()?;
            return Some((a, cur, format!("set:{} ", s.id)));
        }
        if !lw.contains(':') && lw.len() >= 2 {
            let k = query::KEYS.iter().find(|k| k.starts_with(&lw))?;
            return Some((a, cur, format!("{k}:")));
        }
        None
    }

    fn open_best(&mut self, i: usize) {
        if let Some(&(pi, _)) = self.best_pulls().get(i) {
            if let Some(k) = self.coll.slot_of[pi] {
                self.jump_to(k, Some(pi));
                self.focus = Focus::Card;
                self.compact_right = Focus::Card;
            }
        }
    }

    fn on_mouse(&mut self, m: MouseEvent) {
        let pos = Position::new(m.column, m.row);
        let wheel = match m.kind {
            MouseEventKind::ScrollDown => 1,
            MouseEventKind::ScrollUp => -1,
            _ => 0,
        };
        if wheel != 0 {
            self.dirty = true;
            if self.help {
                self.help_scroll = (self.help_scroll as isize + wheel * 3).max(0) as usize;
            } else if self.picker.is_some() {
                let n = self.set_rows().len();
                if let Some(pk) = self.picker.as_mut() {
                    pk.sel = (pk.sel as isize + wheel).clamp(0, n.saturating_sub(1) as isize) as usize;
                }
            } else if self.hits.stats.contains(pos) {
                let n = self.best_pulls().len();
                self.best_sel = (self.best_sel as isize + wheel).clamp(0, n.saturating_sub(1) as isize) as usize;
            } else if self.show_text && self.hits.text.contains(pos) {
                if wheel > 0 && self.hits.text_more > 0 {
                    self.text_scroll += 1;
                } else if wheel < 0 {
                    self.text_scroll = self.text_scroll.saturating_sub(1);
                }
            } else if self.hits.card.contains(pos) {
                self.step_hist(wheel);
            } else {
                self.flip(wheel);
            }
            return;
        }
        if m.kind != MouseEventKind::Down(MouseButton::Left) {
            return;
        }
        self.dirty = true;
        self.notice = None;
        if self.help {
            self.help = false;
            return;
        }
        if self.picker.is_some() {
            if let Some(&(_, row)) = self.hits.picker_rows.iter().find(|(r, _)| r.contains(pos)) {
                if let Some(r) = self.set_rows().get(row) {
                    let ix = r.ix;
                    self.choose_set(ix);
                }
            } else if !self.hits.picker.contains(pos) {
                self.picker = None;
            }
            return;
        }
        self.number = None;
        self.searching = false; // a click ends typing (the query stays)
        if let Some(&(_, _, _, tab)) = self.hits.tabs.iter().find(|t| t.2 == m.row as i32 && (t.0..=t.1).contains(&(m.column as i32))) {
            match tab {
                Tab::Pack(p) => self.set_pack(p),
                Tab::Set => self.open_picker(),
            }
            return;
        }
        if self.hits.prev_page.is_some_and(|r| r.contains(pos)) {
            self.flip(-1);
            return;
        }
        if self.hits.next_page.is_some_and(|r| r.contains(pos)) {
            self.flip(1);
            return;
        }
        if let Some(&(_, i)) = self.hits.slots.iter().find(|(r, _)| r.contains(pos)) {
            // during a search, a click on the selected card opens it on its real page (like Enter)
            let again = self.sel[self.pack] == i;
            self.sel[self.pack] = i;
            self.focus = Focus::Binder;
            if again && !self.search.is_empty() {
                self.open_result();
            }
            return;
        }
        if let Some(&(_, pi)) = self.hits.best.iter().find(|(r, _)| r.contains(pos)) {
            if let Some(i) = self.best_pulls().iter().position(|b| b.0 == pi) {
                self.best_sel = i;
                self.open_best(i);
            }
            return;
        }
        if self.hits.card.contains(pos) {
            self.focus = Focus::Card;
        } else if self.hits.stats.contains(pos) {
            self.focus = Focus::Stats;
        } else if self.hits.binder.contains(pos) {
            self.focus = Focus::Binder;
        }
    }

    /// Shiny-only on/off; landing on a caught shiny when there is one.
    pub fn toggle_shiny(&mut self) {
        if self.coll.packs.is_empty() {
            return;
        }
        self.keeping_selection(|a| a.shiny_only = !a.shiny_only);
        if self.shiny_only {
            let cur = self.selected();
            if cur.is_none_or(|k| self.coll.slot_state(k, true) != SlotState::Caught) {
                let list = self.slots().to_vec();
                if let Some(i) = list.iter().position(|k| self.coll.slot_state(*k, true) == SlotState::Caught) {
                    self.sel[self.pack] = i;
                }
            }
        }
        self.dirty = true;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::data::tests::{fixture_pack, ulid_now, write_log};

    fn app(dir: &std::path::Path, set: &str, search: &str, start: Start) -> App {
        App::new(
            Opts {
                root: dir.to_path_buf(),
                log: dir.join("state/pulls.log"),
                viewed: dir.join("state/viewed.txt"),
                demo_pending: 0,
                start,
                readonly: true,
                search: search.into(),
                set: set.into(),
            },
            0,
        )
    }

    fn sel_id(a: &mut App) -> String {
        let k = a.selected().unwrap();
        a.coll.packs[k.pack].card_list[k.card as usize].id.clone()
    }

    #[test]
    fn newest_pull_lands_on_the_exact_card_in_every_view() {
        // Lycanroc V (swsh7-91, rare-holo-v) and Lycanroc VMAX (swsh7-92, rare-holo-vmax): the newest pull is the
        // VMAX. It must be selected, never the V, in the card view and in the dex view; also through --pull / --card.
        let d = fixture_pack("land");
        write_log(
            &d,
            &[
                "2026-09-29T08:00:00\tp\tlycanroc\trare-ultra\tswsh7-187\t\t0\t",
                "2026-09-29T08:01:00\tp\tlycanroc\trare-holo-v\tswsh7-91\t\t0\t",
                "2026-09-29T08:02:00\tp\tlycanroc\trare-holo-vmax\tswsh7-92\tv-beam\t0\t",
                "2026-09-29T08:03:00\tp\tpikachu\tcommon\tswsh7-49\t\t0\t",
                "2026-09-29T08:04:00\tp\tlycanroc\trare-holo-vmax\tswsh7-92\tv-beam\t0\t",
            ],
        );
        let mut a = app(&d, "", "", Start::Latest);
        assert_eq!(a.views[0], View::Set, "a real-card pack opens on its cards");
        assert_eq!(sel_id(&mut a), "swsh7-92");
        let k = a.selected().unwrap();
        assert_eq!(a.hist_pos(k), Some((1, 2)), "the newest of its two pulls");
        // the dex view: the character's slot shows the pulled card (the rare-ultra V is the higher tier)
        a.views[0] = View::Dex;
        a.select_latest();
        assert_eq!(sel_id(&mut a), "swsh7-92");
        a.dex_focus[0] = None;
        a.slots_key = None;
        let ly = a.coll.packs[0].char_ix["lycanroc"];
        let best = a.slots().iter().find(|k| k.ch == ly).copied().unwrap();
        assert_eq!(a.coll.packs[0].card_list[best.card as usize].id, "swsh7-187", "unfocused, the dex slot is the best card");
        // --card with a card id, and with character/tier
        let mut a = app(&d, "", "", Start::Card("p/swsh7-91".into()));
        assert_eq!(sel_id(&mut a), "swsh7-91");
        let mut a = app(&d, "", "", Start::Card("p/lycanroc/rare-holo-vmax".into()));
        assert_eq!(sel_id(&mut a), "swsh7-92");
        a.views[0] = View::Dex;
        assert!(a.select_card("p/swsh7-91"));
        assert_eq!(sel_id(&mut a), "swsh7-91", "dex view too");
        let _ = std::fs::remove_dir_all(&d);
    }

    #[test]
    fn search_lists_every_card_and_caught_excludes_seen() {
        // the user's /pikachu: 3 earned Pikachu cards and 1 pending (seen) one; every one is listed, `caught` (and its
        // old word `owned`) lists the 3, `seen` (and `pending`) the other
        let d = fixture_pack("pika");
        let (e1, e2, e3, p1) = (ulid_now("EEEEEEEEEEEEEEE1"), ulid_now("EEEEEEEEEEEEEEE2"), ulid_now("EEEEEEEEEEEEEEE3"), ulid_now("PPPPPPPPPPPPPPP1"));
        let now_boot = crate::data::boot_id();
        let lines = vec![
            format!("2026-09-29T08:00:00\tp\tpikachu\tpikachu-rare\tme55-28\t\t0\tpending\tid={e1}\tboot={now_boot}"),
            format!("2026-09-29T08:00:01\tearned:{e1}"),
            format!("2026-09-29T08:01:00\tp\tpikachu\tpikachu-rare\tme55-45\t\t0\tpending\tid={e2}\tboot={now_boot}"),
            format!("2026-09-29T08:01:01\tearned:{e2}"),
            format!("2026-09-29T08:02:00\tp\tpikachu\tpikachu-rare\tme55-48\t\t0\tpending\tid={e3}\tboot={now_boot}"),
            format!("2026-09-29T08:02:01\tearned:{e3}"),
            format!("2026-09-29T08:03:00\tp\tpikachu\tcommon\tswsh7-49\t\t0\tpending\tid={p1}\tboot={now_boot}"),
            "2026-09-29T08:04:00\tp\tpikachu\tcommon\tcommon\t\t0\t".to_string(), // old art: hidden (not built)
        ];
        write_log(&d, &lines.iter().map(|s| s.as_str()).collect::<Vec<_>>());
        for view in [View::Set, View::Dex] {
            let mut a = app(&d, "", "pikachu", Start::Latest);
            a.views[0] = view;
            a.slots_key = None;
            let ids: Vec<String> = a.slots().to_vec().iter().map(|k| a.coll.packs[0].card_list[k.card as usize].id.clone()).collect();
            if view == View::Set {
                for want in ["me55-28", "me55-45", "me55-48", "swsh7-49"] {
                    assert!(ids.contains(&want.to_string()), "{want} in {ids:?}");
                }
                let st: Vec<SlotState> = ["me55-28", "swsh7-49"].iter().map(|id| {
                    let i = a.coll.packs[0].card_list.iter().position(|c| c.id == *id).unwrap();
                    a.coll.slot_state(a.coll.packs[0].key_of(0, i), false)
                }).collect();
                assert_eq!(st, vec![SlotState::Caught, SlotState::Seen]);
            } else {
                assert_eq!(ids.len(), 1, "one pikachu slot in the dex view: {ids:?}");
                // S-02: a character matches if any of its cards does, and its slot shows a matching card (its
                // representative, the common, doesn't match: before, this found nothing)
                a.search = r#"set:30th rarity:"pikachu rare""#.into();
                let k = a.slots().to_vec();
                assert_eq!(k.len(), 1);
                let c = &a.coll.packs[0].card_list[k[0].card as usize];
                assert_eq!((c.set_id.as_str(), a.coll.packs[0].tiers[c.tier].id.as_str()), ("me55", "pikachu-rare"));
                assert_eq!(a.coll.slot_state(k[0], false), SlotState::Caught, "a caught one first");
                a.search = "lycanroc missing".into();
                assert_eq!(a.slots().len(), 1, "a character never pulled: missing, on its first card");
            }
            for q in ["pikachu owned", "pikachu caught", "pikachu is:caught"] {
                a.search = q.into();
                let n = a.slots().len();
                assert_eq!(n, if view == View::Set { 3 } else { 1 }, "{q} {view:?}");
            }
            if view == View::Set {
                for q in ["pikachu seen", "pikachu pending"] {
                    a.search = q.into();
                    let ids: Vec<String> = a.slots().to_vec().iter().map(|k| a.coll.packs[0].card_list[k.card as usize].id.clone()).collect();
                    assert_eq!(ids, vec!["swsh7-49".to_string()], "{q}");
                }
                a.search = "pikachu missing".into();
                assert_eq!(a.slots().len(), 1, "missing = not caught: the seen one");
            }
        }
        let _ = std::fs::remove_dir_all(&d);
    }

    #[test]
    fn set_arg_is_fuzzy_and_forces_the_checklist() {
        let d = fixture_pack("setarg");
        write_log(&d, &["2026-09-29T08:00:00\tp\tlycanroc\trare-holo-v\tswsh7-91\t\t0\t", "2026-09-29T08:01:00\tp\tpikachu\tpikachu-rare\tme55-28\t\t0\t"]);
        for q in ["me55", "30th", "30TH celebration", "celeb"] {
            let mut a = app(&d, q, "", Start::Latest);
            assert_eq!(a.current_set().map(|s| s.id.clone()), Some("me55".into()), "{q}");
            assert_eq!(a.views[0], View::Set);
            assert_eq!(sel_id(&mut a), "me55-28", "lands on the newest pull in the set");
            assert!(a.notice.is_none());
            // the checklist: that set's cards only, in printed order, one slot each
            let nums: Vec<String> = a.slots().to_vec().iter().map(|k| a.coll.packs[0].card_list[k.card as usize].number.clone()).collect();
            assert_eq!(nums, vec!["28/128", "45/128", "48/128", "B/128"]);
        }
        let mut a = app(&d, "evolving", "", Start::Latest);
        assert_eq!(a.current_set().map(|s| s.id.clone()), Some("swsh7".into()));
        assert_eq!(sel_id(&mut a), "swsh7-91");
        let a = app(&d, "zzz", "", Start::Latest);
        assert!(a.current_set().is_none());
        assert!(a.notice.as_deref().unwrap_or("").starts_with("no set matches “zzz”"), "{:?}", a.notice);
        let _ = std::fs::remove_dir_all(&d);
    }

    #[test]
    fn completion_excludes_seen() {
        let d = fixture_pack("done");
        let now_boot = crate::data::boot_id();
        let p1 = ulid_now("PPPPPPPPPPPPPPP1");
        write_log(
            &d,
            &[
                "2026-09-29T08:00:00\tp\tpikachu\tpikachu-rare\tme55-28\t\t0\t",
                &format!("2026-09-29T08:03:00\tp\tpikachu\tpikachu-rare\tme55-45\t\t0\tpending\tid={p1}\tboot={now_boot}"),
            ],
        );
        let a = app(&d, "me55", "", Start::Latest);
        let c = a.view_completion();
        assert_eq!((c.caught, c.seen, c.total), (1, 1, 4));
        let rows = a.tier_rows();
        let pr = rows.iter().find(|r| a.coll.packs[0].tiers[r.tier].id == "pikachu-rare").unwrap();
        assert_eq!((pr.caught, pr.seen, pr.of, pr.pulls), (1, 1, 3, 1), "the tiers panel follows the set; pulls are caught ones");
        assert!(rows.iter().all(|r| a.coll.packs[0].tiers[r.tier].id != "rare-holo-v"), "only the set's rarities");
        let _ = std::fs::remove_dir_all(&d);
    }

    /// Empty, seen (pending, expired by age, expired by an event) and caught slots; the newest pull is a seen one.
    fn seen_log(d: &std::path::Path) -> (String, String) {
        let now_boot = crate::data::boot_id();
        let p = ulid_now("PPPPPPPPPPPPPPP1");
        let old = {
            // a ULID 30 h old: expired by age
            let ms = (crate::data::now_utc() - 30 * 3600) * 1000;
            let mut v = ms;
            let mut s = vec![b'0'; 10];
            for i in (0..10).rev() {
                s[i] = b"0123456789ABCDEFGHJKMNPQRSTVWXYZ"[(v % 32) as usize];
                v /= 32;
            }
            String::from_utf8(s).unwrap() + "XXXXXXXXXXXXXXX1"
        };
        let e = ulid_now("EEEEEEEEEEEEEEE1");
        let lines = vec![
            "2026-09-29T08:00:00\tp\tlycanroc\trare-holo-v\tswsh7-91\t\t0\t".to_string(),
            format!("2026-09-29T08:01:00\tp\tpikachu\tpikachu-rare\tme55-28\t\t0\tpending\tid={p}\tboot={now_boot}"),
            format!("2026-09-29T08:02:00\tp\tbulbasaur\tillustration-rare\tme55-B\t\t0\tpending\tid={old}\tboot={now_boot}"),
            format!("2026-09-29T08:03:00\tp\tlycanroc\trare-holo-vmax\tswsh7-92\tv-beam\t1\tpending\tid={e}\tboot={now_boot}"),
            format!("2026-09-29T08:03:30\texpired:{e}"),
        ];
        write_log(d, &lines.iter().map(|s| s.as_str()).collect::<Vec<_>>());
        (p, e)
    }

    fn state_of(a: &App, id: &str) -> SlotState {
        let i = a.coll.packs[0].card_list.iter().position(|c| c.id == id).unwrap();
        a.coll.slot_state(a.coll.packs[0].key_of(0, i), false)
    }

    #[test]
    fn empty_seen_caught() {
        // every slot is empty, seen (pulled, never earned: pending or expired) or caught; expired pulls count as seen
        let d = fixture_pack("seen");
        let (p, e) = seen_log(&d);
        let mut a = app(&d, "", "", Start::Latest);
        assert_eq!(state_of(&a, "swsh7-91"), SlotState::Caught);
        assert_eq!(state_of(&a, "me55-28"), SlotState::Seen, "pending: seen");
        assert_eq!(state_of(&a, "me55-B"), SlotState::Seen, "expired after 24 h: seen");
        assert_eq!(state_of(&a, "swsh7-92"), SlotState::Seen, "an expired:<id> line: seen");
        assert_eq!(state_of(&a, "swsh7-49"), SlotState::Empty);
        // opening lands on the last caught card, never the newer seen ones
        assert_eq!(sel_id(&mut a), "swsh7-91");
        a.views[0] = View::Dex;
        a.select_latest();
        assert_eq!(sel_id(&mut a), "swsh7-91", "dex view: the caught Lycanroc, not the seen VMAX");
        // stats and completion: caught only; seen apart
        let st = a.stats();
        assert_eq!((st.total, st.unique, st.seen, st.shinies), (1, 1, 3, 0), "the seen VMAX was shiny: not counted");
        let li = st.last.unwrap();
        assert_eq!(a.coll.pulls[li].card, "swsh7-91", "the header's last pull is the last caught");
        a.views[0] = View::Set;
        let c = a.view_completion();
        assert_eq!((c.caught, c.seen, c.total), (1, 3, 8));
        let best: Vec<String> = a.best_pulls().iter().map(|&(i, _)| a.coll.pulls[i].card.clone()).collect();
        assert_eq!(best, vec!["swsh7-91".to_string()], "best pulls: the caught holo; the seen shiny VMAX is none");
        // a seen card: no pulls to step through, no NEW, and how to catch it
        let k28 = a.coll.packs[0].key_of(0, a.coll.packs[0].card_list.iter().position(|c| c.id == "me55-28").unwrap());
        assert_eq!(a.shown_pull(k28), (vec![], None));
        assert!(a.coll.pending_pull(k28).is_some(), "its tab can still catch it");
        let kb = a.coll.packs[0].key_of(0, a.coll.packs[0].card_list.iter().position(|c| c.id == "me55-B").unwrap());
        assert!(a.coll.pending_pull(kb).is_none(), "expired: pull it again");
        // an explicit pull or card lands on its slot, seen or not
        let mut a = app(&d, "", "", Start::Pull(p.clone()));
        assert_eq!(sel_id(&mut a), "me55-28");
        assert!(a.notice.is_none());
        let mut a = app(&d, "", "", Start::Pull(e.clone()));
        assert_eq!(sel_id(&mut a), "swsh7-92", "an expired pull still opens its (seen) slot");
        let mut a = app(&d, "", "", Start::Card("p/me55-B".into()));
        assert_eq!(sel_id(&mut a), "me55-B");
        // L: the last caught card again
        a.on_event(Event::Key(KeyEvent::new(KeyCode::Char('L'), KeyModifiers::SHIFT)));
        assert_eq!(sel_id(&mut a), "swsh7-91");
        // a set: lands on its last caught card, else its first card (not a seen one)
        let mut a = app(&d, "30th", "", Start::Latest);
        assert_eq!(sel_id(&mut a), "me55-28", "the set's first card (none caught there): it happens to be seen");
        assert_eq!(a.sel_ix(), 0);
        // o: caught only; m: missing = not caught (empty and seen)
        let mut a = app(&d, "", "", Start::Latest);
        a.on_event(Event::Key(KeyEvent::new(KeyCode::Char('o'), KeyModifiers::NONE)));
        assert_eq!(a.slots().len(), 1);
        a.on_event(Event::Key(KeyEvent::new(KeyCode::Char('m'), KeyModifiers::NONE)));
        assert_eq!(a.slots().len(), 7);
        // the search words
        for (q, n) in [("seen", 3), ("pending", 3), ("is:seen", 3), ("caught", 1), ("owned", 1), ("missing", 7), ("lyc seen", 1), ("-seen", 5)] {
            let mut a = app(&d, "", q, Start::Latest);
            assert_eq!(a.slots().len(), n, "/{q}");
        }
        let _ = std::fs::remove_dir_all(&d);
    }

    #[test]
    fn nothing_caught_lands_on_the_first_card() {
        // only seen pulls: the binder opens on its first card, not on the seen one
        let d = fixture_pack("seenonly");
        let now_boot = crate::data::boot_id();
        let p = ulid_now("PPPPPPPPPPPPPPP2");
        write_log(&d, &[&format!("2026-09-29T08:01:00\tp\tlycanroc\trare-holo-vmax\tswsh7-92\t\t0\tpending\tid={p}\tboot={now_boot}")]);
        let mut a = app(&d, "", "", Start::Latest);
        assert_eq!(a.sel_ix(), 0);
        assert_eq!(sel_id(&mut a), "swsh7-49");
        assert_eq!(a.stats().last, None);
        let _ = std::fs::remove_dir_all(&d);
    }

    #[test]
    fn seen_cards_render_as_silhouettes() {
        // the binder page and the card panel of a seen card: its name and number, "seen" and how to catch it; no
        // "pending" anywhere, no NEW, no shiny mark
        let d = fixture_pack("seenui");
        let (p, _) = seen_log(&d);
        // the silhouette comes from the character's plain sprite: Pikachu's common (its art has transparent pixels),
        // while the seen card's own art is a full-bleed scene
        std::fs::write(d.join("dist/p/pikachu-swsh7-49.ans"), "\x1b[38;2;250;200;0m\u{2588}\u{2588}\x1b[0m  \n\x1b[38;2;250;200;0m \u{2588}\u{2588}\x1b[0m\n").unwrap();
        std::fs::write(d.join("dist/p/pikachu-me55-28.ans"), "\x1b[38;2;9;9;9;48;2;90;140;60m\u{2580}\u{2580}\u{2580}\x1b[0m\n".repeat(2)).unwrap();
        let mut a = app(&d, "", "", Start::Pull(p));
        let k = a.selected().unwrap();
        let sil = a.art.silhouette(&a.coll.packs[0], k).expect("a silhouette from Pikachu's sprite card");
        assert!(crate::art::is_sprite(&sil) && sil.px.iter().any(|p| p.is_some()), "the common's shape, not the scene: {sil:?}");
        let mut t = ratatui::Terminal::new(ratatui::backend::TestBackend::new(140, 44)).unwrap();
        let buf = t.draw(|f| crate::ui::render(&mut a, f.buffer_mut())).unwrap().buffer.clone();
        let text: String = (0..buf.area.height).map(|y| (0..buf.area.width).map(|x| buf[(x, y)].symbol().to_string()).collect::<String>() + "\n").collect();
        assert!(text.contains("seen") && (text.contains("use its tab") || text.contains("use the tab")), "{text}");
        assert!(!text.to_lowercase().contains("pending"), "{text}");
        assert!(text.contains("caught 1") && text.contains("seen 3"), "header counts: {text}");
        let _ = std::fs::remove_dir_all(&d);
    }

    #[test]
    fn search_opens_the_real_page() {
        // the search shows only the matching cards; Enter opens the selected one on its real, unfiltered page (its
        // neighbours around it), selected and glowing; Esc instead goes back to where you were before searching
        let d = fixture_pack("open");
        write_log(&d, &["2026-09-29T08:00:00	p	lycanroc	rare-holo-vmax	swsh7-92		0	", "2026-09-29T08:01:00	p	pikachu	pikachu-rare	me55-28		0	"]);
        let key = |c: KeyCode| Event::Key(KeyEvent::new(c, KeyModifiers::NONE));
        let ids = |a: &mut App| a.slots().to_vec().iter().map(|k| a.coll.packs[0].card_list[k.card as usize].id.clone()).collect::<Vec<_>>();
        let mut a = app(&d, "", "", Start::Latest);
        let all = ids(&mut a);
        assert_eq!(all.len(), 8);
        assert_eq!(sel_id(&mut a), "me55-28");
        a.on_event(key(KeyCode::Char('/')));
        for c in "lyc vmax".chars() {
            a.on_event(key(KeyCode::Char(c)));
        }
        assert_eq!(ids(&mut a), vec!["swsh7-92"], "the binder shows only the match (not Lycanroc V)");
        let c = a.search_counts().unwrap();
        assert_eq!((c.packs[0], c.sets[0]), (1, 1));
        let sets: Vec<(String, Option<usize>)> = a.set_rows().iter().map(|r| (r.id.clone(), r.hits)).collect();
        assert_eq!(sets, vec![(String::new(), Some(1)), ("swsh7".into(), Some(1))], "the picker keeps the sets with matches");
        a.on_event(key(KeyCode::Enter));
        assert!(a.search.is_empty() && !a.searching);
        assert_eq!(ids(&mut a), all, "the real page: every card");
        assert_eq!(sel_id(&mut a), "swsh7-92");
        let k = a.selected().unwrap();
        assert!(a.flash_level(k) > 0.5, "it glows");
        let at = all.iter().position(|x| x == "swsh7-92").unwrap();
        assert_eq!(a.sel_ix(), at);
        // Esc: back where the search started
        a.on_event(key(KeyCode::Char('/')));
        for c in "pikchu".chars() {
            a.on_event(key(KeyCode::Char(c)));
        }
        assert!(ids(&mut a).iter().all(|x| a.coll.packs[0].card(x).unwrap().name == "Pikachu") && a.slots().len() == 4, "pikchu: the four Pikachu cards");
        a.on_event(key(KeyCode::Right));
        a.on_event(key(KeyCode::Esc));
        assert!(a.search.is_empty());
        assert_eq!(sel_id(&mut a), "swsh7-92", "Esc: where you were");
        // clearing the search by editing goes back too; so does Esc in the binder after arrowing through results
        a.on_event(key(KeyCode::Char('/')));
        a.on_event(key(KeyCode::Char('p')));
        a.on_event(key(KeyCode::Char('i')));
        a.on_event(key(KeyCode::Down));
        a.on_event(key(KeyCode::Esc));
        assert!(a.search.is_empty());
        assert_eq!(sel_id(&mut a), "swsh7-92");
        let _ = std::fs::remove_dir_all(&d);
    }

    #[test]
    fn picker_keys() {
        let d = fixture_pack("picker");
        write_log(&d, &["2026-09-29T08:00:00\tp\tpikachu\tpikachu-rare\tme55-28\t\t0\t"]);
        let mut a = app(&d, "", "", Start::Latest);
        let key = |c: KeyCode| Event::Key(KeyEvent::new(c, KeyModifiers::NONE));
        a.on_event(Event::Key(KeyEvent::new(KeyCode::Char('S'), KeyModifiers::SHIFT)));
        assert!(a.picker.is_some());
        let rows = a.set_rows();
        assert_eq!(rows[0].ix, 0, "every set first");
        assert_eq!(rows[1].id, "me55", "the set you collect most next");
        for c in "evo".chars() {
            a.on_event(key(KeyCode::Char(c)));
        }
        assert_eq!(a.set_rows().iter().map(|r| r.id.as_str()).collect::<Vec<_>>(), vec!["swsh7"]);
        a.on_event(key(KeyCode::Enter));
        assert!(a.picker.is_none());
        assert_eq!(a.current_set().map(|s| s.id.clone()), Some("swsh7".into()));
        // reopen, arrow up to "every set"
        a.on_event(Event::Key(KeyEvent::new(KeyCode::Char('S'), KeyModifiers::SHIFT)));
        a.on_event(key(KeyCode::Home));
        a.on_event(key(KeyCode::Enter));
        assert!(a.current_set().is_none());
        // Esc closes without changing anything
        a.on_event(Event::Key(KeyEvent::new(KeyCode::Char('S'), KeyModifiers::SHIFT)));
        a.on_event(key(KeyCode::Down));
        a.on_event(key(KeyCode::Esc));
        assert!(a.picker.is_none() && a.current_set().is_none());
        // # jumps to a printed number in the set
        a.choose_set(2);
        a.on_event(key(KeyCode::Char('#')));
        for c in "b".chars() {
            a.on_event(key(KeyCode::Char(c)));
        }
        a.on_event(key(KeyCode::Enter));
        assert_eq!(sel_id(&mut a), "me55-B");
        let _ = std::fs::remove_dir_all(&d);
    }

    #[test]
    fn filters_keep_the_selection_and_history() {
        let d = fixture_pack("keep");
        write_log(
            &d,
            &[
                "2026-09-29T08:00:00\tp\tlycanroc\trare-holo-vmax\tswsh7-92\t\t0\t",
                "2026-09-29T08:01:00\tp\tlycanroc\trare-holo-vmax\tswsh7-92\t\t0\t",
                "2026-09-29T08:02:00\tp\tpikachu\tpikachu-rare\tme55-45\t\t0\t",
            ],
        );
        let mut a = app(&d, "", "", Start::Card("p/swsh7-92".into()));
        let k = a.selected().unwrap();
        a.hist = Some((k, 0));
        a.on_event(Event::Key(KeyEvent::new(KeyCode::Char('o'), KeyModifiers::NONE)));
        assert_eq!(sel_id(&mut a), "swsh7-92", "o keeps the card");
        a.on_event(Event::Key(KeyEvent::new(KeyCode::Char('d'), KeyModifiers::NONE)));
        assert_eq!(sel_id(&mut a), "swsh7-92", "d keeps the card");
        // the history cursor belongs to its slot: another card shows its own newest pull
        a.on_event(Event::Key(KeyEvent::new(KeyCode::Char('d'), KeyModifiers::NONE)));
        a.jump_to(a.coll.packs[0].key_of(0, a.coll.packs[0].card_list.iter().position(|c| c.id == "me55-45").unwrap()), None);
        let k2 = a.selected().unwrap();
        assert_eq!(a.hist_pos(k2), Some((0, 1)));
        // ctrl+s is not s (K-01); AltGr (ctrl+alt) + / is / (layouts that type / [ ] # with AltGr)
        a.on_event(Event::Key(KeyEvent::new(KeyCode::Char('s'), KeyModifiers::CONTROL)));
        assert!(!a.shiny_only);
        a.on_event(Event::Key(KeyEvent::new(KeyCode::Char('/'), KeyModifiers::CONTROL | KeyModifiers::ALT)));
        assert!(a.searching);
        // search editing: a cursor, ctrl+w, ctrl+u (K-04)
        for c in "pika chu".chars() {
            a.on_event(Event::Key(KeyEvent::new(KeyCode::Char(c), KeyModifiers::NONE)));
        }
        a.on_event(Event::Key(KeyEvent::new(KeyCode::Left, KeyModifiers::NONE)));
        a.on_event(Event::Key(KeyEvent::new(KeyCode::Char('X'), KeyModifiers::SHIFT)));
        assert_eq!((a.search.as_str(), a.cursor), ("pika chXu", 8));
        a.on_event(Event::Key(KeyEvent::new(KeyCode::Char('w'), KeyModifiers::CONTROL)));
        assert_eq!(a.search, "pika u");
        a.on_event(Event::Key(KeyEvent::new(KeyCode::Char('u'), KeyModifiers::CONTROL)));
        assert_eq!(a.search, "u");
        a.on_event(Event::Key(KeyEvent::new(KeyCode::Esc, KeyModifiers::NONE)));
        assert!(!a.searching && a.search.is_empty());
        let _ = std::fs::remove_dir_all(&d);
    }

    #[test]
    fn no_packs_no_panic() {
        let d = std::env::temp_dir().join(format!("binder-test-nopacks-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&d);
        std::fs::create_dir_all(d.join("packs")).unwrap();
        std::fs::create_dir_all(d.join("state")).unwrap();
        let mut a = app(&d, "x", "y", Start::Latest);
        assert!(a.coll.packs.is_empty());
        assert!(a.selected().is_none());
        for c in ['S', 'd', 's', 'o', 'm', 'g', 'G', ']', '#', '1'] {
            a.on_event(Event::Key(KeyEvent::new(KeyCode::Char(c), KeyModifiers::NONE)));
        }
        let mut t = ratatui::Terminal::new(ratatui::backend::TestBackend::new(80, 24)).unwrap();
        t.draw(|f| crate::ui::render(&mut a, f.buffer_mut())).unwrap();
        let _ = std::fs::remove_dir_all(&d);
    }
}
