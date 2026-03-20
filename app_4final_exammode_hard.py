import streamlit as st
import json
import random
import time
import copy

# --- CONFIGURATION ---
st.set_page_config(page_title="UNR Med Block 4 Midterm Review", layout="wide")

# --- LOAD DATA ---
@st.cache_data
def load_questions():
    try:
        with open('finalblk4_low.json', 'r') as f:
            data = json.load(f)
            # Ensure every question has a valid session key
            for q in data:
                if 'session' not in q:
                    q['session'] = "Unknown Session"
            return data
    except FileNotFoundError:
        return []

all_questions = load_questions()

# --- SESSION STATE MANAGEMENT ---
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = []
if 'current_q_index' not in st.session_state:
    st.session_state.current_q_index = 0
if 'selected_session_state' not in st.session_state:
    st.session_state.selected_session_state = "All Sessions"
if 'performance' not in st.session_state:
    st.session_state.performance = {}
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}

# Track the random seed so we can recreate exact shuffles
if 'random_seed' not in st.session_state:
    st.session_state.random_seed = random.randint(1, 1000000)

def update_score(session_name, is_correct):
    if session_name not in st.session_state.performance:
        st.session_state.performance[session_name] = {'correct': 0, 'total': 0}
    st.session_state.performance[session_name]['total'] += 1
    if is_correct:
        st.session_state.performance[session_name]['correct'] += 1

# --- SIDEBAR: FILTERS & SETTINGS ---
st.sidebar.header("Study Configuration")

# EXAM MODE TOGGLE
exam_mode = st.sidebar.checkbox("📝 Exam Mode (Hide answers, allow changes)")

# Get unique sessions for the dropdown
unique_sessions = sorted(list(set(q['session'] for q in all_questions)))
blueprint_sessions = ["All Sessions"] + unique_sessions

# Dropdown for session selection
selected_session = st.sidebar.selectbox("Select Lecture/Session", blueprint_sessions)

# SEED INPUT: Let user see or change the seed to recreate a specific quiz
st.sidebar.divider()
st.sidebar.subheader("🔄 Quiz State")
manual_seed = st.sidebar.number_input(
    "Quiz Seed (Enter to resume a specific shuffle):", 
    value=st.session_state.random_seed, 
    step=1
)

# Apply manual seed if changed
if manual_seed != st.session_state.random_seed:
    st.session_state.random_seed = manual_seed
    st.session_state.selected_session_state = None # Force a reshuffle with new seed

# Reset logic if topic or seed changes
if selected_session != st.session_state.selected_session_state or not st.session_state.quiz_data:
    st.session_state.selected_session_state = selected_session
    st.session_state.current_q_index = 0
    st.session_state.user_answers = {} # Clear history
    
    if selected_session == "All Sessions":
        subset = copy.deepcopy(all_questions)
    else:
        filtered = [q for q in all_questions if q['session'] == selected_session]
        subset = copy.deepcopy(filtered)
    
    # --- FIXED: SHUFFLE QUESTIONS AND OPTIONS USING THE SEED ---
    rng = random.Random(st.session_state.random_seed)
    rng.shuffle(subset) # Shuffle question order
    for q in subset:
        rng.shuffle(q['options']) # Shuffle answer choice order (A, B, C, D)
        
    st.session_state.quiz_data = subset

# --- PROGRESS REPORT ---
st.sidebar.divider()
if exam_mode and st.session_state.current_q_index < len(st.session_state.quiz_data):
    st.sidebar.info("📊 Stats are hidden during Exam Mode.")
else:
    st.sidebar.subheader("📊 Progress Report")
    if st.sidebar.button("Reset Progress"):
        st.session_state.performance = {}
        st.session_state.user_answers = {}
        st.rerun()

    if not st.session_state.performance:
        st.sidebar.info("Start answering to see your stats!")
    else:
        for sess, stats in st.session_state.performance.items():
            if stats['total'] > 0:
                accuracy = (stats['correct'] / stats['total']) * 100
                color = "green" if accuracy >= 70 else "red"
                st.sidebar.markdown(f"**{sess}**")
                st.sidebar.markdown(f":{color}[{accuracy:.0f}%] ({stats['correct']}/{stats['total']})")
                st.sidebar.progress(accuracy / 100)

# --- MAIN INTERFACE ---
st.title("Block 4 Midterm Review")

if not st.session_state.quiz_data:
    st.warning("No questions available for this selection. Make sure finalblk3_high.json is loaded correctly.")
else:
    total_q = len(st.session_state.quiz_data)

    # --- JUMP TO QUESTION LOGIC ---
    if st.session_state.current_q_index < total_q:
        jump_col1, jump_col2 = st.columns([1, 4])
        with jump_col1:
            jump_to = st.number_input("Jump to Question:", min_value=1, max_value=total_q, value=st.session_state.current_q_index + 1)
            if jump_to - 1 != st.session_state.current_q_index:
                st.session_state.current_q_index = jump_to - 1
                st.rerun()

    # --- EXAM RESULTS SCREEN ---
    if st.session_state.current_q_index >= total_q:
        st.success("🎉 You have reached the end of this set!")
        
        if exam_mode and len(st.session_state.user_answers) > 0:
            st.divider()
            st.header("📝 Exam Results & Review")
            correct_count = 0
            
            # Score and display results
            for idx, q in enumerate(st.session_state.quiz_data):
                user_ans = st.session_state.user_answers.get(idx)
                is_correct = (user_ans == q['correct_answer'])
                if is_correct:
                    correct_count += 1
                update_score(q['session'], is_correct)

                status_icon = "✅" if is_correct else "❌"
                with st.expander(f"Q{idx+1}: {q['question']} {status_icon}"):
                    st.write(f"**Your Answer:** {user_ans if user_ans else 'No Answer'}")
                    st.write(f"**Correct Answer:** {q['correct_answer']}")
                    st.info(f"**Explanation:** {q['explanation']}")
                    st.caption(f"Source: {q['session']} ({q['faculty']})")
            
            score_pct = (correct_count / total_q) * 100
            st.subheader(f"Final Score: {correct_count} / {total_q} ({score_pct:.1f}%)")
            st.session_state.user_answers = {} # Clear so stats aren't double-counted

        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ Back to Last Question"):
                st.session_state.current_q_index -= 1
                st.rerun()
        with col3:
            if st.button("Restart & Reshuffle"):
                st.session_state.random_seed = random.randint(1, 1000000) # Generate new seed
                st.session_state.selected_session_state = None # Force reload
                st.session_state.user_answers = {}
                st.rerun()

    # --- ACTIVE QUIZ SCREEN ---
    else:
        q = st.session_state.quiz_data[st.session_state.current_q_index]
        current_idx = st.session_state.current_q_index
        
        # 1. Setup State & Answer Locking
        saved_answer = st.session_state.user_answers.get(current_idx)
        radio_index = q['options'].index(saved_answer) if saved_answer in q['options'] else None
        
        # LOCK LOGIC: Lock if Normal Mode AND it has been answered
        is_locked = (not exam_mode) and (saved_answer is not None)

        # 2. Header & Progress
        st.progress((current_idx + 1) / total_q)
        
        # Conditionally hide the session name until answered
        if is_locked:
            st.caption(f"**Session:** {q['session']} | Question {current_idx + 1} of {total_q} (Seed: {st.session_state.random_seed})")
        else:
            st.caption(f"Question {current_idx + 1} of {total_q} (Seed: {st.session_state.random_seed})")
        
        # Top Navigation (Only shown in Normal Mode for cleanliness)
        if not exam_mode:
            col_nav1, col_nav2, col_nav3 = st.columns([1, 4, 1])
            with col_nav1:
                if st.button("⬅️ Previous") and current_idx > 0:
                    st.session_state.current_q_index -= 1
                    st.rerun()
            with col_nav3:
                if st.button("Next ➡️"):
                    st.session_state.current_q_index += 1
                    st.rerun()

        st.divider()
        st.subheader(f"Question {current_idx + 1}")
        st.markdown(f"#### {q['question']}")

        # 3. Render Radio Buttons
        option_selected = st.radio(
            "Select your answer:", 
            q['options'], 
            key=f"q_{q['id']}", 
            index=radio_index,
            disabled=is_locked
        )

        # 4. Save Answer in Exam Mode (Live updates)
        if exam_mode and option_selected != saved_answer:
            st.session_state.user_answers[current_idx] = option_selected

        # 5. Logic for Normal Mode (Feedback & Auto-Advance)
        if not exam_mode:
            if is_locked:
                # Reviewing a locked question
                is_correct = (saved_answer == q['correct_answer'])
                if is_correct:
                    st.success("✅ You answered this correctly.")
                else:
                    st.error(f"❌ You answered: {saved_answer}")
                    st.success(f"Correct Answer: {q['correct_answer']}")
                
                # Show Explanation and Source after answering
                st.info(f"**Explanation:** {q['explanation']}")
                st.caption(f"Source: {q['session']} ({q['faculty']})")
            
            else:
                # Answering a new question
                if st.button("Check Answer"):
                    if option_selected:
                        # Save and lock
                        st.session_state.user_answers[current_idx] = option_selected
                        is_correct = (option_selected == q['correct_answer'])
                        
                        update_score(q['session'], is_correct)
                        
                        if is_correct:
                            st.success("✅ Correct!")
                        else:
                            st.error(f"❌ Incorrect. The correct answer is: **{q['correct_answer']}**")
                        
                        # Show Explanation and Source after answering
                        st.info(f"**Explanation:** {q['explanation']}")
                        st.caption(f"Source: {q['session']} ({q['faculty']})")
                        
                        # Auto-advance
                        my_bar = st.progress(0, text="Moving to next question in 5 seconds...")
                        for percent in range(100):
                            time.sleep(0.05)
                            my_bar.progress(percent + 1, text="Moving to next question in 5 seconds...")
                        
                        st.session_state.current_q_index += 1
                        st.rerun()
                    else:
                        st.warning("Please select an option first.")

        # --- EXAM MODE NAVIGATION (Moved to Bottom) ---
        if exam_mode:
            st.divider()
            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                if current_idx > 0:
                    if st.button("⬅️ Previous"):
                        st.session_state.current_q_index -= 1
                        st.rerun()
            with col3:
                next_label = "Finish Exam ➡️" if current_idx == total_q - 1 else "Next ➡️"
                if st.button(next_label):
                    st.session_state.current_q_index += 1
                    st.rerun()