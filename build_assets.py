from pathlib import Path
import math, csv
import qrcode
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H

ROOT=Path('/mnt/data/qr_code_llm_wiki')
AS=ROOT/'assets'; AS.mkdir(exist_ok=True)
payload='QR damage test 2026 | LLM Wiki demo'
levels={'L':ERROR_CORRECT_L,'M':ERROR_CORRECT_M,'Q':ERROR_CORRECT_Q,'H':ERROR_CORRECT_H}

def make(ecc, box=12):
    qr=qrcode.QRCode(version=6,error_correction=ecc,box_size=box,border=4)
    qr.add_data(payload); qr.make(fit=False)
    return qr.make_image(fill_color='black',back_color='white').convert('RGB'), qr.modules_count, box

def decode(im):
    text, pts, straight=cv2.QRCodeDetector().detectAndDecode(np.array(im))
    return text==payload

def damage_center(im,n,box,pct):
    side=max(1,round(math.sqrt(pct)*n))
    x0=4+(n-side)//2; y0=4+(n-side)//2
    d=im.copy(); dr=ImageDraw.Draw(d)
    dr.rectangle([x0*box,y0*box,(x0+side)*box-1,(y0+side)*box-1],fill='white')
    return d, side

def damage_finder(im,n,box):
    d=im.copy(); dr=ImageDraw.Draw(d)
    x0=y0=4
    dr.rectangle([x0*box,y0*box,(x0+9)*box-1,(y0+9)*box-1],fill='white')
    return d

rows=[]
for level,ecc in levels.items():
    im,n,box=make(ecc)
    rows.append([level,'original',0,decode(im),n])
    for pct in [0.05,0.08,0.10,0.12,0.15,0.18,0.20,0.25]:
        d,side=damage_center(im,n,box,pct)
        rows.append([level,'center',pct,decode(d),n])
    d=damage_finder(im,n,box)
    rows.append([level,'top-left finder',None,decode(d),n])

with open(ROOT/'experiment_results.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f); w.writerow(['ECC level','damage pattern','nominal area ratio','OpenCV decoded','version modules']); w.writerows(rows)

# Export selected images using H level for clear demo
im,n,box=make(ERROR_CORRECT_H)
im.save(AS/'qr_original_H.png')
for pct,name in [(0.10,'qr_center_10_H.png'),(0.20,'qr_center_20_H.png'),(0.25,'qr_center_25_H.png')]:
    d,_=damage_center(im,n,box,pct); d.save(AS/name)
damage_finder(im,n,box).save(AS/'qr_finder_damaged_H.png')

# A simple annotated QR structure image. Use original QR and draw overlays in a large canvas.
base=im.resize((492,492),Image.Resampling.NEAREST)
canvas=Image.new('RGB',(980,610),'white'); canvas.paste(base,(42,58))
dr=ImageDraw.Draw(canvas)
# fonts
font_paths=['/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
fp=next((p for p in font_paths if Path(p).exists()),None)
font=ImageFont.truetype(fp,24) if fp else None
small=ImageFont.truetype(fp,18) if fp else None
# overlay boxes on QR (coordinates approximate based on border and module count)
# QR image size is (41+8)*12=588 then resized to 492 => 10.04 px/module; start quiet 4 modules ~40px in pasted base.
ox,oy=42,58; m=492/49
# helper

def boxmod(x,y,w,h,label,tx,ty):
    x1=ox+x*m; y1=oy+y*m; x2=ox+(x+w)*m; y2=oy+(y+h)*m
    dr.rectangle([x1,y1,x2,y2],outline=(20,90,180),width=4)
    dr.line([x2,y1+(y2-y1)/2,tx-12,ty+10],fill=(70,70,70),width=2)
    dr.text((tx,ty),label,fill=(20,20,20),font=font)

# module coords include 4 quiet zone around 41 modules
boxmod(4,4,7,7,'Finder pattern\n定位圖樣',590,70)
boxmod(34,4,7,7,'Finder pattern',590,145)
boxmod(4,34,7,7,'Finder pattern',590,200)
# timing line in symbol
x1=ox+(4+6)*m; y1=oy+(4+6)*m; x2=ox+(4+34)*m
# use a box around timing segments
dr.rectangle([x1, y1-3, x2, y1+6], outline=(185,90,20), width=3)
dr.line([x2,y1,578,290],fill=(70,70,70),width=2); dr.text((590,270),'Timing pattern\n時序圖樣',fill=(20,20,20),font=font)
# quiet zone frame
dr.rectangle([ox,oy,ox+492,oy+492],outline=(25,140,90),width=4)
dr.line([ox+492,oy+480,578,385],fill=(70,70,70),width=2); dr.text((590,365),'Quiet zone\n外圍留白',fill=(20,20,20),font=font)
# data region rough
dr.rectangle([ox+180,oy+180,ox+435,oy+435],outline=(135,65,160),width=4)
dr.line([ox+435,oy+300,578,475],fill=(70,70,70),width=2); dr.text((590,455),'Data + ECC\n資料與錯誤更正碼',fill=(20,20,20),font=font)
dr.text((42,12),'QR Code主要結構（示意）',fill=(20,20,20),font=font)
dr.text((590,540),'※實際還有format/version/alignment等結構',fill=(90,90,90),font=small)
canvas.save(AS/'qr_structure.png')

# Workflow SVG
svg='''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="430" viewBox="0 0 1200 430">
<defs><marker id="a" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#5b5bd6"/></marker></defs>
<rect width="1200" height="430" rx="28" fill="#f7f8fc"/>
<style>.t{font:700 25px sans-serif;fill:#1d2433}.s{font:18px sans-serif;fill:#515a6b}.b{fill:white;stroke:#cbd2e1;stroke-width:2}.c{fill:#eef0ff;stroke:#7777dc;stroke-width:2}.l{stroke:#5b5bd6;stroke-width:4;fill:none;marker-end:url(#a)}</style>
<g>
<rect class="b" x="45" y="145" rx="18" width="175" height="110"/><text class="t" x="132" y="188" text-anchor="middle">取得資料</text><text class="s" x="132" y="220" text-anchor="middle">7篇來源</text>
<rect class="b" x="270" y="145" rx="18" width="175" height="110"/><text class="t" x="357" y="188" text-anchor="middle">Ingest Wiki</text><text class="s" x="357" y="220" text-anchor="middle">切成知識頁</text>
<rect class="b" x="495" y="145" rx="18" width="175" height="110"/><text class="t" x="582" y="188" text-anchor="middle">查詢與整理</text><text class="s" x="582" y="220" text-anchor="middle">只取教學重點</text>
<rect class="c" x="720" y="145" rx="18" width="175" height="110"/><text class="t" x="807" y="188" text-anchor="middle">事實檢查</text><text class="s" x="807" y="220" text-anchor="middle">來源+實驗</text>
<rect class="b" x="945" y="145" rx="18" width="210" height="110"/><text class="t" x="1050" y="188" text-anchor="middle">產生HTML簡報</text><text class="s" x="1050" y="220" text-anchor="middle">教學化改寫</text>
<path class="l" d="M220 200 H260"/><path class="l" d="M445 200 H485"/><path class="l" d="M670 200 H710"/><path class="l" d="M895 200 H935"/>
<path class="l" d="M807 145 C807 55 582 55 582 135"/><text class="s" x="695" y="65" text-anchor="middle">不一致→回到Wiki查詢／重整</text>
<path class="l" d="M1050 255 C1050 350 807 350 807 265"/><text class="s" x="925" y="378" text-anchor="middle">簡報敘述過度簡化→退回檢查</text>
</g></svg>'''
(AS/'workflow.svg').write_text(svg,encoding='utf-8')
print('assets generated', len(rows), 'experiment rows')
