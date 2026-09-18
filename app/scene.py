"""Reusable deterministic revision-board art and full-screen scene cards."""
import math
from PIL import Image, ImageDraw
from app.render import font, lines, WIDTH, HEIGHT, INK, PAPER, TEAL

CORAL = '#db684f'
MUTED = '#78817c'

def paper():
    image = Image.new('RGB', (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)
    for y in range(28, HEIGHT, 36):
        for x in range(28, WIDTH, 36):
            draw.ellipse((x,y,x+2,y+2), fill='#e7e3d7')
    return image, draw

def scribble(draw, box, colour=INK):
    x,y,r,b = box
    draw.line([(x+4,y+1),(r-3,y-2),(r+1,b-3),(x-2,b+2),(x+4,y+1)], fill=colour, width=3)
    draw.line([(x+9,y+7),(r-8,y+5)], fill=colour, width=1)

def label(draw, xy, text, colour=TEAL, size=24):
    draw.text(xy, text, font=font(size), fill=colour)

def wrapped(draw, text, xy, *, size, width, colour=INK, limit=None):
    parts = lines(text,font(size),width)
    if limit and len(parts)>limit:
        raise ValueError('Scene text overflows; shorten and repeat QC')
    x,y = xy
    for part in parts:
        label(draw,(x,y),part,colour,size)
        y += int(size*1.3)
    return y

def header(draw, demo=False):
    label(draw,(64,50),'DRAWN',INK,38)
    label(draw,(64,92),'UNDER PRESSURE',TEAL,38)
    label(draw,(64,155),'A VIVA. A PAUSE. A CLEARER PICTURE.',MUTED,21)
    if demo:
        draw.rounded_rectangle((750,54,1010,110),radius=9,fill=CORAL)
        label(draw,(777,66),'STYLE DEMO',PAPER,24)

def footer(draw, demo=False):
    draw.line((64,1824,1016,1824),fill=TEAL,width=2)
    label(draw,(64,1846),'SYNTHETIC CONTENT / NOT A MEDICAL EPISODE' if demo else 'PRIMARY FRCA / SOURCE-GROUNDED REVISION',TEAL,22)

def card(topic, script, path, *, kind, text='', demo=False):
    image,draw = paper()
    header(draw,demo)
    if kind == 'pause':
        # A generic pause symbol, not a medical illustration.
        draw.ellipse((365,380,715,730),outline=TEAL,width=5)
        draw.rounded_rectangle((470,460,510,650),radius=8,fill=TEAL)
        draw.rounded_rectangle((570,460,610,650),radius=8,fill=TEAL)
        wrapped(draw,script.pause_screen_top,(100,840),size=66,width=880,limit=2)
        wrapped(draw,script.pause_screen_bottom,(100,1040),size=42,width=880,colour=TEAL,limit=2)
        wrapped(draw,topic,(100,1270),size=34,width=880,colour=MUTED,limit=3)
    else:
        label(draw,(80,400),'01 / THE EXAMINER' if kind=='examiner' else '02 / THE MEMORY HOOK',TEAL,28)
        draw.line((80,475,255,475),fill=CORAL,width=10)
        wrapped(draw,text,(80,550),size=58,width=910,limit=9)
        label(draw,(80,1400),'THINK FIRST. THEN SAY IT CLEARLY.',MUTED,24)
    footer(draw,demo)
    image.save(path)

def revision(topic, script, path, *, reveal=None, caption='', demo=False):
    image,draw = paper()
    header(draw,demo)
    y = wrapped(draw,topic,(64,235),size=58,width=950,limit=2) + 24
    draw.line((64,y,440,y-3),fill=CORAL,width=7)
    y += 32
    sections = script.board_sections
    if not 1 <= len(sections) <= 8:
        raise ValueError('Board requires 1 to 8 sections')
    layouts=[]
    for s in sections:
        headings=lines(s.heading,font(30),380)
        bullets=[lines(b,font(28),360) for b in s.bullets]
        height=76+len(headings)*40+sum(len(b)*37+12 for b in bullets)
        layouts.append((headings,bullets,max(210,height)))
    total=sum(max(l[2] for l in layouts[i:i+2])+24 for i in range(0,len(layouts),2))
    if y+total>1500:
        raise ValueError('Board text overflows; shorten the script and repeat QC')
    for start in range(0,len(sections),2):
        row_height=max(l[2] for l in layouts[start:start+2])
        for index in range(start,min(start+2,len(sections))):
            x=64+(index%2)*492
            shown=reveal is None or index<reveal
            draw.rectangle((x,y,x+460,y+row_height),fill=PAPER)
            scribble(draw,(x,y,x+460,y+row_height),TEAL if shown else '#d4d9cc')
            if not shown:
                label(draw,(x+28,y+30),f'{index+1:02}',MUTED,32)
                continue
            draw.ellipse((x+24,y+24,x+64,y+64),fill=CORAL)
            label(draw,(x+34,y+29),str(index+1),PAPER,22)
            headings,bullets,_=layouts[index]
            yy=y+82
            for line in headings:
                label(draw,(x+26,yy),line,TEAL,30)
                yy+=40
            for bullet in bullets:
                draw.line((x+27,yy+18,x+38,yy+17),fill=CORAL,width=3)
                for line in bullet:
                    label(draw,(x+51,yy),line,INK,28)
                    yy+=37
                yy+=12
        y+=row_height+24
    if caption:
        draw.rounded_rectangle((48,1530,1032,1780),radius=18,fill=INK)
        label(draw,(80,1550),'THE CANDIDATE', '#89c9bb',20)
        wrapped(draw,caption,(80,1590),size=36,width=920,colour=PAPER,limit=4)
    else:
        label(draw,(64,1590),'YOUR ONE-PAGE RECALL BOARD',TEAL,27)
        label(draw,(64,1640),'Pause here. Rehearse the answer aloud.',MUTED,25)
    footer(draw,demo)
    image.save(path)
