import json
from difflib import get_close_matches
from typing import List, Optional

def load_knowledge_data(file_path: str) -> dict:
    with open(file_path, 'r') as file:
        data: dict = json.load(file)
    return data

def save_knowledge_data(file_path: str, data: dict):
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2)

def find_best_match(user_question: str, questions: List[str]) -> Optional[str]:
     matches: list = get_close_matches(user_question, questions, n=1, cutoff=0.6)
     return matches[0] if matches else None

def get_best_possible_answer(question: str, knowledge_data: dict) -> Optional[str]:
    for q in knowledge_data['questions']:
         if q["question"] == question:
              return q["answer"]
         
def chat_bot():
     knowledge_data: dict = load_knowledge_data('knowledge_base.json')
     while True:
          user_input: str = input("You: ")

          if user_input.lower() == 'quit':
               break
          
          best_match: Optional[str] = find_best_match(user_input, [q['question'] for q in knowledge_data['questions']])

          if best_match:
               answer: str = get_best_possible_answer(best_match, knowledge_data)
               print(f'NetGeni: {answer}')
          else:
            print('NetGeni: I don\'t have the script, shall I learn from you?')
            new_answer: str = input('Give me the details or you can "ask" me other questions: ')
            if new_answer.lower() != 'ask':
                 knowledge_data["questions"].append({"question": user_input, "answer": new_answer})
                 save_knowledge_data('knowledge_base.json', knowledge_data)
                 print("NetGeni: Thank you! I learned from you to help others!")

if __name__ == '__main__':
     chat_bot()
     

     
