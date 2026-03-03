import os
import streamlit as st
import time
from openai import OpenAI
import glob
import re
import yaml

st.set_page_config(page_title="Komiksy Jakuba Martewicza", page_icon="💬")


import base64

def set_bg(image_path: str):
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{data}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        .stApp::before {{
            content: "";
            position: fixed;
            inset: 0;
            background: linear-gradient(
                rgba(0,0,0,0.35) 0%,
                rgba(0,0,0,0.50) 40%,
                rgba(0,0,0,0.65) 100%
            );
            z-index: 0;
            pointer-events: none;
        }}

        .main, header, footer, [data-testid="stSidebar"] {{
            position: relative;
            z-index: 1;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


set_bg("assets/backgroundpic.png")


st.markdown("""
<h1 style="
background: linear-gradient(
90deg,
#064E3B 0%,
#065F46 18%,
#047857 36%,
#059669 54%,
#10B981 72%,
#6EE7B7 100%
);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
text-shadow: 0 0 14px rgba(16,185,129,0.15);
font-weight:700;
letter-spacing:0.4px;
">
💬 Komiksy Jakuba Martewicza
</h1>
<h3 style="color:#D1FAE5; font-weight:500;">
Lora, Wirtualna Asystentka AI
</h3>
""", unsafe_allow_html=True)



st.caption(
    "Zadaj Lorze pytanie o moje komiksy w okienku czatu poniżej🙂",
    unsafe_allow_html=True
)

# --- STATUS (CSS + dynamiczny placeholder) ---
st.markdown("""
<style>
.pulse-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  margin-right: 8px;
  border-radius: 50%;
  transform: translateY(1px);
}

/* 🟢 ONLINE */
.pulse-online {
  background: #6EE7B7;
  box-shadow: 0 0 0 0 rgba(110, 231, 183, 0.7);
  animation: pulse-online 1.4s infinite;
}
@keyframes pulse-online {
  0%   { box-shadow: 0 0 0 0 rgba(110, 231, 183, 0.7); }
  70%  { box-shadow: 0 0 0 10px rgba(110, 231, 183, 0.0); }
  100% { box-shadow: 0 0 0 0 rgba(110, 231, 183, 0.0); }
}

/* 🟣 TYPING */
.pulse-typing {
  background: #A78BFA;
  box-shadow: 0 0 0 0 rgba(167, 139, 250, 0.7);
  animation: pulse-typing 1.2s infinite;
}
@keyframes pulse-typing {
  0%   { box-shadow: 0 0 0 0 rgba(167, 139, 250, 0.7); }
  70%  { box-shadow: 0 0 0 10px rgba(167, 139, 250, 0.0); }
  100% { box-shadow: 0 0 0 0 rgba(167, 139, 250, 0.0); }
}
</style>
""", unsafe_allow_html=True)

status_placeholder = st.empty()

def show_online():
    status_placeholder.markdown(
        """
        <div style="margin-top:-8px;margin-bottom:10px;color:#9FB3C8;font-size:14px;">
            <span class="pulse-dot pulse-online"></span>
            <strong>Online</strong> • Odpowiada zwykle w kilka sekund
        </div>
        """,
        unsafe_allow_html=True
    )

def show_typing():
    status_placeholder.markdown(
        """
        <div style="margin-top:-8px;margin-bottom:10px;color:#9FB3C8;font-size:14px;">
            <span class="pulse-dot pulse-typing"></span>
            <strong>Asystent jest w akcji!:)</strong>
        </div>
        """,
        unsafe_allow_html=True
    )

# Startowo: online
show_online()
# --- /STATUS ---

def split_front_matter(md_text: str):
    """
    Obsługuje dwa formaty:
    1) --- (YAML) --- (MARKDOWN)
    2) YAML na górze bez --- , do pierwszej pustej linii, potem MARKDOWN
    """
    text = (md_text or "").lstrip("\ufeff")  # usuń BOM jeśli jest

    # Format 1: klasyczny front-matter
    if text.lstrip().startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1].strip()) or {}
            body = parts[2].strip()
            return meta, body
        return {}, text.strip()

    # Format 2: "goły YAML" na początku pliku
    lines = text.splitlines()
    yaml_lines = []
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip() == "":
            body_start = i + 1
            break
        yaml_lines.append(line)
    else:
        # cały plik bez pustej linii -> traktuj jako YAML bez body
        body_start = len(lines)

    yaml_block = "\n".join(yaml_lines).strip()
    meta = {}
    if yaml_block:
        try:
            meta = yaml.safe_load(yaml_block) or {}
        except Exception:
            meta = {}

    body = "\n".join(lines[body_start:]).strip()
    return meta, body


def load_comics(folder: str = "data/comics"):
    docs = []
    for path in sorted(glob.glob(f"{folder}/*.md")):
        if path.lower().endswith("comic_template.md"):
            continue
        raw = open(path, "r", encoding="utf-8").read()
        try:
            meta, body = split_front_matter(raw)
        except Exception as e:
            st.warning(f"⚠️ Błąd YAML/front-matter w pliku: {path} → {e}")
            continue

        # minimalne wymagane pola
        if not meta.get("id") or not meta.get("title") or not meta.get("year"):
            st.warning(f"⚠️ Plik pominięty (brak id/title/year): {path}")
            continue

        docs.append({"path": path, "meta": meta, "body": body})
    return docs


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def build_catalog(docs) -> str:
    items = []
    for d in docs:
        m = d["meta"]
        items.append(
            f"- {m.get('title')} ({m.get('year')}) — seria: {m.get('series')}, zeszyt: {m.get('issue') or '-'}"
        )

    return (
        "W bazie mam takie komiksy:\n" + "\n".join(items)
        if items else
        "Baza komiksów jest pusta."
    )
    
def rag_light_context(question: str, docs, k: int = 4) -> str:
    q = normalize(question)
    
    # ✅ INTENCJA: bardzo ogólne pytanie o komiksy -> pokaż listę
    general_catalog_intent = q in {"komiksy", "komiks", "twoje komiksy", "twoj komiks", "katalog", "oferta"}
    
    if general_catalog_intent:
        return build_catalog(docs)

    # 🔥 FALLBACK — pytanie ogólne o listę wydań (nawet bez słowa "komiks")
    
    list_intent = any(x in q for x in [
        "jakie", "jakiew", "jaki", "lista", "spis", "wszystkie", "wydane"
    ])
    
    release_intent = any(x in q for x in [
        "wyda", "wydal", "wydał", "wydałeś", "wydales", "wydalem", "wydałem"
    ])
    
    if list_intent and release_intent:
        items = []
        for d in docs:
            m = d["meta"]
            items.append(
                f"- {m.get('title')} ({m.get('year')}) — seria: {m.get('series')}, zeszyt: {m.get('issue')}"
            )
    
        return "W bazie mam takie komiksy:\n" + "\n".join(items)

    tokens = [t for t in re.findall(r"[a-ząćęłńóśźż0-9]+", q) if len(t) >= 3]
    if not tokens:
        return "Brak sensownych słów kluczowych w pytaniu."

    def score(doc):
        m = doc["meta"]
        body = normalize(doc["body"])
        title = normalize(str(m.get("title", "")))
        synopsis = normalize(str(m.get("synopsis", "")))
        keywords = " ".join([normalize(x) for x in (m.get("keywords") or [])])
        themes = " ".join([normalize(x) for x in (m.get("themes") or [])])
        chars = " ".join([normalize(x) for x in (m.get("characters") or [])])
        series = normalize(str(m.get("series", "")))

        s = 0
        for t in tokens:
            if t in title:    s += 8
            if t in keywords: s += 6
            if t in chars:    s += 5
            if t in themes:   s += 4
            if t in series:   s += 3
            if t in synopsis: s += 4
            if t in body:     s += 1

        # 🔥 BONUS — dopasowanie całej frazy pytania
        if q and q in title:
            s += 10
        if q and q in series:
            s += 6
        if q and q in keywords:
            s += 6

        return s

    scored = [(score(d), d) for d in docs]
    scored = [x for x in scored if x[0] > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [d for _, d in scored[:k]]

    if not top:
        # ✅ zamiast ślepego "brak", daj użytkownikowi użyteczną odpowiedź
        return build_catalog(docs) + "\n\n(Jeśli doprecyzujesz tytuł/serię/postać, zawężę wyniki.)"


    blocks = []
    for d in top:
        m = d["meta"]
        header = (
            f"ID: {m.get('id')}\n"
            f"Tytuł: {m.get('title')}\n"
            f"Rok: {m.get('year')}\n"
            f"Seria: {m.get('series')}\n"
            f"Zeszyt: {m.get('issue') or '-'}\n"
            f"Słowa kluczowe: {', '.join(m.get('keywords') or [])}\n"
            f"Streszczenie: {m.get('synopsis')}\n"
        )
        body = (d["body"] or "").strip()
        if len(body) > 1200:
            body = body[:1200] + "…"
        blocks.append(header + "\nOPIS (MD):\n" + body)

    context = "\n\n---\n\n".join(blocks)
    return context[:6000]  # limit znaków, żeby prompt nie urósł za bardzo


from pathlib import Path
import os

def comics_cache_key(folder="data/comics"):
    files = sorted(Path(folder).glob("*.md"))
    return tuple((str(p), os.path.getmtime(p)) for p in files)

@st.cache_data
def load_comics_cached(_key):
    return load_comics("data/comics")

comics_docs = load_comics_cached(comics_cache_key())

def last_messages(messages, n=12):
    # zostawiamy pierwszy system_prompt, a potem tylko ostatnie n wiadomości user/assistant
    sys = [messages[0]]  # system_prompt
    tail = messages[1:][-n:]
    return sys + tail

api_key = os.getenv("OPENAI_API_KEY")

comics_docs = load_comics_cached()

feedback_text = os.getenv("FEEDBACK_TEXT", "")

if not api_key:
    st.error("Brak OPENAI_API_KEY")
    st.stop()

client = OpenAI(api_key=api_key)

# prompty się zaczynają
system_prompt = (
    "Jesteś asystentką AI (w formie żeńskiej!) autora komiksów Jakuba Martewicza. Masz na immię Lora. "
    "Odpowiadasz na pytania o wydane komiksy.\n\n"
    "ZASADY:\n"
    "- Odpowiadaj w języku użytkownika i jeśli to możliwe, w formie żeńskiej.\n"
    "- Opieraj się WYŁĄCZNIE na kontekście dostarczonym w wiadomości 'DOPASOWANE FRAGMENTY Z BAZY KOMIKSÓW'.\n"
    "- Nie wymyślaj faktów. Jeśli brak danych — powiedz to wprost.\n"
    "- Spoilery tylko jeśli użytkownik wyraźnie poprosi.\n\n"
    "STYL:\n"
    "- Rzeczowo, konkretnie, ale na luzie. Make small talk if initiated by the user.\n\n"
    "DODATKOWY KONTEKST (parafrazuj):\n"
    f"{feedback_text}"
)


# Reset button
if st.button("Resetuj rozmowę"):
    st.session_state.pop("messages", None)

# Init chat (bez wrzucania CV do historii jako user message)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": "Cześć! 👋 Jestem Lora, wirtualna asystentka Jakuba. O co chcesz zapytać?"}
    ]

question = st.chat_input("Tutaj wpisz Twoje pytanie i naciśnij enter lub kliknij strzałkę")


if question and question.strip():
    q = question.strip()
    st.session_state.messages.append({"role": "user", "content": q})
    show_typing()

    typing_container = st.empty()
    with typing_container.container():
        with st.chat_message("assistant", avatar="jakub.png"):
            typing_placeholder = st.empty()
            answer_placeholder = st.empty()

    dots = ["", ".", "..", "..."]
    i = 0
    full_text = ""
    last_tick = time.time()

    context = rag_light_context(q, comics_docs, k=4)

    # bierzemy ostatnie wiadomości, ale BEZ tego świeżo dodanego pytania usera
    base_messages = last_messages(st.session_state.messages[:-1], n=12)

    messages_for_api = (
        base_messages
        + [{"role": "user", "content": "DOPASOWANE FRAGMENTY Z BAZY KOMIKSÓW:\n\n" + context}]
        + [{"role": "user", "content": q}]
    )

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages_for_api,
        stream=True,
    )

    for event in stream:
        now = time.time()
        if now - last_tick > 0.15:
            typing_placeholder.markdown(f"_Jakub pisze{dots[i % len(dots)]}_")
            i += 1
            last_tick = now

        delta = event.choices[0].delta
        if delta and getattr(delta, "content", None):
            full_text += delta.content
            answer_placeholder.markdown(full_text)

    typing_container.empty()
    st.session_state.messages.append({"role": "assistant", "content": full_text.strip()})
    show_online()


st.divider()

for m in st.session_state.messages:
    role = m.get("role", "")
    if role not in ("user", "assistant"):
        continue  # nie pokazuj system/tool/etc.

    with st.chat_message(
        role,
        avatar="jakub.png" if role == "assistant" else "🙂"
    ):
        st.markdown(m["content"])

st.markdown(
    """
    <script>
    window.scrollTo(0, document.body.scrollHeight);
    </script>
    """,
    unsafe_allow_html=True
)




































































































