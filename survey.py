"""Hard-difficulty survey with typical per-biome loadouts (same formulas as the page)."""
import json, pathlib
D = json.load(open(pathlib.Path(__file__).with_name("data.json"), encoding="utf-8"))
P = D["player"]; FOODS = {f["label"]: f for f in D["foods"]}; BL = {b["label"]: b for b in D["blockers"]}
BLK = "blunt slash pierce fire frost lightning poison spirit".split(); STG = "blunt slash pierce lightning".split(); INST = "blunt slash pierce frost lightning".split()
arm = lambda d, ac: d - ac if ac < d / 2 else min(1, d / (ac * 4)) * d
def armor(d, ac):
    t = sum(d.get(k, 0) for k in BLK)
    if ac <= 0 or t <= 0: return dict(d)
    r = arm(t, ac) / t; return {k: v * r if k in BLK else v for k, v in d.items()}
S = lambda d, ks: sum(d.get(k, 0) for k in ks)
LOAD = {  # biome: shield, quality, skill, foods, armor
 "Meadows": ("Wood Shield", 3, 10, ["Cooked Deer Meat", "Cooked Boar Meat", "Grilled Neck Tail"], 20),
 "Black Forest": ("Bronze Buckler", 3, 20, ["Deer Stew", "Minced Meat Sauce", "Cooked Deer Meat"], 36),
 "Swamp": ("Banded Shield", 3, 30, ["Sausages", "Black Soup", "Deer Stew"], 60),
 "Mountains": ("Silver Shield", 3, 40, ["Wolf Skewer", "Sausages", "Wolf Jerky"], 80),
 "Plains": ("Black Metal Shield", 3, 50, ["Lox Meat Pie", "Fish Wraps", "Wolf Skewer"], 90),
 "Mistlands": ("Carapace Shield", 3, 60, ["Misthare Supreme", "Meat Platter", "Honey Glazed Chicken"], 104),
}
def run(biome, stars, diff=1.5):
    sh, q, sk, fs, ac = LOAD[biome]; b = BL[sh]; foods = [FOODS[f] for f in fs]
    base = b["bp"] + (q - 1) * b["bpLvl"]; bp = base * (1 + sk / 200) * (b["parry"] if b["parry"] > 1 else 1)
    hp = lambda t: P["baseHP"] + sum(f["hp"] * t ** 0.3 for f in foods)
    out = []
    for k, e in D["enemies"].items():
        if e["biome"] != biome: continue
        seen = set()
        for a in e["attacks"]:
            if (a["weapon"], a["anim"]) in seen: continue
            seen.add((a["weapon"], a["anim"]))
            for mult, tag in [(a["mult"], "")] + ([(a["mult"] * a["chainLast"], " finisher")] if a["chainLast"] > 1 else []):
                f = (1 + .5 * stars) * mult * diff
                raw = {t: v * f for t, v in a["damage"].items() if t not in ("chop", "pickaxe", "spirit")}
                if not raw: continue
                unb = not a["blockable"] or a["staggerMult"] >= 100
                left = armor(raw, bp); stag = S(left, STG); full = S(armor(raw, ac), INST)
                holds = lambda t: stag < .4 * hp(t) and S(armor(left, ac), INST) < hp(t)
                if unb: n = None
                elif not holds(1): n = 9
                elif holds(0): n = 0
                else:
                    lo, hi = 0, 1
                    for _ in range(25):
                        m = (lo + hi) / 2; lo, hi = (lo, m) if holds(m) else (m, hi)
                    n = hi
                dead = next((i for i in range(101) if full < hp(i / 100)), None)
                out.append((e["label"] + (" (boss)" if e["boss"] else ""), a["weapon"] + tag, round(S(raw, list(raw)), 0), round(stag, 1), round(.4 * hp(1), 1), n, round(full), dead))
    return round(bp, 1), round(hp(1)), out
for biome in LOAD:
    for stars in (0, 2):
        bp, hp1, rows = run(biome, stars)
        bad = [r for r in rows if r[5] is not None and r[5] > .2]
        print(f"\n== {biome} {stars}* bp {bp} maxHP {hp1}  ({len(bad)}/{len([r for r in rows if r[5] is not None])} blockable hits need >20% food)")
        for r in sorted(bad, key=lambda r: -r[5]):
            print(f"  {r[0]:<22} {r[1]:<32} hit {r[2]:>5} past {r[3]:>6} lim {r[4]:>5} need {'NEVER' if r[5]==9 else f'{r[5]*100:.0f}%':>5} full {r[6]:>4} oneshot<{r[7] if r[7] is not None else 'always'}%")
