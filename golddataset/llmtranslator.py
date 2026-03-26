import os
import random
import re
import time
import openai
from openai import OpenAI
from openai import OpenAI, OpenAIError, APIError, RateLimitError
max_retries = 5  # maximum attempts
base_delay = 2   # base delay in seconds for exponential backoff


api_keys = ['YOUR API KEY']

# Prompt format updated for Arabic-English alignment
prompt_format = '''Please translate the arabic text to English, output text only:
{arabic_text}
'''

prompt_format_ar = '''Please translate the arabic text to Arabic, output text only:
{arabic_text}
'''

def read_file(file_path):
    """Reads the contents of a text file and returns a list of lines."""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        return [line.strip() for line in lines if line.strip()]


def count_words(line):
    """Counts the number of words in a line."""
    return len(re.findall(r'\S+', line))  # \S+ matches non-whitespace sequences


def get_lines_up_to_word_limit(startindex, lines, max_words=500):
    """Selects lines from a list until the word count reaches the limit."""
    selected_lines = []
    total_words = 0
    line_number = []

    for index in range(startindex, len(lines)):
        line = lines[index]
        num_words = count_words(line)
        if total_words + num_words > max_words:
            break
        selected_lines.append(line.strip())
        total_words += num_words
        line_number.append(index)

    return line_number, selected_lines, total_words


def get_lines_up_to_total_lines(total_lines, lines):
    """Selects specific lines from a list based on indexes."""
    selected_lines = []
    total_words = 0
    line_number = 0
    for index in total_lines:
        line = lines[index]
        num_words = count_words(line)
        selected_lines.append(line.strip())
        total_words += num_words
        line_number += 1
    return line_number, selected_lines, total_words


def translate_lines_en(file, source_lines):
    print(f"Start translate: {file}")

    for line in source_lines:
        messages = [
            {
                'role': 'system',
                'content': 'You are an expert in Arabic-English translation.'
            },
            {
                'role': 'user',
                'content': prompt_format.format(
                    arabic_text=line
                )
            }
        ]

        # Retry loop
        for attempt in range(max_retries):
            api_key = api_keys[attempt % len(api_keys)]  # rotate API key if multiple
            client = OpenAI(api_key=api_key)

            try:
                completion = client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=messages,
                )

                if completion and completion.choices:
                    print(completion)
                    result_text = completion.choices[0].message.content.strip()
                    print(result_text)

                    output_dir = "law/artoen"
                    os.makedirs(output_dir, exist_ok=True)
                    output_path = os.path.join(output_dir, f"{file}")

                    with open(output_path, "a", encoding="utf8") as fout:
                        fout.write(result_text + "\n")

                    break  # success → exit retry loop

            except (APIError, RateLimitError, OpenAIError) as e:
                wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
            except Exception as e:
                print(f"Unexpected error on attempt {attempt + 1}: {e}")
                time.sleep(1)
        else:
            print(f"❌ All {max_retries} retries failed for {file} .")



def translate_lines_ar(file, source_lines):
    print(f"Start translate: {file}")

    for line in source_lines:
        messages = [
            {
                'role': 'system',
                'content': 'You are an expert in English-Arabic translation.'
            },
            {
                'role': 'user',
                'content': prompt_format_ar.format(
                    arabic_text=line
                )
            }
        ]

        # Retry loop
        for attempt in range(max_retries):
            api_key = api_keys[attempt % len(api_keys)]  # rotate API key if multiple
            client = OpenAI(api_key=api_key)

            try:
                completion = client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=messages,
                )

                if completion and completion.choices:
                    print(completion)
                    result_text = completion.choices[0].message.content.strip()
                    result_text = result_text.replace("\n", " ")
                    print(result_text)

                    output_dir = "law/entoar"
                    os.makedirs(output_dir, exist_ok=True)
                    output_path = os.path.join(output_dir, f"{file}")

                    with open(output_path, "a", encoding="utf8") as fout:
                        fout.write(result_text + "\n")

                    break  # success → exit retry loop

            except (APIError, RateLimitError, OpenAIError) as e:
                wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
            except Exception as e:
                print(f"Unexpected error on attempt {attempt + 1}: {e}")
                time.sleep(1)
        else:
            output_dir = "entoar"
            output_path = os.path.join(output_dir, f"{file}")

            with open(output_path, "a", encoding="utf8") as fout:
                fout.write("XXerrorXX" + "\n")

            print(f"❌ All {max_retries} retries failed for {file} .")


# ---------------- MAIN EXECUTION ----------------
folder_path = "law/ar"
for file in os.listdir(folder_path):
    # if "005" not in file:
    #     continue
    source_file_path = os.path.join(folder_path, file)
    target_file_path = source_file_path.replace("ar", "en")
    #
    # # Read the files
    source_lines = read_file(source_file_path)
    target_lines = read_file(target_file_path)

    # Gap control
    # gap = 10  # adjustable window size for alignment


    translate_lines_en(file, source_lines)
    translate_lines_ar(file, target_lines)
