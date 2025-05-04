import requests
import random
import time
from datetime import datetime
import json
import re
from bs4 import BeautifulSoup

# Base URL for the API
BASE_URL = "https://oradea.artorius.uk"

# Correct answers extracted from the pickle file
CORRECT_ANSWERS = {
    1: "Al Doilea Război Mondial",
    2: "Constantin Brâncuși",
    3: "Monarhia Habsburgică",
    4: "2018",
    5: "castani",
    6: "1994",
    7: "1600",
    8: "bizantin",
    9: "spadă",
    10: "Regatul Poloniei",
    11: "Steaua lui David",
    12: "Capucinilor",
    13: "craniu",
    14: "Fazele lunii",
    15: "balauri",
    16: "catolic",
    17: "Prim Ministru",
    18: "Miel",
    19: "Vatican",
    20: "Isus și Maria",
    21: "Hohenzollern",
    22: "9",
    23: "ebraică",
    24: "1850",
    25: "Arhanghelul Mihail",
    26: "4",
    27: "Crișul Repede",
    28: "Ady Endre",
    29: "Melpomene și Thalia",
    30: "Liliomfi",
    31: "1919",
    32: "1984",
    33: "Dutka Akos",
    34: "Ferenc Rier",
    35: "România Mare",
    36: "1905",
    37: "Mihai Eminescu",
    38: "arhitect",
    39: "Lege",
    40: "Léda",
    41: "După întuneric, lumină",
    42: "Biblia de la Oradea",
    43: "leu",
    44: "Podul Paralelor"
}

# Incorrect answers from the pickle file (alternatives)
INCORRECT_ANSWERS = [
    "Războiul de Independență", "Primul Război Mondial", "Mircea Eliade", 
    "George Enescu", "Austro-Ungaria", "România", "stejari", "nuci", 
    "slavon", "roman", "sabie", "iatagan", "Transilvania", "Regatul Ungariei",
    "vițel", "berbec", "Nimic. E doar de design.", "Luna calendaristică",
    "vulturi", "lei", "calvin", "lutheran", "Secretar de Stat", "Ministru de Externe",
    "Leu", "Taur", "Îngerul Gabriel", "Sfântul Ladislau", "Habsburg", "Hohenstaufen",
    "Biserica", "Gabriel", "Crișul Negru", "Someș", "Clio și Urania", 
    "Euterpe și Caliope", "Emod Tamas", "Partidul Național Român", "Societatea Literară",
    "Julianna", "Mária", "După război, victorie", "După frică, curaj",
    "Răspândirea religiei catolice în Transilvania", "Legislația Țării Făgărașului",
    "Podul de Fier", "Podul lui Traian"
]

def test_question_view(group_number, question_number, answer_text):
    """Submit an answer to a question for a specific group"""
    url = f"{BASE_URL}/question/?group_number={group_number}&question_number={question_number}"
    
    # First make a GET request to get the CSRF token
    session = requests.Session()
    response = session.get(url)
    
    if response.status_code != 200:
        print(f"Error accessing question: {response.status_code}")
        return None
    
    # Extract CSRF token from the response
    csrf_token = None
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    if csrf_input:
        csrf_token = csrf_input.get('value')
    
    if not csrf_token:
        # Try to extract from the cookie
        csrf_token = session.cookies.get('csrftoken')
    
    if not csrf_token:
        print("Could not extract CSRF token")
        return False
    
    # Now make a POST request with the answer
    data = {
        'answer': answer_text,
        'csrfmiddlewaretoken': csrf_token,
    }
    
    # Add the referer header which is often required for CSRF validation
    headers = {
        'Referer': url
    }
    
    response = session.post(url, data=data, headers=headers)
    
    if response.status_code == 200 or response.status_code == 302:  # 302 is redirect
        print(f"Successfully submitted answer for Group {group_number}, Question {question_number}")
        return True
    else:
        print(f"Error submitting answer: {response.status_code}")
        return False

def view_admin_dashboard():
    """View the admin dashboard"""
    url = f"{BASE_URL}/dashboard/"
    response = requests.get(url)
    
    if response.status_code == 200:
        print("Successfully accessed admin dashboard")
        return response.text
    else:
        print(f"Error accessing admin dashboard: {response.status_code}")
        return None

def view_group_details(group_number):
    """View details for a specific group"""
    url = f"{BASE_URL}/group/{group_number}/"
    response = requests.get(url)
    
    if response.status_code == 200:
        print(f"Successfully accessed details for Group {group_number}")
        return response.text
    else:
        print(f"Error accessing group details: {response.status_code}")
        return None

def run_test_scenario():
    """Run a test scenario with multiple groups answering questions"""
    # Number of groups to simulate
    num_groups = 10
    
    # Get the max question number from our correct answers
    max_question = max(CORRECT_ANSWERS.keys())
    
    # Ensure exactly 3 random groups answer all questions
    complete_groups = random.sample(range(1, num_groups + 1), 3)
    print(f"Groups {complete_groups} will complete 100% of questions")
    
    # Create a list of all (group, question) pairs to be answered
    answer_pairs = []
    
    # First, add all pairs for complete groups
    for group_num in complete_groups:
        for question_num in range(1, max_question + 1):
            answer_pairs.append((group_num, question_num))
    
    # For remaining groups, add 70-80% of questions
    for group_num in range(1, num_groups + 1):
        if group_num not in complete_groups:
            # Decide how many questions this group will answer (70-80%)
            num_answers = random.randint(int(max_question * 0.7), int(max_question * 0.8))
            
            # Randomly select questions
            questions_to_answer = random.sample(range(1, max_question + 1), num_answers)
            
            for question_num in questions_to_answer:
                answer_pairs.append((group_num, question_num))
    
    # Shuffle all the pairs to randomize the order
    random.shuffle(answer_pairs)
    
    # Track groups and their progress
    group_progress = {group_num: 0 for group_num in range(1, num_groups + 1)}
    total_answers_per_group = {
        group_num: max_question if group_num in complete_groups 
        else random.randint(int(max_question * 0.7), int(max_question * 0.8))
        for group_num in range(1, num_groups + 1)
    }
    
    print(f"\nTotal answers planned per group:")
    for group_num, total in total_answers_per_group.items():
        print(f"Group {group_num}: {total} answers ({round(total/max_question*100)}%)")
    
    print(f"\nTotal answer events: {len(answer_pairs)}")
    
    # Now submit all answers in the randomized order
    for i, (group_num, question_num) in enumerate(answer_pairs):
        # Update and show progress
        group_progress[group_num] += 1
        progress_percent = round(group_progress[group_num] / total_answers_per_group[group_num] * 100)
        
        print(f"\n--- Answer {i+1}/{len(answer_pairs)} | Group {group_num} ({progress_percent}% complete) ---")
        
        # Decide if this answer will be correct (70% chance)
        will_be_correct = random.random() < 0.7
        
        if will_be_correct and question_num in CORRECT_ANSWERS:
            # Use the correct answer
            answer = CORRECT_ANSWERS[question_num]
            print(f"Submitting CORRECT answer for question {question_num}: {answer}")
        else:
            # Use an incorrect answer
            answer = random.choice(INCORRECT_ANSWERS)
            print(f"Submitting INCORRECT answer for question {question_num}: {answer}")
        
        # Submit the answer
        test_question_view(group_num, question_num, answer)
        
        # Add a small delay between requests to avoid overwhelming the server
        time.sleep(1)
    
    # View the admin dashboard to see results
    dashboard = view_admin_dashboard()
    if dashboard:
        print("\n--- Admin Dashboard Summary ---")
        # Parse the HTML to extract some meaningful data
        soup = BeautifulSoup(dashboard, 'html.parser')
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            print(f"Found {len(rows)-1} groups in the dashboard")  # -1 for header row
        else:
            print("No table found in dashboard")
    
    # View details for each group
    for group_num in range(1, num_groups + 1):
        details = view_group_details(group_num)
        if details:
            soup = BeautifulSoup(details, 'html.parser')
            answers_table = soup.find_all('table')
            if len(answers_table) > 0:
                rows = answers_table[0].find_all('tr')
                print(f"Group {group_num} has {len(rows)-1} answers")  # -1 for header row
            else:
                print(f"No answer table found for Group {group_num}")

if __name__ == "__main__":
    print(f"Starting API tests for {BASE_URL} at {datetime.now()}")
    run_test_scenario()
    print(f"Tests completed at {datetime.now()}") 