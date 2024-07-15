import re
from typing import List, Mapping, Callable, Tuple, Set


def _make_matcher(patterns: List[str]) -> re.Pattern[str]:
    return re.compile('|'.join(re.escape(pat) for pat in patterns))


def _ruleset_to_converter(rules: List[Tuple[str, str]]) -> Callable[[str], str]:
    # longer replacements come first, relative order is preserved
    rules.sort(key=lambda x: -len(x[0]))
    rulemap = dict(rules)

    rx = _make_matcher([left for left, _ in rules])

    def replace(text: str):
        return rx.sub(lambda m: rulemap.get(m.group(0), m.group(0)), text)

    return replace


def _table_to_ruleset(table: str) -> List[Tuple[str, str]]:
    lines = table.splitlines()
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

    return rules


def _get_unique_rules(rulesets: Mapping[str, List[Tuple[str, str]]]) -> Mapping[str, Set[str]]:
    rulesets = {lang: dict(rules) for lang, rules in rulesets.items()}

    # identify left rules that are unique to given lang code
    uniques = {}
    for lang1, ruleset1 in rulesets.items():
        union = set()

        for lang2, ruleset2 in rulesets.items():
            if lang1 == lang2:
                continue
            union |= ruleset2.keys()

        uniques[lang1] = ruleset1.keys() - union
        assert uniques[lang1]

    return uniques


def _get_unique_detectors(uniques: Mapping[str, Set[str]]) -> Mapping[str, Callable[[str], bool]]:
    detectors = {}

    for lang, unique in uniques.items():
        rx = _make_matcher(sorted(unique, key=lambda x: -len(x[0])))
        detectors[lang] = lambda text: rx.search(text) is not None

    return detectors


class Converter:
    def __init__(self, tables: Mapping[str, str]):
        self.tables = tables
        self.rulesets = {lang: _table_to_ruleset(table) for lang, table in tables.items()}
        self.converters = {lang: _ruleset_to_converter(ruleset) for lang, ruleset in self.rulesets.items()}
        self.uniques = _get_unique_rules(self.rulesets)
        self.unique_detectors = _get_unique_detectors(self.uniques)

    def convert(self, lang: str, text: str) -> str:
        return self.converters[lang](text)

    def detect_lang(self, text: str) -> Set[str]:
        detected = set()

        for lang, detect in self.unique_detectors.items():
            if detect(text):
                detected.add(lang)

        return detected
