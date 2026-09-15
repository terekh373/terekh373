"""
Builds every SVG in ../assets for the github.com/terekh373 profile README.
Palette and type match anton-portfolio (src/styles/global.css), so the README
and the site read as one drawing set.

Edit text here (status stamp, REV date, projects, stack), then rebuild:

    pip install fonttools brotli
    cd tools && npm pack @fontsource/ibm-plex-mono @fontsource/ibm-plex-sans
    mkdir -p fonts && for f in *.tgz; do d=fonts/${f%.tgz}; mkdir -p $d; tar xzf $f -C $d --strip-components=1; done
    python build_assets.py

Fonts are subset to the glyphs each SVG uses and embedded as base64, because
GitHub renders README images without loading external fonts.
"""
import base64, io, os, re, html
from fontTools.ttLib import TTFont
from fontTools import subset

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets")
os.makedirs(OUT, exist_ok=True)
FONTDIR = os.environ.get("FONTDIR", os.path.join(HERE, "fonts"))

C = dict(bg="#0e2233", surface="#15304a", grid="#24435c", ink="#f3f6f2",
         dim="#a9bfc9", line="#6fe7e2", linedim="#3f7b78", stamp="#d9714b")

FONTS = {
    "sans600": ("IBM Plex Sans", 600, "fontsource-ibm-plex-sans-5.3.0/files/ibm-plex-sans-latin-600-normal.woff2"),
    "sans500": ("IBM Plex Sans", 500, "fontsource-ibm-plex-sans-5.3.0/files/ibm-plex-sans-latin-500-normal.woff2"),
    "sans400": ("IBM Plex Sans", 400, "fontsource-ibm-plex-sans-5.3.0/files/ibm-plex-sans-latin-400-normal.woff2"),
    "mono400": ("IBM Plex Mono", 400, "fontsource-ibm-plex-mono-5.3.0/files/ibm-plex-mono-latin-400-normal.woff2"),
    "mono500": ("IBM Plex Mono", 500, "fontsource-ibm-plex-mono-5.3.0/files/ibm-plex-mono-latin-500-normal.woff2"),
    "mono600": ("IBM Plex Mono", 600, "fontsource-ibm-plex-mono-5.3.0/files/ibm-plex-mono-latin-600-normal.woff2"),
}
FALLBACK = {"IBM Plex Sans": "'IBM Plex Sans', 'Segoe UI', Helvetica, Arial, sans-serif",
            "IBM Plex Mono": "'IBM Plex Mono', 'SFMono-Regular', Consolas, Menlo, monospace"}

MONO_ADV = 0.6  # IBM Plex Mono advance width in em


def esc(s):
    return html.escape(s, quote=False)


def font_face(key, chars):
    fam, weight, rel = FONTS[key]
    f = TTFont(os.path.join(FONTDIR, rel))
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga"]
    opts.name_IDs = []
    opts.notdef_outline = True
    s = subset.Subsetter(options=opts)
    s.populate(text="".join(sorted(set(chars))) + " ")
    s.subset(f)
    buf = io.BytesIO()
    f.flavor = "woff2"
    f.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return (f"@font-face{{font-family:'{fam}';font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")


class Sheet:
    """Collects SVG body + records which text is set in which font, then embeds subsets."""

    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.body = []
        self.used = {}
        self.defs = []
        self.css = []

    def add(self, s):
        self.body.append(s)

    def text(self, x, y, s, font="sans400", size=14, fill=None, anchor="start",
             ls=0, cls="", extra=""):
        fam, weight, _ = FONTS[font]
        self.used.setdefault(font, set()).update(s)
        fill = fill or C["ink"]
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        l = f' letter-spacing="{ls}"' if ls else ""
        c = f' class="{cls}"' if cls else ""
        self.add(f'<text x="{x}" y="{y}" font-family="{FALLBACK[fam]}" font-weight="{weight}" '
                 f'font-size="{size}" fill="{fill}"{a}{l}{c}{extra}>{esc(s)}</text>')

    def render(self):
        faces = "".join(font_face(k, v) for k, v in self.used.items())
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{html.escape(self.title)}">'
                f'<title>{esc(self.title)}</title>'
                f'<defs><style>{faces}{"".join(self.css)}'
                f'@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}</style>'
                f'{"".join(self.defs)}</defs>'
                f'{"".join(self.body)}</svg>')

    def save(self, name):
        path = os.path.join(OUT, name)
        with open(path, "w") as fh:
            fh.write(self.render())
        print(f"{name:28s} {os.path.getsize(path)/1024:6.1f} KB")


# ---------------------------------------------------------------- primitives
def paper(sh, rx=14):
    w, h = sh.w, sh.h
    sh.defs.append(
        f'<clipPath id="clip"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>'
        f'<pattern id="g" width="20" height="20" patternUnits="userSpaceOnUse">'
        f'<path d="M20 0H0V20" fill="none" stroke="{C["grid"]}" stroke-width=".6" opacity=".55"/></pattern>'
        f'<pattern id="G" width="100" height="100" patternUnits="userSpaceOnUse">'
        f'<rect width="100" height="100" fill="url(#g)"/>'
        f'<path d="M100 0H0V100" fill="none" stroke="{C["grid"]}" stroke-width="1"/></pattern>'
        f'<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0 1 L9 5 L0 9" fill="none" stroke="{C["line"]}" stroke-width="1.6"/></marker>'
        f'<marker id="ahd" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0 1 L9 5 L0 9" fill="none" stroke="{C["linedim"]}" stroke-width="1.6"/></marker>'
        f'<marker id="tick" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
        f'<path d="M5 0 V10" stroke="{C["linedim"]}" stroke-width="1.4"/></marker>'
    )
    sh.add(f'<g clip-path="url(#clip)"><rect width="{w}" height="{h}" fill="{C["bg"]}"/>'
           f'<rect width="{w}" height="{h}" fill="url(#G)"/></g>')


def ink_filter(sh):
    sh.defs.append(
        '<filter id="ink" x="-15%" y="-25%" width="130%" height="150%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="4" result="warp"/>'
        '<feDisplacementMap in="SourceGraphic" in2="warp" scale="1.8" xChannelSelector="R" yChannelSelector="G" result="d"/>'
        '<feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="2" seed="11" result="speck"/>'
        '<feColorMatrix in="speck" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 -2.6 2.2" result="mask"/>'
        '<feComposite in="d" in2="mask" operator="in"/></filter>')


def corners(sh, inset=12, size=9):
    """Registration crosshairs at the four corners of the drawing frame."""
    w, h, i = sh.w, sh.h, inset
    for (x, y) in [(i, i), (w - i, i), (i, h - i), (w - i, h - i)]:
        sh.add(f'<path d="M{x-size} {y}H{x+size}M{x} {y-size}V{y+size}" stroke="{C["linedim"]}" stroke-width="1"/>')
        sh.add(f'<circle cx="{x}" cy="{y}" r="3.2" fill="none" stroke="{C["linedim"]}" stroke-width="1"/>')


def box(sh, x, y, w, h, title, sub=None, strong=False, tsize=14, label=None):
    stroke = C["line"] if strong else C["linedim"]
    sw = 1.6 if strong else 1.2
    sh.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{C["bg"]}" stroke="{stroke}" stroke-width="{sw}"/>')
    cx = x + w / 2
    if sub:
        sh.text(cx, y + h / 2 - 2, title, "sans500", tsize, anchor="middle")
        sh.text(cx, y + h / 2 + 13, sub, "mono400", 9.5, C["dim"], anchor="middle")
    else:
        sh.text(cx, y + h / 2 + tsize * 0.35, title, "sans500", tsize, anchor="middle")
    if label:
        sh.text(x, y - 6, label, "mono500", 9, C["linedim"], ls=1.2)


def cylinder(sh, x, y, w, h, title, sub=None, label=None):
    ry = 7
    sh.add(f'<path d="M{x} {y+ry} V{y+h-ry} A{w/2} {ry} 0 0 0 {x+w} {y+h-ry} V{y+ry}" '
           f'fill="{C["bg"]}" stroke="{C["linedim"]}" stroke-width="1.2"/>')
    sh.add(f'<ellipse cx="{x+w/2}" cy="{y+ry}" rx="{w/2}" ry="{ry}" fill="{C["bg"]}" stroke="{C["linedim"]}" stroke-width="1.2"/>')
    cx = x + w / 2
    if sub:
        sh.text(cx, y + h / 2 + 4, title, "sans500", 14, anchor="middle")
        sh.text(cx, y + h / 2 + 19, sub, "mono400", 9.5, C["dim"], anchor="middle")
    else:
        sh.text(cx, y + h / 2 + 8, title, "sans500", 14, anchor="middle")
    if label:
        sh.text(x, y - 6, label, "mono500", 9, C["linedim"], ls=1.2)


def arrow(sh, d, dim=False, dashed=False, cls=""):
    col = C["linedim"] if dim else C["line"]
    m = "ahd" if dim else "ah"
    da = ' stroke-dasharray="4 4"' if dashed else ""
    c = f' class="{cls}"' if cls else ""
    sh.add(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="1.3"{da} marker-end="url(#{m})"{c}/>')


def chip_rows(chips, max_w, size=10.5, pad=8, gap=6):
    rows, row, x = [], [], 0
    for c in chips:
        w = len(c) * size * MONO_ADV + 2 * pad
        if row and x + w > max_w:
            rows.append(row)
            row, x = [], 0
        row.append((c, w, x))
        x += w + gap
    rows.append(row)
    return rows


def chips(sh, x0, y0, chips_, max_w, size=10.5, row_h=26):
    for r, row in enumerate(chip_rows(chips_, max_w, size)):
        y = y0 + r * row_h
        for (c, w, x) in row:
            sh.add(f'<rect x="{x0+x:.1f}" y="{y}" width="{w:.1f}" height="20" rx="2" fill="none" '
                   f'stroke="{C["linedim"]}" stroke-width="1"/>')
            sh.text(round(x0 + x + w / 2, 1), y + 14, c, "mono400", size, C["ink"], anchor="middle")


def tag(sh, right_x, y, s, color=None, dot=False):
    color = color or C["line"]
    size = 10
    w = len(s) * (size * MONO_ADV + 0.6) + 18 + (12 if dot else 0)
    x = right_x - w
    sh.add(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="22" rx="11" fill="none" stroke="{color}" stroke-width="1.1"/>')
    tx = x + 9
    if dot:
        sh.add(f'<circle class="pulse" cx="{x+13:.1f}" cy="{y+11}" r="3.2" fill="{color}"/>')
        tx += 12
    sh.text(round(tx, 1), y + 15, s, "mono500", size, color, ls=0.6)


def stamp(sh, cx, cy, rot, big, small, w, h, delay=0.9, size=20):
    ink_filter(sh)
    sh.css.append(
        ".stamp{transform-box:fill-box;transform-origin:center;opacity:.93;"
        f"animation:thump .45s cubic-bezier(.2,.9,.3,1.2) {delay}s both}}"
        "@keyframes thump{0%{opacity:0;transform:scale(1.6)}70%{opacity:.95}100%{opacity:.93;transform:scale(1)}}")
    sh.add(f'<g transform="translate({cx} {cy}) rotate({rot})"><g class="stamp"><g filter="url(#ink)">')
    sh.add(f'<rect x="{-w/2}" y="{-h/2}" width="{w}" height="{h}" rx="4" fill="none" stroke="{C["stamp"]}" stroke-width="3"/>')
    sh.add(f'<rect x="{-w/2+5}" y="{-h/2+5}" width="{w-10}" height="{h-10}" rx="2" fill="none" stroke="{C["stamp"]}" stroke-width="1.2"/>')
    if small:
        sh.text(0, -h / 2 + h * 0.46, big, "mono600", size, C["stamp"], anchor="middle", ls=2)
        sh.text(0, -h / 2 + h * 0.46 + 16, small, "mono600", 10.5, C["stamp"], anchor="middle", ls=1)
    else:
        sh.text(0, size * 0.36, big, "mono600", size, C["stamp"], anchor="middle", ls=2)
    sh.add('</g></g></g>')


def card_head(sh, title, subtitle):
    sh.text(28, 54, title, "sans600", 26, ls=-0.3)
    sh.text(28, 78, subtitle, "sans400", 13.5, C["dim"])


def card_foot(sh, chips_, y):
    sh.add(f'<path d="M28 {y-12}H{sh.w-28}" stroke="{C["linedim"]}" stroke-width="1" stroke-dasharray="2 4"/>')
    chips(sh, 28, y, chips_, sh.w - 56)


# ================================================================= HEADER
def header():
    sh = Sheet(880, 440, "Anton Tereshchenko. Junior .NET developer, backend on C# and ASP.NET Core. "
                         "Kharkiv, Ukraine. Open to remote and outstaff roles.")
    paper(sh, 16)
    W, H = sh.w, sh.h
    # drawing frame with zone gutter
    sh.add(f'<rect x="10" y="10" width="{W-20}" height="{H-20}" rx="8" fill="none" stroke="{C["linedim"]}" stroke-width="1"/>')
    sh.add(f'<rect x="26" y="26" width="{W-52}" height="{H-52}" fill="none" stroke="{C["line"]}" stroke-width="1.2" opacity=".75"/>')
    zw = (W - 52) / 8
    for k in range(8):
        x0 = 26 + zw * k
        if k:
            sh.add(f'<path d="M{x0:.1f} 10V26M{x0:.1f} {H-26}V{H-10}" stroke="{C["linedim"]}" stroke-width="1"/>')
        sh.text(round(x0 + zw / 2, 1), 21.5, str(k + 1), "mono400", 8.5, C["linedim"], anchor="middle")
        sh.text(round(x0 + zw / 2, 1), H - 14.5, str(k + 1), "mono400", 8.5, C["linedim"], anchor="middle")
    zh = (H - 52) / 4
    for k, L in enumerate("ABCD"):
        y0 = 26 + zh * k
        if k:
            sh.add(f'<path d="M10 {y0:.1f}H26M{W-26} {y0:.1f}H{W-10}" stroke="{C["linedim"]}" stroke-width="1"/>')
        sh.text(18, round(y0 + zh / 2 + 3, 1), L, "mono400", 8.5, C["linedim"], anchor="middle")
        sh.text(W - 18, round(y0 + zh / 2 + 3, 1), L, "mono400", 8.5, C["linedim"], anchor="middle")

    # name + role
    sh.text(56, 104, "Anton Tereshchenko", "sans600", 52, ls=-1)
    sh.text(58, 142, "Junior .NET developer. Backend on C# and ASP.NET Core,", "sans400", 19, C["dim"])
    sh.text(58, 167, "with the frontend to match.", "sans400", 19, C["dim"])

    # stamp
    stamp(sh, 740, 108, -8, "OPEN TO WORK", "REMOTE / OUTSTAFF", 196, 70, delay=0.9, size=21)

    # schematic: client -> api -> data
    by, bh = 222, 70
    box(sh, 58, by, 190, bh, "Angular / React", "SPA + JWT interceptor", tsize=16, label="CLIENT")
    box(sh, 364, by, 212, bh, "ASP.NET Core 8", "REST, Clean Architecture", strong=True, tsize=16, label="API")
    cylinder(sh, 692, by - 4, 150, bh + 8, "SQL Server", "PostgreSQL too", label="DATA")
    # request / response
    arrow(sh, f"M250 {by+22}H360")
    sh.text(305, by + 15, "POST /api/links", "mono400", 10, C["dim"], anchor="middle")
    arrow(sh, f"M362 {by+48}H252", dim=True)
    sh.text(307, by + 64, "201 Created", "mono400", 10, C["dim"], anchor="middle")
    arrow(sh, f"M578 {by+35}H688")
    sh.text(633, by + 28, "EF Core", "mono400", 10, C["dim"], anchor="middle")
    sh.text(633, by + 51, "LINQ", "mono400", 10, C["dim"], anchor="middle")
    # auth annotation with leader
    sh.add(f'<path d="M470 {by+bh+1}V{by+bh+24}H494" fill="none" stroke="{C["linedim"]}" stroke-width="1"/>'
           f'<circle cx="470" cy="{by+bh+1}" r="2.2" fill="{C["linedim"]}"/>')
    sh.text(500, by + bh + 28, "auth: Identity + JWT, roles", "mono400", 10, C["dim"])
    # packet travelling the request path
    sh.add(f'<circle r="3.6" fill="{C["line"]}" opacity="0">'
           f'<animate attributeName="opacity" values="0;1;1;1;0" keyTimes="0;.05;.5;.95;1" dur="4.8s" begin="1.6s" repeatCount="indefinite"/>'
           f'<animateMotion dur="4.8s" begin="1.6s" repeatCount="indefinite" calcMode="paced" '
           f'path="M250 {by+22}H362M578 {by+35}H688H578M362 {by+48}H250"/></circle>')

    # title block strip
    ty = 346
    sh.add(f'<path d="M26 {ty}H{W-26}" stroke="{C["line"]}" stroke-width="1.2" opacity=".75"/>')
    cells = [("LOCATION", "Kharkiv, Ukraine", 176), ("CORE STACK", "C#, .NET 8, ASP.NET Core", 232),
             ("NOW", "Team lead on Vexa", 176), ("STUDY", "IT STEP, final year", 156), ("REV", "2026.09", 88)]
    x = 26
    for i, (lab, val, cw) in enumerate(cells):
        if i:
            sh.add(f'<path d="M{x} {ty}V{H-26}" stroke="{C["linedim"]}" stroke-width="1"/>')
        sh.text(x + 12, ty + 20, lab, "mono500", 8.5, C["linedim"], ls=1.4)
        sh.text(x + 12, ty + 45, val, "sans500", 14.5, C["ink"])
        x += cw
    sh.save("header.svg")


# ================================================================= VEXA (wide)
def vexa():
    sh = Sheet(880, 292, "Vexa: online course marketplace. Team lead of 4 developers. "
                         "NestJS, Prisma, PostgreSQL, Docker. 30 models, 22 enums.")
    sh.css.append(".pulse{animation:pulse 2.4s ease-in-out infinite}"
                  "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}")
    paper(sh, 14)
    corners(sh)
    card_head(sh, "Vexa", "Online course marketplace. Diploma project, in active development.")
    tag(sh, sh.w - 28, 34, "TEAM LEAD, 4 DEVS", C["line"])
    tag(sh, sh.w - 158, 34, "IN PROGRESS", C["stamp"], dot=True)

    # --- left: git flow the team works in
    gx, gy = 28, 112
    sh.text(gx, gy, "GIT FLOW", "mono500", 9, C["linedim"], ls=1.2)
    main_y, dev_y, f1, f2 = gy + 22, gy + 50, gy + 78, gy + 102
    x0, x1 = gx + 72, gx + 350
    for lab, yy in [("main", main_y), ("develop", dev_y), ("feature/*", f1)]:
        sh.text(gx, yy + 3.5, lab, "mono400", 10, C["dim"])
    sh.add(f'<path d="M{x0} {main_y}H{x1}" stroke="{C["line"]}" stroke-width="1.6"/>')
    sh.add(f'<path d="M{x0} {dev_y}H{x1}" stroke="{C["linedim"]}" stroke-width="1.6"/>')
    # feature branches: off develop, back into develop via reviewed PR
    for (a, b, yy) in [(x0 + 6, x0 + 84, f1), (x0 + 94, x0 + 172, f1), (x0 + 182, x0 + 250, f1)]:
        sh.add(f'<path d="M{a} {dev_y} C{a+12} {dev_y} {a+8} {yy} {a+22} {yy} H{b-22} '
               f'C{b-8} {yy} {b-12} {dev_y} {b} {dev_y}" fill="none" stroke="{C["dim"]}" stroke-width="1.2" opacity=".8"/>')
        sh.add(f'<circle cx="{b-30}" cy="{yy}" r="3" fill="{C["bg"]}" stroke="{C["dim"]}" stroke-width="1.2"/>')
        # review mark at merge point
        sh.add(f'<circle cx="{b}" cy="{dev_y}" r="4.5" fill="{C["bg"]}" stroke="{C["line"]}" stroke-width="1.4"/>')
    # release to main
    rx_ = x0 + 262
    sh.add(f'<path d="M{rx_-14} {dev_y} C{rx_-4} {dev_y} {rx_-6} {main_y} {rx_+6} {main_y}" fill="none" stroke="{C["line"]}" stroke-width="1.4"/>')
    sh.add(f'<rect x="{rx_+3}" y="{main_y-4}" width="8" height="8" transform="rotate(45 {rx_+7} {main_y})" fill="{C["line"]}"/>')
    sh.text(rx_ - 6, main_y - 8, "sprint release", "mono400", 9.5, C["dim"], anchor="end")
    # legend
    ly = f2 + 8
    sh.add(f'<circle cx="{x0+4}" cy="{ly}" r="4.5" fill="{C["bg"]}" stroke="{C["line"]}" stroke-width="1.4"/>')
    sh.text(x0 + 14, ly + 3.5, "every PR reviewed", "mono400", 9.5, C["dim"])
    sh.text(x0 + 160, ly + 3.5, "2-week Scrum sprints", "mono400", 9.5, C["dim"])

    # divider between halves
    sh.add(f'<path d="M424 104V222" stroke="{C["linedim"]}" stroke-width="1" stroke-dasharray="2 4"/>')

    # --- right: nest modules -> prisma -> postgres inside docker compose
    rx0 = 448
    sh.text(rx0, gy, "NESTJS MODULES", "mono500", 9, C["linedim"], ls=1.2)
    for i, m in enumerate(["auth", "courses", "enrollments"]):
        yy = gy + 12 + i * 30
        sh.add(f'<rect x="{rx0}" y="{yy}" width="112" height="22" rx="2" fill="{C["bg"]}" stroke="{C["linedim"]}" stroke-width="1.1"/>')
        sh.text(rx0 + 10, yy + 15, m, "mono400", 10.5, C["ink"])
        arrow(sh, f"M{rx0+114} {yy+11} C{rx0+140} {yy+11} {rx0+140} {gy+47} {rx0+166} {gy+47}", dim=True)
    # docker compose boundary
    dx = rx0 + 168
    sh.add(f'<rect x="{dx}" y="{gy+4}" width="240" height="96" rx="6" fill="none" stroke="{C["dim"]}" stroke-width="1" stroke-dasharray="5 4"/>')
    sh.add(f'<rect x="{dx+12}" y="{gy-4}" width="104" height="14" fill="{C["bg"]}"/>')
    sh.text(dx + 16, gy + 7, "docker compose", "mono400", 9.5, C["dim"])
    box(sh, dx + 14, gy + 32, 84, 36, "Prisma", strong=True, tsize=14)
    arrow(sh, f"M{dx+100} {gy+50}H{dx+134}")
    cylinder(sh, dx + 138, gy + 22, 88, 56, "Postgres")
    # dimension line: schema size
    dy = gy + 118
    sh.add(f'<path d="M{dx+14} {dy}H{dx+226}" stroke="{C["linedim"]}" stroke-width="1" marker-start="url(#tick)" marker-end="url(#tick)"/>')
    sh.add(f'<rect x="{dx+62}" y="{dy-8}" width="116" height="16" fill="{C["bg"]}"/>')
    sh.text(dx + 120, dy + 3.5, "30 models, 22 enums", "mono500", 10, C["line"], anchor="middle")

    card_foot(sh, ["TypeScript", "NestJS", "PostgreSQL", "Prisma", "Docker", "REST API", "Tech spec", "Scrum"], 250)
    sh.save("work-vexa.svg")


# ================================================================= small cards
CARD_W, CARD_H = 430, 290


def url_shortener():
    sh = Sheet(CARD_W, CARD_H, "URL Shortener: full-stack link shortener built solo. ASP.NET Core 8, "
                               "Angular 17, EF Core, SQL Server, JWT, 11 unit tests with xUnit and Moq.")
    paper(sh); corners(sh)
    card_head(sh, "URL Shortener", "Full-stack link shortener, built solo.")
    tag(sh, CARD_W - 28, 34, "SOLO")
    y = 118
    box(sh, 28, y, 92, 32, "API", tsize=13)
    box(sh, 152, y, 118, 32, "Core", strong=True, tsize=14)
    box(sh, 298, y, 104, 32, "Infrastructure", tsize=12)
    arrow(sh, f"M121 {y+16}H148")
    arrow(sh, f"M297 {y+16}H278")
    box(sh, 168, y + 66, 86, 28, "Tests", tsize=12)
    arrow(sh, f"M211 {y+65}V{y+36}")
    sh.text(28, y - 8, "CLEAN ARCHITECTURE", "mono500", 9, C["linedim"], ls=1.2)
    # annotations
    sh.add(f'<path d="M152 {y+32}L130 {y+56}H40" fill="none" stroke="{C["linedim"]}" stroke-width="1"/>')
    sh.text(40, y + 70, "depends on nothing", "mono400", 9.5, C["dim"])
    sh.add(f'<path d="M255 {y+80}H290" stroke="{C["linedim"]}" stroke-width="1"/>')
    sh.text(296, y + 78, "11 unit tests,", "mono400", 9.5, C["dim"])
    sh.text(296, y + 91, "repo mocked", "mono400", 9.5, C["dim"])
    card_foot(sh, ["ASP.NET Core 8", "Angular 17", "EF Core", "SQL Server", "JWT", "xUnit", "Moq"], 238)
    sh.save("work-url-shortener.svg")


def taskflow():
    sh = Sheet(CARD_W, CARD_H, "TaskFlow: real-time Kanban board, live around the clock. React 18, Redux, "
                               "Node.js, Express, Socket.IO, MongoDB. Vercel, Render, MongoDB Atlas.")
    sh.css.append(".pulse{animation:pulse 2.4s ease-in-out infinite}"
                  "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}"
                  ".ws{animation:flow 1.2s linear infinite}@keyframes flow{to{stroke-dashoffset:-16}}")
    paper(sh); corners(sh)
    card_head(sh, "TaskFlow", "Real-time Kanban board, online since launch.")
    tag(sh, CARD_W - 28, 34, "LIVE 24/7", dot=True)
    y = 114
    box(sh, 28, y, 100, 38, "React 18", "Vercel", tsize=13, label="CLIENT")
    box(sh, 166, y, 110, 38, "Express", "Render", strong=True, tsize=13, label="API")
    cylinder(sh, 314, y - 3, 88, 44, "MongoDB", "Atlas")
    arrow(sh, f"M130 {y+11}H162")
    sh.text(146, y + 6, "REST", "mono400", 8.5, C["dim"], anchor="middle")
    sh.add(f'<path class="ws" d="M130 {y+28}H164" stroke="{C["line"]}" stroke-width="1.3" stroke-dasharray="4 4"/>')
    sh.text(147, y + 44, "WS", "mono400", 8.5, C["dim"], anchor="middle")
    arrow(sh, f"M278 {y+19}H310", dim=True)
    # broadcast to collaborators
    by = y + 72
    for i in range(4):
        bx = 176 + i * 58
        sh.add(f'<path class="ws" d="M221 {y+40}V{y+56}H{bx+18}V{by-2}" fill="none" stroke="{C["line"]}" stroke-width="1" stroke-dasharray="4 4" opacity=".7"/>')
        sh.add(f'<rect x="{bx}" y="{by}" width="36" height="22" rx="2" fill="{C["bg"]}" stroke="{C["linedim"]}" stroke-width="1"/>')
        for c in range(3):
            sh.add(f'<rect x="{bx+4+c*10}" y="{by+4}" width="8" height="{14 - (c*4 if i%2 else (2-c)*3)}" fill="{C["linedim"]}" opacity=".7"/>')
    sh.text(28, by + 8, "Socket.IO pushes", "mono400", 9.5, C["dim"])
    sh.text(28, by + 21, "every change to", "mono400", 9.5, C["dim"])
    sh.text(28, by + 34, "every board member", "mono400", 9.5, C["dim"])
    card_foot(sh, ["React 18", "TypeScript", "Redux", "Node.js", "Socket.IO", "MongoDB", "JWT"], 238)
    sh.save("work-taskflow.svg")


def cryptotracker():
    sh = Sheet(CARD_W, CARD_H, "CryptoTracker: desktop crypto tracker on .NET 8 with strict MVVM. "
                               "WPF, CommunityToolkit.Mvvm, LiveCharts, CoinGecko API.")
    sh.css.append(".spark{stroke-dasharray:420;stroke-dashoffset:420;animation:draw 1.6s ease-out 1s forwards}"
                  "@keyframes draw{to{stroke-dashoffset:0}}")
    paper(sh); corners(sh)
    card_head(sh, "CryptoTracker", "Desktop crypto tracker for Windows, strict MVVM.")
    tag(sh, CARD_W - 28, 34, "SOLO")
    y = 114
    box(sh, 28, y, 86, 34, "View", "XAML", tsize=13, label="MVVM")
    box(sh, 150, y, 110, 34, "ViewModel", "source generators", strong=True, tsize=13)
    box(sh, 296, y, 106, 34, "Service", "CoinGecko API", tsize=13)
    sh.add(f'<path d="M116 {y+12}H146" stroke="{C["line"]}" stroke-width="1.3" marker-end="url(#ah)" marker-start="url(#ah)"/>')
    sh.text(131, y + 30, "bind", "mono400", 8.5, C["dim"], anchor="middle")
    arrow(sh, f"M262 {y+12}H292")
    sh.text(277, y + 30, "async", "mono400", 8.5, C["dim"], anchor="middle")
    # price chart
    cy0, cx0, cw, ch = y + 58, 28, 250, 50
    sh.add(f'<path d="M{cx0} {cy0}V{cy0+ch}H{cx0+cw}" fill="none" stroke="{C["linedim"]}" stroke-width="1"/>')
    pts = [0.62, 0.55, 0.66, 0.48, 0.52, 0.38, 0.44, 0.30, 0.36, 0.22, 0.30, 0.18, 0.26, 0.12, 0.2, 0.08]
    poly = " ".join(f"{cx0+6+i*(cw-10)/(len(pts)-1):.1f},{cy0+p*ch:.1f}" for i, p in enumerate(pts))
    sh.add(f'<polyline class="spark" points="{poly}" fill="none" stroke="{C["line"]}" stroke-width="1.6" stroke-linejoin="round"/>')
    # period switcher
    px = 296
    for i, p in enumerate(["1D", "7D", "30D", "1Y"]):
        bx = px + i * 27
        on = p == "7D"
        sh.add(f'<rect x="{bx}" y="{cy0+6}" width="24" height="18" rx="2" fill="{C["line"] if on else "none"}" '
               f'stroke="{C["line"] if on else C["linedim"]}" stroke-width="1"/>')
        sh.text(bx + 12, cy0 + 18.5, p, "mono500", 8.5, C["bg"] if on else C["dim"], anchor="middle")
    sh.text(px, cy0 + 44, "runtime dark/light", "mono400", 9.5, C["dim"])
    card_foot(sh, ["C# 12", ".NET 8", "WPF", "MVVM Toolkit", "LiveCharts", "HttpClient", "System.Text.Json"], 238)
    sh.save("work-cryptotracker.svg")


def habitghost():
    sh = Sheet(CARD_W, CARD_H, "HabitGhost: habit and goal tracker for Windows. First place in the IT STEP "
                               "cohort. Team lead of 4. C#, WPF, TCP client-server, SQL Server.")
    paper(sh); corners(sh)
    card_head(sh, "HabitGhost", "Habit and goal tracker for Windows.")
    stamp(sh, 344, 60, 7, "1ST PLACE", "IT STEP COHORT", 124, 62, delay=0.6, size=15)
    y = 118
    box(sh, 28, y, 104, 36, "WPF client", "tray, autostart", tsize=13, label="ARCHITECTURE")
    box(sh, 166, y, 104, 36, "TCP server", "sockets", strong=True, tsize=13)
    cylinder(sh, 306, y - 3, 96, 42, "SQL Server")
    sh.add(f'<path d="M134 {y+18}H162" stroke="{C["line"]}" stroke-width="1.3" marker-end="url(#ah)" marker-start="url(#ah)"/>')
    sh.add(f'<path d="M272 {y+18}H302" stroke="{C["linedim"]}" stroke-width="1.3" marker-end="url(#ahd)" marker-start="url(#ahd)"/>')
    # team of four, lead highlighted
    ty = y + 78
    sh.text(28, ty - 18, "TEAM", "mono500", 9, C["linedim"], ls=1.2)
    for i in range(4):
        cx = 36 + i * 26
        lead = i == 0
        sh.add(f'<circle cx="{cx}" cy="{ty}" r="8" fill="{C["line"] if lead else "none"}" stroke="{C["line"] if lead else C["linedim"]}" stroke-width="1.2"/>')
    sh.add(f'<path d="M36 {ty+10}V{ty+18}H48" fill="none" stroke="{C["linedim"]}" stroke-width="1"/>')
    sh.text(52, ty + 21, "me: lead, UI/UX, models", "mono400", 9.5, C["dim"])
    sh.text(166, ty - 3, "habits, goals, analytics,", "mono400", 9.5, C["dim"])
    sh.text(166, ty + 10, "journal, reminders", "mono400", 9.5, C["dim"])
    card_foot(sh, ["C#", ".NET", "WPF", "XAML", "SQL Server", "SSMS", "TCP/IP", "Git", "Agile"], 238)
    sh.save("work-habitghost.svg")


# ================================================================= STACK SHEET
def stack():
    groups = [
        ("Core", "what I ship with", ["C#", ".NET 8", "ASP.NET Core", "Web API", "EF Core", "LINQ",
                                      "SQL Server", "PostgreSQL", "JWT"], "strong"),
        ("Frontend", "the client side", ["Angular 17", "RxJS", "React 18", "Redux", "TypeScript",
                                         "JavaScript", "HTML", "CSS"], "normal"),
        ("Design & tests", "how it holds up", ["Clean Architecture", "SOLID", "MVVM", "Repository",
                                               "Dependency injection", "xUnit", "Moq"], "normal"),
        ("Tools", "how it gets out", ["Git / GitHub", "Docker", "Azure", "CI/CD", "Agile / Scrum"], "normal"),
        ("Also used", "in real projects", ["WPF", "WinForms", "Node.js", "NestJS", "Prisma", "MongoDB",
                                           "Socket.IO", "C++", "Python"], "dim"),
    ]
    W = 880
    label_w = 150
    size = 11.5
    rows_layout = []
    y = 44
    for g in groups:
        rows = chip_rows(g[2], W - 56 - label_w, size, pad=9, gap=8)
        rows_layout.append((g, rows, y))
        y += max(len(rows) * 30, 44) + 20
    H = y + 6
    sh = Sheet(W, H, "Toolbox. Core: C#, .NET 8, ASP.NET Core, REST, EF Core, LINQ, SQL Server, PostgreSQL, JWT. "
                     "Frontend: Angular, RxJS, React, Redux, TypeScript. Design and tests: Clean Architecture, SOLID, "
                     "MVVM, xUnit, Moq. Tools: Git, Docker, Azure, CI/CD, Scrum.")
    paper(sh, 14); corners(sh)
    sh.text(28, 30, "BILL OF MATERIALS", "mono500", 9, C["linedim"], ls=1.4)
    for idx, (g, rows, y0) in enumerate(rows_layout):
        name, note, kind = g[0], g[1], g[3]
        if idx:
            sh.add(f'<path d="M28 {y0-11}H{W-28}" stroke="{C["linedim"]}" stroke-width="1" stroke-dasharray="2 4"/>')
        sh.text(28, y0 + 17, name, "sans600", 16)
        sh.text(28, y0 + 34, note, "mono400", 9.5, C["dim"])
        x0 = 28 + label_w
        for r, row in enumerate(rows):
            yy = y0 + r * 30
            for (c, w, x) in row:
                if kind == "strong":
                    stroke, fill, tc, da = C["line"], "none", C["ink"], ""
                elif kind == "dim":
                    stroke, fill, tc, da = C["linedim"], "none", C["dim"], ' stroke-dasharray="3 3"'
                else:
                    stroke, fill, tc, da = C["linedim"], "none", C["ink"], ""
                sh.add(f'<rect x="{x0+x:.1f}" y="{yy}" width="{w:.1f}" height="23" rx="2" fill="{fill}" '
                       f'stroke="{stroke}" stroke-width="{1.3 if kind=="strong" else 1}"{da}/>')
                sh.text(round(x0 + x + w / 2, 1), yy + 15.8, c, "mono400", size, tc, anchor="middle")
    sh.save("stack.svg")


# ================================================================= LINK BUTTONS
def button(name, label, icon):
    size = 12
    w = int(len(label) * size * MONO_ADV + 58)
    sh = Sheet(w, 40, label)
    sh.add(f'<rect x=".75" y=".75" width="{w-1.5}" height="38.5" rx="4" fill="{C["bg"]}" stroke="{C["line"]}" stroke-width="1.5"/>')
    sh.add(f'<g transform="translate(14 12)" fill="none" stroke="{C["line"]}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{icon}</g>')
    sh.text(40, 24.5, label, "mono500", size, C["ink"])
    sh.save(f"btn-{name}.svg")


ICONS = {
    # 16x16 line icons drawn for this set
    "site": '<rect x="0.5" y="1.5" width="15" height="13" rx="1.5"/><path d="M0.5 5.5H15.5M3 3.5h.01M5 3.5h.01"/>',
    "linkedin": '<rect x="0.5" y="0.5" width="15" height="15" rx="2"/><path d="M4.5 7V12M4.5 4.3v.01M8 12V7M8 9.2c0-1.4 1-2.3 2.1-2.3 1.2 0 1.9.8 1.9 2.3V12"/>',
    "mail": '<rect x="0.5" y="2.5" width="15" height="11" rx="1.5"/><path d="M1 3.5l7 5.2 7-5.2"/>',
    "cv": '<path d="M3 0.5h6.5L13.5 4.5V15.5H3Z"/><path d="M9.5 0.5V4.5H13.5M5.5 8.5h5.5M5.5 11.5h5.5"/>',
}


if __name__ == "__main__":
    header()
    vexa()
    url_shortener()
    taskflow()
    cryptotracker()
    habitghost()
    stack()
    button("portfolio", "Portfolio", ICONS["site"])
    button("linkedin", "LinkedIn", ICONS["linkedin"])
    button("email", "Email", ICONS["mail"])
    button("cv", "Résumé", ICONS["cv"])
