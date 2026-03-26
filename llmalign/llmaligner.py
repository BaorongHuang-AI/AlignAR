import os
import re
import time
import openai
from openai import OpenAI


api_keys = ['YOUR API KEY']

prompt_format = '''You are an expert in translation. Align two documents and output bilingual pairs. 
Document A is in Arabic, and Document B is in English. 
Both documents contain sentences that are similar in meaning but may not be direct translations of each other. 
Your task is to find the translations from Document B for lines in Document A and output them as bilingual pairs.
Use the source line as one sentence as much as possible. In some cases, more than one source lines are matched to more than one target lines.
Find the translations for all the source lines. Do not merge the source lines unless absolutely necessary.
Produce the complete bilingual alignment in one large JSON array.
When finding the translation, ignore the line number such as §0§, §1§ at the beginning of each sentence and keep the line number in the output.

Document A (Arabic):
{arabic_text}

Document B (English):
{english_text}


Output Format:
[
{{"Arabic Sentence": "$line no$نظام القضاء",
 "English Sentence": "$line no$Law of the Judiciary"
}}
]
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

def align_lines(file, index, source_lines, target_lines):
    print(f"Start aligning: {file} - chunk {index}")

    messages = [
        {
            'role': 'system',
            'content': 'You are an expert in Arabic-English translation alignment.'
        },
        {
            'role': 'user',
            'content': prompt_format.format(
                arabic_text="\n".join(source_lines),
                english_text="\n".join(target_lines),
            )
        }
    ]

    client = OpenAI(api_key=api_keys[0])

    completion = client.chat.completions.create(
        model="gpt-5-mini",
        messages=messages,
    )
    print("finish aligning")
    if completion:
        result_text = completion.choices[0].message.content.strip()
        print(result_text)

        output_dir = "llmalignresults/law/gpt"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{file}")

        with open(output_path, "a", encoding="utf8") as fout:
            fout.write(result_text + "\n")


# ---------------- MAIN EXECUTION ----------------
folder_path = "../golddataset/law/ar"
for file in os.listdir(folder_path):
    if "005"  not  in file:
        continue
    source_file_path = os.path.join(folder_path, file)
    target_file_path = source_file_path.replace("ar", "en")

    # Read the files
    source_lines = read_file(source_file_path)
    target_lines = read_file(target_file_path)
    source_lines = [f"§{index}§ {line}" for index, line in enumerate(source_lines)]
    target_lines = [f"§{index}§ {line}" for index, line in enumerate(target_lines)]
    index = 0
    align_lines(file, index, source_lines, target_lines)
