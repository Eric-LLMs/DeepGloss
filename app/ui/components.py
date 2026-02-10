import streamlit as st

def render_term_card(term_data, on_play_callback=None):
    """
    渲染一个单词卡片
    term_data: 数据库查出来的字典 {'word': '...', 'definition': '...'}
    """
    st.markdown(f"""
    <div style="padding: 15px; border-radius: 8px; background-color: #f0f2f6; border-left: 5px solid #ff4b4b; margin-bottom: 15px;">
        <h3 style="margin:0; color: #333;">{term_data['word']}</h3>
        <p style="margin:5px 0 0 0; color: #666;">{term_data['definition']}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔊 发音", key=f"btn_card_{term_data['id']}"):
            if on_play_callback:
                on_play_callback(term_data['word'])