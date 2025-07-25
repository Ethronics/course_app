# app.py  —  Ethronics Summer 2025 course dashboard
import base64, json
from pathlib import Path
import streamlit as st




# ────────────────────────────────────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────────────────────────────────────
# ——— config ———
ICON_FILE = Path("assets/ethronics_icon.png")   # <‑ your PNG
st.set_page_config(
    page_title="Ethronics Summer 2025",
    page_icon=str(ICON_FILE),   # Streamlit accepts a local image as the favicon
    layout="wide",
)

# helper to embed the PNG inside HTML
def _icon_img_tag(height=40):
    if ICON_FILE.exists():
        b64 = base64.b64encode(ICON_FILE.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{b64}" height="{height}"/>'
    return ""

DATA_PATH = Path("data/courses.json")
UTF8 = {"encoding": "utf-8"}

# ────────────────────────────────────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────────────────────────────────────
def load_data():
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(**UTF8))
    st.error("data/courses.json not found"); st.stop()

def save_data(d):
    DATA_PATH.write_text(json.dumps(d, indent=2, ensure_ascii=False), **UTF8)

def ethronics_header():
    st.markdown(
        """
        <div style="
            background:linear-gradient(90deg,#004d7a,#008793,#00bf72,#a8eb12);
            padding:1.2rem 1rem;border-radius:0.4rem;margin-bottom:1.2rem;
            box-shadow:0 2px 10px rgba(0,0,0,0.1);">
          <h1 style="color:white;margin:0;">Ethronics Summer 2025</h1>
          <p style="color:white;margin:0;font-size:0.95rem;">
            Pushing the boundaries of technology through groundbreaking research and development
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def ethronics_footer():
    st.markdown(
        """
        <hr style="margin-top:2rem;">
        <p style="text-align:center;font-size:0.85rem;">
          © 2025 <a href="https://www.ethronics.com" target="_blank">Ethronics Institute of Robotics &amp; Autonomous Systems</a>
          · Inspiring Ethiopia through Technology
        </p>
        """,
        unsafe_allow_html=True,
    )

# load once
data = load_data()

# initialize session state
for k, v in [("page", "home"), ("group", None), ("course", None)]:
    st.session_state.setdefault(k, v)

# ────────────────────────────────────────────────────────────────────────────────
# HOME  ─── select GROUP
# ────────────────────────────────────────────────────────────────────────────────
if st.session_state.page == "home":
    ethronics_header()
    st.subheader("Select your group")
    cols = st.columns(len(data))
    for col, grp in zip(cols, data.keys()):
        if col.button(grp, use_container_width=True):
            st.session_state.group = grp
            st.session_state.page = "courses"
            st.rerun()
    ethronics_footer()

# ────────────────────────────────────────────────────────────────────────────────
# COURSES  ─── select COURSE inside chosen group
# ────────────────────────────────────────────────────────────────────────────────
elif st.session_state.page == "courses":
    ethronics_header()
    if st.button("← Back to groups"):
        st.session_state.page = "home"; st.rerun()

    grp = st.session_state.group
    st.subheader(f"Courses for **{grp}**")
    left, right = st.columns(2)
    for i, course_code in enumerate(sorted(data[grp].keys())):
        target_col = left if i % 2 == 0 else right
        if target_col.button(course_code, use_container_width=True):
            st.session_state.course = course_code
            st.session_state.page = "course"
            st.rerun()
    ethronics_footer()

# ────────────────────────────────────────────────────────────────────────────────
# COURSE  ─── description, weeks, (optional) edit mode
# ────────────────────────────────────────────────────────────────────────────────
else:
    ethronics_header()
    grp, course = st.session_state.group, st.session_state.course
    if st.button("← Back to courses"): st.session_state.page = "courses"; st.rerun()

    course_dict = data[grp][course]
    st.subheader(f"{course}  ·  {grp}")
    st.markdown(f"**Description**: {course_dict.get('Description','*(no description)*')}")

    # ── passkey gate ───────────────────────────────────────────────────────────
    auth_key = f"auth_{grp}_{course}"
    if not st.session_state.get(auth_key, False):
        with st.expander("Instructor login to edit"):
            pwd = st.text_input("Passkey", type="password")
            if st.button("Unlock"):
                if pwd == f"{course}1234":
                    st.session_state[auth_key] = True
                    st.success("Editing unlocked"); st.rerun()
                else:
                    st.error("Incorrect passkey")

    can_edit = st.session_state.get(auth_key, False)

    # ── render weeks ───────────────────────────────────────────────────────────
    week_keys = [k for k in course_dict if k.lower().startswith("week")]
    week_keys.sort(key=lambda w: int(w.split()[1]))
    for wk in week_keys:
        block = course_dict[wk]
        with st.expander(wk):
            st.markdown("#### Content")
            st.markdown(block["content"])
            st.markdown("---")
            st.markdown("#### Assessment")
            st.markdown(block["assessment"])

            if can_edit:
                new_c = st.text_area("Edit content", block["content"],
                                     key=f"c-{wk}", height=180)
                new_a = st.text_area("Edit assessment", block["assessment"],
                                     key=f"a-{wk}", height=140)
                if st.button("Save changes", key=f"s-{wk}"):
                    block.update(content=new_c, assessment=new_a)
                    save_data(data)
                    st.success("Saved"); st.rerun()

    ethronics_footer()
