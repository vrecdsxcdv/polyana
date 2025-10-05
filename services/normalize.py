# services/normalize.py
import re

EMOJI_RE = re.compile(r'[\u2600-\u26FF\u2700-\u27BF\U0001F000-\U0001FAFF]+')
SPACES_RE = re.compile(r'\s+')

ALIASES = {
    "визитки": {"визитки","🪪 визитки","визитка","визитка 90x50","визитка 90×50"},
    "флаеры": {"флаеры","📄 флаеры","буклеты","буклет"},
    "баннеры": {"баннеры","🖼 баннеры","баннер"},
    "плакаты": {"плакаты","📰 плакаты","плакат"},
    "наклейки": {"наклейки","🏷 наклейки","наклейка"},
    "листы": {"листы","📚 листы","листы а4","листы а3"},
    "другое": {"другое","📦 другое"},
    "обычная печать": {"обычная печать","🖨 обычная печать"},
    "назад": {"назад","⬅️ назад","/back","back"},
    "отмена": {"отмена","❌ отмена","/cancel","cancel"},
    "далее": {"далее","➡️ далее","/next","next"},
    "пропустить": {"пропустить","⏭️ пропустить","skip"},
}

def norm_btn(text: str) -> str:
    t = text or ""
    t = EMOJI_RE.sub("", t)
    t = t.lower().strip()
    t = SPACES_RE.sub(" ", t)
    return t

def is_btn(text: str, key: str) -> bool:
    t = norm_btn(text)
    return any(t == norm_btn(a) for a in ALIASES.get(key, {key}))

def just_text(text: str) -> str:
    return SPACES_RE.sub(" ", EMOJI_RE.sub("", text or "")).strip()