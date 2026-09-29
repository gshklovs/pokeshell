// pokeshell core: the startup pull's decision logic, the loop guards and the spawn gate.
//
// Why C#: Windows PowerShell 5.1 pays ~1 ms the first time each statement/call site runs, so the same
// logic interpreted costs ~100 ms per new tab. This file is compiled once (at `pokeshell install`, or by
// the first tab that needs it) into %LOCALAPPDATA%\pokeshell\pokeshell-core-*.dll with the C# compiler
// that ships with Windows / PowerShell; loading it and making one call costs ~10 ms.
// PowerShell (lib\roll.ps1) keeps the parts that touch the console and Windows Terminal.
// C# 5 only (the .NET Framework compiler used by Windows PowerShell): no $"", no ?., no => members.
//
// Loop-safety layers (each one alone stops a tab from spawning another):
//   1 identity  WT_PROFILE_ID must be a plain profile (skinned tabs have their own GUIDs)
//   2 argv      the shell was started with no arguments (only -NoLogo is tolerated); pulled tabs
//               are started with -NoExit -EncodedCommand
//   3 markers   POKESHELL_PULL / POKESHELL_ROLLED in the environment, and CARDSHELL_ROLLED, the marker shared with
//               opshell: whichever hook rolls first sets it, so with both in $PROFILE only one rolls per tab
//   4 gate      machine-wide lock file: one spawn per 3 s; a 6th spawn inside 60 s trips a 10-minute breaker
//   5 install   only skins recorded by `pokeshell install` can drop; nothing installed means no spawns
//   6 kill      `pokeshell off` (enabled=0) or POKESHELL_DISABLE=1
//
// The earned rule (docs/BINDER_SPEC.md): every pull gets an id (a ULID) and is logged `pending`; the tab's first
// real command earns it (Earn, below: it appends an `earned:<id>` line). pulls.log stays append-only TSV:
//   pull    time pack character tier art skin shiny flags [id=<ulid> boot=<unix s> key=value...]
//           flags: comma-separated notes (denied:rate, foil-not-placed:x, dryrun, ...) plus "pending"
//   event   time earned:<id>   |   time expired:<id>
// A line without an id (older logs) is earned. A pending pull with no event expires after 24 h, or when its boot
// session is over (boot= differs from this boot's by more than BootSlackSec). ReadPulls applies these rules;
// binder/src/data.rs and tools/binder_web.py mirror them.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;

namespace Pokeshell
{
    public class Pull
    {
        public string Action = "skip";   // skip | stale | common | foil | foil-denied
        public string Reason = "";
        public string Pack = "", Character = "", Name = "", TierId = "", Label = "", Art = "", Skin = "", Guid = "";
        public string Frame = "", Tag = "", Display = "card";   // optional card frame (tier "frame" in pack.json) and title tag (pack.json "tags")
        public string Poster = "", Bounty = "";   // frame-style texts (pack.json "poster_names", "bounties"): the wanted poster's full name and bounty
        public int Tier;
        public bool Shiny;
        public string[] WtArgs;
        public string Id = "";            // the pull id (ULID); also the tab's POKESHELL_PULL
        public string Earn = "first-command";   // the use rule (config `earn`): first-command | minutes:N | off
        public long Boot;                 // boot session (unix seconds of the last boot)
        public long PullTicks;            // UTC ticks of the roll

        // The earned rule's additions are made on the way out, so Roll() sets these as before:
        //   Text / FallbackText read back with the binder footer (Core.WithFooter) once the pull has an id;
        //   LogLine / FallbackLogLine are set to the first 8 columns (time .. the flags / note column) and read back
        //   complete: the pending flag and the id / boot columns added (Core.FinishLine).
        string text = "", fallbackText = "", logHead = "", fallbackHead = "";
        /// art + banner to print (common / denied pulls)
        public string Text { get { return Core.WithFooter(text, Id); } set { text = value ?? ""; } }
        /// what to print if opening the foil tab fails
        public string FallbackText { get { return Core.WithFooter(fallbackText, Id); } set { fallbackText = value ?? ""; } }
        public string LogLine { get { return Core.FinishLine(logHead, "", this); } set { logHead = value ?? ""; } }
        /// the log line if the foil ends up shown here as a common
        public string FallbackLogLine { get { return Core.FinishLine(fallbackHead, "", this); } set { fallbackHead = value ?? ""; } }
        /// the complete pulls.log line with an extra note (dryrun, foil-not-placed:x, ...) before the pending flag
        public string Line(string extra) { return Core.FinishLine(logHead, extra, this); }
        public string FallbackLine(string extra) { return Core.FinishLine(fallbackHead, extra, this); }
    }

    /// <summary>
    /// The earned rule in the tab that shows a pull: its first real command (anything that lands in Get-History; an
    /// empty Enter doesn't) appends `earned:&lt;id&gt;` to pulls.log and prints one dim line, once.
    ///
    /// How: a PreCommandLookupAction delegate. Whenever the host looks up `prompt` (before every prompt), it hands
    /// back a small wrapper that checks the history, then runs whatever `prompt` function is defined at that moment,
    /// so a `function prompt` later in $PROFILE (or an oh-my-posh style prompt) keeps working and doesn't unhook us.
    /// Every other lookup returns at once. Registering is one call from the $PROFILE hook (a few microseconds; the
    /// wrapper is only parsed at the first prompt); once the pull is earned or expired the previous action is back.
    /// </summary>
    public static class Earn
    {
        static string id, stateDir, mode, text, msg;
        static long ticks;
        static bool done;
        static System.Management.Automation.CommandInvocationIntrinsics invoke;
        static EventHandler<System.Management.Automation.CommandLookupEventArgs> prev, mine;
        static System.Management.Automation.ScriptBlock wrapper;

        const string WrapperText =
            "try { $__pokeshellH = Get-History -Count 1; $__pokeshellM = [Pokeshell.Earn]::OnPrompt($(if ($__pokeshellH) { [long]$__pokeshellH.Id } else { 0L })); " +
            "if ($__pokeshellM) { $Host.UI.WriteLine($__pokeshellM) } } catch { }\n" +
            "if ($function:prompt) { & $function:prompt } else { \"PS $($executionContext.SessionState.Path.CurrentLocation)$('>' * ($nestedPromptLevel + 1)) \" }";

        /// Start watching this tab for the first command. No-op when the rule is off, or already registered here.
        public static void Register(System.Management.Automation.EngineIntrinsics engine, string pullId, string state, string earnMode,
                                    long pullUtcTicks, string name, string label, bool shiny)
        {
            if (engine != null) Register(engine.InvokeCommand, pullId, state, earnMode, pullUtcTicks, name, label, shiny);
        }

        /// The $PROFILE hook's path (Core.Startup, which gets $ExecutionContext): no PowerShell call site of its own.
        public static void Register(System.Management.Automation.EngineIntrinsics engine, Pull r, string state)
        {
            try { if (engine != null) Register(engine.InvokeCommand, r.Id, state, r.Earn, r.PullTicks, r.Name, r.Label, r.Shiny); }
            catch (Exception) { }
        }

        static void Register(System.Management.Automation.CommandInvocationIntrinsics ic, string pullId, string state, string earnMode,
                             long pullUtcTicks, string name, string label, bool shiny)
        {
            if (ic == null || string.IsNullOrEmpty(pullId) || id != null || Core.EarnMode(earnMode) == "off") return;
            id = pullId; stateDir = state; mode = earnMode; ticks = pullUtcTicks; done = false; msg = null;
            text = "\u001b[2m\u2726 " + name + " " + label + (shiny ? " (shiny)" : "") + " added to your binder\u001b[0m";
            invoke = ic;
            prev = invoke.PreCommandLookupAction;
            mine = OnLookup;
            invoke.PreCommandLookupAction = mine;
        }

        public static bool Active { get { return id != null && !done; } }

        static void OnLookup(object sender, System.Management.Automation.CommandLookupEventArgs e)
        {
            if (prev != null) prev(sender, e);
            if (done || !string.Equals(e.CommandName, "prompt", StringComparison.OrdinalIgnoreCase)) return;
            if (wrapper == null) wrapper = System.Management.Automation.ScriptBlock.Create(WrapperText);
            e.CommandScriptBlock = wrapper;
            e.StopSearch = true;
        }

        /// Called by the prompt wrapper with the newest history id (0: nothing run yet). Returns the line to print, or null.
        public static string OnPrompt(long lastHistoryId)
        {
            if (done || id == null) return null;
            try
            {
                long now = DateTime.UtcNow.Ticks;
                string v = Core.EarnCheck(mode, lastHistoryId, ticks, now);
                if (v == "wait") return null;
                done = true;
                Core.Log(stateDir, "pulls.log", Core.EventLine(v == "earn" ? "earned" : "expired", id, now));
                msg = v == "earn" ? text : null;
            }
            catch (Exception) { done = true; msg = null; }
            // hand command lookup back as it was
            if (invoke != null && invoke.PreCommandLookupAction == mine) invoke.PreCommandLookupAction = prev;
            string m = msg; msg = null;
            return m;
        }

        /// tests: forget this process's registration
        public static void Reset()
        {
            if (invoke != null && mine != null && invoke.PreCommandLookupAction == mine) invoke.PreCommandLookupAction = prev;
            id = null; done = false; msg = null; prev = null; mine = null; invoke = null;
        }
    }

    /// One pull as ReadPulls sees it, with the earned rule applied.
    public class PullRecord
    {
        public string Time = "", Pack = "", Character = "", Tier = "", Art = "", Skin = "", Flags = "", Id = "", Card = "";
        public bool Shiny, New;
        public bool Derived;               // expired by age / boot session (no expired:<id> line yet)
        public long Boot;
        public string Status = "earned";   // earned | pending | expired
    }

    public static class Core
    {
        public const string DefaultPlainProfiles =
            "{61c54bbd-c2c6-5271-96e7-009a87ff44bf},{574e775e-4f2a-5b96-ac1e-a2962a402336}";
        /// Shared with opshell (the One Piece sister project): set by whichever hook rolls a tab first, checked by both,
        /// so a $PROFILE with both hooks gets one pull per tab. Keep the name in sync across the cardshell tools.
        public const string SharedMarker = "CARDSHELL_ROLLED";
        public const int MinGapSec = 3, WindowSec = 60, Burst = 5, TripSec = 600;
        const long Tps = 10000000L;

        public static Dictionary<string, string> ReadConfig(string stateDir)
        {
            var cfg = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            cfg["pack"] = "pokemon"; cfg["enabled"] = "1"; cfg["plain_profiles"] = DefaultPlainProfiles; cfg["earn"] = "first-command";
            string p = Path.Combine(stateDir, "config.txt");
            if (File.Exists(p))
                foreach (string line in File.ReadAllLines(p))
                {
                    int i = line.IndexOf('=');
                    if (i > 0 && !line.StartsWith("#")) cfg[line.Substring(0, i).Trim()] = line.Substring(i + 1).Trim();
                }
            return cfg;
        }

        static bool Env(string name) { return !string.IsNullOrEmpty(Environment.GetEnvironmentVariable(name)); }

        /// How pulls print: "card" (default: the framed card, or art + banner for frameless tiers) or "picture"
        /// (just the art). POKESHELL_DISPLAY overrides the config's `display` for one shell.
        public static string Display(Dictionary<string, string> cfg)
        {
            string v = Environment.GetEnvironmentVariable("POKESHELL_DISPLAY"), c;
            if (string.IsNullOrEmpty(v) && cfg != null && cfg.TryGetValue("display", out c)) v = c;
            return string.Equals((v ?? "").Trim(), "picture", StringComparison.OrdinalIgnoreCase) ? "picture" : "card";
        }

        // "" when this shell may roll, otherwise why not (layers 1-3 and 6)
        public static string SkipReason(string profileId, string[] argv, Dictionary<string, string> cfg)
        {
            if (Env("POKESHELL_PULL")) return "marker:POKESHELL_PULL";
            if (Env("POKESHELL_ROLLED")) return "marker:POKESHELL_ROLLED";
            if (Env(SharedMarker)) return "marker:" + SharedMarker;   // opshell (or another cardshell hook) already rolled this tab
            if (Environment.GetEnvironmentVariable("POKESHELL_DISABLE") == "1" || cfg["enabled"] == "0") return "disabled";
            if (string.IsNullOrEmpty(profileId)) return "not-windows-terminal";
            bool plain = false;
            foreach (string g in cfg["plain_profiles"].Split(','))
                if (string.Equals(g.Trim(), profileId.Trim(), StringComparison.OrdinalIgnoreCase)) plain = true;
            if (!plain) return "profile";
            if (argv == null || argv.Length < 1) return "args";
            for (int i = 1; i < argv.Length; i++)
                if (!string.Equals(argv[i], "-NoLogo", StringComparison.OrdinalIgnoreCase) &&
                    !string.Equals(argv[i], "/NoLogo", StringComparison.OrdinalIgnoreCase)) return "args";
            return "";
        }

        // Layer 4. Returns "ok" (and records the spawn) or why it refused: rate | tripped | busy.
        // The file is opened exclusively, so concurrent tabs serialize; one that can't get the lock refuses.
        public static string EnterSpawnGate(string stateDir, long now)
        {
            long gap = MinGapSec * Tps, win = WindowSec * Tps, trip = TripSec * Tps;
            Directory.CreateDirectory(stateDir);
            FileStream fs;
            try { fs = new FileStream(Path.Combine(stateDir, "spawn-gate.txt"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None); }
            catch (IOException) { return "busy"; }
            catch (UnauthorizedAccessException) { return "busy"; }
            using (fs)
            {
                var bytes = new byte[fs.Length];
                int n = 0; while (n < bytes.Length) { int r = fs.Read(bytes, n, bytes.Length - n); if (r <= 0) break; n += r; }
                long tripUntil = 0; var recent = new List<long>();
                foreach (string raw in Encoding.ASCII.GetString(bytes, 0, n).Split('\n'))
                {
                    string line = raw.Trim(); long v;
                    if (line.StartsWith("trip ")) { if (long.TryParse(line.Substring(5), out v)) tripUntil = v; }
                    else if (long.TryParse(line, out v) && v > now - win && v <= now + win) recent.Add(v);   // drop far-future (clock changed)
                }
                if (tripUntil > now + trip) tripUntil = 0;   // the clock went backwards past the trip
                string reason = "ok";
                if (tripUntil > now) reason = "tripped";
                else
                {
                    foreach (long t in recent) if (Math.Abs(now - t) < gap) reason = "rate";
                    if (reason == "ok" && recent.Count >= Burst) { reason = "tripped"; tripUntil = now + trip; }
                }
                if (reason == "ok") recent.Add(now);
                var sb = new StringBuilder();
                if (tripUntil > now) sb.Append("trip ").Append(tripUntil).Append('\n');
                foreach (long t in recent) sb.Append(t).Append('\n');
                byte[] ob = Encoding.ASCII.GetBytes(sb.ToString());
                fs.SetLength(0); fs.Position = 0; fs.Write(ob, 0, ob.Length); fs.Flush();
                return reason;
            }
        }

        // art + banner, e.g. "secret rare : Pikachu (shiny)". Falls back to the non-shiny / common art, then none.
        public static string PullText(string root, string pack, string character, string name, string art, string label, int tier, bool shiny)
        {
            return PullText(root, pack, character, name, art, label, tier, shiny, "", "");
        }

        /// With a frame (a preset name or comma-separated #rrggbb gradient stops), the art is drawn inside a
        /// rounded box instead of above the banner: name (and tag) on the top edge, label on the bottom edge.
        public static string PullText(string root, string pack, string character, string name, string art, string label, int tier, bool shiny,
                                      string frame, string tag)
        {
            return PullText(root, pack, character, name, art, label, tier, shiny, frame, tag, false);
        }

        /// picture = just the art: no frame, no banner (the `display` setting: card | picture)
        public static string PullText(string root, string pack, string character, string name, string art, string label, int tier, bool shiny,
                                      string frame, string tag, bool picture)
        {
            return PullText(root, pack, character, name, art, label, tier, shiny, frame, tag, picture, "", "");
        }

        /// poster / bounty: the texts a frame style may use instead of the name / tag (the wanted poster's full
        /// name under the art and the bounty on its bottom edge); "" falls back to the name (upper-cased) / tag.
        public static string PullText(string root, string pack, string character, string name, string art, string label, int tier, bool shiny,
                                      string frame, string tag, bool picture, string poster, string bounty)
        {
            string b = Path.Combine(Path.Combine(Path.Combine(root, "dist"), pack), character + "-");
            string file = b + art + "-shiny.ans";
            if (!shiny || !File.Exists(file)) file = b + art + ".ans";
            if (!File.Exists(file)) file = b + "common.ans";
            string raw = File.Exists(file) ? File.ReadAllText(file, Encoding.UTF8) : "";
            string img = raw.Replace("\r\n", "\n").Replace("\n", "\r\n");
            if (picture) return "\r\n" + img + "\r\n";
            if (!string.IsNullOrEmpty(frame))
            {
                if (FrameStyle(frame) == "wanted")
                    return "\r\n" + Wanted(raw, frame, character, string.IsNullOrEmpty(poster) ? (name ?? "").ToUpperInvariant() : poster,
                                            string.IsNullOrEmpty(bounty) ? (tag ?? "") : bounty, label ?? "", shiny) + "\r\n";
                return "\r\n" + Framed(raw, FrameStops(frame), name, tag, label, shiny) + "\r\n";
            }
            string[] colors = { "38;2;150;150;150", "38;2;185;215;235", "38;2;110;165;255", "38;2;225;120;230", "38;2;240;200;80" };
            string c = colors[Math.Min(Math.Max(tier, 0), colors.Length - 1)];
            const string e = "\u001b";
            return "\r\n" + img + "  " + e + "[1;" + c + "m" + label + e + "[0;" + c + "m : " + name + (shiny ? " (shiny)" : "") + e + "[0m\r\n\r\n";
        }

        // ---- card frames
        // (plain arrays and a switch, no generic collections: each new generic instantiation costs JIT time on the startup path)
        static readonly string[] FramePresets = {
            "plain",   "#c9a93a,#f4dc6a,#c9a93a",                                   // the yellow border of a regular card
            "silver",  "#8d97a5,#eef3f8,#9aa6b4,#f7fafc,#8d97a5",
            "holo",    "#7fa7d9,#e6f0ff,#b59ce0,#e8fbff,#7fd3c9",
            "rainbow", "#ff6b8b,#ffb86b,#ffe66b,#7df09a,#6bd5ff,#9a8bff,#ff6bd6",
            "gold",    "#b8862b,#fff1b0,#d4a43a,#fff7d6,#c8952e",
        };

        static int Hex(char c) { return c >= '0' && c <= '9' ? c - '0' : c >= 'a' && c <= 'f' ? c - 'a' + 10 : c >= 'A' && c <= 'F' ? c - 'A' + 10 : -1; }

        // a preset name or "#rrggbb,#rrggbb,..." -> gradient stops
        static int[][] FrameStops(string frame)
        {
            string spec = frame.Trim();
            for (int p = 0; p < FramePresets.Length; p += 2)
                if (string.Equals(spec, FramePresets[p], StringComparison.OrdinalIgnoreCase)) spec = FramePresets[p + 1];
            string[] parts = spec.Split(',');
            int[][] tmp = new int[parts.Length][]; int n = 0;
            foreach (string s0 in parts)
            {
                string s = s0.Trim().TrimStart('#');
                if (s.Length != 6) continue;
                int[] c = new int[3]; bool ok = true;
                for (int k = 0; k < 3; k++) { int hi = Hex(s[2 * k]), lo = Hex(s[2 * k + 1]); if (hi < 0 || lo < 0) ok = false; c[k] = hi * 16 + lo; }
                if (ok) tmp[n++] = c;
            }
            if (n == 0) return new[] { new[] { 200, 200, 200 } };
            int[][] stops = new int[n][];
            for (int k = 0; k < n; k++) stops[k] = tmp[k];
            return stops;
        }

        static string Fg(int[][] stops, double t, bool bold)
        {
            t = Math.Max(0, Math.Min(1, t)) * (stops.Length - 1);
            int i = Math.Min((int)t, stops.Length - 1), j = Math.Min(i + 1, stops.Length - 1); double f = t - i, lift = bold ? 0.35 : 0;   // text: a bit lighter
            var sb = new StringBuilder("\u001b[").Append(bold ? "1;38;2" : "0;38;2");
            for (int k = 0; k < 3; k++) { double v = stops[i][k] + (stops[j][k] - stops[i][k]) * f; sb.Append(";").Append((int)(v + (255 - v) * lift)); }
            return sb.Append("m").ToString();
        }

        // visible cells of one line of art (escape sequences take none; every other char one)
        static int VisibleWidth(string s)
        {
            int n = 0;
            for (int i = 0; i < s.Length; i++)
            {
                if (s[i] == '\u001b' && i + 1 < s.Length && s[i + 1] == '[') { i += 2; while (i < s.Length && (s[i] < '@' || s[i] > '~')) i++; }
                else if (!char.IsLowSurrogate(s[i])) n++;
            }
            return n;
        }

        // one edge: "<l>\u2500 text \u2500\u2500\u2500\u2500 right \u2500<r>", colored along the gradient (t runs 0..1 left to right, offset by row)
        static void Edge(StringBuilder sb, int[][] st, int inner, string l, string r, string left, string right, double t0)
        {
            // the edge as a string of cells, with the text (the left part is bold) at fixed positions
            string lp = left.Length > 0 ? " " + left + " " : "", rp = right.Length > 0 ? " " + right + " " : "";
            string cells = l + "\u2500" + lp + new string('\u2500', Math.Max(0, inner - 2 - lp.Length - rp.Length)) + rp + "\u2500" + r;
            int boldFrom = 3, boldTo = 2 + left.Length;   // left text occupies cells 3 .. 2+len
            string last = null;
            for (int x = 0; x < cells.Length; x++)
            {
                string c = Fg(st, 0.5 * t0 + 0.5 * x / Math.Max(1, cells.Length - 1), left.Length > 0 && x >= boldFrom && x <= boldTo);
                if (c != last) { sb.Append(c); last = c; }
                sb.Append(cells[x]);
            }
            sb.Append("\u001b[0m\r\n");
        }

        // the narrowest inner width an edge with these texts fits in: corner \u2500 [ left ] \u2500\u2026 [ right ] \u2500 corner
        static int EdgeMin(string left, string right)
        {
            return 1 + (left.Length > 0 ? left.Length + 2 : 0) + 1 + (right.Length > 0 ? right.Length + 2 : 0) + 1;
        }

        static string Framed(string raw, int[][] st, string name, string tag, string label, bool shiny)
        {
            var lines = new List<string>(raw.Replace("\r\n", "\n").Split('\n'));
            while (lines.Count > 0 && VisibleWidth(lines[lines.Count - 1]) == 0) lines.RemoveAt(lines.Count - 1);
            string title = (shiny ? "\u2726 " : "") + (name ?? ""), right = tag ?? "", bottom = (label ?? "") + (shiny ? " \u2726 shiny" : "");
            int w = 0; foreach (string l in lines) w = Math.Max(w, VisibleWidth(l));
            // inner width: the art plus a space each side, wide enough for the edge texts
            int inner = Math.Max(w + 2, Math.Max(EdgeMin(title, right), EdgeMin("", bottom)));
            int left = (inner - w) / 2, h = lines.Count;
            var sb = new StringBuilder();
            Edge(sb, st, inner, "\u256d", "\u256e", title, right, 0);
            for (int y = 0; y < h; y++)
            {
                double ty = (y + 1.0) / (h + 1);
                sb.Append(Fg(st, 0.5 * ty, false)).Append('\u2502').Append("\u001b[0m").Append(' ', left).Append(lines[y]).Append("\u001b[0m")
                  .Append(' ', inner - left - VisibleWidth(lines[y])).Append(Fg(st, 0.5 * ty + 0.5, false)).Append('\u2502').Append("\u001b[0m\r\n");
            }
            Edge(sb, st, inner, "\u2570", "\u256f", "", bottom, 1);
            return sb.ToString();
        }

        // ---- frame styles
        // A tier "frame" object in pack.json ({ "style": "wanted", "palette": "manga" }) reaches the core as one
        // string, "wanted;palette=manga;seed=manga-rare" (lib\common.ps1 adds seed = the tier id). A frame whose
        // first ';' field isn't a known style is a preset / gradient-stops frame (Framed above).
        static readonly string[] FrameStyles = { "wanted" };

        /// the style of a frame spec: "wanted", or "" for a preset / gradient-stops frame
        public static string FrameStyle(string frame)
        {
            if (string.IsNullOrEmpty(frame)) return "";
            string s = frame; int i = s.IndexOf(';'); if (i >= 0) s = s.Substring(0, i);
            s = s.Trim();
            foreach (string st in FrameStyles) if (string.Equals(s, st, StringComparison.OrdinalIgnoreCase)) return st;
            return "";
        }

        // "key=value" from a style spec (dflt when missing or empty)
        static string SpecValue(string spec, string key, string dflt)
        {
            foreach (string part in spec.Split(';'))
            {
                int i = part.IndexOf('=');
                if (i > 0 && string.Equals(part.Substring(0, i).Trim(), key, StringComparison.OrdinalIgnoreCase))
                { string v = part.Substring(i + 1).Trim(); if (v.Length > 0) return v; }
            }
            return dflt;
        }

        static int[] Rgb(string s)
        {
            s = (s ?? "").Trim().TrimStart('#');
            var c = new int[3];
            if (s.Length != 6) return c;
            for (int k = 0; k < 3; k++) { int hi = Hex(s[2 * k]), lo = Hex(s[2 * k + 1]); c[k] = hi < 0 || lo < 0 ? 0 : hi * 16 + lo; }
            return c;
        }

        static int[] Mix(int[] a, int[] b, double t)
        {
            var c = new int[3];
            for (int k = 0; k < 3; k++) c[k] = (int)Math.Round(a[k] + (b[k] - a[k]) * t);   // half to even, like Python's round()
            return c;
        }

        static int[] Grad(int[][] stops, double t)
        {
            t = Math.Max(0.0, Math.Min(1.0, t)) * (stops.Length - 1);
            int i = Math.Min((int)t, stops.Length - 1), j = Math.Min(i + 1, stops.Length - 1);
            return Mix(stops[i], stops[j], t - i);
        }

        // Deterministic 0..1 per key: the first 24 bits of md5(key), the style-lab prototype's noise() (keys are
        // Python tuple reprs, so the runtime draws the prototype's exact stains and nibbles). Hand-rolled MD5:
        // the framework's provider would open a CryptoAPI context on the startup path.
        static readonly uint[] Md5K = {
            0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee, 0xf57c0faf, 0x4787c62a, 0xa8304613, 0xfd469501,
            0x698098d8, 0x8b44f7af, 0xffff5bb1, 0x895cd7be, 0x6b901122, 0xfd987193, 0xa679438e, 0x49b40821,
            0xf61e2562, 0xc040b340, 0x265e5a51, 0xe9b6c7aa, 0xd62f105d, 0x02441453, 0xd8a1e681, 0xe7d3fbc8,
            0x21e1cde6, 0xc33707d6, 0xf4d50d87, 0x455a14ed, 0xa9e3e905, 0xfcefa3f8, 0x676f02d9, 0x8d2a4c8a,
            0xfffa3942, 0x8771f681, 0x6d9d6122, 0xfde5380c, 0xa4beea44, 0x4bdecfa9, 0xf6bb4b60, 0xbebfbc70,
            0x289b7ec6, 0xeaa127fa, 0xd4ef3085, 0x04881d05, 0xd9d4d039, 0xe6db99e5, 0x1fa27cf8, 0xc4ac5665,
            0xf4292244, 0x432aff97, 0xab9423a7, 0xfc93a039, 0x655b59c3, 0x8f0ccc92, 0xffeff47d, 0x85845dd1,
            0x6fa87e4f, 0xfe2ce6e0, 0xa3014314, 0x4e0811a1, 0xf7537e82, 0xbd3af235, 0x2ad7d2bb, 0xeb86d391 };
        static readonly int[] Md5R = { 7, 12, 17, 22, 5, 9, 14, 20, 4, 11, 16, 23, 6, 10, 15, 21 };

        static double Noise(string key)
        {
            byte[] msg = Encoding.UTF8.GetBytes(key);
            int n = ((msg.Length + 8) / 64 + 1) * 64;
            var buf = new byte[n];
            Array.Copy(msg, buf, msg.Length);
            buf[msg.Length] = 0x80;
            long bits = (long)msg.Length * 8;
            for (int k = 0; k < 8; k++) buf[n - 8 + k] = (byte)(bits >> (8 * k));
            uint a0 = 0x67452301, b0 = 0xefcdab89, c0 = 0x98badcfe, d0 = 0x10325476;
            var m = new uint[16];
            for (int off = 0; off < n; off += 64)
            {
                for (int k = 0; k < 16; k++)
                    m[k] = (uint)(buf[off + 4 * k] | buf[off + 4 * k + 1] << 8 | buf[off + 4 * k + 2] << 16 | buf[off + 4 * k + 3] << 24);
                uint a = a0, b = b0, c = c0, d = d0;
                for (int i = 0; i < 64; i++)
                {
                    uint f; int g;
                    if (i < 16) { f = (b & c) | (~b & d); g = i; }
                    else if (i < 32) { f = (d & b) | (~d & c); g = (5 * i + 1) % 16; }
                    else if (i < 48) { f = b ^ c ^ d; g = (3 * i + 5) % 16; }
                    else { f = c ^ (b | ~d); g = (7 * i) % 16; }
                    f = f + a + Md5K[i] + m[g];
                    int r = Md5R[(i / 16) * 4 + i % 4];
                    a = d; d = c; c = b; b = b + ((f << r) | (f >> (32 - r)));
                }
                a0 += a; b0 += b; c0 += c; d0 += d;
            }
            // hexdigest()[:6] = the digest's first three bytes = a0's low three bytes, lowest first
            uint v = (a0 & 0xff) << 16 | ((a0 >> 8) & 0xff) << 8 | ((a0 >> 16) & 0xff);
            return v / (double)0xFFFFFF;
        }

        // Python's repr() of a tuple (a[, b[, c]], x, y) of plain strings and ints: the noise keys
        static string Tup(string a, string b, string c, int x, int y)
        {
            var sb = new StringBuilder("('").Append(a).Append('\'');
            if (b != null) sb.Append(", '").Append(b).Append('\'');
            if (c != null) sb.Append(", '").Append(c).Append('\'');
            return sb.Append(", ").Append(x.ToString(CultureInfo.InvariantCulture)).Append(", ").Append(y.ToString(CultureInfo.InvariantCulture)).Append(')').ToString();
        }

        // one row of cells: runs of (fg, bg, bold) as one SGR each, raw ANSI art spliced in (the prototype's Row)
        class CellRow
        {
            readonly StringBuilder sb; string last;
            public CellRow(StringBuilder sb) { this.sb = sb; }
            public void Put(string text, int[] fg, int[] bg, bool bold)
            {
                if (text.Length == 0) return;
                var k = new StringBuilder("\u001b[0");
                if (bold) k.Append(";1");
                if (fg != null) k.Append(";38;2;").Append(fg[0]).Append(';').Append(fg[1]).Append(';').Append(fg[2]);
                if (bg != null) k.Append(";48;2;").Append(bg[0]).Append(';').Append(bg[1]).Append(';').Append(bg[2]);
                string key = k.Append('m').ToString();
                if (key != last) { sb.Append(key); last = key; }
                sb.Append(text);
            }
            public void Raw(string ansi) { sb.Append("\u001b[0m").Append(ansi).Append("\u001b[0m"); last = null; }
            public void End() { sb.Append("\u001b[0m\r\n"); }
        }

        // wanted palettes: name, paper, stain, ink, accent ink (bounty / rarity); "" paper = gold leaf
        static readonly string[] WantedPalettes = {
            "common",      "#e6d3a3", "#cfb57c", "#3b2616", "#3b2616",
            "super-rare",  "#cfa467", "#9c7040", "#2a170a", "#8e1b12",
            "secret-rare", "",        "",        "#3a2408", "#7a1a10",
            "manga",       "#ecebe4", "#c9c8c0", "#111111", "#c8281e",
        };
        static readonly string[] GoldLeaf = { "#c8952e", "#f6dc7a", "#fff3c4", "#e2b24a", "#f8e08a", "#c8952e" };

        class WantedCard
        {
            public string Ch, Seed; public int W, H; public int[] Paper, Stain, Burn; public int[][] Gold; public bool News;

            // the paper color of a frame cell
            public int[] Pap(int x, int y)
            {
                if (Paper == null)   // gold leaf: diagonal shimmer
                {
                    int[] b = Grad(Gold, ((double)x / W * 0.8 + (double)y / H * 0.35) % 1.0);
                    return Noise(Tup("s", null, null, x, y)) > 0.93 ? Mix(b, Burn, 0.35) : b;
                }
                double n = Noise(Tup("p", Ch, null, x, y));
                if (News) return n > 0.9 ? Mix(Paper, Stain, 0.55) : Paper;   // newsprint: faint screentone speckle
                // stains cluster near the edges (aged paper)
                double edge = Math.Min(Math.Min(x, W - 1 - x), Math.Min(y * 2, (H - 1 - y) * 2)) / 6.0;
                double k = Math.Max(0.0, 0.85 - edge) * 0.8 + (n > 0.93 ? 0.35 : 0) + 0.12 * Noise(Tup("q", null, null, x / 3, y));
                return Mix(Paper, Stain, Math.Min(1.0, k));
            }

            // a bite out of the edge here?
            public bool Nib(int x, int y, double prob) { return Noise(Tup("n", Ch, Seed, x, y)) < prob; }
        }

        // A One Piece wanted poster: aged paper all round (background-colored cells) with torn corners, nibbled
        // edges and stains; "W A N T E D" on the top edge, the full name under the art, the bounty (left) and the
        // rarity (right) on the bottom edge. Art height + 3 rows; art + 4 columns (or wider, to fit the texts).
        // Spec keys: palette (common | super-rare | secret-rare | manga), seed (the stain / nibble pattern; the
        // tier id), and paper / stain / ink / accent (#rrggbb overrides of the palette).
        static string Wanted(string raw, string spec, string character, string full, string bounty, string label, bool shiny)
        {
            var lines = new List<string>(raw.Replace("\r\n", "\n").Split('\n'));
            while (lines.Count > 0 && VisibleWidth(lines[lines.Count - 1]) == 0) lines.RemoveAt(lines.Count - 1);
            string pal = SpecValue(spec, "palette", "common").ToLowerInvariant();
            if (pal == "manga-rare") pal = "manga";
            int pi = 0;
            for (int p = 0; p < WantedPalettes.Length; p += 5) if (WantedPalettes[p] == pal) pi = p;
            pal = WantedPalettes[pi];
            string paper = SpecValue(spec, "paper", WantedPalettes[pi + 1]);
            var card = new WantedCard();
            card.Ch = character ?? ""; card.Seed = SpecValue(spec, "seed", pal); card.News = pal == "manga";
            if (paper.Length > 0) card.Paper = Rgb(paper);
            if (paper.Length > 0) card.Stain = Rgb(SpecValue(spec, "stain", WantedPalettes[pi + 2].Length > 0 ? WantedPalettes[pi + 2] : paper));
            else
            {
                card.Gold = new int[GoldLeaf.Length][];
                for (int k = 0; k < GoldLeaf.Length; k++) card.Gold[k] = Rgb(GoldLeaf[k]);
                card.Burn = Rgb("#b07a22");
            }
            int[] ink = Rgb(SpecValue(spec, "ink", WantedPalettes[pi + 3])), acc = Rgb(SpecValue(spec, "accent", WantedPalettes[pi + 4]));
            bool accBold = pal != "common";

            int w = 0; foreach (string l in lines) w = Math.Max(w, VisibleWidth(l));
            int h = lines.Count;
            const string title = "W A N T E D";
            string botL = bounty.Length > 0 ? "\u0e3f " + bounty + "-" : "";
            string botR = label.ToUpperInvariant() + (shiny ? " \u2726" : "");
            int inner = Math.Max(Math.Max(w, full.Length + 2), Math.Max(botL.Length + botR.Length + 1, title.Length + 6));
            int W = inner + 4;
            card.W = W; card.H = h + 3;
            var sb = new StringBuilder();

            // top edge
            var r = new CellRow(sb); int t0 = (W - title.Length) / 2;
            for (int x = 0; x < W; x++)
            {
                if (x == 0) { r.Put("\u2597", card.Pap(x, 0), null, false); continue; }
                if (x == W - 1) { r.Put("\u2596", card.Pap(x, 0), null, false); continue; }
                if (t0 <= x && x < t0 + title.Length) r.Put(title.Substring(x - t0, 1), ink, card.Pap(x, 0), true);
                else if ((x < t0 - 1 || x > t0 + title.Length) && card.Nib(x, 0, 0.13)) r.Put("\u2584", card.Pap(x, 0), null, false);
                else r.Put(" ", null, card.Pap(x, 0), false);
            }
            r.End();
            // art rows: the art centered, a paper band of 2 cells each side
            int left = (inner - w) / 2;
            for (int y = 0; y < h; y++)
            {
                r = new CellRow(sb); int yy = y + 1, vw = VisibleWidth(lines[y]);
                if (card.Nib(0, yy, 0.12)) r.Put("\u2590", card.Pap(0, yy), null, false); else r.Put(" ", null, card.Pap(0, yy), false);
                r.Put(" ", null, card.Pap(1, yy), false);
                r.Put(new string(' ', left), null, null, false);
                r.Raw(lines[y]);
                r.Put(new string(' ', Math.Max(0, inner - left - vw)), null, null, false);
                r.Put(" ", null, card.Pap(W - 2, yy), false);
                if (card.Nib(W - 1, yy, 0.12)) r.Put("\u258c", card.Pap(W - 1, yy), null, false); else r.Put(" ", null, card.Pap(W - 1, yy), false);
                r.End();
            }
            // the full name
            r = new CellRow(sb); int ny = h + 1, n0 = (W - full.Length) / 2;
            for (int x = 0; x < W; x++)
            {
                if (n0 <= x && x < n0 + full.Length) r.Put(full.Substring(x - n0, 1), ink, card.Pap(x, ny), true);
                else r.Put(" ", null, card.Pap(x, ny), false);
            }
            r.End();
            // bottom edge: bounty left, rarity right, torn
            r = new CellRow(sb); int by = h + 2, b0 = 2, r0 = W - 2 - botR.Length;
            for (int x = 0; x < W; x++)
            {
                if (x == 0) { r.Put("\u259d", card.Pap(x, by), null, false); continue; }
                if (x == W - 1) { r.Put("\u2598", card.Pap(x, by), null, false); continue; }
                if (b0 <= x && x < b0 + botL.Length) r.Put(botL.Substring(x - b0, 1), ink, card.Pap(x, by), true);
                else if (r0 <= x && x < r0 + botR.Length) r.Put(botR.Substring(x - r0, 1), acc, card.Pap(x, by), accBold);
                else if (b0 + botL.Length < x && x < r0 - 1 && card.Nib(x, by, 0.16)) r.Put("\u2580", card.Pap(x, by), null, false);
                else r.Put(" ", null, card.Pap(x, by), false);
            }
            r.End();
            return sb.ToString();
        }

        // ---- the earned rule

        public const long ExpireSec = 24 * 3600;   // a pending pull older than this is expired
        public const long BootSlackSec = 120;      // boot ids of one session differ by clock jitter only
        const long UnixEpochTicks = 621355968000000000L;
        const string Crockford = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";

        [System.Runtime.InteropServices.DllImport("kernel32.dll")] static extern ulong GetTickCount64();

        /// This boot session: the unix time (seconds) the machine last booted. Pulls from another session expire.
        public static long BootId()
        {
            try { return (DateTime.UtcNow.Ticks - UnixEpochTicks) / Tps - (long)(GetTickCount64() / 1000UL); }
            catch (Exception) { return 0; }
        }

        /// A new pull id: a ULID (48-bit unix ms + 80 random bits, Crockford base32, 26 chars, sorts by time).
        public static string NewPullId(long utcTicks)
        {
            long ms = Math.Max(0, (utcTicks - UnixEpochTicks) / 10000L);
            byte[] r = Guid.NewGuid().ToByteArray();
            var c = new char[26];
            for (int i = 9; i >= 0; i--) { c[i] = Crockford[(int)(ms & 31)]; ms >>= 5; }
            int bit = 0;
            for (int i = 10; i < 26; i++)
            {
                int v = 0;
                for (int b = 0; b < 5; b++, bit++) v = (v << 1) | ((r[bit >> 3] >> (7 - (bit & 7))) & 1);
                c[i] = Crockford[v];
            }
            return new string(c);
        }

        /// UTC ticks encoded in a pull id (0 if it isn't a ULID)
        public static long PullIdTicks(string id)
        {
            if (id == null || id.Length != 26) return 0;
            long ms = 0;
            for (int i = 0; i < 10; i++)
            {
                int v = Crockford.IndexOf(char.ToUpperInvariant(id[i]));
                if (v < 0) return 0;
                ms = ms * 32 + v;
            }
            return UnixEpochTicks + ms * 10000L;
        }

        /// head = the first 8 columns (the flags column may already hold a note); adds the extra note, the pending
        /// flag (unless the rule is off) and the id / boot columns
        public static string FinishLine(string head, string extra, Pull p)
        {
            var sb = new StringBuilder(head ?? "");
            bool empty = sb.Length == 0 || sb[sb.Length - 1] == '\t';
            if (!string.IsNullOrEmpty(extra)) { if (!empty) sb.Append(','); sb.Append(extra); empty = false; }
            if (p == null || string.IsNullOrEmpty(p.Id)) return sb.ToString();
            if (EarnMode(p.Earn) != "off") { if (!empty) sb.Append(','); sb.Append("pending"); }
            return sb.Append("\tid=").Append(p.Id).Append("\tboot=").Append(p.Boot.ToString(CultureInfo.InvariantCulture)).ToString();
        }

        /// the use rule, normalized: first-command (default) | minutes:N | off
        public static string EarnMode(string v)
        {
            v = (v ?? "").Trim().ToLowerInvariant();
            if (v == "off" || v == "0" || v == "none") return "off";
            if (v.StartsWith("minutes:"))
            {
                double m;
                if (double.TryParse(v.Substring(8), NumberStyles.Float, CultureInfo.InvariantCulture, out m) && m >= 0) return "minutes:" + m.ToString(CultureInfo.InvariantCulture);
            }
            return "first-command";
        }

        /// Is a pending pull earned yet? commands = how many commands this tab has run. "earn" | "wait" | "expired".
        public static string EarnCheck(string mode, long commands, long pullUtcTicks, long nowUtcTicks)
        {
            if (pullUtcTicks > 0 && nowUtcTicks - pullUtcTicks > ExpireSec * Tps) return "expired";
            mode = EarnMode(mode);
            if (mode == "off") return "earn";
            if (mode.StartsWith("minutes:"))
            {
                double m = double.Parse(mode.Substring(8), CultureInfo.InvariantCulture);
                return nowUtcTicks - pullUtcTicks >= (long)(m * 60 * Tps) ? "earn" : "wait";
            }
            return commands > 0 ? "earn" : "wait";
        }

        static string LocalStamp(long utcTicks) { return new DateTime(utcTicks, DateTimeKind.Utc).ToLocalTime().ToString("s", CultureInfo.InvariantCulture); }

        /// the event line that earns (or expires) a pull
        public static string EventLine(string what, string id, long utcTicks) { return LocalStamp(utcTicks) + "\t" + what + ":" + id; }

        /// Every pull in pulls.log with the earned rule applied (dry runs left out, expired ones included with
        /// Status "expired"). viewed.txt (ids the binder has shown) clears New.
        public static PullRecord[] ReadPulls(string stateDir, long nowUtcTicks, long bootNow)
        {
            var list = new List<PullRecord>();
            string log = Path.Combine(stateDir, "pulls.log");
            if (!File.Exists(log)) return list.ToArray();
            string[] lines;
            try { lines = File.ReadAllLines(log, Encoding.UTF8); } catch (IOException) { return list.ToArray(); }
            var earned = new Dictionary<string, bool>(StringComparer.Ordinal);
            var expired = new Dictionary<string, bool>(StringComparer.Ordinal);
            foreach (string line in lines)
            {
                string[] f = line.Split('\t');
                if (f.Length < 2 || f.Length >= 7) continue;
                string ev = f[1].Trim();
                if (ev.StartsWith("earned:")) earned[ev.Substring(7)] = true;
                else if (ev.StartsWith("expired:")) expired[ev.Substring(8)] = true;
            }
            var viewed = new Dictionary<string, bool>(StringComparer.Ordinal);
            string vf = Path.Combine(stateDir, "viewed.txt");
            if (File.Exists(vf)) try { foreach (string v in File.ReadAllLines(vf)) if (v.Trim().Length > 0) viewed[v.Trim()] = true; } catch (IOException) { }
            foreach (string line in lines)
            {
                string[] f = line.Split('\t');
                if (f.Length < 7) continue;
                var r = new PullRecord { Time = f[0], Pack = f[1], Character = f[2], Tier = f[3], Art = f[4], Skin = f[5], Shiny = f[6].Trim() == "1" };
                r.Flags = f.Length > 7 ? f[7].Trim() : "";
                if (r.Flags.Contains("dryrun")) continue;
                for (int i = 8; i < f.Length; i++)
                {
                    int eq = f[i].IndexOf('=');
                    if (eq <= 0) continue;
                    string k = f[i].Substring(0, eq).Trim(), v = f[i].Substring(eq + 1).Trim();
                    long b;
                    if (k == "id") r.Id = v;
                    else if (k == "boot" && long.TryParse(v, NumberStyles.Integer, CultureInfo.InvariantCulture, out b)) r.Boot = b;
                    else if (k == "card") r.Card = v;
                }
                bool pending = false;
                foreach (string fl in r.Flags.Split(',')) if (fl.Trim() == "pending") pending = true;
                if (r.Id.Length == 0 || !pending || earned.ContainsKey(r.Id)) r.Status = "earned";
                else if (expired.ContainsKey(r.Id)) r.Status = "expired";
                else
                {
                    long t = PullIdTicks(r.Id);
                    bool old = t > 0 && nowUtcTicks - t > ExpireSec * Tps;
                    bool otherBoot = r.Boot != 0 && bootNow != 0 && Math.Abs(r.Boot - bootNow) > BootSlackSec;
                    r.Status = old || otherBoot ? "expired" : "pending";
                    r.Derived = r.Status == "expired";
                }
                r.New = r.Status == "earned" && r.Id.Length > 0 && !viewed.ContainsKey(r.Id);
                list.Add(r);
            }
            return list.ToArray();
        }

        /// The small footer printed under a pulled card: "binder \u23ce", an OSC 8 link to pokeshell://binder?pull=<id>
        /// (the art itself is left unlinked: Windows Terminal underlines link text). Right-aligned to the card.
        public static string WithFooter(string text, string id)
        {
            if (string.IsNullOrEmpty(id) || string.IsNullOrEmpty(text)) return text;
            int e = text.Length;
            while (e > 0 && (text[e - 1] == '\n' || text[e - 1] == '\r')) e--;
            string body = text.Substring(0, e), tail = text.Substring(e);
            int w = 0;
            foreach (string l in body.Split('\n')) w = Math.Max(w, VisibleWidth(l.TrimEnd('\r')));
            const string hint = "binder \u23ce";
            string url = "pokeshell://binder?pull=" + id;
            string link = "\u001b]8;;" + url + "\u001b\\" + hint + "\u001b]8;;\u001b\\";
            return body + "\r\n" + new string(' ', Math.Max(2, w - hint.Length - 1)) + "\u001b[2;38;2;140;140;150m" + link + "\u001b[0m" + (tail.Length > 0 ? tail : "\r\n");
        }

        public static void Log(string stateDir, string file, string line)
        {
            try { Directory.CreateDirectory(stateDir); File.AppendAllText(Path.Combine(stateDir, file), line + "\r\n"); }
            catch (Exception) { }
        }

        class PackRows
        {
            public string Id; public double Foil, Shiny; public List<string[]> Chars = new List<string[]>(), Tiers = new List<string[]>(), Skins = new List<string[]>(); public int Weight;
            public List<string[]> Cards = new List<string[]>(), Odds = new List<string[]>();   // real-card packs (card mode, below)
        }

        // roll.tsv rows, or null when it's missing/stale (line 1 stamps its inputs' mtimes; line 2 the pack selection)
        static List<PackRows> ReadCache(string stateDir, string selection)
        {
            string cache = Path.Combine(stateDir, "roll.tsv");
            if (!File.Exists(cache)) return null;
            string[] lines = File.ReadAllLines(cache);
            if (lines.Length < 2 || !lines[0].StartsWith("stamp\t") || lines[1] != "select\t" + selection) return null;
            foreach (string s in lines[0].Split('\t'))
            {
                int bar = s.LastIndexOf('|'); long want;
                if (bar <= 0) continue;
                if (!long.TryParse(s.Substring(bar + 1), out want) || File.GetLastWriteTimeUtc(s.Substring(0, bar)).Ticks != want) return null;
            }
            var packs = new List<PackRows>(); PackRows p = null;
            foreach (string line in lines)
            {
                string[] f = line.Split('\t');
                if (f[0] == "pack" && f.Length >= 4)
                {
                    p = new PackRows { Id = f[1], Foil = double.Parse(f[2], CultureInfo.InvariantCulture), Shiny = double.Parse(f[3], CultureInfo.InvariantCulture) };
                    packs.Add(p);
                }
                else if (p == null) continue;
                else if (f[0] == "char" && f.Length >= 3) p.Chars.Add(f);                                   // char id name [tag [poster bounty]]
                else if (f[0] == "tier" && f.Length >= 4) p.Tiers.Add(f);                                   // tier id label art [frame]
                else if (f[0] == "skin" && f.Length >= 5) { p.Skins.Add(f); p.Weight += int.Parse(f[2]); }  // skin name weight tier guid
                else if (f[0] == "card" && f.Length >= 5) p.Cards.Add(f);                                   // card tier character name cardid [tag]
                else if (f[0] == "odds" && f.Length >= 3) p.Odds.Add(f);                                    // odds tier weight
            }
            return packs;
        }

        // ---- card mode: a real-card pack (pack.json "cards"; the roll.tsv card / odds rows, see lib\common.ps1)
        // A tier is rolled by its odds weight among the tiers that have cards (an empty tier never rolls: its odds
        // spread over the others, as if rerolled), then one of that tier's cards uniformly, then a skin of that tier
        // (weighted; a tier with no installed skin prints in the plain tab, no spawn). A forced foilChance >= 0 (tests,
        // measurements) first decides skinned or not, then rolls among the tiers on that side (one side empty: all).
        static bool TierHasSkin(PackRows p, string tier)
        {
            foreach (string[] s in p.Skins) if (s[3] == tier) return true;
            return false;
        }

        static string[] RollCard(PackRows p, Random rng, double foilChance, out int tier, out string[] skin)
        {
            int total = 0, foilW = 0;
            foreach (string[] o in p.Odds) { int w = int.Parse(o[2]); total += w; if (TierHasSkin(p, o[1])) foilW += w; }
            int side = -1;   // -1 any tier, 1 skinned tiers only, 0 plain tiers only
            if (foilChance >= 0) { side = rng.NextDouble() < foilChance ? 1 : 0; if ((side == 1 ? foilW : total - foilW) <= 0) side = -1; }
            int pick = rng.Next(Math.Max(1, side < 0 ? total : side == 1 ? foilW : total - foilW));
            string tid = p.Odds[0][1];
            foreach (string[] o in p.Odds)
            {
                if (side >= 0 && TierHasSkin(p, o[1]) != (side == 1)) continue;
                pick -= int.Parse(o[2]); if (pick < 0) { tid = o[1]; break; }
            }
            tier = int.Parse(tid);
            skin = null; int sw = 0;
            foreach (string[] s in p.Skins) if (s[3] == tid) sw += int.Parse(s[2]);
            if (sw > 0)
            {
                int k = rng.Next(sw);
                foreach (string[] s in p.Skins) if (s[3] == tid) { k -= int.Parse(s[2]); if (k < 0) { skin = s; break; } }
            }
            int n = 0; foreach (string[] c in p.Cards) if (c[1] == tid) n++;
            int j = rng.Next(Math.Max(1, n));
            foreach (string[] c in p.Cards) if (c[1] == tid && j-- == 0) return c;
            return p.Cards[0];
        }

        /// the card a denied / unplaced foil shows instead: the same character's card in its lowest tier (else the
        /// pack's lowest-tier card), as a legacy pack falls back to tier 0
        static string[] LowestCard(PackRows p, string[] card)
        {
            // the same character at the pack's lowest tier; else any lowest-tier card (a character with only foil cards
            // must not fall back to its own foil card shown without its shader)
            string[] best = null, any = null;
            foreach (string[] c in p.Cards)
                if (any == null || int.Parse(c[1]) < int.Parse(any[1])) any = c;
            foreach (string[] c in p.Cards)
                if (c[2] == card[2] && c[1] == any[1]) { best = c; break; }
            return best ?? any;
        }

        // a card row (card tier character name cardid [tag]) as a char row (char character name tag)
        static string[] CardChar(string[] c) { return new[] { "char", c[2], c[3], c.Length > 5 ? c[5] : "" }; }

        /// What the $PROFILE hook calls: Roll with the real clock and fresh dice (fewer PowerShell call sites).
        public static Pull Startup(string root, string stateDir, string profileId, string[] argv, string libDir, double foilChance)
        {
            return Roll(root, stateDir, profileId, argv, DateTime.UtcNow.Ticks, Guid.NewGuid().GetHashCode(), foilChance, null, null, libDir);
        }

        /// The same, given the hook's $ExecutionContext: a pull shown in this tab (common, or a foil the gate denied)
        /// also starts the earned rule's hook (Earn), in the same call.
        public static Pull Startup(System.Management.Automation.EngineIntrinsics engine, string root, string stateDir, string profileId,
                                   string[] argv, string libDir, double foilChance)
        {
            Pull r = Startup(root, stateDir, profileId, argv, libDir, foilChance);
            if (r.Action == "common" || r.Action == "foil-denied") Earn.Register(engine, r, stateDir);
            return r;
        }
        [System.Runtime.InteropServices.DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();

        /// The foreground window: Windows Terminal's `-w 0` targets the most recently used window, which is
        /// this tab's window only when that window is in the foreground (checked before a foil replaces the tab).
        public static IntPtr ForegroundWindow() { return GetForegroundWindow(); }
        static string Quote(string s) { return "'" + (s ?? "").Replace("'", "''") + "'"; }

        /// The startup pull. foilChance < 0 uses the pack's odds. exe/cwd (null: this process / its current folder)
        /// and libDir (where roll.ps1 lives) describe the new tab to open.
        /// Returns Action "stale" (nothing rolled, no marker set) when roll.tsv must be rebuilt first.
        public static Pull Roll(string root, string stateDir, string profileId, string[] argv, long now, int seed,
                                double foilChance, string exe, string cwd, string libDir)
        {
            var res = new Pull();
            var cfg = ReadConfig(stateDir);
            res.Reason = SkipReason(profileId, argv, cfg);
            if (res.Reason != "") return res;
            var packs = ReadCache(stateDir, cfg["pack"]);
            if (packs == null) { res.Action = "stale"; return res; }
            Environment.SetEnvironmentVariable("POKESHELL_ROLLED", "1");   // layer 3: nothing started from here rolls again
            Environment.SetEnvironmentVariable(SharedMarker, "1");        // ... and no other cardshell hook (opshell) rolls this tab
            if (packs.Count == 0) { res.Reason = "no-packs"; return res; }

            var rng = new Random(seed);
            PackRows p = packs[rng.Next(packs.Count)];
            bool cards = p.Cards.Count > 0 && p.Odds.Count > 0;   // a real-card pack (card mode)
            if ((p.Chars.Count == 0 && !cards) || p.Tiers.Count == 0) { res.Reason = "empty-pack"; return res; }
            int tier = 0; string[] skin = null, card = null;
            if (cards) card = RollCard(p, rng, foilChance, out tier, out skin);
            else if (foilChance < 0) foilChance = p.Foil;
            if (!cards && p.Weight > 0 && rng.NextDouble() < foilChance)
            {
                int pick = rng.Next(p.Weight);
                foreach (string[] s in p.Skins) { pick -= int.Parse(s[2]); if (pick < 0) { skin = s; break; } }
                tier = int.Parse(skin[3]);
                if (tier < 0 || tier >= p.Tiers.Count) { skin = null; tier = 0; }
            }
            string[] ch = card != null ? CardChar(card) : p.Chars[rng.Next(p.Chars.Count)];
            bool shiny = rng.NextDouble() < p.Shiny;
            string note = "";
            if (skin != null)
            {
                string gate = EnterSpawnGate(stateDir, now);   // layer 4
                if (gate != "ok") { note = "denied:" + gate; res.Action = "foil-denied"; tier = 0; skin = null; }
                if (gate != "ok" && card != null) { card = LowestCard(p, card); tier = int.Parse(card[1]); ch = CardChar(card); }
            }
            string[] t = p.Tiers[tier];
            string art = card != null ? card[4] : t[3];   // a real card is its own art: dist\<pack>\<character>-<card id>.ans, logged in the art column
            res.Pack = p.Id; res.Character = ch[1]; res.Name = ch[2]; res.Tier = tier; res.TierId = t[1]; res.Label = t[2]; res.Art = art; res.Shiny = shiny;
            if (skin != null) { res.Skin = skin[1]; res.Guid = skin[4]; }
            res.Frame = t.Length > 4 ? t[4] : ""; res.Tag = ch.Length > 3 ? ch[3] : ""; res.Display = Display(cfg);
            res.Poster = ch.Length > 4 ? ch[4] : ""; res.Bounty = ch.Length > 5 ? ch[5] : "";
            bool picture = res.Display == "picture";
            // the earned rule: the pull's id (the tab carries it as POKESHELL_PULL), logged pending until the tab is used
            string earn; cfg.TryGetValue("earn", out earn);
            res.Earn = EarnMode(earn); res.PullTicks = now; res.Id = NewPullId(now); res.Boot = BootId();
            Environment.SetEnvironmentVariable("POKESHELL_PULL", res.Id);   // layer 3 as well: set in every tab that rolled

            res.LogLine = new DateTime(now, DateTimeKind.Utc).ToLocalTime().ToString("s", CultureInfo.InvariantCulture) + "\t" + p.Id + "\t" + ch[1] + "\t" +
                          t[1] + "\t" + art + "\t" + res.Skin + "\t" + (shiny ? "1" : "0") + "\t" + note;

            if (skin == null)
            {
                if (res.Action != "foil-denied") res.Action = "common";
                res.Text = PullText(root, p.Id, ch[1], ch[2], art, t[2], tier, shiny, res.Frame, res.Tag, picture, res.Poster, res.Bounty);
                Log(stateDir, "pulls.log", res.LogLine);
                return res;
            }

            // foil: PowerShell opens this skinned tab (same folder) and closes the current one
            res.Action = "foil";
            if (string.IsNullOrEmpty(exe))   // the shell running this: powershell.exe or pwsh.exe
                try { exe = System.Diagnostics.Process.GetCurrentProcess().MainModule.FileName; } catch (Exception) { exe = "powershell.exe"; }
            if (string.IsNullOrEmpty(cwd)) cwd = Environment.CurrentDirectory;   // at profile time = the tab's folder   // layer 3: inherited if WT passes our environment on
            string[] t0 = p.Tiers[0], ch0 = ch; string art0 = t0[3]; int tier0 = 0;   // shown here if the foil can't open
            if (card != null) { string[] low = LowestCard(p, card); tier0 = int.Parse(low[1]); t0 = p.Tiers[tier0]; ch0 = CardChar(low); art0 = low[4]; }
            res.FallbackText = PullText(root, p.Id, ch0[1], ch0[2], art0, t0[2], tier0, shiny, t0.Length > 4 ? t0[4] : "", ch0.Length > 3 ? ch0[3] : "", picture, res.Poster, res.Bounty);
            res.FallbackLogLine = new DateTime(now, DateTimeKind.Utc).ToLocalTime().ToString("s", CultureInfo.InvariantCulture) + "\t" + p.Id + "\t" + ch0[1] + "\t" +
                                  t0[1] + "\t" + art0 + "\t\t" + (shiny ? "1" : "0") + "\t";
            string cmd = "$env:POKESHELL_PULL=" + Quote(res.Id) + "; $env:POKESHELL_ROLLED='1'; $env:" + SharedMarker + "='1'; . " + Quote(Path.Combine(libDir, "roll.ps1")) +
                         "; Show-PokeshellPull -Root " + Quote(root) + " -Pack " + Quote(p.Id) + " -Character " + Quote(ch[1]) +
                         " -Name " + Quote(ch[2]) + " -Art " + Quote(art) +" -Label " + Quote(t[2]) + " -Tier " + tier + (shiny ? " -Shiny" : "") +
                         (res.Frame != "" ? " -Frame " + Quote(res.Frame) : "") + (res.Tag != "" ? " -Tag " + Quote(res.Tag) : "") +
                         (res.Poster != "" ? " -Poster " + Quote(res.Poster) : "") + (res.Bounty != "" ? " -Bounty " + Quote(res.Bounty) : "") +
                         " -PullId " + Quote(res.Id) + " -Earn " + Quote(res.Earn) + " -PullTicks " + now.ToString(CultureInfo.InvariantCulture) + " -StateDir " + Quote(stateDir) +
                         (picture ? " -Picture" : "");   // the pulled tab prints the same way, and earns its pull
            string enc = Convert.ToBase64String(Encoding.Unicode.GetBytes(cmd));
            // wt.exe treats ';' as its own command separator, so escape it; base64 never contains one
            res.WtArgs = new[] { "-w", "0", "nt", "-p", res.Guid, "-d", cwd.Replace(";", "\\;"), exe, "-NoLogo", "-NoExit", "-EncodedCommand", enc };
            return res;
        }
    }
}
