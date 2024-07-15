import re

def build_converter(table: str):
    lines = table.split('\n')
    rules = []
    for raw in lines:
        # remove trailing # comments
        line = re.sub(r'\s*#.*?$', r'', raw)

        # remove empty lines and lines with whitespace only
        line = line.strip()
        if not line:
            continue

        # verify that all lines have one " - " and split into left and right
        parts = re.split(r'\s+-\s+', line, 1)

        if len(parts) != 2:
            raise ValueError(f'Expected single delimiter " - " at line: {raw}')

        left, right = [re.split(r'\s+', part.strip()) for part in parts]
        if len(left) != len(right):
            raise ValueError(f'Left and right halves must have the same number of tokens, '
                             f'left has {len(left)}, right has {len(right)} at line: {raw}')

        for l, r in zip(left, right):
            rules.append((l, r))

    # longer replacements come first, relative order is preserved
    rules.sort(key=lambda x: -len(x[0]))
    rulemap = dict(rules)

    rx = re.compile('|'.join(re.escape(left) for left, _ in rules))

    def replace(text: str):
        return rx.sub(lambda m: rulemap.get(m.group(0), m.group(0)), text)

    return replace
