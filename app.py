from flask import Flask, render_template, request, send_file, abort
from io import BytesIO
from datetime import date
import secrets
import qrcode
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader

app = Flask(__name__)

DEFAULTS = {
    "member_name": "Nama Member",
    "title": "CERTIFICATE OF MEMBERSHIP",
    "intro": "This certificate is proudly presented to",
    "description": "In recognition of being part of the Mineblox Community.",
    "period": "2025 – 2027",
    "issued_date": date.today().strftime("%d %B %Y"),
    "community": "MINEBLOX COMMUNITY",
    "signer": "Mineblox Team",
    "role": "Community Representative",
}

def clean_form(source):
    data = {}
    for key, default in DEFAULTS.items():
        value = source.get(key, default).strip()
        data[key] = value[:180] if value else default
    data["certificate_id"] = source.get("certificate_id", "").strip()[:40] or secrets.token_hex(4).upper()
    return data

@app.route("/", methods=["GET", "POST"])
def index():
    data = clean_form(request.form) if request.method == "POST" else {**DEFAULTS, "certificate_id": secrets.token_hex(4).upper()}
    return render_template("index.html", data=data)

def make_qr(data):
    # This QR is a decorative identifier, not an online verification service.
    qr = qrcode.QRCode(box_size=5, border=1)
    qr.add_data(f"Mineblox community certificate ID: {data['certificate_id']}")
    qr.make(fit=True)
    return qr.make_image(fill_color="#17233b", back_color="white").convert("RGB")

def font_path(bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if __import__("os").path.exists(p):
            return p
    return None

def fit_font(draw, text, path, start, max_width):
    size = start
    while size > 18:
        f = ImageFont.truetype(path, size) if path else ImageFont.load_default()
        if draw.textbbox((0, 0), text, font=f)[2] <= max_width:
            return f
        size -= 2
    return ImageFont.truetype(path, size) if path else ImageFont.load_default()

def render_png(data):
    W, H = 1600, 1131
    img = Image.new("RGB", (W, H), "#f7f5ef")
    d = ImageDraw.Draw(img)
    navy, gold, ink = "#14233d", "#c7a45a", "#263247"
    d.rectangle((28, 28, W-28, H-28), outline=navy, width=12)
    d.rectangle((48, 48, W-48, H-48), outline=gold, width=3)
    d.rectangle((70, 70, W-70, H-70), outline="#d9c99f", width=1)
    # restrained corner accents
    for x, y, sx, sy in [(85,85,1,1),(W-85,85,-1,1),(85,H-85,1,-1),(W-85,H-85,-1,-1)]:
        d.line((x,y,x+55*sx,y), fill=gold, width=4)
        d.line((x,y,x,y+55*sy), fill=gold, width=4)

    regular, bold = font_path(False), font_path(True)
    def f(size, is_bold=False):
        p = bold if is_bold else regular
        return ImageFont.truetype(p, size) if p else ImageFont.load_default()
    def centered(text, y, font, fill):
        box = d.textbbox((0,0), text, font=font)
        d.text(((W-(box[2]-box[0]))/2, y), text, font=font, fill=fill)

    centered(data["community"].upper(), 120, f(34, True), navy)
    centered("✦", 178, f(34, True), gold)
    centered(data["title"].upper(), 240, f(42, True), ink)
    centered(data["intro"], 340, f(27), ink)
    name_font = fit_font(d, data["member_name"].upper(), bold, 76, 1260)
    centered(data["member_name"].upper(), 405, name_font, navy)
    d.line((300, 515, 1300, 515), fill=gold, width=3)
    # wrap description into up to two centered lines
    words, lines, line = data["description"].split(), [], ""
    for word in words:
        test = (line + " " + word).strip()
        if d.textbbox((0,0), test, font=f(25))[2] > 1180 and line:
            lines.append(line); line = word
        else:
            line = test
    if line: lines.append(line)
    for i, text in enumerate(lines[:2]):
        centered(text, 555 + i*42, f(25), ink)
    centered("MEMBERSHIP PERIOD", 680, f(19, True), gold)
    centered(data["period"], 715, f(34, True), navy)
    centered(f"Certificate ID: {data['certificate_id']}     •     Issued: {data['issued_date']}", 805, f(18), ink)
    # signature area
    d.line((1010, 960, 1350, 960), fill=navy, width=2)
    centered_sign = data["signer"]
    d.text((1010, 970), centered_sign, font=f(22, True), fill=navy)
    d.text((1010, 1005), data["role"], font=f(16), fill=ink)
    qr = make_qr(data).resize((112,112))
    img.paste(qr, (135, 900))
    d.text((260, 940), "MEMBERSHIP", font=f(15, True), fill=gold)
    d.text((260, 966), "CERTIFICATE", font=f(15, True), fill=gold)
    return img

@app.route("/download/png", methods=["POST"])
def download_png():
    data = clean_form(request.form)
    output = BytesIO()
    render_png(data).save(output, format="PNG", dpi=(300,300))
    output.seek(0)
    return send_file(output, mimetype="image/png", as_attachment=True, download_name=f"mineblox-{data['certificate_id']}.png")

@app.route("/download/pdf", methods=["POST"])
def download_pdf():
    data = clean_form(request.form)
    png = render_png(data)
    png_io = BytesIO()
    png.save(png_io, format="PNG", dpi=(300,300))
    png_io.seek(0)
    output = BytesIO()
    page = landscape(A4)
    c = canvas.Canvas(output, pagesize=page)
    c.drawImage(ImageReader(png_io), 0, 0, width=page[0], height=page[1])
    c.save()
    output.seek(0)
    return send_file(output, mimetype="application/pdf", as_attachment=True, download_name=f"mineblox-{data['certificate_id']}.pdf")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
