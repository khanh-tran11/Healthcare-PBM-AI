"""Streamlit UI for older Vietnamese users. Run: streamlit run app.py"""
import json

import streamlit as st

from src import config
from src.pipeline import check_claim
from src.schema import LABEL_VI

st.set_page_config(page_title="Tin sức khỏe này có đúng không?", page_icon="🩺", layout="centered")
st.markdown(
    """<style>
    html, body, [class*="css"], .stMarkdown, p, li, label, textarea { font-size: 20px !important; }
    h1 { font-size: 2.1rem !important; }
    .stButton > button { min-height: 56px; font-size: 20px !important; width: 100%; }
    .badge { display:inline-block; padding:10px 18px; border-radius:12px; color:#fff; font-weight:700; font-size:26px; }
    .dung{background:#15803d} .sai{background:#b91c1c} .gay_hieu_lam{background:#b45309} .chua_du_bang_chung{background:#4b5563}
    .doctor { background:#fee2e2; color:#7f1d1d; border:2px solid #b91c1c; padding:12px; border-radius:10px; font-weight:700; }
    .understood { background:#eef6f5; padding:10px 14px; border-radius:10px; }
    </style>""",
    unsafe_allow_html=True,
)

st.title("Tin sức khỏe này có đúng không?")
st.caption("Dán tin nhắn bạn nhận được trên Zalo hoặc Facebook. Hệ thống đối chiếu với nguồn Bộ Y tế, WHO.")
if config.OFFLINE:
    st.warning("Đang chạy chế độ offline (chưa có khóa watsonx): kết luận dùng luật đơn giản, chỉ để minh họa.")


@st.cache_data(show_spinner=False)
def _samples() -> list[str]:
    rows = [json.loads(l) for l in config.CLAIMS_PATH.read_text("utf-8").splitlines() if l.strip()]
    return [r["claim"] for r in rows if r["id"] in (1, 6, 16)]


@st.cache_data(show_spinner=False)
def _check(text: str):
    return check_claim(text).model_dump()


if "claim" not in st.session_state:
    st.session_state.claim = ""
st.write("**Thử nhanh:**")
for i, s in enumerate(_samples()):
    if st.button(s, key=f"s{i}"):
        st.session_state.claim = s

claim = st.text_area("Dán tin bạn nhận được vào đây", key="claim", height=120)
if st.button("Kiểm tra", type="primary") and claim.strip():
    try:
        with st.spinner("Đang kiểm tra nguồn Bộ Y tế, WHO..."):
            v = _check(claim.strip())
    except FileNotFoundError:
        st.error("Chưa có dữ liệu nguồn. Hãy chạy: python -m src.ingest")
        st.stop()
    except Exception as e:  # friendly message, details for the developer
        st.error("Xin lỗi, hệ thống đang gặp lỗi. Bạn thử lại sau ít phút nhé.")
        st.caption(f"Chi tiết kỹ thuật: {e}")
        st.stop()

    label = v["label"]
    st.markdown(
        f'<span class="badge {label}">{LABEL_VI[label]}</span> &nbsp; Độ tin cậy: <b>{v["confidence"]:.0%}</b>',
        unsafe_allow_html=True,
    )
    if v["understood"]:
        st.markdown(f'<div class="understood">Đã hiểu: {v["understood"]}</div>', unsafe_allow_html=True)
    st.write(v["explanation_vi"])
    if v["citations"]:
        st.write("**Nguồn:** " + " · ".join(
            f"[{c['source_id']}]({c['url']})" if c["url"] else c["source_id"] for c in v["citations"]))
    if v["see_doctor"]:
        st.markdown('<div class="doctor">Nên đi khám ngay hoặc gọi 115 nếu có dấu hiệu nguy hiểm.</div>', unsafe_allow_html=True)
    st.info("Thông tin tham khảo, không thay thế bác sĩ.")

    with st.expander("Vì sao hệ thống kết luận như vậy?"):
        if v["retried_query"]:
            st.write(f"Lần 1 chưa đủ bằng chứng, đã tìm lại với: *{v['retried_query']}*")
        for c in (v["citations"] or v["retrieved"][:3]):
            st.markdown(f"**{c['source_id']}**: “{c['text'][:300]}…”")

    url = v["citations"][0]["url"] if v["citations"] else ""
    msg = (f"Bố/Mẹ ơi, con vừa kiểm tra tin này: {LABEL_VI[label]}. {v['explanation_vi']}"
           + (f" Nguồn: {url}." if url else "") + " Bố mẹ hỏi bác sĩ trước khi làm theo nhé.")
    st.subheader("Copy gửi gia đình")
    st.code(msg, language=None)
    st.caption(f"{v['latency_ms']} ms · {v['mode']} · Powered by IBM watsonx · Built with IBM Bob")
