//! Layout and panels. `render` paints a full frame; `render_card` repaints only the big card
//! (the animation path: the rest of the frame is reused from the last full paint).

use crate::app::{App, Focus, PER_PAGE, View};
use crate::card::{self, Card};
use crate::cardtext;
use crate::color::{Rgb, darken, grad, lighten, mix, rgb};
use crate::data::{self, SlotKey, SlotState};
use crate::draw::{Seg, Titles, braille, fill, meter, panel, put, puts, seg, segb, trunc, width};
use crate::theme::{THEMES, Theme};
use ratatui::buffer::Buffer;
use ratatui::layout::Rect;

const SUP: [&str; 9] = ["¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"];

#[derive(Default, Clone, Copy)]
pub struct Lay {
    pub header: Option<Rect>,
    pub binder: Option<Rect>,
    pub card: Option<Rect>,
    pub packs: Option<Rect>,
    pub tiers: Option<Rect>,
    pub activity: Option<Rect>,
    pub best: Option<Rect>,
}

fn rect(x: u16, y: u16, w: u16, h: u16) -> Option<Rect> {
    if w >= 8 && h >= 3 { Some(Rect::new(x, y, w, h)) } else { None }
}

pub fn layout(app: &App, a: Rect) -> Lay {
    let (w, h) = (a.width, a.height);
    let mut l = Lay::default();
    let hh = if h >= 18 { 2 } else { 1 };
    l.header = Some(Rect::new(a.x, a.y, w, hh));
    let (by, bh) = (a.y + hh, h.saturating_sub(hh));
    let ntiers = app.coll.packs.get(app.pack).map(|p| p.live_tiers().len()).unwrap_or(4) as u16;
    let npacks = app.coll.packs.len() as u16;

    // stats stack for a column of width cw starting at y with height ch (compact/tiny modes)
    let stack = |l: &mut Lay, x: u16, y: u16, cw: u16, ch: u16| {
        let pk = (npacks + 2).min(ch);
        l.packs = rect(x, y, cw, pk);
        let rem = ch - pk;
        let th = (ntiers + 3).min(rem);
        l.tiers = rect(x, y + pk, cw, th);
        let rem2 = rem - th;
        if rem2 >= 10 {
            let ah = rem2 / 2;
            l.activity = rect(x, y + pk + th, cw, ah);
            l.best = rect(x, y + pk + th + ah, cw, rem2 - ah);
        } else {
            l.best = rect(x, y + pk + th, cw, rem2);
        }
    };

    if w >= 100 && h >= 30 {
        // binder: 3x3 slots, each ~5:3 cells (a card's shape in half-block pixels)
        let slot_h = (bh.saturating_sub(2)) / 3;
        let slot_w = (slot_h * 5 / 3).clamp(14, 34);
        let bw = (3 * slot_w + 2 + 2).min(w * 56 / 100);
        l.binder = rect(a.x, by, bw, bh);
        let (rx, rw) = (a.x + bw, w - bw);
        // right column: the card gets the lion's share, stats take the rest
        let tiers_h = ntiers + 3;
        let low_min = 8;
        // never taller than the biggest art (16 rows) + frame + info needs
        let card_h = bh.saturating_sub(tiers_h + low_min).clamp(14, 40).min(bh * 62 / 100).max(bh.saturating_sub(tiers_h + low_min + 12)).min(27);
        // the text half (v) needs the height: the card panel takes the whole column but the tiers
        let card_h = if app.show_text { bh.saturating_sub(tiers_h).max(card_h) } else { card_h };
        l.card = rect(rx, by, rw, card_h);
        let rem = bh - card_h;
        let big = rw >= 84 && npacks > 0;
        if big {
            // wide right column: packs beside tiers
            let pw = rw * 38 / 100;
            let row_a = (npacks.max(ntiers + 1) + 2).min(rem);
            l.packs = rect(rx, by + card_h, pw, row_a);
            l.tiers = rect(rx + pw, by + card_h, rw - pw, row_a);
            let rb = rem - row_a;
            let aw = rw * 55 / 100;
            l.activity = rect(rx, by + card_h + row_a, aw, rb);
            l.best = rect(rx + aw, by + card_h + row_a, rw - aw, rb);
        } else {
            let th = tiers_h.min(rem);
            l.tiers = rect(rx, by + card_h, rw, th);
            let rb = rem - th;
            let aw = rw * 50 / 100;
            l.activity = rect(rx, by + card_h + th, aw, rb);
            l.best = rect(rx + aw, by + card_h + th, rw - aw, rb);
        }
    } else if w >= 60 {
        let bw = (w * 56 / 100).max(34);
        l.binder = rect(a.x, by, bw, bh);
        let (rx, rw) = (a.x + bw, w - bw);
        if app.compact_right == Focus::Stats {
            stack(&mut l, rx, by, rw, bh);
        } else {
            l.card = rect(rx, by, rw, bh);
        }
    } else {
        match app.focus {
            Focus::Binder => l.binder = rect(a.x, by, w, bh),
            Focus::Card => l.card = rect(a.x, by, w, bh),
            Focus::Stats => stack(&mut l, a.x, by, w, bh),
        }
    }
    l
}

fn box_col(t: &Theme, base: Rgb, focused: bool) -> Rgb {
    if focused { mix(base, t.box_focus, 0.55) } else { base }
}

// ---------------------------------------------------------------- stats

#[allow(dead_code)]
struct Stats {
    total: usize,
    foils: usize,
    shinies: usize,
    unique: usize,
    slots_all: usize,
    pending: usize,
    last: Option<usize>,
    streak: i64,
    drought: usize,
    today: usize,
}

fn stats(app: &App) -> Stats {
    let c = &app.coll;
    let mut unique = 0;
    let mut slots_all = 0;
    for (pi, p) in c.packs.iter().enumerate() {
        slots_all += p.slot_count();
        unique += c.by_slot.keys().filter(|k| k.pack == pi && c.slot_state(**k, false) == SlotState::Owned).count();
    }
    let foil = |k: &Option<SlotKey>| k.is_some_and(|k| c.packs[k.pack].foil_tier(k.tier));
    let foils = c.slot_of.iter().filter(|k| foil(k)).count();
    let days: std::collections::BTreeSet<i64> = c.pulls.iter().map(|p| p.ts.div_euclid(86400)).collect();
    let today = app.now.div_euclid(86400);
    let mut d = if days.contains(&today) { today } else { today - 1 };
    let mut streak = 0;
    while days.contains(&d) {
        streak += 1;
        d -= 1;
    }
    let drought = c.slot_of.iter().rev().take_while(|k| !foil(k)).count();
    Stats {
        total: c.pulls.len(),
        foils,
        shinies: c.pulls.iter().filter(|p| p.shiny).count(),
        unique,
        slots_all,
        pending: app.pending_count(),
        last: if c.pulls.is_empty() { None } else { Some(c.pulls.len() - 1) },
        streak,
        drought,
        today: c.pulls.iter().filter(|p| p.ts.div_euclid(86400) == today).count(),
    }
}

/// Completion of a pack: "set" (char x tier slots) for small packs, "dex" (characters caught) for big ones.
fn pack_completion(app: &App, pi: usize) -> (&'static str, usize, usize) {
    let c = &app.coll;
    let p = &c.packs[pi];
    if p.is_big() {
        let caught = (0..p.chars.len()).filter(|&ch| c.best_slot(pi, ch, false).is_some()).count();
        ("dex", caught, p.chars.len())
    } else {
        let owned = c.by_slot.keys().filter(|k| k.pack == pi && c.slot_state(**k, false) != SlotState::Empty).count();
        ("set", owned, p.slot_count())
    }
}

/// A set's checklist: its cards in pack.json, and how many you have (or have pending).
fn set_completion(app: &App, pi: usize, set: &str) -> (&'static str, usize, usize) {
    let p = &app.coll.packs[pi];
    let cards: Vec<usize> = (0..p.card_list.len()).filter(|&i| p.card_list[i].set_id == set).collect();
    let owned = cards
        .iter()
        .filter(|&&i| {
            let c = &p.card_list[i];
            app.coll.slot_state(SlotKey { pack: pi, ch: c.ch, tier: c.tier, card: i as u32 }, false) != SlotState::Empty
        })
        .count();
    ("set", owned, cards.len())
}

fn odds(p: f64) -> String {
    if p <= 0.0 {
        return "never".into();
    }
    let n = 1.0 / p;
    if n < 1.05 {
        "always".into()
    } else if n < 10.0 {
        format!("1 in {:.1}", n)
    } else if n < 10000.0 {
        format!("1 in {}", group(n.round() as u64))
    } else {
        format!("1 in {:.0}k", n / 1000.0)
    }
}

fn odds_short(p: f64) -> String {
    let n = 1.0 / p.max(1e-12);
    if n >= 10000.0 { format!("1/{:.0}k", n / 1000.0) } else { format!("1/{}", n.round() as u64) }
}

fn group(n: u64) -> String {
    let s = n.to_string();
    let mut out = String::new();
    for (i, c) in s.chars().enumerate() {
        if i > 0 && (s.len() - i) % 3 == 0 {
            out.push(',');
        }
        out.push(c);
    }
    out
}

// ---------------------------------------------------------------- full frame

pub fn render(app: &mut App, buf: &mut Buffer) {
    let area = buf.area;
    let theme = THEMES[app.theme].clone();
    fill(buf, area, theme.bg);
    app.hits = Default::default();
    if area.width < 20 || area.height < 6 {
        puts(buf, 0, 0, "binder: terminal too small", theme.fg, theme.bg, false, area.width as usize);
        return;
    }
    let lay = layout(app, area);
    let st = stats(app);
    if let Some(r) = lay.header {
        header(app, buf, r, &theme, &st);
    }
    if let Some(r) = lay.binder {
        binder(app, buf, r, &theme);
    }
    if let Some(r) = lay.card {
        card_panel(app, buf, r, &theme);
    }
    let stats_focus = app.focus == Focus::Stats;
    let mut stats_rect: Option<Rect> = None;
    let mut grow = |r: Rect| stats_rect = Some(stats_rect.map_or(r, |s: Rect| s.union(r)));
    if let Some(r) = lay.packs {
        packs_panel(app, buf, r, &theme, stats_focus);
        grow(r);
    }
    if let Some(r) = lay.tiers {
        tiers_panel(app, buf, r, &theme, stats_focus);
        grow(r);
    }
    if let Some(r) = lay.activity {
        activity_panel(app, buf, r, &theme, stats_focus);
        grow(r);
    }
    if let Some(r) = lay.best {
        best_panel(app, buf, r, &theme, stats_focus);
        grow(r);
    }
    app.hits.stats = stats_rect.unwrap_or_default();
    if app.help {
        help(buf, area, &theme);
    }
}

// ---------------------------------------------------------------- header

fn header(app: &App, buf: &mut Buffer, r: Rect, t: &Theme, st: &Stats) {
    let (x0, y0, w) = (r.x as i32, r.y as i32, r.width as usize);
    // row 0: logo, totals (dropped from the right when narrow), clock
    let logo = " ◓ pokeshell";
    for (i, ch) in logo.chars().enumerate() {
        let c = grad(&t.meter, i as f32 / (logo.chars().count() - 1) as f32);
        crate::draw::putc(buf, x0 + i as i32, y0, ch, Some(lighten(c, 0.2)), None, true);
    }
    let mut x = x0 + width(logo) as i32;
    x += puts(buf, x, y0, " binder", t.dim, None, false, 10) as i32 + 3;
    let clock = format!("{} {}  ", data::weekday(app.now), data::date_short(app.now));
    let time = format!("{} ", data::hhmm(app.now));
    let right_w = width(&clock) + width(&time) + 1;
    let pend_c = if st.pending > 0 { t.warn } else { t.dim };
    let mut chips: Vec<Vec<(String, Rgb, bool)>> = vec![
        vec![(st.total.to_string(), t.title, true), (" pulls".into(), t.dim, false)],
        vec![(st.unique.to_string(), t.title, true), (" cards".into(), t.dim, false)],
        vec![(st.foils.to_string(), t.accent, true), (" foils".into(), t.dim, false)],
        vec![("✦ ".into(), t.hi, false), (st.shinies.to_string(), t.hi, true), (" shiny".into(), t.dim, false)],
        vec![("◌ ".into(), pend_c, false), (st.pending.to_string(), pend_c, true), (" pending".into(), t.dim, false)],
        vec![(app.coll.new_count().to_string(), if app.coll.new_count() > 0 { rgb(0xff5fa2) } else { t.dim }, true), (" new".into(), t.dim, false)],
        vec![("streak ".into(), t.dim, false), (format!("{}d", st.streak), t.good, true)],
        vec![("drought ".into(), t.dim, false), (st.drought.to_string(), if st.drought > 10 { t.warn } else { t.title }, true)],
    ];
    if app.coll.hidden > 0 {
        // pulls that no longer resolve to a current card (retired art): left out, never deleted from pulls.log
        chips.push(vec![(app.coll.hidden.to_string(), t.dim, true), (" retired".into(), t.faint, false)]);
    }
    for (i, chip) in chips.iter().enumerate() {
        let need: usize = chip.iter().map(|c| width(&c.0)).sum::<usize>() + 3;
        if (x - x0) as usize + need + right_w + 1 > w {
            break;
        }
        if i > 0 {
            x += puts(buf, x, y0, " · ", t.faint, None, false, 3) as i32;
        }
        for (s, c, b) in chip {
            x += puts(buf, x, y0, s, *c, None, *b, 20) as i32;
        }
    }
    let rx = x0 + w as i32 - right_w as i32;
    puts(buf, rx, y0, &clock, t.dim, None, false, 20);
    puts(buf, rx + width(&clock) as i32, y0, &time, t.title, None, true, 8);
    if r.height < 2 {
        return;
    }
    // row 1: a completion meter per pack (btop's cpu-core row), then the last pull, then help
    let y = y0 + 1;
    let hint_w = 8;
    let hint_x = x0 + w as i32 - hint_w;
    puts(buf, hint_x + 1, y, "?", t.hi, None, true, 1);
    puts(buf, hint_x + 2, y, " help ", t.dim, None, false, 6);
    let mut last_segs: Vec<(String, Rgb, bool)> = vec![];
    if let Some(li) = st.last {
        let p = &app.coll.pulls[li];
        let (name, tier, tc) = match app.coll.slot_of[li] {
            Some(k) => {
                let pk = &app.coll.packs[k.pack];
                (pk.name_for(k.ch, k.card), pk.tiers[k.tier].label.clone(), pk.tiers[k.tier].color)
            }
            None => (p.ch.clone(), p.tier.clone(), t.fg),
        };
        last_segs = vec![
            ("last ".into(), t.dim, false),
            (format!("{}{}", if p.shiny { "✦ " } else { "" }, name), t.title, true),
            (format!(" {tier}"), tc, false),
            (format!(" {}", data::ago(app.now - p.ts)), t.dim, false),
        ];
    }
    let last_w: usize = last_segs.iter().map(|s| width(&s.0)).sum();
    let avail = (hint_x - x0 - 1) as usize;
    let show_last = avail >= last_w + 3 * 18;
    let meters_w = if show_last { avail - last_w - 2 } else { avail };
    let np = app.coll.packs.len().max(1);
    let per = meters_w / np;
    let mut x = x0 + 1;
    for (i, p) in app.coll.packs.iter().enumerate() {
        let (_, have, tot) = pack_completion(app, i);
        let frac = have as f32 / tot.max(1) as f32;
        let active = i == app.pack;
        let pct = format!("{:>3.0}%", frac * 100.0);
        let name_w = width(&p.id).min(9).min(per.saturating_sub(12)).max(3);
        let mw = per.saturating_sub(name_w + 1 + 1 + pct.len() + 2).min(24);
        if mw < 3 {
            break;
        }
        puts(buf, x, y, SUP.get(i).copied().unwrap_or(" "), if active { t.hi } else { t.faint }, None, false, 1);
        let nm: String = p.id.chars().take(name_w).collect();
        puts(buf, x + 1, y, &nm, if active { t.title } else { t.dim }, None, active, name_w);
        let mx = x + 1 + name_w as i32 + 1;
        meter(buf, mx, y, mw, frac.max(0.001), &t.meter, t.meter_bg);
        puts(buf, mx + mw as i32 + 1, y, &pct, if active { t.title } else { t.fg }, None, active, 4);
        x += per as i32;
    }
    if show_last {
        let mut lx = hint_x - 1 - last_w as i32;
        for (s, c, b) in last_segs {
            lx += puts(buf, lx, y, &s, c, None, b, 40) as i32;
        }
    }
}

// ---------------------------------------------------------------- binder

fn binder(app: &mut App, buf: &mut Buffer, r: Rect, t: &Theme) {
    let focused = app.focus == Focus::Binder;
    let line = box_col(t, t.box_binder, focused);
    let mut ti = Titles::new();
    let wide = r.width >= 56;
    for (i, p) in app.coll.packs.iter().enumerate() {
        let active = i == app.pack;
        let label = if wide || active { p.id.clone() } else { p.id.chars().take(3).collect() };
        let mut g = vec![seg(SUP.get(i).copied().unwrap_or(""), if active { t.hi } else { t.dim })];
        g.push(if active { segb(label, t.title) } else { seg(label, t.dim) });
        ti.tl.push(g);
    }
    // real-card packs: the set tab (S or a click cycles: every set / one set's checklist)
    if !app.coll.packs[app.pack].sets.is_empty() {
        let (lab, c) = match app.current_set() {
            Some(s) => (trunc(&s.name, if wide { 22 } else { 10 }), t.title),
            None => ("all sets".to_string(), t.dim),
        };
        ti.tl.push(vec![seg("set ", t.faint), segb(lab, c)]);
    }
    let view = app.views[app.pack];
    let mut tr = vec![seg(if view == View::Set { "set" } else { "dex" }, t.accent)];
    if app.shiny_only {
        tr.push(segb(" ✦shiny", t.hi));
    }
    if app.owned_only {
        tr.push(seg(" owned", t.good));
    }
    ti.tr.push(tr);
    let n = app.slots().len();
    let pages = app.pages();
    let page = app.page();
    let sel = app.sel_ix();
    let (_, owned, total) = match app.current_set().map(|s| s.id.clone()) {
        Some(set) => set_completion(app, app.pack, &set),
        None => pack_completion(app, app.pack),
    };
    if app.searching || !app.search.is_empty() {
        let mut g = vec![seg("/", t.hi), segb(app.search.clone(), t.title)];
        if app.searching {
            g.push(seg("▏", t.hi));
        }
        g.push(seg(format!(" {n}"), t.dim));
        ti.bl.push(g);
    } else {
        ti.bl.push(vec![segb(owned.to_string(), t.title), seg(format!("/{total}"), t.dim)]);
    }
    ti.br.push(vec![seg("◂ ", t.dim), segb(format!("{}", page + 1), t.title), seg(format!("/{pages}"), t.dim), seg(" ▸", t.dim)]);
    let (tabs, inner) = panel(buf, r, line, t.bg, &ti);
    for (i, (a, b)) in tabs.iter().enumerate() {
        app.hits.tabs.push((*a, *b, r.y as i32, i));
    }
    app.hits.binder = r;
    // page arrows on the bottom border (click targets)
    let bw = width(&format!("◂ {}/{pages} ▸", page + 1)) as u16;
    let bx = r.x + r.width - 2 - bw;
    app.hits.prev_page = Some(Rect::new(bx, r.y + r.height - 1, 2, 1));
    app.hits.next_page = Some(Rect::new(bx + bw - 2, r.y + r.height - 1, 2, 1));

    if n == 0 {
        let msg = if app.shiny_only && app.coll.packs[app.pack].shiny <= 0.0 {
            "no shinies in this pack"
        } else if !app.search.is_empty() {
            "no cards match"
        } else {
            "no cards"
        };
        let x = inner.x as i32 + (inner.width as i32 - width(msg) as i32) / 2;
        puts(buf, x, inner.y as i32 + inner.height as i32 / 2, msg, t.dim, None, false, 40);
        return;
    }
    let sw = (inner.width.saturating_sub(2)) / 3;
    let sh = inner.height / 3;
    if sw < 6 || sh < 3 {
        return;
    }
    let ox = inner.x + (inner.width - (sw * 3 + 2)) / 2;
    let oy = inner.y + (inner.height - sh * 3) / 2;
    let slots: Vec<SlotKey> = app.slots().iter().skip(page * PER_PAGE).take(PER_PAGE).copied().collect();
    let theme = t.clone();
    for (i, k) in slots.iter().enumerate() {
        let (cx, cy) = ((i % 3) as u16, (i / 3) as u16);
        let sr = Rect::new(ox + cx * (sw + 1), oy + cy * sh, sw, sh);
        let idx = page * PER_PAGE + i;
        app.hits.slots.push((sr, idx));
        let pack = &app.coll.packs[k.pack];
        let state = app.coll.slot_state(*k, app.shiny_only);
        let count = app.coll.slot_pulls(*k).iter().filter(|&&pi| !app.shiny_only || app.coll.pulls[pi].shiny).count();
        let shiny_owned = app.shiny_only || app.coll.slot_pulls(*k).iter().any(|&pi| app.coll.pulls[pi].shiny);
        let tier = &pack.tiers[k.tier];
        let (fw, fh) = match (&tier.frame, state) {
            (_, SlotState::Empty) => (sw.saturating_sub(4), sh.saturating_sub(2)),
            _ => (sw.saturating_sub(2), sh.saturating_sub(2)),
        };
        // empty slots show the base art's silhouette (full-art tiers would be solid rectangles)
        // empty slots show a silhouette: the base art (legacy packs; full-art tiers would be solid) or the slot's card
        let art = if state == SlotState::Empty && !pack.is_cards { pack.tiers[0].art.clone() } else { pack.art_at(*k) };
        // (a real card's art is a whole scene, whose silhouette would be a solid block: empty real-card slots show "?")
        let img = if state == SlotState::Empty && pack.is_cards {
            None
        } else {
            app.art.thumb(pack, &pack.chars[k.ch], &art, shiny_owned && state != SlotState::Empty, fw as usize, fh as usize)
        };
        let c = Card {
            pack,
            ch: k.ch,
            tier: k.tier,
            shiny: shiny_owned && state != SlotState::Empty,
            state,
            selected: idx == sel,
            count,
            thumb: true,
            new: app.coll.slot_new(*k, app.shiny_only),
            card: k.card,
        };
        card::draw(buf, sr, &c, img.as_deref(), &theme);
    }
}

// ---------------------------------------------------------------- card detail

/// Which pull of the selected slot the detail panel shows (history cursor, newest by default).
fn shown_pull(app: &App, k: SlotKey) -> (Vec<usize>, Option<usize>) {
    let shiny = app.shiny_only;
    let list: Vec<usize> = app.coll.slot_pulls(k).iter().copied().filter(|&i| !shiny || app.coll.pulls[i].shiny).collect();
    if list.is_empty() {
        return (list, None);
    }
    let h = if app.hist >= list.len() { list.len() - 1 } else { app.hist };
    (list.clone(), Some(h))
}

fn card_panel(app: &mut App, buf: &mut Buffer, r: Rect, t: &Theme) {
    let focused = app.focus == Focus::Card;
    let line = box_col(t, t.box_card, focused);
    let sel = app.sel_ix();
    let n = app.slots().len();
    let key = app.selected();
    let mut ti = Titles::new();
    ti.tl.push(vec![segb("card", t.title)]);
    if let Some(k) = key {
        let p = &app.coll.packs[k.pack];
        ti.tr.push(vec![seg(p.name.clone(), t.dim), seg(format!(" {}/{}", sel + 1, n), t.faint)]);
        let (list, h) = shown_pull(app, k);
        if list.len() > 1 {
            let h = h.unwrap_or(0);
            ti.bl.push(vec![seg("◂ ", t.dim), seg("pull ", t.dim), segb(format!("{}", h + 1), t.title), seg(format!("/{}", list.len()), t.dim), seg(" ▸", t.dim)]);
        }
    }
    let (_, inner) = panel(buf, r, line, t.bg, &ti);
    app.hits.card = r;
    let Some(k) = key else {
        puts(buf, inner.x as i32 + 2, inner.y as i32 + 1, "nothing selected", t.dim, None, false, 30);
        return;
    };
    // info block: beside the card when there is room, else under it
    let side = inner.width >= 84;
    // with the text half showing (v), it gets the room and the info shrinks to its status line
    let info_rows: u16 = if side { 0 } else if app.show_text { 1 } else if inner.height >= 24 { 4 } else if inner.height >= 15 { 3 } else { 2 };
    let info_w: u16 = if side { 30 } else { 0 };
    let area = Rect::new(inner.x, inner.y, inner.width - info_w, inner.height - info_rows);
    let (cr, stack_h) = big_card(app, buf, area, t, k, if side { 0 } else { info_rows + 1 });
    app.hits.card_art = cr;
    let info = if side {
        Rect::new(inner.x + inner.width - info_w, inner.y + 1, info_w - 1, inner.height - 1)
    } else {
        let iy = (cr.y + stack_h + 1).min(inner.y + inner.height - info_rows);
        Rect::new(inner.x + 1, iy, inner.width - 2, info_rows)
    };
    card_info(app, buf, info, t, k, side);
}

/// Draw the selected card as big as fits in `area`; returns its rect and the height of the card plus its text
/// half. With `v` on and card data for it
/// (docs/CARD_FORMAT.md), the text half stacks under the art like a real card and the art shrinks to make room.
fn big_card(app: &mut App, buf: &mut Buffer, area: Rect, t: &Theme, k: SlotKey, below: u16) -> (Rect, u16) {
    let state = app.coll.slot_state(k, app.shiny_only);
    let (list, h) = shown_pull(app, k);
    let shown = h.map(|h| list[h]);
    let shiny = shown.is_some_and(|i| app.coll.pulls[i].shiny) || (app.shiny_only && state != SlotState::Empty);
    // (the text half shows for any card with card data, pulled or not: a set checklist can be read too)
    let text = if app.show_text { app.card_text(k) } else { None };
    let new = app.coll.slot_new(k, app.shiny_only);
    let pack = &app.coll.packs[k.pack];
    let tier = &pack.tiers[k.tier];
    let art = pack.art_at(k);
    let (pw, ph) = card::frame_pad(&tier.frame, false);
    let aw = area.width.saturating_sub(2) as usize;
    let c = Card { pack, ch: k.ch, tier: k.tier, shiny, state, selected: false, count: list.len(), thumb: false, new, card: k.card };
    // the art as big as fits over `reserve` rows kept free under the card
    let place = |reserve: u16| {
        let ah = area.height.saturating_sub(reserve) as usize;
        let fit = (aw.saturating_sub(pw), ah.saturating_sub(ph).max(2));
        // (an empty real-card slot shows "?": its scene's silhouette would be a solid block)
        let img = if state == SlotState::Empty && pack.is_cards { None } else { app.art.fitted(pack, &pack.chars[k.ch], &art, shiny, fit.0, fit.1) };
        let (iw, ir) = img.as_ref().map(|i| (i.w, i.rows())).unwrap_or((16, 8));
        let (cw, ch) = card::card_size(&c, iw, ir);
        (fit, img, cw.min(area.width), ch.min(area.height))
    };
    let (mut fit, mut img, mut cw, mut ch) = place(0);
    let mut th = 0u16;
    let text_w = |cw: u16| cw.max(34).min(area.width);
    if let Some(v) = text.as_deref() {
        // the text half's height depends on its width (the card's), which depends on the art's height: settle it
        for _ in 0..3 {
            th = cardtext::height(v, text_w(cw), t);
            if ch + th <= area.height {
                break;
            }
            let min_art = (ph as u16 + 6).min(area.height);
            let reserve = th.min(area.height.saturating_sub(min_art));
            (fit, img, cw, ch) = place(reserve);
        }
        th = th.min(area.height.saturating_sub(ch));
    } else if app.show_text && area.height > ch {
        th = 1; // "no card text" note
    }
    // center the card (and its text half) together with the info block under it
    let slack = (area.height + below).saturating_sub(ch + th + below);
    let cy = area.y + (slack / 2).min(area.height - ch - th);
    let cr = Rect::new(area.x + (area.width - cw) / 2, cy, cw, ch);
    // clear the region (animation repaints land here)
    fill(buf, area, t.bg);
    card::draw(buf, cr, &c, img.as_deref(), t);
    if state == SlotState::Owned && card::is_foil(pack, k.tier, shiny) {
        let phase = app.anim_phase();
        card::shimmer(buf, cr, &tier.frame, shiny, phase);
    }
    if let Some(v) = text.as_deref() {
        if th >= 3 {
            let tw = text_w(cw);
            let tr = Rect::new(area.x + (area.width - tw) / 2, cy + ch, tw, th);
            let line = if state == SlotState::Pending { t.faint } else { tier.color };
            cardtext::draw(buf, tr, v, line, t);
        }
    } else if th == 1 {
        let note = "no card text for this card (v)";
        puts(buf, area.x as i32 + (area.width as i32 - width(note) as i32).max(0) / 2, (cy + ch) as i32, note, t.faint, None, false, area.width as usize);
    }
    app.hits.card_fit = fit;
    (cr, ch + th)
}

/// Animation path: repaint only the big card.
pub fn render_card(app: &mut App, buf: &mut Buffer) {
    let r = app.hits.card_art;
    if r.width == 0 {
        return;
    }
    let Some(k) = app.selected() else { return };
    let t = THEMES[app.theme].clone();
    // the card area is centered in its region; repaint just the card rect (same size every frame)
    let pack = &app.coll.packs[k.pack];
    let tier = &pack.tiers[k.tier];
    let state = app.coll.slot_state(k, app.shiny_only);
    let (list, h) = shown_pull(app, k);
    let shiny = h.is_some_and(|h| app.coll.pulls[list[h]].shiny) || (app.shiny_only && state != SlotState::Empty);
    let fit = app.hits.card_fit;
    let art = pack.art_at(k);
    let img = if state == SlotState::Empty && pack.is_cards { None } else { app.art.fitted(pack, &pack.chars[k.ch], &art, shiny, fit.0, fit.1) };
    let new = app.coll.slot_new(k, app.shiny_only);
    let c = Card { pack, ch: k.ch, tier: k.tier, shiny, state, selected: false, count: list.len(), thumb: false, new, card: k.card };
    card::draw(buf, r, &c, img.as_deref(), &t);
    if state == SlotState::Owned && card::is_foil(pack, k.tier, shiny) {
        card::shimmer(buf, r, &tier.frame, shiny, app.anim_phase());
    }
}

fn card_info(app: &mut App, buf: &mut Buffer, r: Rect, t: &Theme, k: SlotKey, side: bool) {
    let state = app.coll.slot_state(k, app.shiny_only);
    let (list, h) = shown_pull(app, k);
    let pack = &app.coll.packs[k.pack];
    let tier = &pack.tiers[k.tier];
    let shown = h.map(|h| &app.coll.pulls[list[h]]);
    let shiny = shown.is_some_and(|p| p.shiny) || app.shiny_only;
    let (x0, y0, w) = (r.x as i32, r.y as i32, r.width as usize);
    let (badge, bc): (String, Rgb) = match state {
        SlotState::Owned if app.coll.slot_new(k, app.shiny_only) => ("● collected · NEW".into(), t.good),
        SlotState::Owned => ("● collected".into(), t.good),
        SlotState::Pending => ("◌ pending · use its tab to earn it".into(), t.warn),
        SlotState::Empty => ("○ not pulled yet".into(), t.dim),
    };
    let first = list.first().map(|&i| data::when(app.coll.pulls[i].ts, app.now));
    let last = list.last().map(|&i| data::when(app.coll.pulls[i].ts, app.now));
    let mut skins: Vec<&str> = list.iter().map(|&i| app.coll.pulls[i].skin.as_str()).filter(|s| !s.is_empty()).collect();
    skins.dedup();
    let cp = pack.card_p(k.tier, shiny);
    let tp = pack.tier_p(k.tier);
    // a real card's tags (search them with `/`: set:swsh7 rarity:"rare rainbow" type:water ...)
    let card = pack.card_at(k.card).cloned();
    let kinds = card.as_ref().map(|c| c.types.iter().chain(c.subtypes.iter()).cloned().collect::<Vec<_>>().join(" · ")).unwrap_or_default();
    if side {
        let mut tag_rows: Vec<(&str, String, Rgb, bool)> = vec![];
        if let Some(c) = &card {
            let set = if c.set_name.is_empty() { c.set_id.clone() } else { format!("{} ({})", c.set_name, c.set_id) };
            tag_rows.push(("set", set, t.fg, false));
            if !c.rarity.is_empty() {
                tag_rows.push(("rarity", c.rarity.clone(), tier.color, false));
            }
            if !kinds.is_empty() {
                tag_rows.push(("kind", kinds.clone(), t.fg, false));
            }
            if !c.artist.is_empty() {
                tag_rows.push(("artist", c.artist.clone(), t.dim, false));
            }
        }
        let rows: Vec<(&str, String, Rgb, bool)> = vec![
            ("", pack.name_for(k.ch, k.card), t.title, true),
            ("", format!("{} {}", pack.tag_for(k.ch, k.card), if shiny { "✦ shiny" } else { "" }), t.dim, false),
            ("", String::new(), t.fg, false),
            ("status", badge.clone(), bc, true),
            ("tier", tier.label.clone(), tier.color, true),
        ];
        let rows: Vec<(&str, String, Rgb, bool)> = rows.into_iter().chain(tag_rows).chain(vec![
            ("pulls", if list.is_empty() { "-".into() } else { format!("×{}", list.len()) }, t.title, true),
            ("first", first.clone().unwrap_or("-".into()), t.fg, false),
            ("last", last.clone().unwrap_or("-".into()), t.fg, false),
            ("skin", shown.map(|p| if p.skin.is_empty() { "—".to_string() } else { p.skin.clone() }).unwrap_or("-".into()), t.accent, false),
            ("seen", if skins.is_empty() { "-".into() } else { skins.join(", ") }, t.dim, false),
            ("", String::new(), t.fg, false),
            ("odds", odds(cp), t.hi, true),
            ("tier", odds(tp), t.fg, false),
            ("rolls", if pack.is_cards { format!("shiny {}", if pack.shiny > 0.0 { odds_short(pack.shiny) } else { "-".into() }) } else { format!("foil {:.0}% · shiny {}", pack.foil * 100.0, if pack.shiny > 0.0 { odds_short(pack.shiny) } else { "-".into() }) }, t.dim, false),
        ]).collect();
        for (i, (l, v, c, b)) in rows.iter().enumerate() {
            let y = y0 + i as i32;
            if i as u16 >= r.height {
                break;
            }
            if l.is_empty() {
                puts(buf, x0, y, v, *c, None, *b, w);
            } else {
                puts(buf, x0, y, l, t.dim, None, false, 7);
                puts(buf, x0 + 7, y, &trunc(v, w - 7), *c, None, *b, w - 7);
            }
        }
        return;
    }
    // under the card: dense lines, right-aligned extras dropped first when narrow
    let mut lines: Vec<(Vec<(String, Rgb, bool)>, Vec<(String, Rgb, bool)>)> = vec![];
    let mut l1 = vec![(badge, bc, true)];
    if !list.is_empty() {
        l1.push((format!("  ×{}", list.len()), t.title, true));
        let span = if first == last { first.clone().unwrap_or_default() } else { format!("{} → {}", first.clone().unwrap_or_default(), last.clone().unwrap_or_default()) };
        l1.push((format!("  {span}"), t.dim, false));
    }
    lines.push((l1, vec![("odds ".into(), t.dim, false), (odds(cp), t.hi, true)]));
    if let Some(c) = &card {
        let mut l: Vec<(String, Rgb, bool)> = vec![(if c.set_name.is_empty() { c.set_id.clone() } else { c.set_name.clone() }, t.fg, false)];
        l.push((format!(" {}", c.number), t.dim, false));
        if !c.rarity.is_empty() {
            l.push((format!(" · {}", c.rarity), tier.color, false));
        }
        if !kinds.is_empty() {
            l.push((format!(" · {kinds}"), t.dim, false));
        }
        lines.push((l, if c.artist.is_empty() { vec![] } else { vec![(c.artist.clone(), t.faint, false)] }));
    }
    // skins of this tier: the one on the shown pull highlighted, seen ones lit, the rest dim
    let mut l2: Vec<(String, Rgb, bool)> = vec![("skins".into(), t.dim, false)];
    if tier.skins.is_empty() {
        l2.push((" none · a plain tab".into(), t.faint, false));
    }
    let cur_skin = shown.map(|p| p.skin.as_str()).unwrap_or("");
    let mut order: Vec<&(String, u32)> = tier.skins.iter().collect();
    order.sort_by_key(|(sk, w)| (sk != cur_skin, !skins.contains(&sk.as_str()), std::cmp::Reverse(*w)));
    for (sk, _) in order {
        let seen = skins.contains(&sk.as_str());
        let (mark, c, b) = if sk == cur_skin { ("●", t.accent, true) } else if seen { ("●", t.fg, false) } else { ("○", t.faint, false) };
        l2.push((format!(" {mark}"), c, false));
        l2.push((sk.clone(), c, b));
    }
    lines.push((l2, vec![]));
    let mut l3: Vec<(String, Rgb, bool)> = vec![];
    if let Some(p) = shown {
        if list.len() > 1 {
            l3.push((format!("pull {}/{} {}  ", h.unwrap() + 1, list.len(), data::when(p.ts, app.now)), t.dim, false));
        }
    }
    l3.push(("tier ".into(), t.dim, false));
    l3.push((odds(tp), t.fg, false));
    if !pack.is_cards {
        l3.push((format!("  foil {:.0}%", pack.foil * 100.0), t.faint, false));
    }
    if pack.shiny > 0.0 {
        l3.push((format!("  shiny {}", odds_short(pack.shiny)), t.faint, false));
    }
    let r3 = if shiny { vec![("✦ shiny".to_string(), t.hi, true)] } else { vec![] };
    lines.push((l3, r3));
    for (i, (left, right)) in lines.iter().take(r.height as usize).enumerate() {
        let y = y0 + i as i32;
        let rw: usize = right.iter().map(|s| width(&s.0)).sum();
        let mut rx = x0 + w as i32 - rw as i32;
        for (s, c, b) in right {
            rx += puts(buf, rx, y, s, *c, None, *b, 30) as i32;
        }
        let limit = x0 + w as i32 - rw as i32 - if rw > 0 { 2 } else { 0 };
        let mut x = x0;
        for (s, c, b) in left {
            let sw = width(s) as i32;
            if x + sw > limit {
                // a partial segment only if it is text (not a lone marker)
                if sw > 3 && limit - x > 4 {
                    let room = (limit - x) as usize;
                    puts(buf, x, y, &trunc(s, room), *c, None, *b, room);
                }
                break;
            }
            x += puts(buf, x, y, s, *c, None, *b, sw as usize) as i32;
        }
    }
}

// ---------------------------------------------------------------- stats panels

fn packs_panel(app: &mut App, buf: &mut Buffer, r: Rect, t: &Theme, focused: bool) {
    let mut ti = Titles::new();
    ti.tl.push(vec![segb("packs", t.title)]);
    let (_, inner) = panel(buf, r, box_col(t, t.box_stats, focused), t.bg, &ti);
    let w = inner.width as usize;
    for (i, p) in app.coll.packs.iter().enumerate().take(inner.height as usize) {
        let y = inner.y as i32 + i as i32;
        let x = inner.x as i32;
        let (kind, have, tot) = pack_completion(app, i);
        let frac = have as f32 / tot.max(1) as f32;
        let active = i == app.pack;
        let name_w = 9.min(w / 3);
        puts(buf, x, y, SUP.get(i).copied().unwrap_or(" "), if active { t.hi } else { t.faint }, None, false, 1);
        puts(buf, x + 1, y, &trunc(&p.id, name_w), if active { t.title } else { t.fg }, None, active, name_w);
        let pct = format!("{:>3.0}%", frac * 100.0);
        let tail = format!(" {kind}");
        let mw = w.saturating_sub(name_w + 2 + pct.len() + tail.len() + 1);
        meter(buf, x + name_w as i32 + 2, y, mw, frac, &t.meter, t.meter_bg);
        let px = x + (name_w + 2 + mw + 1) as i32;
        puts(buf, px, y, &pct, t.title, None, true, 4);
        puts(buf, px + 4, y, &tail, t.faint, None, false, 4);
    }
}

fn tiers_panel(app: &mut App, buf: &mut Buffer, r: Rect, t: &Theme, focused: bool) {
    let pi = app.pack;
    let mut ti = Titles::new();
    ti.tl.push(vec![segb("tiers", t.title)]);
    ti.tr.push(vec![seg(app.coll.packs[pi].id.clone(), t.dim)]);
    let (_, inner) = panel(buf, r, box_col(t, t.box_stats, focused), t.bg, &ti);
    let c = &app.coll;
    let p = &c.packs[pi];
    let counts: Vec<usize> = (0..p.tiers.len())
        .map(|ti| c.slot_of.iter().filter(|k| k.is_some_and(|k| k.pack == pi && k.tier == ti)).count())
        .collect();
    let total: usize = counts.iter().sum();
    let w = inner.width as usize;
    let lw = 13.min(w / 4);
    let (x0, y0) = (inner.x as i32, inner.y as i32);
    // columns: label | completion meter + n/m | pull share bar + count
    let mw = ((w.saturating_sub(lw + 2)) * 40 / 100).clamp(3, 14);
    let fw = 6;
    let bx = x0 + (lw + 1 + mw + 1 + fw) as i32;
    let bw = (w as i32 - (bx - x0) - 5).max(0) as usize;
    puts(buf, x0, y0, "tier", t.faint, None, false, lw);
    puts(buf, x0 + lw as i32 + 1, y0, "caught", t.faint, None, false, mw + fw);
    puts(buf, bx, y0, "pulls ┊odds", t.faint, None, false, bw + 5);
    // real-card packs: only the rarities that have cards, each out of the characters that have one
    for (row, i) in p.live_tiers().into_iter().enumerate() {
        let tier = &p.tiers[i];
        let y = y0 + 1 + row as i32;
        if y >= (inner.y + inner.height) as i32 {
            break;
        }
        let (caught, of) = if p.is_cards {
            let cards: Vec<usize> = (0..p.card_list.len()).filter(|&x| p.card_list[x].tier == i).collect();
            let got = cards.iter().filter(|&&x| c.slot_state(SlotKey { pack: pi, ch: p.card_list[x].ch, tier: i, card: x as u32 }, false) != SlotState::Empty).count();
            (got, cards.len())
        } else {
            ((0..p.chars.len()).filter(|&ch| c.slot_state(SlotKey::legacy(pi, ch, i), false) != SlotState::Empty).count(), p.chars.len())
        };
        let frac = caught as f32 / of.max(1) as f32;
        put(buf, x0, y, "●", Some(tier.color), None, false);
        puts(buf, x0 + 2, y, &trunc(&tier.label, lw - 2), t.fg, None, false, lw - 2);
        meter(buf, x0 + lw as i32 + 1, y, mw, frac, &t.meter, t.meter_bg);
        let fr = if p.is_big() { format!("{caught}") } else { format!("{caught}/{of}") };
        puts(buf, x0 + (lw + 1 + mw + 1) as i32, y, &trunc(&fr, fw - 1), t.dim, None, false, fw);
        // rarity distribution: share of this pack's pulls, with the expected share tick
        let share = counts[i] as f32 / total.max(1) as f32;
        let exp = p.tier_p(i) as f32;
        let cells = share * bw as f32;
        for j in 0..bw {
            let f = cells - j as f32;
            let c0 = mix(darken(tier.color, 0.55), tier.color, j as f32 / bw.max(1) as f32);
            let sym = if f >= 1.0 {
                "█"
            } else if f >= 0.75 {
                "▊"
            } else if f >= 0.5 {
                "▌"
            } else if f >= 0.25 || (j == 0 && counts[i] > 0) {
                "▎"
            } else {
                " "
            };
            put(buf, bx + j as i32, y, sym, Some(c0), None, false);
        }
        let ex = bx + (exp * bw as f32).round().min(bw.saturating_sub(1) as f32) as i32;
        if (exp * bw as f32) > cells {
            put(buf, ex, y, "┊", Some(t.dim), None, false);
        }
        puts(buf, bx + bw as i32 + 1, y, &format!("{:>3}", counts[i]), if counts[i] > 0 { t.title } else { t.faint }, None, counts[i] > 0, 4);
    }
}

fn activity_panel(app: &mut App, buf: &mut Buffer, r: Rect, t: &Theme, focused: bool) {
    let pulls = &app.coll.pulls;
    let mut ti = Titles::new();
    ti.tl.push(vec![segb("activity", t.title)]);
    // bucket size: the smallest "nice" step so the graph spans first pull -> now
    let inner_w = r.width.saturating_sub(2) as i64;
    let n = (inner_w * 2).max(2);
    let first = pulls.first().map(|p| p.ts).unwrap_or(app.now);
    let span = (app.now - first).max(60);
    const STEPS: [(i64, &str); 14] = [
        (60, "1m"), (120, "2m"), (300, "5m"), (600, "10m"), (900, "15m"), (1800, "30m"), (3600, "1h"),
        (7200, "2h"), (10800, "3h"), (21600, "6h"), (43200, "12h"), (86400, "1d"), (172800, "2d"), (604800, "1w"),
    ];
    let (step, sname) = STEPS.iter().copied().find(|(s, _)| s * n >= span).unwrap_or((604800, "1w"));
    ti.tr.push(vec![seg("pulls/", t.dim), seg(sname, t.accent)]);
    let maxv_pre = {
        let end = app.now - app.now.rem_euclid(step) + step;
        let start = end - step * n;
        let mut b = vec![0u32; n as usize];
        for p in pulls.iter().filter(|p| p.ts >= start && p.ts < end) {
            b[((p.ts - start) / step) as usize] += 1;
        }
        b.into_iter().max().unwrap_or(0)
    };
    ti.bl.push(vec![seg("peak ", t.faint), seg(maxv_pre.to_string(), t.dim)]);
    let (_, inner) = panel(buf, r, box_col(t, t.box_stats, focused), t.bg, &ti);
    if inner.height < 2 {
        return;
    }
    let end = app.now - app.now.rem_euclid(step) + step;
    let start = end - step * n;
    let mut bins = vec![0u32; n as usize];
    let mut foil_bins = vec![0usize; n as usize];
    for (i, p) in pulls.iter().enumerate() {
        if p.ts < start || p.ts >= end {
            continue;
        }
        let b = ((p.ts - start) / step) as usize;
        bins[b] += 1;
        if let Some(k) = app.coll.slot_of[i] {
            if k.tier > foil_bins[b] && app.coll.packs[k.pack].foil_tier(k.tier) {
                foil_bins[b] = k.tier;
            }
        }
    }
    let max = *bins.iter().max().unwrap_or(&1) as f32;
    let vals: Vec<f32> = bins.iter().map(|&b| b as f32 / max.max(1.0)).collect();
    let gh = inner.height - 1;
    braille(buf, Rect::new(inner.x, inner.y, inner.width, gh), &vals, &t.graph, Some(t.faint));
    // axis: foil markers under their bucket, time labels at the ends
    let ay = (inner.y + gh) as i32;
    for cx in 0..inner.width as usize {
        let tier = foil_bins.get(cx * 2).copied().unwrap_or(0).max(foil_bins.get(cx * 2 + 1).copied().unwrap_or(0));
        let pk = &app.coll.packs[app.pack];
        let col = if tier > 0 { pk.tiers.get(tier).map(|x| x.color).unwrap_or(t.accent) } else { t.faint };
        put(buf, inner.x as i32 + cx as i32, ay, if tier > 0 { "▴" } else { "─" }, Some(if tier > 0 { col } else { mix(t.faint, t.bg_guess, 0.4) }), None, false);
    }
    let l = data::when(start, app.now);
    puts(buf, inner.x as i32, ay, &format!("{l} "), t.dim, None, false, 14);
    let rl = " now";
    puts(buf, inner.x as i32 + inner.width as i32 - width(rl) as i32, ay, rl, t.dim, None, false, 4);
}

fn best_panel(app: &mut App, buf: &mut Buffer, r: Rect, t: &Theme, focused: bool) {
    let best = app.best_pulls();
    let mut ti = Titles::new();
    ti.tl.push(vec![segb("best pulls", t.title)]);
    // the cutoff (config.txt best_since), subtly: "since Sep 29"
    ti.tr.push(vec![seg(&app.best_since.map_or("rarest".to_string(), |s| format!("since {}", crate::data::date_short(s))), t.dim)]);
    let (_, inner) = panel(buf, r, box_col(t, t.box_stats, focused), t.bg, &ti);
    let rows = inner.height as usize;
    if best.is_empty() {
        puts(buf, inner.x as i32 + 1, inner.y as i32, "no foils yet", t.dim, None, false, 20);
        return;
    }
    let sel = app.best_sel.min(best.len() - 1);
    let off = if sel >= rows { sel + 1 - rows } else { 0 };
    let w = inner.width as usize;
    for (row, (i, &(pi, p))) in best.iter().enumerate().skip(off).take(rows).enumerate() {
        let y = inner.y as i32 + row as i32;
        let x = inner.x as i32;
        let pull = &app.coll.pulls[pi];
        let k = app.coll.slot_of[pi].unwrap();
        let pk = &app.coll.packs[k.pack];
        let tier = &pk.tiers[k.tier];
        let on = focused && i == sel;
        let bg = if on { Some(mix(t.bg_guess, t.hi, 0.18)) } else { None };
        if on {
            fill(buf, Rect::new(inner.x, y as u16, inner.width, 1), Some(mix(t.bg_guess, t.hi, 0.18)));
        }
        let rank = format!("{:>2}", i + 1);
        puts(buf, x, y, &rank, if i < 3 { t.hi } else { t.faint }, bg, i < 3, 2);
        put(buf, x + 3, y, "●", Some(tier.color), bg, false);
        let od = odds_short(p);
        let name = format!("{}{}", if pull.shiny { "✦" } else { "" }, pk.name_for(k.ch, k.card));
        let right = format!(" {od}");
        let lab_w = w.saturating_sub(5 + right.len());
        let name_w = (width(&name)).min(lab_w);
        puts(buf, x + 5, y, &trunc(&name, name_w), t.title, bg, true, name_w);
        let rest = lab_w.saturating_sub(name_w + 1);
        if rest >= 4 {
            puts(buf, x + 5 + name_w as i32 + 1, y, &trunc(&tier.label, rest), tier.color, bg, false, rest);
        }
        puts(buf, x + w as i32 - right.len() as i32, y, &right, t.hi, bg, false, right.len());
        app.hits.best.push((Rect::new(inner.x, y as u16, inner.width, 1), pi));
    }
}

// ---------------------------------------------------------------- help

fn help(buf: &mut Buffer, area: Rect, t: &Theme) {
    let dimbg = t.bg_guess;
    crate::draw::recolor(buf, area, &|_, _, c| mix(c, dimbg, 0.72));
    let keys: &[(&str, &str)] = &[
        ("← → ↑ ↓   h j k l", "move in the binder; the edges flip pages"),
        ("PgUp PgDn  wheel", "flip binder pages"),
        ("1-9   [ ]   click", "switch pack"),
        ("tab   shift-tab", "cycle panels: binder › card › stats"),
        ("← →   in card", "step through this card's pulls"),
        ("↑ ↓ ⏎   in stats", "pick a best pull and open it"),
        ("/", "search: words, set:swsh7 rarity:\"rare rainbow\""),
        ("  type:water vmax", "  artist:… subtype:… char:… shiny foil new pending"),
        ("S", "sets: every set / one set's checklist"),
        ("s", "shiny-only binder"),
        ("o", "owned-only"),
        ("v", "the card's text half (moves, HP, weakness) under the art"),
        ("d", "view: full set / one slot per character"),
        ("t", "cycle theme"),
        ("L", "jump to the latest pull"),
        ("r", "reload pulls.log"),
        ("q   esc", "quit"),
    ];
    let w = 68u16.min(area.width.saturating_sub(4));
    let h = (keys.len() as u16 + 5).min(area.height.saturating_sub(2));
    let r = Rect::new(area.x + (area.width - w) / 2, area.y + (area.height - h) / 2, w, h);
    let mut ti = Titles::new();
    ti.tl.push(vec![segb("help", t.title)]);
    ti.tr.push(vec![seg("theme ", t.dim), segb(t.name, t.accent)]);
    ti.br.push(vec![seg("any key closes", t.dim)]);
    let (_, inner) = panel(buf, r, t.box_focus, t.bg.or(Some(t.bg_guess)), &ti);
    let (x0, y0) = (inner.x as i32 + 2, inner.y as i32 + 1);
    for (i, (k, d)) in keys.iter().enumerate() {
        let y = y0 + i as i32;
        if y >= (inner.y + inner.height) as i32 {
            break;
        }
        puts(buf, x0, y, k, t.hi, None, true, 20);
        puts(buf, x0 + 21, y, d, t.fg, None, false, inner.width.saturating_sub(23) as usize);
    }
    let y = y0 + keys.len() as i32 + 1;
    let legend: Vec<(&str, Rgb, &str)> = vec![("● ", t.good, "earned  "), ("◌ ", t.warn, "pending: use its tab  "), ("NEW ", rgb(0xff5fa2), "not viewed  "), ("┆ ", t.slot_line, "empty")];
    let mut x = x0;
    for (s, c, d) in legend {
        x += puts(buf, x, y, s, c, None, true, 2) as i32;
        x += puts(buf, x, y, d, t.dim, None, false, 40) as i32;
    }
    let _: Vec<Seg> = vec![];
}
