import streamlit as st
from openai import OpenAI
import os


st.set_page_config(page_title="야식 챗봇", page_icon="🍜")

st.title("🍜 야식 챗봇 — 밤에 뭐 먹을까?")

# Default system prompt (used as placeholder and reset value)
SYSTEM_PROMPT = (
    "You are a friendly late-night snack recommender named '야식 챗봇'. "
    "When the user asks, suggest 3 tailored late-night options and ask at least one clarifying question "
    "(dietary restrictions, spice tolerance, time, budget, or available cooking equipment). "
    "Be concise, give short bullet suggestions and follow up to continue the conversation. "
    "If the user asks for a single recommendation, explain why it's a good choice."
)

# System prompt editor placed immediately below the title
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = SYSTEM_PROMPT

st.markdown("**시스템 프롬프트 (챗봇 동작 방식)**")
prompt_text = st.text_area(
    label="시스템 프롬프트 편집",
    value="",
    placeholder=st.session_state.system_prompt,
    height=180,
)

col_apply, col_reset = st.columns([1, 1])
with col_apply:
    if st.button("적용"):
        if prompt_text and prompt_text.strip():
            st.session_state.system_prompt = prompt_text.strip()
            # update system message in conversation if present
            if "messages" in st.session_state and len(st.session_state.messages) > 0 and st.session_state.messages[0].get("role") == "system":
                st.session_state.messages[0]["content"] = st.session_state.system_prompt
            else:
                st.session_state.messages = [{"role": "system", "content": st.session_state.system_prompt}]
            st.success("시스템 프롬프트가 적용되었습니다.")
with col_reset:
    if st.button("기본값으로 복원"):
        st.session_state.system_prompt = SYSTEM_PROMPT
        if "messages" in st.session_state and len(st.session_state.messages) > 0 and st.session_state.messages[0].get("role") == "system":
            st.session_state.messages[0]["content"] = st.session_state.system_prompt
        else:
            st.session_state.messages = [{"role": "system", "content": st.session_state.system_prompt}]
        st.success("시스템 프롬프트가 기본값으로 복원되었습니다.")

st.write("야식 추천과 대화를 이어가며 사용자의 상황에 맞는 메뉴를 제안해주는 챗봇입니다.")


# Load API key from Streamlit secrets (no user input required)
api_key = None
if isinstance(st.secrets, dict) and "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    st.error("OpenAI API 키가 설정되어 있지 않습니다. `.streamlit/secrets.toml`에 `OPENAI_API_KEY`를 추가하세요.")
    st.stop()

# Initialize OpenAI client
client = OpenAI(api_key=api_key)


if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": st.session_state.system_prompt}
    ]


def format_message_display(role, content):
    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)
    elif role == "assistant":
        with st.chat_message("assistant"):
            st.markdown(content)
    else:
        st.write(content)


# Display previous messages
for m in st.session_state.messages:
    # skip system from rendering
    if m["role"] == "system":
        continue
    format_message_display(m["role"], m["content"])


col1, col2 = st.columns([1, 4])
with col1:
    if st.button("초기화"):  # clear chat
        st.session_state.messages = [{"role": "system", "content": st.session_state.get("system_prompt", SYSTEM_PROMPT)}]
        # Streamlit will rerun automatically on interaction; no explicit rerun needed.
        pass
with col2:
    st.caption("예시: '매운 거 먹고싶어', '다이어트 중인데 가벼운 야식 추천해줘', '집에 치즈랑 라면 있어' 등")


user_input = st.chat_input("원하시는 야식이나 상황을 적어보세요...")
if user_input:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    format_message_display("user", user_input)

    # Prepare messages for API
    api_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    # Call OpenAI Chat Completions with gpt-4o-mini
    with st.spinner("추천을 불러오는 중... 잠시만 기다려 주세요."):
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=api_messages,
                temperature=0.7,
                max_tokens=500,
            )

            # Extract assistant text robustly
            assistant_text = ""
            try:
                assistant_text = resp.choices[0].message.content
            except Exception:
                try:
                    assistant_text = resp.choices[0]["message"]["content"]
                except Exception:
                    assistant_text = str(resp)

        except Exception as e:
            st.error(f"API 요청 중 오류가 발생했습니다: {e}")
            assistant_text = "죄송합니다. 응답을 불러오지 못했습니다. 나중에 다시 시도해주세요."

    # Append and display assistant reply
    st.session_state.messages.append({"role": "assistant", "content": assistant_text})
    format_message_display("assistant", assistant_text)

    # Scroll to bottom by rerunning (Streamlit retains messages)
    # No explicit rerun required; Streamlit will refresh after user interaction.
    pass
