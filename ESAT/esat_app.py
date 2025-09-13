import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
from PIL import Image
import glob
import time

# Configure page
st.set_page_config(
    page_title="ENGAA/TMUA Exam Prep",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'selected_exam' not in st.session_state:
    st.session_state.selected_exam = None
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'total_time' not in st.session_state:
    st.session_state.total_time = 0
if 'question_start_time' not in st.session_state:
    st.session_state.question_start_time = None
if 'question_times' not in st.session_state:
    st.session_state.question_times = {}

def load_questions_config():
    """Load questions configuration from JSON file"""
    config_file = 'questions_config.json'
    
    # Default configuration with your actual exam structure
    default_config = {
        "ENGAA_2023": {
            "name": "ENGAA 2023",
            "sections": {
                "Part A": {
                    "questions": list(range(1, 21)),
                    "answers": ["A", "F", "C", "F", "F", "B", "D", "B", "D", "E", 
                              "B", "A", "H", "C", "B", "D", "E", "B", "C", "A"]
                },
                "Part B": {
                    "questions": list(range(21, 41)),
                    "answers": ["H", "D", "A", "D", "G", "C", "E", "E", "F", "B",
                              "E", "B", "C", "G", "A", "E", "B", "A", "G", "A"]
                }
            }
        },
        "ENGAA_2022": {
            "name": "ENGAA 2022",
            "sections": {
                "Part A": {"questions": list(range(1, 21)), "answers": ["A"] * 20},
                "Part B": {"questions": list(range(21, 41)), "answers": ["A"] * 20}
            }
        },
        "ENGAA_2021": {
            "name": "ENGAA 2021", 
            "sections": {
                "Part A": {"questions": list(range(1, 21)), "answers": ["A"] * 20},
                "Part B": {"questions": list(range(21, 41)), "answers": ["A"] * 20}
            }
        },
        "ENGAA_2020": {
            "name": "ENGAA 2020",
            "sections": {
                "Part A": {"questions": list(range(1, 21)), "answers": ["A"] * 20},
                "Part B": {"questions": list(range(21, 41)), "answers": ["A"] * 20}
            }
        },
        "ENGAA_2019": {
            "name": "ENGAA 2019",
            "sections": {
                "Part A": {"questions": list(range(1, 21)), "answers": ["A"] * 20},
                "Part B": {"questions": list(range(21, 41)), "answers": ["A"] * 20}
            }
        },
        "ENGAA_2018": {
            "name": "ENGAA 2018",
            "sections": {
                "Part A": {"questions": list(range(1, 21)), "answers": ["A"] * 20},
                "Part B": {"questions": list(range(21, 41)), "answers": ["A"] * 20}
            }
        },
        "TMUA_2023": {
            "name": "TMUA 2023",
            "sections": {
                "Paper 1": {"questions": list(range(1, 16)), "answers": ["A"] * 15}
            }
        },
        "TMUA_2022": {
            "name": "TMUA 2022",
            "sections": {
                "Paper 1": {"questions": list(range(1, 21)), "answers": ["A"] * 20},
                "Paper 2": {"questions": list(range(21, 41)), "answers": ["A"] * 20}
            }
        },
        "TMUA_2021": {
            "name": "TMUA 2021",
            "sections": {
                "Paper 1": {"questions": list(range(1, 21)), "answers": ["A"] * 20},
                "Paper 2": {"questions": list(range(21, 41)), "answers": ["A"] * 20}
            }
        },
        "TMUA_2020": {
            "name": "TMUA 2020",
            "sections": {
                "Paper 1": {"questions": list(range(1, 21)), "answers": ["A"] * 20},
                "Paper 2": {"questions": list(range(21, 41)), "answers": ["A"] * 20}
            }
        }
    }
    
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create the config file
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config

def format_time(seconds):
    """Format time in seconds to mm:ss format"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

def save_session_log(exam_id, questions, answers, user_answers, question_times):
    """Save session results to JSON log file"""
    log_file = 'exam_sessions_log.json'

    # Load existing log or create new
    try:
        with open(log_file, 'r') as f:
            log_data = json.load(f)
    except FileNotFoundError:
        log_data = []

    # Create session entry
    session_entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S"),
        "exam_id": exam_id,
        "results": []
    }

    for i, q_num in enumerate(questions):
        user_answer = user_answers.get(f"{exam_id}_{q_num}", "")
        correct_answer = answers[i]
        is_correct = user_answer == correct_answer if user_answer else None
        time_spent = question_times.get(f"{exam_id}_{q_num}", 0)

        session_entry["results"].append({
            "question": q_num,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "time_spent": time_spent
        })

    log_data.append(session_entry)

    # Save updated log
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)

def load_session_log():
    """Load session log from JSON file"""
    log_file = 'exam_sessions_log.json'
    try:
        with open(log_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def find_question_image(exam_id, question_num):
    """Find question image file"""
    possible_patterns = [
        f"images/{exam_id}/question_{question_num:02d}.*",
        f"images/{exam_id}/q{question_num}.*",
        f"images/{exam_id}/{question_num}.*"
    ]
    
    for pattern in possible_patterns:
        files = glob.glob(pattern)
        if files:
            return files[0]
    return None

def display_question(exam_id, question_num):
    """Display a question with multiple choice options"""
    image_path = find_question_image(exam_id, question_num)
    
    if image_path and os.path.exists(image_path):
        try:
            image = Image.open(image_path)
            st.image(image)
        except Exception as e:
            st.error(f"Error loading image: {e}")
    else:
        st.warning(f"Question {question_num} image not found")
        st.info(f"Expected: images/{exam_id}/question_{question_num:02d}.jpg")
    
    # Multiple choice options
    options = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    current_answer = st.session_state.user_answers.get(f"{exam_id}_{question_num}")
    
    selected = st.radio(
        f"Select your answer for Question {question_num}:",
        options,
        index=options.index(current_answer) if current_answer in options else None
    )
    
    return selected

def main():
    st.title("ENGAA/TMUA Exam Preparation")

    # Load configuration and create file
    config = load_questions_config()

    # Create tabs
    tab1, tab2 = st.tabs(["Practice", "History"])

    with tab1:
        practice_tab(config)

    with tab2:
        history_tab(config)

def practice_tab(config):
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        
        # Exam selection
        exam_options = {k: v['name'] for k, v in config.items()}
        selected_exam_key = st.selectbox(
            "Select Exam:", 
            options=list(exam_options.keys()), 
            format_func=lambda x: exam_options[x]
        )
        
        if selected_exam_key != st.session_state.selected_exam:
            st.session_state.selected_exam = selected_exam_key
            st.session_state.current_question = 0
            st.session_state.start_time = time.time()
            st.session_state.total_time = 0
            st.session_state.question_start_time = time.time()
            st.session_state.question_times = {}
            st.rerun()
        
        if selected_exam_key:
            exam_config = config[selected_exam_key]
            sections = list(exam_config['sections'].keys())
            selected_section = st.selectbox("Select Section:", sections)
            
            questions = exam_config['sections'][selected_section]['questions']
            answers = exam_config['sections'][selected_section]['answers']
            
            question_idx = st.slider("Question", 0, len(questions)-1, st.session_state.current_question)
            current_q_num = questions[question_idx]
            
            if question_idx != st.session_state.current_question:
                # Save time spent on previous question
                if st.session_state.question_start_time and st.session_state.current_question >= 0:
                    prev_q_num = questions[st.session_state.current_question]
                    time_spent = time.time() - st.session_state.question_start_time
                    current_time = st.session_state.question_times.get(f"{selected_exam_key}_{prev_q_num}", 0)
                    st.session_state.question_times[f"{selected_exam_key}_{prev_q_num}"] = current_time + time_spent

                st.session_state.current_question = question_idx
                st.session_state.question_start_time = time.time()
                st.rerun()
            
            # Statistics
            answered = len([q for q in questions if f"{selected_exam_key}_{q}" in st.session_state.user_answers])
            correct_count = 0
            for i, q_num in enumerate(questions):
                user_answer = st.session_state.user_answers.get(f"{selected_exam_key}_{q_num}")
                if user_answer == answers[i]:
                    correct_count += 1
            
            wrong_count = answered - correct_count

            st.progress(answered / len(questions))
            st.write(f"Progress: {answered}/{len(questions)}")

            # Timer display and controls
            st.markdown("---")
            st.subheader("⏱️ Timer")

            if st.session_state.start_time is None:
                if st.button("Start Timer"):
                    st.session_state.start_time = time.time()
                    st.rerun()
                st.write("Timer not started")
            else:
                current_time = time.time()
                elapsed = current_time - st.session_state.start_time + st.session_state.total_time
                st.write(f"**Time Elapsed:** {format_time(elapsed)}")

                col_reset, col_pause = st.columns(2)
                with col_reset:
                    if st.button("Reset Timer"):
                        st.session_state.start_time = time.time()
                        st.session_state.total_time = 0
                        st.rerun()
                with col_pause:
                    if st.button("Pause Timer"):
                        st.session_state.total_time += current_time - st.session_state.start_time
                        st.session_state.start_time = None
                        st.rerun()

            st.markdown("---")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Correct", correct_count)
            with col2:
                st.metric("Wrong", wrong_count)
            with col3:
                if answered > 0:
                    accuracy = (correct_count / answered) * 100
                    st.metric("Accuracy", f"{accuracy:.0f}%")
                else:
                    st.metric("Accuracy", "0%")
    
    # Main content
    if selected_exam_key:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"{exam_config['name']} - {selected_section}")
            
            # Display question
            selected_answer = display_question(selected_exam_key, current_q_num)
            
            # Save answer
            if selected_answer:
                st.session_state.user_answers[f"{selected_exam_key}_{current_q_num}"] = selected_answer
            
            # Navigation buttons
            col_prev, col_next, col_check = st.columns([1, 1, 1])
            
            with col_prev:
                if st.button("← Previous", disabled=question_idx == 0):
                    # Save time spent on current question
                    if st.session_state.question_start_time:
                        time_spent = time.time() - st.session_state.question_start_time
                        current_time = st.session_state.question_times.get(f"{selected_exam_key}_{current_q_num}", 0)
                        st.session_state.question_times[f"{selected_exam_key}_{current_q_num}"] = current_time + time_spent

                    st.session_state.current_question = max(0, question_idx - 1)
                    st.session_state.question_start_time = time.time()
                    st.rerun()

            with col_next:
                if st.button("Next →", disabled=question_idx == len(questions) - 1):
                    # Save time spent on current question
                    if st.session_state.question_start_time:
                        time_spent = time.time() - st.session_state.question_start_time
                        current_time = st.session_state.question_times.get(f"{selected_exam_key}_{current_q_num}", 0)
                        st.session_state.question_times[f"{selected_exam_key}_{current_q_num}"] = current_time + time_spent

                    st.session_state.current_question = min(len(questions) - 1, question_idx + 1)
                    st.session_state.question_start_time = time.time()
                    st.rerun()
            
            with col_check:
                if st.button("Check Answer"):
                    correct_answer = answers[question_idx]
                    user_answer = st.session_state.user_answers.get(f"{selected_exam_key}_{current_q_num}")
                    
                    if user_answer == correct_answer:
                        st.success(f"Correct! Answer: {correct_answer}")
                    elif user_answer:
                        st.error(f"Wrong. Your answer: {user_answer}, Correct: {correct_answer}")
                    else:
                        st.warning(f"Select an answer first. Correct: {correct_answer}")
                    st.rerun()
        
        with col2:
            st.subheader("Quick Jump")
            
            # Question grid
            cols = st.columns(4)
            for i, q_num in enumerate(questions):
                with cols[i % 4]:
                    answered = f"{selected_exam_key}_{q_num}" in st.session_state.user_answers
                    if st.button("✓" if answered else str(q_num), key=f"jump_{q_num}"):
                        # Save time spent on current question
                        if st.session_state.question_start_time and st.session_state.current_question >= 0:
                            current_q_num_old = questions[st.session_state.current_question]
                            time_spent = time.time() - st.session_state.question_start_time
                            current_time = st.session_state.question_times.get(f"{selected_exam_key}_{current_q_num_old}", 0)
                            st.session_state.question_times[f"{selected_exam_key}_{current_q_num_old}"] = current_time + time_spent

                        st.session_state.current_question = i
                        st.session_state.question_start_time = time.time()
                        st.rerun()
            
            # Results
            if st.button("Show Results"):
                results_data = []
                for i, q_num in enumerate(questions):
                    user_answer = st.session_state.user_answers.get(f"{selected_exam_key}_{q_num}", "NA")
                    correct_answer = answers[i]
                    time_spent = st.session_state.question_times.get(f"{selected_exam_key}_{q_num}", 0)

                    if user_answer == "NA":
                        result_icon = ""  # Empty for unanswered
                    elif user_answer == correct_answer:
                        result_icon = "✅"
                    else:
                        result_icon = "❌"

                    results_data.append({
                        "Q": q_num,
                        "YA": user_answer,
                        "CA": correct_answer,
                        "R": result_icon,
                        "T": format_time(time_spent) if time_spent > 0 else ""
                    })
                
                # Results table with styled NA values
                df = pd.DataFrame(results_data)
                
                # Create styled dataframe for display
                def style_na(val):
                    if val == "NA":
                        return "color: lightgrey"
                    return ""
                
                styled_df = df.style.applymap(style_na, subset=['YA'])
                st.dataframe(styled_df)
                
                # Final score metrics in two rows
                score_percentage_total = (correct_count / len(questions)) * 100 if len(questions) > 0 else 0
                answered_percentage = (correct_count / answered) * 100 if answered > 0 else 0
                
                st.markdown(f"**Total Score:** {correct_count}/{len(questions)} ({score_percentage_total:.1f}%)")
                if answered > 0:
                    st.markdown(f"**Answered Score:** {correct_count}/{answered} ({answered_percentage:.1f}%)")
                else:
                    st.markdown(f"**Answered Score:** 0/0 (0%)")

            # Save session button
            if st.button("Save Session"):
                save_session_log(selected_exam_key, questions, answers,
                               st.session_state.user_answers, st.session_state.question_times)
                st.success("Session saved to log!")
    
    else:
        st.info("Select an exam to begin.")

def history_tab(config):
    st.header("Exam History")

    # Load session log
    log_data = load_session_log()

    if not log_data:
        st.info("No exam sessions found. Complete and save some practice sessions first!")
        return

    # Get unique exam types and years for filtering
    exam_types = set()
    exam_years = set()
    for session in log_data:
        exam_id = session['exam_id']
        exam_type = exam_id.split('_')[0]  # ENGAA or TMUA
        exam_year = exam_id.split('_')[1]  # 2023, 2022, etc
        exam_types.add(exam_type)
        exam_years.add(exam_year)

    # Filter controls
    col1, col2 = st.columns(2)
    with col1:
        selected_type = st.selectbox("Select Exam Type", ["All"] + sorted(list(exam_types)))
    with col2:
        selected_year = st.selectbox("Select Year", ["All"] + sorted(list(exam_years), reverse=True))

    # Filter sessions based on selection
    filtered_sessions = []
    for session in log_data:
        exam_id = session['exam_id']
        exam_type = exam_id.split('_')[0]
        exam_year = exam_id.split('_')[1]

        type_match = selected_type == "All" or exam_type == selected_type
        year_match = selected_year == "All" or exam_year == selected_year

        if type_match and year_match:
            filtered_sessions.append(session)

    if not filtered_sessions:
        st.warning("No sessions match the selected filters.")
        return

    # Create pivot table view
    st.subheader("Results Matrix")

    # Collect all questions and dates
    all_questions = set()
    all_dates = []

    for session in filtered_sessions:
        date_time = f"{session['date']} {session['time']}"
        all_dates.append(date_time)
        for result in session['results']:
            if result['user_answer']:  # Only include answered questions
                all_questions.add(result['question'])

    all_questions = sorted(list(all_questions))
    all_dates = sorted(list(set(all_dates)))

    if not all_questions:
        st.warning("No answered questions found in the filtered sessions.")
        return

    # Create matrix data
    matrix_data = []
    for q_num in all_questions:
        row_data = {"Question": f"Q{q_num}"}

        for date_time in all_dates:
            # Find session for this date_time
            session = next((s for s in filtered_sessions
                          if f"{s['date']} {s['time']}" == date_time), None)

            if session:
                # Find result for this question
                result = next((r for r in session['results']
                             if r['question'] == q_num), None)

                if result and result['user_answer']:
                    correct_icon = "✅" if result['is_correct'] else "❌"
                    time_str = format_time(result['time_spent']) if result['time_spent'] > 0 else ""
                    cell_value = f"{result['user_answer']} {correct_icon} ({time_str})"
                    row_data[date_time] = cell_value
                else:
                    row_data[date_time] = ""
            else:
                row_data[date_time] = ""

        matrix_data.append(row_data)

    # Display matrix
    df_matrix = pd.DataFrame(matrix_data)
    st.dataframe(df_matrix, use_container_width=True)

    # Summary statistics
    st.subheader("Summary Statistics")

    total_sessions = len(filtered_sessions)
    total_questions_attempted = sum(len([r for r in s['results'] if r['user_answer']]) for s in filtered_sessions)
    total_correct = sum(len([r for r in s['results'] if r['is_correct']]) for s in filtered_sessions)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Sessions", total_sessions)
    with col2:
        st.metric("Questions Attempted", total_questions_attempted)
    with col3:
        if total_questions_attempted > 0:
            accuracy = (total_correct / total_questions_attempted) * 100
            st.metric("Overall Accuracy", f"{accuracy:.1f}%")
        else:
            st.metric("Overall Accuracy", "0%")

if __name__ == "__main__":
    main()

    # cd ESAT/
    # python -m streamlit run esat_app.py

    # Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    # claude