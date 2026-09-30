# Binder UX spec

Status: **built** on branch `binder-earned` (2026-09-29): the earned rule, all four entry points, tags and search.
Branch `binder-seen` (2026-09-29): empty / seen / caught slots (a Pokédex's), replacing "pending" in both binders.
The terminal app is `binder/` (Rust, ratatui; from the `style-lab/binder-tui` prototype), the web binder is
`binder/src/webexport.rs` (`binder --export-web`) + `tools/binder-web/index.html` (from `style-lab/binder-web`). Still open: the backend (below),
`collection.json` (not needed so far: reading `pulls.log` takes a few ms), and the open questions at the end.

## Implementation notes
- **Pull log** (`pulls.log`, append-only, docs in `scripts/lib/Pokeshell.cs`): a pull line keeps its 8 columns and adds
  `pending` to the flags column plus `id=<ulid>` and `boot=<unix s of the last boot>` columns (`key=value`, so more can
  follow). Events are 2-column lines: `<time> earned:<id>` / `<time> expired:<id>`. A line without an id is earned.
  A pending pull with no event is expired after 24 h or when `boot=` differs from this boot session's by more than
  2 minutes; the CLI then writes its `expired:<id>` line. One rule, three readers: `Core.ReadPulls` (C#),
  `binder/src/data.rs`, `binder/src/webexport.rs`. Real-card packs then resolve each pull (`retired`, docs/PACK_FORMAT.md).
- **First use**: a `PreCommandLookupAction` delegate in the core, registered by `Core.Startup` itself (no extra
  PowerShell on the tab-open path), hands the host a small wrapper whenever it looks up `prompt`: it checks
  `Get-History`, and runs whatever `prompt` exists then (so a `function prompt` later in `$PROFILE` still works). The
  foil tab registers it from `Show-PokeshellPull`. Removed once the pull is earned or expired.
- **Use rule**: config `earn` = `first-command` (default) | `minutes:N` (earned at the first prompt after the tab has
  been open N minutes) | `off` (logged earned, no hook).
- **Viewed**: the app appends a card's ids to `viewed.txt` when it shows it; its NEW sticker stays until you move on.
- **Branch `binder-links` (2026-09-29): both ways in from a pulled card work after a plain install.** `pokeshell install`
  (install.ps1, the module install, `pokeshell update`) sets up the hotkey and the link whenever it finds the binder app;
  `pokeshell hotkey off` / `urlhandler off` remove one and leave `hotkey.off` / `urlhandler.off` so later installs
  don't add it back; `pokeshell uninstall` removes both (byte for byte in settings.json).
- **What Windows Terminal does with a link** (1.24, `src/cascadia/TerminalApp/TerminalPage.cpp` on `release-1.24`:
  `_OpenHyperlinkHandler`, `_IsUriSupported`, `_IsUriConsideredSomewhatSafe`): only a **Ctrl+click** opens a link
  (`ControlInteractivity::PointerPressed`). http(s) opens at once. `file://` is allowed for local paths (and `wsl$`),
  with no existence check; a path ending in a `%PATHEXT%` extension (.exe, .cmd, .bat, ...) gets the "This link may
  lead to an unsafe location" dialog first. Any other scheme (`pokeshell://`) is supported but gets that dialog too,
  unless it is listed in the top-level `safeUriSchemes` setting. Then `ShellExecuteW(nullptr, L"open", uri, ...)`.
- **Click**: the OSC 8 link is on the `binder ⏎` footer only (Windows Terminal underlines link text, which would stripe
  the art): `pokeshell://binder?pull=<id>`. The install registers `HKCU\Software\Classes\pokeshell` →
  `binder-link.exe --root <root> [--state <dir>] --url "%1"` and adds `"safeUriSchemes": ["pokeshell"]` to settings.json
  (recorded in `urlhandler.txt` / `safeuri.tsv`). `binder-link.exe` (`binder/src/link.rs`) is a GUI-subsystem program,
  so a click never flashes a console: it accepts only `?pull=<ulid>` / `?card=<pack/char/tier>` (`binder/src/linkurl.rs`,
  shared with `binder --url`) and runs `wt -w 0 sp -V --title binder -- binder.exe --root <root> --pull <id>`: a split
  pane in the window that was clicked (`-w 0` = the most recently used window). The link itself never reaches wt.exe:
  wt splits its arguments on any unescaped `;`, so a handler of `wt.exe ... --url "%1"` would let a crafted link
  (`?pull=x;nt;cmd`) open a tab running anything, with no dialog once the scheme is safe. Without wt.exe it opens the
  binder in a console window of its own. Other terminals use the same handler.
- **Why not a `file://` link** (the only kind Windows Terminal opens without a dialog by default): a `.exe` / `.cmd`
  target gets the PATHEXT dialog, and a `.lnk` shortcut (per pull, or one static one) costs ~300 ms inside
  `ShellExecuteW` before its target even starts (measured on this machine, any target; WT's UI thread waits for it),
  plus a file write on every pull. A protocol dispatch measures ~10 ms to `ShellExecuteW`'s return and ~25 ms to the
  handler's first instruction.
- **Footer**: `binder ⏎  ctrl+click · ctrl+shift+b`, right-aligned under the card: the link, then (dimmer) what works
  here. The core reads it from the state folder on every pull (`Core.FooterSetup`: `urlhandler.txt` exists → the link and
  `ctrl+click`; `hotkey.tsv` → its keys; ~0.06 ms). With neither, a plain `binder ⏎`: what to type.
- **Hotkey**: the install (or `pokeshell hotkey on`) adds a `splitPane` action (`User.pokeshell.binder`, `split:
  vertical`, `commandline: binder.exe --root <root> --pull latest`) and its `ctrl+shift+b` keybinding to settings.json
  (WT 1.21+ `actions` + `keybindings`; inline `keys` for older files; Ctrl+Shift+B is not bound in 1.24's defaults),
  verified and backed up like the skins. Keys already bound in settings.json: the install skips the hotkey and says so
  (`pokeshell hotkey on -Keys <keys>`). `--pull latest` lands on the newest pull (a fresh tab's card, caught or seen)
  unless it has expired, then on the last card caught: a key can't know which tab it was pressed in (the new pane
  doesn't inherit that tab's `POKESHELL_PULL`), and the newest pull is almost always the tab just opened.
- **Text half**: `v` in the app, from `packs/<pack>/cards/<card id>.json` (CARD_FORMAT); the view toggle moved to `d`.
- **Printed card**: `p` in the app and on the web (`r` is reload): the real scan beside ours, caught cards only (below).
  Caught cards only ("Empty, seen, caught" below). `binder --card <id> --text --first-frame` renders it headless.

## Entry points (all four ship)
| How | What happens |
|---|---|
| `binder` / `pokeshell binder` | Opens the terminal app full-screen in the current tab (alternate screen). `q` restores the prompt exactly as it was. If the exe is missing, it falls back to today's text table. |
| Hotkey (Windows Terminal keybinding, default `Ctrl+Shift+B`) | Opens the terminal app in a new pane next to your work (a `splitPane` action running `binder.exe --pull latest`): on your newest pull. The installer adds it to settings.json, the same way skins are installed. |
| Ctrl+click the pull | The card printed at the top of a new tab carries an OSC 8 hyperlink `pokeshell://binder?pull=<id>` on its `binder ⏎` footer. The installer registers the handler (`binder-link.exe`) and lists the scheme in `safeUriSchemes`, so it opens the binder on that card in a split pane, with no dialog. Without the binder app, the footer is a plain `binder ⏎`: what to type. |
| `binder --web` | Regenerates the static web binder from the latest pulls (about 1 s) and opens it in the default browser. |

## Landing
- It opens on the **last card you caught**: the binder page containing it, the card selected and shown in the detail
  panel. Never on a seen card: a newer pull that is pending or expired isn't in the binder yet. Every "newest pull"
  landing does the same: plain `binder`, `L` in the app, a `--set` / `--search` start (the last caught card they show,
  else their first card), the header's "last" pull. Nothing caught yet: the first card of the binder.
- An explicit request for a pull or card lands on that card's slot even when it isn't caught (it then shows its
  silhouette): `--pull <id>` and `--url pokeshell://binder?pull=<id>` (the `binder ⏎` link under a freshly pulled
  card), `--card <pack/char/tier>` or `--card <pack/card id>`, and the web page's `?card=`.
- The web page opens closed on its title page, as before; its fresh-pulls strip and best pulls are caught cards only.

## Earning a card
1. **Roll.** Each roll gets a pull id (ULID) and is logged with the `pending` flag. The id is exported to the tab as `POKESHELL_PULL`.
2. **First use.** The first real command in that tab (a hook on the prompt function; an empty Enter doesn't count) marks the pull `earned`, and prints one line once: `✦ Pikachu holo added to your binder`.
3. **Closed unused.** The pull stays pending and expires when the next session starts (or after 24 h).
4. **In the binder.** A new earned card shows a **NEW** sticker until it has been viewed. A pulled card that isn't
   earned (pending or expired) is **seen**: its silhouette (below).
- What counts as "use": the lookbook question `use_rule` decides this. The default is the first command.

Storage stays append-only: `pulls.log` gets `pending` / `earned:<id>` / `expired:<id>` lines. `collection.json` is a derived cache the binder rebuilds when it's stale. `viewed.txt` holds the ids already seen, which is what clears NEW stickers.

## Empty, seen, caught (both binders)
Every card slot is in one of three states, like a Pokédex:

| State | When | Shows |
|---|---|---|
| **Empty** | never pulled | the empty pocket: its number, name and rarity hint. No art; the text half stays hidden. |
| **Seen** | pulled, never earned: every pull of it is pending or expired | a **silhouette**: the sprite's shape in one flat dark shadow colour on plain card stock, with its name, number and rarity hint. No colours, scene, foil, shimmer, animation, shiny or NEW sticker, no ribbon or tape. The text half stays hidden. |
| **Caught** | earned at least once | the real card, exactly as before, with every effect |

- **Expired pulls now count as seen** (you saw the card and didn't catch it). Before `binder-seen`, expired pulls
  never showed. Both readers keep them (status `Expired` in the app, `"expired"` in data.json); the CLI's
  `pokeshell collection` table still leaves them out.
- **The detail panel** of a seen card says **seen** and how to catch it: "use the tab it was pulled in to catch it (5m ago)" while
  a pull of it is still pending, else "pull it again". It lists no pulls, copies, skins or history (those are caught
  pulls only).
- **Counts** are Pokédex counts: **caught N · seen M** (seen = slots seen but not caught), in the headers (app: `caught
  58 · seen 125` chips; web: chips, the cover label, the title page), on the completion line (`58/342 ■■□□ 17% · seen
  125`) and in the legends. Completion counts caught only. The word "pending" is gone from both binders.
- **Duplicates, best pulls, foils, shiny counts, pulls, streak, drought and activity** count caught pulls only.
- **The web's fresh-pulls strip** shows caught pulls only (seen ones are not there at all).
- **How the silhouette is made** (the same order in `ArtStore::silhouette` and the web export, `webexport.rs`): the sprite's opaque
  pixels, never a scene's background.
  1. Packs without real cards: the character's base (tier 0) art (web dex pages: the pulled sprite).
  2. A real card whose art is the plain sprite (the commons): its own art. A card's art is its plain sprite when at
     least 10% of it is transparent; every scene is full-bleed (0%), every common 26-66% (measured on the 342 cards).
  3. A scene card: the character's plain sprite from one of its commons in the pack. This is the shipped art, so it
     works on every install; about half the characters have a common.
  4. Else the colorscripts sprite: `vendor/pokemon-colorscripts/colorscripts/large/regular/<name>` (or
     `$POKESHELL_VENDOR`), then `dist/pokedex/<name>-common.ans`. Checkouts that build the art have these.
  5. Else the card art's own **sprite layer**: the sprite sits pixel-exact over the scene (docs/ART_METHOD.md) and only
     it changes colour in the `-shiny` art, so the pixels that differ, grown twice into the dark outline around them
     and with enclosed holes filled, are its shape. Rougher (eyes or colours a shiny keeps can nibble it), so it is the
     last resort. On a plain install, characters without a common land here.
  6. Else no shape: the seen card shows a "?" on its stock.
  The web exports a silhouette image only when no exported art already gives it (`img/<pack>/<character>/_seen.png`,
  `<card id>-seen.png`) and draws any of them blacked out (`filter: brightness(0)`).
- **The text half** (the moveset: HP, abilities, attacks, weakness, retreat; `v` in the app, the card on the web) shows
  for **caught cards only** (branch `binder-hide-text`; before, cards never pulled showed it too). `v` on a seen card
  says "seen: catch it to read its text (v)", on an empty one "not caught yet: catch it to read its text (v)". On the
  web an uncaught card's text isn't even in `data.json` (the web export leaves it out), and the page draws it for
  caught cards only as well.
- **The printed card** (`p` in both binders, like `v` it stays on as you move; the web remembers it in the browser):
  the real printed card, pokemontcg.io's scan (`images.large` in `packs/<pack>/cards/<id>.json`, else
  `images.pokemontcg.io/<set>/<number>_hires.png` from the card id), beside ours and as tall as it, for **caught cards
  only**; a seen or empty card shows nothing extra. Scans are never shipped (not in the repo, not in the art release):
  the app downloads one the first time it is shown (curl on a background thread, 5 s to connect, 20 s at most) into
  `<state>\cache\realcards\<set>\<file>.png`; the web page only carries the URL (`data.json` has it for caught cards
  only) and the browser loads it. Offline or no scan: a short note in its place, never a wait. In the app our card
  shrinks to make room (not below 12 rows); narrower than that, the printed card takes our card's place. It is drawn
  as sixel (crisp) where the terminal does sixel, else in half blocks: `POKESHELL_SIXEL=on|off|auto`, or config.txt
  `sixel=`, else auto: the first `p` asks the terminal (DA1, `ESC [ c`); sixel when the reply lists 4 (Windows Terminal
  1.22+), half blocks otherwise or when no reply comes within 300 ms. Sixel sizes assume Windows Terminal's 10x20
  virtual cell (`POKESHELL_CELL_PX=WxH` for other terminals).
- **The web detail of an empty card** is its empty pocket, as in the app: the name, number, rarity hint and set, its
  tags and the pull odds (the app's panel shows those too), but no art and no text half. A `?card=` link to a card
  never pulled opens the same.
- **Empty pockets lose their faint silhouette** (the pokedex and One Piece packs had one): a shape now means seen.

## Tags and search (both binders)
- **Search** (`/`), the same in both binders (`binder/src/query.rs`; the page's `search:begin`/`search:end` block is a
  port of it, and tests/test-earned.ps1 runs that block in node on the real cards):
  - **Words are forgiving.** A word matches a tag when it is inside it, or when its letters come in order from a word
    start with few gaps (fzf's v2 scoring: bonuses for word starts and runs must outweigh the gaps), so `pikchu` finds
    Pikachu, `lyc vmax` / `lycvmax` Lycanroc VMAX (not Lycanroc V), `evs rainbow` the Evolving Skies rare rainbows.
    Under 3 letters a word must start a word of the tag (`ex`, `v`). Every term must match (AND); `-term` (or
    `-key:value`) leaves out what matches. Case and accents don't matter (`flabebe` finds Flabébé).
  - **Tags**: set id and name, printed rarity and our tier id, subtypes, Pokémon types (from the card's
    `cards/<id>.json`, else pack.json's card fields), character, name, number, card id, artist, pack, for every slot;
    the page also has `attack:` / `ability:` (key-only, so bare words find the same cards in both binders), which
    match **caught cards only**: the moves are the text half, so a search can't reveal them. State words (bare,
    or `is:seen`) test the card: `caught`, `seen` (pulled, not caught), `missing` (not caught: empty or seen), `new`,
    `shiny`, `foil`. `owned` still works as `caught`, and `pending` as `seen` (both undocumented in the binders).
  - **`key:value`** matches that key's tags like a bare word (`rarity:rainbow`, `type:drk`, `artist:ito`); quotes only
    keep spaces (`rarity:"rare rainbow"`) and mean nothing else, in both binders (before, the app took a quoted value
    as a substring and the page as a whole tag). Three keys are exact: `set:` names the best-matching sets by id or
    name (`set:swsh1` is Sword & Shield, not swsh10; `set:30th`, `set:evolving`, `set:evsk`), ranked like the set
    picker; `number:17` is the printed numerator (17/203, not 117 or 170; `number:17/203` the whole number); `id:` is
    the whole card id.
  - **Results stay binder pockets**, in binder order (set, then printed number), not a ranked list. While a search is
    on, pack and set tabs without matches disappear and the rest show their count (app: the pack tabs, the set tab and
    the `S` picker's rows; page: the pack and set dividers).
  - **Opening a result** (app: Enter, or a click on the selected card; page: a click) clears the search and shows the
    card on its real, unfiltered binder page among its neighbours, selected and glowing for 1.6 s (the page then opens
    its details, which close back onto that page). Esc, or clearing the search, returns to where you were before it.
- **Sets**: real-card packs get a set tab (app: next to the pack tabs, `S` or a click opens the set picker, with each
  set's completion, filtered by typing; web: a divider tab per set). A set page is its checklist: every card of that
  set in pack.json `cards`, in printed-number order (plain numbers, the secret rares past the printed total after
  them, then prefixed groups such as GG, SV, TG, each in order, then letters such as B / G / R), with empty pockets
  for the cards not pulled. A real card is its own slot (a character can have several cards per rarity across sets).
  `--set` takes an id or a name, matched the same way as `set:`.
- **Completion** counts caught cards only; seen ones are shown apart (`13/193 7% · seen 45`), since a seen card isn't
  in the binder until it is caught. `o` shows caught cards only, `m` the missing ones (empty or seen).
- **Web**: a card's page lists its tags as chips; a click runs that search.

## Web binder
- **Now:** a static file, rebuilt on open (`binder --export-web`, webexport.rs, into `<state>\web`). Nothing stays running. Each real
  card shows its text half, once caught, from `packs/<pack>/cards/<id>.json` (HP, abilities, attacks with energy costs, weakness /
  resistance / retreat, rules; docs/CARD_FORMAT.md); the tab skin stays in the card's details. Odds are the game's
  (only tiers with a built card roll). Seen cards show as silhouettes and are never counted. Decoded art is cached
  (`img\.cache.json`), so a rebuild takes well under a second once the art is cached.
- **Soon: hosted backend** for sync and battles; see below.

## Backend (next phase: sync + battles)
- **Identity:** GitHub device-flow login. No passwords are stored; the token is kept in the OS keychain (Windows Credential Manager, libsecret on Linux).
- **Sync:**
  - The client pushes earned pull records (`id, time, pack, character, tier, skin, shiny`), never the whole log.
  - The server merges by pull id, so it's idempotent across machines.
  - Pending and expired (seen) pulls never leave the machine.
- **Anti-farm:** the server rate-limits accepted pulls per account per hour to match the client's tab-spawn rate limit. Cards are cosmetic, so light checks are enough.
- **Hosted binder:** `https://<host>/u/<github-login>`, the same web UI reading from the API, public or private per user.
- **Battles (to spec separately):**
  - Card stats come from pack data: HP/attacks from the real card for Pokémon, bounty for One Piece.
  - Turn-based, async over the API, playable from the terminal app (a `battle` panel) and the web.
  - Open questions: whether cards are wagered or just used, whether the rules are real TCG-lite or our own simpler rules, and how matchmaking works.
- **Candidate stack:** a small Rust (axum) or Cloudflare Workers + D1 service; the pull records are tiny.

## Open questions
- ~~The hotkey default, and whether the pane opens left or right.~~ Decided (`binder-links`): `Ctrl+Shift+B`, installed
  by default; the pane opens on the right (a vertical split), from the key and from the link alike.
- Whether the NEW sticker should also appear in the tab card footer ("3 new in binder").
- Battles: the rules scope (above), and whether they arrive in the same release as sync.
