# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse, hashlib, json, os, re, sys, textwrap, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from ccswitch_image import generate_image

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
LAYOUT_VARIANTS = {
    "left_title_right_visual": "left title-safe editorial poster; article-specific visual subject on the right",
    "center_title_hero": "centered quiet title area with one restrained hero object",
    "top_title_bottom_system": "top title area, lower visual system or action loop",
    "split_before_after": "two-state contrast that shows a before-to-after cognitive turn",
    "quiet_object_focus": "one calm object or human-scale work scene with generous whitespace",
    "concept_map_cover": "sparse concept relationship map for ideas, tradeoffs, or mental models",
    "magazine_card": "editorial magazine-like hero object with calm surrounding space",
}
GENERIC_VISUAL_TERMS = {
    "generic ai", "ai dashboard", "ai agent", "future technology", "developer workspace",
    "robot", "humanoid robot", "chip brain", "code rain", "neon dashboard",
}
DEFAULT_FORBIDDEN_GENERIC = "generic humanoid robot, chip brain, neon AI dashboard collage, random code rain, unbound floating plugin cards, real product screenshot, readable generated text, logo, QR code, watermark"
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


def overlay(base_path: Path, out_path: Path, title: str, subtitle: str, tags: list[str], canvas: tuple[int,int], layout_variant: str = "left_title_right_visual") -> None:
    """Compose deterministic Chinese typography over a text-free image background.

    The background generation prompt may vary by article type; this overlay must vary too,
    otherwise different articles still look identical in a WeChat feed.
    """
    im = fit(Image.open(base_path), canvas).convert("RGBA")
    w,h = canvas; sx=w/1792; sy=h/764; s=min(sx,sy)
    tags=(tags+["要点","路径","校验","交付"])[:4]
    ov = Image.new("RGBA", canvas, (0,0,0,0)); d=ImageDraw.Draw(ov)

    def shade(kind: str) -> None:
        if kind in {"left_title_right_visual", "quiet_object_focus"}:
            for x in range(0, min(w, int(w*0.68))):
                t = x / max(1, int(w*0.68))
                d.line((x,0,x,h), fill=(*PAL["bg"], int(248*(1-t)**1.55 + 12)), width=1)
            d.rectangle((int(w*0.60),0,w,h), fill=(0,0,0,20))
        elif kind == "top_title_bottom_system":
            d.rounded_rectangle((int(44*sx), int(36*sy), int(w-44*sx), int(245*sy)), radius=max(18,int(26*s)), fill=(4,14,32,182), outline=(*PAL["blue"],60), width=max(1,int(1.2*s)))
            d.rectangle((0,int(h*0.63),w,h), fill=(0,0,0,28))
        elif kind == "split_before_after":
            d.rectangle((0,0,w,int(190*sy)), fill=(4,14,32,205))
            d.rectangle((0,int(h*0.78),w,h), fill=(4,14,32,118))
        elif kind == "concept_map_cover":
            d.rectangle((0,0,int(w*0.44),h), fill=(4,14,32,202))
            d.rectangle((int(w*0.44),0,w,h), fill=(0,0,0,16))
        elif kind == "magazine_card":
            d.rectangle((0,int(h*0.48),w,h), fill=(4,14,32,172))
            d.rectangle((0,0,int(w*0.38),h), fill=(4,14,32,92))
        else:
            d.rectangle((0,0,int(w*0.58),h), fill=(4,14,32,190))

    def brand(x: int, y: int, scale: float = 1.0, label: str = "AI Workbench") -> None:
        rr=max(14,int(20*s*scale)); ww=max(3,int(4*s*scale))
        pts=[(x+rr,y),(x+int(1.7*rr),y+int(.45*rr)),(x+int(1.7*rr),y+int(1.35*rr)),(x+rr,y+int(1.8*rr)),(x+int(.3*rr),y+int(1.35*rr)),(x+int(.3*rr),y+int(.45*rr))]
        d.polygon(pts, fill=(4,14,32,218), outline=(*PAL["blue"],220))
        d.line((x+int(.72*rr),y+int(.62*rr),x+int(1.02*rr),y+int(.90*rr),x+int(.72*rr),y+int(1.18*rr)), fill=PAL["cyan"], width=ww)
        d.text((x+int(58*s*scale), y+int(8*s*scale)), label, font=font(BOLD,max(20,int(30*s*scale))), fill=(*PAL["white"],242))

    def tag_bar(x: int, y: int, width: int, height: int, vertical: bool = False) -> None:
        tf=font(BOLD,max(17,int(23*s))); icon_box=max(18,int(27*s)); gap=max(7,int(9*s))
        if vertical:
            slot=height/len(tags)
            d.rounded_rectangle((x,y,x+width,y+height), radius=max(12,int(18*s)), fill=(7,18,42,148), outline=(*PAL["blue"],80), width=1)
            for i,tag in enumerate(tags):
                yy=int(y+i*slot+slot/2)
                draw_icon(d,["plugin","skill","workflow","share"][i],x+int(26*s),yy,[PAL["blue"],PAL["violet"],PAL["cyan"],PAL["violet"]][i],max(.52,s*.68))
                bb=d.textbbox((0,0),tag,font=tf); th=bb[3]-bb[1]
                d.text((x+int(52*s), yy-th//2-int(1*s)), tag, font=tf, fill=(*PAL["white"],245))
                if i:
                    d.line((x+int(14*s),int(y+i*slot),x+width-int(14*s),int(y+i*slot)), fill=(*PAL["blue"],35), width=1)
            return
        d.rounded_rectangle((x,y,x+width,y+height), radius=max(10,int(16*s)), fill=(7,18,42,150), outline=(*PAL["blue"],90), width=1)
        slot=width/len(tags)
        for i,tag in enumerate(tags):
            x0=int(x+i*slot); x1=int(x+(i+1)*slot); cx=(x0+x1)//2; cy=y+height//2
            bb=d.textbbox((0,0),tag,font=tf); tw=bb[2]-bb[0]; th=bb[3]-bb[1]
            gw=icon_box+gap+tw; gx=int(cx-gw/2)
            draw_icon(d,["plugin","skill","workflow","share"][i],gx+icon_box//2,cy,[PAL["blue"],PAL["violet"],PAL["cyan"],PAL["violet"]][i],max(.50,s*.70))
            d.text((gx+icon_box+gap, int(cy-th/2)-int(1*s)), tag, font=tf, fill=(*PAL["white"],245))
            if i:
                d.line((x0,y+int(16*sy),x0,y+height-int(16*sy)), fill=(*PAL["blue"],38), width=1)

    def draw_title(x: int, y: int, title_size: int = 80, second_gradient: bool = True, max_width: int | None = None) -> int:
        lines=[t.strip() for t in title.replace("\\n","\n").split("\n") if t.strip()] or [title]
        if len(lines) == 1 and len(lines[0]) > 12:
            line = lines[0]
            cut = min(len(line), 11)
            lines = [line[:cut], line[cut:]]
        yy=y
        for i,line in enumerate(lines[:2]):
            f=font(BOLD,max(46,int((title_size - i*10)*s)))
            if i == 1 and second_gradient:
                gradient_text(im, (x, yy), line, f, PAL["blue"], PAL["violet"], canvas)
            else:
                d.text((x,yy), line, font=f, fill=(*PAL["white"],255))
            yy += int((title_size+14)*s)
        return yy

    shade(layout_variant)
    im = Image.alpha_composite(im, ov); d=ImageDraw.Draw(im)

    if layout_variant == "top_title_bottom_system":
        brand(int(72*sx), int(58*sy), .82)
        y2=draw_title(int(72*sx), int(108*sy), 72, False)
        d.text((int(72*sx), y2+int(10*sy)), subtitle, font=font(BOLD,max(28,int(39*s))), fill=(*PAL["white"],242))
        tag_bar(int(70*sx), int(620*sy), int(720*sx), int(72*sy))
    elif layout_variant == "split_before_after":
        brand(int(68*sx), int(48*sy), .78)
        y2=draw_title(int(68*sx), int(92*sy), 68, False)
        d.text((int(68*sx), y2+int(2*sy)), subtitle, font=font(BOLD,max(26,int(35*s))), fill=(*PAL["white"],238))
        tag_bar(int(540*sx), int(622*sy), int(710*sx), int(70*sy))
    elif layout_variant == "concept_map_cover":
        brand(int(58*sx), int(54*sy), .78)
        y2=draw_title(int(58*sx), int(140*sy), 74, True)
        d.text((int(58*sx), y2+int(20*sy)), subtitle, font=font(BOLD,max(28,int(38*s))), fill=(*PAL["white"],238))
        tag_bar(int(88*sx), int(560*sy), int(650*sx), int(70*sy))
    elif layout_variant == "quiet_object_focus":
        brand(int(64*sx), int(72*sy), .80)
        y2=draw_title(int(64*sx), int(210*sy), 78, False)
        d.text((int(66*sx), y2+int(20*sy)), subtitle, font=font(BOLD,max(28,int(38*s))), fill=(*PAL["white"],238))
        tag_bar(int(70*sx), int(596*sy), int(690*sx), int(70*sy))
    elif layout_variant == "magazine_card":
        brand(int(64*sx), int(82*sy), .78)
        y2=draw_title(int(66*sx), int(380*sy), 72, False)
        d.text((int(68*sx), y2+int(8*sy)), subtitle, font=font(BOLD,max(27,int(37*s))), fill=(*PAL["white"],238))
        tag_bar(int(1050*sx), int(70*sy), int(560*sx), int(68*sy))
    else:
        brand(int(62*sx), int(58*sy), 1.0)
        y2=draw_title(int(54*sx), int(172*sy), 86, True)
        d.text((int(54*sx), int(405*sy)), subtitle, font=font(BOLD,max(34,int(45*s))), fill=(*PAL["white"],245))
        tag_bar(int(42*sx), int(560*sy), int(800*sx), int(90*sy))

    d.rounded_rectangle((6,6,w-7,h-7), radius=max(14,int(22*s)), outline=(*PAL["blue"],105), width=max(1,int(1.5*s)))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(out_path, quality=96)


def split_list(text: str) -> list[str]:
    return [x.strip() for x in re.split(r"[,，、;；\n]+", text or "") if x.strip()]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_article_brief(path_text: str | None) -> dict[str, object]:
    if not path_text:
        return {}
    path = Path(path_text)
    if not path.is_absolute():
        path = REPO / path
    if not path.exists():
        raise FileNotFoundError(path)
    raw = path.read_text(encoding="utf-8-sig")
    lines = [x.strip() for x in raw.splitlines() if x.strip()]
    headings = [re.sub(r"^#+\s*", "", x) for x in lines if x.startswith("#")][:8]
    first_screen = " ".join([x for x in lines if not x.startswith("!")][:8])[:600]
    quote = next((x.lstrip("> ").strip() for x in lines if x.startswith(">")), "")
    return {
        "article_path": str(path),
        "article_sha256": sha256_file(path),
        "headings": headings,
        "first_screen_excerpt": first_screen,
        "candidate_core_claim": quote,
    }



def load_cover_brief(path_text: str | None) -> dict[str, object]:
    """Load a reusable cover semantic brief.

    JSON is the canonical format. Markdown briefs are accepted as source evidence,
    but are not auto-parsed beyond preserving their excerpt.
    """
    if not path_text:
        return {}
    path = Path(path_text)
    if not path.is_absolute():
        path = REPO / path
    if not path.exists():
        raise FileNotFoundError(path)
    raw = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError(f"cover brief must be a JSON object: {path}")
        data["_cover_brief_path"] = str(path)
        data["_cover_brief_sha256"] = sha256_file(path)
        return data
    return {
        "_cover_brief_path": str(path),
        "_cover_brief_sha256": sha256_file(path),
        "_cover_brief_excerpt": raw[:1200],
    }


def apply_cover_brief_defaults(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    brief = load_cover_brief(args.cover_brief)
    setattr(args, "_loaded_cover_brief", brief)
    if not brief:
        return

    def value(*keys: str):
        for key in keys:
            if key in brief and brief[key] not in (None, "", []):
                val = brief[key]
                if isinstance(val, list):
                    return ",".join(str(x) for x in val if str(x).strip())
                return str(val)
        return None

    mappings = {
        "candidate_id": ("article_id", "candidate_id"),
        "article_type": ("article_type",),
        "title": ("title",),
        "subtitle": ("subtitle",),
        "reader_scene": ("reader_scene",),
        "reader_pain": ("reader_pain",),
        "core_claim": ("core_claim",),
        "cognitive_turn": ("cognitive_turn",),
        "action_exit": ("action_exit",),
        "semantic_anchors": ("semantic_anchors", "article_anchors"),
        "metaphor": ("primary_metaphor", "visual_metaphor", "metaphor"),
        "supporting_elements": ("supporting_elements", "supporting_objects"),
        "avoid_generic": ("forbidden_generic_elements", "avoid_generic"),
        "theme": ("style_route", "theme"),
        "palette": ("palette",),
        "layout_variant": ("layout_variant",),
    }
    for attr, keys in mappings.items():
        val = value(*keys)
        if val is None:
            continue
        current = getattr(args, attr)
        default = parser.get_default(attr)
        if current in (None, "") or current == default:
            setattr(args, attr, val)


def build_semantic_brief(args: argparse.Namespace) -> dict[str, object]:
    article = extract_article_brief(args.article)
    anchors = split_list(args.semantic_anchors)
    if not anchors and article.get("headings"):
        anchors = [x for x in article["headings"] if len(x) <= 24][:6]
    return {
        "version": "cover-semantic-brief.v1",
        "article_id": args.candidate_id or safe(args.stem),
        "title": args.title,
        "subtitle": args.subtitle,
        "article_type": args.article_type.strip(),
        "reader_scene": args.reader_scene.strip(),
        "reader_pain": args.reader_pain.strip(),
        "core_claim": args.core_claim.strip() or article.get("candidate_core_claim", ""),
        "cognitive_turn": args.cognitive_turn.strip(),
        "action_exit": args.action_exit.strip(),
        "semantic_anchors": anchors,
        "primary_metaphor": args.metaphor.strip(),
        "supporting_elements": split_list(args.supporting_elements)[:2],
        "forbidden_generic_elements": split_list(args.avoid_generic or DEFAULT_FORBIDDEN_GENERIC),
        "style_route": args.theme,
        "palette": args.palette,
        "layout_variant": args.layout_variant,
        "article_binding": article,
        "cover_brief_source": getattr(args, "_loaded_cover_brief", {}).get("_cover_brief_path", ""),
        "cover_brief_sha256": getattr(args, "_loaded_cover_brief", {}).get("_cover_brief_sha256", ""),
        "reverse_validation_question": "Hide the title: can the image be explained as this exact article, not just generic AI productivity?",
    }


def build_prompt(args: argparse.Namespace, brief: dict[str, object]) -> str:
    palette = PALETTES.get(args.palette, PALETTES["dev"])
    anchors = ", ".join(brief.get("semantic_anchors", [])[:6]) or args.theme
    supporting = ", ".join(brief.get("supporting_elements", [])[:2]) or "two restrained article-bound detail elements"
    forbidden = ", ".join(brief.get("forbidden_generic_elements", [])[:16])
    layout_desc = LAYOUT_VARIANTS.get(args.layout_variant, LAYOUT_VARIANTS["left_title_right_visual"])
    return textwrap.dedent(f"""
    Generate a premium WeChat technology article cover background, final crop ratio 2.35:1.
    CRITICAL: no readable text, no Chinese or English words, no brand names, no logos, no QR codes, no watermarks, no screenshots or trademarks.
    CRITICAL: no people, no human figure, no back-view person, no face, no digital human head, no humanoid robot unless the article explicitly requires it.

    Article binding, not generic style:
    - Article type: {brief.get('article_type') or 'unspecified practical WeChat tutorial/article'}.
    - Reader scene: {brief.get('reader_scene') or 'a reader solving the article-specific problem at a workstation'}.
    - Reader pain: {brief.get('reader_pain') or 'confusion before applying the method'}.
    - Core claim: {brief.get('core_claim') or args.subtitle}.
    - Cognitive turn: {brief.get('cognitive_turn') or 'from scattered tool use to a controlled, inspectable workflow'}.
    - Action exit: {brief.get('action_exit') or 'one concrete next step after reading'}.
    - Semantic anchors from the article: {anchors}.
    - One primary visual metaphor: {brief.get('primary_metaphor') or args.theme}.
    - Supporting elements, at most two: {supporting}.

    Layout variant: {args.layout_variant} - {layout_desc}.
    Keep the deterministic Chinese title area calm and uncluttered; do not place light streaks, panels, horizontal lines, or high-contrast objects across the title/subtitle safe area. Bottom keyword tags may be added later by local layout, so the bottom-left area must remain calm.

    Visual direction: express the primary metaphor through an original, no-person software/product/workbench scene. Use a single focal subject and two restrained support elements; avoid a repeated generic dashboard collage. The cover should still make sense when the title is hidden and should point to the article-specific topic, not merely to AI, efficiency, or future technology.

    Style: 2026 AI technology editorial cover, premium technology magazine, professional product keynote restraint, clean glassmorphism, original abstract tool/workflow modules, calm composition, no copied UI.
    Color palette: {palette}. Article theme / style route: {args.theme}.
    Avoid: {forbidden}, cartoon style, cheap cyberpunk, clutter, excessive glow, unreadable microcopy.
    """).strip()


def validate_style_spec(args: argparse.Namespace, canvas: tuple[int,int]) -> dict[str, object]:
    w,h=canvas; ratio=w/h
    tags=split_list(args.tags)
    anchors=split_list(args.semantic_anchors)
    problems=[]; warnings=[]
    if abs(ratio-2.35)>0.025: problems.append(f"ratio should be about 2.35:1, got {ratio:.3f}")
    if not args.title.strip() or not args.subtitle.strip(): problems.append("title and subtitle are required")
    if not 3 <= len(tags) <= 5: problems.append(f"3 to 5 bottom keywords required, got {len(tags)}")
    if any(len(t)>8 for t in tags): problems.append("bottom keywords should be short")
    if args.layout_variant not in LAYOUT_VARIANTS: problems.append(f"unsupported layout_variant: {args.layout_variant}")
    semantic_mode = bool(args.article or args.cover_brief or args.metaphor or args.reader_scene or args.semantic_anchors)
    if semantic_mode:
        if not args.metaphor.strip(): problems.append("--metaphor is required when article/semantic cover generation is requested")
        if not args.reader_scene.strip(): problems.append("--reader-scene is required when article/semantic cover generation is requested")
        if len(anchors) < 3 and not args.article: problems.append("--semantic-anchors must provide at least 3 anchors unless --article is supplied")
        generic_blob = " ".join([args.theme, args.metaphor]).lower()
        if any(term in generic_blob for term in GENERIC_VISUAL_TERMS) and not anchors:
            problems.append("generic AI visual terms need article-specific --semantic-anchors")
    else:
        warnings.append("semantic cover brief not supplied; compatibility mode only, not recommended for publication covers")
    if problems: raise RuntimeError("style precheck failed:\n- " + "\n- ".join(problems))
    msg = "style precheck passed: 2.35:1, title hierarchy, 3-5 concise tags, semantic cover brief gate"
    if warnings:
        msg += "; warnings: " + "; ".join(warnings)
    print(msg + ".")
    return {"tags": tags, "warnings": warnings}

def redact(x: str) -> str:
    return re.sub(r"sk-[A-Za-z0-9_\-\*]{8,}", "sk-***REDACTED***", x)


def call_api(prompt: str, out: Path) -> dict[str, str]:
    # Covers deliberately avoid the project remote endpoint and use local CC Switch only.
    return generate_image(
        prompt,
        out,
        size=os.environ.get("CC_SWITCH_IMAGE_SIZE", "1536x1024"),
        quality=os.environ.get("CC_SWITCH_IMAGE_QUALITY", "high"),
    )


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--title", default=DEFAULT_TITLE)
    parser.add_argument("--subtitle", default=DEFAULT_SUBTITLE)
    parser.add_argument("--tags", default=DEFAULT_TAGS)
    parser.add_argument("--theme", default="AI developer workflow, deliverable AI workbench")
    parser.add_argument("--article-type", default="", help="Tutorial, review, story, trend, retrospective, or workflow type used for semantic routing")
    parser.add_argument("--palette", default="dev", choices=sorted(PALETTES))
    parser.add_argument("--article", help="Path to the article markdown used for semantic binding")
    parser.add_argument("--cover-brief", help="Optional existing cover semantic brief JSON/Markdown path")
    parser.add_argument("--layout-variant", default="left_title_right_visual", choices=sorted(LAYOUT_VARIANTS))
    parser.add_argument("--metaphor", default="", help="One article-specific primary visual metaphor")
    parser.add_argument("--reader-scene", default="", help="Concrete reader moment represented by the cover")
    parser.add_argument("--reader-pain", default="", help="Reader pain or friction this article solves")
    parser.add_argument("--core-claim", default="", help="Core claim to preserve in the cover concept")
    parser.add_argument("--cognitive-turn", default="", help="From old view to new view")
    parser.add_argument("--action-exit", default="", help="Concrete next action after reading")
    parser.add_argument("--semantic-anchors", default="", help="Comma-separated 3-6 article anchors")
    parser.add_argument("--supporting-elements", default="", help="Comma-separated max two supporting visual elements")
    parser.add_argument("--avoid-generic", default=DEFAULT_FORBIDDEN_GENERIC, help="Comma-separated forbidden generic elements")
    parser.add_argument("--candidate-id", default="", help="Stable id for this cover candidate or article")
    parser.add_argument("--output-size", default="1792x764")
    parser.add_argument("--stem", default=DEFAULT_STEM_TITLE)
    parser.add_argument("--skip-api", action="store_true")
    args=parser.parse_args()
    apply_cover_brief_defaults(args, parser)
    load_env(); canvas=parse_size(args.output_size); validation=validate_style_spec(args, canvas)
    BASE_DIR.mkdir(parents=True, exist_ok=True); COVER_DIR.mkdir(parents=True, exist_ok=True); RECORD.parent.mkdir(parents=True, exist_ok=True)
    stem=safe(args.stem)
    base=BASE_DIR/(stem+"-gpt-image底图.png")
    cover=COVER_DIR/(stem+"-封面.png")
    pf=BASE_DIR/(stem+"-gpt-image提示词.txt")
    brief_path=BASE_DIR/(stem+"-cover-semantic-brief.json")
    brief=build_semantic_brief(args)
    pr=build_prompt(args, brief)
    brief["prompt_sha256"] = sha256_text(pr)
    pf.write_text(pr, encoding="utf-8")
    brief_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("prompt saved: "+str(pf))
    print("cover semantic brief saved: "+str(brief_path))
    route_note = "CC Switch local proxy http://127.0.0.1:15721/v1"
    model_note = "CC Switch Responses image_generation (backend selected by provider)"
    if not args.skip_api:
        route = call_api(pr, base)
        route_note = route["route"]
        model_note = route["image_model_selection"]
        print("generated through CC Switch local proxy: "+route_note+"; model: "+model_note)
        print("base generated: "+str(base))
    elif not base.exists():
        raise FileNotFoundError(str(base))
    tags=validation["tags"]
    overlay(base, cover, args.title, args.subtitle, tags, canvas, args.layout_variant); print("cover generated: "+str(cover))
    brief["base_image_sha256"] = sha256_file(base)
    brief["final_cover_sha256"] = sha256_file(cover)
    brief_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    if not RECORD.exists(): RECORD.write_text("# image generation record\n\n", encoding="utf-8")
    with RECORD.open("a", encoding="utf-8") as f:
        f.write(f"\n## {time.strftime('%Y-%m-%d %H:%M:%S')} - cover regenerated\n\n- route: {route_note}\n- model: {model_note}\n- size: {canvas[0]} x {canvas[1]}\n- layout_variant: {args.layout_variant}\n- primary_metaphor: {brief.get('primary_metaphor')}\n- semantic_anchors: {', '.join(brief.get('semantic_anchors', []))}\n- reverse_validation: hide title; image must explain the article beyond generic AI productivity\n- prompt_sha256: `{brief.get('prompt_sha256')}`\n- base_sha256: `{brief.get('base_image_sha256')}`\n- cover_sha256: `{brief.get('final_cover_sha256')}`\n- semantic_brief: `{brief_path.relative_to(REPO).as_posix()}`\n- base: `{base.relative_to(REPO).as_posix()}`\n- cover: `{cover.relative_to(REPO).as_posix()}`\n")

if __name__ == "__main__":
    main()


