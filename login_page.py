"""login_page.py - the first screen: a dark login / sign-up card on a dotted background.

This is a demo login: it checks that you typed a sensible name/email, but there
are no real accounts or passwords, and nothing is saved anywhere.
"""
import re
import streamlit as st
from dot_background import add_dot_background

EMAIL_OK = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# small icons for the social buttons (shown with CSS, so no extra files needed)
_GOOGLE = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E"
           "%3Cpath fill='%234285F4' d='M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z'/%3E"
           "%3Cpath fill='%2334A853' d='M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z'/%3E"
           "%3Cpath fill='%23FBBC05' d='M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z'/%3E"
           "%3Cpath fill='%23EA4335' d='M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z'/%3E%3C/svg%3E")
_GITHUB = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E"
           "%3Cpath d='M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.699-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.462-1.11-1.462-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.379.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.577.688.48C19.138 20.161 22 16.416 22 12c0-5.523-4.477-10-10-10z'/%3E%3C/svg%3E")
_APPLE = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E"
          "%3Cpath d='M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.04 2.26-.79 3.59-.76 1.56.04 2.88.75 3.65 1.89-3.08 1.75-2.58 5.61.35 6.75-1.01 2.37-2.39 4.39-4.29 4.29zM12.03 7.25c-.15-2.23 1.66-4.07 3.72-4.25.36 2.38-1.92 4.34-3.72 4.25z'/%3E%3C/svg%3E")

_CSS = """
<style>
[data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
.block-container { max-width: 400px !important; background: #121212 !important; border: 1px solid #222;
    border-radius: 12px; padding: 2rem !important; margin: 7vh auto 0 auto; box-shadow: 0 10px 40px rgba(0,0,0,0.8);
    backdrop-filter: none !important; }
.login-head { text-align: center; }
.login-logo { width: 44px; height: 44px; border-radius: 50%; background: #111; border: 1px solid #333; margin: 0 auto 0.75rem auto;
    display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.15rem; color: #fff; }
.login-head h1 { font-size: 1.35rem !important; font-weight: 600; letter-spacing: -0.025em; margin: 0 0 0.25rem 0; padding: 0; color: #fff; }
.login-head p { font-size: 0.85rem; color: #888; margin: 0 0 0.5rem 0; }
.login-foot { text-align: center; font-size: 0.75rem; color: #666; line-height: 1.5; }
.login-or { height: 1px; background: #222; width: 100%; margin: 0.35rem 0; }
.login-switch { text-align: center; font-size: 0.875rem; color: #888; margin-top: 0.5rem; }
/* form + inputs */
[data-testid="stForm"] { border: none !important; padding: 0 !important; }
.block-container [data-baseweb="input"], .block-container [data-baseweb="base-input"] {
    background: #000 !important; border-radius: 6px !important; }
.block-container [data-baseweb="input"] { border: 1px solid #333 !important; }
.block-container input { color: #fff !important; font-size: 0.875rem; }
[data-testid="InputInstructions"] { display: none !important; }
/* main button: "Continue with Email" */
[data-testid="stFormSubmitButton"] button { width: 100%; background: #ededed !important; border: none !important; border-radius: 6px; color: #000 !important; }
[data-testid="stFormSubmitButton"] button p { color: #000 !important; font-weight: 500; }
/* social buttons */
[class*="st-key-soc_"] button { width: 100%; background: transparent !important; border: 1px solid #333 !important; border-radius: 6px;
    color: #fff !important; display: flex; align-items: center; justify-content: center; gap: 0.5rem; }
[class*="st-key-soc_"] button p { font-size: 0.875rem; font-weight: 500; color: #fff !important; }
[class*="st-key-soc_"] button:hover { background: #1c1c1c !important; }
[class*="st-key-soc_"] button::before { content: ""; width: 16px; height: 16px; flex-shrink: 0; background-size: contain; background-repeat: no-repeat; background-position: center; }
.st-key-soc_google button::before { background-image: url("__GOOGLE__"); }
.st-key-soc_github button::before { background-image: url("__GITHUB__"); }
.st-key-soc_apple  button::before { background-image: url("__APPLE__"); }
/* Sign Up / Sign In link-style button */
.st-key-toggle_mode > div, .st-key-toggle_mode { display: flex; justify-content: center; }
.st-key-toggle_mode button { background: none !important; border: none !important; padding: 0 !important; min-height: 0 !important; width: auto; }
.st-key-toggle_mode button p { color: #fff !important; font-weight: 600; font-size: 0.875rem; }
</style>
""".replace("__GOOGLE__", _GOOGLE).replace("__GITHUB__", _GITHUB).replace("__APPLE__", _APPLE)


def _flip_mode():
    st.session_state.auth_mode = "signup" if st.session_state.auth_mode == "signin" else "signin"


def _social_clicked(name):
    st.toast(f"{name} sign-in isn't set up in this demo. Please continue with email.")


def show_login():
    """Draws the login card. When details are OK it sets logged_in and moves to the next page."""
    add_dot_background()
    st.markdown(_CSS, unsafe_allow_html=True)

    mode = st.session_state.get("auth_mode", "signin")
    signup = mode == "signup"

    st.markdown(f"""
<div class="login-head">
  <div class="login-logo">SS</div>
  <h1>{'Sign up for Sudoku Solver' if signup else 'Sign in to Sudoku Solver'}</h1>
  <p>{'Create a new account to get started.' if signup else 'Sign in to your account.'}</p>
</div>""", unsafe_allow_html=True)

    with st.form("login_form", border=False):
        name = st.text_input("Full name", placeholder="Full Name", label_visibility="collapsed") if signup else ""
        email = st.text_input("Email", placeholder="name@work-email.com", label_visibility="collapsed")
        go = st.form_submit_button("Sign Up with Email" if signup else "Continue with Email")

    if go:
        if signup and not name.strip():
            st.error("Please enter your full name.")
        elif not EMAIL_OK.match(email.strip()):
            st.error("Please enter a valid email address (like name@example.com).")
        else:
            st.session_state.logged_in = True
            st.session_state.user_name = name.strip() if signup else email.split("@")[0]
            st.session_state.page = "learn"
            st.rerun()

    st.markdown('<div class="login-or"></div>', unsafe_allow_html=True)
    verb = "Sign up with" if signup else "Continue with"
    for key, label in (("google", "Google"), ("github", "GitHub"), ("apple", "Apple")):
        st.button(f"{verb} {label}", key=f"soc_{key}", on_click=_social_clicked, args=(label,))

    st.markdown(f'<div class="login-switch">{"Already have an account?" if signup else "Don’t have an account?"}</div>',
                unsafe_allow_html=True)
    st.button("Sign In" if signup else "Sign Up", key="toggle_mode", on_click=_flip_mode)
    st.markdown('<div class="login-foot">This is a student project demo. Your details are only used to greet you '
                'and are not stored.</div>', unsafe_allow_html=True)
