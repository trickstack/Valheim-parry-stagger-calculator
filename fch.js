// Valheim character file (.fch) reader: equipped items, foods with time left, skills.
// Format from decompiled PlayerProfile.LoadPlayerFromDisk / Player.Save / Inventory.Save / ItemData.Save / Skills.Save.
function stableHash(s) { // String.GetStableHashCode
  let a = 5381, b = 5381;
  for (let i = 0; i < s.length; i += 2) {
    a = (Math.imul(a, 33) ^ s.charCodeAt(i)) | 0;
    if (i === s.length - 1) break;
    b = (Math.imul(b, 33) ^ s.charCodeAt(i + 1)) | 0;
  }
  return (a + Math.imul(b, 1566083941)) | 0;
}

function readFch(buf) {
  const u8 = new Uint8Array(buf), dv = new DataView(u8.buffer, u8.byteOffset, u8.byteLength);
  const dataLen = dv.getInt32(0, true), end = 4 + dataLen;
  // the profile's last field is bool(1) + byte[] playerData, so find it from the end
  let p = -1;
  for (let i = end - 8; i > 4; i--) if (u8[i - 1] === 1 && dv.getInt32(i, true) === end - i - 4) { p = i + 4; break; }
  if (p < 0) throw new Error("no player data in this file");
  let o = p;
  const int = () => { const v = dv.getInt32(o, true); o += 4; return v; };
  const f32 = () => { const v = dv.getFloat32(o, true); o += 4; return v; };
  const u16 = () => { const v = dv.getUint16(o, true); o += 2; return v; };
  const byte = () => u8[o++];
  const str = () => {
    let n = 0, shift = 0, b;
    do { b = byte(); n |= (b & 127) << shift; shift += 7; } while (b & 128);
    const s = new TextDecoder().decode(u8.subarray(o, o + n)); o += n; return s;
  };
  const strings = () => { const n = int(); for (let i = 0; i < n; i++) str(); };
  const ver = int();
  if (ver < 28) throw new Error("character saved by an older game version (" + ver + "); log in and save once");
  const maxHP = f32(), hp = f32(), maxStamina = f32(); f32(); str(); f32();
  const items = [], invVer = int();
  if (invVer < 108) throw new Error("old inventory format (" + invVer + "); log in and save once");
  const nItems = u16();
  for (let i = 0; i < nItems; i++) {
    const it = { durability: int() / 100, x: byte(), y: byte() }; o += 1; const fl = byte(); // y 0 = hotbar
    it.equipped = !!(fl & 2);
    it.quality = fl & 4 ? u16() : 1;
    if (fl & 8) u16();
    if (fl & 16) int();
    if (fl & 32) { o += 8; str(); }
    it.hash = fl & 64 ? int() : 0;
    if (fl & 128) { let n = byte(); if (n & 128) n = ((n & 127) << 8) | byte(); for (let k = 0; k < n; k++) { str(); str(); } }
    if (invVer >= 109 || invVer === 107) byte();
    items.push(it);
  }
  strings(); // known recipes
  { const n = int(); for (let i = 0; i < n; i++) { str(); int(); } } // stations
  strings(); strings(); strings(); strings(); // materials, tutorials, uniques, trophies
  if (ver >= 33 || ver === 31) strings(); else { const n = int(); o += 4 * n; } // biomes
  { const n = int(); for (let i = 0; i < n; i++) { str(); str(); } } // texts
  str(); str(); o += 24; int(); // beard, hair, colours, model
  const foods = [];
  { const n = int(); for (let i = 0; i < n; i++) foods.push({ name: str(), time: f32() }); }
  const skills = {};
  { int(); const n = int(); for (let i = 0; i < n; i++) { const t = int(); skills[t] = f32(); f32(); } }
  return { maxHP, hp, maxStamina, items, foods, skills };
}
if (typeof module !== "undefined") module.exports = { readFch, stableHash };
