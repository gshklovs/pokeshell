---
name: new-card-set
description: Build a new set of pokeshell card art the way Evolving Skies and 30th Celebration were built (colorscripts sprite over the real card's scene, one effect per printed rarity, 16-frame loops, text half), or rebuild, audit or import cards of an existing set. Use for "make the <set> cards", "next Pokémon set", "One Piece / MTG Marvel set", "redo card X", "import the approved cards", "audit the set", or any work in artlab/.
---

The method is **docs/ART_METHOD.md**. Read it before doing anything: the rules in section 1 are the user's
decisions and are not up for change. The code is in `artlab/` (tracked). The data (scans, card JSON, masks,
outputs) is in `style-lab/<set>/`, git-excluded (`artlab/artpaths.py`; `$env:ARTLAB_DATA` overrides it). Python is
the repo's `.venv` (`pip install -r artlab\requirements.txt`). Never read API keys or `.env` files.

Checklist for a new Pokémon set (ART_METHOD section numbers in brackets):

1. **Set up the set.**
   - Write `artlab/sets/<folder>/set.json`: set id, scan prefix, printed total, rarity → group map, labels. [4, 5]
   - Run `artlab\tools\fetch_set.py <folder>`: the set list, `cards/`, and the hires scans. It sends a User-Agent and retries; re-run it until nothing is missing. [4]
2. **Plan.** Run `artlab\tools\make_plan.py <folder>`, then read every scan for forms (Dusk / Midnight, Crowned, Gigantamax, regional) and put them in `set.json` `forms`. Trainers and sprite-less cards are skipped with a reason. [5]
3. **Set lib.** Copy the `sets/p30/p30*.py` pattern: `<x>lib.py` calls `setlib.use_set(E, "<folder>", "<prefix>")`, and the evs modules are loaded by file path. [14]
4. **Ladder.** Build ONE card per printed rarity with its effect from the catalogue:
   - Pick the effect from the catalogue. [9]
   - Commons are the plain sprite. Recolours only at Rainbow (0.55), Gold and Futuristic (≤ 0.35). Alt-art paintings get the Umbreon 215 treatment. [10, 11]
   - Every card needs the 16-frame loop with the last frame equal to the static art, and its text half. [12, 13]
5. **Show the ladder.** Put it in the lookbook as **real card | ours | ours + text half** (`artlab\tools\lb_set.py`, page from `artlab\lookbook\template.html`), then wait for the user's sign-off. [15]
6. **Brief.** Write `FULLSET.md` (copy `sets/p30/FULLSET.md`) and give one agent per `plan.json` group a `batch_<group>.py`: masks → build → anim → verify → sheet. Agents never edit shared files. [6-8, 14]
7. **Lookbook per group.** Add each group's side-by-side section to the lookbook as it lands, and move answered questions to "Decided". [15]
8. **Audit.** Run one audit agent over every card: treatment, facing, forms, ghosts, data, anims. Clear errors are fixed in `batch_fixes.py`; taste calls are flagged in the lookbook. [16]
9. **Import** only the approved ids:
   - Run `tools\build_realcards.py import <batch> --only <ids>`, with `--dry-run` first.
   - If `packs\pokemon\pack.json` changed only in line endings, restore it.
   - Add the tier, weight, frame colour and own tab skin for each new rarity. [17, 18]
10. **Test** from PowerShell: `powershell -NoProfile -File tests\test-cards.ps1`. Then check the definition of done. [19]
11. **Skipped list**: add the set to `SETS` in `tools/skipped_report.py` (a `why` for Pokémon skipped on purpose) and
    run it, so `docs/SKIPPED.md` lists every card not served and why. [19]

Rebuilding one card: run the **highest** module that lists it (ladder < group batch < rainbow_secret / altart <
batch_fixes; section 14), in an isolated `$env:ARTLAB_DATA` first when you only need to check it (section 21).
Worked example with exact commands: section 20 (Leafeon V swsh7-7). One Piece / MTG Marvel: section 23.

Hard rules:

- Test in isolation only. Never write `%LOCALAPPDATA%\pokeshell`, Windows Terminal `settings.json`, `$PROFILE` or the registry.
- Never overwrite the live `dist\pokemon` / `packs\pokemon\art` from a test run.
- Never spawn WT tabs.
