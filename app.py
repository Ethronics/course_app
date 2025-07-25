import json
from pathlib import Path
import streamlit as st

DATA_PATH = Path("data/courses.json")
UTF8 = {"encoding": "utf-8"}

def load_data():
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(**UTF8))
    st.error("data/courses.json not found"); st.stop()

def save_data(d):  # always UTF‑8
    DATA_PATH.write_text(json.dumps(d, indent=2, ensure_ascii=False), **UTF8)

# ---------- Streamlit config ----------
st.set_page_config(page_title="Ethronics dashboard", layout="wide")

data = load_data()
for k, v in [("page", "home"), ("group", None), ("course", None)]:  # session defaults
    st.session_state.setdefault(k, v)

# ---------- common header ----------
def header():
    st.title("Ethronics Summer 2025")

# ---------- HOME ----------
if st.session_state.page == "home":
    header()
    st.subheader("Choose your group")
    cols = st.columns(len(data))
    for col, grp in zip(cols, data.keys()):
        if col.button(grp, use_container_width=True):
            st.session_state.update(group=grp, page="courses")
            st.rerun()

# ---------- COURSE LIST ----------
elif st.session_state.page == "courses":
    header()
    if st.button("← back to groups"):
        st.session_state.page = "home"; st.rerun()

    grp = st.session_state.group
    st.subheader(f"Group {grp}")
    col1, col2 = st.columns(2)
    for idx, code in enumerate(sorted(data[grp].keys())):
        (col1 if idx % 2 == 0 else col2).button(
            code, use_container_width=True, key=code,
            on_click=lambda c=code: st.session_state.update(course=c, page="course") or st.rerun()
        )

# ---------- SINGLE COURSE ----------
else:
    header()
    grp, course = st.session_state.group, st.session_state.course
    if st.button("← back to courses"): st.session_state.page = "courses"; st.rerun()

    course_dict = data[grp][course]
    st.subheader(f"{course} · Group {grp}")
    st.markdown(f"**Description**: {course_dict.get('Description','No description')}")

    # ---------- passkey gate ----------
    auth_key = f"auth_{grp}_{course}"
    if not st.session_state.get(auth_key, False):
        with st.expander("Instructor login"):
            pwd = st.text_input("Passkey", type="password")
            if st.button("Unlock"):
                if pwd == f"{course}1234":
                    st.session_state[auth_key] = True
                    st.success("Editing unlocked"); st.rerun()
                else:
                    st.error("Incorrect passkey")

    can_edit = st.session_state.get(auth_key, False)

    # ---------- show weeks ----------
    week_keys = [k for k in course_dict if k.lower().startswith("week")]
    week_keys.sort(key=lambda w: int(w.split()[1]))
    for wk in week_keys:
        wk_dict = course_dict[wk]
        with st.expander(wk):
            st.markdown("#### Content"); st.markdown(wk_dict["content"])
            st.markdown("#### Assessment"); st.markdown(wk_dict["assessment"])

            if can_edit:
                new_c = st.text_area("Edit content", wk_dict["content"], key=f"c-{wk}", height=160)
                new_a = st.text_area("Edit assessment", wk_dict["assessment"], key=f"a-{wk}", height=120)
                if st.button("Save changes", key=f"save-{wk}"):
                    wk_dict.update(content=new_c, assessment=new_a); save_data(data); st.success("Saved"); st.rerun()
