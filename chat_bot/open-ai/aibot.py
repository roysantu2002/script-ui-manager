import openai
from typing import Optional
import json
import datetime

with open('api.txt') as file:
    openai.api_key = file.read()

    
# Fetch the model data
model_data = openai.Model.list()['data']

# Write the data to a JSON file
with open('model.json', 'w') as json_file:
    json.dump(model_data, json_file, indent=4)

def api_response(prompt: str) -> Optional[str]:
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0.9,
            max_tokens=150,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0.6,
            stop=[' Human:', ' AI:']
        )


        # return response.get('choices')[0],
        
        
        # choices: dict = response.get('choices')[0]
        # print(choices)
        # text = choices.get('text')

        return {
            "generated_text": response.get('choices')[0],
            "text": response["choices"][0]["text"]
        }
    
    except Exception as e:
        print(f"error : {e}")

def update_prompt(message: str, pl: list[str]):
    pl.append(message)


def create_prompt(message: str, pl: list[str]) -> str:
    u_message: str = f'\Human: {message}'
    update_prompt(u_message, pl)
    prompt: str = ''.join(pl)
    return prompt

def get_reponse(message: str, pl: list[str]) -> str:
    prompt: str = create_prompt(message, pl)
    bot_response: str = api_response(prompt)
    print(bot_response)

    if bot_response:
       bot_response = bot_response["text"]
       update_prompt(bot_response, pl)
  
       loc: int = bot_response.find('\nAI: ')
       if loc != -1:
            bot_response = bot_response[loc + 5:]

            # bot_response = bot_response[loc + 5:]
    else:
       bot_response = 'Somthing went wrong...'
    
    return bot_response

def main():


    prompt_list: list[str] = ['You be become a Python developer that you would respond with "Yes"',
                              '\nHuman: What is Pythonn',
                              '\nAI: Python is a high-level, versatile, and widely used programming language, Yes']
    while True:
        user_input: str = input('You: ')
        response: str = get_reponse(user_input, prompt_list)
        print(f"Bot: {response}")

if __name__ == '__main__':
    main()
    # response_data = api_response(prompt)

# # Create a unique timestamp
# timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

# # Define the file name with the timestamp and json extension
# json_file_name = f"generated_text_{timestamp}.json"
# text_file_name = f"generated_text_{timestamp}.txt"

# # Write the response data to the JSON file
# with open(json_file_name, 'w') as json_file:
#     json.dump(response_data["generated_text"], json_file, indent=4)

# # Append the generated text to the text file
# with open(text_file_name, 'a') as text_file:
#     text_file.write(response_data["text"])
    
# generated_text = api_response(prompt)
# print(generated_text)

# # Create a unique timestamp
# timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

# # # Define the file name with the timestamp
# # file_name = f"generated_text_{timestamp}.txt"

# # Define the file name with the timestamp and json extension
# file_name = f"generated_text_{timestamp}.json"

# # Write the generated text to the file in JSON format
# with open(file_name, 'w') as json_file:
#     json.dump({"generated_text": generated_text}, json_file, indent=4)
