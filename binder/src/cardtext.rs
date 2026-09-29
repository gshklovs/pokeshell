//! The card's text half (docs/CARD_FORMAT.md): name, HP, abilities, attacks, weakness / resistance / retreat, set
//! and artist, stacked under the art like a real card (`v`). The box is the card's width, in the tier's colour.

use crate::color::{Rgb, lighten, mix, rgb};
use crate::draw::{put, puts, take_cells, trunc, width};
use crate::theme::Theme;
use ratatui::buffer::Buffer;
use ratatui::layout::Rect;
use serde_json::Value;

/// A run of text in one style.
#[derive(Clone)]
pub struct Run {
    pub text: String,
    pub fg: Rgb,
    pub bold: bool,
}

fn run(text: impl Into<String>, fg: Rgb, bold: bool) -> Run {
    Run { text: text.into(), fg, bold }
}

/// One row of the box: runs from the left, and runs pinned to the right edge (HP, damage).
#[derive(Clone, Default)]
pub struct Row {
    pub left: Vec<Run>,
    pub right: Vec<Run>,
}

/// Energy colours: one `●` per energy, one cell each (no emoji: they are two cells wide).
pub fn energy(t: &str) -> Rgb {
    match t.to_ascii_lowercase().as_str() {
        "grass" => rgb(0x7ac74c),
        "fire" => rgb(0xee6b3b),
        "water" => rgb(0x4aa8e8),
        "lightning" => rgb(0xf7d02c),
        "psychic" => rgb(0xb36bd0),
        "fighting" => rgb(0xc2703d),
        "darkness" => rgb(0x6d7f8c),
        "metal" => rgb(0xa8b4c0),
        "fairy" => rgb(0xee99ac),
        "dragon" => rgb(0xc9a227),
        _ => rgb(0xd8d8d8), // colorless
    }
}

fn s<'a>(v: &'a Value, k: &str) -> &'a str {
    v.get(k).and_then(|x| x.as_str()).unwrap_or("")
}

fn arr<'a>(v: &'a Value, k: &str) -> Vec<&'a Value> {
    v.get(k).and_then(|x| x.as_array()).map(|a| a.iter().collect()).unwrap_or_default()
}

fn strs(v: &Value, k: &str) -> Vec<String> {
    arr(v, k).iter().filter_map(|x| x.as_str().map(String::from)).collect()
}

/// Word-wrap to `w` cells (long words are cut).
pub fn wrap(text: &str, w: usize) -> Vec<String> {
    let w = w.max(4);
    let mut out = Vec::new();
    for para in text.split('\n') {
        let mut line = String::new();
        for word in para.split_whitespace() {
            let mut word = word.to_string();
            while width(&word) > w {
                if !line.is_empty() {
                    out.push(std::mem::take(&mut line));
                }
                let head = take_cells(&word, w);
                if head.is_empty() {
                    break;
                }
                word = word[head.len()..].to_string();
                out.push(head);
            }
            if line.is_empty() {
                line = word;
            } else if width(&line) + 1 + width(&word) <= w {
                line.push(' ');
                line.push_str(&word);
            } else {
                out.push(std::mem::replace(&mut line, word));
            }
        }
        if !line.is_empty() {
            out.push(line);
        }
    }
    out
}

fn text_rows(rows: &mut Vec<Row>, text: &str, w: usize, fg: Rgb) {
    for l in wrap(text, w) {
        rows.push(Row { left: vec![run(l, fg, false)], right: vec![] });
    }
}

fn glyphs(types: &[String]) -> Vec<Run> {
    types.iter().map(|t| run("●", energy(t), false)).collect()
}

/// The rows of the text half for an inner width `w`.
pub fn rows(v: &Value, w: usize, t: &Theme, accent: Rgb) -> Vec<Row> {
    let mut out: Vec<Row> = Vec::new();
    // header: name, subtype badge .. HP + type glyph
    let name = s(v, "name");
    let mut head = vec![run(name, t.title, true)];
    let subs = strs(v, "subtypes");
    // the mechanic badge (V, VMAX, ex ...) in the accent, unless the name already ends with it ("Rayquaza V", V-02):
    // then the stage (Basic, Stage 1) in dim
    let last = name.split_whitespace().last().unwrap_or("");
    let badge = subs.iter().find(|x| matches!(x.as_str(), "V" | "VMAX" | "VSTAR" | "EX" | "ex" | "GX" | "BREAK" | "MEGA" | "Radiant" | "V-UNION"));
    match badge {
        Some(b) if !b.eq_ignore_ascii_case(last) => head.push(run(format!(" {b}"), accent, true)),
        _ => {
            if let Some(stage) = subs.iter().find(|x| Some(*x) != badge) {
                head.push(run(format!(" {stage}"), t.dim, false));
            }
        }
    }
    let mut right = vec![];
    if !s(v, "hp").is_empty() {
        right.push(run("HP ", t.dim, false));
        right.push(run(s(v, "hp"), t.title, true));
        right.push(run(" ", t.dim, false));
    }
    right.extend(glyphs(&strs(v, "types")));
    out.push(Row { left: head, right });
    if !s(v, "evolvesFrom").is_empty() {
        out.push(Row { left: vec![run(format!("evolves from {}", s(v, "evolvesFrom")), t.dim, false)], right: vec![] });
    }
    // abilities
    for a in arr(v, "abilities") {
        out.push(Row::default());
        let kind = if s(a, "type").is_empty() { "Ability" } else { s(a, "type") };
        out.push(Row { left: vec![run(format!("{kind} "), rgb(0xe25c5c), true), run(s(a, "name"), t.title, true)], right: vec![] });
        text_rows(&mut out, s(a, "text"), w, t.fg);
    }
    // attacks: cost, name .. damage; the text under it
    for a in arr(v, "attacks") {
        out.push(Row::default());
        let mut left = glyphs(&strs(a, "cost"));
        if !left.is_empty() {
            left.push(run(" ", t.fg, false));
        }
        left.push(run(s(a, "name"), t.title, true));
        out.push(Row { left, right: vec![run(s(a, "damage"), t.title, true)] });
        if !s(a, "text").is_empty() {
            text_rows(&mut out, s(a, "text"), w, t.fg);
        }
    }
    for r in strs(v, "rules") {
        out.push(Row::default());
        text_rows(&mut out, &r, w, t.dim);
    }
    // footer: weakness / resistance / retreat, then set, number, rarity, artist
    out.push(Row::default());
    let mut foot = vec![run("weak ", t.dim, false)];
    let weak = arr(v, "weaknesses");
    if weak.is_empty() {
        foot.push(run("-", t.faint, false));
    }
    for x in weak {
        foot.push(run("●", energy(s(x, "type")), false));
        foot.push(run(s(x, "value"), t.fg, false));
    }
    foot.push(run("  resist ", t.dim, false));
    let res = arr(v, "resistances");
    if res.is_empty() {
        foot.push(run("-", t.faint, false));
    }
    for x in res {
        foot.push(run("●", energy(s(x, "type")), false));
        foot.push(run(s(x, "value"), t.fg, false));
    }
    let retreat = strs(v, "retreatCost");
    foot.push(run("  retreat ", t.dim, false));
    if retreat.is_empty() {
        foot.push(run("-", t.faint, false));
    }
    foot.extend(glyphs(&retreat));
    out.push(Row { left: foot, right: vec![] });
    let set = v.get("set").map(|x| s(x, "name").to_string()).unwrap_or_default();
    let total = v.get("set").and_then(|x| x.get("printedTotal")).and_then(|x| x.as_u64());
    let num = match (s(v, "number"), total) {
        ("", _) => String::new(),
        (n, Some(tot)) => format!("{n}/{tot}"),
        (n, None) => n.to_string(),
    };
    let mut line = vec![set, num, s(v, "rarity").to_string()];
    line.retain(|x| !x.is_empty());
    if !line.is_empty() {
        text_rows(&mut out, &line.join(" · "), w, t.dim);
    }
    if !s(v, "artist").is_empty() {
        text_rows(&mut out, &format!("illus. {}", s(v, "artist")), w, t.faint);
    }
    if !s(v, "flavorText").is_empty() {
        out.push(Row::default());
        text_rows(&mut out, s(v, "flavorText"), w, mix(t.dim, t.faint, 0.3));
    }
    out
}

/// How tall the box is for this card at this outer width (rows + the two border rows).
pub fn height(v: &Value, outer_w: u16, t: &Theme) -> u16 {
    rows(v, outer_w.saturating_sub(4) as usize, t, t.accent).len() as u16 + 2
}

/// Draw the text half in `r` (its top row is the box's top edge), scrolled down `scroll` rows. When it doesn't fit,
/// the borders say so (▲ / ▼ n more) and the rest scrolls (↑↓ with the card focused, or the wheel). Returns the scroll
/// used (clamped) and how many rows are still hidden below.
pub fn draw(buf: &mut Buffer, r: Rect, v: &Value, line: Rgb, t: &Theme, scroll: usize) -> (usize, usize) {
    if r.width < 8 || r.height < 3 {
        return (0, 0);
    }
    let (x0, y0, x1, y1) = (r.x as i32, r.y as i32, (r.x + r.width - 1) as i32, (r.y + r.height - 1) as i32);
    let bg = t.card_bg;
    for y in y0..=y1 {
        for x in x0..=x1 {
            put(buf, x, y, " ", None, Some(bg), false);
        }
    }
    let edge = Some(t.bg.unwrap_or(t.bg_guess));
    for x in x0 + 1..x1 {
        put(buf, x, y0, "─", Some(line), edge, false);
        put(buf, x, y1, "─", Some(line), edge, false);
    }
    for y in y0 + 1..y1 {
        put(buf, x0, y, "│", Some(line), edge, false);
        put(buf, x1, y, "│", Some(line), edge, false);
    }
    put(buf, x0, y0, "╭", Some(line), edge, false);
    put(buf, x1, y0, "╮", Some(line), edge, false);
    put(buf, x0, y1, "╰", Some(line), edge, false);
    put(buf, x1, y1, "╯", Some(line), edge, false);
    let w = r.width.saturating_sub(4) as usize;
    let all = rows(v, w, t, lighten(line, 0.2));
    let room = r.height.saturating_sub(2) as usize;
    let scroll = scroll.min(all.len().saturating_sub(room));
    let below = all.len().saturating_sub(scroll + room);
    let (left_x, right_x) = (x0 + 2, x0 + 2 + w as i32); // the text column: [left_x, right_x)
    for (i, row) in all.iter().skip(scroll).take(room).enumerate() {
        let y = y0 + 1 + i as i32;
        // the right runs (HP, damage) keep their cells when they fit; the left text stops a cell before them
        let rw: usize = row.right.iter().map(|r| width(&r.text)).sum::<usize>().min(w);
        let limit = right_x - if rw > 0 { rw as i32 + 1 } else { 0 };
        let mut x = left_x;
        for run in &row.left {
            let room = (limit - x).max(0) as usize;
            if room == 0 {
                break;
            }
            x += puts(buf, x, y, &trunc(&run.text, room), run.fg, Some(bg), run.bold, room) as i32;
        }
        let mut rx = (right_x - rw as i32).max(left_x);
        for run in &row.right {
            let room = (right_x - rx).max(0) as usize;
            rx += puts(buf, rx, y, &run.text, run.fg, Some(bg), run.bold, room) as i32;
        }
    }
    let dim = t.dim;
    if scroll > 0 {
        puts(buf, x1 - 4, y0, " ▲ ", dim, edge, false, 3);
    }
    if below > 0 {
        let note = format!(" ▼ {below} more ");
        puts(buf, x1 - 1 - width(&note) as i32, y1, &note, dim, edge, false, 20);
    }
    (scroll, below)
}
