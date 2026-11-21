"""Reddit screenshots: parry-check.html + a preset state -> screenshots/*.png via headless Chrome."""
import json, pathlib, subprocess, tempfile
d = pathlib.Path(__file__).parent
out = d.parent / "screenshots"; out.mkdir(exist_ok=True)
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
html = (d / "parry-check.html").read_text(encoding="utf-8")
SHOTS = {
    "parry": {"view": "parry", "biome": "Black Forest", "enemy": "troll", "blocker": "Bronze Buckler", "quality": 1, "skill": 15,
              "foods": ["Deer Stew", "Boar Jerky", "Queen's Jam"], "armor": 24, "diff": 150, "stars": 0, "row": 4},
    "stagger": {"view": "stagger", "biome": "Swamp", "enemy": "draugr_elite", "wpn": "Iron Atgeir", "wq": 2, "wskill": 20, "pdmg": 100, "stars": 0},
}
for name, st in SHOTS.items():
    inject = f"<script>document.documentElement.dataset.theme='dark';Object.assign(S,{json.dumps(st)});initControls=()=>{{}};" \
             "['blocker','wpn'].forEach(i=>$(i).value=S[i]);fillFoods();$('skill').value=S.skill;$('armor').value=S.armor;$('diff').value=S.diff;$('wskill').value=S.wskill;update();</script>"
    page = pathlib.Path(tempfile.gettempdir()) / f"parry-shot-{name}.html"
    page.write_text(html.replace("</script>\n", "</script>\n", 1) + inject, encoding="utf-8")
    subprocess.run([CHROME, "--headless=new", "--hide-scrollbars", "--force-device-scale-factor=2", "--window-size=1440," + ("1640" if name == "parry" else "1180"),
                    "--virtual-time-budget=4000", f"--screenshot={out / (name + '.png')}", page.as_uri()], check=True, capture_output=True)
    print(out / (name + ".png"))
