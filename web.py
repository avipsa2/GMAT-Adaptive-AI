import streamlit as st
import pandas as pd
import random
import matplotlib.pyplot as plt
import google.generativeai as genai

genai.configure(api_key="API_KEY")

def generate_questions(difficulty):
    questions = []
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-002", api_version="v1beta")
    for i in range(10):
        prompt = f"""
        Generate a single Graduate Management Admission Test (GMAT) quantitative reasoning question with {difficulty} difficulty.
        Ensure:
        - The question is logically sound and grammatically correct.
        - The correct answer is a whole number percentage or a clean numerical value.
        - Provide four distinct answer choices labeled A, B, C, and D, where exactly one is correct.
        - ENSURE THAT THE OPTIONS GENERATED MUST CONTAIN THE CORRECT ANSWER TO THE QUESTION.
        - Format the correct answer as: "Correct Answer: X", where X is A, B, C, or D.
        - Do the calculation before generating the options and correct answer but don't show it.

        The question should be based on one of the following topics:
        - Algebra
        - Arithmetic
        - Data Sufficiency
        - Multi-Source Reasoning (analyzing data from various sources like text, tables, graphics)
        - Table Analysis
        - Graphics Interpretation (scatter plots, x/y graphs, bar charts, pie charts, statistical distributions)
        - Two-Part Analysis (Quantitative, Verbal, or both)

        Example:
        A car dealership sells two models of cars: sedan and SUV. In January, the dealership sold 120 sedans and 80 SUVs. 
        In February, the dealership sold 150 sedans and 60 SUVs. By what percentage did the total number of cars sold 
        by the dealership decrease from January to February?
        
        A) 5%
        B) 10%
        C) 15%
        D) 20%
        Correct Answer: A
        """

        response = model.generate_content(prompt)
        question_data = response.text

        try:
            question_text = question_data.split("Correct Answer:")[0].strip()

            choices = {}
            for line in question_data.split("\n"):
                if line.startswith(("A)", "B)", "C)", "D)")):
                    key, value = line.split(")", 1)
                    choices[key.strip()] = value.strip()

            correct_option = question_data.split("Correct Answer:")[1].strip()

            questions.append({
                "question": question_text,
                "choices": choices,
                "correct_answer": correct_option
            })

        except (IndexError, ValueError) as e:
            print(f"Error parsing response: {question_data}, Error: {e}")
            continue

    return questions



def get_correct_answer(question_data):
    return question_data['correct_answer']

def get_points(difficulty):
    if difficulty == 'hard':
        return 3
    elif difficulty == 'medium':
        return 2
    else:
        return 1

def adjust_difficulty_correct(current_difficulty):
    if current_difficulty == 'easy':
        return 'medium'
    elif current_difficulty == 'medium':
        return 'hard'
    return 'hard'  

def adjust_difficulty_incorrect(current_difficulty):
    if current_difficulty == 'hard':
        return 'medium'
    elif current_difficulty == 'medium':
        return 'easy'
    return 'easy' 

st.title("AI-Powered Adaptive GMAT Quant Test")

if 'current_question' not in st.session_state:
    st.session_state['current_question'] = 0
    st.session_state['score'] = 0
    st.session_state['responses'] = []
    st.session_state['difficulty_levels'] = []
    st.session_state['max_score'] = 30
    st.session_state['min_score'] = 0
    st.session_state['question_difficulty'] = 'medium'
    st.session_state['questions'] = []
    st.session_state['user_answers'] = [] 
    st.session_state['correct_answers'] = [] 

if st.button("Start Test"):
    st.session_state['questions'] = generate_questions(st.session_state['question_difficulty'])
    st.session_state['all_questions'] = st.session_state['questions'][:]
    st.session_state['current_question'] = 0
    st.session_state['score'] = 0
    st.session_state['responses'] = []
    st.session_state['difficulty_levels'] = []
    st.session_state['question_difficulty'] = 'medium'
    st.session_state['user_answers'] = []
    st.session_state['correct_answers'] = []
    st.rerun()

if 'questions' in st.session_state and len(st.session_state['questions']) > 0:
    current_question = st.session_state['current_question']
    if current_question < len(st.session_state['questions']):
        question_data = st.session_state['questions'][current_question]

        st.write(question_data['question'])
        answer = st.radio("Select your answer:", options=["A", "B", "C", "D"])

        if st.button("Submit Answer"):
            correct_answer = get_correct_answer(question_data)
            st.session_state['correct_answers'].append(correct_answer)
            st.session_state['user_answers'].append(answer)
            if answer == correct_answer:
                st.session_state['score'] += get_points(st.session_state['question_difficulty'])
                st.session_state['difficulty_levels'].append(st.session_state['question_difficulty'])
                st.session_state['responses'].append(True)
                st.session_state['question_difficulty'] = adjust_difficulty_correct(st.session_state['question_difficulty'])
            else:
                st.session_state['difficulty_levels'].append(st.session_state['question_difficulty'])
                st.session_state['responses'].append(False)
                st.session_state['question_difficulty'] = adjust_difficulty_incorrect(st.session_state['question_difficulty'])

            new_questions = generate_questions(st.session_state["question_difficulty"])
            st.session_state["questions"] = new_questions
            st.session_state["all_questions"].extend(new_questions)  
            st.session_state["current_question"] += 1
            st.rerun()

if 'difficulty_levels' in st.session_state and len(st.session_state['difficulty_levels']) > 0:
    if len(st.session_state['user_answers']) == len(st.session_state['questions']):
        st.write("Test Complete")
        st.write(f"Your Score: {st.session_state['score']}")
        summary_data = {
            "Difficulty": st.session_state['difficulty_levels'],
            "Correct": st.session_state['responses']
        }
        summary_df = pd.DataFrame(summary_data)
        st.table(summary_df)

        st.write("### Summary of All Questions and Your Answers:")
        for i in range(len(st.session_state["all_questions"])):
            question_data = st.session_state["all_questions"][i]
            st.write(f"**Question {i + 1}:** {question_data['question']}")
            st.write(f"  **Your Answer:** {st.session_state['user_answers'][i]}")
            st.write(f"  **Correct Answer:** {st.session_state['correct_answers'][i]}")

        min_score = st.session_state['min_score']
        max_score = st.session_state['max_score']
        user_score = st.session_state['score']

        fig, ax = plt.subplots(figsize=(8, 1))

        ax.barh([0], max_score - min_score, left=min_score, height=0.5, color='lightgray')

        ax.barh([0], user_score - min_score, left=min_score, height=0.5, color='skyblue')

        ax.plot([min_score, min_score], [-0.25, 0.75], color='black', linestyle='--')
        ax.plot([max_score, max_score], [-0.25, 0.75], color='black', linestyle='--')
        ax.plot([user_score, user_score], [-0.25, 0.75], color='red', marker='o', markersize=8)

        ax.text(min_score, -0.4, f"Min: {min_score}", ha='center', va='top')
        ax.text(max_score, -0.4, f"Max: {max_score}", ha='center', va='top')
        ax.text(user_score, 0.9, f"Your Score: {user_score}", ha='center', va='bottom', color='red')

        ax.set_yticks([])
        ax.set_xlim(min_score - 1, max_score + 1)
        ax.set_xlabel("Score")

        st.pyplot(fig)
