"""prefabs.json + loc.json -> parry/data.json: enemy attacks per biome, blockers, foods, player constants."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
comps = json.load(open(ROOT / "prefabs.json", encoding="utf-8"))
L = json.load(open(ROOT / "parry" / "loc.json", encoding="utf-8"))
en = lambda k: L.get((k or "").lstrip("$"), "").replace(chr(0xfffd), "a")
by = {}
it_names = {}
for c in comps:
    by.setdefault(c["path"].lower(), {})[c["class"]] = c["data"]
    it_names[c["path"].lower()] = c["path"]

DT = ["m_blunt", "m_slash", "m_pierce", "m_chop", "m_pickaxe", "m_fire", "m_frost", "m_lightning", "m_poison", "m_spirit"]
dmg = lambda d: {k[2:]: round(d.get(k, 0), 2) for k in DT if d.get(k, 0)}

def shared(name):
    it = by.get(name.lower(), {}).get("ItemDrop")
    return it and it["m_itemData"]["m_shared"]

def aoe_of(prefab):
    """Damage an attack-spawned prefab deals on its own (only when it ignores the attack's damage)."""
    if not prefab or prefab.startswith("@"):
        return None
    for cls, d in by.get(prefab.lower(), {}).items():
        if "Aoe" in cls and not d.get("m_useAttackSettings", 1):
            return {"damage": dmg(d["m_damage"]), "blockable": d["m_blockable"], "prefab": prefab}
    return None

def attacks(weapon):
    s = shared(weapon)
    if not s:
        return []
    out = []
    for key in ("m_attack", "m_secondaryAttack"):
        a = s.get(key) or {}
        if not a.get("m_attackAnimation"):
            continue
        hit = {"weapon": weapon, "anim": a["m_attackAnimation"], "label": en(s["m_name"]),
               "damage": dmg(s["m_damages"]), "mult": a.get("m_damageMultiplier", 1),
               "blockable": s["m_blockable"],
               "chainLast": a.get("m_lastChainDamageMultiplier", 1) if a.get("m_attackChainLevels", 0) > 1 else 1,
               "ranged": bool(a.get("m_attackProjectile")), "staggerMult": a.get("m_staggerMultiplier", 1)}
        spawned = aoe_of(a.get("m_attackProjectile")) or aoe_of(a.get("m_spawnOnTrigger"))
        if spawned:
            hit["aoe"] = spawned
        out.append(hit)
    return out

BIOMES = {  # curated from parry/biomes.json spawn tables + known locations; "?" = biome guessed
    "Meadows": "greyling neck boar skeleton_meadows eikthyr",
    "Black Forest": "greydwarf greydwarf_elite greydwarf_shaman troll bjorn skeleton ghost skeleton_hildir gd_king",
    "Swamp": "draugr draugr_elite draugr_ranged skeleton_swamps skeleton_poison blob blobelite leech wraith abomination writhan surtling bogwitchkvastur bonemass",
    "Mountains": "wolf fenring fenring_cultist ulv hatchling stonegolem bat skeleton_mountains fenring_cultist_hildir dragon",
    "Plains": "goblin goblinarcher goblinbrute goblinshaman deathsquito lox blobtar unbjorn goblinbrutebros goblinking",
    "Mistlands": "seeker seekerbrood seekerbrute tick gjall dverger dvergermagefire dvergermageice seekerqueen",
    "Ashlands": "charred_melee charred_archer charred_mage charred_twitcher asksvin volture fallenvalkyrie morgen_nonsleeping bonemawserpent dvergerashlands blobmork? charred_melee_dyrnwyn fader",
    "Deep North": "greydwarf_frozen greydwarf_shaman_frozen skeleton_deepnorth elaking elakinglantern elakingmole? jotunwarrior jotunwarriordualwield jotunwitch trollfrost barka moose shadowperson frysling? blobfrost? dvergerdeepnorth? goblindeepnorth? fallenwarrior? frozenking?",
    "Ocean": "serpent",
}
BOSSES = {"eikthyr", "gd_king", "bonemass", "dragon", "goblinking", "seekerqueen", "fader", "frozenking"}

def clean(name):
    return name.split(">")[1].split("<")[0].strip() if "<color" in name else name

enemies = {}
for biome, names in BIOMES.items():
    for n in names.split():
        guess, n = n.endswith("?"), n.rstrip("?")
        cl = by[n]
        ch = cl.get("Character+Humanoid") or cl.get("Character")
        weapons = set(ch.get("m_defaultItems") or []) | set(ch.get("m_randomWeapon") or [])
        for st in ch.get("m_randomSets") or []:
            weapons |= set(st["m_items"])
        atk = [a for w in sorted(x for x in weapons if x and not x.startswith("@")) for a in attacks(w)]
        atk = [a for a in atk if sum(a["damage"].values()) or a.get("aoe")]
        assert atk, n
        mods = ch["m_damageModifiers"]
        enemies[n] = {"label": clean(en(ch["m_name"])), "biome": biome, "guess": guess, "boss": n in BOSSES,
                      "health": ch["m_health"], "attacks": atk, "stagF": ch["m_staggerDamageFactor"],
                      "mods": {k: mods["m_" + k] for k in ("blunt", "slash", "pierce", "lightning")}}

# player melee weapons for the Stagger view (Attack.DoMeleeAttack / DoAreaAttack)
SKILLS = {1: "Swords", 2: "Knives", 3: "Clubs", 4: "Polearms", 5: "Spears", 7: "Axes", 11: "Fists"}
def swing(s, a, name, mult):
    return {"name": name, "mult": mult, "stag": a["m_staggerMultiplier"], "area": a["m_attackType"] == 4,
            "split": bool(a["m_multiHit"] and a["m_lowerDamagePerHit"]), "thru": bool(a["m_hitThroughWalls"]),
            "angle": a["m_attackAngle"], "range": round(a["m_attackRange"], 2), "height": a["m_attackHeight"],
            "width": round(a["m_attackRayWidth"], 2), "flat": a["m_maxYAngle"] == 0, "vertical": a["m_attackType"] == 1}
weapons = {}
for path, cl in by.items():
    it = cl.get("ItemDrop")
    if not it or "/" in path or it_names[path].startswith(("FW_", "SP_")):
        continue
    s = it["m_itemData"]["m_shared"]
    if s["m_skillType"] not in SKILLS or s["m_itemType"] not in (3, 14, 22) or s["m_attack"]["m_attackType"] not in (0, 1, 4):
        continue
    if not (s["m_name"].startswith("$item_") or path == "playerunarmed"):
        continue
    label = en(s["m_name"]) or "Unarmed"
    if not label or "UNUSED" in label:
        continue
    a, b = s["m_attack"], s["m_secondaryAttack"]
    sw = [swing(s, a, "Light attack", a["m_damageMultiplier"])]
    if a.get("m_attackChainLevels", 0) > 1 and a["m_lastChainDamageMultiplier"] != 1:
        sw.append(swing(s, a, "Light combo finisher", a["m_damageMultiplier"] * a["m_lastChainDamageMultiplier"]))
    if b.get("m_attackAnimation") and b["m_attackType"] in (0, 1, 4):
        sw.append(swing(s, b, "Special", b["m_damageMultiplier"]))
    if not any(s["m_damages"]["m_" + k] for k in ("blunt", "slash", "pierce", "lightning")):
        continue
    weapons[label] = {"id": it_names[path], "label": label, "skill": s["m_skillType"], "skillName": SKILLS[s["m_skillType"]],
                      "maxQ": s["m_maxQuality"], "damage": dmg(s["m_damages"]), "perLvl": dmg(s["m_damagesPerLevel"]), "swings": sw}

blockers, foods, armor = [], [], {}
for path, cl in by.items():
    it = cl.get("ItemDrop")
    if not it or "/" in path:
        continue
    s = it["m_itemData"]["m_shared"]
    t, label = s["m_itemType"], en(s["m_name"])
    it_name = it_names[path]
    if t in (6, 7, 11, 17) and s["m_armor"] > 0:  # helmet, chest, legs, shoulder = GetBodyArmor slots
        armor[it_name] = [s["m_armor"], s["m_armorPerLevel"]]
    if not s["m_name"].startswith("$item_") or not label or "UNUSED" in label:
        continue
    if s["m_blockPower"] > 0 and t in (3, 4, 5, 14, 22):
        blockers.append({"id": it_name, "label": label, "shield": t == 5, "bp": s["m_blockPower"], "bpLvl": s["m_blockPowerPerLevel"], "maxQ": s["m_maxQuality"],
                         "parry": s["m_timedBlockBonus"], "mods": {m["m_type"]: m["m_modifier"] for m in s["m_damageModifiers"]},
                         "staminaMod": s.get("m_blockStaminaModifier", 0)})
    if t == 2 and (s["m_food"] > 0 or s["m_foodStamina"] > 0 or s["m_foodEitr"] > 0):
        hp, st, ei = s["m_food"], s["m_foodStamina"], s["m_foodEitr"]
        # same colour rule as the inventory icon (InventoryGrid); feasts are the 50-minute foods
        kind = ("Feasts" if s["m_foodBurnTime"] >= 3000 else "Eitr" if hp < ei / 2 and st < ei / 2
                else "Health" if st < hp / 2 else "Stamina" if hp < st / 2 else "Balanced")
        foods.append({"id": it_name, "label": label, "hp": hp, "st": st, "eitr": ei, "burn": s["m_foodBurnTime"], "kind": kind})

p = by["player"]["Character+Humanoid"]
out = {"player": {k[2:]: p[k] for k in ("m_baseHP", "m_baseStamina", "m_staggerDamageFactor", "m_blockStaminaDrain")},
       "biomes": list(BIOMES), "enemies": enemies, "armor": armor,
       "weapons": sorted(weapons.values(), key=lambda w: (w["skillName"], sum(w["damage"].values()))),
       "blockers": sorted({b["label"]: b for b in blockers}.values(), key=lambda b: (not b["shield"], b["bp"])),
       "foods": sorted({f["label"]: f for f in foods}.values(), key=lambda f: -f["hp"])}
(ROOT / "parry" / "data.json").write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
print(len(enemies), "enemies", len(out["blockers"]), "blockers", len(out["foods"]), "foods")
