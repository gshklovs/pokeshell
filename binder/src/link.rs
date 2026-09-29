//! binder-link: what the pokeshell:// handler runs when you Ctrl+click the `binder ⏎` link under a pulled card.
//!
//!   binder-link --root <dir> [--state <dir>] --url pokeshell://binder?pull=<id>
//!   binder-link ... --dry-run     print the command it would run (one argument per line), run nothing
//!
//! A windowless (GUI-subsystem) program, so a click never flashes a console window: it checks the link (only
//! `?pull=<ulid>` and `?card=<pack/character/tier>`, as `binder --url` does) and hands Windows Terminal
//! `wt -w 0 sp -V -- binder.exe --root ... --pull <id>`, which splits the pane you clicked in and runs the binder
//! there. The link itself never reaches wt.exe, so a crafted link can't smuggle in wt commands (`;`). Without
//! wt.exe it opens the binder in a console window of its own.
#![cfg_attr(windows, windows_subsystem = "windows")]

mod linkurl;

use linkurl::Link;
use std::path::PathBuf;
use std::process::Command;

fn wt_exe() -> PathBuf {
    // the app execution alias survives Windows Terminal updates (its package folder is versioned)
    if let Ok(l) = std::env::var("LOCALAPPDATA") {
        let p = PathBuf::from(l).join("Microsoft").join("WindowsApps").join("wt.exe");
        if p.exists() {
            return p;
        }
    }
    PathBuf::from("wt.exe")
}

fn main() {
    let mut root = None;
    let mut state = None;
    let mut link = None;
    let mut dry = false;
    let mut it = std::env::args().skip(1);
    while let Some(a) = it.next() {
        match a.as_str() {
            "--root" => root = it.next(),
            "--state" => state = it.next(),
            "--url" => link = it.next().and_then(|u| linkurl::parse_url(&u)),
            "--pull" => link = it.next().filter(|v| linkurl::is_pull_id(v)).map(Link::Pull),
            "--card" => link = it.next().filter(|v| linkurl::is_card_spec(v)).map(Link::Card),
            "--dry-run" => dry = true,
            _ => {}
        }
    }
    let Some(link) = link else { std::process::exit(2) };
    let exe = std::env::current_exe().ok();
    let binder = exe.as_ref().and_then(|e| e.parent()).map(|d| d.join(if cfg!(windows) { "binder.exe" } else { "binder" }));
    let Some(binder) = binder else { std::process::exit(1) };
    let binder = binder.to_string_lossy().to_string();
    let wt = wt_exe();
    let args = linkurl::wt_args(&binder, root.as_deref(), state.as_deref(), &link);
    if dry {
        println!("{}", wt.display());
        for a in &args {
            println!("{a}");
        }
        return;
    }
    if Command::new(&wt).args(&args).spawn().is_ok() {
        return;
    }
    // no Windows Terminal: the binder in a console window of its own (the args after wt's `--`)
    let own: Vec<&String> = args.iter().skip_while(|a| a.as_str() != "--").skip(2).collect();
    let mut c = Command::new(&binder);
    c.args(own.iter().map(|a| a.replace("\\;", ";")));
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        c.creation_flags(0x0000_0010); // CREATE_NEW_CONSOLE
    }
    let _ = c.spawn();
}
