"""Status effects that change damage taken (SE_Stats m_mods) -> parry/se.json, keyed "@<pathID>" like prefabs.json refs."""
import UnityPy, json, os, pathlib
D = os.environ.get("VALHEIM_DIR", r"C:/Program Files (x86)/Steam/steamapps/common/Valheim")
env = UnityPy.load(D + "/valheim_Data/StreamingAssets/SoftRef/Bundles/c4210710")
out = {}
for o in env.objects:
    if o.type.name != "MonoBehaviour":
        continue
    try:
        mb = o.read_typetree()
    except Exception:
        continue
    if "m_mods" in mb and "m_name" in mb:
        out["@" + str(o.path_id)] = {"name": mb["m_name"], "obj": mb.get("m_Name", ""), "tooltip": mb.get("m_tooltip", ""),
                                     "mods": [m for m in mb["m_mods"] if m["m_modifier"]],
                                     "stagger": mb.get("m_staggerModifier", 0)}
pathlib.Path(__file__).with_name("se.json").write_text(json.dumps(out, indent=0), encoding="utf-8")
print(len(out), "status effects with damage mods")
