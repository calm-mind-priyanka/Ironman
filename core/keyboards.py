from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def start_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 My Plan", callback_data="plan"),
         InlineKeyboardButton("⚙️ Help", callback_data="help")],
        [InlineKeyboardButton("🔎 Search", switch_inline_query_current_chat="")],
    ])

def settings_kb(s):
    def on(v): return "ON ✅" if v else "OFF ❌"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📝 AUTO FILTER: {on(s.get('auto_filter', True))}", callback_data="set#auto_filter"),
         InlineKeyboardButton(f"🔒 FILE SECURE: {on(s.get('file_secure', True))}", callback_data="set#file_secure")],
        [InlineKeyboardButton(f"🈴 IMDB: {on(s.get('imdb', True))}", callback_data="set#imdb"),
         InlineKeyboardButton(f"🔍 SPELL CHECK: {on(s.get('spell_check', True))}", callback_data="set#spell_check")],
        [InlineKeyboardButton(f"🗑️ AUTO DELETE: {on(s.get('auto_delete', False))}", callback_data="set#auto_delete"),
         InlineKeyboardButton(f"📚 RESULT MODE: {'BUTTON 📚' if s.get('result_mode', True) else 'TEXT 📋'}", callback_data="set#result_mode")],
        [InlineKeyboardButton(f"📁 FILES MODE: {'SHORTLINK 🔗' if s.get('files_mode', True) else 'DIRECT 📁'}", callback_data="set#files_mode"),
         InlineKeyboardButton("📋 FILES CAPTION", callback_data="caption")],
        [InlineKeyboardButton("🥁 TUTORIAL LINK", callback_data="tutorial"),
         InlineKeyboardButton("🔗 SET SHORTLINK", callback_data="shortlink")],
        [InlineKeyboardButton("📢 SET MOVIE REQ", callback_data="movie_req"),
         InlineKeyboardButton("💡 DETAILS", callback_data="details")],
        [InlineKeyboardButton("👥 FORCE CHANNEL", callback_data="forcesub"),
         InlineKeyboardButton(f"ℹ️ MAX RES: {s.get('max_results', 10)}", callback_data="max_results")],
        [InlineKeyboardButton("‼️ CLOSE SETTINGS MENU ‼️", callback_data="close_settings")],
    ])

def result_kb(query, page, total_pages, langs, quals, seasons):
    rows = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("<< PREV", callback_data=f"page#{query}#{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1} / {total_pages}", callback_data="noop"))
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton("NEXT >>", callback_data=f"page#{query}#{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([
        InlineKeyboardButton("LANGUAGE", callback_data=f"lang#{query}"),
        InlineKeyboardButton("QUALITY", callback_data=f"quality#{query}")
    ])
    rows.append([
        InlineKeyboardButton("SEASON", callback_data=f"season#{query}"),
        InlineKeyboardButton("SEND ALL", callback_data=f"sendall#{query}")
    ])
    return InlineKeyboardMarkup(rows)

def filter_kb(prefix, query, values):
    rows = [[InlineKeyboardButton(v.title(), callback_data=f"apply#{prefix}#{query}#{v}")] for v in values]
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data=f"back#{query}")])
    return InlineKeyboardMarkup(rows)
