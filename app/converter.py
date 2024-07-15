import re
from typing import List, Mapping, Callable, Tuple, Set

from app.tables import UKR_TABLE, ISV_TABLE, NUMERALS_TABLE


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
        _rx = _make_matcher(sorted(unique, key=lambda x: (-len(x[0]), x[0])))
        detectors[lang] = lambda text, *, rx=_rx: rx.search(text) is not None

    return detectors


class Converter:
    def __init__(self):
        self.tables = {
            'ukr': UKR_TABLE,
            'isv': ISV_TABLE,
        }
        self.rulesets = {lang: _table_to_ruleset(table) for lang, table in self.tables.items()}
        self.converters = {lang: _ruleset_to_converter(ruleset) for lang, ruleset in self.rulesets.items()}
        self.uniques = _get_unique_rules(self.rulesets)
        self.unique_detectors = _get_unique_detectors(self.uniques)
        self.numeral_ruleset = dict(_table_to_ruleset(NUMERALS_TABLE))

    def convert(self, lang: str, text: str) -> str:
        text = self.converters[lang](text)

        for other_lang, converter in self.converters.items():
            if lang != other_lang:
                text = self.converters[other_lang](text)

        text = self.convert_numerals(text)

        return text

    def detect_lang(self, text: str) -> Set[str]:
        detected = set()

        for lang, detect in self.unique_detectors.items():
            if detect(text):
                detected.add(lang)

        return detected

    def convert_numerals(self, text: str) -> str:
        return re.sub(r'(\d+)', lambda m: self._convert_numeral(m.group(1)), text)

    def _convert_numeral(self, digits: str):
        num = int(digits)
        if num >= 10_000 or num == 0:
            return digits

        converted = []
        for offset, digit in enumerate(digits):
            if digit == '0':
                continue

            offset = len(digits) - offset - 1
            key = f'{digit}{'0' * offset}'
            converted.append(self.numeral_ruleset[key])

        if 11 <= (num % 100) <= 19:
            converted[-2:] = reversed(converted[-2:])

        converted[(len(converted) - 1) // 2] += '҃'
        converted = ''.join(converted)
        converted = f'·{converted}·'

        return converted
