// Test harness for lib\Anim.cs (tests\test-anim.ps1): a fake console with a tiny VT screen model and a
// virtual clock, and a headless pseudoconsole (ConPTY) runner for end-to-end key-passthrough checks.
// Neither opens a window or a Windows Terminal tab. C# 5 (Windows PowerShell's compiler).
using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using Microsoft.Win32.SafeHandles;

namespace PokeshellTest
{
    /// A W x H screen that interprets what the player writes: text, CR, LF, CSI A/B/C/D/G/H/K/J, SGR (m) and
    /// ?25 l/h. Every cell remembers its char and the SGR state it was written with, so two screens compare
    /// equal only if they look the same. Clamped cursor moves, scrolls and wraps are counted: the player must
    /// cause none. Time is virtual: Wait() advances it, KeyAt / ResizeAt / CancelAt script events.
    public class FakeConsole : Pokeshell.IAnimConsole
    {
        public int W, H, X, Y; int sx, sy;
        public string[,] Style; public char[,] Ch;
        string style = "";
        public bool CursorVisible = true;
        public int Clamps, Scrolls, Wraps, Newlines, Writes;
        public long Now;
        public long KeyAt = -1, ResizeAt = -1, CancelAt = -1;
        public int ResizeW = -1, ResizeH = -1;
        public int WriteCostMs;
        public List<string> Log = new List<string>();
        public bool Recording;

        public FakeConsole(int w, int h)
        {
            W = w; H = h; Style = new string[h, w]; Ch = new char[h, w];
            for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) { Ch[y, x] = ' '; Style[y, x] = ""; }
        }

        public int Width { get { return ResizeAt >= 0 && Now >= ResizeAt && ResizeW > 0 ? ResizeW : W; } }
        public int Height { get { return ResizeAt >= 0 && Now >= ResizeAt && ResizeH > 0 ? ResizeH : H; } }
        public int Row { get { return Y; } }
        public int Col { get { return X; } }
        public long Ms { get { return Now; } }
        public bool Cancelled { get { return CancelAt >= 0 && Now >= CancelAt; } }
        public bool KeyAvailable() { return KeyAt >= 0 && Now >= KeyAt; }
        public void Wait(int ms)
        {
            long end = Now + Math.Max(1, ms);
            foreach (long t in new[] { KeyAt, ResizeAt, CancelAt }) if (t > Now && t < end) end = t;
            Now = end;
        }

        void Scroll()
        {
            for (int y = 1; y < H; y++) for (int x = 0; x < W; x++) { Ch[y - 1, x] = Ch[y, x]; Style[y - 1, x] = Style[y, x]; }
            for (int x = 0; x < W; x++) { Ch[H - 1, x] = ' '; Style[H - 1, x] = ""; }
            Scrolls++;
        }

        void Down() { if (Y == H - 1) Scroll(); else Y++; }

        // SGR, semantically (so a stream re-encoded by conhost compares equal): the style is "fg|bg|bold"
        string fg = "", bg = ""; bool bold;
        void Sgr(string p)
        {
            string[] a = p.Split(';');
            for (int i = 0; i < a.Length; i++)
            {
                int v; if (!int.TryParse(a[i], out v)) v = 0;
                if (v == 0) { fg = ""; bg = ""; bold = false; }
                else if (v == 1) bold = true;
                else if (v == 22) bold = false;
                else if (v == 39) fg = "";
                else if (v == 49) bg = "";
                else if ((v == 38 || v == 48) && i + 1 < a.Length && a[i + 1] == "2" && i + 4 < a.Length)
                { string c = a[i + 2] + "," + a[i + 3] + "," + a[i + 4]; if (v == 38) fg = c; else bg = c; i += 4; }
                else if ((v == 38 || v == 48) && i + 1 < a.Length && a[i + 1] == "5" && i + 2 < a.Length)
                { string c = "p" + a[i + 2]; if (v == 38) fg = c; else bg = c; i += 2; }
                else if (v >= 30 && v <= 37 || v >= 90 && v <= 97) fg = "p" + v;
                else if (v >= 40 && v <= 47 || v >= 100 && v <= 107) bg = "p" + v;
            }
            style = fg == "" && bg == "" && !bold ? "" : fg + "|" + bg + (bold ? "|b" : "");
        }

        public void Write(string s)
        {
            Writes++;
            if (Recording) Log.Add(s);
            Now += WriteCostMs;
            for (int i = 0; i < s.Length; i++)
            {
                char c = s[i];
                if (c == '\u001b' && i + 1 < s.Length && s[i + 1] == ']')
                {   // OSC (titles): skip to BEL or ESC \
                    int j = i + 2; while (j < s.Length && s[j] != '\u0007' && !(s[j] == '\u001b' && j + 1 < s.Length && s[j + 1] == '\\')) j++;
                    i = j < s.Length && s[j] == '\u001b' ? j + 1 : j; continue;
                }
                if (c == '\u001b' && i + 1 < s.Length && (s[i + 1] == '7' || s[i + 1] == '8'))
                { if (s[i + 1] == '7') { sx = X; sy = Y; } else { X = sx; Y = sy; } i++; continue; }
                if (c == '\u001b' && i + 1 < s.Length && s[i + 1] == '[')
                {
                    int j = i + 2; while (j < s.Length && (s[j] < '@' || s[j] > '~')) j++;
                    string p = s.Substring(i + 2, j - i - 2); char f = j < s.Length ? s[j] : '?';
                    i = j;
                    if (p.StartsWith("?")) { if (p == "?25") { if (f == 'l') CursorVisible = false; if (f == 'h') CursorVisible = true; } continue; }
                    int n = 1; int.TryParse(p.Split(';')[0], out n); if (n < 1) n = 1;
                    switch (f)
                    {
                        case 'A': if (Y - n < 0) Clamps++; Y = Math.Max(0, Y - n); break;
                        case 'B': if (Y + n > H - 1) Clamps++; Y = Math.Min(H - 1, Y + n); break;
                        case 'C': X = Math.Min(W - 1, X + n); break;
                        case 'D': X = Math.Max(0, X - n); break;
                        case 'G': X = Math.Min(W - 1, n - 1); break;
                        case 'H':
                            { string[] a = p.Split(';'); int r = 1, cc = 1; if (a.Length > 0) int.TryParse(a[0], out r); if (a.Length > 1) int.TryParse(a[1], out cc);
                              Y = Math.Min(H - 1, Math.Max(1, r) - 1); X = Math.Min(W - 1, Math.Max(1, cc) - 1); break; }
                        case 'K':
                            { int a0 = 0; int.TryParse(p, out a0); int from = a0 == 0 ? X : 0, to = a0 == 1 ? X + 1 : W;
                              for (int x = from; x < to && x < W; x++) { Ch[Y, x] = ' '; Style[Y, x] = ""; } break; }
                        case 'X': for (int x = X; x < X + n && x < W; x++) { Ch[Y, x] = ' '; Style[Y, x] = ""; } break;
                        case 'J':
                            { int a0 = 0; int.TryParse(p, out a0);
                              for (int y = 0; y < H; y++) for (int x = 0; x < W; x++)
                                  if (a0 == 2 || a0 == 3 || (a0 == 0 && (y > Y || y == Y && x >= X)) || (a0 == 1 && (y < Y || y == Y && x <= X))) { Ch[y, x] = ' '; Style[y, x] = ""; }
                              break; }
                        case 'd': Y = Math.Min(H - 1, n - 1); break;
                        case 'S': for (int k = 0; k < n; k++) Scroll(); break;
                        case 'm': Sgr(p); break;
                    }
                    continue;
                }
                if (c == '\r') { X = 0; continue; }
                if (c == '\n') { Newlines++; Down(); continue; }
                if (char.IsLowSurrogate(c)) continue;
                if (X >= W) { Wraps++; X = 0; Down(); }
                Ch[Y, X] = c; Style[Y, X] = style; X++;
            }
        }

        /// the screen as text (one line per row, cells as "style|char" runs), for comparisons
        public string Dump()
        {
            var sb = new StringBuilder();
            for (int y = 0; y < H; y++)
            {
                string last = null;
                for (int x = 0; x < W; x++)
                {
                    string st = Style[y, x];
                    if (Ch[y, x] == ' ') { string[] f = st.Split('|'); st = f.Length > 1 && f[1] != "" ? "|" + f[1] : ""; }   // a blank shows only its background
                    if (st != last) { sb.Append('{').Append(st).Append('}'); last = st; }
                    sb.Append(Ch[y, x]);
                }
                sb.Append('\n');
            }
            return sb.ToString();
        }

        public void ResetCounters() { Clamps = Scrolls = Wraps = Newlines = Writes = 0; Log.Clear(); }
    }

    /// A process on a headless pseudoconsole: we write its keyboard input and read everything it draws.
    public sealed class PtyProcess : IDisposable
    {
        [StructLayout(LayoutKind.Sequential)] struct COORD { public short X, Y; }
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        struct STARTUPINFO
        {
            public int cb; public string lpReserved, lpDesktop, lpTitle;
            public int dwX, dwY, dwXSize, dwYSize, dwXCountChars, dwYCountChars, dwFillAttribute, dwFlags;
            public short wShowWindow, cbReserved2; public IntPtr lpReserved2, hStdInput, hStdOutput, hStdError;
        }
        [StructLayout(LayoutKind.Sequential)] struct STARTUPINFOEX { public STARTUPINFO StartupInfo; public IntPtr lpAttributeList; }
        [StructLayout(LayoutKind.Sequential)] struct PROCESS_INFORMATION { public IntPtr hProcess, hThread; public int dwProcessId, dwThreadId; }

        [DllImport("kernel32.dll", SetLastError = true)] static extern int CreatePseudoConsole(COORD size, SafeFileHandle hInput, SafeFileHandle hOutput, uint flags, out IntPtr phPC);
        [DllImport("kernel32.dll", SetLastError = true)] static extern void ClosePseudoConsole(IntPtr hPC);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool CreatePipe(out SafeFileHandle r, out SafeFileHandle w, IntPtr sa, int size);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool InitializeProcThreadAttributeList(IntPtr list, int count, int flags, ref IntPtr size);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool UpdateProcThreadAttribute(IntPtr list, uint flags, IntPtr attr, IntPtr value, IntPtr size, IntPtr prev, IntPtr retSize);
        [DllImport("kernel32.dll", SetLastError = true)] static extern void DeleteProcThreadAttributeList(IntPtr list);
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        static extern bool CreateProcessW(string app, StringBuilder cmd, IntPtr pa, IntPtr ta, bool inherit, uint flags, IntPtr env, string cwd, ref STARTUPINFOEX si, out PROCESS_INFORMATION pi);
        [DllImport("kernel32.dll", SetLastError = true)] static extern uint WaitForSingleObject(IntPtr h, uint ms);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetExitCodeProcess(IntPtr h, out uint code);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool CloseHandle(IntPtr h);

        IntPtr hPC, attrs; PROCESS_INFORMATION pi;
        FileStream input; Thread reader;
        readonly StringBuilder output = new StringBuilder();
        public PtyProcess(string commandLine, short cols, short rows)
        {
            SafeFileHandle inR, inW, outR, outW;
            if (!CreatePipe(out inR, out inW, IntPtr.Zero, 0) || !CreatePipe(out outR, out outW, IntPtr.Zero, 0)) throw new IOException("CreatePipe");
            int hr = CreatePseudoConsole(new COORD { X = cols, Y = rows }, inR, outW, 0, out hPC);
            if (hr != 0) throw new IOException("CreatePseudoConsole: 0x" + hr.ToString("x"));
            inR.Dispose(); outW.Dispose();   // the pseudoconsole has its own copies
            input = new FileStream(inW, FileAccess.Write);
            var outStream = new FileStream(outR, FileAccess.Read);
            reader = new Thread(delegate()
            {
                var buf = new byte[1 << 16]; var dec = Encoding.UTF8.GetDecoder(); var chars = new char[1 << 17];
                try { int n; while ((n = outStream.Read(buf, 0, buf.Length)) > 0) { int c = dec.GetChars(buf, 0, n, chars, 0); lock (output) output.Append(chars, 0, c); } }
                catch (Exception) { }
            });
            reader.IsBackground = true; reader.Start();

            IntPtr size = IntPtr.Zero;
            InitializeProcThreadAttributeList(IntPtr.Zero, 1, 0, ref size);
            attrs = Marshal.AllocHGlobal(size);
            if (!InitializeProcThreadAttributeList(attrs, 1, 0, ref size)) throw new IOException("InitializeProcThreadAttributeList");
            if (!UpdateProcThreadAttribute(attrs, 0, (IntPtr)0x00020016, hPC, (IntPtr)IntPtr.Size, IntPtr.Zero, IntPtr.Zero))   // PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE
                throw new IOException("UpdateProcThreadAttribute");
            var si = new STARTUPINFOEX(); si.StartupInfo.cb = Marshal.SizeOf(typeof(STARTUPINFOEX)); si.lpAttributeList = attrs;
            si.StartupInfo.dwFlags = 0x100;   // STARTF_USESTDHANDLES with none given: the child's std handles are the pseudoconsole's, not our (redirected) ones
            if (!CreateProcessW(null, new StringBuilder(commandLine), IntPtr.Zero, IntPtr.Zero, false, 0x00080000 /* EXTENDED_STARTUPINFO_PRESENT */, IntPtr.Zero, null, ref si, out pi))
                throw new IOException("CreateProcess: " + Marshal.GetLastWin32Error());
        }

        public string Output { get { lock (output) return output.ToString(); } }
        public void Type(string s) { byte[] b = Encoding.UTF8.GetBytes(s); input.Write(b, 0, b.Length); input.Flush(); }
        /// waits until the output contains text (true) or the timeout passes
        public bool WaitFor(string text, int ms)
        {
            var end = DateTime.UtcNow.AddMilliseconds(ms);
            while (DateTime.UtcNow < end) { if (Output.Contains(text)) return true; Thread.Sleep(25); }
            return Output.Contains(text);
        }
        public bool WaitExit(int ms) { return WaitForSingleObject(pi.hProcess, (uint)ms) == 0; }
        public int ExitCode { get { uint c; GetExitCodeProcess(pi.hProcess, out c); return (int)c; } }

        public void Dispose()
        {
            try { input.Dispose(); } catch (Exception) { }
            if (hPC != IntPtr.Zero) { ClosePseudoConsole(hPC); hPC = IntPtr.Zero; }   // ends the pseudoconsole session (the child sees its console close)
            if (attrs != IntPtr.Zero) { DeleteProcThreadAttributeList(attrs); Marshal.FreeHGlobal(attrs); attrs = IntPtr.Zero; }
            if (pi.hProcess != IntPtr.Zero) { CloseHandle(pi.hProcess); CloseHandle(pi.hThread); pi.hProcess = IntPtr.Zero; }
        }
    }
}
