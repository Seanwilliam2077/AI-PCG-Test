"""top: crop+zoom a preview PNG in metre coordinates (frame 1.80 previews)."""
import sys
from PIL import Image

def main():
    src = sys.argv[1]
    y0, y1 = float(sys.argv[2]), float(sys.argv[3])   # metres, y0 < y1
    x0, x1 = float(sys.argv[4]), float(sys.argv[5])   # metres, screen-x
    zoom = int(sys.argv[6]) if len(sys.argv) > 6 else 3
    out = sys.argv[7] if len(sys.argv) > 7 else 'out/top_crop.png'
    im = Image.open(src).convert('RGBA')
    W, H = im.size
    s = H / 1.80                     # px per metre
    cx = W / 2.0
    row = lambda y: int(round((1.80 - y) * s))
    col = lambda x: int(round(cx + x * s))
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
    im = Image.alpha_composite(bg, im)
    c = im.crop((col(x0), row(y1), col(x1), row(y0)))
    c = c.resize((c.width * zoom, c.height * zoom), Image.NEAREST)
    c.convert('RGB').save(out)
    print(out, c.size, 'px/m at zoom', s * zoom)

main()
