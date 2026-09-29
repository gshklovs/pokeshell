# Roadmap

## v1 (current)
Windows Terminal + PowerShell: pack pulls on new tabs, holo pixel-shader skins, pixel art per rarity,
shinies, and the Pokemon pack (Gen 1 starters + Pikachu). Distributed via
the PowerShell Gallery (`Install-Module pokeshell`).

## v2

### Card-accurate pixel art
Still pixel art, but each character's shape, pose and expression should match real card illustrations
rather than generic sprites: the silhouette, stance and facial expression a collector would recognize from
the actual cards, with each rarity variant echoing its card type (e.g. the full-art variant modeled on how
full-art cards frame and pose the character, the gold variant on the secret-rare gold cards). Agents
should study reference card art per character and per rarity before redrawing, then iterate with
`tools/build_art.py` previews side by side with the reference.

### Full card by default
Every pull prints as a full card (art plus the card's text: name, HP, attacks, weakness/retreat, flavor), as
decided in the lookbook. A setting switches to picture-only (just the art):
`pokeshell display card|picture` (persisted in the config) and `POKESHELL_DISPLAY=picture` for one shell.
Narrow windows fall back per the lookbook's choice.

### Earned collection
You only collect a card if you actually use the terminal session it was pulled in.
- A pull starts as *pending*, tied to its tab (pull id passed to the tab, e.g. an env var).
- It becomes *collected* once the session is used; open question: what counts as use (first real
  command run, N commands, a minimum time open, or a Claude Code session started in it).
- Tabs closed unused expire their pull, so spamming new tabs doesn't farm cards.
- Backend: local first (`%LOCALAPPDATA%\pokeshell\collection.json`), `pokeshell collection` shows the
  binder (per pack, character, variant, shiny, counts, first-pulled date). Open question: optional sync
  across machines (GitHub gist, or a small hosted API for trading/leaderboards).

## Later
- Linux (target: Ubuntu users): bash/zsh startup hook + the same prebuilt art. Install from the GitHub repo:
  `curl -fsSL .../install.sh | bash` (or `git clone` + `./install.sh`) into `~/.local/share/pokeshell`, one line
  added to `~/.bashrc`, `pokeshell update` for new versions; no root. Later a `.deb` on GitHub Releases
  (`sudo apt install ./pokeshell.deb`); a PPA only if there's real demand. Holo skins ported to GLSL for
  Ghostty's `custom-shader` (GNOME Terminal, Ubuntu's default, has no shaders: art + pulls only there).
  Keep packs/art/pack.json platform-neutral; platform-specific scripts and shader languages in their own folders.
- Faster foil tabs: slim the heaviest shaders (cosmos, galaxy-reverse, illustration-rare) toward <150 ms
  compile, since Windows Terminal only accepts HLSL source (precompiled .cso is rejected).
- Sister project `opshell`: the One Piece pack (Luffy, Zoro, Sanji; super rare / secret rare / manga rare
  foils) on the same engine.
