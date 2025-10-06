from datetime import datetime
def format_order_summary(ud: dict) -> str:
    lines=[]
    lines.append(f"📦 Продукт: {ud.get('what_to_print','')}")
    qty = ud.get("quantity")
    lines.append(f"📊 Количество: {qty if qty else '—'} шт")
    fmt = ud.get('format','')
    if ud.get('sheet_format')=='custom' and ud.get('custom_size_mm'):
        fmt = f"Пользовательский: {ud['custom_size_mm']}"
    elif ud.get('sheet_format'): fmt = f"{ud['sheet_format']} ({fmt})"
    if fmt: lines.append(f"📐 Формат: {fmt}")
    if ud.get('sides'): lines.append("🖨️ Печать: "+("Двусторонняя" if ud['sides']=='2' else "Односторонняя"))
    if ud.get('paper'): lines.append(f"📄 Бумага: {ud['paper']}")
    lam = {"none":"нет","matte":"мат","glossy":"глянец"}[ud.get("lamination","none")]
    lines.append(f"✨ Ламинация: {lam}")
    lines.append(f"➖ Биговка: {ud.get('bigovka_count',0)}")
    lines.append(f"🔘 Скругление углов: {'да' if ud.get('corner_rounding') else 'нет'}")
    if ud.get('material'): lines.append("📄 Материал: "+({"paper":"Бумага","vinyl":"Винил"}.get(ud['material'],ud['material'])))
    lines.append("🎨 Цветность: "+({"color":"Цветная","bw":"Ч/Б"}.get(ud.get("print_color","color"),"")))
    if ud.get('deadline_at'): lines.append("🕒 Срок: "+ud['deadline_at'].strftime('%d.%m.%Y %H:%M'))
    if ud.get('contact'): lines.append("📞 Телефон: "+ud['contact'])
    if ud.get('notes'): lines.append("💬 Пожелания: "+ud['notes'])
    return "\n".join(lines)