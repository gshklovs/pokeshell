//! Search: forgiving words plus tag filters (docs/BINDER_SPEC.md "Tags and search"). tools/binder-web/index.html
//! has the same rules in JS, so both binders find the same cards.
//!
//!   pikachu  pikchu           a word matches a tag (name, set, rarity, type, artist, number, ...) when it is
//!   lyc vmax  evs rainbow     inside it, or its letters are in order from a word start with few gaps ("pikchu"
//!                             finds Pikachu, "evs" Evolving Skies); under 3 letters, the start of a word ("ex")
//!   set:swsh7  set:evolving   a set: its id or name, the best-matching sets (set:swsh1 is not swsh10; set:30th)
//!   number:17  number:TG05    the printed number (its numerator: 17 is 17/203, not 117); number:17/203 whole
//!   id:swsh7-17               the card id, whole
//!   rarity:"rare rainbow"     other keys: the value matches that key's tags like a word; quotes keep spaces and
//!                             mean nothing else (the web binder matches the same way)
//!   -holo  -set:swsh7         leave out what matches
//!   shiny  foil  new  pending owned  missing     state words: bare, or as is:shiny
//!
//! Every term must match (AND). Case and accents don't matter (flabebe finds Flabébé). Keys: set (id or name),
//! rarity, tier, type, subtype (sub), char (character), artist, pack, name, number, id (card).
//! The fuzzy test is fzf's v2 scoring (16 a letter, bonuses for word starts and runs, gaps cost 3 then 1 a letter):
//! letters in order count when the first is at a word start and the bonuses outweigh the gaps (fuzzy_floor).
//! Results keep the binder's order (set, then printed number); the score only ranks sets (set:, the S picker).

use crate::data::SetDef;

const SCORE_MATCH: i32 = 16;
const GAP_START: i32 = -3;
const GAP_EXT: i32 = -1;
const BONUS_BOUNDARY: i32 = SCORE_MATCH / 2;
const BONUS_NONWORD: i32 = SCORE_MATCH / 2;
const BONUS_CAMEL: i32 = BONUS_BOUNDARY + GAP_EXT;
const BONUS_CONSEC: i32 = -(GAP_START + GAP_EXT);
const FIRST_MULT: i32 = 2;
const BONUS_WHITE: i32 = BONUS_BOUNDARY + 2;
const BONUS_DELIM: i32 = BONUS_BOUNDARY + 1;
/// a set named whole (its id or name) beats every partial match
const EXACT_BONUS: i32 = 100_000;

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
        "finish" => "tier".into(),
        other => other.to_string(),
    }
}

/// A lower-case char's accent-folded form (é -> e, ß -> ss); nothing for a combining accent.
fn fold_char(l: char, out: &mut Vec<char>) {
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
        'ß' => out.extend(['s', 's']),
        'æ' => out.extend(['a', 'e']),
        'œ' => out.extend(['o', 'e']),
        '\u{300}'..='\u{36f}' => {} // combining accents
        '’' | '‘' => out.push('\''),
        _ => out.push(l),
    }
}

/// Lower-case, accents folded to their base letter (é -> e, ß -> ss): the form every comparison uses.
pub fn fold(s: &str) -> String {
    fold_chars(s).into_iter().collect()
}

fn fold_chars(s: &str) -> Vec<char> {
    let mut out = Vec::with_capacity(s.len());
    for c in s.chars() {
        for l in c.to_lowercase() {
            fold_char(l, &mut out);
        }
    }
    out
}

/// fold, then punctuation as spaces and runs of spaces collapsed ("Scarlet & Violet—151" -> "scarlet and violet 151").
pub fn norm(s: &str) -> String {
    let f = fold(s).replace('&', " and ");
    f.split(|c: char| !c.is_alphanumeric()).filter(|w| !w.is_empty()).collect::<Vec<_>>().join(" ")
}

#[derive(Clone, Copy, PartialEq)]
enum Class {
    White,
    NonWord,
    Delim,
    Lower,
    Upper,
    Letter,
    Number,
}

fn class(c: char) -> Class {
    if c.is_whitespace() {
        Class::White
    } else if "/,:;|".contains(c) {
        Class::Delim
    } else if c.is_lowercase() {
        Class::Lower
    } else if c.is_uppercase() {
        Class::Upper
    } else if c.is_numeric() {
        Class::Number
    } else if c.is_alphabetic() {
        Class::Letter
    } else {
        Class::NonWord
    }
}

fn bonus_for(prev: Class, cur: Class) -> i32 {
    let word = |c: Class| matches!(c, Class::Lower | Class::Upper | Class::Letter | Class::Number);
    if word(cur) {
        match prev {
            Class::White => return BONUS_WHITE,
            Class::Delim => return BONUS_DELIM,
            Class::NonWord => return BONUS_BOUNDARY,
            _ => {}
        }
    }
    if (prev == Class::Lower && cur == Class::Upper) || (prev != Class::Number && cur == Class::Number) {
        return BONUS_CAMEL;
    }
    match cur {
        Class::NonWord | Class::Delim => BONUS_NONWORD,
        Class::White => BONUS_WHITE,
        _ => 0,
    }
}

/// A tag prepared for matching: folded chars (and as a string, for the substring test) and each char's bonus
/// (from the original case, so camelCase counts).
#[derive(Clone, Debug)]
pub struct Field {
    s: String,
    t: Vec<char>,
    bonus: Vec<i32>,
}

impl Field {
    pub fn new(src: &str) -> Field {
        let mut t = Vec::with_capacity(src.len());
        let mut bonus = Vec::with_capacity(src.len());
        let mut prev = Class::White;
        let mut tmp = Vec::with_capacity(2);
        for c in src.chars() {
            tmp.clear();
            for l in c.to_lowercase() {
                fold_char(l, &mut tmp);
            }
            for (i, &f) in tmp.iter().enumerate() {
                let cl = if i == 0 { class(c) } else { class(f) };
                bonus.push(bonus_for(prev, cl));
                prev = cl;
                t.push(f);
            }
        }
        Field { s: t.iter().collect(), t, bonus }
    }
    pub fn is(&self, v: &str) -> bool {
        self.s == v
    }
}

/// fzf's FuzzyMatchV2 (case-insensitive: both sides folded): the best score of the pattern's chars in order, and
/// where its first char landed. None: not all the chars are there in order.
fn fuzzy(f: &Field, p: &[char]) -> Option<(i32, usize)> {
    let t = &f.t;
    let (m, n) = (p.len(), t.len());
    if m == 0 || m > n {
        return None;
    }
    // the chars in order; the first occurrence of each (first) bounds the table
    let mut first = Vec::with_capacity(m);
    let mut j = 0;
    for &pc in p {
        while j < n && t[j] != pc {
            j += 1;
        }
        if j == n {
            return None;
        }
        first.push(j);
        j += 1;
    }
    let mut last = n - 1;
    while t[last] != p[m - 1] {
        last -= 1;
    }
    let (lo, w) = (first[0], last + 1 - first[0]);
    if m == 1 {
        return (lo..=last).filter(|&j| t[j] == p[0]).map(|j| (SCORE_MATCH + f.bonus[j] * FIRST_MULT, j)).max_by_key(|x| (x.0, std::cmp::Reverse(x.1)));
    }
    let mut h = vec![0i32; m * w];
    let mut c = vec![0i32; m * w];
    let mut in_gap = false;
    let mut prev = 0;
    for j in 0..w {
        let col = lo + j;
        if t[col] == p[0] {
            h[j] = SCORE_MATCH + f.bonus[col] * FIRST_MULT;
            c[j] = 1;
            in_gap = false;
        } else {
            h[j] = (prev + if in_gap { GAP_EXT } else { GAP_START }).max(0);
            in_gap = true;
        }
        prev = h[j];
    }
    let (mut max_score, mut max_pos) = (0, 0);
    for i in 1..m {
        let row = i * w;
        let f0 = first[i] - lo;
        let mut in_gap = false;
        for j in f0..w {
            let col = lo + j;
            let left = if j > 0 { h[row + j - 1] } else { 0 };
            let s2 = left + if in_gap { GAP_EXT } else { GAP_START };
            let mut s1 = 0;
            let mut consec = 0;
            if t[col] == p[i] && j > 0 {
                s1 = h[row - w + j - 1] + SCORE_MATCH;
                let mut b = f.bonus[col];
                consec = c[row - w + j - 1] + 1;
                if consec > 1 {
                    let fb = f.bonus[col + 1 - consec as usize];
                    if b >= BONUS_BOUNDARY && b > fb {
                        consec = 1;
                    } else {
                        b = b.max(BONUS_CONSEC).max(fb);
                    }
                }
                if s1 + b < s2 {
                    s1 += f.bonus[col];
                    consec = 0;
                } else {
                    s1 += b;
                }
            }
            c[row + j] = consec;
            in_gap = s1 < s2;
            let score = s1.max(s2).max(0);
            if i == m - 1 && score > max_score {
                max_score = score;
                max_pos = j;
            }
            h[row + j] = score;
        }
    }
    // walk back to where the first char landed
    let (mut i, mut j) = (m - 1, max_pos);
    let mut prefer = true;
    loop {
        let row = i * w;
        let f0 = first[i] - lo;
        let s = h[row + j];
        let s1 = if i > 0 && j >= f0 && j > 0 { h[row - w + j - 1] } else { 0 };
        let s2 = if j > f0 { h[row + j - 1] } else { 0 };
        if s > s1 && (s > s2 || (s == s2 && prefer)) {
            if i == 0 {
                break;
            }
            i -= 1;
        }
        prefer = c[row + j] > 1 || (row + w + j + 1 < c.len() && c[row + w + j + 1] > 0);
        if j == 0 {
            break;
        }
        j -= 1;
    }
    Some((max_score, lo + j))
}

/// The least score letters in order must reach: 16 a letter plus 4 for each after the first (a run's bonus), so
/// word starts and runs pass and letters scattered mid-word don't.
fn fuzzy_floor(m: usize) -> i32 {
    (SCORE_MATCH + BONUS_CONSEC) * m as i32 - BONUS_CONSEC
}

/// Does a word (folded) match a tag, and how well (the fzf score; higher is better)?
///   under 3 letters: the start of a word of the tag ("ex", "v", "17")
///   else: inside the tag, or its letters in order from a word start with the bonuses outweighing the gaps
fn word_score(v: &str, vc: &[char], f: &Field) -> Option<i32> {
    if vc.len() < 3 {
        let hit = f.s.match_indices(v).any(|(i, _)| {
            let ci = f.s[..i].chars().count();
            ci == 0 || !f.t[ci - 1].is_alphanumeric()
        });
        return if hit { Some(fuzzy(f, vc).map(|x| x.0).unwrap_or(1)) } else { None };
    }
    let (score, at) = fuzzy(f, vc)?;
    if f.s.contains(v) {
        return Some(score.max(1));
    }
    let word_start = at == 0 || !f.t[at - 1].is_alphanumeric() || f.bonus[at] >= BONUS_CAMEL;
    (word_start && score >= fuzzy_floor(vc.len())).then_some(score)
}

/// One search term: a key (None: a bare word) and a folded value.
#[derive(Clone, Debug, PartialEq)]
pub struct Term {
    pub key: Option<String>,
    pub value: String,
    /// `-term`: leave out what matches
    pub neg: bool,
    /// `set:` terms, resolved against the pack's sets (resolve_terms): the ids of the sets it names
    pub sets: Option<Vec<String>>,
    chars: Vec<char>,
}

impl Term {
    fn new(key: Option<String>, value: String, neg: bool) -> Term {
        Term { chars: value.chars().collect(), key, value, neg, sets: None }
    }
}

/// Split a query into terms. `key:value` / `key:"a b"` are filters; `"a b"` is one phrase; `-` leaves out.
pub fn parse(q: &str) -> Vec<Term> {
    let mut out = Vec::new();
    let cs: Vec<char> = q.chars().collect();
    let mut i = 0;
    while i < cs.len() {
        if cs[i].is_whitespace() {
            i += 1;
            continue;
        }
        let neg = cs[i] == '-' && i + 1 < cs.len() && !cs[i + 1].is_whitespace();
        if neg {
            i += 1;
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
        let value = fold(value.trim());
        if value.is_empty() {
            continue;
        }
        // is:shiny == shiny
        let key = match key.as_deref() {
            Some("is") | Some("state") => None,
            _ => key,
        };
        out.push(Term::new(key, value, neg));
    }
    out
}

/// Keys in a query that no slot has (`foo:bar`), for the no-match message.
pub fn unknown_keys(terms: &[Term]) -> Vec<String> {
    terms.iter().filter_map(|t| t.key.clone()).filter(|k| !KEYS.contains(&k.as_str())).collect()
}

/// A set's fields: its id, its name, and the name normalized ("Sword & Shield" also as "sword and shield").
fn set_fields(set: &SetDef) -> [Field; 3] {
    [Field::new(&set.id), Field::new(&set.name), Field::new(&norm(&set.name))]
}

fn set_term(t: &Term, fs: &[Field; 3]) -> Option<i32> {
    fs.iter().filter_map(|f| if f.is(&t.value) { Some(EXACT_BONUS) } else { word_score(&t.value, &t.chars, f) }).max()
}

/// How well a filter names a set (0: not at all): every word of it must match its id or name (the same test as
/// the search), a whole id or name first, then the fzf score. The set picker (S), `set:`, its Tab completion and
/// --set all rank sets with this.
pub fn set_score(set: &SetDef, q: &str) -> i32 {
    let fs = set_fields(set);
    let whole = Term::new(None, fold(q.trim()), false);
    if whole.value.is_empty() {
        return 0;
    }
    if fs.iter().any(|f| f.is(&whole.value)) {
        return EXACT_BONUS;
    }
    let words: Vec<Term> = whole.value.split_whitespace().map(|w| Term::new(None, w.into(), false)).collect();
    let mut total = set_term(&whole, &fs).unwrap_or(0);
    if total == 0 {
        for w in &words {
            match set_term(w, &fs) {
                Some(s) => total += s,
                None => return 0,
            }
        }
    }
    total.max(1)
}

/// The sets a query names best: every set at the top score (several when it is ambiguous), in the given order.
pub fn resolve_sets<'a>(sets: impl IntoIterator<Item = &'a SetDef>, q: &str) -> Vec<&'a SetDef> {
    let scored: Vec<(&SetDef, i32)> = sets.into_iter().map(|s| (s, set_score(s, q))).filter(|x| x.1 > 0).collect();
    let top = scored.iter().map(|x| x.1).max().unwrap_or(0);
    scored.into_iter().filter(|x| x.1 == top).map(|x| x.0).collect()
}

/// Resolve the `set:` terms against a pack's sets (set_score; the best-scoring sets). A pack without sets matches
/// its set tags like any key.
pub fn resolve_terms(terms: &mut [Term], sets: &[SetDef]) {
    if sets.is_empty() {
        return;
    }
    for t in terms.iter_mut() {
        if t.key.as_deref() == Some("set") {
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

/// A slot's tags prepared once for matching: (key, field). App caches these, so a keystroke only matches.
pub type Hay = Vec<(&'static str, Field)>;

pub fn prepare(tags: &[(&'static str, String)]) -> Hay {
    tags.iter().map(|(k, v)| (*k, Field::new(v))).collect()
}

fn term_ok(t: &Term, hay: &[(&'static str, Field)], flags: Flags) -> bool {
    let Some(k) = t.key.as_deref() else {
        if STATES.contains(&t.value.as_str()) {
            return flags.get(&t.value);
        }
        return hay.iter().any(|(_, f)| word_score(&t.value, &t.chars, f).is_some());
    };
    let mut vals = hay.iter().filter(|(tk, _)| *tk == k).map(|(_, f)| f);
    match k {
        // resolved: the card's set id is one of them
        "set" if t.sets.is_some() => {
            let ids = t.sets.as_ref().unwrap();
            vals.any(|f| ids.iter().any(|id| f.is(id)))
        }
        "number" if t.value.contains('/') => vals.any(|f| f.is(&t.value)),
        "number" => {
            let want = crate::data::numerator(&t.value);
            vals.any(|f| crate::data::numerator(&f.s) == want)
        }
        "id" => vals.any(|f| f.is(&t.value)),
        _ if !KEYS.contains(&k) => false,
        _ => vals.any(|f| word_score(&t.value, &t.chars, f).is_some()),
    }
}

/// Does a slot with these prepared tags and this state match every term?
pub fn matches_hay(terms: &[Term], hay: &[(&'static str, Field)], flags: Flags) -> bool {
    terms.iter().all(|t| term_ok(t, hay, flags) != t.neg)
}

/// Does a slot with these tags and state match every term? (prepares the tags on the fly)
pub fn matches(terms: &[Term], tags: &[(&'static str, String)], flags: Flags) -> bool {
    matches_hay(terms, &prepare(tags), flags)
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

    fn w(v: &str, tag: &str) -> Option<i32> {
        let v = fold(v);
        word_score(&v, &v.chars().collect::<Vec<_>>(), &Field::new(tag))
    }

    #[test]
    fn fzf_scores() {
        // fzf v2's numbers: "fbb" on "foo bar baz" is three word starts (the first doubled) and two gaps
        let f = Field::new("foo bar baz");
        assert_eq!(fuzzy(&f, &['f', 'b', 'b']), Some((SCORE_MATCH * 3 + BONUS_WHITE * FIRST_MULT + BONUS_WHITE * 2 + GAP_START * 2 + GAP_EXT * 4, 0)));
        // "o-ba" on "foo-bar": the "-" and "b" are boundaries, "a" continues the run
        assert_eq!(fuzzy(&Field::new("foo-bar"), &['o', '-', 'b', 'a']).map(|x| x.0), Some(SCORE_MATCH * 4 + BONUS_BOUNDARY * 3));
        // camelCase counts: "dc" on "DocCard" lands on both capitals
        assert!(fuzzy(&Field::new("DocCard"), &['d', 'c']).unwrap().0 > fuzzy(&Field::new("docucard"), &['d', 'c']).unwrap().0);
        // where the first letter lands: the best alignment, not the first one
        assert_eq!(fuzzy(&Field::new("xsx Skies"), &['s', 'k']).map(|x| x.1), Some(4));
        assert_eq!(fuzzy(&Field::new("abc"), &['x']), None);
    }

    #[test]
    fn forgiving_words() {
        assert!(w("pikachu", "Pikachu V").is_some() && w("pikchu", "Pikachu").is_some() && w("pkachu", "Pikachu").is_some());
        assert!(w("lycvmax", "Lycanroc VMAX").is_some() && w("lyc", "Lycanroc").is_some());
        assert!(w("evs", "Evolving Skies").is_some() && w("evsk", "Evolving Skies").is_some());
        assert!(w("olving", "Evolving Skies").is_some(), "inside a tag");
        assert!(w("kachu", "Pikachu").is_some(), "inside, not from a word start: still a substring");
        assert!(w("abcd", "axxxxbxxxxcxxxxd").is_none(), "letters scattered mid-word: no");
        assert!(w("vmax", "Vivid Voltage Mega Axe").is_some(), "word starts outweigh the gaps");
        assert!(w("ikchu", "Pikachu").is_none(), "letters in order but not from a word start: no");
        assert!(w("ex", "Charizard ex").is_some() && w("ex", "Hex Maniac").is_none() && w("ex", "Alexa").is_none(), "short: a word start");
        assert!(w("17", "17/203").is_some() && w("v", "Rare Holo V").is_some());
        assert!(w("rainbow", "Rare Rainbow").is_some() && w("rnbw", "Rare Rainbow").is_some() && w("rwbn", "Rare Rainbow").is_none());
        assert!(w("FLABÉBÉ", "Flabébé").is_some() && w("flabebe", "Flabébé").is_some(), "case and accents don't matter");
    }

    #[test]
    fn parse_terms() {
        let t = parse(r#"evolving skies set:swsh7 rarity:"rare rainbow" Type:Water is:shiny sub:vmax -holo -set:30th"#);
        let k: Vec<(Option<&str>, &str, bool)> = t.iter().map(|x| (x.key.as_deref(), x.value.as_str(), x.neg)).collect();
        assert_eq!(
            k,
            vec![
                (None, "evolving", false),
                (None, "skies", false),
                (Some("set"), "swsh7", false),
                (Some("rarity"), "rare rainbow", false),
                (Some("type"), "water", false),
                (None, "shiny", false),
                (Some("subtype"), "vmax", false),
                (None, "holo", true),
                (Some("set"), "30th", true),
            ]
        );
        assert_eq!(parse(r#""evolving skies""#), vec![Term::new(None, "evolving skies".into(), false)]);
        assert!(parse("   ").is_empty());
        assert!(parse("set:").is_empty(), "an empty value is no term (yet)");
        assert_eq!(parse("- x").len(), 2, "a lone - is a word");
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
        assert!(m("evolving skies") && m("evs rainbow") && m("umb vmax") && m("umbvmax"));
        assert!(m("set:swsh7") && m("set:evolving") && m("set:skies") && m("set:EVOLV") && m(r#"set:"evolving skies""#));
        assert!(m("set:evsk"), "letters in order");
        assert!(m("set:swsh"), "no set is swsh: the ids starting with it");
        assert!(!m("set:swsh1"), "swsh1 is a set: exactly it, not swsh10 or swsh7");
        assert!(m(r#"rarity:"rare rainbow""#) && m("rarity:rainbow") && m("rarity:rare") && !m("rarity:holo"));
        assert!(m("type:dark vmax") && m("type:drkness"));
        assert!(m(r#"artist:"keiichiro ito""#) && m("artist:ito"));
        assert!(m("foil owned") && !m("shiny") && !m("type:water") && !m("set:swsh8") && !m("missing"));
        assert!(m("number:215") && !m("number:15") && !m("number:21"));
        assert!(m("number:215/203") && !m("number:215/204"));
        assert!(m("id:swsh7-215") && !m("id:swsh7-21") && !m(r#"id:"swsh7-21""#), "quotes change nothing");
        assert!(m("-holo") && !m("-rainbow") && m("-set:30th") && !m("-set:evolving") && m("-shiny") && !m("-owned"), "- leaves out");
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
        assert_eq!(ids("evsk"), vec!["swsh7"]);
        assert_eq!(ids("evo sk"), vec!["swsh7"]);
        assert_eq!(ids("30th"), vec!["me55"]);
        assert_eq!(ids("celebration"), vec!["me55", "cel25"], "ambiguous: both, in order");
        assert_eq!(ids("celebrations"), vec!["cel25"]);
        assert_eq!(ids("sword and shield"), vec!["swsh1"]);
        assert_eq!(ids("sword & shield"), vec!["swsh1"]);
        assert_eq!(ids("151"), vec!["sv3pt5"]);
        assert_eq!(ids("swsh"), vec!["swsh7", "swsh1", "swsh10"], "an id prefix");
        assert!(ids("zzz").is_empty());
        assert!(ids("").is_empty());
        let (a, b) = (SetDef { id: "x1".into(), name: "Radiant Stars".into() }, SetDef { id: "x2".into(), name: "Paradise Dragons".into() });
        assert!(set_score(&a, "rad") > set_score(&b, "rad") && set_score(&b, "rad") > 0, "the picker ranks a word start above a match inside a word");
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

    /// The user's cases, on the real pokemon pack.json (its name, number, rarity and set; no art needed).
    #[test]
    fn real_cards() {
        let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("..");
        let v: serde_json::Value = serde_json::from_slice(&std::fs::read(root.join("packs/pokemon/pack.json")).unwrap()).unwrap();
        let cards = v["cards"].as_object().unwrap();
        let mut sets: Vec<SetDef> = vec![];
        let mut all: Vec<(String, String, Hay)> = vec![];
        for (id, c) in cards {
            let s = |k: &str| c[k].as_str().unwrap_or("").to_string();
            let set_id = id.rsplit_once('-').unwrap().0.to_string();
            if !sets.iter().any(|x| x.id == set_id) {
                sets.push(SetDef { id: set_id.clone(), name: s("set") });
            }
            let tags: Vec<(&'static str, String)> = vec![
                ("pack", "pokemon".into()),
                ("char", s("character")),
                ("name", s("name")),
                ("tier", s("tier")),
                ("id", id.clone()),
                ("number", s("number")),
                ("rarity", s("rarity")),
                ("set", set_id),
                ("set", s("set")),
            ];
            all.push((id.clone(), s("name"), prepare(&tags)));
        }
        let find = |q: &str| -> Vec<(String, String)> {
            let mut t = parse(q);
            resolve_terms(&mut t, &sets);
            all.iter().filter(|(_, _, h)| matches_hay(&t, h, Flags::default())).map(|(i, n, _)| (i.clone(), n.clone())).collect()
        };
        let pika: Vec<String> = all.iter().filter(|(_, n, _)| n.contains("Pikachu")).map(|x| x.0.clone()).collect();
        assert!(pika.len() > 10);
        for q in ["pikachu", "pikchu", "Pikachu", "pkachu"] {
            let got = find(q);
            assert!(pika.iter().all(|id| got.iter().any(|g| &g.0 == id)), "{q}: every Pikachu card");
            assert!(got.iter().all(|g| g.1.contains("Pikachu")), "{q}: only Pikachu cards: {got:?}");
        }
        for q in ["lyc vmax", "lycvmax", "lycanroc vmax"] {
            let got = find(q);
            assert!(got.iter().any(|g| g.0 == "swsh7-92"), "{q}: Lycanroc VMAX swsh7-92: {got:?}");
            assert!(!got.iter().any(|g| g.1 == "Lycanroc V"), "{q}: not Lycanroc V: {got:?}");
        }
        let evs = find("evs rainbow");
        let want: Vec<&String> = cards.iter().filter(|(id, c)| id.starts_with("swsh7-") && c["rarity"] == "Rare Rainbow").map(|x| x.0).collect();
        assert!(!want.is_empty() && want.iter().all(|id| evs.iter().any(|g| &&g.0 == id)), "evs rainbow: every Evolving Skies rare rainbow");
        assert!(evs.iter().all(|g| g.0.starts_with("swsh7-") && cards[&g.0]["rarity"] == "Rare Rainbow"), "evs rainbow: only those: {evs:?}");
        let c30 = find("set:30th");
        assert!(!c30.is_empty() && c30.iter().all(|g| cards[&g.0]["set"].as_str().unwrap().contains("30th")), "set:30th: the 30th Celebration");
        assert_eq!(c30.len(), cards.values().filter(|c| c["set"].as_str().unwrap().contains("30th")).count());
    }
}
