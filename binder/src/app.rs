//! App state: which pack/page/card is selected, filters, focus, and input handling.

use crate::art::ArtStore;
use crate::data::{Collection, NO_CARD, ReadCtx, SlotKey, SlotState, Status, boot_id, load_packs, mark_viewed, now_local, now_utc, read_pulls, read_viewed};
use crossterm::event::{Event, KeyCode, KeyEvent, KeyEventKind, KeyModifiers, MouseButton, MouseEvent, MouseEventKind};
use ratatui::layout::{Position, Rect};
use serde_json::Value;
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

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum View {
    /// Every character x every tier, tier by tier: the full set.
    Set,
    /// One slot per character showing its best card (the 905-mon pokedex).
    Dex,
}

#[derive(Default)]
pub struct Hits {
    pub slots: Vec<(Rect, usize)>,
    pub tabs: Vec<(i32, i32, i32, usize)>, // x0, x1, y, pack
    pub best: Vec<(Rect, usize)>,          // pull index
    pub binder: Rect,
    pub card: Rect,
    pub stats: Rect,
    pub prev_page: Option<Rect>,
    pub next_page: Option<Rect>,
    /// the big card's rect (animated region)
    pub card_art: Rect,
    /// the art box the big card was fitted to (reused by animation frames)
    pub card_fit: (usize, usize),
}

/// Where the binder opens: the newest pull (default), a pull id (--pull, the card's link) or a card (--card).
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
    /// start with this search (--search) / on this set's checklist (--set <set id>)
    pub search: String,
    pub set: String,
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
    pub owned_only: bool,
    /// `/`: free text and tag filters (query.rs)
    pub search: String,
    pub searching: bool,
    /// per pack: 0 = every set, i + 1 = pack.sets[i] (the set's checklist)
    pub set_sel: Vec<usize>,
    pub focus: Focus,
    pub help: bool,
    pub hist: usize,
    pub best_sel: usize,
    pub now: i64,
    pub anim_t0: Instant,
    /// Fixed shimmer phase (snapshots); None = real time.
    pub phase_override: Option<f32>,
    pub hits: Hits,
    pub quit: bool,
    pub log_mtime: Option<SystemTime>,
    slots_key: (usize, View, bool, bool, String, usize, usize),
    slots: Vec<SlotKey>,
    /// Set when anything but the animation changed: the next draw repaints everything.
    pub dirty: bool,
    pub compact_right: Focus,
    /// `v`: the card's text half (docs/CARD_FORMAT.md) stacked under the art
    pub show_text: bool,
    text_cache: HashMap<PathBuf, Option<Rc<Value>>>,
    viewed: HashSet<String>,
    /// the slot whose NEW pulls were last shown in the card panel (they lose the sticker once you move on)
    seen_slot: Option<SlotKey>,
}

fn mtime(p: &PathBuf) -> Option<SystemTime> {
    std::fs::metadata(p).and_then(|m| m.modified()).ok()
}

impl App {
    fn load_pulls(opts: &Opts, viewed: &HashSet<String>) -> Vec<crate::data::Pull> {
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
            owned_only: false,
            search: String::new(),
            set_sel: vec![0; n],
            searching: false,
            focus: Focus::Binder,
            help: false,
            hist: 0,
            best_sel: 0,
            now: now_local(),
            anim_t0: Instant::now(),
            phase_override: None,
            hits: Hits::default(),
            quit: false,
            slots_key: (usize::MAX, View::Set, false, false, String::new(), 0, 0),
            slots: Vec::new(),
            dirty: true,
            compact_right: Focus::Card,
            show_text: false,
            text_cache: HashMap::new(),
            viewed,
            seen_slot: None,
        };
        // --set / --search: open on that set (in its pack) / with that search, on its first card
        let set = app.opts.set.clone();
        if !set.is_empty() {
            for (pi, p) in app.coll.packs.iter().enumerate() {
                if let Some(si) = p.sets.iter().position(|s| s.id.eq_ignore_ascii_case(&set) || s.name.eq_ignore_ascii_case(&set)) {
                    app.pack = pi;
                    app.set_sel[pi] = si + 1;
                    break;
                }
            }
        }
        app.search = app.opts.search.clone();
        if !set.is_empty() || !app.search.is_empty() {
            app.hist = usize::MAX;
            return app;
        }
        let start = app.opts.start.clone();
        let landed = match &start {
            Start::Latest => false,
            Start::Pull(id) => app.select_pull(id),
            Start::Card(c) => app.select_card(c),
        };
        if !landed {
            app.select_latest();
        }
        app
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

    /// Open on a card: "pack/character/tier" (tier by id or label; the character may be a card id).
    pub fn select_card(&mut self, spec: &str) -> bool {
        let parts: Vec<&str> = spec.split('/').map(|s| s.trim()).collect();
        let (pack, ch, tier) = match parts.as_slice() {
            [p, c, t] => (*p, *c, *t),
            [p, c] => (*p, *c, ""),
            _ => return false,
        };
        let Some(pi) = self.coll.packs.iter().position(|p| p.id.eq_ignore_ascii_case(pack)) else { return false };
        let pk = &self.coll.packs[pi];
        // a card id (pokemon/swsh4-170), or a character and a tier (by id or label; none: its lowest tier with a card)
        let k = if let Some(ix) = pk.card_list.iter().position(|c| c.id.eq_ignore_ascii_case(ch)) {
            let c = &pk.card_list[ix];
            SlotKey { pack: pi, ch: c.ch, tier: c.tier, card: ix as u32 }
        } else {
            let Some(&ci) = pk.char_ix.get(ch) else { return false };
            let ti = if tier.is_empty() {
                (0..pk.tiers.len()).find(|&t| pk.has_slot(ci, t))
            } else {
                pk.tier_ix(tier).or_else(|| pk.tiers.iter().position(|t| t.label.eq_ignore_ascii_case(tier)))
            };
            let Some(ti) = ti else { return false };
            // real-card packs: that character's first card in that tier
            let card = pk.card_list.iter().position(|c| c.ch == ci && c.tier == ti).map(|i| i as u32).unwrap_or(NO_CARD);
            if pk.is_cards && card == NO_CARD {
                return false;
            }
            SlotKey { pack: pi, ch: ci, tier: ti, card }
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

    /// Record that the selected card was shown: its NEW pulls go to viewed.txt; the sticker stays until you move on.
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
        self.seen_slot = cur;
        let Some(k) = cur else { return };
        let ids: Vec<String> = self
            .coll
            .slot_pulls(k)
            .iter()
            .map(|&i| &self.coll.pulls[i])
            .filter(|p| p.new && !self.viewed.contains(&p.id))
            .map(|p| p.id.clone())
            .collect();
        if !self.opts.readonly {
            mark_viewed(&self.opts.viewed, &ids);
        }
        self.viewed.extend(ids);
    }

    /// Start on the card you pulled most recently.
    pub fn select_latest(&mut self) {
        let last = (0..self.coll.pulls.len()).rev().find_map(|i| self.coll.slot_of[i].map(|k| (i, k)));
        if let Some((i, k)) = last {
            self.jump_to(k, Some(i));
        }
    }

    pub fn reload_if_changed(&mut self) -> bool {
        let m = mtime(&self.opts.log);
        if m == self.log_mtime {
            return false;
        }
        self.log_mtime = m;
        let cur = self.selected();
        let pulls = Self::load_pulls(&self.opts, &self.viewed);
        let packs = std::mem::take(&mut self.coll.packs);
        self.seen_slot = None;
        self.coll = Collection::build(pulls, packs);
        self.slots_key.5 = self.slots_key.5.wrapping_add(1);
        self.slots_key.0 = usize::MAX;
        if let Some(k) = cur {
            self.jump_to(k, None);
        }
        true
    }

    /// The slots of the current pack after filters (cached).
    pub fn slots(&mut self) -> &[SlotKey] {
        let key = (self.pack, self.views[self.pack], self.shiny_only, self.owned_only, self.search.to_lowercase(), self.slots_key.5, self.set_sel[self.pack]);
        if key != self.slots_key {
            self.slots = self.compute_slots(&key.4);
            self.slots_key = key;
        }
        &self.slots
    }

    /// The set the current pack's binder is showing (None: every set).
    pub fn current_set(&self) -> Option<&crate::data::SetDef> {
        let s = *self.set_sel.get(self.pack)?;
        if s == 0 { None } else { self.coll.packs[self.pack].sets.get(s - 1) }
    }

    /// `S`: every set -> each set's checklist in turn -> every set.
    pub fn cycle_set(&mut self, d: isize) {
        let n = self.coll.packs.get(self.pack).map(|p| p.sets.len()).unwrap_or(0) as isize;
        if n == 0 {
            return;
        }
        let s = &mut self.set_sel[self.pack];
        *s = (*s as isize + d).rem_euclid(n + 1) as usize;
        self.sel[self.pack] = 0;
        self.hist = usize::MAX;
        self.dirty = true;
    }

    /// The state words of a slot for the search (query.rs).
    pub fn slot_flags(&self, k: SlotKey) -> crate::query::Flags {
        let st = self.coll.slot_state(k, false);
        crate::query::Flags {
            shiny: self.coll.slot_pulls(k).iter().any(|&i| self.coll.pulls[i].shiny),
            foil: self.coll.packs[k.pack].foil_tier(k.tier),
            new: self.coll.slot_new(k, false),
            pending: st == SlotState::Pending,
            owned: st == SlotState::Owned,
        }
    }

    fn compute_slots(&self, q: &str) -> Vec<SlotKey> {
        let pi = self.pack;
        let Some(p) = self.coll.packs.get(pi) else { return vec![] };
        let terms = crate::query::parse(q);
        let set = self.current_set().map(|s| s.id.clone());
        let keep = |k: SlotKey| {
            (terms.is_empty() || crate::query::matches(&terms, &p.slot_tags(k), self.slot_flags(k)))
                && (!self.owned_only || self.coll.slot_state(k, self.shiny_only) != SlotState::Empty)
        };
        let mut out = Vec::new();
        match self.views[pi] {
            // real cards: one slot per card, set by set in checklist (printed number) order; a set picked with `S`
            // is that set's whole checklist, pulled or not
            View::Set if p.is_cards => {
                let mut ix: Vec<usize> = (0..p.card_list.len()).filter(|&i| set.as_ref().is_none_or(|s| &p.card_list[i].set_id == s)).collect();
                let set_order = |i: usize| p.sets.iter().position(|s| s.id == p.card_list[i].set_id).unwrap_or(usize::MAX);
                ix.sort_by_key(|&i| (set_order(i), p.card_list[i].number_key(), i));
                for i in ix {
                    let c = &p.card_list[i];
                    let k = SlotKey { pack: pi, ch: c.ch, tier: c.tier, card: i as u32 };
                    if keep(k) {
                        out.push(k);
                    }
                }
            }
            View::Set => {
                for tier in 0..p.tiers.len() {
                    for ch in 0..p.chars.len() {
                        let k = SlotKey::legacy(pi, ch, tier);
                        if keep(k) {
                            out.push(k);
                        }
                    }
                }
            }
            View::Dex => {
                for ch in 0..p.chars.len() {
                    // the best card pulled; unowned: the character's lowest-tier card (legacy packs: tier 0)
                    let first = || {
                        let c = (0..p.card_list.len())
                            .filter(|&i| p.card_list[i].ch == ch && set.as_ref().is_none_or(|s| &p.card_list[i].set_id == s))
                            .min_by_key(|&i| p.card_list[i].tier)?;
                        Some(SlotKey { pack: pi, ch, tier: p.card_list[c].tier, card: c as u32 })
                    };
                    let k = match self.coll.best_slot(pi, ch, self.shiny_only) {
                        Some(k) if set.as_ref().is_none_or(|s| p.card_at(k.card).is_some_and(|c| &c.set_id == s)) => k,
                        _ if p.is_cards => match first() {
                            Some(k) => k,
                            None => continue,
                        },
                        _ => SlotKey::legacy(pi, ch, 0),
                    };
                    if keep(k) {
                        out.push(k);
                    }
                }
            }
        }
        out
    }

    pub fn sel_ix(&mut self) -> usize {
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

    pub fn jump_to(&mut self, k: SlotKey, pull: Option<usize>) {
        self.pack = k.pack;
        let dex = self.views[k.pack] == View::Dex;
        let pos = self.slots().iter().position(|s| if dex { s.ch == k.ch } else { *s == k });
        let pos = match pos {
            Some(p) => Some(p),
            None => {
                // filtered out: clear filters and retry
                self.search.clear();
                self.set_sel[k.pack] = 0;
                self.owned_only = false;
                if self.shiny_only && !pull.is_some_and(|i| self.coll.pulls[i].shiny) {
                    self.shiny_only = false;
                }
                self.slots().iter().position(|s| if dex { s.ch == k.ch } else { *s == k })
            }
        };
        if let Some(p) = pos {
            self.sel[k.pack] = p;
        }
        self.hist = pull
            .and_then(|pi| self.coll.slot_pulls(k).iter().position(|&x| x == pi))
            .unwrap_or(usize::MAX);
        self.dirty = true;
    }

    fn move_sel(&mut self, d: isize) {
        let n = self.slots().len() as isize;
        if n == 0 {
            return;
        }
        let s = self.sel_ix() as isize;
        self.sel[self.pack] = (s + d).clamp(0, n - 1) as usize;
        self.hist = usize::MAX;
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
        self.hist = usize::MAX;
    }

    fn move_grid(&mut self, dx: isize, dy: isize) {
        let n = self.slots().len();
        if n == 0 {
            return;
        }
        let s = self.sel_ix();
        let (page, within) = (s / PER_PAGE, s % PER_PAGE);
        let (col, row) = ((within % 3) as isize, (within / 3) as isize);
        let (nc, nr) = (col + dx, row + dy);
        if nc < 0 {
            // off the left edge: previous page, rightmost column
            if page > 0 || self.pages() > 1 {
                self.flip(-1);
                let p = self.sel_ix() / PER_PAGE;
                self.sel[self.pack] = (p * PER_PAGE + row as usize * 3 + 2).min(n - 1);
            }
        } else if nc > 2 || (dx > 0 && s + 1 >= n) {
            self.flip(1);
            let p = self.sel_ix() / PER_PAGE;
            self.sel[self.pack] = (p * PER_PAGE + row as usize * 3).min(n - 1);
        } else if nr < 0 {
            self.move_sel(-3);
        } else if nr > 2 {
            // below the last row: next page, same column
            self.flip(1);
            let p = self.sel_ix() / PER_PAGE;
            self.sel[self.pack] = (p * PER_PAGE + col as usize).min(n - 1);
        } else {
            let t = page * PER_PAGE + nr as usize * 3 + nc as usize;
            if t < n {
                self.sel[self.pack] = t;
            } else if dy > 0 {
                self.flip(1);
                let p = self.sel_ix() / PER_PAGE;
                self.sel[self.pack] = (p * PER_PAGE + col as usize).min(n - 1);
            }
        }
        self.hist = usize::MAX;
    }

    pub fn set_pack(&mut self, p: usize) {
        if p < self.coll.packs.len() && p != self.pack {
            self.pack = p;
            self.hist = usize::MAX;
            self.dirty = true;
        }
    }

    /// Ranked best pulls across all packs: rarest odds first.
    pub fn best_pulls(&self) -> Vec<(usize, f64)> {
        let mut v: Vec<(usize, f64)> = (0..self.coll.pulls.len())
            .filter_map(|i| {
                let k = self.coll.slot_of[i]?;
                let p = &self.coll.pulls[i];
                if !self.coll.packs[k.pack].foil_tier(k.tier) && !p.shiny {
                    return None;
                }
                Some((i, self.coll.packs[k.pack].card_p(k.tier, p.shiny)))
            })
            .collect();
        v.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap().then(b.0.cmp(&a.0)));
        v
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
        if self.help || self.hits.card_art.width == 0 {
            return false;
        }
        let Some(k) = self.selected() else { return false };
        let shiny = self.shiny_only;
        let st = self.coll.slot_state(k, shiny);
        st != SlotState::Empty && crate::card::is_foil(&self.coll.packs[k.pack], k.tier, shiny)
    }

    // ------------------------------------------------------------ input

    pub fn on_event(&mut self, ev: Event) {
        match ev {
            Event::Key(k) if k.kind != KeyEventKind::Release => self.on_key(k),
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
        if k.modifiers.contains(KeyModifiers::CONTROL) && matches!(k.code, KeyCode::Char('c')) {
            self.quit = true;
            return;
        }
        if self.help {
            self.help = false;
            return;
        }
        if self.searching {
            match k.code {
                KeyCode::Esc => {
                    self.searching = false;
                    self.search.clear();
                }
                KeyCode::Enter => self.searching = false,
                KeyCode::Backspace => {
                    self.search.pop();
                }
                KeyCode::Char(c) => {
                    self.search.push(c);
                    self.sel[self.pack] = 0;
                }
                KeyCode::Left | KeyCode::Right | KeyCode::Up | KeyCode::Down => {
                    self.searching = false;
                    self.on_key(k);
                }
                _ => {}
            }
            return;
        }
        match k.code {
            KeyCode::Char('q') => self.quit = true,
            KeyCode::Esc => {
                if !self.search.is_empty() {
                    self.search.clear();
                } else {
                    self.quit = true;
                }
            }
            KeyCode::Char('?') | KeyCode::F(1) => self.help = true,
            KeyCode::Char('/') => {
                self.searching = true;
                self.focus = Focus::Binder;
            }
            KeyCode::Char('s') => self.toggle_shiny(),
            KeyCode::Char('o') => self.owned_only = !self.owned_only,
            KeyCode::Char('v') => self.show_text = !self.show_text,
            KeyCode::Char('S') => self.cycle_set(1),
            KeyCode::Char('d') => {
                let v = &mut self.views[self.pack];
                *v = if *v == View::Set { View::Dex } else { View::Set };
                self.sel[self.pack] = 0;
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
                self.sel[self.pack] = 0;
                self.hist = usize::MAX;
            }
            KeyCode::End | KeyCode::Char('G') => {
                let n = self.slots().len();
                self.sel[self.pack] = n.saturating_sub(1);
                self.hist = usize::MAX;
            }
            _ => match self.focus {
                Focus::Binder => match k.code {
                    KeyCode::Left | KeyCode::Char('h') => self.move_grid(-1, 0),
                    KeyCode::Right | KeyCode::Char('l') => self.move_grid(1, 0),
                    KeyCode::Up | KeyCode::Char('k') => self.move_grid(0, -1),
                    KeyCode::Down | KeyCode::Char('j') => self.move_grid(0, 1),
                    _ => {}
                },
                Focus::Card => {
                    let n = self.selected().map(|s| self.coll.slot_pulls(s).len()).unwrap_or(0);
                    let cur = if self.hist >= n { n.saturating_sub(1) } else { self.hist };
                    match k.code {
                        KeyCode::Left | KeyCode::Up | KeyCode::Char('h') | KeyCode::Char('k') => self.hist = cur.saturating_sub(1),
                        KeyCode::Right | KeyCode::Down | KeyCode::Char('l') | KeyCode::Char('j') => {
                            self.hist = (cur + 1).min(n.saturating_sub(1))
                        }
                        _ => {}
                    }
                }
                Focus::Stats => {
                    let n = self.best_pulls().len();
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
        match m.kind {
            MouseEventKind::ScrollDown | MouseEventKind::ScrollUp => {
                let d = if m.kind == MouseEventKind::ScrollDown { 1 } else { -1 };
                if self.hits.stats.contains(pos) {
                    let n = self.best_pulls().len();
                    self.best_sel = (self.best_sel as isize + d).clamp(0, n.saturating_sub(1) as isize) as usize;
                } else if self.hits.card.contains(pos) {
                    let n = self.selected().map(|s| self.coll.slot_pulls(s).len()).unwrap_or(0);
                    let cur = if self.hist >= n { n.saturating_sub(1) } else { self.hist };
                    self.hist = (cur as isize + d).clamp(0, n.saturating_sub(1) as isize) as usize;
                } else {
                    self.flip(d);
                }
                self.dirty = true;
            }
            MouseEventKind::Down(MouseButton::Left) => {
                self.dirty = true;
                if self.help {
                    self.help = false;
                    return;
                }
                if let Some(&(_, _, _, p)) = self.hits.tabs.iter().find(|t| t.2 == m.row as i32 && (t.0..=t.1).contains(&(m.column as i32))) {
                    if p < self.coll.packs.len() {
                        self.set_pack(p);
                    } else {
                        self.cycle_set(1);
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
                    self.sel[self.pack] = i;
                    self.hist = usize::MAX;
                    self.focus = Focus::Binder;
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
            _ => {}
        }
    }

    /// Shiny-only on/off; landing on an owned shiny when there is one.
    pub fn toggle_shiny(&mut self) {
        self.shiny_only = !self.shiny_only;
        self.hist = usize::MAX;
        if self.shiny_only {
            let cur = self.selected();
            if cur.is_none_or(|k| self.coll.slot_state(k, true) == SlotState::Empty) {
                let shiny = self.shiny_only;
                let list = self.slots().to_vec();
                let hit = list.iter().position(|k| self.coll.slot_state(*k, shiny) != SlotState::Empty);
                if let Some(i) = hit {
                    self.sel[self.pack] = i;
                }
            }
        }
        self.dirty = true;
    }

    pub fn pending_count(&self) -> usize {
        self.coll.pulls.iter().filter(|p| p.status == Status::Pending).count()
    }
}
