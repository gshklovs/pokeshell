import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import evlib as E
from evlib import L
from PIL import Image
ims=[]
for n in sys.argv[2].split(','):
    s=E.Sprite(n); r2=[''.join(ch+ch for ch in r) for r in s.rows for _ in (0,1)]
    im=L.term_png(r2,s.pal,E.WORK/'audit'/'tmp.png').convert('RGB'); ims.append(im.resize((im.width*260//im.height,260)))
o=Image.new('RGB',(sum(i.width+10 for i in ims),260)); x=0
for i in ims: o.paste(i,(x,0)); x+=i.width+10
o.save(sys.argv[1])
