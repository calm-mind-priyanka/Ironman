import re, asyncio
from math import ceil
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from db import files_col_1, files_col_2
from core.settings import get
from core.state import SEARCH_CACHE
from core.utils import clean_query, extract_filters, file_size, caption_from_template
from core.keyboards import result_kb, filter_kb

def rx(q):
    return {"$regex": re.escape(q), "$options":"i"}

async def docs_for(query, skip=0, limit=10, lang=None, quality=None, season=None):
    base = {"file_name": rx(query)}
    if lang: base["file_name"]["$regex"] = re.escape(query)
    # Add simple post-filtering so mixed filenames can be narrowed reliably.
    cur = files_col_1.find(base).sort("_id", -1).skip(skip).limit(limit * 5)
    out=[]
    async for d in cur:
        name=(d.get("file_name") or "").lower()
        if lang and lang.lower() not in name: continue
        if quality and quality.lower() not in name: continue
        if season and season.lower() not in name: continue
        out.append(d)
        if len(out)>=limit: break
    if not out and files_col_1 is not files_col_2:
        cur = files_col_2.find(base).sort("_id",-1).skip(skip).limit(limit*5)
        async for d in cur:
            name=(d.get("file_name") or "").lower()
            if lang and lang.lower() not in name: continue
            if quality and quality.lower() not in name: continue
            if season and season.lower() not in name: continue
            out.append(d)
            if len(out)>=limit: break
    return out

async def count(query, lang=None, quality=None, season=None):
    cur = files_col_1.find({"file_name":rx(query)}, {"file_name":1})
    n=0
    async for d in cur:
        name=(d.get("file_name") or "").lower()
        if lang and lang.lower() not in name: continue
        if quality and quality.lower() not in name: continue
        if season and season.lower() not in name: continue
        n+=1
    return n

async def render(client, message, query, page=0, lang=None, quality=None, season=None):
    s = await get(message.chat.id)
    limit=max(1,min(20,int(s.get("max_results",10))))
    total=await count(query,lang,quality,season)
    pages=max(1,ceil(total/limit))
    page=min(page,pages-1)
    docs=await docs_for(query,page*limit,limit,lang,quality,season)
    if not docs: return await message.edit_text("❌ No matching files.")
    SEARCH_CACHE[(message.chat.id,message.id)]={"query":query,"page":page,"docs":docs,"lang":lang,"quality":quality,"season":season}
    rows=[]
    for i,d in enumerate(docs):
        label=(d.get("file_name") or "File")[:50]
        rows.append([InlineKeyboardButton(f"📁 {label}",callback_data=f"file#{message.id}#{i}")])
    rows.append([InlineKeyboardButton("🔤 LANGUAGE",callback_data=f"lang#{message.id}"),
                 InlineKeyboardButton("🎞 QUALITY",callback_data=f"quality#{message.id}")])
    rows.append([InlineKeyboardButton("🌟 SEASON",callback_data=f"season#{message.id}"),
                 InlineKeyboardButton("📤 SEND ALL",callback_data=f"sendall#{message.id}")])
    nav=[]
    if page: nav.append(InlineKeyboardButton("<< PREV",callback_data=f"page#{message.id}#{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{pages}",callback_data="noop"))
    if page+1<pages: nav.append(InlineKeyboardButton("NEXT >>",callback_data=f"page#{message.id}#{page+1}"))
    rows.append(nav)
    await message.edit_text(f"🔎 **Results for:** `{query}`\n\nTotal: `{total}`",reply_markup=InlineKeyboardMarkup(rows))

def register(app):
    @app.on_message(filters.command("cancel") & filters.private, group=0)
    async def cancel(_,m):
        from core.state import INPUT
        INPUT.pop(m.from_user.id,None); await m.reply_text("❌ Cancelled.")

    @app.on_message(filters.text & ~filters.command(["start","help","settings","stats","index","add_premium","remove_premium","broadcast","cancel"]), group=10)
    async def search(_,m):
        if not m.from_user: return
        q=clean_query(m.text)
        if len(q)<2: return
        s=await get(m.chat.id)
        if not s.get("auto_filter",True): return
        await m.reply_text("🔎 Searching...")
        # Edit the same message for stable callback IDs.
        status=await m.reply_text("⏳ Preparing results...")
        await render(app,status,q)

    @app.on_callback_query(filters.regex(r"^noop$"))
    async def noop(_,q): await q.answer()

    @app.on_callback_query(filters.regex(r"^page#"))
    async def page(_,q):
        await q.answer()
        data=SEARCH_CACHE.get((q.message.chat.id,q.message.reply_to_message_id or q.message.id))
        # Search message id is stored in callback; retrieve by parsing.
        parts=q.data.split("#"); mid=int(parts[1]); page_no=int(parts[2])
        data=SEARCH_CACHE.get((q.message.chat.id,mid))
        if not data: return await q.message.edit_text("❌ Search expired. Search again.")
        await render(app,q.message,data["query"],page_no,data["lang"],data["quality"],data["season"])

    @app.on_callback_query(filters.regex(r"^(lang|quality|season)#"))
    async def filter_menu(_,q):
        kind,mid=q.data.split("#"); data=SEARCH_CACHE.get((q.message.chat.id,int(mid)))
        if not data: return await q.answer("Search expired.",show_alert=True)
        vals = (data["lang"], data["quality"], data["season"])
        names = {"lang":"lang","quality":"quality","season":"season"}
        langs, quals, seasons = extract_filters(" ".join(d.get("file_name","") for d in data["docs"]))
        values = langs if kind=="lang" else quals if kind=="quality" else seasons
        if not values: return await q.answer("No filters found on this page.",show_alert=True)
        await q.message.edit_text(f"Choose {kind}:",reply_markup=filter_kb(kind,mid,values))
        await q.answer()

    @app.on_callback_query(filters.regex(r"^apply#"))
    async def apply(_,q):
        _,kind,mid,val=q.data.split("#",3)
        data=SEARCH_CACHE.get((q.message.chat.id,int(mid)))
        if not data: return await q.answer("Search expired.",show_alert=True)
        kw={"lang":"lang","quality":"quality","season":"season"}[kind]
        await q.answer()
        await render(app,q.message,data["query"],0,val if kw=="lang" else data["lang"],
                     val if kw=="quality" else data["quality"],val if kw=="season" else data["season"])

    @app.on_callback_query(filters.regex(r"^back#"))
    async def back(_,q):
        mid=int(q.data.split("#")[1]); data=SEARCH_CACHE.get((q.message.chat.id,mid))
        if data: await render(app,q.message,data["query"],data["page"],data["lang"],data["quality"],data["season"])
        await q.answer()

    @app.on_callback_query(filters.regex(r"^file#"))
    async def file(_,q):
        _,mid,idx=q.data.split("#"); data=SEARCH_CACHE.get((q.message.chat.id,int(mid)))
        if not data: return await q.answer("Search expired.",show_alert=True)
        doc=data["docs"][int(idx)]
        s=await get(q.message.chat.id)
        cap=caption_from_template(s.get("files_caption"),doc.get("file_name"),file_size(doc.get("file_size")))
        try:
            await app.send_cached_media(q.from_user.id,doc["file_id"],caption=cap,protect_content=bool(s.get("file_secure",True)))
            await q.answer("✅ File sent")
        except Exception:
            await q.answer("❌ Could not send file.",show_alert=True)

    @app.on_callback_query(filters.regex(r"^sendall#"))
    async def sendall(_,q):
        _,mid=q.data.split("#"); data=SEARCH_CACHE.get((q.message.chat.id,int(mid)))
        if not data: return await q.answer("Search expired.",show_alert=True)
        s=await get(q.message.chat.id)
        await q.answer("Sending...")
        for d in data["docs"]:
            try:
                cap=caption_from_template(s.get("files_caption"),d.get("file_name"),file_size(d.get("file_size")))
                await app.send_cached_media(q.from_user.id,d["file_id"],caption=cap,protect_content=bool(s.get("file_secure",True)))
                await asyncio.sleep(0.25)
            except Exception: pass
