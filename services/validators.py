import re
from dateparser import parse as dp

def to_int(s:str):
    s = (s or "").strip().replace(" ","")
    return int(s) if s.isdigit() else None

def is_multiple_of_50(n:int)->bool:
    return n>=50 and n%50==0

FLY_SIZES={"A7":(105,74),"A6":(148,105),"A5":(210,148),"A4":(297,210)}

def parse_fly_choice(text):
    t=(text or "").lower().replace("x","×").replace("*","×").replace("х","×")
    for k,(w,h) in FLY_SIZES.items():
        if t.startswith(k.lower()) or t.startswith(f"{w}×{h}"): return k,(w,h)
    return None

def normalize_phone(s):
    import re
    d=re.sub(r"\D","",s or "")
    if d.startswith("8") and len(d)==11: return "+7"+d[1:]
    if d.startswith("7") and len(d)==11: return "+7"+d[1:]
    if len(d)==10 and d[0]=="9": return "+7"+d
    if (s or "").strip().startswith("+7") and len(d)==11: return "+7"+d[1:]
    return None

def parse_due(text, tz):
    return dp(text, languages=["ru","en"],
              settings={"PREFER_DATES_FROM":"future","TIMEZONE":tz,"RETURN_AS_TIMEZONE_AWARE":True})

def parse_custom_size(text):
    text=(text or "").strip().replace(" ","").replace("x","×").replace("X","×").replace("*","×")
    m=re.match(r"^(\d+)[×xX*](\d+)$", text)
    if not m: return None
    w,h=int(m.group(1)),int(m.group(2))
    return (w,h) if 20<=w<=1200 and 20<=h<=1200 else None

def parse_banner_size(text):
    text=(text or "").strip().replace(" ","").replace("x","×").replace("X","×").replace("*","×")
    m=re.match(r"^(\d+(?:\.\d+)?)[×xX*](\d+(?:\.\d+)?)$", text)
    if not m: return None
    w,h=float(m.group(1)),float(m.group(2))
    return (w,h) if 0.1<=w<=20.0 and 0.1<=h<=20.0 else None

def parse_bigovka_count(text):
    try:
        n=int((text or "").strip());  return n if 0<=n<=5 else None
    except: return None