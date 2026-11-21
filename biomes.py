"""Spawn tables (SpawnSystemList) + dungeon/location spawners -> parry/biomes.json {prefab: [biome bits]} (read-only)."""
import UnityPy, json, pathlib
env = UnityPy.load(__import__("os").environ.get("VALHEIM_DIR", r"C:/Program Files (x86)/Steam/steamapps/common/Valheim") + "/valheim_Data/StreamingAssets/SoftRef/Bundles/c4210710")
names, mbs = {}, []
for o in env.objects:
    if o.type.name == "GameObject":
        names[o.path_id] = o.read_typetree()["m_Name"]
    elif o.type.name == "MonoBehaviour":
        mbs.append(o)
out = {}
for o in mbs:
    try:
        t = o.read_typetree()
    except Exception:
        continue
    for s in t.get("m_spawners") or []:
        if isinstance(s, dict) and "m_biome" in s and s.get("m_enabled", 1):
            n = names.get(s["m_prefab"]["m_PathID"])
            if n:
                out.setdefault(n.lower(), set()).add(s["m_biome"])
    if "m_locations" in t:
        for l in t["m_locations"]:
            if isinstance(l, dict) and "m_biome" in l:
                out.setdefault("@loc:" + str(l.get("m_prefabName") or l.get("m_prefab", {}).get("m_assetGUID", "")), set()).add(l["m_biome"])
pathlib.Path(__file__).with_name("biomes.json").write_text(json.dumps({k: sorted(v) for k, v in out.items()}, indent=0))
print(len(out))
