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
//   3 markers   POKESHELL_PULL / POKESHELL_ROLLED in the environment
//   4 gate      machine-wide lock file: one spawn per 3 s; a 6th spawn inside 60 s trips a 10-minute breaker
//   5 install   only skins recorded by `pokeshell install` can drop; nothing installed means no spawns
//   6 kill      `pokeshell off` (enabled=0) or POKESHELL_DISABLE=1
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
        public int Tier;
        public bool Shiny;
        public string Text = "";          // art + banner to print (common / denied pulls)
        public string FallbackText = "";  // what to print if opening the foil tab fails
        public string LogLine = "";
        public string FallbackLogLine = "";  // the log line if the foil ends up shown here as a common (note appended)
        public string[] WtArgs;
    }

    public static class Core
    {
        public const string DefaultPlainProfiles =
            "{61c54bbd-c2c6-5271-96e7-009a87ff44bf},{574e775e-4f2a-5b96-ac1e-a2962a402336}";
        public const int MinGapSec = 3, WindowSec = 60, Burst = 5, TripSec = 600;
        const long Tps = 10000000L;

        public static Dictionary<string, string> ReadConfig(string stateDir)
        {
            var cfg = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            cfg["pack"] = "pokemon"; cfg["enabled"] = "1"; cfg["plain_profiles"] = DefaultPlainProfiles;
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

        // "" when this shell may roll, otherwise why not (layers 1-3 and 6)
        public static string SkipReason(string profileId, string[] argv, Dictionary<string, string> cfg)
        {
            if (Env("POKESHELL_PULL")) return "marker:POKESHELL_PULL";
            if (Env("POKESHELL_ROLLED")) return "marker:POKESHELL_ROLLED";
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
            string b = Path.Combine(Path.Combine(Path.Combine(root, "dist"), pack), character + "-");
            string file = b + art + "-shiny.ans";
            if (!shiny || !File.Exists(file)) file = b + art + ".ans";
            if (!File.Exists(file)) file = b + "common.ans";
            string img = File.Exists(file) ? File.ReadAllText(file, Encoding.UTF8).Replace("\r\n", "\n").Replace("\n", "\r\n") : "";
            string[] colors = { "38;2;150;150;150", "38;2;185;215;235", "38;2;110;165;255", "38;2;225;120;230", "38;2;240;200;80" };
            string c = colors[Math.Min(Math.Max(tier, 0), colors.Length - 1)];
            const string e = "\u001b";
            return "\r\n" + img + "  " + e + "[1;" + c + "m" + label + e + "[0;" + c + "m : " + name + (shiny ? " (shiny)" : "") + e + "[0m\r\n\r\n";
        }

        public static void Log(string stateDir, string file, string line)
        {
            try { Directory.CreateDirectory(stateDir); File.AppendAllText(Path.Combine(stateDir, file), line + "\r\n"); }
            catch (Exception) { }
        }

        class PackRows { public string Id; public double Foil, Shiny; public List<string[]> Chars = new List<string[]>(), Tiers = new List<string[]>(), Skins = new List<string[]>(); public int Weight; }

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
                else if (f[0] == "char" && f.Length >= 3) p.Chars.Add(f);                                   // char id name
                else if (f[0] == "tier" && f.Length >= 4) p.Tiers.Add(f);                                   // tier id label art
                else if (f[0] == "skin" && f.Length >= 5) { p.Skins.Add(f); p.Weight += int.Parse(f[2]); }  // skin name weight tier guid
            }
            return packs;
        }

        /// What the $PROFILE hook calls: Roll with the real clock and fresh dice (fewer PowerShell call sites).
        public static Pull Startup(string root, string stateDir, string profileId, string[] argv, string libDir, double foilChance)
        {
            return Roll(root, stateDir, profileId, argv, DateTime.UtcNow.Ticks, Guid.NewGuid().GetHashCode(), foilChance, null, null, libDir);
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
            if (packs.Count == 0) { res.Reason = "no-packs"; return res; }

            var rng = new Random(seed);
            PackRows p = packs[rng.Next(packs.Count)];
            if (p.Chars.Count == 0 || p.Tiers.Count == 0) { res.Reason = "empty-pack"; return res; }
            if (foilChance < 0) foilChance = p.Foil;
            int tier = 0; string[] skin = null;
            if (p.Weight > 0 && rng.NextDouble() < foilChance)
            {
                int pick = rng.Next(p.Weight);
                foreach (string[] s in p.Skins) { pick -= int.Parse(s[2]); if (pick < 0) { skin = s; break; } }
                tier = int.Parse(skin[3]);
                if (tier < 0 || tier >= p.Tiers.Count) { skin = null; tier = 0; }
            }
            string[] ch = p.Chars[rng.Next(p.Chars.Count)];
            bool shiny = rng.NextDouble() < p.Shiny;
            string note = "";
            if (skin != null)
            {
                string gate = EnterSpawnGate(stateDir, now);   // layer 4
                if (gate != "ok") { note = "denied:" + gate; res.Action = "foil-denied"; tier = 0; skin = null; }
            }
            string[] t = p.Tiers[tier];
            res.Pack = p.Id; res.Character = ch[1]; res.Name = ch[2]; res.Tier = tier; res.TierId = t[1]; res.Label = t[2]; res.Art = t[3]; res.Shiny = shiny;
            if (skin != null) { res.Skin = skin[1]; res.Guid = skin[4]; }
            res.LogLine = new DateTime(now, DateTimeKind.Utc).ToLocalTime().ToString("s", CultureInfo.InvariantCulture) + "\t" + p.Id + "\t" + ch[1] + "\t" +
                          t[1] + "\t" + t[3] + "\t" + res.Skin + "\t" + (shiny ? "1" : "0") + "\t" + note;

            if (skin == null)
            {
                if (res.Action != "foil-denied") res.Action = "common";
                res.Text = PullText(root, p.Id, ch[1], ch[2], t[3], t[2], tier, shiny);
                Log(stateDir, "pulls.log", res.LogLine);
                return res;
            }

            // foil: PowerShell opens this skinned tab (same folder) and closes the current one
            res.Action = "foil";
            Environment.SetEnvironmentVariable("POKESHELL_PULL", "1");
            if (string.IsNullOrEmpty(exe))   // the shell running this: powershell.exe or pwsh.exe
                try { exe = System.Diagnostics.Process.GetCurrentProcess().MainModule.FileName; } catch (Exception) { exe = "powershell.exe"; }
            if (string.IsNullOrEmpty(cwd)) cwd = Environment.CurrentDirectory;   // at profile time = the tab's folder   // layer 3: inherited if WT passes our environment on
            string[] t0 = p.Tiers[0];
            res.FallbackText = PullText(root, p.Id, ch[1], ch[2], t0[3], t0[2], 0, shiny);
            res.FallbackLogLine = new DateTime(now, DateTimeKind.Utc).ToLocalTime().ToString("s", CultureInfo.InvariantCulture) + "\t" + p.Id + "\t" + ch[1] + "\t" +
                                  t0[1] + "\t" + t0[3] + "\t\t" + (shiny ? "1" : "0") + "\t";
            string cmd = "$env:POKESHELL_PULL='1'; $env:POKESHELL_ROLLED='1'; . " + Quote(Path.Combine(libDir, "roll.ps1")) +
                         "; Show-PokeshellPull -Root " + Quote(root) + " -Pack " + Quote(p.Id) + " -Character " + Quote(ch[1]) +
                         " -Name " + Quote(ch[2]) + " -Art " + Quote(t[3]) + " -Label " + Quote(t[2]) + " -Tier " + tier + (shiny ? " -Shiny" : "");
            string enc = Convert.ToBase64String(Encoding.Unicode.GetBytes(cmd));
            // wt.exe treats ';' as its own command separator, so escape it; base64 never contains one
            res.WtArgs = new[] { "-w", "0", "nt", "-p", res.Guid, "-d", cwd.Replace(";", "\\;"), exe, "-NoLogo", "-NoExit", "-EncodedCommand", enc };
            return res;
        }
    }
}
