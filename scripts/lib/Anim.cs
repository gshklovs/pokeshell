// pokeshell card animation: plays a card's approved effect loop (dist\<pack>\<character>-<card id>[-shiny].anim)
// over the rows of the card that was just printed, until a key is pressed (or once, or not at all: config
// `anim=untilkey|intro|off`, POKESHELL_NO_ANIM=1).
//
// Kept apart from Pokeshell.cs (the roll core) and compiled into its own DLL,
// %LOCALAPPDATA%\pokeshell\pokeshell-anim-<Anim.cs mtime>-<edition>.dll, by lib\anim.ps1. Only a tab whose
// card has an .anim loads it; commons never do. C# 5 only (the .NET Framework compiler of Windows PowerShell).
//
// How it plays
//   - The card is printed first, as always (instant); the animation then redraws only the art rows of that
//     printed text, in place: relative cursor moves up from the prompt line (CUU/CUD/CHA), never a newline,
//     so nothing scrolls. Rows that scrolled out of a short window are skipped (clipped), not reached.
//   - Where the art sits inside the printed card (frame, banner, picture, wanted poster) is found by matching the
//     static .ans's lines in the printed text, so the player never re-implements the card layouts; any mismatch
//     (or a card wider than the window, which wrapped) means no animation, just the static card.
//   - Stop: the first key press (the key is NOT consumed: it stays in the console input buffer and PSReadLine
//     reads it as the first character at the prompt), Ctrl+C, the 30 s cap, the end of the intro loop, or a
//     window resize. Every stop but a resize that wrapped the card redraws the final frame, which is the
//     static .ans, so the card ends exactly as printed; the cursor is hidden while playing and shown after.
//   - Timing: the printed card is the loop's final frame, so the loop starts at the print: the next frame is due
//     83 ms (one period at 12 fps) after it, and the player's setup (~20-30 ms) hides inside that period.
//   - Idle: between frames the thread blocks on the console input handle (WaitForSingleObject), so a key stops
//     it at once and nothing polls.
// .anim format (style-lab/anim/build_anim.py): a JSON header line {"lines", "fps", "frames", "final"}, then each
// frame after a form feed (\f): full truecolor half-block rows, '\n' separated. Frames are read as they are
// needed (streamed), so the first one is on screen before the rest of the ~1 MB bundle is read.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

namespace Pokeshell
{
    /// The console the player draws on: the real one (AnimConsole) or a test fake.
    public interface IAnimConsole
    {
        int Width { get; }
        int Height { get; }
        int Row { get; }            // cursor row inside the visible window, 0 = top
        int Col { get; }
        long Ms { get; }            // monotonic milliseconds
        bool Cancelled { get; }     // Ctrl+C / Ctrl+Break during playback
        void Write(string s);
        bool KeyAvailable();        // a key press is waiting; must NOT consume it
        void Wait(int ms);          // sleep up to ms, returning early when input arrives
    }

    public class AnimResult
    {
        public string Status = "static";   // static | played
        public string Reason = "";         // static: why
        public string Stop = "";           // played: key | cap | intro | resize | cancel | mismatch | error:<message>
        public string Mode = "", Bundle = "";
        public int Frames;                 // frames drawn before the stop (the final redraw not counted)
        public long FirstFrameMs = -1, TotalMs, ReadyMs = -1;   // ms after the card was printed: first frame drawn, stop, first frame ready to draw
        public long FirstFrameStamp;      // Stopwatch.GetTimestamp() when the first frame was written (startup measurements)
        public string Timing = "";        // ms into Run when each startup step was done (stats)
        public int ArtRows, VisibleRows, Col;
        public bool FinalRestored;
        public List<int> FrameMs = new List<int>();        // when each frame was written (ms after the card was printed)
        public List<int> FrameIndex = new List<int>();     // which bundle frame it was
        public override string ToString()
        {
            if (Status != "played") return "static\t" + Reason + "\t" + Bundle;
            return "played\t" + Mode + "\tstop=" + Stop + "\tframes=" + Frames + "\tfirst=" + FirstFrameMs + "ms\ttotal=" + TotalMs +
                   "ms\trows=" + VisibleRows + "/" + ArtRows + "\tcol=" + Col + "\tfinal=" + (FinalRestored ? "1" : "0") + "\t" + Bundle + "\t" + Timing;
        }
    }

    /// Where the art rows are in the printed card text, relative to the cursor that printing left behind.
    public class AnimLayout
    {
        public string[] Static;   // the art rows as printed (= the .anim's final frame)
        public int[] Dist;        // lines above the cursor line, per art row
        public int[] Width;       // visible width of each static row
        public int Col;           // the art's column (0-based)
        public int MaxArtWidth;   // widest static row: a frame row may not be wider (it would hit the card's border)
        public int MaxLineWidth;  // widest printed line: the window must be wider, or the card wrapped
    }

    public static class Anim
    {
        public const double CapSeconds = 30;

        // ---- which bundle, which mode

        /// The .anim to play for a printed card and the static .ans it ends on (both "" when none). Mirrors
        /// Core.PullText's choice of art: the shiny art when it exists, else the regular art; a shiny card whose
        /// shiny .ans exists but has no shiny .anim does not animate (the regular loop would end on the wrong art).
        public static string[] Find(string root, string pack, string character, string art, bool shiny)
        {
            string b = Path.Combine(Path.Combine(Path.Combine(root, "dist"), pack), character + "-" + art);
            string ans = b + ".ans", anim = b + ".anim";
            if (shiny && File.Exists(b + "-shiny.ans")) { ans = b + "-shiny.ans"; anim = b + "-shiny.anim"; }
            if (!File.Exists(ans) || !File.Exists(anim)) return new[] { "", "" };
            return new[] { anim, ans };
        }

        /// untilkey (default) | intro | off. POKESHELL_NO_ANIM (any value but 0) forces off; else config.txt `anim`.
        public static string Mode(string stateDir)
        {
            string e = Environment.GetEnvironmentVariable("POKESHELL_NO_ANIM");
            if (!string.IsNullOrEmpty(e) && e.Trim() != "0") return "off";
            string v = "";
            try
            {
                string p = Path.Combine(stateDir ?? "", "config.txt");
                if (File.Exists(p))
                    foreach (string line in File.ReadAllLines(p))
                    {
                        int i = line.IndexOf('=');
                        if (i > 0 && !line.StartsWith("#") && string.Equals(line.Substring(0, i).Trim(), "anim", StringComparison.OrdinalIgnoreCase))
                            v = line.Substring(i + 1).Trim().ToLowerInvariant();
                    }
            }
            catch (Exception) { }
            if (v == "off" || v == "0" || v == "none" || v == "static") return "off";
            if (v == "intro" || v == "once") return "intro";
            return "untilkey";
        }

        /// "" when this process may animate before its prompt, else why not: -NonInteractive, or a script
        /// (-Command / -File / -EncodedCommand) that doesn't end at a prompt (-NoExit). A pulled tab is
        /// `-NoExit -EncodedCommand`: allowed.
        public static string ArgvReason(string[] argv)
        {
            if (argv == null) return "";
            bool scripted = false, noExit = false;
            for (int i = 1; i < argv.Length; i++)
            {
                string a = argv[i] ?? "";
                if (a.Length < 2 || (a[0] != '-' && a[0] != '/')) continue;
                string n = a.Substring(1).ToLowerInvariant();
                if (n.Length >= 4 && "noninteractive".StartsWith(n)) return "non-interactive";
                if (n.Length >= 3 && "noexit".StartsWith(n)) noExit = true;
                if ("command".StartsWith(n) || "file".StartsWith(n) || "encodedcommand".StartsWith(n) || n == "ec")
                { scripted = true; break; }   // the rest is the command / script arguments
            }
            return scripted && !noExit ? "scripted" : "";
        }

        // ---- layout

        // visible cells of one line (escape sequences take none; every other char one) = Core.VisibleWidth
        public static int VisibleWidth(string s)
        {
            int n = 0;
            for (int i = 0; i < s.Length; i++)
            {
                if (s[i] == '\u001b' && i + 1 < s.Length && s[i + 1] == '[') { i += 2; while (i < s.Length && (s[i] < '@' || s[i] > '~')) i++; }
                else if (!char.IsLowSurrogate(s[i])) n++;
            }
            return n;
        }

        static string[] ArtLines(string raw)
        {
            var l = new List<string>(raw.Replace("\r\n", "\n").Split('\n'));
            while (l.Count > 0 && VisibleWidth(l[l.Count - 1]) == 0) l.RemoveAt(l.Count - 1);
            return l.ToArray();
        }

        /// Finds the static art's rows in the printed text. Null (why says why) if they aren't there in one
        /// column, one row after another, or the printed text doesn't end at the start of a line.
        public static AnimLayout Locate(string printed, string staticAns, out string why)
        {
            why = "";
            string[] art = ArtLines(staticAns ?? "");
            string[] L = (printed ?? "").Replace("\r\n", "\n").Split('\n');
            int k = L.Length - 1, h = art.Length;
            if (h == 0) { why = "empty art"; return null; }
            if (L[k].Length != 0) { why = "printed text does not end with a newline"; return null; }
            for (int j = 0; j + h <= k; j++)
            {
                int at = L[j].IndexOf(art[0], StringComparison.Ordinal);
                if (at < 0) continue;
                int col = VisibleWidth(L[j].Substring(0, at));
                bool ok = true;
                for (int y = 1; y < h && ok; y++)
                {
                    if (art[y].Length == 0) continue;
                    int a = L[j + y].IndexOf(art[y], StringComparison.Ordinal);
                    ok = a >= 0 && VisibleWidth(L[j + y].Substring(0, a)) == col;
                }
                if (!ok) continue;
                var lay = new AnimLayout { Static = art, Dist = new int[h], Width = new int[h], Col = col };
                for (int y = 0; y < h; y++)
                {
                    lay.Dist[y] = k - (j + y);
                    lay.Width[y] = VisibleWidth(art[y]);
                    lay.MaxArtWidth = Math.Max(lay.MaxArtWidth, lay.Width[y]);
                }
                foreach (string line in L) lay.MaxLineWidth = Math.Max(lay.MaxLineWidth, VisibleWidth(line));
                return lay;
            }
            why = "art not found in the printed card";
            return null;
        }

        // ---- the bundle, streamed

        class FrameReader   // over a reader the caller owns
        {
            readonly TextReader r; readonly char[] buf = new char[1 << 16]; int pos, len; bool eof;
            readonly StringBuilder sb = new StringBuilder(1 << 17);
            public int Lines, Fps, Count, Final;
            public FrameReader(TextReader reader)
            {
                r = reader;
                string hdr = Chunk();
                Lines = Int(hdr, "lines"); Fps = Int(hdr, "fps"); Count = Int(hdr, "frames"); Final = Int(hdr, "final");
                if (Fps <= 0) Fps = 12;
            }
            static int Int(string s, string key)
            {
                int i = s.IndexOf("\"" + key + "\"", StringComparison.Ordinal);
                if (i < 0) return -1;
                i = s.IndexOf(':', i); if (i < 0) return -1;
                i++; while (i < s.Length && s[i] == ' ') i++;
                int v = 0, n = 0; bool neg = i < s.Length && s[i] == '-'; if (neg) i++;
                while (i < s.Length && s[i] >= '0' && s[i] <= '9') { v = v * 10 + (s[i] - '0'); i++; n++; }
                return n == 0 ? -1 : neg ? -v : v;
            }
            // text up to the next form feed (or the end); null at the end
            string Chunk()
            {
                sb.Length = 0; bool any = false;
                while (true)
                {
                    if (pos >= len) { if (eof) break; len = r.Read(buf, 0, buf.Length); pos = 0; if (len <= 0) { eof = true; len = 0; break; } }
                    int ff = Array.IndexOf(buf, '\f', pos, len - pos);
                    if (ff < 0) { sb.Append(buf, pos, len - pos); pos = len; any = true; continue; }
                    sb.Append(buf, pos, ff - pos); pos = ff + 1; any = true;
                    return sb.ToString();
                }
                return any && sb.Length > 0 ? sb.ToString() : null;
            }
            public string[] Next() { string c = Chunk(); return c == null ? null : ArtLines(c); }
        }

        // ---- playback

        /// Plays the bundle over the layout on con. Assumes the printed card is on screen with the cursor on the
        /// line after it, at column 0. The printed card is the loop's final frame, shown sinceMs ago: the next frame
        /// is due one frame period after the print, so setup time up to one period (83 ms) is invisible. maxSeconds
        /// caps playback, counted from the print (<= 30). Never throws.
        public static AnimResult Play(TextReader bundle, AnimLayout lay, string mode, double maxSeconds, IAnimConsole con)
        {
            return Play(bundle, lay, mode, maxSeconds, con, 0);
        }

        public static AnimResult Play(TextReader bundle, AnimLayout lay, string mode, double maxSeconds, IAnimConsole con, long sinceMs)
        {
            var res = new AnimResult(); res.Mode = mode;
            if (lay == null) { res.Reason = "no layout"; return res; }
            int h = lay.Static.Length;
            res.ArtRows = h; res.Col = lay.Col;
            int w0, h0, row;
            try
            {
                w0 = con.Width; h0 = con.Height; row = con.Row;
                if (lay.MaxLineWidth >= w0) { res.Reason = "window too narrow"; return res; }
                if (con.Col != 0) { res.Reason = "cursor not at the start of a line"; return res; }
                if (con.KeyAvailable()) { res.Reason = "key already waiting"; return res; }
            }
            catch (Exception e) { res.Reason = "no console: " + e.Message; return res; }
            var vis = new List<int>();
            for (int y = 0; y < h; y++) if (lay.Dist[y] <= row) vis.Add(y);
            res.VisibleRows = vis.Count;
            if (vis.Count == 0) { res.Reason = "card scrolled out of the window"; return res; }

            FrameReader fr;
            try
            {
                fr = new FrameReader(bundle);
                if (fr.Lines != h || fr.Count < 2 || fr.Final < 0 || fr.Final >= fr.Count) { res.Reason = "bundle does not fit the card"; return res; }
            }
            catch (Exception e) { res.Reason = "bundle unreadable: " + e.Message; return res; }

            var cache = new List<string[]>();
            string[] shown = (string[])lay.Static.Clone();   // what each art row shows now
            int[] shownW = (int[])lay.Width.Clone();
            double cap = Math.Min(maxSeconds > 0 ? maxSeconds : CapSeconds, CapSeconds) * 1000;
            int n = fr.Count;
            double period = 1000.0 / fr.Fps;
            bool intro = mode == "intro", finalChecked = false;
            string stop = "";
            long tp = con.Ms - Math.Max(0, sinceMs);   // the print: the final frame went up then
            double anchor = 0;                         // frame k is due at anchor + k * period (ms after the print)
            res.Status = "played";
            bool hidden = false;
            try
            {
                int idx = (fr.Final + 1) % n, k = 0;
                while (true)
                {
                    // the next frame, read ahead of its time (streamed: the bundle is read as far as needed)
                    while (cache.Count <= idx) { string[] f = fr.Next(); if (f == null) break; cache.Add(f); }
                    if (cache.Count <= idx) { stop = "mismatch"; break; }   // fewer frames than the header says
                    // the format promises the final frame is the static card: if not, stop and show the static card
                    if (!finalChecked && cache.Count > fr.Final)
                    {
                        if (!Same(cache[fr.Final], lay.Static)) { stop = "mismatch"; break; }
                        finalChecked = true;
                    }
                    string[] frame = cache[idx];
                    if (frame.Length != h) { stop = "mismatch"; break; }
                    if (k == 0) res.ReadyMs = con.Ms - tp;
                    double due = anchor + (k + 1) * period;
                    while (stop == "")
                    {
                        if (con.Cancelled) stop = "cancel";
                        else if (con.KeyAvailable()) stop = "key";
                        else if (con.Width != w0 || con.Height != h0) stop = "resize";
                        else
                        {
                            long now = con.Ms - tp;
                            if (now >= cap) stop = "cap";
                            else if (now >= due) break;
                            else con.Wait((int)Math.Max(1, Math.Min(Math.Ceiling(due - now), cap - now)));
                        }
                    }
                    if (stop != "") break;
                    if (!hidden) { con.Write("\u001b[?25l"); hidden = true; }
                    if (!Draw(con, lay, vis, frame, shown, shownW, false)) { stop = "mismatch"; break; }
                    long t = con.Ms - tp;
                    if (res.FirstFrameMs < 0) { res.FirstFrameMs = t; res.FirstFrameStamp = Stopwatch.GetTimestamp(); }
                    res.FrameMs.Add((int)t); res.FrameIndex.Add(idx); k++;
                    if (t > due + period) anchor = t - k * period;   // fell behind (slow setup, a busy machine): keep the pace from here
                    if (intro && k >= n) { stop = "intro"; break; }
                    idx = (idx + 1) % n;
                }
            }
            catch (Exception e) { stop = "error:" + e.Message; }
            finally
            {
                res.Stop = stop; res.Frames = res.FrameMs.Count;
                try
                {
                    if (stop == "resize")
                    {
                        // the window changed under us: if the card still fits (no rewrap), the rows are where they
                        // were relative to the cursor; redraw the static card there, else leave it as it is
                        int nw = con.Width, nr = con.Row;
                        if (lay.MaxLineWidth < nw && con.Col == 0)
                        {
                            var v2 = new List<int>();
                            for (int y = 0; y < h; y++) if (lay.Dist[y] <= nr) v2.Add(y);
                            res.FinalRestored = Draw(con, lay, v2, lay.Static, shown, shownW, true);
                        }
                    }
                    else res.FinalRestored = Draw(con, lay, vis, lay.Static, shown, shownW, false);
                }
                catch (Exception) { }
                if (hidden) try { con.Write("\u001b[0m\u001b[?25h"); } catch (Exception) { }
                res.TotalMs = con.Ms - tp;
            }
            return res;
        }

        static bool Same(string[] a, string[] b)
        {
            if (a.Length != b.Length) return false;
            for (int i = 0; i < a.Length; i++) if (!string.Equals(a[i], b[i], StringComparison.Ordinal)) return false;
            return true;
        }

        // One frame: only the visible art rows that changed, top to bottom, each at the art's column, padded with
        // blanks over whatever the previous frame left wider; then back to the cursor line, column 0.
        static bool Draw(IAnimConsole con, AnimLayout lay, List<int> vis, string[] frame, string[] shown, int[] shownW, bool force)
        {
            var sb = new StringBuilder(1 << 17);
            int cur = 0;   // lines above the cursor line we are on
            var ws = new int[vis.Count];
            for (int i = 0; i < vis.Count; i++)
            {
                ws[i] = VisibleWidth(frame[vis[i]]);
                if (ws[i] > lay.MaxArtWidth) return false;   // would overwrite the card's border
            }
            sb.Append("\u001b[0m");
            for (int i = 0; i < vis.Count; i++)
            {
                int y = vis[i];
                if (!force && string.Equals(frame[y], shown[y], StringComparison.Ordinal)) continue;
                int d = lay.Dist[y];
                if (d < cur) sb.Append("\u001b[").Append(cur - d).Append('B');
                else if (d > cur) sb.Append("\u001b[").Append(d - cur).Append('A');
                cur = d;
                sb.Append("\u001b[").Append(lay.Col + 1).Append('G').Append(frame[y]).Append("\u001b[0m");
                int pad = Math.Max(shownW[y], lay.Width[y]) - ws[i];
                if (force) pad = Math.Max(pad, lay.MaxArtWidth - ws[i]);
                if (pad > 0) sb.Append(' ', pad);
                shown[y] = frame[y]; shownW[y] = ws[i];
            }
            if (cur > 0) sb.Append("\u001b[").Append(cur).Append('B');
            sb.Append('\r');
            if (sb.Length > 5) con.Write(sb.ToString());
            return true;
        }

        // ---- the real console

        /// Everything a tab needs: which bundle, whether it may animate here, then play on the real console.
        /// printed = the exact text just written for the card; hostName = $Host.Name; printedAt = the
        /// Stopwatch.GetTimestamp() taken right after it was written (0: now). Never throws: an error leaves the
        /// static card and goes to <state>\errors.log. With POKESHELL_ANIM_STATS = <file>, one line per call is
        /// appended there (tests, measurements).
        public static AnimResult Run(string root, string stateDir, string pack, string character, string art, bool shiny,
                                     string printed, string hostName, long printedAt)
        {
            var res = new AnimResult();
            if (printedAt == 0) printedAt = Stopwatch.GetTimestamp();
            try
            {
                string[] f = Find(root, pack, character, art, shiny);
                res.Bundle = f[0];
                if (f[0] == "") res.Reason = "no animation for this card";
                else
                {
                    res.Mode = Mode(stateDir);
                    string why = res.Mode == "off" ? "anim=off" : StaticReason(hostName);
                    AnimLayout lay = null;
                    if (why == "") lay = Locate(printed, File.ReadAllText(f[1], Encoding.UTF8), out why);
                    if (why != "") res.Reason = why;
                    else
                    {
                        double max = CapSeconds, m;
                        string env = Environment.GetEnvironmentVariable("POKESHELL_ANIM_MAX");   // tests / measurements: a shorter cap
                        if (!string.IsNullOrEmpty(env) && double.TryParse(env, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out m) && m > 0) max = Math.Min(m, CapSeconds);
                        using (var con = new AnimConsole())
                        using (var reader = new StreamReader(f[0], new UTF8Encoding(false), false, 1 << 16))
                        {
                            long since = (Stopwatch.GetTimestamp() - printedAt) * 1000 / Stopwatch.Frequency;
                            string mode = res.Mode;
                            res = Play(reader, lay, mode, max, con, since);
                            res.Bundle = f[0];
                            if (res.Status == "played")
                                res.Timing = "setup=" + since + "ms ready=" + res.ReadyMs + "ms";   // after the print: Run entered + checked, first frame ready
                        }
                    }
                }
            }
            catch (Exception e)
            {
                res.Status = "static"; res.Reason = "error: " + e.Message;
                Log(stateDir, DateTime.Now.ToString("s", System.Globalization.CultureInfo.InvariantCulture) + "\tanim: " + e.Message);
            }
            string stats = Environment.GetEnvironmentVariable("POKESHELL_ANIM_STATS");
            if (!string.IsNullOrEmpty(stats)) try { File.AppendAllText(stats, res.ToString() + "\r\n"); } catch (Exception) { }
            return res;
        }

        public static AnimResult Run(string root, string stateDir, string pack, string character, string art, bool shiny,
                                     string printed, string hostName)
        {
            return Run(root, stateDir, pack, character, art, shiny, printed, hostName, 0);
        }

        static void Log(string stateDir, string line)
        {
            try { if (!string.IsNullOrEmpty(stateDir)) { Directory.CreateDirectory(stateDir); File.AppendAllText(Path.Combine(stateDir, "errors.log"), line + "\r\n"); } }
            catch (Exception) { }
        }

        /// "" when the real console can animate: an interactive console host with a real (not redirected)
        /// console on both ends, VT output on, and a session that ends at a prompt.
        public static string StaticReason(string hostName)
        {
            if (!string.IsNullOrEmpty(hostName) && hostName != "ConsoleHost") return "host " + hostName;
            try
            {
                if (Console.IsOutputRedirected) return "output redirected";
                if (Console.IsInputRedirected) return "input redirected";
            }
            catch (Exception) { return "no console"; }
            if (!Environment.UserInteractive) return "non-interactive";
            string a = ArgvReason(Environment.GetCommandLineArgs());
            if (a != "") return a;
            if (!AnimConsole.VtOutput()) return "no VT output";
            return "";
        }
    }

    /// The process's console: WriteConsoleW (VT, UTF-16: no code page in the way), Console for the window and
    /// cursor, Console.KeyAvailable to peek for a key press (it drops key-ups, modifier-only presses, mouse and
    /// focus events, and leaves the first real key-down in the buffer), and a wait on the input handle between
    /// frames. Ctrl+C is taken over while playing (it stops the animation, not the pulled tab's command).
    public sealed class AnimConsole : IAnimConsole, IDisposable
    {
        [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr GetStdHandle(int n);
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        static extern bool WriteConsoleW(IntPtr h, string s, int n, out int written, IntPtr reserved);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetConsoleMode(IntPtr h, out uint mode);
        [DllImport("kernel32.dll", SetLastError = true)] static extern uint WaitForSingleObject(IntPtr h, uint ms);

        readonly IntPtr hOut, hIn;
        readonly Stopwatch sw = Stopwatch.StartNew();
        volatile bool cancelled;
        ConsoleCancelEventHandler onCancel;

        public AnimConsole() { hOut = GetStdHandle(-11); hIn = GetStdHandle(-10); }

        // taken at the first wait, not up front: registering costs a few ms that belong after the first frame is ready
        void HookCtrlC()
        {
            if (onCancel != null) return;
            onCancel = delegate(object s, ConsoleCancelEventArgs e) { cancelled = true; e.Cancel = true; };
            try { Console.CancelKeyPress += onCancel; } catch (Exception) { }
        }

        public static bool VtOutput()
        {
            uint m;
            return GetConsoleMode(GetStdHandle(-11), out m) && (m & 0x4) != 0;   // ENABLE_VIRTUAL_TERMINAL_PROCESSING
        }

        public int Width { get { return Console.WindowWidth; } }
        public int Height { get { return Console.WindowHeight; } }
        public int Row { get { return Console.CursorTop - Console.WindowTop; } }
        public int Col { get { return Console.CursorLeft; } }
        public long Ms { get { return sw.ElapsedMilliseconds; } }
        public bool Cancelled { get { return cancelled; } }
        public bool KeyAvailable() { return Console.KeyAvailable; }

        public void Write(string s)
        {
            int off = 0;
            while (off < s.Length)
            {
                int n = Math.Min(s.Length - off, 1 << 15), w;
                string part = off == 0 && n == s.Length ? s : s.Substring(off, n);
                if (!WriteConsoleW(hOut, part, part.Length, out w, IntPtr.Zero) || w <= 0) throw new IOException("WriteConsoleW failed");
                off += w;
            }
        }

        public void Wait(int ms)
        {
            HookCtrlC();
            if (ms <= 0) return;
            long end = sw.ElapsedMilliseconds + ms;
            // signaled = input waiting; if it was only events KeyAvailable drops (key-ups, focus, mouse), wait on
            if (WaitForSingleObject(hIn, (uint)ms) == 0 && !Console.KeyAvailable)
            {
                long left = end - sw.ElapsedMilliseconds;
                if (left > 0) Thread.Sleep((int)Math.Min(left, 10));
            }
        }

        public void Dispose() { if (onCancel != null) try { Console.CancelKeyPress -= onCancel; } catch (Exception) { } }
    }
}
