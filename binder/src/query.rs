//! Search: free text plus tag filters (docs/BINDER_SPEC.md "Tags and search"), the same syntax as the web binder.
//!
//!   evolving skies            every word must match somewhere (name, character, card id, number, any tag value)
//!   set:swsh7  set:evolving   a set: its id exactly, or its name (word prefixes: set:30th, set:"evolving skies")
//!   number:17  number:TG05    the printed number (its numerator: 17 is 17/203, not 117)
//!   id:swsh7-17               the card id, exactly
//!   rarity:"rare rainbow"     other keys: a substring of the value; quotes keep spaces (and make any key a substring)
//!   type:water vmax           filters and words combine (all must match)
//!   shiny  foil  new  pending owned  missing     state words: bare, or as is:shiny
//!
//! Matching ignores case and accents (flabebe finds Flabébé). Keys: set (id or name), rarity, tier, type, subtype
//! (sub), char (character), artist, pack, name, number, id (card).

use crate::data::SetDef;

/// One search term: a key (None: free text) and a folded value.
#[derive(Clone, Debug, PartialEq)]
pub struct Term {
    pub key: Option<String>,
    pub value: String,
    /// `key:"..."`: a plain substring match whatever the key
    pub quoted: bool,
    /// `set:` terms, resolved against the pack's sets (resolve_sets): the ids of the sets it names
    pub sets: Option<Vec<String>>,
}

/// The state words: they test the slot, not its tags.
pub const STATES: &[&str] = &["shiny", "foil", "new", "pending", "owned", "missing"];
/// The tag keys a slot has (Pack::slot_tags).
pub const KEYS: &[&str] = &["set", "rarity", "type", "subtype", "name", "number", "artist", "char", "tier", "pack", "id"];

fn canon_key(k: &str) -> String {
    match k {
        "sub" | "subtypes" | "stage" => "subtype".into(),
        "character" | "pokemon" | "chars" => "char".into(),
        "types" | "energy" => "type".into(),
        "card" => "id".into(),
        "no" | "num" | "#" => "number".into(),
        "setname" | "series" | "sets" => "set".into(),
        "rare" | "rarities" => "rarity".into(),
        "illus" | "illustrator" => "artist".into(),
        other => other.to_string(),
    }
}

/// Lower-case, accents folded to their base letter (é -> e, ß -> ss): the form every comparison uses.
pub fn fold(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    for c in s.chars() {
        for l in c.to_lowercase() {
            match l {
                'à' | 'á' | 'â' | 'ã' | 'ä' | 'å' | 'ā' | 'ă' | 'ą' => out.push('a'),
                'ç' | 'ć' | 'ĉ' | 'ċ' | 'č' => out.push('c'),
                'ď' | 'đ' => out.push('d'),
                'è' | 'é' | 'ê' | 'ë' | 'ē' | 'ĕ' | 'ė' | 'ę' | 'ě' => out.push('e'),
                'ĝ' | 'ğ' | 'ġ' | 'ģ' => out.push('g'),
                'ì' | 'í' | 'î' | 'ï' | 'ĩ' | 'ī' | 'ĭ' | 'į' | 'ı' => out.push('i'),
                'ñ' | 'ń' | 'ņ' | 'ň' => out.push('n'),
                'ò' | 'ó' | 'ô' | 'õ' | 'ö' | 'ø' | 'ō' | 'ŏ' | 'ő' => out.push('o'),
                'ś' | 'ŝ' | 'ş' | 'š' => out.push('s'),
                'ù' | 'ú' | 'û' | 'ü' | 'ũ' | 'ū' | 'ŭ' | 'ů' | 'ű' | 'ų' => out.push('u'),
                'ý' | 'ÿ' => out.push('y'),
                'ź' | 'ż' | 'ž' => out.push('z'),
                'ß' => out.push_str("ss"),
                'æ' => out.push_str("ae"),
                'œ' => out.push_str("oe"),
                '\u{300}'..='\u{36f}' => {} // combining accents
                '’' | '‘' => out.push('\''),
                _ => out.push(l),
            }
        }
    }
    out
}

/// fold, then punctuation as spaces and runs of spaces collapsed ("Scarlet & Violet—151" -> "scarlet and violet 151").
pub fn norm(s: &str) -> String {
    let f = fold(s).replace('&', " and ");
    f.split(|c: char| !c.is_alphanumeric()).filter(|w| !w.is_empty()).collect::<Vec<_>>().join(" ")
}

fn compact(s: &str) -> String {
    s.chars().filter(|c| c.is_alphanumeric()).collect()
}

fn subsequence(needle: &str, hay: &str) -> bool {
    let mut h = hay.chars();
    needle.chars().all(|c| h.any(|x| x == c))
}

/// How well a query names a set (0: not at all). Case, accents and punctuation don't matter.
///   100 its id ("swsh7")          95 its whole name ("evolving skies")
///    80 every word starts a word of the name ("evolving", "30th", "evo sk")
///    60 the start of its id ("swsh")   50 inside its name ("olving")   20 the letters in order ("evsk", 3+ letters)
pub fn set_score(set: &SetDef, q: &str) -> u8 {
    let qn = norm(q);
    if qn.is_empty() {
        return 0;
    }
    let qc = compact(&qn);
    let (idc, nn) = (compact(&norm(&set.id)), norm(&set.name));
    let nc = compact(&nn);
    if qc == idc {
        100
    } else if qn == nn || qc == nc {
        95
    } else if qn.split(' ').all(|w| nn.split(' ').any(|x| x.starts_with(w))) {
        80
    } else if idc.starts_with(&qc) {
        60
    } else if nc.contains(&qc) {
        50
    } else if qc.chars().count() >= 3 && (subsequence(&qc, &nc) || subsequence(&qc, &idc)) {
        20
    } else {
        0
    }
}

/// The sets a query names best: every set at the top score (several when it is ambiguous), in the given order.
pub fn resolve_sets<'a>(sets: impl IntoIterator<Item = &'a SetDef>, q: &str) -> Vec<&'a SetDef> {
    let scored: Vec<(&SetDef, u8)> = sets.into_iter().map(|s| (s, set_score(s, q))).filter(|x| x.1 > 0).collect();
    let top = scored.iter().map(|x| x.1).max().unwrap_or(0);
    scored.into_iter().filter(|x| x.1 == top).map(|x| x.0).collect()
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
        let quoted = i < cs.len() && cs[i] == '"';
        let value: String = if quoted {
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
        let value = fold(value.trim());
        if value.is_empty() {
            continue;
        }
        // is:shiny == shiny
        let key = match key.as_deref() {
            Some("is") | Some("state") => None,
            _ => key,
        };
        out.push(Term { key, value, quoted, sets: None });
    }
    out
}

/// Keys in a query that no slot has (`foo:bar`), for the no-match message.
pub fn unknown_keys(terms: &[Term]) -> Vec<String> {
    terms.iter().filter_map(|t| t.key.clone()).filter(|k| !KEYS.contains(&k.as_str())).collect()
}

/// Resolve the `set:` terms against a pack's sets (set_score; the best-scoring sets). A pack without sets keeps the
/// plain substring match.
pub fn resolve_terms(terms: &mut [Term], sets: &[SetDef]) {
    if sets.is_empty() {
        return;
    }
    for t in terms.iter_mut() {
        if t.key.as_deref() == Some("set") && !t.quoted {
            t.sets = Some(resolve_sets(sets, &t.value).into_iter().map(|s| fold(&s.id)).collect());
        }
    }
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

fn term_ok(t: &Term, tags: &[(&str, String)], flags: Flags) -> bool {
    let Some(k) = t.key.as_deref() else {
        if STATES.contains(&t.value.as_str()) {
            return flags.get(&t.value);
        }
        return tags.iter().any(|(_, v)| fold(v).contains(&t.value));
    };
    let vals = tags.iter().filter(|(tk, _)| *tk == k).map(|(_, v)| fold(v));
    if t.quoted {
        return vals.into_iter().any(|v| v.contains(&t.value));
    }
    match k {
        // resolved: the card's set id is one of them; unresolved (no sets): the id or a word of the name
        "set" => match &t.sets {
            Some(ids) => vals.into_iter().any(|v| ids.contains(&v)),
            None => vals.into_iter().any(|v| v == t.value || norm(&v).split(' ').any(|w| w.starts_with(&norm(&t.value)))),
        },
        "number" => {
            let want = if t.value.contains('/') { t.value.clone() } else { crate::data::numerator(&t.value) };
            vals.into_iter().any(|v| if t.value.contains('/') { v == want } else { crate::data::numerator(&v) == want })
        }
        "id" => vals.into_iter().any(|v| v == t.value),
        _ => vals.into_iter().any(|v| v.contains(&t.value)),
    }
}

/// Does a slot with these tags and state match every term?
pub fn matches(terms: &[Term], tags: &[(&str, String)], flags: Flags) -> bool {
    terms.iter().all(|t| term_ok(t, tags, flags))
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
            ("number", "215/203".into()),
        ]
    }

    fn sets() -> Vec<SetDef> {
        vec![
            SetDef { id: "swsh7".into(), name: "Evolving Skies".into() },
            SetDef { id: "me55".into(), name: "30th Celebration".into() },
            SetDef { id: "swsh1".into(), name: "Sword & Shield".into() },
            SetDef { id: "swsh10".into(), name: "Astral Radiance".into() },
            SetDef { id: "cel25".into(), name: "Celebrations".into() },
            SetDef { id: "sv3pt5".into(), name: "151".into() },
        ]
    }

    #[test]
    fn parse_terms() {
        let t = parse(r#"evolving skies set:swsh7 rarity:"rare rainbow" Type:Water is:shiny sub:vmax"#);
        let k: Vec<(Option<&str>, &str, bool)> = t.iter().map(|x| (x.key.as_deref(), x.value.as_str(), x.quoted)).collect();
        assert_eq!(
            k,
            vec![
                (None, "evolving", false),
                (None, "skies", false),
                (Some("set"), "swsh7", false),
                (Some("rarity"), "rare rainbow", true),
                (Some("type"), "water", false),
                (None, "shiny", false),
                (Some("subtype"), "vmax", false),
            ]
        );
        assert_eq!(parse(r#""evolving skies""#), vec![Term { key: None, value: "evolving skies".into(), quoted: true, sets: None }]);
        assert!(parse("   ").is_empty());
        assert!(parse("set:").is_empty(), "an empty value is no term (yet)");
        assert_eq!(unknown_keys(&parse("foo:bar set:x")), vec!["foo".to_string()]);
    }

    #[test]
    fn match_terms() {
        let tg = tags();
        let f = Flags { owned: true, foil: true, ..Default::default() };
        let m = |q: &str| {
            let mut t = parse(q);
            resolve_terms(&mut t, &sets());
            matches(&t, &tg, f)
        };
        assert!(m("evolving skies"));
        assert!(m("set:swsh7"));
        assert!(m("set:evolving") && m("set:skies") && m("set:EVOLV") && m(r#"set:"evolving skies""#));
        assert!(m("set:evsk"), "letters in order");
        assert!(m("set:swsh"), "no set is swsh: the ids starting with it");
        assert!(!m("set:swsh1"), "swsh1 is a set: exactly it, not swsh10 or swsh7");
        assert!(m(r#"rarity:"rare rainbow""#));
        assert!(m("type:dark vmax"));
        assert!(m(r#"artist:"keiichiro ito""#));
        assert!(m("foil owned"));
        assert!(!m("shiny"));
        assert!(!m("type:water"));
        assert!(!m("set:swsh8"));
        assert!(!m("missing"));
        assert!(m("number:215") && !m("number:15") && !m("number:21"));
        assert!(m("number:215/203") && !m("number:215/204"));
        assert!(m("id:swsh7-215") && !m("id:swsh7-21"));
        assert!(m(r#"id:"swsh7-21""#), "quoted: substring");
        assert!(!m("foo:bar"), "an unknown key matches nothing");
    }

    #[test]
    fn set_ids_exact() {
        // set:swsh1 is Sword & Shield, not swsh10 (S-12)
        let s = sets();
        let ids = |q: &str| resolve_sets(&s, q).iter().map(|x| x.id.clone()).collect::<Vec<_>>();
        assert_eq!(ids("swsh1"), vec!["swsh1"]);
        assert_eq!(ids("SWSH7"), vec!["swsh7"]);
        assert_eq!(ids("evolving"), vec!["swsh7"]);
        assert_eq!(ids("Evolving Skies"), vec!["swsh7"]);
        assert_eq!(ids("30th"), vec!["me55"]);
        assert_eq!(ids("celebration"), vec!["me55", "cel25"], "ambiguous: both, in order");
        assert_eq!(ids("celebrations"), vec!["cel25"]);
        assert_eq!(ids("sword and shield"), vec!["swsh1"]);
        assert_eq!(ids("sword & shield"), vec!["swsh1"]);
        assert_eq!(ids("151"), vec!["sv3pt5"]);
        assert_eq!(ids("swsh"), vec!["swsh7", "swsh1", "swsh10"], "an id prefix");
        assert!(ids("zzz").is_empty());
        assert!(ids("").is_empty());
    }

    #[test]
    fn accents() {
        assert_eq!(fold("Flabébé"), "flabebe");
        assert_eq!(fold("Flabe\u{301}be\u{301}"), "flabebe");
        assert_eq!(norm("Scarlet & Violet—151"), "scarlet and violet 151");
        let tg: Vec<(&str, String)> = vec![("name", "Flabébé".into()), ("set", "Pokémon GO".into())];
        assert!(matches(&parse("flabebe"), &tg, Flags::default()));
        assert!(matches(&parse("FLABÉBÉ"), &tg, Flags::default()));
        let s = vec![SetDef { id: "pgo".into(), name: "Pokémon GO".into() }];
        assert_eq!(resolve_sets(&s, "pokemon go").len(), 1);
        assert_eq!(resolve_sets(&s, "POKÉMON").len(), 1);
    }
}
