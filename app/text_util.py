import re
from typing import Iterator


def split_long_text(text: str, max_len: int = 4096) -> Iterator[str]:
    """Attempt to split text into chunks, so that every chunk is not longer than max_len.

    First try to split by double line breaks, then by single line breaks, then by sentence breaks, then by whitespace,
    and if everything else failed, by codepoints.
    """

    patterns = [
        r'\n\n',
        r'\n',
        r'[.?!]+\s+',
        r'\s+',
    ]
    matchers = [re.compile(fr'(.*{pattern}).*?$', re.DOTALL).match for pattern in patterns]

    while text:
        if len(text) <= max_len:
            yield text
            return

        full_chunk = chunk = text[:max_len]
        for matcher in matchers:
            rxm = matcher(chunk)
            if rxm:
                chunk = rxm.group(1)
                if chunk:
                    break
        else:
            chunk = full_chunk

        assert chunk
        yield chunk
        text = text[len(chunk):]
