// pokeshell booster packs: the roll of one whole real booster (packs/<pack>/boosters.json, docs/BOOSTERS.md).
//
// PowerShell (lib\booster.ps1) reads boosters.json + pack.json and hands this file a flat model: the pack's slots,
// each with its outcomes (a label, an effective weight, the pool of card indices it draws from, the finish).
// This file only does the dice, so the 20k-pack Monte Carlo in tests\test-boosters.ps1 runs in well under a second.
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
    }
}
