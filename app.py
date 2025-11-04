import streamlit as st

from faq_engine import ElectroStoreFAQ


st.set_page_config(page_title="ElectroStore FAQ Bot", page_icon="⚡")


@st.cache_resource(show_spinner=False)
def load_engine() -> ElectroStoreFAQ:
    return ElectroStoreFAQ()


faq_engine = load_engine()

if "conversation" not in st.session_state:
    st.session_state.conversation = []

st.title("ElectroStore FAQ Chatbot")
st.write("Hỏi nhanh những thắc mắc về sản phẩm và dịch vụ của ElectroStore.")

for message in st.session_state.conversation:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("source"):
            st.caption(message["source"])

prompt = st.chat_input("Nhập câu hỏi của bạn...")
if prompt:
    st.session_state.conversation.append({"role": "user", "content": prompt})
    response = faq_engine.ask(prompt)
    if response:
        answer_text = response.answer
        source_text = f"Nguồn: “{response.matched_question}” (độ tương đồng {response.similarity:.2f})"
    else:
        answer_text = "Không có câu trả lời!"
        source_text = None

    st.session_state.conversation.append(
        {
            "role": "assistant",
            "content": answer_text,
            "source": source_text,
        }
    )
    st.rerun()
