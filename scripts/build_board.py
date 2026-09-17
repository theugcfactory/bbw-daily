#!/usr/bin/env python3
"""Build the Built By Will daily creative board.

Usage:
  python3 scripts/build_board.py spec.json boards/YYYY-MM-DD.jpg

spec.json:
{
  "row1_label": "1D — top ads yesterday (Tue Sep 16)",
  "row2_label": "7D — top ads last 7 days (Sep 10–16)",
  "row1": [ {"name": "...", "kind": "static|video", "spend": 19.03, "leads": 0, "cpl": null, "image_url": "https://..."} , ... up to 5 ],
  "row2": [ ... up to 5 ]
}
Cards are ranked left to right in the order given. Images are downloaded directly (no credentials needed for fbcdn URLs).
"""
import json, sys, urllib.request, hashlib, os
from PIL import Image, ImageDraw, ImageFont

B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
R = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
CW, CH, G, LBL, PAD = 432, 540, 14, 110, 24
SUB = "ranked by leads, then CPL, then spend · $1+ spend"


def fetch(url):
    p = '/tmp/board_' + hashlib.md5(url.encode()).hexdigest() + '.img'
    if not os.path.exists(p):
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as r, open(p, 'wb') as f:
            f.write(r.read())
    return Image.open(p).convert('RGB')


def card(a, rank):
    im = fetch(a['image_url']).resize((1080, 1350))
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    fv = ImageFont.truetype(B, 52)
    fs = ImageFont.truetype(B, 34)
    leads = int(a.get('leads') or 0)
    l1 = f"${a['spend']:,.2f} · {leads} lead{'s' if leads != 1 else ''}"
    l2 = f"${a['cpl']:,.2f} CPL" if a.get('cpl') is not None else "— CPL"
    pad = 30
    w = max(d.textlength(l1, font=fv), d.textlength(l2, font=fv)) + pad * 2
    h = pad * 2 + 52 + 52 + 16
    d.rounded_rectangle([40, 40, 40 + w, 40 + h], radius=24, fill=(0, 0, 0, 238))
    d.text((40 + pad, 40 + pad), l1, fill='white', font=fv)
    d.text((40 + pad, 40 + pad + 68), l2, fill=(255, 214, 0, 255), font=fv)
    d.rounded_rectangle([1080 - 40 - 96, 40, 1080 - 40, 136], radius=24, fill=(255, 214, 0, 245))
    fr = ImageFont.truetype(B, 58)
    t = str(rank)
    tw = d.textlength(t, font=fr)
    d.text((1080 - 40 - 48 - tw / 2, 54), t, fill='black', font=fr)
    d.rectangle([0, 1350 - 78, 1080, 1350], fill=(0, 0, 0, 225))
    name = a['name']
    fn = fs
    while d.textlength(f"{name}  ·  {a.get('kind','')}", font=fn) > 1000 and fn.size > 20:
        fn = ImageFont.truetype(B, fn.size - 2)
    d.text((40, 1350 - 60), f"{name}  ·  {a.get('kind','')}", fill='white', font=fn)
    out = Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')
    out.thumbnail((CW, CH))
    return out


def main(spec_path, out_path):
    spec = json.load(open(spec_path))
    W = PAD * 2 + 5 * CW + 4 * G
    H = PAD * 2 + 2 * (LBL + CH) + G
    sheet = Image.new('RGB', (W, H), '#0f0f0f')
    D = ImageDraw.Draw(sheet)
    fl = ImageFont.truetype(B, 40)
    fsub = ImageFont.truetype(R, 24)
    rows = [(spec['row1_label'], spec['row1']), (spec['row2_label'], spec['row2'])]
    for r, (label, row) in enumerate(rows):
        y = PAD + r * (LBL + CH + G)
        D.text((PAD, y + 14), label, fill='white', font=fl)
        D.text((PAD, y + 66), SUB if r == 0 else "same ranking", fill=(170, 170, 170), font=fsub)
        for i, a in enumerate(row[:5]):
            sheet.paste(card(a, i + 1), (PAD + i * (CW + G), y + LBL))
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    sheet.save(out_path, quality=88)
    print(out_path, sheet.size)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
