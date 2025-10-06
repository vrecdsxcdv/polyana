import re
EMOJI_RE = re.compile(r'[\u2600-\u26FF\u2700-\u27BF\U0001F000-\U0001FAFF]+')
SPACES_RE = re.compile(r'\s+')

ALIASES = {
  "визитки":{"визитки","🪪 визитки","визитка"},
  "флаеры":{"флаеры","📄 флаеры","буклеты"},
  "баннеры":{"баннеры","🖼 баннеры"},
  "плакаты":{"плакаты","📰 плакаты"},
  "наклейки":{"наклейки","🏷 наклейки"},
  "листы":{"листы","📚 листы","обычная печать","🖨 обычная печать"},
  "другое":{"другое","📦 другое"},
  "назад":{"назад","⬅️ назад","/back","back"},
  "отмена":{"отмена","❌ отмена","/cancel","cancel"},
  "далее":{"далее","➡️ далее","/next","next"},
  "пропустить":{"пропустить","⏭️ пропустить"},
}

def norm_btn(t:str)->str:
    t = t or ""
    t = EMOJI_RE.sub("", t)
    t = t.lower().strip()
    t = SPACES_RE.sub(" ", t)
    return t

def is_btn(text: str, key: str) -> bool:
    t = norm_btn(text)
    return any(t == norm_btn(a) for a in ALIASES.get(key, {key}))