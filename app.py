import streamlit as st

from faq_engine import ElectroStoreFAQ
from scraper import CATEGORIES
from update_service import fetch_and_build


st.set_page_config(page_title="ElectroStore FAQ Bot", page_icon="⚡")


@st.cache_resource(show_spinner=False)
def load_engine() -> ElectroStoreFAQ:
    return ElectroStoreFAQ()


faq_engine = load_engine()

if "conversation" not in st.session_state:
    st.session_state.conversation = []

# ── Sidebar: update data from thegioididong.com ──
with st.sidebar:
    st.header("Cập nhật dữ liệu")
    st.caption("Crawl sản phẩm từ thegioididong.com và thêm vào cơ sở dữ liệu.")

    selected_cats = st.multiselect(
        "Danh mục",
        options=list(CATEGORIES.keys()),
        default=["dtdd"],
        format_func=lambda slug: CATEGORIES[slug],
    )

    if st.button("🔄 Cập nhật từ thegioididong.com"):
        with st.spinner("Đang crawl dữ liệu…"):
            update_result = fetch_and_build(
                categories=selected_cats or None,
            )

        if update_result.scrape_errors:
            for err in update_result.scrape_errors:
                st.error(err)

        if update_result.entries:
            entry_dicts = [
                {"id": e.id, "question": e.question, "answer": e.answer}
                for e in update_result.entries
            ]
            added = faq_engine.add_entries(entry_dicts)
            st.success(
                f"Đã thêm {added} câu hỏi từ "
                f"{update_result.products_found} sản phẩm."
            )
        elif not update_result.scrape_errors:
            st.warning("Không tìm thấy sản phẩm nào.")

    st.divider()
    st.metric("Tổng câu hỏi trong DB", faq_engine.total_entries)

# ── Main chat area ──
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
        source_text = f"Nguồn: \u201c{response.matched_question}\u201d (độ tương đồng {response.similarity:.2f})"
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
