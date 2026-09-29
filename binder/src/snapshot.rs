//! Headless rendering: TestBackend frames dumped as truecolor ANSI (+ plain text), and a timing bench.
//! tools/snap.py turns the .ans files into PNGs via the repo's tools/render_ansi.py.

use crate::app::{App, Focus, Opts};
use crate::data::SlotKey;
use crate::theme::THEMES;
use crate::ui;
use ratatui::Terminal;
use ratatui::backend::TestBackend;
use ratatui::buffer::Buffer;
use ratatui::style::{Color, Modifier};
use std::fmt::Write as _;
use std::io;
use std::path::Path;
use std::time::Instant;

pub fn to_ansi(buf: &Buffer) -> String {
    let a = buf.area;
    let mut s = String::with_capacity((a.width as usize * 24) * a.height as usize);
    for y in a.y..a.y + a.height {
        let mut last = String::new();
        for x in a.x..a.x + a.width {
            let c = &buf[(x, y)];
            let mut code = String::from("0");
            if c.modifier.contains(Modifier::BOLD) {
                code.push_str(";1");
            }
            if let Color::Rgb(r, g, b) = c.fg {
                let _ = write!(code, ";38;2;{r};{g};{b}");
            }
            if let Color::Rgb(r, g, b) = c.bg {
                let _ = write!(code, ";48;2;{r};{g};{b}");
            }
            if code != last {
                let _ = write!(s, "\x1b[{code}m");
                last = code;
            }
            s.push_str(if c.symbol().is_empty() { " " } else { c.symbol() });
        }
        s.push_str("\x1b[0m\n");
    }
    s
}

pub fn to_text(buf: &Buffer) -> String {
    let a = buf.area;
    let mut s = String::new();
    for y in a.y..a.y + a.height {
        for x in a.x..a.x + a.width {
            s.push_str(buf[(x, y)].symbol());
        }
        s.push('\n');
    }
    s
}

fn frame(app: &mut App, w: u16, h: u16) -> Buffer {
    let mut term = Terminal::new(TestBackend::new(w, h)).unwrap();
    let done = term.draw(|f| ui::render(app, f.buffer_mut())).unwrap();
    done.buffer.clone()
}

fn find(app: &App, pack: &str, ch: &str, tier: &str) -> Option<SlotKey> {
    let pi = app.coll.packs.iter().position(|p| p.id == pack)?;
    let p = &app.coll.packs[pi];
    let (ci, ti) = (*p.char_ix.get(ch)?, p.tier_ix(tier)?);
    let card = p.card_list.iter().position(|c| c.ch == ci && c.tier == ti).map(|i| i as u32).unwrap_or(crate::data::NO_CARD);
    Some(SlotKey { pack: pi, ch: ci, tier: ti, card })
}

fn save(dir: &Path, name: &str, buf: &Buffer) -> io::Result<()> {
    std::fs::write(dir.join(format!("{name}.ans")), to_ansi(buf))?;
    std::fs::write(dir.join(format!("{name}.txt")), to_text(buf))?;
    println!("wrote {name} ({}x{})", buf.area.width, buf.area.height);
    Ok(())
}

pub fn run(opts: Opts, theme: usize, dir: &Path) -> io::Result<()> {
    crate::require_packs(&App::new(Opts { log: dir.join("-none-"), ..opts.clone() }, theme));
    std::fs::create_dir_all(dir)?;
    let mk = |pending: usize| {
        let mut app = App::new(Opts { demo_pending: pending, ..opts.clone() }, theme);
        app.phase_override = Some(0.9); // resting (no band) unless a scenario sets one
        app
    };

    // 1. main view: whatever you pulled last
    let mut app = mk(0);
    save(dir, "main-120x40", &frame(&mut app, 120, 40))?;

    // 2. foil detail: the rainbow-frame ultra rare, card panel focused, shimmer band mid-sweep
    let mut app = mk(0);
    if let Some(k) = find(&app, "pokemon", "bulbasaur", "ultra-rare") {
        app.jump_to(k, None);
    }
    app.focus = Focus::Card;
    app.phase_override = Some(0.22);
    save(dir, "foil-120x40", &frame(&mut app, 120, 40))?;
    // a few shimmer frames for the animation strip
    for (i, ph) in [0.05f32, 0.15, 0.25, 0.35, 0.45].iter().enumerate() {
        app.phase_override = Some(*ph);
        save(dir, &format!("shimmer-{i}"), &frame(&mut app, 120, 40))?;
    }

    // 3. narrow layout
    let mut app = mk(0);
    if let Some(k) = find(&app, "pokemon", "charmander", "secret-rare") {
        app.jump_to(k, None);
    }
    app.phase_override = Some(0.3);
    save(dir, "narrow-80x24", &frame(&mut app, 80, 24))?;
    app.compact_right = Focus::Stats;
    app.focus = Focus::Stats;
    save(dir, "narrow-stats-80x24", &frame(&mut app, 80, 24))?;

    // 4. help overlay
    let mut app = mk(0);
    app.help = true;
    save(dir, "help-120x40", &frame(&mut app, 120, 40))?;

    // extras: one piece wanted posters, the pokedex, pending preview, big terminal, themes
    let mut app = mk(0);
    if let Some(k) = find(&app, "onepiece", "zoro", "manga-rare") {
        app.jump_to(k, None);
    }
    app.phase_override = Some(0.25);
    save(dir, "onepiece-120x40", &frame(&mut app, 120, 40))?;

    let mut app = mk(3);
    save(dir, "pending-120x40", &frame(&mut app, 120, 40))?;

    let mut app = mk(0);
    if let Some(k) = find(&app, "pokemon", "charmander", "secret-rare") {
        app.jump_to(k, None);
    }
    app.phase_override = Some(0.3);
    save(dir, "big-160x50", &frame(&mut app, 160, 50))?;

    for (ti, t) in THEMES.iter().enumerate().skip(1) {
        let mut app = mk(0);
        app.theme = ti;
        if let Some(k) = find(&app, "pokemon", "charmander", "holo") {
            app.jump_to(k, None);
        }
        save(dir, &format!("theme-{}", t.name), &frame(&mut app, 120, 40))?;
    }

    let mut app = mk(0);
    app.pack = app.coll.packs.iter().position(|p| p.id == "pokedex").unwrap_or(0);
    app.toggle_shiny();
    save(dir, "shiny-120x40", &frame(&mut app, 120, 40))?;

    // the text half (v) on the newest pull, and the same at a small size
    let mut app = mk(0);
    app.show_text = true;
    if let Some(k) = find(&app, "pokemon", "pikachu", "common") {
        app.jump_to(k, None);
    }
    save(dir, "text-120x40", &frame(&mut app, 120, 40))?;
    save(dir, "text-80x24", &frame(&mut app, 80, 24))?;

    // a set's checklist and a tag search
    let mut app = mk(0);
    if let Some(pi) = app.coll.packs.iter().position(|p| !p.sets.is_empty()) {
        app.pack = pi;
        app.choose_set(1);
    }
    save(dir, "set-120x40", &frame(&mut app, 120, 40))?;
    let mut app = mk(0);
    app.search = "type:darkness vmax".into();
    save(dir, "tags-120x40", &frame(&mut app, 120, 40))?;

    let mut app = mk(0);
    app.search = "char".into();
    app.searching = true;
    app.pack = 0;
    save(dir, "search-120x40", &frame(&mut app, 120, 40))?;
    qa_scenes(&opts, theme, dir)
}

/// The QA scenes, each at 120x40, 80x24 and 200x60: qa-<scene>-<w>x<h>. The main view, a set's checklist (--set),
/// the set picker (S), search results (a word, and set + rarity tags) and the text half (v) of a V card.
fn qa_scenes(opts: &Opts, theme: usize, dir: &Path) -> io::Result<()> {
    let sizes = [(120u16, 40u16), (80, 24), (200, 60)];
    type Setup = fn(&mut App);
    let scenes: Vec<(&str, Opts, Setup)> = vec![
        ("main", opts.clone(), |_| {}),
        ("set", Opts { set: "evolving".into(), ..opts.clone() }, |_| {}),
        ("picker", opts.clone(), |app| app.on_event(key('S'))),
        ("search", Opts { search: "pikachu".into(), ..opts.clone() }, |_| {}),
        ("search-page1", Opts { search: "pikachu".into(), ..opts.clone() }, |app| app.on_event(key('g'))),
        ("search-owned", Opts { search: "pikachu owned".into(), ..opts.clone() }, |_| {}),
        ("search-tags", Opts { search: "set:30th rarity:\"pikachu rare\"".into(), ..opts.clone() }, |_| {}),
        ("search-typing", opts.clone(), |app| {
            for c in "/set:evo".chars() {
                app.on_event(key(c));
            }
        }),
        ("text", Opts { start: crate::app::Start::Card("pokemon/swsh7-218".into()), ..opts.clone() }, |app| app.on_event(key('v'))),
        ("text-scrolled", Opts { start: crate::app::Start::Card("pokemon/swsh7-218".into()), ..opts.clone() }, |app| {
            app.on_event(key('v'));
            app.focus = crate::app::Focus::Card;
        }),
        ("dex", opts.clone(), |app| app.on_event(key('d'))),
        ("url-lycanroc", Opts { start: crate::app::Start::Pull("01M3PVNCBPMN1R80FRY6ZMVD19".into()), ..opts.clone() }, |_| {}),
        ("missing", Opts { set: "evolving".into(), ..opts.clone() }, |app| app.on_event(key('m'))),
        ("nomatch", Opts { search: "set:zzz foo:bar".into(), ..opts.clone() }, |_| {}),
        ("help", opts.clone(), |app| app.on_event(key('?'))),
    ];
    for (name, o, setup) in scenes {
        for &(w, h) in &sizes {
            let mut app = App::new(o.clone(), theme);
            app.phase_override = Some(0.9);
            setup(&mut app);
            if name == "text-scrolled" {
                // scroll the text half as a user would: a frame first (it measures what is hidden), then ↓ x6
                frame(&mut app, w, h);
                for _ in 0..6 {
                    app.on_event(crossterm::event::Event::Key(crossterm::event::KeyEvent::new(crossterm::event::KeyCode::Down, crossterm::event::KeyModifiers::NONE)));
                    frame(&mut app, w, h);
                }
            }
            save(dir, &format!("qa-{name}-{w}x{h}"), &frame(&mut app, w, h))?;
        }
    }
    // small terminals: the binder as a list, the header and borders degrading
    for (w, h) in [(40u16, 12u16), (60, 10), (30, 8), (20, 6)] {
        let mut app = App::new(opts.clone(), theme);
        app.phase_override = Some(0.9);
        save(dir, &format!("qa-small-{w}x{h}"), &frame(&mut app, w, h))?;
    }
    Ok(())
}

fn key(c: char) -> crossterm::event::Event {
    use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
    let m = if c.is_ascii_uppercase() { KeyModifiers::SHIFT } else { KeyModifiers::NONE };
    Event::Key(KeyEvent::new(KeyCode::Char(c), m))
}

/// Cold start: parse the log + packs, lay out, paint a full frame and encode it (what the real
/// terminal gets), then an animation frame. Prints timings in ms.
pub fn bench(opts: Opts, theme: usize, t0: Instant, first_only: bool) -> io::Result<()> {
    let t_args = t0.elapsed();
    let mut app = App::new(opts, theme);
    crate::require_packs(&app);
    let t_load = t0.elapsed();
    let mut term = Terminal::new(TestBackend::new(120, 40)).unwrap();
    let base = term.draw(|f| ui::render(&mut app, f.buffer_mut())).unwrap().buffer.clone();
    let ansi = to_ansi(&base);
    let t_frame = t0.elapsed();
    if first_only {
        use std::io::Write;
        io::stdout().write_all(ansi.as_bytes())?;
        return Ok(());
    }
    // steady state: one shimmer frame (repaint only the card on a copy of the last frame)
    let n = 200;
    let ta = Instant::now();
    for i in 0..n {
        app.phase_override = Some(i as f32 / n as f32 * 0.55);
        term.draw(|f| {
            let b = f.buffer_mut();
            b.content.clone_from_slice(&base.content);
            ui::render_card(&mut app, b);
        })
        .unwrap();
    }
    let per_anim = ta.elapsed() / n;
    let tf = Instant::now();
    for _ in 0..50 {
        app.dirty = true;
        term.draw(|f| ui::render(&mut app, f.buffer_mut())).unwrap();
    }
    let per_full = tf.elapsed() / 50;
    // a keypress: move the selection (new card panel, history, text) and redraw; a search keystroke (the slot list
    // is recomputed) and redraw
    use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
    let k = |c: KeyCode| Event::Key(KeyEvent::new(c, KeyModifiers::NONE));
    let tk = Instant::now();
    for i in 0..50 {
        app.on_event(k(if i % 10 < 5 { KeyCode::Right } else { KeyCode::Left }));
        term.draw(|f| ui::render(&mut app, f.buffer_mut())).unwrap();
    }
    let per_key = tk.elapsed() / 50;
    app.on_event(k(KeyCode::Char('/')));
    let ts = Instant::now();
    for c in "set:evolving rare ".chars() {
        app.on_event(k(KeyCode::Char(c)));
        term.draw(|f| ui::render(&mut app, f.buffer_mut())).unwrap();
    }
    let per_search = ts.elapsed() / 18;
    println!(
        "args {:.2} ms | load (log + packs) {:.2} ms | first frame {:.2} ms ({} KB ansi) | full redraw {:.3} ms | keypress + redraw {:.3} ms | search keystroke + redraw {:.3} ms | shimmer frame {:.3} ms | pulls {} packs {}",
        t_args.as_secs_f64() * 1e3,
        t_load.as_secs_f64() * 1e3,
        t_frame.as_secs_f64() * 1e3,
        ansi.len() / 1024,
        per_full.as_secs_f64() * 1e3,
        per_key.as_secs_f64() * 1e3,
        per_search.as_secs_f64() * 1e3,
        per_anim.as_secs_f64() * 1e3,
        app.coll.pulls.len(),
        app.coll.packs.len()
    );
    Ok(())
}

/// Drive the real event handler with a scripted + pseudo-random stream of keys, mouse clicks,
/// wheel and resizes, rendering (full + animation path) after each, at many sizes. Panics = failure.
pub fn selftest(opts: Opts, theme: usize) -> io::Result<()> {
    use crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers, MouseButton, MouseEvent, MouseEventKind};
    let mut app = App::new(opts, theme);
    crate::require_packs(&app);
    let key = |c: KeyCode| Event::Key(KeyEvent::new(c, KeyModifiers::NONE));
    let shift = |c: char| Event::Key(KeyEvent::new(KeyCode::Char(c), KeyModifiers::SHIFT));
    let ctrl = |c: char| Event::Key(KeyEvent::new(KeyCode::Char(c), KeyModifiers::CONTROL));
    let mut script: Vec<Event> = vec![
        key(KeyCode::Right), key(KeyCode::Down), key(KeyCode::PageDown), key(KeyCode::Char('2')), key(KeyCode::Left),
        key(KeyCode::Tab), key(KeyCode::Right), key(KeyCode::Tab), key(KeyCode::Down), key(KeyCode::Enter),
        key(KeyCode::Char('/')), key(KeyCode::Char('z')), key(KeyCode::Char('o')), key(KeyCode::Enter), key(KeyCode::Esc),
        key(KeyCode::Char('s')), key(KeyCode::Char('3')), key(KeyCode::Char('d')), key(KeyCode::Char('v')), shift('S'), key(KeyCode::End), key(KeyCode::Char('s')),
        key(KeyCode::Char('t')), key(KeyCode::Char('?')), key(KeyCode::Char('x')), key(KeyCode::Char('o')), key(KeyCode::Char('L')),
        // the set picker: open, move both ways, filter, backspace, pick; reopen and close; then # and search editing
        key(KeyCode::Char('1')), shift('S'), key(KeyCode::Down), key(KeyCode::Down), key(KeyCode::Up), key(KeyCode::Tab), key(KeyCode::BackTab),
        shift('S'), key(KeyCode::PageDown), key(KeyCode::PageUp), key(KeyCode::Char('e')), key(KeyCode::Char('v')), key(KeyCode::Backspace),
        key(KeyCode::Char('z')), key(KeyCode::Char('q')), key(KeyCode::Enter), shift('S'), key(KeyCode::Esc), shift('S'), key(KeyCode::Char('3')), key(KeyCode::Char('0')),
        key(KeyCode::Esc), key(KeyCode::Esc), shift('S'), key(KeyCode::End), key(KeyCode::Enter), key(KeyCode::Char('m')), key(KeyCode::Char('d')), key(KeyCode::Char('m')),
        key(KeyCode::Char('#')), key(KeyCode::Char('1')), key(KeyCode::Char('7')), key(KeyCode::Enter), key(KeyCode::Char('#')), key(KeyCode::Backspace),
        key(KeyCode::Char('/')), key(KeyCode::Char('s')), key(KeyCode::Char('e')), key(KeyCode::Char('t')), key(KeyCode::Char(':')), key(KeyCode::Tab), key(KeyCode::Char('3')),
        key(KeyCode::Tab), key(KeyCode::Left), key(KeyCode::Left), key(KeyCode::Delete), key(KeyCode::Home), key(KeyCode::End), ctrl('w'), ctrl('u'), key(KeyCode::Enter),
        key(KeyCode::Char('v')), key(KeyCode::Tab), key(KeyCode::Down), key(KeyCode::Down), key(KeyCode::Up), key(KeyCode::Char('v')), ctrl('s'), ctrl('q'),
    ];
    // every picker row, both directions, at each size (the picker is re-rendered after each key)
    for _ in 0..4 {
        script.extend([shift('S'), key(KeyCode::Down), key(KeyCode::Enter), shift('S'), key(KeyCode::Up), key(KeyCode::Up), key(KeyCode::Enter)]);
    }
    let sizes = [(120u16, 40u16), (80, 24), (60, 20), (45, 16), (200, 60), (100, 30), (40, 12), (20, 6), (10, 3)];
    let mut seed = 0x1234_5678u32;
    let mut rnd = move |n: u32| {
        seed ^= seed << 13;
        seed ^= seed >> 17;
        seed ^= seed << 5;
        seed % n.max(1)
    };
    let keys = [
        KeyCode::Left, KeyCode::Right, KeyCode::Up, KeyCode::Down, KeyCode::PageUp, KeyCode::PageDown, KeyCode::Tab, KeyCode::BackTab,
        KeyCode::Enter, KeyCode::Char('s'), KeyCode::Char('o'), KeyCode::Char('m'), KeyCode::Char('v'), KeyCode::Char('d'), KeyCode::Char('S'), KeyCode::Char('S'),
        KeyCode::Char('1'), KeyCode::Char('2'), KeyCode::Char('3'), KeyCode::Char('/'), KeyCode::Char('#'), KeyCode::Char('a'), KeyCode::Char('e'), KeyCode::Char(':'),
        KeyCode::Backspace, KeyCode::Delete, KeyCode::Home, KeyCode::End, KeyCode::Esc, KeyCode::Char('?'), KeyCode::Char('g'), KeyCode::Char('G'),
        KeyCode::Char(']'), KeyCode::Char('t'),
    ];
    let mut steps = 0;
    for (si, &(w, h)) in sizes.iter().enumerate() {
        let mut term = Terminal::new(TestBackend::new(w, h)).unwrap();
        let evs: Vec<Event> = if si == 0 {
            script.clone()
        } else {
            let mut v: Vec<Event> = script.clone();
            v.extend((0..400).map(|_| match rnd(10) {
                    0..=6 => {
                        let c = keys[rnd(keys.len() as u32) as usize];
                        let m = if c == KeyCode::Char('S') { KeyModifiers::SHIFT } else { KeyModifiers::NONE };
                        Event::Key(KeyEvent::new(c, m))
                    }
                    7 | 8 => Event::Mouse(MouseEvent {
                        kind: match rnd(3) {
                            0 => MouseEventKind::Down(MouseButton::Left),
                            1 => MouseEventKind::ScrollDown,
                            _ => MouseEventKind::ScrollUp,
                        },
                        column: rnd(w as u32) as u16,
                        row: rnd(h as u32) as u16,
                        modifiers: KeyModifiers::NONE,
                    }),
                    _ => Event::Resize(w, h),
                }));
            v
        };
        for ev in evs {
            app.quit = false;
            app.on_event(ev);
            app.phase_override = Some(rnd(100) as f32 / 180.0);
            let base = term.draw(|f| ui::render(&mut app, f.buffer_mut())).unwrap().buffer.clone();
            term.draw(|f| {
                let b = f.buffer_mut();
                b.content.clone_from_slice(&base.content);
                ui::render_card(&mut app, b);
            })
            .unwrap();
            steps += 1;
        }
    }
    println!("selftest ok: {steps} events rendered across {} sizes", sizes.len());
    Ok(())
}
