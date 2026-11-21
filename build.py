"""template.html + data.json -> parry-check.html"""
import pathlib
d = pathlib.Path(__file__).parent
html = (d / "template.html").read_text(encoding="utf-8").replace("/*DATA*/null", (d / "data.json").read_text(encoding="utf-8"))
fch = (d / "fch.js").read_text(encoding="utf-8").replace('if (typeof module !== "undefined") module.exports = { readFch, stableHash };', "")
html = html.replace("/*FCH*/", fch)
(d / "parry-check.html").write_text(html, encoding="utf-8")
(d / "index.html").write_text(html, encoding="utf-8")  # GitHub Pages entry
print(len(html))
