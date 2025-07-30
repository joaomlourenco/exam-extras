import sys
import re

def extract_correct_choices_from_text(text):
    key = ""
    
    # Match all \begin{choices} ... \end{choices} blocks (including optional parameters like [2])
    choices_blocks = re.findall(r'\\begin\{choices.*?\}.*?\\end\{choices\}', text, re.DOTALL)

    for block in choices_blocks:
        lines = block.strip().split('\n')
        letters = ['A', 'B', 'C', 'D']
        correct_letters = []

        # for i, line in enumerate(lines[1:-1]):
        #     print(i, line)
        # print("------------------------------------------------------------")
        for i, line in enumerate(lines[1:-1]):
            if line.strip().startswith('\\CHOICE'):
                if i < len(letters):
                    correct_letters.append(letters[i])
        key += "\t"+"".join(correct_letters)
    return key.strip()

def main():
    version = ""
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        match = re.search(r'-(\w)\.tex', filename)
        if match:
            version = match.group(1)
        else:
            version = "X"
        with open(filename, 'r', encoding='utf-8') as file:
            text = file.read()
    else:
        version = "X"
        text = sys.stdin.read()
    
    key = extract_correct_choices_from_text(text)
    print (f"{version.upper()}\t{key}")

if __name__ == '__main__':
    main()
