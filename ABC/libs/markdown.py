import functools

import html_sanitizer
import markdown_it


@functools.cache
def _init():
    """Use a common function for init so the whole app uses the same config"""
    return markdown_it.MarkdownIt('gfm-like'), html_sanitizer.Sanitizer()


def render(text):
    markdown, sanitizer = _init()
    return sanitizer.sanitize(markdown.render(text))


def render_unsafe(text):
    markdown, _ = _init()
    return markdown.render(text)
