import re
from datetime import datetime

def clean_query(text):
    text = re.sub(r"[_\.]+", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def file_size(n):
    if not n:
        return "Unknown"
    units = ["B", "KB", "MB", "GB", "TB"]
    n = float(n)
    for unit in units:
        if n < 1024 or unit == units[-1]:
            return f"{n:.1f} {unit}"
        n /= 1024

def extract_filters(name):
    s = (name or "").lower()
    languages = []
    for x in ["hindi", "english", "tamil", "telugu", "malayalam", "kannada", "bengali", "punjabi", "dual audio"]:
        if x in s:
            languages.append(x)
    qualities = []
    for x in ["2160p", "4k", "1080p", "720p", "480p", "360p", "hdr", "web-dl", "webrip", "bluray"]:
        if x in s:
            qualities.append(x)
    seasons = sorted(set(re.findall(r"\bs\d{1,2}\b", s)))
    return languages, qualities, seasons

def caption_from_template(template, name, size):
    return (template or "{file_name}").replace("{file_name}", name or "File").replace("{file_size}", size or "Unknown")
