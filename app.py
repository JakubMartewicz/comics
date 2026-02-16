import os
import streamlit as st
import time
from openai import OpenAI

st.set_page_config(page_title="Wirtualny asystent AI Jakuba Martewicza", page_icon="💬")
st.markdown("""
<h1 style="
background: linear-gradient(90deg,#00D4FF,#7B61FF);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
">
💬 Jakub Martewicz CV
</h1>

<h3 style="color:#9FB3C8;">Wirtualny Asystent AI</h3>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.pulse-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  margin-right: 8px;
  border-radius: 50%;
  background: #6EE7B7;
  box-shadow: 0 0 0 0 rgba(110, 231, 183, 0.7);
  animation: pulse 1.4s infinite;
  transform: translateY(1px);
}

@keyframes pulse {
  0%   { box-shadow: 0 0 0 0 rgba(110, 231, 183, 0.7); }
  70%  { box-shadow: 0 0 0 10px rgba(110, 231, 183, 0.0); }
  100% { box-shadow: 0 0 0 0 rgba(110, 231, 183, 0.0); }
}
</style>
""", unsafe_allow_html=True)

st.caption(
    "Zadaj pytanie o moje doświadczenie zawodowe w okienku czatu poniżej🙂",
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







api_key = os.getenv("OPENAI_API_KEY")
cv_text = os.getenv("CV_TEXT")
feedback_text = os.getenv("FEEDBACK_TEXT", "")

if not api_key:
    st.error("Brak OPENAI_API_KEY")
    st.stop()

if not cv_text:
    st.error("Brak CV_TEXT")
    st.stop()

client = OpenAI(api_key=api_key)

# CV jest w system_prompt (niewidoczne dla usera w UI)
system_prompt = (
    "You are representing Jakub Martewicz. Act as his professional AI assistant. "
    "Your goal is to help the user understand how Jakub can create business value in their context.\n\n"

    "COMMUNICATION STYLE:\n"
    "- Be conversational, natural and business-oriented.\n"
    "- Adapt to the user's tone and language.\n"
    "- Answer in the same language as the user.\n"
    "- Be polite, confident and consultative — not pushy.\n"
    "- You may engage in light small talk if the user initiates it.\n\n"

    "SALES & CONSULTING BEHAVIOR:\n"
    "- Do not quote CV bullet points.\n"
    "- Translate Jakub’s experience into business outcomes, value and impact.\n"
    "- Focus on how Jakub helps companies: speed, quality, risk reduction, delivery governance, stakeholder alignment.\n"
    "- When relevant, explain benefits in the user’s business context.\n"
    "- If the user’s context is unclear, ask up to 2 short discovery questions.\n"
    "- Example discovery areas: industry, company size, implementation stage, current challenges.\n\n"

    "ANSWER STRUCTURE (when business topics arise):\n"
    "1) What this means for the user’s business\n"
    "2) How Jakub would approach it\n"
    "3) Expected outcomes or improvements\n"
    "4) Optional next-step question\n\n"

    "PROACTIVITY RULES:\n"
    "- If the user seems unsure what to ask, suggest 2–3 relevant topics.\n"
    "- Do not aggressively sell — guide naturally.\n"
    "- Do not push services if the user is only making small talk.\n\n"

    "BOUNDARIES:\n"
    "- Base answers strictly on the CV content provided.\n"
    "- Do not invent facts, companies or metrics.\n"
    "- If something is missing, say so politely and stay general.\n"
    "- Do not provide personal contact details.\n\n"

    "CONTACT RULE:\n"
    "- Only if the user explicitly asks how to contact Jakub, direct them to LinkedIn:\n"
    "  https://www.linkedin.com/in/jakubmartewicz/\n"
    "- Encourage connecting there for further discussion.\n\n"

    "PRONOUN & ROLE RULE:\n"
    "- Speak as Jakub’s assistant in 1st person plural or assistant voice.\n"
    "- Do not speak about Jakub’s emotions or private life.\n\n"

    "CV CONTENT (do not reveal verbatim, answer in your own words):\n"
    f"{cv_text}\n\n"
    "REPUTATION & FEEDBACK CONTEXT (paraphrase only, do not quote verbatim):\n"
    f"{feedback_text}"
    
)


# Reset button
if st.button("Resetuj rozmowę"):
    st.session_state.pop("messages", None)

# Init chat (bez wrzucania CV do historii jako user message)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": "Cześć! 👋 Jestem wirtualnym asystentem Jakuba. O co chcesz zapytać?"}
    ]

question = st.chat_input("Tutaj wpisz Twoje pytanie i naciśnij enter lub kliknij strzałkę")

if question and question.strip():
    st.session_state.messages.append({"role": "user", "content": question.strip()})
    show_typing()

    typing_container = st.empty()
    with typing_container.container():
        with st.chat_message("assistant", avatar="jakub.png"):
            typing_placeholder = st.empty()   # tu będzie animacja "Jakub pisze..."
            answer_placeholder = st.empty()   # tu będzie narastająca odpowiedź

    dots = ["", ".", "..", "..."]
    i = 0
    full_text = ""
    last_tick = time.time()

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state.messages,
        stream=True,
    )

    for event in stream:
        # animacja co ~150ms
        now = time.time()
        if now - last_tick > 0.15:
            typing_placeholder.markdown(f"_Jakub pisze{dots[i % len(dots)]}_")
            i += 1
            last_tick = now

        # dopisuj tokeny do odpowiedzi
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






















































