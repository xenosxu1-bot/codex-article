# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse, base64, json, os, re, sys, textwrap, time, urllib.error, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parents[1]
IMG_DIR = REPO / "08-\u7d20\u6750\u5e93" / "\u56fe\u7247"
BASE_DIR = IMG_DIR / "\u5c01\u9762\u5e95\u56fe"
COVER_DIR = IMG_DIR / "\u6587\u7ae0\u5c01\u9762"
RECORD = REPO / "07-\u8d44\u6599\u4e0e\u6d41\u7a0b" / "\u56fe\u7247\u751f\u6210\u8bb0\u5f55.md"
FONT = Path(r"C:\Windows\Fonts\msyh.ttc")
BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")

PAL = {
    "bg": (2, 8, 22),
    "white": (248, 252, 255),
    "muted": (184, 204, 236),
    "blue": (59, 167, 255),
    "cyan": (24, 224, 255),
    "violet": (139, 92, 246),
}
PALETTES = {
    "dev": "black and deep navy gradient, electric cyan, restrained cobalt blue, soft violet purple, professional white highlights",
    "security": "black navy and deep teal gradient, cyan green, amber accents, cool white highlights",
    "content": "midnight indigo and purple-black gradient, magenta violet, soft cyan, subtle coral highlights",
    "research": "deep blue and blue-gray gradient, violet, cyan, soft white data glow",
    "business": "deep navy and graphite gradient, blue green, subtle gold accents, premium white highlights",
}
DEFAULT_TITLE = "\u522b\u518d\u53ea\u4f1a\u95ee AI\\n\u638c\u63e1 AI \u5f00\u53d1\u5de5\u4f5c\u6d41"
DEFAULT_SUBTITLE = "\u628a AI \u53d8\u6210\u53ef\u4ea4\u4ed8\u5de5\u4f5c\u6d41"
DEFAULT_TAGS = "\u63d2\u4ef6\u6269\u5c55,Skill\u6c89\u6dc0,\u5de5\u4f5c\u6d41\u96c6\u6210,\u56e2\u961f\u5171\u4eab"
DEFAULT_STEM_TITLE = "10-\u522b\u518d\u53ea\u4f1a\u95ee AI\uff1a2026 \u5e74\u6700\u503c\u5f97\u638c\u63e1\u7684\uff0c\u662f\u628a AI \u53d8\u6210\u53ef\u4ea4\u4ed8\u5de5\u4f5c\u6d41"


def load_env() -> None:
    for ep in [REPO / ".env", REPO.parent.parent / ".env"]:
        if not ep.exists():
            continue
        for raw in ep.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip().lstrip("\ufeff")
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


def safe(s: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "-", s).strip()[:120]


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def parse_size(text: str) -> tuple[int, int]:
    a, b = text.lower().split("x", 1)
    return int(a), int(b)


def fit(im: Image.Image, canvas: tuple[int, int]) -> Image.Image:
    im = im.convert("RGB")
    tw, th = canvas
    target = tw / th
    cur = im.width / im.height
    if cur > target:
        nw = int(im.height * target)
        x = (im.width - nw) // 2
        im = im.crop((x, 0, x + nw, im.height))
    else:
        nh = int(im.width / target)
        y = max(0, (im.height - nh) // 2)
        im = im.crop((0, y, im.width, y + nh))
    return im.resize(canvas, Image.Resampling.LANCZOS)


def draw_icon(d: ImageDraw.ImageDraw, kind: str, cx: int, cy: int, color, scale: float = 1.0) -> None:
    w = max(2, int(3.4 * scale)); r = int(12 * scale)
    if kind == "plugin":
        d.rounded_rectangle((cx-r,cy-r,cx+r,cy+r), radius=int(4*scale), outline=color, width=w)
        d.rectangle((cx-int(4*scale),cy-r-int(5*scale),cx+int(4*scale),cy-r+int(3*scale)), fill=color)
        d.rectangle((cx-int(4*scale),cy+r-int(3*scale),cx+int(4*scale),cy+r+int(5*scale)), fill=color)
    elif kind == "skill":
        pts=[(cx,cy-r-int(4*scale)),(cx+int(7*scale),cy-int(2*scale)),(cx+r+int(4*scale),cy),(cx+int(7*scale),cy+int(2*scale)),(cx,cy+r+int(4*scale)),(cx-int(7*scale),cy+int(2*scale)),(cx-r-int(4*scale),cy),(cx-int(7*scale),cy-int(2*scale))]
        d.polygon(pts, fill=color)
    elif kind == "workflow":
        rr=int(5*scale)
        for dx,dy in [(-r,-r),(r,-r),(0,r)]:
            d.ellipse((cx+dx-rr,cy+dy-rr,cx+dx+rr,cy+dy+rr), outline=color, width=w)
        d.line((cx-r+rr,cy-r,cx+r-rr,cy-r), fill=color, width=w)
        d.line((cx-r+int(2*scale),cy-r+rr,cx-int(2*scale),cy+r-rr), fill=color, width=w)
        d.line((cx+r-int(2*scale),cy-r+rr,cx+int(2*scale),cy+r-rr), fill=color, width=w)
    else:
        d.pieslice((cx-r,cy-r,cx+r,cy+r),205,335, fill=color)
        d.polygon([(cx-int(2*scale),cy),(cx+r+int(6*scale),cy-int(8*scale)),(cx+r-int(2*scale),cy+int(10*scale))], fill=color)


def gradient_text(base: Image.Image, xy, text: str, ft, c1, c2, canvas) -> None:
    x, y = xy
    mask = Image.new("L", canvas, 0)
    md = ImageDraw.Draw(mask)
    md.text((x, y), text, font=ft, fill=255)
    x0, y0, x1, y1 = md.textbbox((x, y), text, font=ft)
    width = max(1, x1 - x0)
    grad = Image.new("RGBA", canvas, (0,0,0,0))
    gd = ImageDraw.Draw(grad)
    for xx in range(x0, x1 + 1):
        t = (xx - x0) / width
        col = tuple(int(c1[i]*(1-t)+c2[i]*t) for i in range(3))
        gd.line((xx, y0, xx, y1), fill=(*col,255), width=1)
    base.alpha_composite(Image.composite(grad, Image.new("RGBA", canvas, (0,0,0,0)), mask))


def overlay(base_path: Path, out_path: Path, title: str, subtitle: str, tags: list[str], canvas: tuple[int,int]) -> None:
    im = fit(Image.open(base_path), canvas).convert("RGBA")
    w,h = canvas; sx=w/1792; sy=h/764; s=min(sx,sy)
    ov = Image.new("RGBA", canvas, (0,0,0,0)); d=ImageDraw.Draw(ov)
    # Stronger left reading area and slight right dimming so title remains first focus.
    for x in range(0, min(w, int(w*0.72))):
        t = x / max(1, int(w*0.72))
        d.line((x,0,x,h), fill=(*PAL["bg"], int(252*(1-t)**1.65 + 18)), width=1)
    d.rectangle((int(w*0.58),0,w,h), fill=(0,0,0,26))
    im = Image.alpha_composite(im, ov); d=ImageDraw.Draw(im)

    mx,my=int(62*sx),int(58*sy); r=int(28*s)
    pts=[(mx+r,my),(mx+int(1.7*r),my+int(.45*r)),(mx+int(1.7*r),my+int(1.35*r)),(mx+r,my+int(1.8*r)),(mx+int(.3*r),my+int(1.35*r)),(mx+int(.3*r),my+int(.45*r))]
    d.polygon(pts, fill=(4,14,32,225), outline=(*PAL["blue"],220))
    d.line((mx+int(.72*r),my+int(.62*r),mx+int(1.02*r),my+int(.90*r),mx+int(.72*r),my+int(1.18*r)), fill=PAL["cyan"], width=max(3,int(5*s)))
    d.line((mx+int(1.12*r),my+int(1.24*r),mx+int(1.36*r),my+int(1.24*r)), fill=PAL["violet"], width=max(3,int(5*s)))
    d.text((mx+int(78*s), my+int(12*s)), "AI Workbench", font=font(BOLD, max(28,int(39*s))), fill=(*PAL["white"],250))

    lines=[x.strip() for x in title.replace("\\n","\n").split("\n") if x.strip()]
    tx,ty=int(54*sx),int(172*sy)
    if lines:
        d.text((tx,ty), lines[0], font=font(BOLD,max(58,int(86*s))), fill=(*PAL["white"],255))
    if len(lines) > 1:
        gradient_text(im, (tx, ty+int(94*s)), lines[1], font(BOLD,max(52,int(72*s))), PAL["blue"], PAL["violet"], canvas)
    d.text((tx, int(405*sy)), subtitle, font=font(BOLD,max(34,int(45*s))), fill=(*PAL["white"],245))

    # Compact keyword-only bottom tag bar.
    tags=(tags+["\u63d2\u4ef6\u6269\u5c55","Skill\u6c89\u6dc0","\u5de5\u4f5c\u6d41\u96c6\u6210","\u56e2\u961f\u5171\u4eab"])[:4]
    bar=(int(42*sx), int(560*sy), int(800*sx), int(650*sy))
    d.rounded_rectangle(bar, radius=max(10,int(16*s)), fill=(7,18,42,158), outline=(*PAL["blue"],96), width=max(1,int(1.2*s)))
    slot=(bar[2]-bar[0])/4
    kinds=["plugin","skill","workflow","share"]; cols=[PAL["blue"],PAL["violet"],PAL["cyan"],PAL["violet"]]
    tf=font(BOLD,max(20,int(25*s))); icon_box=int(30*s); gap=int(10*s)
    for i,tag in enumerate(tags):
        x0=int(bar[0]+i*slot); x1=int(bar[0]+(i+1)*slot); cx=(x0+x1)//2; cy=(bar[1]+bar[3])//2
        bb=d.textbbox((0,0),tag,font=tf); tw=bb[2]-bb[0]; th=bb[3]-bb[1]
        gw=icon_box+gap+tw; gx=int(cx-gw/2)
        draw_icon(d,kinds[i],gx+icon_box//2,cy,cols[i],max(.55,s*.78))
        d.text((gx+icon_box+gap, int(cy-th/2)-int(2*s)), tag, font=tf, fill=(*PAL["white"],248))
        if i:
            d.line((x0,bar[1]+int(18*sy),x0,bar[3]-int(18*sy)), fill=(*PAL["blue"],42), width=1)

    d.rounded_rectangle((6,6,w-7,h-7), radius=max(14,int(22*s)), outline=(*PAL["blue"],105), width=max(1,int(1.5*s)))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(out_path, quality=96)


def build_prompt(theme: str, palette_key: str) -> str:
    palette = PALETTES.get(palette_key, PALETTES["dev"])
    return textwrap.dedent(f"""
    Generate a premium WeChat technology article cover background, final crop ratio 2.35:1.
    CRITICAL: no readable text, no Chinese or English words, no brand names, no logos, no QR codes, no watermarks, no screenshots or trademarks.

    Layout: leave the left 55 to 60 percent as clean dark negative space for later Chinese title and subtitle overlay. The bottom-left area must stay calm for a compact four-keyword tag bar.

    Right side: include exactly 3 core visuals only:
    1) a dim semi-transparent code/control panel as a background layer,
    2) a clear three-node workflow chain showing input -> orchestration -> delivery with large icon-only nodes,
    3) a subdued glowing delivery core or cube.
    Avoid five-node chains, scattered cards, dense side panels, extra floating modules, excessive data streams, busy floor grids, strong center glow, and over-stacked UI elements. The right side must support the title, not compete with it.

    Style: 2026 AI technology product launch keynote visual, premium technology magazine cover, professional AI developer ecosystem, dark futuristic UI, AI Agent, developer workspace, neon blue purple lighting, premium SaaS product design, Apple keynote-level restraint, OpenAI Codex-like mood without copying any real brand or UI.

    Background: black plus deep navy gradient, subtle particle glow, faint data streams, restrained code light trails, ambient rim light. High-end, restrained, professional, futuristic, cinematic.
    Color palette: {palette}. Article theme: {theme}.
    Quality: high-resolution commercial illustration, cinematic lighting, realistic software product presentation. Keep lighting restrained: left title should remain the brightest reading focus, right-side delivery core glow must be subdued. Avoid cartoon style, flashy background, low-quality text, clutter, cheap cyberpunk, copied brands or logos.
    """).strip()


def validate_style_spec(args: argparse.Namespace, canvas: tuple[int,int]) -> None:
    w,h=canvas; ratio=w/h
    tags=[x.strip() for x in re.split(r"[,，]", args.tags) if x.strip()]
    problems=[]
    if abs(ratio-2.35)>0.025: problems.append(f"ratio should be about 2.35:1, got {ratio:.3f}")
    if not args.title.strip() or not args.subtitle.strip(): problems.append("title and subtitle are required")
    if len(tags)!=4: problems.append(f"exactly 4 bottom keywords required, got {len(tags)}")
    if any(len(t)>8 for t in tags): problems.append("bottom keywords should be short")
    if problems: raise RuntimeError("style precheck failed:\n- " + "\n- ".join(problems))
    print("style precheck passed: 2.35:1, clear title hierarchy, left 55-60% clean title/subtitle area, right 3 theme visuals, compact bottom 4 keywords, AI tech style.")


def redact(x: str) -> str:
    return re.sub(r"sk-[A-Za-z0-9_\-\*]{8,}", "sk-***REDACTED***", x)


def call_api(prompt: str, out: Path) -> None:
    key=os.environ.get("OPENAI_API_KEY")
    if not key or "请在这里" in key: raise RuntimeError("OPENAI_API_KEY missing")
    base=os.environ.get("OPENAI_BASE_URL","https://api.openai.com/v1").rstrip("/")
    endpoint=f"{base}/images/generations"
    payload={"model":os.environ.get("OPENAI_IMAGE_MODEL","gpt-image-2"),"prompt":prompt,"size":os.environ.get("OPENAI_IMAGE_SIZE","1536x1024"),"n":1}
    q=os.environ.get("OPENAI_IMAGE_QUALITY","high")
    if q: payload["quality"]=q
    req=urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"}, method="POST")
    print("image endpoint: "+endpoint)
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            body=json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"image API failed HTTP {e.code}\n{redact(e.read().decode('utf-8',errors='replace'))}")
    item=body.get("data",[{}])[0]
    if item.get("b64_json"):
        out.write_bytes(base64.b64decode(item["b64_json"]))
    elif item.get("url"):
        with urllib.request.urlopen(item["url"], timeout=240) as r: out.write_bytes(r.read())
    else:
        raise RuntimeError("image response has no b64_json or url")


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--title", default=DEFAULT_TITLE)
    parser.add_argument("--subtitle", default=DEFAULT_SUBTITLE)
    parser.add_argument("--tags", default=DEFAULT_TAGS)
    parser.add_argument("--theme", default="AI developer workflow, deliverable AI workbench")
    parser.add_argument("--palette", default="dev", choices=sorted(PALETTES))
    parser.add_argument("--output-size", default="1792x764")
    parser.add_argument("--stem", default=DEFAULT_STEM_TITLE)
    parser.add_argument("--skip-api", action="store_true")
    args=parser.parse_args()
    load_env(); canvas=parse_size(args.output_size); validate_style_spec(args, canvas)
    BASE_DIR.mkdir(parents=True, exist_ok=True); COVER_DIR.mkdir(parents=True, exist_ok=True); RECORD.parent.mkdir(parents=True, exist_ok=True)
    stem=safe(args.stem); base=BASE_DIR/(stem+"-gpt-image\u5e95\u56fe.png"); cover=COVER_DIR/(stem+"-\u5c01\u9762.png"); pf=BASE_DIR/(stem+"-gpt-image\u63d0\u793a\u8bcd.txt")
    pr=build_prompt(args.theme, args.palette); pf.write_text(pr, encoding="utf-8"); print("prompt saved: "+str(pf))
    if not args.skip_api:
        print("generating with: "+os.environ.get("OPENAI_IMAGE_MODEL","gpt-image-2")); call_api(pr, base); print("base generated: "+str(base))
    elif not base.exists():
        raise FileNotFoundError(str(base))
    tags=[x.strip() for x in re.split(r"[,，]", args.tags) if x.strip()]
    overlay(base, cover, args.title, args.subtitle, tags, canvas); print("cover generated: "+str(cover))
    if not RECORD.exists(): RECORD.write_text("# image generation record\n\n", encoding="utf-8")
    with RECORD.open("a", encoding="utf-8") as f:
        f.write(f"\n## {time.strftime('%Y-%m-%d %H:%M:%S')} - cover regenerated\n\n- model: {os.environ.get('OPENAI_IMAGE_MODEL','gpt-image-2')}\n- size: {canvas[0]} x {canvas[1]}\n- style: clear title hierarchy, compact bottom keywords, right side exactly 3 visuals\n- base: `{base.relative_to(REPO).as_posix()}`\n- cover: `{cover.relative_to(REPO).as_posix()}`\n")

if __name__ == "__main__":
    main()


