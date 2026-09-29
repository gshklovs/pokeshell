//! Layout and panels. `render` paints a full frame; `render_card` repaints only the big card
//! (the animation path: the rest of the frame is reused from the last full paint).

use crate::app::{App, Completion, Focus, Own, PER_PAGE, Tab, View};
use crate::card::{self, Card, short_label};
use crate::cardtext;
use crate::color::{Rgb, darken, grad, lighten, mix, rgb};
use crate::data::{self, SlotKey, SlotState, Status};
use crate::draw::{Seg, Titles, braille, fill, groups_w, meter, meter_segs, panel, panel_ex, put, puts, seg, segb, trunc, width};
use crate::query;
use crate::theme::{THEMES, Theme};
use ratatui::buffer::Buffer;
use ratatui::layout::Rect;

const SUP: [&str; 9] = ["¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"];
const NEW_PINK: Rgb = rgb(0xff5fa2);

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
    let ntiers = app.tier_rows().len() as u16;
    let npacks = app.coll.packs.len() as u16;

    // stats stack for a column (compact/tiny modes): the tiers and the best pulls first, then the packs (the header
    // has their meters), then the activity graph (V-08)
    let stack = |l: &mut Lay, x: u16, y: u16, cw: u16, ch: u16| {
        let (pk_h, t_h) = (npacks + 2, ntiers + 3);
        if ch >= pk_h + t_h + 8 {
            l.packs = rect(x, y, cw, pk_h);
            l.tiers = rect(x, y + pk_h, cw, t_h);
            let rem = ch - pk_h - t_h;
            if rem >= 12 {
                let ah = rem / 2;
                l.activity = rect(x, y + pk_h + t_h, cw, ah);
                l.best = rect(x, y + pk_h + t_h + ah, cw, rem - ah);
            } else {
                l.best = rect(x, y + pk_h + t_h, cw, rem);
            }
        } else {
            // tiers get what they need, the best pulls at least 3 rows of their own when there is room
            let th = t_h.min(ch.saturating_sub(5).max(4)).min(ch);
            l.tiers = rect(x, y, cw, th);
            l.best = rect(x, y + th, cw, ch - th);
        }
    };

    if w >= 100 && h >= 30 {
        // binder: 3x3 slots, each ~5:3 cells (a card's shape in half-block pixels)
        let slot_h = (bh.saturating_sub(2)) / 3;
        let slot_w = (slot_h * 5 / 3).clamp(14, 34);
        let bw = (3 * slot_w + 2 + 2).min(w * 56 / 100);
        l.binder = rect(a.x, by, bw, bh);
        let (rx, rw) = (a.x + bw, w - bw);
        if app.show_text {
            // the text half (v) gets the whole column: moves, weakness, set and artist all show (V-03)
            l.card = rect(rx, by, rw, bh);
            return l;
        }
        // right column: the card gets the lion's share, stats take the rest
        let tiers_h = ntiers + 3;
        let low_min = 8;
        // never taller than the biggest art (16 rows) + frame + info needs
        let card_h = bh.saturating_sub(tiers_h + low_min).clamp(14, 40).min(bh * 62 / 100).max(bh.saturating_sub(tiers_h + low_min + 12)).min(27);
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

/// "1/5027", "1/14k"; "—" for odds of zero (a shiny in a pack without shinies, D-08).
fn odds_short(p: f64) -> String {
    if p <= 0.0 || !p.is_finite() {
        return "—".into();
    }
    let n = 1.0 / p;
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

fn pct(c: &Completion) -> String {
    let p = c.frac() * 100.0;
    // 0% only when nothing is caught, 100% only when everything is
    let p = if c.owned > 0 && p < 1.0 { 1.0 } else if c.owned < c.total && p > 99.0 { 99.0 } else { p.round() };
    format!("{p:.0}%")
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
    if app.coll.packs.is_empty() {
        let lines = [
            ("no packs found".to_string(), theme.title),
            (format!("under {}", app.opts.root.join("packs").display()), theme.dim),
            ("(pass the pokeshell checkout with --root) · q quits".to_string(), theme.faint),
        ];
        for (i, (s, c)) in lines.iter().enumerate() {
            let s = trunc(s, area.width as usize - 2);
            let x = (area.width as i32 - width(&s) as i32) / 2;
            puts(buf, x, area.height as i32 / 2 - 1 + i as i32, &s, *c, None, i == 0, area.width as usize);
        }
        return;
    }
    let lay = layout(app, area);
    if let Some(r) = lay.header {
        header(app, buf, r, &theme);
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
    if app.picker.is_some() {
        picker(app, buf, area, &theme);
    }
    if app.help {
        help(app, buf, area, &theme);
    }
}

// ---------------------------------------------------------------- header

fn header(app: &App, buf: &mut Buffer, r: Rect, t: &Theme) {
    let (x0, y0, w) = (r.x as i32, r.y as i32, r.width as usize);
    let st = app.stats();
    // row 0: logo, totals (dropped from the right when narrow), clock (never over the logo, V-05)
    let logo = " ◓ pokeshell";
    let logo_w = width(logo);
    let time = format!("{} ", data::hhmm(app.now));
    let date = format!("{} {}  ", data::weekday(app.now), data::date_short(app.now));
    let show_time = w >= logo_w + 1 + width(&time);
    let show_date = show_time && w >= logo_w + 8 + width(&time) + width(&date);
    let right_w = if show_time { width(&time) } else { 0 } + if show_date { width(&date) } else { 0 };
    for (i, (g, _)) in crate::draw::clusters(logo).into_iter().enumerate() {
        let c = grad(&t.meter, i as f32 / (logo_w - 1) as f32);
        if i >= w {
            break;
        }
        put(buf, x0 + i as i32, y0, g, Some(lighten(c, 0.2)), None, true);
    }
    let mut x = x0 + logo_w as i32;
    if (x - x0) as usize + 7 + right_w + 1 <= w {
        x += puts(buf, x, y0, " binder", t.dim, None, false, 10) as i32 + 3;
    }
    let pend_c = if st.pending > 0 { t.warn } else { t.dim };
    let new_n = app.coll.new_count();
    let mut chips: Vec<Vec<(String, Rgb, bool)>> = vec![
        vec![(st.total.to_string(), t.title, true), (" pulls".into(), t.dim, false)],
        vec![(st.unique.to_string(), t.title, true), (" cards".into(), t.dim, false)],
        vec![(st.foils.to_string(), t.accent, true), (" foils".into(), t.dim, false)],
        vec![("✦ ".into(), t.hi, false), (st.shinies.to_string(), t.hi, true), (" shiny".into(), t.dim, false)],
        vec![("◌ ".into(), pend_c, false), (st.pending.to_string(), pend_c, true), (" pending".into(), t.dim, false)],
        vec![(new_n.to_string(), if new_n > 0 { NEW_PINK } else { t.dim }, true), (" new".into(), t.dim, false)],
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
    if show_date {
        puts(buf, rx, y0, &date, t.dim, None, false, 20);
    }
    if show_time {
        puts(buf, x0 + w as i32 - width(&time) as i32, y0, &time, t.title, None, true, 8);
    }
    if r.height < 2 {
        return;
    }
    // row 1: a completion meter per pack (btop's cpu-core row), then the last pull, then the key hints
    let y = y0 + 1;
    let hints: Vec<(&str, &str)> = vec![("S", " sets  "), ("/", " search  "), ("?", " help ")];
    let full_hint_w: usize = hints.iter().map(|h| width(h.0) + width(h.1)).sum();
    let hints = if w >= 120 { hints } else { vec![("?", " help ")] };
    let hint_w = if w >= 120 { full_hint_w } else { 7 } as i32;
    let hint_x = x0 + w as i32 - hint_w;
    let mut hx = hint_x;
    for (k, d) in &hints {
        hx += puts(buf, hx, y, k, t.hi, None, true, 2) as i32;
        hx += puts(buf, hx, y, d, t.dim, None, false, 10) as i32;
    }
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
        if p.status == Status::Pending {
            last_segs.push((" ◌".into(), t.warn, false));
        }
    }
    let last_w: usize = last_segs.iter().map(|s| width(&s.0)).sum();
    let avail = (hint_x - x0 - 1).max(0) as usize;
    let np = app.coll.packs.len().max(1);
    let show_last = avail >= last_w + np.min(3) * 18 + 2;
    let meters_w = if show_last { avail - last_w - 2 } else { avail };
    let per = meters_w / np;
    let mut x = x0 + 1;
    for (i, p) in app.coll.packs.iter().enumerate() {
        let c = app.pack_completion(i);
        let frac = c.frac();
        let active = i == app.pack;
        let pc = format!("{:>4}", pct(&c));
        let name_w = width(&p.id).min(9).min(per.saturating_sub(12)).max(3);
        let mw = per.saturating_sub(name_w + 1 + 1 + pc.len() + 2).min(24);
        if mw < 3 {
            break;
        }
        puts(buf, x, y, SUP.get(i).copied().unwrap_or(" "), if active { t.hi } else { t.faint }, None, false, 1);
        puts(buf, x + 1, y, &crate::draw::take_cells(&p.id, name_w), if active { t.title } else { t.dim }, None, active, name_w);
        let mx = x + 1 + name_w as i32 + 1;
        meter(buf, mx, y, mw, frac.max(0.001), &t.meter, t.meter_bg);
        puts(buf, mx + mw as i32 + 1, y, &pc, if active { t.title } else { t.fg }, None, active, 4);
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

/// The binder's top-left tabs at a level of detail (0 = most): the packs, then the set tab. Narrower, the other
/// packs' names shorten to 3 letters, then to their key (a superscript), then go, before the set's name is cut.
fn binder_tabs(app: &App, t: &Theme, level: u8) -> (Vec<Vec<Seg>>, Vec<Tab>) {
    let mut groups = Vec::new();
    let mut ids = Vec::new();
    // with a search on, a pack without matching cards has no tab, and the others show how many match
    let counts = app.search_counts();
    for (i, p) in app.coll.packs.iter().enumerate() {
        let active = i == app.pack;
        let hits = counts.as_ref().map(|c| c.packs[i]);
        if !active && (level >= 3 || hits == Some(0)) {
            continue;
        }
        let label = match (active, level) {
            (true, _) | (false, 0) => p.id.clone(),
            (false, 1) => crate::draw::take_cells(&p.id, 3),
            _ => String::new(),
        };
        let mut g = vec![seg(SUP.get(i).copied().unwrap_or(""), if active { t.hi } else { t.dim })];
        if !label.is_empty() {
            g.push(if active { segb(label, t.title) } else { seg(label, t.dim) });
        }
        if let Some(n) = hits.filter(|_| level <= 2) {
            g.push(seg(format!(" {n}"), if n > 0 { t.accent } else { t.faint }));
        }
        groups.push(g);
        ids.push(Tab::Pack(i));
    }
    // real-card packs: the set tab (S or a click opens the set picker)
    if !app.coll.packs[app.pack].sets.is_empty() {
        let name_max = match level {
            0 | 1 => 26,
            2 | 3 => 22,
            4 => 14,
            _ => 10,
        };
        let mut g = vec![];
        match app.current_set() {
            Some(s) => {
                if level <= 1 {
                    g.push(seg("set ", t.faint));
                }
                g.push(segb(trunc(&s.name, name_max), t.title));
            }
            None => g.push(seg("all sets", t.dim)),
        }
        if let Some(n) = counts.as_ref().and_then(|c| c.sets.get(app.set_sel[app.pack]).copied()) {
            g.push(seg(format!(" {n}"), if n > 0 { t.accent } else { t.faint }));
        }
        g.push(seg(" ▾", t.dim));
        groups.push(g);
        ids.push(Tab::Set);
    }
    (groups, ids)
}

/// The completion line on the binder's bottom border: "87/193 ■■■■□□ 45% +3 pending" (earned only; pending apart).
fn completion_group(app: &App, t: &Theme, room: usize) -> Vec<Seg> {
    let c = app.view_completion();
    let dex = app.views[app.pack] == View::Dex;
    let what = if dex { " caught" } else { "" };
    let mut full = vec![segb(c.owned.to_string(), t.title), seg(format!("/{}{what}", c.total), t.dim)];
    let bar = meter_segs(8, c.frac(), &t.meter, t.meter_bg);
    let mut g = full.clone();
    g.push(seg(" ", t.dim));
    g.extend(bar.clone());
    g.push(seg(format!(" {}", pct(&c)), t.fg));
    if c.pending > 0 {
        g.push(seg(format!(" +{} pending", c.pending), t.warn));
    }
    for cand in [g.clone(), g.iter().take(g.len() - usize::from(c.pending > 0)).cloned().collect::<Vec<_>>()] {
        if crate::draw::segs_w(&cand) + 2 <= room {
            return cand;
        }
    }
    full.push(seg(format!(" {}", pct(&c)), t.fg));
    if crate::draw::segs_w(&full) + 2 <= room {
        return full;
    }
    vec![segb(c.owned.to_string(), t.title), seg(format!("/{}", c.total), t.dim)]
}

/// The search box on the bottom border: "/set:evo▏lving 12" (the cursor where it is).
fn search_group(app: &App, t: &Theme, n: usize) -> Vec<Seg> {
    let mut g = vec![seg("/", t.hi)];
    if app.searching {
        let cs: Vec<char> = app.search.chars().collect();
        let cur = app.cursor.min(cs.len());
        g.push(segb(cs[..cur].iter().collect::<String>(), t.title));
        g.push(seg("▏", t.hi));
        g.push(segb(cs[cur..].iter().collect::<String>(), t.title));
    } else {
        g.push(segb(app.search.clone(), t.title));
    }
    g.push(seg(format!(" {n} {}", if n == 1 { "card" } else { "cards" }), t.dim));
    g
}

fn binder(app: &mut App, buf: &mut Buffer, r: Rect, t: &Theme) {
    let focused = app.focus == Focus::Binder;
    let line = box_col(t, t.box_binder, focused);
    let n = app.slots().len();
    let pages = app.pages();
    let page = app.page();
    let sel = app.sel_ix();
    // top right: the view (cards / dex) and the filters on
    let view = app.views[app.pack];
    let mut tr = vec![seg(if view == View::Set { "cards" } else { "dex" }, t.accent)];
    if app.shiny_only {
        tr.push(segb(" ✦shiny", t.hi));
    }
    match app.own {
        Own::Owned => tr.push(seg(" owned", t.good)),
        Own::Missing => tr.push(seg(" missing", t.warn)),
        Own::All => {}
    }
    let span = r.width.saturating_sub(3) as usize;
    let tr_w = groups_w(&[tr.clone()]) + 1;
    // the tabs at the most detail that fits beside the view label, else without it (S-09)
    let mut ti = Titles::new();
    let mut tab_ids = vec![];
    for level in 0..=5u8 {
        let (g, ids) = binder_tabs(app, t, level);
        let fits_with = groups_w(&g) + 1 + tr_w <= span;
        if fits_with || level == 5 {
            if fits_with {
                ti.tr.push(tr.clone());
            }
            ti.tl = g;
            tab_ids = ids;
            break;
        }
    }
    let room = r.width.saturating_sub(4) as usize;
    let page_g = vec![seg("◂ ", t.dim), segb(format!("{}", page + 1), t.title), seg(format!("/{pages}"), t.dim), seg(" ▸", t.dim)];
    if let Some(q) = &app.number {
        ti.bl.push(vec![seg("#", t.hi), segb(q.clone(), t.title), seg("▏", t.hi), seg(" ⏎ jump", t.dim)]);
    } else if app.searching || !app.search.is_empty() {
        ti.bl.push(search_group(app, t, n));
    } else {
        let g = completion_group(app, t, room.saturating_sub(groups_w(&[page_g.clone()]) + 1));
        ti.bl.push(g);
    }
    ti.br.push(page_g);
    let ((tabs, inner), page_range) = panel_ex(buf, r, line, t.bg, &ti);
    for ((a, b), id) in tabs.iter().zip(tab_ids) {
        app.hits.tabs.push((*a, *b, r.y as i32, id));
    }
    app.hits.binder = r;
    // page arrows on the bottom border (click targets)
    if let Some((a, b)) = page_range {
        let y = r.y + r.height - 1;
        app.hits.prev_page = Some(Rect::new(a.max(0) as u16, y, 2, 1));
        app.hits.next_page = Some(Rect::new((b - 2).max(0) as u16, y, 2, 1));
    }
    if inner.width < 4 || inner.height < 1 {
        return;
    }
    // bottom rows: the search's key/value hints while typing, a notice
    let mut grid = inner;
    if app.searching && grid.height >= 8 {
        grid.height -= 1;
        search_hint(app, buf, Rect::new(inner.x, inner.y + inner.height - 1, inner.width, 1), t);
    }
    if let Some(msg) = app.notice.clone() {
        if grid.height >= 6 {
            grid.height -= 1;
        }
        let y = (grid.y + grid.height) as i32;
        let bg = mix(t.bg_guess, t.warn, 0.16);
        fill(buf, Rect::new(inner.x, y as u16, inner.width, 1), Some(bg));
        puts(buf, inner.x as i32 + 1, y, &trunc(&format!("! {msg}"), inner.width as usize - 2), t.warn, Some(bg), false, inner.width as usize - 2);
    }

    if n == 0 {
        empty_message(app, buf, grid, t);
        return;
    }
    let sw = (grid.width.saturating_sub(2)) / 3;
    let sh = grid.height / 3;
    let slots: Vec<SlotKey> = app.slots().iter().skip(page * PER_PAGE).take(PER_PAGE).copied().collect();
    if sw < 8 || sh < 3 {
        // too small for the grid: this page as a list, one card a line (V-04)
        list_page(app, buf, grid, t, &slots, page, sel);
        return;
    }
    let ox = grid.x + (grid.width - (sw * 3 + 2)) / 2;
    let oy = grid.y + (grid.height - sh * 3) / 2;
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
        // empty slots show a silhouette: the base art (legacy packs; full-art tiers would be solid) or "?" (a real
        // card's art is a whole scene, whose silhouette would be a solid block)
        let art = if state == SlotState::Empty && !pack.is_cards { pack.tiers[0].art.clone() } else { pack.art_at(*k) };
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
        flash(app, buf, sr, *k, &theme);
    }
}

/// An opened search result glows on its real page for a moment (App::flash): its pocket brightens, fading out.
fn flash(app: &App, buf: &mut Buffer, r: Rect, k: SlotKey, t: &Theme) {
    let lv = app.flash_level(k);
    if lv <= 0.0 {
        return;
    }
    let hi = t.hi;
    let (x0, y0, x1, y1) = (r.x as i32, r.y as i32, (r.x + r.width) as i32 - 1, (r.y + r.height) as i32 - 1);
    crate::draw::recolor(buf, r, &|x, y, c| {
        let edge = x == x0 || x == x1 || y == y0 || y == y1;
        mix(c, hi, lv * if edge { 0.85 } else { 0.22 })
    });
}

/// The binder's page as a list (terminals too small for the 3x3 grid): "● 17/203 Applin  R holo".
fn list_page(app: &mut App, buf: &mut Buffer, r: Rect, t: &Theme, slots: &[SlotKey], page: usize, sel: usize) {
    let rows = r.height as usize;
    let within = sel - page * PER_PAGE;
    let off = if within >= rows { within + 1 - rows } else { 0 };
    for (row, (i, k)) in slots.iter().enumerate().skip(off).take(rows).enumerate() {
        let y = r.y + row as u16;
        let idx = page * PER_PAGE + i;
        let on = idx == sel;
        let bg = if on { Some(mix(t.bg_guess, t.hi, 0.18)) } else { None };
        if on {
            fill(buf, Rect::new(r.x, y, r.width, 1), bg);
        }
        let pack = &app.coll.packs[k.pack];
        let st = app.coll.slot_state(*k, app.shiny_only);
        let (mark, mc) = match st {
            SlotState::Owned => ("●", t.good),
            SlotState::Pending => ("◌", t.warn),
            SlotState::Empty => ("○", t.faint),
        };
        let w = r.width as usize;
        let mut x = r.x as i32;
        x += puts(buf, x, y as i32, mark, mc, bg, false, 1) as i32 + 1;
        let tag = pack.tag_for(k.ch, k.card);
        if !tag.is_empty() && w >= 24 {
            x += puts(buf, x, y as i32, &format!("{} ", tag.split('/').next().unwrap_or("")), t.dim, bg, false, 6) as i32;
        }
        let used = (x - r.x as i32) as usize;
        let lab = short_label(&pack.tiers[k.tier].label, 10.min(w.saturating_sub(used + 6) / 2));
        let name_room = w.saturating_sub(used + width(&lab) + 1);
        let fg = if st == SlotState::Empty { t.dim } else { t.title };
        puts(buf, x, y as i32, &trunc(&pack.name_for(k.ch, k.card), name_room), fg, bg, on, name_room);
        puts(buf, r.x as i32 + w as i32 - width(&lab) as i32, y as i32, &lab, pack.tiers[k.tier].color, bg, false, 12);
        if app.coll.slot_new(*k, app.shiny_only) && w >= 30 {
            puts(buf, r.x as i32 + w as i32 - width(&lab) as i32 - 5, y as i32, "NEW", rgb(0x1a1020), Some(NEW_PINK), true, 3);
        }
        app.hits.slots.push((Rect::new(r.x, y, r.width, 1), idx));
        flash(app, buf, Rect::new(r.x, y, r.width, 1), *k, t);
    }
}

/// Nothing to show: say what filters are on and how to clear them (S-13).
fn empty_message(app: &App, buf: &mut Buffer, r: Rect, t: &Theme) {
    let mut lines: Vec<(String, Rgb)> = vec![];
    let terms = app.terms();
    if !app.search.is_empty() {
        lines.push((format!("no cards match /{}", app.search.trim()), t.title));
        let unknown = query::unknown_keys(&terms);
        if !unknown.is_empty() {
            lines.push((format!("{}: is no key · try set: rarity: type: name: number: artist:", unknown.join(": ")), t.warn));
        }
        for tm in &terms {
            if let Some(ids) = &tm.sets {
                if ids.is_empty() {
                    lines.push((format!("no set matches “{}”", tm.value), t.warn));
                } else if let Some(cur) = app.current_set() {
                    if !ids.contains(&query::fold(&cur.id)) {
                        lines.push((format!("the binder shows {} only · S picks every set", cur.name), t.warn));
                    }
                }
            }
        }
        lines.push(("esc clears the search".into(), t.dim));
    } else if app.shiny_only && app.coll.packs[app.pack].shiny <= 0.0 {
        lines.push(("no shinies in this pack".into(), t.dim));
    } else {
        let what = match app.own {
            Own::Owned => "no cards earned here yet · o shows all",
            Own::Missing => "nothing missing here · m shows all",
            Own::All => "no cards",
        };
        lines.push((what.into(), t.dim));
    }
    let y0 = r.y as i32 + (r.height as i32 - lines.len() as i32) / 2;
    for (i, (s, c)) in lines.iter().enumerate() {
        let s = trunc(s, r.width.saturating_sub(2) as usize);
        let x = r.x as i32 + (r.width as i32 - width(&s) as i32) / 2;
        puts(buf, x, y0 + i as i32, &s, *c, None, i == 0, r.width as usize);
    }
}

/// While typing a search: what the word under the cursor can be (the sets for set:, the rarities for rarity:, ...),
/// else the keys and state words.
fn search_hint(app: &App, buf: &mut Buffer, r: Rect, t: &Theme) {
    let p = &app.coll.packs[app.pack];
    let cs: Vec<char> = app.search.chars().collect();
    let cur = app.cursor.min(cs.len());
    let mut a = cur;
    while a > 0 && !cs[a - 1].is_whitespace() {
        a -= 1;
    }
    let word: String = cs[a..cur].iter().collect::<String>().to_lowercase();
    let (key, val) = word.split_once(':').map(|(k, v)| (k.to_string(), v.trim_matches('"').to_string())).unwrap_or_default();
    let mut segs: Vec<(String, Rgb)> = vec![];
    let distinct = |f: &dyn Fn(&crate::data::CardDef) -> Vec<String>| {
        let mut v: Vec<String> = vec![];
        for c in &p.card_list {
            for x in f(c) {
                if !x.is_empty() && !v.contains(&x) {
                    v.push(x);
                }
            }
        }
        v
    };
    match key.as_str() {
        "set" | "sets" | "setname" if !p.sets.is_empty() => {
            segs.push(("sets ".into(), t.dim));
            let list: Vec<&crate::data::SetDef> = if val.is_empty() { p.sets.iter().collect() } else { query::resolve_sets(&p.sets, &val) };
            if list.is_empty() {
                segs.push((format!("none match “{val}”"), t.warn));
            }
            for (i, s) in list.iter().enumerate() {
                segs.push((if i > 0 { " · ".into() } else { String::new() }, t.faint));
                segs.push((s.name.clone(), t.title));
                segs.push((format!(" {}", s.id), t.dim));
            }
            segs.push(("  tab completes".into(), t.faint));
        }
        "rarity" | "type" | "subtype" | "sub" if p.is_cards => {
            let vals = match key.as_str() {
                "rarity" => distinct(&|c| vec![c.rarity.to_lowercase()]),
                "type" => distinct(&|c| c.types.iter().map(|x| x.to_lowercase()).collect()),
                _ => distinct(&|c| c.subtypes.iter().map(|x| x.to_lowercase()).collect()),
            };
            segs.push((format!("{key} "), t.dim));
            for (i, v) in vals.iter().filter(|v| v.contains(&val)).enumerate() {
                segs.push((if i > 0 { " · ".into() } else { String::new() }, t.faint));
                segs.push((if v.contains(' ') { format!("\"{v}\"") } else { v.clone() }, t.fg));
            }
        }
        _ => {
            for (s, c) in [
                ("set: rarity: type: name: number: artist:", t.fg),
                ("  ·  ", t.faint),
                ("owned missing pending new shiny foil", t.accent),
                ("  ·  ", t.faint),
                ("⏎ open on its page  esc back", t.dim),
            ] {
                segs.push((s.to_string(), c));
            }
        }
    }
    let mut x = r.x as i32 + 1;
    let end = (r.x + r.width) as i32 - 1;
    for (s, c) in segs {
        let room = (end - x).max(0) as usize;
        if room == 0 {
            break;
        }
        x += puts(buf, x, r.y as i32, &trunc(&s, room), c, None, false, room) as i32;
    }
}

// ---------------------------------------------------------------- card detail

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
        if let Some((h, len)) = app.hist_pos(k) {
            if len > 1 {
                ti.bl.push(vec![seg("◂ ", t.dim), seg("pull ", t.dim), segb(format!("{}", h + 1), t.title), seg(format!("/{len}"), t.dim), seg(" ▸", t.dim)]);
            }
        }
    }
    let (_, inner) = panel(buf, r, line, t.bg, &ti);
    app.hits.card = r;
    if inner.width < 4 || inner.height < 3 {
        return;
    }
    let Some(k) = key else {
        puts(buf, inner.x as i32 + 2, inner.y as i32 + 1, "nothing selected", t.dim, None, false, 30);
        return;
    };
    // info block: beside the card when there is room, else under it
    let side = inner.width >= 84;
    // with the text half showing (v), it gets the room and the info shrinks to its status line
    let info_rows: u16 = if side { 0 } else if app.show_text { 1 } else if inner.height >= 24 { 4 } else if inner.height >= 15 { 3 } else { 2 };
    let info_rows = info_rows.min(inner.height.saturating_sub(4));
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
/// half. With `v` on and card data for it (docs/CARD_FORMAT.md), the text half stacks under the art like a real
/// card: the art shrinks to make room, and what still doesn't fit scrolls.
fn big_card(app: &mut App, buf: &mut Buffer, area: Rect, t: &Theme, k: SlotKey, below: u16) -> (Rect, u16) {
    let state = app.coll.slot_state(k, app.shiny_only);
    let (_, shown) = app.shown_pull(k);
    let shiny = shown.is_some_and(|i| app.coll.pulls[i].shiny) || (app.shiny_only && state != SlotState::Empty);
    let count = app.shown_pull(k).0.len();
    // (the text half shows for any card with card data, pulled or not: a set checklist can be read too)
    let text = if app.show_text { app.card_text(k) } else { None };
    let scroll = app.text_scroll_for(k);
    let new = app.coll.slot_new(k, app.shiny_only);
    let pack = &app.coll.packs[k.pack];
    let tier = &pack.tiers[k.tier];
    let art = pack.art_at(k);
    let (pw, ph) = card::frame_pad(&tier.frame, false);
    let aw = area.width.saturating_sub(2) as usize;
    let c = Card { pack, ch: k.ch, tier: k.tier, shiny, state, selected: false, count, thumb: false, new, card: k.card };
    let empty_real = state == SlotState::Empty && pack.is_cards;
    // the art as big as fits over `reserve` rows kept free under the card
    let place = |reserve: u16| {
        let ah = area.height.saturating_sub(reserve) as usize;
        let fit = (aw.saturating_sub(pw), ah.saturating_sub(ph).max(2));
        // (an empty real-card slot shows "?": its scene's silhouette would be a solid block)
        let img = if empty_real { None } else { app.art.fitted(pack, &pack.chars[k.ch], &art, shiny, fit.0, fit.1) };
        // the "?" placeholder: small when the text half wants the room
        let ph_rows = if text.is_some() { 3 } else { 8 };
        let (iw, ir) = img.as_ref().map(|i| (i.w, i.rows())).unwrap_or((16.min(fit.0.max(4)), ph_rows.min(fit.1)));
        let (cw, ch) = card::card_size(&c, iw, ir);
        (fit, img, cw.min(area.width), ch.min(area.height))
    };
    let (mut fit, mut img, mut cw, mut ch) = place(0);
    let mut th = 0u16;
    let text_w = |cw: u16| cw.max(40).min(area.width);
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
    let cy = area.y + (slack / 2).min(area.height.saturating_sub(ch + th));
    let cr = Rect::new(area.x + (area.width - cw) / 2, cy, cw, ch);
    // clear the region (animation repaints land here)
    fill(buf, area, t.bg);
    card::draw(buf, cr, &c, img.as_deref(), t);
    if state == SlotState::Owned && card::is_foil(pack, k.tier, shiny) {
        let phase = app.anim_phase();
        card::shimmer(buf, cr, &tier.frame, shiny, phase);
    }
    let mut hidden = 0;
    if let Some(v) = text.as_deref() {
        if th >= 3 {
            let tw = text_w(cw);
            let tr = Rect::new(area.x + (area.width - tw) / 2, cy + ch, tw, th);
            let line = if state == SlotState::Pending { t.faint } else { tier.color };
            let (s, below_rows) = cardtext::draw(buf, tr, v, line, t, scroll);
            app.text_scroll = s;
            hidden = below_rows;
            app.hits.text = tr;
        }
    } else if th == 1 {
        let note = "no card text for this card (v)";
        puts(buf, area.x as i32 + (area.width as i32 - width(note) as i32).max(0) / 2, (cy + ch) as i32, note, t.faint, None, false, area.width as usize);
    }
    app.hits.text_more = hidden;
    app.hits.card_fit = fit;
    (cr, ch + th)
}

/// Animation path: repaint only the big card.
pub fn render_card(app: &mut App, buf: &mut Buffer) {
    let r = app.hits.card_art;
    if r.width == 0 || app.coll.packs.is_empty() {
        return;
    }
    let Some(k) = app.selected() else { return };
    let t = THEMES[app.theme].clone();
    // the card area is centered in its region; repaint just the card rect (same size every frame)
    let state = app.coll.slot_state(k, app.shiny_only);
    let (list, shown) = app.shown_pull(k);
    let shiny = shown.is_some_and(|i| app.coll.pulls[i].shiny) || (app.shiny_only && state != SlotState::Empty);
    let new = app.coll.slot_new(k, app.shiny_only);
    let pack = &app.coll.packs[k.pack];
    let tier = &pack.tiers[k.tier];
    let fit = app.hits.card_fit;
    let art = pack.art_at(k);
    let img = if state == SlotState::Empty && pack.is_cards { None } else { app.art.fitted(pack, &pack.chars[k.ch], &art, shiny, fit.0, fit.1) };
    let c = Card { pack, ch: k.ch, tier: k.tier, shiny, state, selected: false, count: list.len(), thumb: false, new, card: k.card };
    card::draw(buf, r, &c, img.as_deref(), &t);
    if state == SlotState::Owned && card::is_foil(pack, k.tier, shiny) {
        card::shimmer(buf, r, &tier.frame, shiny, app.anim_phase());
    }
}

fn card_info(app: &mut App, buf: &mut Buffer, r: Rect, t: &Theme, k: SlotKey, side: bool) {
    let state = app.coll.slot_state(k, app.shiny_only);
    let (list, shown_i) = app.shown_pull(k);
    let hp = app.hist_pos(k);
    let pack = &app.coll.packs[k.pack];
    let tier = &pack.tiers[k.tier];
    let shown = shown_i.map(|i| &app.coll.pulls[i]);
    let shiny = shown.is_some_and(|p| p.shiny) || app.shiny_only;
    let (x0, y0, w) = (r.x as i32, r.y as i32, r.width as usize);
    if w < 4 || r.height == 0 {
        return;
    }
    let is_new = state == SlotState::Owned && app.coll.slot_new(k, app.shiny_only);
    let (badge, bc): (String, Rgb) = match state {
        SlotState::Owned if is_new && side => ("● collected · NEW".into(), t.good),
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
        let rows: Vec<(&str, String, Rgb, bool)> = rows
            .into_iter()
            .chain(tag_rows)
            .chain(vec![
                ("pulls", if list.is_empty() { "-".into() } else { format!("×{}", list.len()) }, t.title, true),
                ("first", first.clone().unwrap_or("-".into()), t.fg, false),
                ("last", last.clone().unwrap_or("-".into()), t.fg, false),
                ("skin", shown.map(|p| if p.skin.is_empty() { "—".to_string() } else { p.skin.clone() }).unwrap_or("-".into()), t.accent, false),
                ("seen", if skins.is_empty() { "-".into() } else { skins.join(", ") }, t.dim, false),
                ("", String::new(), t.fg, false),
                ("odds", odds(cp), t.hi, true),
                ("tier", odds(tp), t.fg, false),
                (
                    "rolls",
                    if pack.is_cards {
                        format!("shiny {}", if pack.shiny > 0.0 { odds_short(pack.shiny) } else { "-".into() })
                    } else {
                        format!("foil {:.0}% · shiny {}", pack.foil * 100.0, if pack.shiny > 0.0 { odds_short(pack.shiny) } else { "-".into() })
                    },
                    t.dim,
                    false,
                ),
            ])
            .collect();
        for (i, (l, v, c, b)) in rows.iter().enumerate() {
            let y = y0 + i as i32;
            if i as u16 >= r.height {
                break;
            }
            if l.is_empty() {
                puts(buf, x0, y, &trunc(v, w), *c, None, *b, w);
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
    if is_new {
        l1.push((" · NEW".into(), NEW_PINK, true));
    }
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
    if let (Some(p), Some((h, n))) = (shown, hp) {
        if n > 1 {
            l3.push((format!("pull {}/{} {}  ", h + 1, n, data::when(p.ts, app.now)), t.dim, false));
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
        // the right extras only when the left's first segment still fits whole
        let right_on = rw + 2 + left.first().map(|s| width(&s.0)).unwrap_or(0) <= w;
        if right_on {
            let mut rx = x0 + w as i32 - rw as i32;
            for (s, c, b) in right {
                rx += puts(buf, rx, y, s, *c, None, *b, 30) as i32;
            }
        }
        let limit = x0 + w as i32 - if right_on && rw > 0 { rw as i32 + 2 } else { 0 };
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
        let c = app.pack_completion(i);
        let kind = if p.is_cards { "cards" } else if p.is_big() { "dex" } else { "set" };
        let active = i == app.pack;
        let name_w = 9.min(w / 3);
        puts(buf, x, y, SUP.get(i).copied().unwrap_or(" "), if active { t.hi } else { t.faint }, None, false, 1);
        puts(buf, x + 1, y, &trunc(&p.id, name_w), if active { t.title } else { t.fg }, None, active, name_w);
        let pc = format!("{:>4}", pct(&c));
        let tail = format!(" {kind}");
        let mw = w.saturating_sub(name_w + 2 + pc.len() + tail.len() + 1);
        meter(buf, x + name_w as i32 + 2, y, mw, c.frac(), &t.meter, t.meter_bg);
        let px = x + (name_w + 2 + mw + 1) as i32;
        puts(buf, px, y, &pc, t.title, None, true, 4);
        puts(buf, px + 4, y, &tail, t.faint, None, false, 6);
    }
}

fn tiers_panel(app: &mut App, buf: &mut Buffer, r: Rect, t: &Theme, focused: bool) {
    let pi = app.pack;
    let rows = app.tier_rows();
    let mut ti = Titles::new();
    ti.tl.push(vec![segb("tiers", t.title)]);
    // the panel follows the set on screen (S-08)
    ti.tr.push(match app.current_set() {
        Some(s) => vec![seg("set ", t.faint), seg(s.id.clone(), t.accent)],
        None => vec![seg(app.coll.packs[pi].id.clone(), t.dim)],
    });
    let (_, inner) = panel(buf, r, box_col(t, t.box_stats, focused), t.bg, &ti);
    let p = &app.coll.packs[pi];
    let total: usize = rows.iter().map(|r| r.pulls).sum::<usize>();
    let w = inner.width as usize;
    let longest = rows.iter().map(|r| width(&p.tiers[r.tier].label)).max().unwrap_or(8) + 2;
    let lw = longest.min(if w >= 56 { 22 } else if w >= 44 { 15 } else { 13.min(w / 3) });
    let (x0, y0) = (inner.x as i32, inner.y as i32);
    // columns: label | completion meter + n/m | pull share bar + count
    let mw = ((w.saturating_sub(lw + 2)) * 40 / 100).clamp(3, 14);
    let fw = 8;
    let bx = x0 + (lw + 1 + mw + 1 + fw) as i32;
    let bw = (w as i32 - (bx - x0) - 5).max(0) as usize;
    puts(buf, x0, y0, "tier", t.faint, None, false, lw);
    puts(buf, x0 + lw as i32 + 1, y0, if app.shiny_only { "caught ✦" } else { "caught" }, t.faint, None, false, mw + fw);
    if bw >= 6 {
        puts(buf, bx, y0, "pulls ┊odds", t.faint, None, false, bw + 5);
    }
    let dex = p.is_big();
    for (row, tr) in rows.iter().enumerate() {
        let tier = &p.tiers[tr.tier];
        let y = y0 + 1 + row as i32;
        if y >= (inner.y + inner.height) as i32 {
            break;
        }
        let frac = tr.caught as f32 / tr.of.max(1) as f32;
        put(buf, x0, y, "●", Some(tier.color), None, false);
        puts(buf, x0 + 2, y, &short_label(&tier.label, lw - 2), t.fg, None, false, lw - 2);
        meter(buf, x0 + lw as i32 + 1, y, mw, frac, &t.meter, t.meter_bg);
        let fr = if dex { format!("{}", tr.caught) } else { format!("{}/{}", tr.caught, tr.of) };
        puts(buf, x0 + (lw + 1 + mw + 1) as i32, y, &trunc(&fr, fw - 1), if tr.caught > 0 { t.fg } else { t.dim }, None, false, fw);
        if bw == 0 {
            continue;
        }
        // rarity distribution: share of these pulls, with the expected share tick
        let share = tr.pulls as f32 / total.max(1) as f32;
        let exp = p.tier_p(tr.tier) as f32;
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
            } else if f >= 0.25 || (j == 0 && tr.pulls > 0) {
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
        puts(buf, bx + bw as i32 + 1, y, &format!("{:>3}", tr.pulls), if tr.pulls > 0 { t.title } else { t.faint }, None, tr.pulls > 0, 4);
    }
}

fn activity_panel(app: &mut App, buf: &mut Buffer, r: Rect, t: &Theme, focused: bool) {
    let st = app.stats();
    let pulls = &app.coll.pulls;
    let mut ti = Titles::new();
    ti.tl.push(vec![segb("activity", t.title)]);
    // bucket size: the smallest "nice" step so the graph spans first pull -> now
    let inner_w = r.width.saturating_sub(2) as i64;
    let n = (inner_w * 2).max(2);
    let first = st.first_ts.unwrap_or(app.now);
    let span = (app.now - first).max(60);
    const STEPS: [(i64, &str); 14] = [
        (60, "1m"), (120, "2m"), (300, "5m"), (600, "10m"), (900, "15m"), (1800, "30m"), (3600, "1h"),
        (7200, "2h"), (10800, "3h"), (21600, "6h"), (43200, "12h"), (86400, "1d"), (172800, "2d"), (604800, "1w"),
    ];
    let (step, sname) = STEPS.iter().copied().find(|(s, _)| s * n >= span).unwrap_or((604800, "1w"));
    ti.tr.push(vec![seg("pulls/", t.dim), seg(sname, t.accent)]);
    let end = app.now - app.now.rem_euclid(step) + step;
    let start = end - step * n;
    let mut bins = vec![0u32; n as usize];
    // per bucket: its rarest foil pull (by the odds of its card, so packs compare) (V-13)
    let mut foil_bins: Vec<Option<(f64, Rgb)>> = vec![None; n as usize];
    for (i, p) in pulls.iter().enumerate() {
        if p.ts < start || p.ts >= end {
            continue;
        }
        let b = ((p.ts - start) / step) as usize;
        bins[b] += 1;
        if let Some(k) = app.coll.slot_of[i] {
            let pk = &app.coll.packs[k.pack];
            if pk.foil_tier(k.tier) {
                let odds = pk.card_p(k.tier, p.shiny);
                if foil_bins[b].is_none_or(|(o, _)| odds < o) {
                    foil_bins[b] = Some((odds, pk.tiers[k.tier].color));
                }
            }
        }
    }
    let maxv = bins.iter().copied().max().unwrap_or(0);
    ti.bl.push(vec![seg("peak ", t.faint), seg(maxv.to_string(), t.dim)]);
    let (_, inner) = panel(buf, r, box_col(t, t.box_stats, focused), t.bg, &ti);
    if inner.height < 2 {
        return;
    }
    let max = maxv.max(1) as f32;
    let vals: Vec<f32> = bins.iter().map(|&b| b as f32 / max).collect();
    let gh = inner.height - 1;
    braille(buf, Rect::new(inner.x, inner.y, inner.width, gh), &vals, &t.graph, Some(t.faint));
    // axis: foil markers under their bucket, time labels at the ends
    let ay = (inner.y + gh) as i32;
    for cx in 0..inner.width as usize {
        let pick = [foil_bins.get(cx * 2).copied().flatten(), foil_bins.get(cx * 2 + 1).copied().flatten()]
            .into_iter()
            .flatten()
            .min_by(|a, b| a.0.total_cmp(&b.0));
        match pick {
            Some((_, col)) => put(buf, inner.x as i32 + cx as i32, ay, "▴", Some(col), None, false),
            None => put(buf, inner.x as i32 + cx as i32, ay, "─", Some(mix(t.faint, t.bg_guess, 0.4)), None, false),
        }
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
    // the cutoff (config.txt best_since), subtly, on the bottom border (the top one is too short for both):
    // "since Sep 29", or "rarest" when every pull counts
    ti.bl.push(vec![seg(app.best_since.map_or("rarest".to_string(), |s| format!("since {}", crate::data::date_short(s))), t.dim)]);
    let (_, inner) = panel(buf, r, box_col(t, t.box_stats, focused), t.bg, &ti);
    let rows = inner.height as usize;
    if best.is_empty() {
        puts(buf, inner.x as i32 + 1, inner.y as i32, "no foils yet", t.dim, None, false, 20);
        return;
    }
    app.best_sel = app.best_sel.min(best.len() - 1); // the list can shrink on a reload (D-12)
    let sel = app.best_sel;
    let off = if sel >= rows { sel + 1 - rows } else { 0 };
    let w = inner.width as usize;
    for (row, (i, &(pi, p))) in best.iter().enumerate().skip(off).take(rows).enumerate() {
        let y = inner.y as i32 + row as i32;
        let x = inner.x as i32;
        let pull = &app.coll.pulls[pi];
        let Some(k) = app.coll.slot_of[pi] else { continue };
        let pk = &app.coll.packs[k.pack];
        let tier = &pk.tiers[k.tier];
        let on = focused && i == sel;
        let bg = if on { Some(mix(t.bg_guess, t.hi, 0.18)) } else { None };
        if on {
            fill(buf, Rect::new(inner.x, y as u16, inner.width, 1), bg);
        }
        let rank = format!("{:>2}", i + 1);
        puts(buf, x, y, &rank, if i < 3 { t.hi } else { t.faint }, bg, i < 3, 2);
        put(buf, x + 3, y, "●", Some(tier.color), bg, false);
        let od = odds_short(p);
        let name = format!("{}{}", if pull.shiny { "✦" } else { "" }, pk.name_for(k.ch, k.card));
        let right = format!(" {od}");
        let lab_w = w.saturating_sub(5 + width(&right));
        let name_w = width(&name).min(lab_w);
        puts(buf, x + 5, y, &trunc(&name, name_w), t.title, bg, true, name_w);
        let rest = lab_w.saturating_sub(name_w + 1);
        if rest >= 3 {
            puts(buf, x + 5 + name_w as i32 + 1, y, &short_label(&tier.label, rest), tier.color, bg, false, rest);
        }
        puts(buf, x + w as i32 - width(&right) as i32, y, &right, t.hi, bg, false, width(&right));
        app.hits.best.push((Rect::new(inner.x, y as u16, inner.width, 1), pi));
    }
}

// ---------------------------------------------------------------- set picker

/// `S`: the pack's sets with their completion, filterable by typing; Enter opens one's checklist.
fn picker(app: &mut App, buf: &mut Buffer, area: Rect, t: &Theme) {
    let rows = app.set_rows();
    let Some(pk) = app.picker.clone() else { return };
    let dimbg = t.bg_guess;
    crate::draw::recolor(buf, area, &|_, _, c| mix(c, dimbg, 0.6));
    let w = 76u16.min(area.width.saturating_sub(4)).max(24.min(area.width));
    let want_h = rows.len().max(1) as u16 + 4;
    let h = want_h.min(area.height.saturating_sub(2)).max(5.min(area.height));
    let r = Rect::new(area.x + (area.width - w) / 2, area.y + (area.height.saturating_sub(h)) / 3, w, h);
    let mut ti = Titles::new();
    ti.tl.push(vec![segb("sets", t.title)]);
    ti.tr.push(vec![seg(app.coll.packs[app.pack].name.clone(), t.dim)]);
    ti.bl.push(vec![seg("⏎ ", t.hi), seg("open  ", t.dim), seg("↑↓ ", t.hi), seg("move  ", t.dim), seg("esc ", t.hi), seg("close", t.dim)]);
    let (_, inner) = panel(buf, r, t.box_focus, t.bg.or(Some(t.bg_guess)), &ti);
    app.hits.picker = r;
    if inner.height < 2 || inner.width < 10 {
        return;
    }
    let (x0, iw) = (inner.x as i32 + 1, inner.width.saturating_sub(2) as usize);
    // the filter line
    let fy = inner.y as i32;
    if pk.filter.is_empty() {
        puts(buf, x0, fy, "type to filter: a name, an id, letters in order", t.faint, None, false, iw);
    } else {
        let n = puts(buf, x0, fy, "/", t.hi, None, false, 1);
        let m = puts(buf, x0 + n as i32, fy, &pk.filter, t.title, None, true, iw - 2);
        puts(buf, x0 + (n + m) as i32, fy, "▏", t.hi, None, false, 1);
    }
    let list_h = inner.height.saturating_sub(2) as usize;
    let ly = inner.y as i32 + 2;
    if rows.is_empty() {
        puts(buf, x0, ly, &format!("no set matches “{}”", pk.filter), t.warn, None, false, iw);
        return;
    }
    let sel = pk.sel.min(rows.len() - 1);
    let off = if sel >= list_h { sel + 1 - list_h } else { 0 };
    // columns (right to left): pct 4 | bar 10 | counts 9 | id 8 | name (the rest); narrow: the id, then the bar go
    let counts_w = rows.iter().map(|r| format!("{}/{}", r.done.owned, r.done.total).len()).max().unwrap_or(5);
    let id_w = rows.iter().map(|r| width(&r.id)).max().unwrap_or(0).min(10);
    let show_bar = iw >= 44;
    let show_id = iw >= 56 && id_w > 0;
    let bar_w = if show_bar { 10 } else { 0 };
    let right_w = 4 + 1 + if show_bar { bar_w + 2 } else { 0 } + counts_w + if show_id { id_w + 3 } else { 0 };
    let name_w = iw.saturating_sub(2 + right_w);
    let cur = app.set_sel[app.pack];
    for (row, (i, sr)) in rows.iter().enumerate().skip(off).take(list_h).enumerate() {
        let y = ly + row as i32;
        let on = i == sel;
        let bg = if on { Some(mix(t.bg_guess, t.hi, 0.2)) } else { None };
        if on {
            fill(buf, Rect::new(inner.x, y as u16, inner.width, 1), bg);
        }
        let mark = if sr.ix == cur { ("●", t.hi) } else { (" ", t.dim) };
        puts(buf, x0, y, mark.0, mark.1, bg, false, 1);
        let fg = if sr.ix == 0 { t.dim } else { t.title };
        let nw = puts(buf, x0 + 2, y, &trunc(&sr.name, name_w), fg, bg, on || sr.ix == cur, name_w);
        if let Some(n) = sr.hits {
            let s = format!(" {n} found");
            if nw + width(&s) <= name_w {
                puts(buf, x0 + 2 + nw as i32, y, &s, t.accent, bg, false, name_w - nw);
            }
        }
        let mut x = x0 + iw as i32 - right_w as i32;
        if show_id {
            puts(buf, x, y, &trunc(&sr.id, id_w), t.dim, bg, false, id_w);
            x += id_w as i32 + 3;
        }
        let cnt = format!("{}/{}", sr.done.owned, sr.done.total);
        puts(buf, x + (counts_w - cnt.len()) as i32, y, &cnt, if sr.done.owned > 0 { t.fg } else { t.dim }, bg, false, counts_w);
        x += counts_w as i32 + 2;
        if show_bar {
            meter(buf, x, y, bar_w, sr.done.frac(), &t.meter, t.meter_bg);
            x += bar_w as i32;
        }
        puts(buf, x, y, &format!("{:>4}", pct(&sr.done)), if sr.done.owned > 0 { t.title } else { t.faint }, bg, sr.done.owned > 0, 4);
        app.hits.picker_rows.push((Rect::new(inner.x, y as u16, inner.width, 1), i));
    }
    if rows.len() > list_h {
        let note = format!(" {}-{} of {} ", off + 1, (off + list_h).min(rows.len()), rows.len());
        puts(buf, r.x as i32 + r.width as i32 - 2 - width(&note) as i32, r.y as i32 + r.height as i32 - 1, &note, t.dim, None, false, 20);
    }
}

// ---------------------------------------------------------------- help

fn help(app: &mut App, buf: &mut Buffer, area: Rect, t: &Theme) {
    let dimbg = t.bg_guess;
    crate::draw::recolor(buf, area, &|_, _, c| mix(c, dimbg, 0.72));
    let keys: &[(&str, &str)] = &[
        ("← → ↑ ↓   h j k l", "move in the binder; the edges flip pages"),
        ("PgUp PgDn  space  wheel", "flip binder pages"),
        ("g G   Home End", "first / last card"),
        ("⏎", "open the card (focus the card panel)"),
        ("1-9   [ ]   n N   click", "switch pack"),
        ("tab   shift-tab", "cycle panels: binder › card › stats"),
        ("← →   in card", "step through this card's pulls (↑ ↓ scroll the text half)"),
        ("↑ ↓ ⏎   in stats", "pick a best pull and open it"),
        ("S   click the set tab", "sets: pick one (type to filter) · its checklist"),
        ("#", "jump to a printed number in the set: #17  #TG05  #B"),
        ("/", "search: the binder shows only the matching cards; ⏎ opens one on its real page"),
        ("  pikchu  lyc vmax", "  forgiving: letters in order (evs rainbow), every word must match"),
        ("  set:evolving set:swsh7", "  a set by name or id  ·  number:17  id:swsh7-17  -holo leaves out"),
        ("  rarity:\"rare rainbow\"", "  type:water  subtype:vmax  artist:…  name:…"),
        ("  owned missing pending", "  state words (also new shiny foil); tab completes; esc goes back"),
        ("o   m", "owned only (earned) · missing only"),
        ("s", "shiny-only binder"),
        ("v", "the card's text half (moves, HP, weakness) under the art"),
        ("d", "view: every card / one slot per character (dex)"),
        ("t", "cycle theme"),
        ("L", "jump to the latest pull"),
        ("r", "reload pulls.log (it also reloads by itself)"),
        ("? F1", "this help (↑ ↓ scroll)"),
        ("esc", "clear the search, then quit"),
        ("q   ctrl-c", "quit"),
    ];
    let w = 96u16.min(area.width.saturating_sub(4)).max(20.min(area.width));
    let h = (keys.len() as u16 + 4).min(area.height.saturating_sub(2)).max(3.min(area.height));
    let r = Rect::new(area.x + (area.width - w) / 2, area.y + (area.height.saturating_sub(h)) / 2, w, h);
    let rows = h.saturating_sub(2) as usize;
    let total = keys.len() + 2; // + a blank row + the legend
    let more = total.saturating_sub(rows);
    app.help_scroll = app.help_scroll.min(more);
    let off = app.help_scroll;
    let mut ti = Titles::new();
    ti.tl.push(vec![segb("help", t.title)]);
    ti.tr.push(vec![seg("theme ", t.dim), segb(t.name, t.accent)]);
    if more > 0 {
        ti.br.push(vec![seg(format!("↑↓ {}/{} · any key closes", off + rows.min(total), total), t.dim)]);
    } else {
        ti.br.push(vec![seg("any key closes", t.dim)]);
    }
    let (_, inner) = panel(buf, r, t.box_focus, t.bg.or(Some(t.bg_guess)), &ti);
    app.hits.help = r;
    app.hits.help_more = more;
    // the key column shrinks on narrow terminals; descriptions are cut, never overlapped
    let kw = if inner.width >= 70 { 26 } else { (inner.width as usize / 3).max(8) };
    let (x0, y0) = (inner.x as i32 + 2, inner.y as i32);
    let dw = inner.width.saturating_sub(kw as u16 + 4) as usize;
    for (row, i) in (off..total).take(rows).enumerate() {
        let y = y0 + row as i32;
        if let Some((k, d)) = keys.get(i) {
            puts(buf, x0, y, &trunc(k, kw - 1), t.hi, None, true, kw - 1);
            puts(buf, x0 + kw as i32, y, &trunc(d, dw), t.fg, None, false, dw);
        } else if i == keys.len() + 1 {
            let legend: Vec<(&str, Rgb, &str)> = vec![("● ", t.good, "earned  "), ("◌ ", t.warn, "pending: use its tab  "), ("NEW ", NEW_PINK, "not viewed  "), ("┆ ", t.slot_line, "not pulled")];
            let mut x = x0;
            let end = (inner.x + inner.width) as i32 - 1;
            for (s, c, d) in legend {
                x += puts(buf, x, y, s, c, None, true, (end - x).max(0) as usize) as i32;
                x += puts(buf, x, y, d, t.dim, None, false, (end - x).max(0) as usize) as i32;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn odds_text() {
        assert_eq!(odds_short(0.0), "—", "a shiny in a pack without shinies (D-08)");
        assert_eq!(odds_short(1.0 / 5027.0), "1/5027");
        assert_eq!(odds_short(1.0 / 14000.0), "1/14k");
        assert_eq!(odds(0.0), "never");
    }

    #[test]
    fn short_labels() {
        assert_eq!(short_label("rare holo VMAX", 20), "rare holo VMAX");
        assert_eq!(short_label("rare holo VMAX", 11), "R holo VMAX");
        assert_eq!(short_label("rare holo VSTAR", 11), "RH VSTAR");
        assert_ne!(short_label("rare holo VMAX", 11), short_label("rare holo VSTAR", 11), "V-07: distinct tiers stay distinct");
        assert_eq!(short_label("special illustration rare", 11), "sp illus R");
        assert_eq!(short_label("illustration rare", 11), "illus R");
        assert_eq!(short_label("pikachu rare", 11), "pika R");
        assert_eq!(short_label("rare holo VMAX", 7), "RH VMAX");
    }

    #[test]
    fn pct_never_lies() {
        assert_eq!(pct(&Completion { owned: 1, pending: 0, total: 342 }), "1%");
        assert_eq!(pct(&Completion { owned: 341, pending: 0, total: 342 }), "99%");
        assert_eq!(pct(&Completion { owned: 0, pending: 3, total: 342 }), "0%");
        assert_eq!(pct(&Completion { owned: 5, pending: 0, total: 5 }), "100%");
    }
}
