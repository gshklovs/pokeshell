// pokeshell booster packs: the roll of one whole real booster (packs/<pack>/boosters.json, docs/BOOSTERS.md).
//
// PowerShell (lib\booster.ps1) reads boosters.json + pack.json and hands this file a flat model: the pack's slots,
// each with its outcomes (a label, an effective weight, the pool of card indices it draws from, the finish).
// This file does the dice, so the 20k-pack Monte Carlo in tests\test-boosters.ps1 runs in well under a second, and the
// whole open: the booster index (<state>\booster-index.tsv, every set's model resolved once, so an open never parses
// pack.json), the set choice of `pack open random` (weighted by pack price), the shiny rolls, effects, NEW and the
// reveal order.
// Compiled on demand into <state>\pokeshell-booster-*.dll (like the startup core). C# 5 only.
using System;
using System.Collections.Generic;
using System.Security.Cryptography;

namespace Pokeshell
{
    /// The dice. Default: every draw comes from the OS CSPRNG (RandomNumberGenerator), so packs can't be predicted
    /// or replayed. With a seed (tests, --seed): System.Random, reproducible.
    public class BoosterRng
    {
        readonly RandomNumberGenerator csp;
        readonly Random seeded;
        readonly byte[] buf = new byte[8];
        public readonly bool Secure;
        public BoosterRng() { csp = RandomNumberGenerator.Create(); Secure = true; }
        public BoosterRng(int seed) { seeded = new Random(seed); Secure = false; }
        /// uniform in [0, 1), 53 bits
        public double NextDouble()
        {
            if (seeded != null) return seeded.NextDouble();
            csp.GetBytes(buf);
            ulong v = BitConverter.ToUInt64(buf, 0) >> 11;
            return v * (1.0 / 9007199254740992.0);
        }
        /// uniform integer in [0, n)
        public int Next(int n)
        {
            if (n <= 1) return 0;
            int r = (int)(NextDouble() * n);
            return r >= n ? n - 1 : r;
        }
    }

    public class BoosterOutcome
    {
        public string Label = "";
        public double Weight;          // effective weight (already scaled by served/printed); <= 0 or an empty pool never rolls
        public int[] Pool = new int[0]; // card indices (into the caller's card table)
        public string Finish = "";     // "" = the slot's finish
    }

    public class BoosterSlot
    {
        public string Id = "";
        public int Count = 1;
        public string Finish = "normal";   // normal | reverse | holo ...
        public bool Distinct = true;       // several cards of one slot are all different cards (as printed packs are)
        public List<BoosterOutcome> Outcomes = new List<BoosterOutcome>();
        public void Add(string label, double weight, int[] pool, string finish)
        {
            Outcomes.Add(new BoosterOutcome { Label = label ?? "", Weight = weight, Pool = pool ?? new int[0], Finish = finish ?? "" });
        }
        /// the outcome's probability once empty outcomes are dropped (the renormalisation of docs/BOOSTERS.md)
        public double Probability(int outcome)
        {
            double total = 0;
            foreach (var o in Outcomes) if (o.Weight > 0 && o.Pool.Length > 0) total += o.Weight;
            var x = Outcomes[outcome];
            return total > 0 && x.Weight > 0 && x.Pool.Length > 0 ? x.Weight / total : 0;
        }
    }

    public class BoosterPick
    {
        public int Slot;          // index into the slots
        public string SlotId = "";
        public int Outcome;       // index into that slot's outcomes
        public string Label = "";
        public int Card;          // index into the caller's card table
        public string Finish = "";
    }

    public static class Booster
    {
        /// One pack: every slot in order, Count cards each. Returns the picks in slot order (the caller sorts the reveal).
        public static BoosterPick[] Roll(BoosterSlot[] slots, BoosterRng rng)
        {
            var picks = new List<BoosterPick>();
            for (int s = 0; s < slots.Length; s++)
            {
                var slot = slots[s];
                var used = new HashSet<int>();
                for (int k = 0; k < slot.Count; k++)
                {
                    int o = PickOutcome(slot, rng);
                    if (o < 0) break;   // nothing we serve can fill this slot: the pack has one card fewer
                    var oc = slot.Outcomes[o];
                    int card = PickCard(oc.Pool, slot.Distinct ? used : null, rng);
                    used.Add(card);
                    picks.Add(new BoosterPick { Slot = s, SlotId = slot.Id, Outcome = o, Label = oc.Label, Card = card,
                                                Finish = oc.Finish.Length > 0 ? oc.Finish : slot.Finish });
                }
            }
            return picks.ToArray();
        }

        static int PickOutcome(BoosterSlot slot, BoosterRng rng)
        {
            double total = 0;
            foreach (var o in slot.Outcomes) if (o.Weight > 0 && o.Pool.Length > 0) total += o.Weight;
            if (total <= 0) return -1;
            double r = rng.NextDouble() * total;
            int last = -1;
            for (int i = 0; i < slot.Outcomes.Count; i++)
            {
                var o = slot.Outcomes[i];
                if (o.Weight <= 0 || o.Pool.Length == 0) continue;
                last = i;
                r -= o.Weight;
                if (r < 0) return i;
            }
            return last;   // floating-point edge: the last live outcome
        }

        /// uniform over the pool; when the slot must stay distinct, over the cards not drawn yet (if any are left)
        static int PickCard(int[] pool, HashSet<int> used, BoosterRng rng)
        {
            if (used == null || used.Count == 0) return pool[rng.Next(pool.Length)];
            var left = new List<int>(pool.Length);
            foreach (int c in pool) if (!used.Contains(c)) left.Add(c);
            if (left.Count == 0) return pool[rng.Next(pool.Length)];
            return left[rng.Next(left.Count)];
        }

        /// Monte Carlo of the set choice (pack open random): count each set index over n draws
        public static long[] SimulateSets(BoosterIndex idx, int n, BoosterRng rng)
        {
            var counts = new long[idx.Sets.Count];
            for (int i = 0; i < n; i++) { int s = idx.PickSet(rng); if (s >= 0) counts[s]++; }
            return counts;
        }

        /// Monte Carlo: roll n packs, count every pick as "<slot index>/<outcome index>" (and cards per pack in "cards").
        public static Dictionary<string, long> Simulate(BoosterSlot[] slots, int n, BoosterRng rng)
        {
            var counts = new Dictionary<string, long>();
            counts["packs"] = n; counts["cards"] = 0;
            for (int i = 0; i < n; i++)
            {
                var picks = Roll(slots, rng);
                counts["cards"] += picks.Length;
                foreach (var p in picks)
                {
                    string k = p.Slot + "/" + p.Outcome;
                    long v; counts.TryGetValue(k, out v); counts[k] = v + 1;
                }
            }
            return counts;
        }

        // the effect family the reveal shows for a card (a tier's default; an outcome's "fx" overrides it) and how big
        // the reveal is (0-5): see Open
        static readonly Dictionary<string, string> Fx = MakeFx();
        static Dictionary<string, string> MakeFx()
        {
            var d = new Dictionary<string, string>();
            foreach (var t in "common uncommon rare".Split(' ')) d[t] = "plain";
            foreach (var t in ("rare-holo promo trainer-gallery-rare-holo pikachu-rare rare-holo-v rare-holo-vmax rare-holo-vstar rare-holo-gx " +
                               "rare-holo-ex double-rare rare-holo-lv-x rare-prime rare-break legend rare-holo-star rare-prism-star " +
                               "ace-spec-rare futuristic-rare").Split(' ')) d[t] = "holo";
            foreach (var t in "rare-ultra ultra-rare illustration-rare".Split(' ')) d[t] = "full-art";
            d["special-illustration-rare"] = "alt-art";
            foreach (var t in "rare-rainbow shiny-ultra-rare".Split(' ')) d[t] = "rainbow";
            foreach (var t in "rare-secret hyper-rare".Split(' ')) d[t] = "gold";
            foreach (var t in "radiant-rare amazing-rare rare-shining".Split(' ')) d[t] = "radiant";
            foreach (var t in "rare-shiny rare-shiny-gx shiny-rare".Split(' ')) d[t] = "shiny";
            return d;
        }
        static readonly Dictionary<string, int> Hit = new Dictionary<string, int> {
            { "plain", 0 }, { "reverse", 1 }, { "holo", 2 }, { "full-art", 3 }, { "radiant", 3 }, { "shiny", 3 }, { "alt-art", 4 }, { "rainbow", 4 }, { "gold", 5 } };

        /// One pack of set s from the index: the roll, each card's shiny roll, effect and reveal size, NEW against the
        /// caught set (updated in place), in reveal order (rarest last). The same draws, in the same order, as the
        /// PowerShell open had: Roll, then one NextDouble per card for its shiny chance, so a seeded pack stays the same.
        public static BoosterCardOut[] Open(BoosterIndex idx, int s, BoosterRng rng, HashSet<string> caught)
        {
            var set = idx.Sets[s];
            var picks = Roll(set.Slots, rng);
            var outs = new List<BoosterCardOut>();
            for (int n = 0; n < picks.Length; n++)
            {
                var p = picks[n];
                var c = idx.Cards[p.Card];
                var om = set.Meta[p.Slot][p.Outcome];
                double roll = rng.NextDouble();   // always drawn, so a seeded pack stays in step
                bool shiny = roll < idx.ShinyChance && !idx.PrintedShinyTiers.Contains(c.Tier) && c.ShinyArt;
                string fx;
                if (om.Fx.Length > 0) fx = om.Fx; else if (!Fx.TryGetValue(c.TierId, out fx)) fx = "holo";
                if (p.Finish != "normal" && fx == "plain") fx = "reverse";   // a foil print of a non-foil card
                int hit; if (!Hit.TryGetValue(fx, out hit)) hit = 0;
                if (fx == "plain" && c.TierId == "rare") hit = 1;   // the rare slot's floor still comes last
                if (shiny) hit = Math.Min(5, hit + 1);
                double prob = set.Slots[p.Slot].Probability(p.Outcome);
                bool isNew = !caught.Contains(c.Id); caught.Add(c.Id);   // a second copy in the same pack isn't new
                outs.Add(new BoosterCardOut {
                    Id = c.Id, Name = c.Name, Number = c.Number, Rarity = c.Rarity, Tier = c.TierId, TierLabel = c.TierLabel,
                    Slot = p.SlotId, Outcome = p.Label, Finish = p.Finish, Fx = fx, Hit = hit, Shiny = shiny, IsNew = isNew,
                    OneIn = prob > 0 ? Math.Round(1 / prob, 1) : 0, Character = c.Character, SetName = c.SetName,
                    Image = "img/" + idx.Pack + "/" + c.Character + "/" + c.Id + (shiny ? "-shiny" : "") + ".png",
                    Order = n, TierIndex = c.Tier });
            }
            // reveal order, rarest last: the size of the hit (a shiny half a step up), then the odds of that kind of hit
            // (lower = later), then the slot order printed packs have (commons first, rare at the back)
            outs.Sort(delegate(BoosterCardOut a, BoosterCardOut b) {
                int r = (a.Hit + (a.Shiny ? 0.5 : 0)).CompareTo(b.Hit + (b.Shiny ? 0.5 : 0));
                if (r == 0) r = a.OneIn.CompareTo(b.OneIn);
                if (r == 0) r = a.Order.CompareTo(b.Order);
                return r;
            });
            return outs.ToArray();
        }

        /// the card ids caught in this pack (earned pulls, resolved as Resolve-PokeshellPull does: the art column is a
        /// built card of the same character, else pack.json "retired" maps character/tier to a built card). records are
        /// Pokeshell.Core.ReadPulls's PullRecords, read by field name (this assembly doesn't reference the core).
        public static HashSet<string> Caught(BoosterIndex idx, System.Collections.IEnumerable records)
        {
            var set = new HashSet<string>(StringComparer.Ordinal);
            System.Reflection.FieldInfo fStatus = null, fPack = null, fChar = null, fTier = null, fArt = null;
            foreach (object r in records)
            {
                if (r == null) continue;
                if (fStatus == null)
                {
                    var t = r.GetType();
                    fStatus = t.GetField("Status"); fPack = t.GetField("Pack"); fChar = t.GetField("Character"); fTier = t.GetField("Tier"); fArt = t.GetField("Art");
                    if (fStatus == null || fPack == null || fChar == null || fTier == null || fArt == null) throw new ArgumentException("not a pull record: " + t.FullName);
                }
                if ((string)fStatus.GetValue(r) != "earned" || (string)fPack.GetValue(r) != idx.Pack) continue;
                string ch = (string)fChar.GetValue(r), art = (string)fArt.GetValue(r) ?? "";
                int i;
                if (idx.ById.TryGetValue(art, out i) && idx.Cards[i].Character == ch) { set.Add(art); continue; }
                string to;
                if (idx.Retired.TryGetValue(ch + "/" + (string)fTier.GetValue(r), out to) && to.Length > 0 && idx.ById.ContainsKey(to)) set.Add(to);
            }
            return set;
        }
    }

    /// one card of an opened pack, as `pokeshell pack open --json` reports it
    public class BoosterCardOut
    {
        public string Id = "", Name = "", Number = "", Rarity = "", Tier = "", TierLabel = "", Slot = "", Outcome = "", Finish = "", Fx = "";
        public int Hit; public bool Shiny, IsNew; public double OneIn;
        public string Character = "", SetName = "", Image = "";
        public int Order, TierIndex;
    }

    /// a built card of the pack (the index's card table: every card whose art is built, so pull resolution sees them all)
    public class BoosterCard
    {
        public string Id = "", Character = "", Name = "", Number = "", TierId = "", TierLabel = "", Rarity = "", SetName = "";
        public int Tier;
        public bool ShinyArt;   // dist\<pack>\<character>-<id>-shiny.ans exists
    }

    /// what `pack odds` shows of an outcome
    public class BoosterOutcomeMeta
    {
        public string Label = "", Fx = "";
        public double Rate;
        public int Printed, Served;
        public bool Base;
    }

    public class BoosterSet
    {
        public string Id = "", Name = "";
        public string[] Aliases = new string[0];
        public double Price;            // USD, one sealed pack (boosters.json "price"); 0 = never picked at random
        public int Cards;               // the served cards of the set
        public BoosterSlot[] Slots = new BoosterSlot[0];
        public BoosterOutcomeMeta[][] Meta = new BoosterOutcomeMeta[0][];
        public bool Openable { get { return Cards > 0; } }
    }

    /// <summary>
    /// Every booster of a pack, resolved against the cards we serve, in one file (<state>\booster-index.tsv) so a pack
    /// opens without parsing pack.json: lib\booster.ps1 builds it from Get-PokeshellBoosterModel when its stamp (the data
    /// files, the art folder, this code) changes, then every open just loads it. Tab-separated lines:
    ///   stamp  &lt;stamp&gt;
    ///   pack   &lt;id&gt;  &lt;shiny chance&gt;  &lt;price exponent k&gt;  &lt;tier indices that print their shiny, comma-separated&gt;
    ///   card   &lt;id&gt; &lt;character&gt; &lt;name&gt; &lt;number&gt; &lt;tier index&gt; &lt;tier id&gt; &lt;tier label&gt; &lt;rarity&gt; &lt;set name&gt; &lt;shiny art 0/1&gt;
    ///   retired &lt;character/tier&gt; &lt;card id&gt;
    ///   set    &lt;id&gt; &lt;name&gt; &lt;aliases, comma-separated&gt; &lt;price&gt; &lt;served cards&gt;
    ///   slot   &lt;id&gt; &lt;count&gt; &lt;finish&gt; &lt;distinct 0/1&gt;
    ///   out    &lt;label&gt; &lt;weight&gt; &lt;finish&gt; &lt;fx&gt; &lt;rate&gt; &lt;printed&gt; &lt;served&gt; &lt;base 0/1&gt; &lt;pool: card indices, comma-separated&gt;
    /// </summary>
    public class BoosterIndex
    {
        public string Stamp = "", Pack = "";
        public double ShinyChance, PriceExponent;
        public HashSet<int> PrintedShinyTiers = new HashSet<int>();
        public List<BoosterCard> Cards = new List<BoosterCard>();
        public Dictionary<string, int> ById = new Dictionary<string, int>(StringComparer.Ordinal);
        public Dictionary<string, string> Retired = new Dictionary<string, string>(StringComparer.Ordinal);
        public List<BoosterSet> Sets = new List<BoosterSet>();

        static readonly System.Globalization.CultureInfo Inv = System.Globalization.CultureInfo.InvariantCulture;
        static string Clean(string s) { return (s ?? "").Replace('\t', ' ').Replace('\r', ' ').Replace('\n', ' '); }
        static string D(double d) { return d.ToString("R", Inv); }
        static double P(string s) { return double.Parse(s, Inv); }

        public int AddCard(BoosterCard c) { ById[c.Id] = Cards.Count; Cards.Add(c); return Cards.Count - 1; }

        /// <summary>
        /// Each set's chance to be the one `pack open random` opens: weight = price^-k over the openable sets with a
        /// price (boosters.json "priceExponent" is k), normalised. 0 for the others.
        /// </summary>
        public double[] SetChances()
        {
            var w = new double[Sets.Count]; double total = 0;
            for (int i = 0; i < Sets.Count; i++)
            {
                var s = Sets[i];
                if (!s.Openable || !(s.Price > 0)) continue;
                w[i] = Math.Pow(s.Price, -PriceExponent); total += w[i];
            }
            for (int i = 0; i < w.Length; i++) w[i] = total > 0 ? w[i] / total : 0;
            return w;
        }

        /// the set `pack open random` opens: one draw, by SetChances; -1 when no set can be opened at random
        public int PickSet(BoosterRng rng)
        {
            var ch = SetChances();
            double r = rng.NextDouble(); int last = -1;
            for (int i = 0; i < ch.Length; i++)
            {
                if (ch[i] <= 0) continue;
                last = i; r -= ch[i];
                if (r < 0) return i;
            }
            return last;
        }

        /// a set by id or alias, else its exact name, else a word of its name (Find-PokeshellBoosterSet's rule)
        public int FindSet(string want)
        {
            string w = (want ?? "").Trim().ToLowerInvariant();
            var hit = new List<int>();
            for (int i = 0; i < Sets.Count; i++) if (Sets[i].Id.ToLowerInvariant() == w || Array.IndexOf(Sets[i].Aliases, w) >= 0) hit.Add(i);
            if (hit.Count == 0) for (int i = 0; i < Sets.Count; i++) if (Sets[i].Name.ToLowerInvariant() == w) hit.Add(i);
            if (hit.Count == 0) for (int i = 0; i < Sets.Count; i++) if (Sets[i].Name.ToLowerInvariant().Contains(w)) hit.Add(i);
            if (hit.Count == 1) return hit[0];
            if (hit.Count > 1)
            {
                var names = new List<string>(); foreach (int i in hit) names.Add(Sets[i].Id + " (" + Sets[i].Name + ")");
                throw new ArgumentException("'" + want + "' matches several sets: " + string.Join(", ", names.ToArray()));
            }
            var ids = new List<string>(); foreach (var s in Sets) ids.Add(s.Id);
            throw new ArgumentException("no booster '" + want + "' (pokeshell pack sets lists them: " + string.Join(", ", ids.ToArray()) + ")");
        }

        public void Save(string file)
        {
            var sb = new System.Text.StringBuilder();
            sb.Append("stamp\t").Append(Clean(Stamp)).Append('\n');
            var pst = new List<string>(); foreach (int t in PrintedShinyTiers) pst.Add(t.ToString(Inv));
            sb.Append("pack\t").Append(Clean(Pack)).Append('\t').Append(D(ShinyChance)).Append('\t').Append(D(PriceExponent)).Append('\t').Append(string.Join(",", pst.ToArray())).Append('\n');
            foreach (var c in Cards)
                sb.Append("card\t").Append(Clean(c.Id)).Append('\t').Append(Clean(c.Character)).Append('\t').Append(Clean(c.Name)).Append('\t').Append(Clean(c.Number))
                  .Append('\t').Append(c.Tier.ToString(Inv)).Append('\t').Append(Clean(c.TierId)).Append('\t').Append(Clean(c.TierLabel)).Append('\t').Append(Clean(c.Rarity))
                  .Append('\t').Append(Clean(c.SetName)).Append('\t').Append(c.ShinyArt ? '1' : '0').Append('\n');
            foreach (var kv in Retired) sb.Append("retired\t").Append(Clean(kv.Key)).Append('\t').Append(Clean(kv.Value)).Append('\n');
            foreach (var s in Sets)
            {
                sb.Append("set\t").Append(Clean(s.Id)).Append('\t').Append(Clean(s.Name)).Append('\t').Append(Clean(string.Join(",", s.Aliases))).Append('\t').Append(D(s.Price))
                  .Append('\t').Append(s.Cards.ToString(Inv)).Append('\n');
                for (int i = 0; i < s.Slots.Length; i++)
                {
                    var sl = s.Slots[i];
                    sb.Append("slot\t").Append(Clean(sl.Id)).Append('\t').Append(sl.Count.ToString(Inv)).Append('\t').Append(Clean(sl.Finish)).Append('\t').Append(sl.Distinct ? '1' : '0').Append('\n');
                    for (int o = 0; o < sl.Outcomes.Count; o++)
                    {
                        var oc = sl.Outcomes[o]; var m = s.Meta[i][o];
                        var pool = new string[oc.Pool.Length]; for (int k = 0; k < pool.Length; k++) pool[k] = oc.Pool[k].ToString(Inv);
                        sb.Append("out\t").Append(Clean(oc.Label)).Append('\t').Append(D(oc.Weight)).Append('\t').Append(Clean(oc.Finish)).Append('\t').Append(Clean(m.Fx))
                          .Append('\t').Append(D(m.Rate)).Append('\t').Append(m.Printed.ToString(Inv)).Append('\t').Append(m.Served.ToString(Inv)).Append('\t').Append(m.Base ? '1' : '0')
                          .Append('\t').Append(string.Join(",", pool)).Append('\n');
                    }
                }
            }
            string tmp = file + "." + Guid.NewGuid().ToString("N") + ".tmp";
            System.IO.File.WriteAllText(tmp, sb.ToString(), new System.Text.UTF8Encoding(false));
            if (System.IO.File.Exists(file)) System.IO.File.Replace(tmp, file, null); else System.IO.File.Move(tmp, file);
        }

        /// the index in file, or null when it's missing, unreadable, or its stamp isn't this one
        public static BoosterIndex Load(string file, string stamp)
        {
            if (!System.IO.File.Exists(file)) return null;
            string[] lines;
            try { lines = System.IO.File.ReadAllLines(file, System.Text.Encoding.UTF8); } catch (System.IO.IOException) { return null; }
            if (lines.Length == 0 || lines[0] != "stamp\t" + Clean(stamp)) return null;
            var x = new BoosterIndex { Stamp = stamp };
            BoosterSet set = null; var slots = new List<BoosterSlot>(); var meta = new List<BoosterOutcomeMeta[]>(); var om = new List<BoosterOutcomeMeta>();
            Action close = delegate {
                if (set == null) return;
                if (slots.Count > 0) { meta[meta.Count - 1] = om.ToArray(); }
                set.Slots = slots.ToArray(); set.Meta = meta.ToArray();
            };
            try
            {
                for (int n = 1; n < lines.Length; n++)
                {
                    var f = lines[n].Split('\t');
                    switch (f[0])
                    {
                        case "pack":
                            x.Pack = f[1]; x.ShinyChance = P(f[2]); x.PriceExponent = P(f[3]);
                            foreach (var t in f[4].Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries)) x.PrintedShinyTiers.Add(int.Parse(t, Inv));
                            break;
                        case "card":
                            x.AddCard(new BoosterCard { Id = f[1], Character = f[2], Name = f[3], Number = f[4], Tier = int.Parse(f[5], Inv), TierId = f[6], TierLabel = f[7],
                                                        Rarity = f[8], SetName = f[9], ShinyArt = f[10] == "1" });
                            break;
                        case "retired": x.Retired[f[1]] = f[2]; break;
                        case "set":
                            close();
                            set = new BoosterSet { Id = f[1], Name = f[2], Aliases = f[3].Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries), Price = P(f[4]), Cards = int.Parse(f[5], Inv) };
                            x.Sets.Add(set); slots = new List<BoosterSlot>(); meta = new List<BoosterOutcomeMeta[]>(); om = new List<BoosterOutcomeMeta>();
                            break;
                        case "slot":
                            if (slots.Count > 0) meta[meta.Count - 1] = om.ToArray();
                            slots.Add(new BoosterSlot { Id = f[1], Count = int.Parse(f[2], Inv), Finish = f[3], Distinct = f[4] == "1" });
                            meta.Add(null); om = new List<BoosterOutcomeMeta>();
                            break;
                        case "out":
                            var pool = f[9].Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries);
                            var ix = new int[pool.Length]; for (int k = 0; k < pool.Length; k++) ix[k] = int.Parse(pool[k], Inv);
                            slots[slots.Count - 1].Add(f[1], P(f[2]), ix, f[3]);
                            om.Add(new BoosterOutcomeMeta { Label = f[1], Fx = f[4], Rate = P(f[5]), Printed = int.Parse(f[6], Inv), Served = int.Parse(f[7], Inv), Base = f[8] == "1" });
                            break;
                    }
                }
                close();
            }
            catch (Exception) { return null; }   // a damaged file: rebuilt
            return x;
        }
    }
}
