# Binder UX spec

Status: **built** on branch `binder-earned` (2026-09-29): the earned rule, all four entry points, tags and search.
The terminal app is `binder/` (Rust, ratatui; from the `style-lab/binder-tui` prototype), the web binder is
`tools/binder_web.py` + `tools/binder-web/index.html` (from `style-lab/binder-web`). Still open: the backend (below),
`collection.json` (not needed so far: reading `pulls.log` takes a few ms), and the open questions at the end.

## Implementation notes
- **Pull log** (`pulls.log`, append-only, docs in `scripts/lib/Pokeshell.cs`): a pull line keeps its 8 columns and adds
  `pending` to the flags column plus `id=<ulid>` and `boot=<unix s of the last boot>` columns (`key=value`, so more can
  follow). Events are 2-column lines: `<time> earned:<id>` / `<time> expired:<id>`. A line without an id is earned.
  A pending pull with no event is expired after 24 h or when `boot=` differs from this boot session's by more than
  2 minutes; the CLI then writes its `expired:<id>` line. One rule, three readers: `Core.ReadPulls` (C#),
  `binder/src/data.rs`, `tools/binder_web.py`. Real-card packs then resolve each pull (`retired`, docs/PACK_FORMAT.md).
- **First use**: a `PreCommandLookupAction` delegate in the core, registered by `Core.Startup` itself (no extra
  PowerShell on the tab-open path), hands the host a small wrapper whenever it looks up `prompt`: it checks
  `Get-History`, and runs whatever `prompt` exists then (so a `function prompt` later in `$PROFILE` still works). The
  foil tab registers it from `Show-PokeshellPull`. Removed once the pull is earned or expired.
- **Use rule**: config `earn` = `first-command` (default) | `minutes:N` (earned at the first prompt after the tab has
  been open N minutes) | `off` (logged earned, no hook).
- **Viewed**: the app appends a card's ids to `viewed.txt` when it shows it; its NEW sticker stays until you move on.
- **Click**: the OSC 8 link is on the `binder ⏎` footer only (Windows Terminal underlines link text, which would stripe
  the art). The `pokeshell://` handler (`pokeshell urlhandler on`) runs `binder.exe --url "%1"`, which accepts only
  `pokeshell://binder?pull=<ulid>` or `?card=<pack/char/tier>`. Windows Terminal may refuse non-http(s) link schemes;
  then the hint is the way in.
- **Hotkey**: `pokeshell hotkey on` adds a `splitPane` action (`User.pokeshell.binder`) and its `ctrl+shift+b`
  keybinding to settings.json (WT 1.21+ `actions` + `keybindings`; inline `keys` for older files), verified and backed
  up like the skins; refuses keys that are already bound; `off` / `pokeshell uninstall` restore the file byte for byte.
- **Text half**: `v` in the app, from `packs/<pack>/cards/<card id>.json` (CARD_FORMAT); the view toggle moved to `d`.

## Entry points (all four ship)
| How | What happens |
|---|---|
| `binder` / `pokeshell binder` | Opens the terminal app full-screen in the current tab (alternate screen). `q` restores the prompt exactly as it was. If the exe is missing, it falls back to today's text table. |
| Hotkey (Windows Terminal keybinding, default `Ctrl+Shift+B`) | Opens the terminal app in a new pane next to your work (`wt -w 0 sp -V binder.exe`). The installer adds it to settings.json, the same way skins are installed. |
| Click the pull | The card printed at the top of a new tab carries an OSC 8 hyperlink `pokeshell://binder?pull=<id>`, registered as a URL handler, which opens the binder on that card. If link handlers aren't available, the card footer shows a hint instead: `binder ⏎`. |
| `binder --web` | Regenerates the static web binder from the latest pulls (about 1 s) and opens it in the default browser. |

## Landing
- It always opens on the **newest pull**: the binder page containing that card, with the card selected and shown in the detail panel.
- `--card <pack/char/tier>` and `--pull <id>` (used by the click link) override that.

## Earning a card
1. **Roll.** Each roll gets a pull id (ULID) and is logged with the `pending` flag. The id is exported to the tab as `POKESHELL_PULL`.
2. **First use.** The first real command in that tab (a hook on the prompt function; an empty Enter doesn't count) marks the pull `earned`, and prints one line once: `✦ Pikachu holo added to your binder`.
3. **Closed unused.** The pull stays pending and expires when the next session starts (or after 24 h). Expired pulls never show.
4. **In the binder.** A new earned card shows a **NEW** sticker until it has been viewed. Pending cards show greyed out with "use its tab to earn it".
- What counts as "use": the lookbook question `use_rule` decides this. The default is the first command.

Storage stays append-only: `pulls.log` gets `pending` / `earned:<id>` / `expired:<id>` lines. `collection.json` is a derived cache the binder rebuilds when it's stale. `viewed.txt` holds the ids already seen, which is what clears NEW stickers.

## Tags and search (both binders)
- **Tags per card**: set id and name, printed rarity and our tier id, subtypes, Pokémon types (from the card's
  `cards/<id>.json`, else pack.json's card fields), character, artist, pack; state tags `shiny`, `foil`, `new`,
  `pending` (and `owned`, `missing`) from the pulls.
- **Search** (`/`): words match any tag; `key:value` / `key:"a b"` filter one tag (keys: set, rarity, tier, type,
  subtype, char, artist, pack, name, number, id); state words stand alone. Example: `set:swsh7 rarity:"rare rainbow"`.
  Same parser in `binder/src/query.rs` and the page.
- **Sets**: real-card packs get a set tab (app: next to the pack tabs, `S` cycles; web: a divider tab per set). A set
  page is its checklist: every card of that set in pack.json `cards`, in printed-number order, with empty pockets for
  the cards not pulled. A real card is its own slot (a character can have several cards per rarity across sets).
- **Web**: a card's page lists its tags as chips; a click runs that search.

## Web binder
- **Now:** a static file, rebuilt on open (`tools/binder_web.py` into `<state>\web`). Nothing stays running.
- **Soon: hosted backend** for sync and battles; see below.

## Backend (next phase: sync + battles)
- **Identity:** GitHub device-flow login. No passwords are stored; the token is kept in the OS keychain (Windows Credential Manager, libsecret on Linux).
- **Sync:**
  - The client pushes earned pull records (`id, time, pack, character, tier, skin, shiny`), never the whole log.
  - The server merges by pull id, so it's idempotent across machines.
  - Pending pulls never leave the machine.
- **Anti-farm:** the server rate-limits accepted pulls per account per hour to match the client's tab-spawn rate limit. Cards are cosmetic, so light checks are enough.
- **Hosted binder:** `https://<host>/u/<github-login>`, the same web UI reading from the API, public or private per user.
- **Battles (to spec separately):**
  - Card stats come from pack data: HP/attacks from the real card for Pokémon, bounty for One Piece.
  - Turn-based, async over the API, playable from the terminal app (a `battle` panel) and the web.
  - Open questions: whether cards are wagered or just used, whether the rules are real TCG-lite or our own simpler rules, and how matchmaking works.
- **Candidate stack:** a small Rust (axum) or Cloudflare Workers + D1 service; the pull records are tiny.

## Open questions
- The hotkey default, and whether the pane opens left or right.
- Whether the NEW sticker should also appear in the tab card footer ("3 new in binder").
- Battles: the rules scope (above), and whether they arrive in the same release as sync.
