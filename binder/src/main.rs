//! pokeshell binder: a btop-style TUI for your card pulls.
//!
//!   binder                     run it (reads the real pulls.log + packs/*/pack.json); opens on the last card you caught
//!   binder --pull <id>         open on that pull (its id is the tab's POKESHELL_PULL; not caught yet: its silhouette)
//!   binder --pull latest       open on the newest pull (the Ctrl+Shift+B pane): the last card pulled, unless it has
//!                              expired (then the last card you caught)
//!   binder --card <pack/character/tier>   open on that card
//!   binder --url pokeshell://binder?pull=<id>   the card's link (binder-link.exe hands it over as --pull; also ?card=...)
//!   binder --search <query>    open with a search: words and tag filters (set:evolving rarity:"rare rainbow" type:water caught)
//!   binder --set <set>         open on a set's checklist: its id or name, fuzzy (swsh7, evolving, "30th")
//!   binder --state <dir>       the state folder (default: $POKESHELL_HOME, else %LOCALAPPDATA%\pokeshell)
//!   binder --root <dir>        the pokeshell checkout (default: $POKESHELL_ROOT, else found from the exe / cwd)
//!   binder --theme btop        start with a theme (holo | btop | gameboy | term)
//!   binder --snapshot DIR      render headless frames (TestBackend) to DIR/*.ans
//!   binder --bench             time cold load + first full frame + redraw costs (in-memory backend)
//!   binder --first-frame       load, paint + encode one frame, exit (for wall-clock startup timing)
//!   binder --text              with --first-frame / --bench: the text half (v) on
//!   binder --selftest          fuzz keys/mouse/resizes through the event handler, rendering each
//!   binder --demo-pending N    preview the earned rule: treat the N newest pulls as pending (seen, not caught)
//!   binder --export-web DIR    write the web binder (data.json, img\, binder.html) into DIR and exit (webexport.rs;
//!                              `pokeshell binder --web`); --no-art: no art decoded or written; --owner NAME: the cover's
//!                              name (default: $POKESHELL_OWNER, else the user name); --only ID,ID,...: incremental,
//!                              only these cards' images are (re)rendered, every other image is taken from the art
//!                              cache as it is (no stat, no prune); data.json and binder.html are still rewritten
//!
//! In the app, `p` shows the real printed card beside ours (caught cards; the scan is downloaded once into
//! <state>\cache\realcards). POKESHELL_SIXEL=on|off|auto: sixel or half blocks (auto asks the terminal, DA1).

mod app;
mod art;
mod card;
mod cardtext;
mod color;
mod data;
mod draw;
mod linkurl;
mod query;
mod real;
mod snapshot;
mod theme;
mod ui;
mod webexport;

use app::{App, Opts, Start};
use crossterm::event::{self, DisableFocusChange, DisableMouseCapture, EnableFocusChange, EnableMouseCapture};
use crossterm::execute;
use crossterm::terminal::{EnterAlternateScreen, LeaveAlternateScreen, disable_raw_mode, enable_raw_mode};
use ratatui::Terminal;
use ratatui::backend::CrosstermBackend;
use ratatui::buffer::Buffer;
use ratatui::layout::Rect;
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

fn is_root(p: &Path) -> bool {
    p.join("packs").is_dir() && p.join("scripts").join("pokeshell.ps1").is_file()
}

/// The pokeshell checkout: --root, $POKESHELL_ROOT, or walk up from the exe / the cwd.
fn find_root(arg: Option<String>) -> Option<PathBuf> {
    if let Some(a) = arg.or_else(|| std::env::var("POKESHELL_ROOT").ok()) {
        return Some(PathBuf::from(a));
    }
    let starts = [std::env::current_exe().ok(), std::env::current_dir().ok()];
    for s in starts.into_iter().flatten() {
        let mut p: Option<&Path> = Some(&s);
        while let Some(d) = p {
            if is_root(d) {
                return Some(d.to_path_buf());
            }
            p = d.parent();
        }
    }
    None
}

/// The state folder: $POKESHELL_HOME (what the PowerShell side uses), $POKESHELL_STATE, %LOCALAPPDATA%\pokeshell
/// (Windows), else $XDG_STATE_HOME/pokeshell.
fn default_state() -> PathBuf {
    for v in ["POKESHELL_HOME", "POKESHELL_STATE"] {
        if let Ok(s) = std::env::var(v) {
            if !s.is_empty() {
                return PathBuf::from(s);
            }
        }
    }
    if let Ok(l) = std::env::var("LOCALAPPDATA") {
        return PathBuf::from(l).join("pokeshell");
    }
    let base = std::env::var("XDG_STATE_HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from(std::env::var("HOME").unwrap_or_default()).join(".local").join("state"));
    base.join("pokeshell")
}

/// The `binder ⏎` link (linkurl.rs): only `?pull=<ulid>` and `?card=<pack/character/tier>` are accepted.
fn parse_url(u: &str) -> Option<Start> {
    linkurl::parse_url(u).map(|l| match l {
        linkurl::Link::Pull(id) => Start::Pull(id),
        linkurl::Link::Card(c) => Start::Card(c),
    })
}

struct Args {
    root: Option<String>,
    log: Option<String>,
    state: Option<String>,
    start: Start,
    search: String,
    set: String,
    theme: String,
    snapshot: Option<String>,
    bench: bool,
    first_only: bool,
    text: bool,
    selftest: bool,
    demo_pending: usize,
    export_web: Option<String>,
    owner: Option<String>,
    no_art: bool,
    only: Option<Vec<String>>,
    number_order: Option<String>,
}

fn parse_args() -> Args {
    let mut a = Args {
        root: None,
        log: None,
        state: None,
        start: Start::Latest,
        search: String::new(),
        set: String::new(),
        theme: "holo".into(),
        snapshot: None,
        bench: false,
        first_only: false,
        text: false,
        selftest: false,
        demo_pending: 0,
        export_web: None,
        owner: None,
        no_art: false,
        only: None,
        number_order: None,
    };
    let mut it = std::env::args().skip(1).peekable();
    // a flag's value: the next argument, unless it is another flag (D-07: `--state --snapshot x` is an error, not a
    // state folder called --snapshot)
    let val = |flag: &str, it: &mut std::iter::Peekable<std::iter::Skip<std::env::Args>>| -> String {
        match it.peek() {
            Some(v) if !v.starts_with("--") => it.next().unwrap_or_default(),
            _ => {
                eprintln!("binder: {flag} needs a value (try --help)");
                std::process::exit(2);
            }
        }
    };
    while let Some(x) = it.next() {
        match x.as_str() {
            "--root" => a.root = Some(val("--root", &mut it)),
            "--log" => a.log = Some(val("--log", &mut it)),
            "--state" => a.state = Some(val("--state", &mut it)),
            "--search" => a.search = val("--search", &mut it),
            "--set" => a.set = val("--set", &mut it),
            "--pull" => {
                let v = val("--pull", &mut it);
                a.start = if v.eq_ignore_ascii_case("latest") { Start::Newest } else { Start::Pull(v) }
            }
            "--card" => a.start = Start::Card(val("--card", &mut it)),
            "--url" => {
                let u = val("--url", &mut it);
                match parse_url(&u) {
                    Some(s) => a.start = s,
                    None => eprintln!("binder: ignoring the link {u:?} (not a pokeshell://binder?pull= or ?card= link)"),
                }
            }
            "--theme" => a.theme = val("--theme", &mut it),
            "--snapshot" => a.snapshot = Some(val("--snapshot", &mut it)),
            "--bench" => a.bench = true,
            "--selftest" => a.selftest = true,
            "--first-frame" => {
                a.bench = true;
                a.first_only = true
            }
            "--text" => a.text = true,
            "--export-web" => a.export_web = Some(val("--export-web", &mut it)),
            "--owner" => a.owner = Some(val("--owner", &mut it)),
            "--no-art" => a.no_art = true,
            "--only" => a.only = Some(val("--only", &mut it).split([',', ' ']).map(str::trim).filter(|x| !x.is_empty()).map(str::to_string).collect()),
            // (tests: the web export's checklist order of card numbers, comma-separated in, sorted out)
            "--number-order" => a.number_order = Some(it.next().unwrap_or_default()),
            "--demo-pending" => a.demo_pending = val("--demo-pending", &mut it).parse().unwrap_or(0),
            "-h" | "--help" => {
                println!("{}", include_str!("main.rs").lines().take_while(|l| l.starts_with("//!")).map(|l| l.trim_start_matches("//!")).collect::<Vec<_>>().join("\n"));
                std::process::exit(0);
            }
            other => {
                eprintln!("binder: unknown argument {other} (try --help)");
                std::process::exit(2);
            }
        }
    }
    a
}

fn main() -> io::Result<()> {
    let t0 = Instant::now();
    let args = parse_args();
    if let Some(list) = &args.number_order {
        let mut v: Vec<&str> = list.split(',').collect();
        v.sort_by_key(|n| webexport::number_key(n));
        println!("{}", v.join(","));
        return Ok(());
    }
    let Some(root) = find_root(args.root.clone()) else {
        eprintln!("binder: can't find the pokeshell checkout (use --root or POKESHELL_ROOT)");
        std::process::exit(1);
    };
    if !root.join("packs").is_dir() {
        eprintln!("binder: {} is not a pokeshell checkout (no packs folder)", root.display());
        std::process::exit(1);
    }
    let state = args.state.clone().map(PathBuf::from).unwrap_or_else(default_state);
    if let Some(out) = &args.export_web {
        let o = webexport::Opts { root, state, log: args.log.clone().map(PathBuf::from), out: PathBuf::from(out), owner: args.owner.clone(), no_art: args.no_art, only: args.only.clone() };
        std::process::exit(webexport::run(o));
    }
    let log = args.log.clone().map(PathBuf::from).unwrap_or_else(|| state.join("pulls.log"));
    let viewed = log.parent().map(|d| d.join("viewed.txt")).unwrap_or_else(|| state.join("viewed.txt"));
    let headless = args.snapshot.is_some() || args.selftest || args.bench;
    let opts = Opts {
        root,
        log,
        viewed,
        demo_pending: args.demo_pending,
        start: args.start.clone(),
        readonly: headless,
        search: args.search.clone(),
        set: args.set.clone(),
    };
    let theme = theme::by_name(&args.theme);

    if let Some(dir) = args.snapshot {
        return snapshot::run(opts, theme, Path::new(&dir));
    }
    if args.selftest {
        return snapshot::selftest(opts, theme);
    }
    if args.bench {
        return snapshot::bench(opts, theme, t0, args.first_only, args.text);
    }

    let mut app = App::new(opts, theme);
    require_packs(&app);
    run(&mut app)
}

/// No pack loaded (an empty packs folder, or every pack.json unreadable): say so and exit, rather than draw an empty
/// binder (T-01).
pub fn require_packs(app: &App) {
    if app.coll.packs.is_empty() {
        eprintln!("binder: no packs found under {} (every packs/*/pack.json is missing or unreadable)", app.opts.root.join("packs").display());
        std::process::exit(1);
    }
}

fn restore() {
    let _ = disable_raw_mode();
    let _ = execute!(io::stdout(), DisableMouseCapture, DisableFocusChange, LeaveAlternateScreen, crossterm::cursor::Show);
}

fn run(app: &mut App) -> io::Result<()> {
    enable_raw_mode()?;
    let mut out = io::stdout();
    execute!(out, EnterAlternateScreen, EnableMouseCapture, EnableFocusChange, crossterm::cursor::Hide)?;
    let prev = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        restore();
        prev(info);
    }));
    let mut term = Terminal::new(CrosstermBackend::new(io::BufWriter::with_capacity(1 << 16, out)))?;
    term.clear()?;
    let res = event_loop(app, &mut term);
    restore();
    res
}

/// Ask the terminal whether it does sixel (DA1, real.rs): write `ESC [ c` and read its reply, which arrives as
/// keystrokes, for up to real::PROBE_MS. Keys typed meanwhile are handed on; a reply that comes later is swallowed
/// by the filter.
fn probe_sixel<W: Write>(app: &mut App, term: &mut Terminal<CrosstermBackend<W>>, filter: &mut real::ReplyFilter) -> io::Result<()> {
    use crossterm::event::{Event, KeyCode, KeyEventKind};
    if !cfg!(windows) {
        // crossterm's Unix reader keeps DA1 replies to itself: there, sixel is POKESHELL_SIXEL / config.txt only
        app.real.gfx = Some(real::Gfx::Blocks);
        return Ok(());
    }
    term.backend_mut().write_all(b"\x1b[c")?;
    term.backend_mut().flush()?;
    let end = Instant::now() + Duration::from_millis(real::PROBE_MS);
    let mut reply = String::new();
    let mut other: Vec<Event> = vec![];
    while let Some(left) = end.checked_duration_since(Instant::now()) {
        if !event::poll(left)? {
            break;
        }
        let ev = event::read()?;
        let ch = match &ev {
            Event::Key(k) if k.kind != KeyEventKind::Release => match k.code {
                KeyCode::Esc => Some('\x1b'),
                KeyCode::Char(c) => Some(c),
                _ => None,
            },
            _ => None,
        };
        match ch {
            // (the console host hands the reply over as keystrokes, and on Windows the ESC doesn't come through:
            // it starts at "[?")
            Some(c @ ('\x1b' | '[')) if reply.is_empty() => reply.push(c),
            Some(c) if !reply.is_empty() => {
                reply.push(c);
                if c == 'c' || reply.len() > 96 {
                    break;
                }
            }
            _ => other.push(ev),
        }
    }
    let got = real::da1_has_sixel(&reply);
    app.real.gfx = Some(if got == Some(true) { real::Gfx::Sixel } else { real::Gfx::Blocks });
    if got.is_none() {
        filter.armed = true; // no reply yet: if one turns up late, it is not typed into the binder
        // what was collected wasn't a reply after all: those were keys
        for c in reply.chars() {
            let code = if c == '\x1b' { KeyCode::Esc } else { KeyCode::Char(c) };
            other.push(Event::Key(crossterm::event::KeyEvent::new(code, crossterm::event::KeyModifiers::NONE)));
        }
    }
    for ev in other {
        app.on_event(ev);
    }
    app.dirty = true;
    Ok(())
}

/// A key event through the late-reply filter: what to hand the app.
fn filtered(filter: &mut real::ReplyFilter, ev: event::Event) -> Vec<event::Event> {
    use crossterm::event::{Event, KeyCode, KeyEvent, KeyEventKind, KeyModifiers};
    if !filter.armed {
        return vec![ev];
    }
    let ch = match &ev {
        Event::Key(k) if k.kind != KeyEventKind::Release => match k.code {
            KeyCode::Esc => Some('\x1b'),
            KeyCode::Char(c) => Some(c),
            _ => None,
        },
        Event::Key(_) => return vec![],
        _ => return vec![ev],
    };
    let to_ev = |c: char| if c == '\x1b' { Event::Key(KeyEvent::new(KeyCode::Esc, KeyModifiers::NONE)) } else { Event::Key(KeyEvent::new(KeyCode::Char(c), KeyModifiers::NONE)) };
    match filter.feed(ch) {
        real::Filtered::Pass(cs) => {
            let mut out: Vec<Event> = cs.iter().take(cs.len().saturating_sub(ch.is_some() as usize)).map(|&c| to_ev(c)).collect();
            out.push(ev); // the event itself, as it came (its modifiers intact)
            out
        }
        _ => vec![],
    }
}

/// The sixel image of the printed card, when the last full frame asked for one: written at its rect after the
/// frame (the frame leaves those cells blank). A frame that drops or moves it clears the screen first, since text
/// drawn by the diff alone would leave the old image's pixels behind.
fn sixel_after_frame<W: Write>(app: &mut App, term: &mut Terminal<CrosstermBackend<W>>, shown: &mut Option<(Rect, String)>, force: bool) -> io::Result<Option<Buffer>> {
    let want = app.hits.sixel.clone();
    if want == *shown && !(force && want.is_some()) {
        return Ok(None);
    }
    let mut repainted = None;
    if shown.is_some() {
        // the old image goes first: gone, moved, or another card's (whose transparent corners would keep the old
        // one's pixels); a resize has cleared the screen already
        if !force {
            term.clear()?;
            let done = term.draw(|f| ui::render(app, f.buffer_mut()))?;
            repainted = Some(done.buffer.clone());
        }
    }
    let want = app.hits.sixel.clone();
    if let Some((r, url)) = &want {
        if let Some(img) = app.real.sixel_for(url, r.width, r.height) {
            let b = term.backend_mut();
            write!(b, "\x1b7\x1b[{};{}H", r.y + 1, r.x + 1)?;
            b.write_all(img.as_bytes())?;
            b.write_all(b"\x1b8")?;
            b.flush()?;
        }
    }
    *shown = want;
    Ok(repainted)
}

fn event_loop<W: Write>(app: &mut App, term: &mut Terminal<CrosstermBackend<W>>) -> io::Result<()> {
    // Last full frame: animation frames start from it and repaint only the card.
    let mut cached: Option<Buffer> = None;
    let mut anim_due = false;
    let mut minute = app.now / 60;
    // the sixel image on screen (the printed card, p), and the late-DA1-reply filter
    let mut sixel_shown: Option<(Rect, String)> = None;
    let mut filter = real::ReplyFilter::default();
    let mut filter_until = Instant::now();
    loop {
        if app.show_real && app.real.gfx.is_none() {
            probe_sixel(app, term, &mut filter)?;
            filter_until = Instant::now() + Duration::from_secs(3);
        }
        if app.dirty || cached.is_none() {
            let before = cached.as_ref().map(|b| b.area);
            let done = term.draw(|f| ui::render(app, f.buffer_mut()))?;
            let resized = before != Some(done.area);
            cached = Some(done.buffer.clone());
            if let Some(b) = sixel_after_frame(app, term, &mut sixel_shown, resized)? {
                cached = Some(b); // (redrawn after a clear)
            }
            app.dirty = false;
            anim_due = false;
            // the card on screen: its NEW sticker is cleared for next time (only if the card panel showed it, D-15)
            if !app.help && app.picker.is_none() && app.hits.card_art.width > 0 {
                app.mark_seen();
            }
        } else if anim_due {
            let base = cached.as_ref().unwrap();
            term.draw(|f| {
                let b = f.buffer_mut();
                if b.area == base.area {
                    b.content.clone_from_slice(&base.content);
                    ui::render_card(app, b);
                } else {
                    ui::render(app, b);
                }
            })?;
            anim_due = false;
        }
        if app.quit {
            return Ok(());
        }
        // Sleep until the next thing can change: an input event, the next shimmer frame
        // (only while a foil card is on screen and mid-sweep), or the clock's next minute.
        let now_s = data::now_local();
        // (and every couple of seconds: pulls.log is polled, so a new pull shows up while the binder is open, D-10)
        let to_minute = Duration::from_millis(((60 - now_s.rem_euclid(60)) * 1000 + 50) as u64).min(Duration::from_millis(2000));
        let timeout = if app.animating() {
            let ph = app.anim_phase();
            if ph < card::SWEEP {
                Duration::from_millis(66)
            } else {
                Duration::from_secs_f32(((1.0 - ph) * card::CYCLE_SECS).max(0.01))
            }
            .min(to_minute)
        } else {
            to_minute
        };
        // an opened search result glows on its real page: redraw it as it fades
        let timeout = if app.flash.is_some() { timeout.min(Duration::from_millis(50)) } else { timeout };
        // a printed card downloading: look for it often (it shows as soon as it lands); a held ESC: settle it soon
        let timeout = if app.real.busy() || filter.armed { timeout.min(Duration::from_millis(100)) } else { timeout };
        if event::poll(timeout)? {
            // drain everything queued (wheel bursts, resize storms) before drawing once
            loop {
                let ev = event::read()?;
                for ev in filtered(&mut filter, ev) {
                    app.on_event(ev);
                }
                if app.quit || !event::poll(Duration::ZERO)? {
                    break;
                }
            }
            if app.real.poll() {
                app.dirty = true;
            }
        } else {
            for c in filter.flush() {
                let code = if c == '\x1b' { crossterm::event::KeyCode::Esc } else { crossterm::event::KeyCode::Char(c) };
                app.on_event(event::Event::Key(crossterm::event::KeyEvent::new(code, crossterm::event::KeyModifiers::NONE)));
            }
            if filter.armed && Instant::now() > filter_until {
                filter.armed = false; // no late reply came
            }
            if app.real.poll() {
                app.dirty = true;
            }
            if app.flash_tick() {
                app.dirty = true;
            }
            let n = data::now_local();
            if app.poll_reload() {
                app.now = n;
            }
            if n / 60 != minute {
                minute = n / 60;
                app.now = n;
                app.dirty = true;
            } else if !app.dirty && app.animating() {
                anim_due = true;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn urls() {
        assert_eq!(parse_url("pokeshell://binder?pull=01M3NZHEB37XPA8TAG8Z9MZ8C3"), Some(Start::Pull("01M3NZHEB37XPA8TAG8Z9MZ8C3".into())));
        assert_eq!(parse_url("pokeshell://binder/?card=pokemon%2Fpikachu%2Fholo"), Some(Start::Card("pokemon/pikachu/holo".into())));
        assert_eq!(parse_url("pokeshell://binder?pull=nope"), None);
        assert_eq!(parse_url("pokeshell://binder?card=a/b/c/d"), None);
        assert_eq!(parse_url("pokeshell://binder?card=x\";calc"), None);
        assert_eq!(parse_url("https://example.com/?pull=01M3NZHEB37XPA8TAG8Z9MZ8C3"), None);
        // D-06: other params first, a trailing slash, upper-case scheme/host
        assert_eq!(parse_url("pokeshell://binder?x=1&pull=01M3NZHEB37XPA8TAG8Z9MZ8C3"), Some(Start::Pull("01M3NZHEB37XPA8TAG8Z9MZ8C3".into())));
        assert_eq!(parse_url("pokeshell://binder?pull=01M3NZHEB37XPA8TAG8Z9MZ8C3/"), Some(Start::Pull("01M3NZHEB37XPA8TAG8Z9MZ8C3".into())));
        assert_eq!(parse_url("POKESHELL://Binder/?card=pokemon/swsh7-92"), Some(Start::Card("pokemon/swsh7-92".into())));
        assert_eq!(parse_url("pokeshell://binder?pull=nope&card=pokemon/x"), None, "a bad pull value is not skipped over");
    }
}