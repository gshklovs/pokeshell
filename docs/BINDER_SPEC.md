# Binder UX spec (draft)

Status: draft, decisions from 2026-09-28. The prototypes are in `style-lab/binder-tui` (Rust, ratatui) and `style-lab/binder-web` (static HTML).

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

## Web binder
- **Now:** a static file, rebuilt on open (`style-lab/binder-web/export.py`, which moves to `tools/`). Nothing stays running.
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
