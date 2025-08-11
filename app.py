import base64, json
from pathlib import Path
import streamlit as st
import os
from pymongo import MongoClient

# Mongo connection
MONGO_URI = st.secrets.get("mongo", {}).get("uri") or os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["ethronics"]
col = db["courses"]

DOC_ID = "curriculum_v1"

def _ensure_doc():
    if not col.find_one({"_id": DOC_ID}):
        col.insert_one({"_id": DOC_ID, "data": {}})

def load_data():
    _ensure_doc()
    return col.find_one({"_id": DOC_ID})["data"]

def save_data(d: dict):
    col.update_one({"_id": DOC_ID}, {"$set": {"data": d}}, upsert=True)

st.set_page_config(
    page_title="Ethronics Summer 2025",
    layout="wide",
)

DATA_PATH = Path("data/courses.json")
UTF8 = {"encoding": "utf-8"}

def ethronics_header():
    st.markdown(
        """
        <div style="
            background:linear-gradient(90deg,#004d7a,#008793,#00bf72,#a8eb12);
            padding:1.2rem 1rem;border-radius:0.4rem;margin-bottom:1.2rem;
            box-shadow:0 2px 10px rgba(0,0,0,0.1);">
          <h1 style="color:white;margin:0;">Ethronics Summer 2025</h1>
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
          © 2025 <a href="https://www.ethronics.com" target="_blank">Ethronics Institute of Robotics &amp; Autonomous Systems</a>
          · Inspiring Ethiopia through Technology
        </p>
        """,
        unsafe_allow_html=True,
    )

data = load_data()

for k, v in [("page", "home"), ("group", None), ("course", None)]:
    st.session_state.setdefault(k, v)

if st.session_state.page == "home":
    ethronics_header()
    st.subheader("Select your group")
    if not data:
        st.info("No groups yet. Add data to the database.")
    else:
        cols = st.columns(len(data))
        for col, grp in zip(cols, data.keys()):
            if col.button(grp, use_container_width=True, key=f"btn_grp_{grp}"):
                st.session_state.group = grp
                st.session_state.page = "courses"
                st.rerun()
    ethronics_footer()

elif st.session_state.page == "courses":
    ethronics_header()
    if st.button("← Back to groups", key="back_to_groups"):
        st.session_state.page = "home"
        st.rerun()

    grp = st.session_state.group
    st.subheader(f"Courses for **{grp}**")
    left, right = st.columns(2)
    for i, course_code in enumerate(sorted(data[grp].keys())):
        target_col = left if i % 2 == 0 else right
        if target_col.button(course_code, use_container_width=True, key=f"btn_course_{grp}_{course_code}"):
            st.session_state.course = course_code
            st.session_state.page = "course"
            st.rerun()
    ethronics_footer()

else:
    ethronics_header()
    grp, course = st.session_state.group, st.session_state.course
    if st.button("← Back to courses", key=f"back_to_courses_{grp}_{course}"):
        st.session_state.page = "courses"
        st.rerun()

    course_dict = data[grp][course]
    st.subheader(f"{course}  ·  {grp}")
    st.markdown(f"**Description**: {course_dict.get('Description','*(no description)*')}")

    # ── Instructor auth (unique keys)
    auth_key = f"auth_{grp}_{course}"
    if not st.session_state.get(auth_key, False):
        with st.expander("Instructor login to edit", expanded=False):
            pwd = st.text_input("Passkey", type="password", key=f"passkey_{grp}_{course}")
            if st.button("Unlock", key=f"unlock_{grp}_{course}"):
                if pwd == f"{course}1234":
                    st.session_state[auth_key] = True
                    st.success("Editing unlocked")
                    st.rerun()
                else:
                    st.error("Incorrect passkey")

    can_edit = st.session_state.get(auth_key, False)

    # ── Weeks
    week_keys = [k for k in course_dict if k.lower().startswith("week")]
    week_keys.sort(key=lambda w: int(w.split()[1]) if w.split()[1].isdigit() else 0)

    for wk in week_keys:
        block = course_dict[wk]
        with st.expander(wk, expanded=False):
            st.markdown("#### Content")
            st.markdown(block.get("content", ""))

            st.markdown("---")
            st.markdown("#### Assessment")
            st.markdown(block.get("assessment", ""))

            if can_edit:
                # Use a form per week so state is clean and Save is atomic
                with st.form(key=f"form_edit_{grp}_{course}_{wk}"):
                    new_c = st.text_area(
                        "Edit content",
                        block.get("content", ""),
                        key=f"ta_content_{grp}_{course}_{wk}",
                        height=180,
                    )
                    new_a = st.text_area(
                        "Edit assessment",
                        block.get("assessment", ""),
                        key=f"ta_assess_{grp}_{course}_{wk}",
                        height=140,
                    )
                    saved = st.form_submit_button("Save changes", use_container_width=False)
                    if saved:
                        block.update(content=new_c, assessment=new_a)
                        save_data(data)
                        st.success("Saved")
                        st.experimental_rerun()

    # ── Add a new week (render ONCE per course, with unique keys)
    if can_edit:
        st.markdown("---")
        st.markdown("### ➕ Add a new week")
        # pick a default next week number
        existing_nums = []
        for wk in week_keys:
            parts = wk.split()
            if len(parts) >= 2 and parts[1].isdigit():
                existing_nums.append(int(parts[1]))
        default_next = max(existing_nums) + 1 if existing_nums else 1

        new_num = st.number_input(
            "Week number",
            min_value=1,
            step=1,
            format="%d",
            value=default_next,
            key=f"week_number_{grp}_{course}",
        )
        new_key = f"Week {int(new_num)}"

        if new_key in course_dict:
            st.info(f"{new_key} already exists.")
        else:
            new_content = st.text_area("Content (Markdown)", key=f"new_content_{grp}_{course}")
            new_assess  = st.text_area("Assessment (Markdown)", key=f"new_assess_{grp}_{course}")
            if st.button("Create week", key=f"create_week_{grp}_{course}"):
                if new_content.strip() and new_assess.strip():
                    course_dict[new_key] = {
                        "content": new_content.strip(),
                        "assessment": new_assess.strip(),
                    }
                    save_data(data)
                    st.success(f"{new_key} added.")
                    st.experimental_rerun()
                else:
                    st.error("Both content and assessment are required.")

    ethronics_footer()
