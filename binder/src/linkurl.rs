//! The `binder ⏎` link under a pulled card: `pokeshell://binder?pull=<ulid>` (or `?card=<pack/character/tier>`).
//! Shared by the binder (`--url`) and `binder-link.exe`, the small windowless launcher the pokeshell:// handler runs
//! (docs/BINDER_SPEC.md, "Click"): it turns a link into a Windows Terminal split pane running the binder.

const CROCKFORD: &[u8] = b"0123456789ABCDEFGHJKMNPQRSTVWXYZ";

/// A pull id: a 26-character Crockford base32 ULID (so it can never carry a `;`, a quote or a space).
pub fn is_pull_id(s: &str) -> bool {
    s.len() == 26 && s.bytes().all(|c| CROCKFORD.contains(&c.to_ascii_uppercase()))
}

#[derive(Clone, Debug, PartialEq)]
pub enum Link {
    Pull(String),
    Card(String),
}

/// pokeshell://binder?pull=<ulid> | pokeshell://binder?card=<pack/character/tier>. Anything else is ignored (the
/// URL comes from a link anyone could write, so only these two exact shapes are accepted). The scheme and host are
/// case-insensitive, a slash after the host or at the end is fine (the shell adds one: `pokeshell://binder/?pull=`),
/// and the pull/card parameter may come after others (D-06).
pub fn parse_url(u: &str) -> Option<Link> {
    let u = u.trim();
    let lower = u.to_ascii_lowercase();
    if !lower.starts_with("pokeshell://") {
        return None;
    }
    let rest = &u["pokeshell://".len()..];
    let rest = if rest.len() >= 6 && rest[..6].eq_ignore_ascii_case("binder") { &rest[6..] } else { rest };
    let q = rest.trim_start_matches('/').strip_prefix('?')?;
    for pair in q.split('&') {
        let Some((k, v)) = pair.split_once('=') else { continue };
        let v = v.trim_end_matches('/').replace("%2F", "/").replace("%2f", "/").replace("%20", " ").replace('+', " ");
        match k.to_ascii_lowercase().as_str() {
            "pull" if is_pull_id(&v) => return Some(Link::Pull(v)),
            "card" if is_card_spec(&v) => return Some(Link::Card(v)),
            "pull" | "card" => return None,
            _ => {}
        }
    }
    None
}

/// A card spec from a link: letters, digits, `-_./` and spaces only, at most three parts.
pub fn is_card_spec(v: &str) -> bool {
    !v.is_empty() && v.len() <= 120 && v.chars().all(|c| c.is_ascii_alphanumeric() || "-_./ ".contains(c)) && v.matches('/').count() <= 2
}

/// wt.exe treats `;` as its command separator, in any argument: escape it (`\;` is a literal semicolon).
#[allow(dead_code)] // (the binder itself only parses links)
fn wt_escape(s: &str) -> String {
    s.replace(';', "\\;")
}

/// The wt.exe arguments that open the binder on `link` in a split pane of the current window: `-w 0` is the most
/// recently used window, which is the one the link was clicked in. `--` ends wt's own options, so the binder's
/// `--root` / `--pull` can't be read as wt's. The only free text is the root and state paths (escaped); a pull id or
/// card spec was validated above and has no `;`.
#[allow(dead_code)]
pub fn wt_args(binder: &str, root: Option<&str>, state: Option<&str>, link: &Link) -> Vec<String> {
    let mut a: Vec<String> = ["-w", "0", "sp", "-V", "--title", "binder", "--"].iter().map(|s| s.to_string()).collect();
    a.push(wt_escape(binder));
    if let Some(r) = root {
        a.push("--root".into());
        a.push(wt_escape(r));
    }
    if let Some(s) = state {
        a.push("--state".into());
        a.push(wt_escape(s));
    }
    match link {
        Link::Pull(id) => {
            a.push("--pull".into());
            a.push(id.clone());
        }
        Link::Card(c) => {
            a.push("--card".into());
            a.push(c.clone());
        }
    }
    a
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn urls() {
        assert_eq!(parse_url("pokeshell://binder?pull=01M3NZHEB37XPA8TAG8Z9MZ8C3"), Some(Link::Pull("01M3NZHEB37XPA8TAG8Z9MZ8C3".into())));
        assert_eq!(parse_url("pokeshell://binder/?pull=01M3NZHEB37XPA8TAG8Z9MZ8C3"), Some(Link::Pull("01M3NZHEB37XPA8TAG8Z9MZ8C3".into())), "the shell's form");
        assert_eq!(parse_url("pokeshell://binder?pull=01M3NZHEB37XPA8TAG8Z9MZ8C3;nt;calc"), None);
        assert_eq!(parse_url("pokeshell://binder?card=pokemon/x;nt"), None);
        assert!(!is_pull_id("01M3NZHEB37XPA8TAG8Z9MZ8C3;nt"));
    }

    #[test]
    fn wt_command() {
        let a = wt_args(r"C:\p s\binder.exe", Some(r"C:\a;b"), None, &Link::Pull("01M3NZHEB37XPA8TAG8Z9MZ8C3".into()));
        assert_eq!(a.join(" "), r"-w 0 sp -V --title binder -- C:\p s\binder.exe --root C:\a\;b --pull 01M3NZHEB37XPA8TAG8Z9MZ8C3");
        let a = wt_args("b.exe", Some("r"), Some("s"), &Link::Card("pokemon/pikachu/holo".into()));
        assert_eq!(a[a.len() - 4..].join(" "), "--state s --card pokemon/pikachu/holo");
    }
}
