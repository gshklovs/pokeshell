//! Search: free text plus tag filters (docs/BINDER_SPEC.md "Tags and search"), the same syntax as the web binder.
//!
//!   evolving skies            every word must match somewhere (name, character, card id, number, any tag value)
//!   set:swsh7                 a tag filter: key:value (the value is a case-insensitive substring)
//!   rarity:"rare rainbow"     quotes keep spaces
//!   type:water vmax           filters and words combine (all must match)
//!   shiny  foil  new  pending owned  missing     state words: bare, or as is:shiny
//!
//! Keys: set (id or name), rarity, tier, type, subtype (sub), char (character), artist, pack, name, number, id (card).

/// One search term: a key (None: free text) and a lower-cased value.
#[derive(Clone, Debug, PartialEq)]
pub struct Term {
    pub key: Option<String>,
    pub value: String,
}

/// The state words: they test the slot, not its tags.
pub const STATES: &[&str] = &["shiny", "foil", "new", "pending", "owned", "missing"];

fn canon_key(k: &str) -> String {
    match k {
        "sub" | "subtypes" => "subtype".into(),
        "character" | "pokemon" => "char".into(),
        "types" => "type".into(),
        "card" => "id".into(),
        "no" | "num" => "number".into(),
        "setname" | "series" => "set".into(),
        other => other.to_string(),
    }
}

/// Split a query into terms. `key:value` / `key:"a b"` are filters; `"a b"` is one free-text phrase.
pub fn parse(q: &str) -> Vec<Term> {
    let mut out = Vec::new();
    let cs: Vec<char> = q.chars().collect();
    let mut i = 0;
    while i < cs.len() {
        if cs[i].is_whitespace() {
            i += 1;
            continue;
        }
        // a word, possibly key:, possibly quoted
        let mut key: Option<String> = None;
        let start = i;
        while i < cs.len() && !cs[i].is_whitespace() && cs[i] != ':' && cs[i] != '"' {
            i += 1;
        }
        if i < cs.len() && cs[i] == ':' && i > start {
            key = Some(canon_key(&cs[start..i].iter().collect::<String>().to_lowercase()));
            i += 1;
        } else {
            i = start;
        }
        let value: String = if i < cs.len() && cs[i] == '"' {
            i += 1;
            let s = i;
            while i < cs.len() && cs[i] != '"' {
                i += 1;
            }
            let v = cs[s..i].iter().collect();
            i += 1;
            v
        } else {
            let s = i;
            while i < cs.len() && !cs[i].is_whitespace() {
                i += 1;
            }
            cs[s..i].iter().collect()
        };
        let value = value.trim().to_lowercase();
        if value.is_empty() {
            continue;
        }
        // is:shiny == shiny
        let key = match key.as_deref() {
            Some("is") | Some("state") => None,
            _ => key,
        };
        out.push(Term { key, value });
    }
    out
}

/// The state of a slot, for the state words.
#[derive(Clone, Copy, Default)]
pub struct Flags {
    pub shiny: bool,
    pub foil: bool,
    pub new: bool,
    pub pending: bool,
    pub owned: bool,
}

impl Flags {
    fn get(&self, w: &str) -> bool {
        match w {
            "shiny" => self.shiny,
            "foil" => self.foil,
            "new" => self.new,
            "pending" => self.pending,
            "owned" => self.owned,
            "missing" => !self.owned && !self.pending,
            _ => false,
        }
    }
}

/// Does a slot with these tags and state match every term?
pub fn matches(terms: &[Term], tags: &[(&str, String)], flags: Flags) -> bool {
    terms.iter().all(|t| match &t.key {
        None if STATES.contains(&t.value.as_str()) => flags.get(&t.value),
        None => tags.iter().any(|(_, v)| v.to_lowercase().contains(&t.value)),
        Some(k) => tags.iter().any(|(tk, v)| *tk == k.as_str() && v.to_lowercase().contains(&t.value)),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tags() -> Vec<(&'static str, String)> {
        vec![
            ("pack", "pokemon".into()),
            ("char", "umbreon".into()),
            ("name", "Umbreon VMAX".into()),
            ("set", "swsh7".into()),
            ("set", "Evolving Skies".into()),
            ("rarity", "Rare Rainbow".into()),
            ("subtype", "VMAX".into()),
            ("type", "Darkness".into()),
            ("artist", "KEIICHIRO ITO".into()),
            ("id", "swsh7-215".into()),
        ]
    }

    #[test]
    fn parse_terms() {
        let t = parse(r#"evolving skies set:swsh7 rarity:"rare rainbow" Type:Water is:shiny sub:vmax"#);
        let k: Vec<(Option<&str>, &str)> = t.iter().map(|x| (x.key.as_deref(), x.value.as_str())).collect();
        assert_eq!(
            k,
            vec![
                (None, "evolving"),
                (None, "skies"),
                (Some("set"), "swsh7"),
                (Some("rarity"), "rare rainbow"),
                (Some("type"), "water"),
                (None, "shiny"),
                (Some("subtype"), "vmax"),
            ]
        );
        assert_eq!(parse(r#""evolving skies""#), vec![Term { key: None, value: "evolving skies".into() }]);
        assert!(parse("   ").is_empty());
    }

    #[test]
    fn match_terms() {
        let tg = tags();
        let f = Flags { owned: true, foil: true, ..Default::default() };
        let m = |q: &str| matches(&parse(q), &tg, f);
        assert!(m("evolving skies"));
        assert!(m("set:swsh7"));
        assert!(m(r#"rarity:"rare rainbow""#));
        assert!(m("type:dark vmax"));
        assert!(m(r#"artist:"keiichiro ito""#));
        assert!(m("foil owned"));
        assert!(!m("shiny"));
        assert!(!m("type:water"));
        assert!(!m("set:swsh8"));
        assert!(!m("missing"));
    }
}
