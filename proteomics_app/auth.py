import streamlit as st

def require_password(title: str = "Restricted Access") -> None:
    """
    Simple password gate using Streamlit secrets.
    Requires st.secrets["APP_PASSWORD"] to be set (locally via .streamlit/secrets.toml,
    in Community Cloud via App Settings -> Secrets).
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return

    st.title(title)
    pw = st.text_input("Password", type="password")

    if pw:
        expected = st.secrets.get("APP_PASSWORD", "")
        if expected and pw == expected:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")

    st.stop()
