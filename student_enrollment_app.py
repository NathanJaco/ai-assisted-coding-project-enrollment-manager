"""Streamlit UI for the Module 8 student enrollment app.

This file is the UI layer. It uses the existing Session 1 backend:
- EnrollmentStore handles SQLite/database work.
- EnrollmentManager handles enrollment rules and student actions.

Run with:
    streamlit run student_enrollment_app.py
"""

from __future__ import annotations

import streamlit as st

from enrollment_starter import (
    CURRENT_STUDENT,
    DB_PATH,
    EnrollmentManager,
    EnrollmentStore,
    STATUS_ENROLLED,
    STATUS_UNENROLLED,
)


# -----------------------------
# Setup Helpers
# -----------------------------

def build_manager() -> EnrollmentManager:
    """Create the store and manager, then make sure sample data exists."""
    store = EnrollmentStore(DB_PATH)
    store.create_tables()
    store.seed_sample_data()
    return EnrollmentManager(store)


def initialize_session_state() -> None:
    """Set default values used for app routing and feedback."""
    if "page" not in st.session_state:
        st.session_state["page"] = "dashboard"

    if "selected_class" not in st.session_state:
        st.session_state["selected_class"] = None

    if "role" not in st.session_state:
        st.session_state["role"] = "student"

    if "current_student" not in st.session_state:
        st.session_state["current_student"] = CURRENT_STUDENT

    if "message" not in st.session_state:
        st.session_state["message"] = None


def set_message(message_type: str, text: str) -> None:
    """Store one short feedback message in session state."""
    st.session_state["message"] = {
        "type": message_type,
        "text": text,
    }


def show_message() -> None:
    """Show the current session message, if one exists."""
    message = st.session_state.get("message")

    if not message:
        return

    message_type = message.get("type")
    text = message.get("text", "")

    if message_type == "success":
        st.success(text)
    elif message_type == "warning":
        st.warning(text)
    elif message_type == "error":
        st.error(text)
    else:
        st.info(text)


def find_enrolled_class(
    manager: EnrollmentManager,
    user_id: str,
    course_id: str,
) -> dict | None:
    """Find a currently enrolled class by course ID."""
    for course in manager.get_student_enrollments(user_id):
        if course["course_id"] == course_id:
            return course

    return None


# -----------------------------
# Page: Student Dashboard
# -----------------------------

def show_dashboard(manager: EnrollmentManager) -> None:
    """Display the student dashboard page."""
    student = st.session_state["current_student"]
    user_id = student["user_id"]
    email = student["email"]

    st.title("Student Enrollment Dashboard")
    st.caption("View your enrolled classes, enter an enrollment key, or open a class page.")

    show_message()

    with st.container(border=True):
        st.subheader("Current Student")
        st.write(f"**Name:** {student['name']}")
        st.write(f"**Email:** {student['email']}")
        st.write(f"**Role:** {st.session_state['role']}")

    st.divider()

    summary = manager.get_student_summary(user_id)
    enrolled_classes = manager.get_student_enrollments(user_id)

    metric_col_1, metric_col_2, metric_col_3 = st.columns(3)

    with metric_col_1:
        st.metric("Total Records", summary["total_records"])

    with metric_col_2:
        st.metric("Currently Enrolled", summary[STATUS_ENROLLED])

    with metric_col_3:
        st.metric("Unenrolled", summary[STATUS_UNENROLLED])

    st.divider()

    with st.container(border=True):
        st.subheader("Enter Enrollment Key")
        st.caption("Use a valid course key to enroll or re-enroll in a class.")

        with st.form("enrollment_key_form", clear_on_submit=True):
            enrollment_key = st.text_input(
                "Enrollment Key",
                placeholder="Example: DATA210-SPRING",
            )
            submitted = st.form_submit_button("Enroll")

        if submitted:
            if not enrollment_key.strip():
                set_message("warning", "Please enter an enrollment key before submitting.")
                st.rerun()

            new_record = manager.enroll_with_key(
                user_id=user_id,
                email=email,
                enrollment_key=enrollment_key,
            )

            if new_record:
                selected_class = find_enrolled_class(
                    manager=manager,
                    user_id=user_id,
                    course_id=new_record["course_id"],
                )
                st.session_state["selected_class"] = selected_class
                st.session_state["page"] = "class_page"
                set_message("success", "Enrollment was successful. The class page is open now.")
                st.rerun()

            set_message("error", "That enrollment key was not found. Please check the key and try again.")
            st.rerun()

    st.divider()

    st.subheader("My Enrolled Classes")

    if not enrolled_classes:
        st.info("You are not currently enrolled in any classes.")
        return

    table_rows = [
        {
            "Course ID": course["course_id"],
            "Course Name": course["course_name"],
            "Instructor": course["instructor"],
            "Status": course["status"],
            "Enrolled At": course["enrolled_at"],
        }
        for course in enrolled_classes
    ]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    for course in enrolled_classes:
        with st.container(border=True):
            info_col, go_col, unenroll_col = st.columns([4, 1, 1])

            with info_col:
                st.markdown(f"### {course['course_id']}: {course['course_name']}")
                st.write(f"**Instructor:** {course['instructor']}")
                st.write(f"**Status:** {course['status']}")

            with go_col:
                if st.button("Go to Class", key=f"go_{course['course_id']}"):
                    st.session_state["selected_class"] = course
                    st.session_state["page"] = "class_page"
                    st.rerun()

            with unenroll_col:
                if st.button("Unenroll", key=f"unenroll_{course['course_id']}"):
                    success = manager.soft_unenroll_student(
                        user_id=user_id,
                        course_id=course["course_id"],
                    )

                    st.session_state["selected_class"] = None
                    st.session_state["page"] = "dashboard"

                    if success:
                        set_message(
                            "success",
                            f"You were unenrolled from {course['course_id']}. The record stayed in the database.",
                        )
                    else:
                        set_message(
                            "error",
                            f"Could not unenroll from {course['course_id']}. Please try again.",
                        )

                    st.rerun()


# -----------------------------
# Page: Selected Class Page
# -----------------------------

def show_class_page() -> None:
    """Display the selected class page."""
    selected_class = st.session_state.get("selected_class")

    if not selected_class:
        st.warning("No class is currently selected.")

        if st.button("Back to Dashboard"):
            st.session_state["page"] = "dashboard"
            st.rerun()

        return

    st.title(selected_class["course_name"])
    st.caption(f"Course page for {selected_class['course_id']}")

    show_message()

    with st.container(border=True):
        st.subheader("Class Information")

        col_1, col_2 = st.columns(2)

        with col_1:
            st.write(f"**Course ID:** {selected_class['course_id']}")
            st.write(f"**Course Name:** {selected_class['course_name']}")
            st.write(f"**Instructor:** {selected_class['instructor']}")

        with col_2:
            st.write(f"**Status:** {selected_class['status']}")
            st.write(f"**Enrolled At:** {selected_class['enrolled_at']}")

    st.divider()


    if st.button("Back to Dashboard"):
        st.session_state["page"] = "dashboard"
        st.rerun()


# -----------------------------
# Main App
# -----------------------------

def main() -> None:
    """Run the Streamlit app."""
    st.set_page_config(
        page_title="Student Enrollment App",
        page_icon="🎓",
        layout="wide",
    )

    initialize_session_state()

    if st.session_state["role"] != "student":
        st.error("This app is only available for student users.")
        st.stop()

    manager = build_manager()

    with st.sidebar:
        st.title("Navigation")
        st.write("Student View")

        page_choice = st.radio(
            "Go to",
            ["Dashboard", "Selected Class"],
            index=0 if st.session_state["page"] == "dashboard" else 1,
        )

        if page_choice == "Dashboard":
            st.session_state["page"] = "dashboard"
        elif st.session_state.get("selected_class"):
            st.session_state["page"] = "class_page"
        else:
            st.warning("Choose a class first from the dashboard.")
            st.session_state["page"] = "dashboard"

    if st.session_state["page"] == "class_page":
        show_class_page()
    else:
        show_dashboard(manager)


if __name__ == "__main__":
    main()
