"""Pull English names from the game's localization TextAssets -> parry/loc.json (read-only)."""
import UnityPy, csv, io, json, pathlib
env = UnityPy.load(__import__("os").environ.get("VALHEIM_DIR", r"C:/Program Files (x86)/Steam/steamapps/common/Valheim") + "/valheim_Data/resources.assets")
loc = {}
for o in env.objects:
    if o.type.name != "TextAsset":
        continue
    t = o.read()
    text = t.m_Script if isinstance(t.m_Script, str) else t.m_Script.decode("utf-8", "ignore")
    if "item_shield_bronzebuckler" not in text and "enemy_troll" not in text:
        continue
    rows = list(csv.reader(io.StringIO(text)))
    head = rows[0]
    en = head.index("English") if "English" in head else 1
    for r in rows[1:]:
        if len(r) > en and r[0] and r[en]:
            loc.setdefault(r[0], r[en])
pathlib.Path(__file__).with_name("loc.json").write_text(json.dumps(loc))
print(len(loc), loc.get("item_shield_bronzebuckler"), loc.get("enemy_troll"))
