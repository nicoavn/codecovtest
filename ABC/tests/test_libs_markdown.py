import textwrap

from ..libs import markdown


def test_render_unsafe():
    src = textwrap.dedent(
        '''
        # A Test
        <script></script>
        http://example.com
    '''
    )

    expected = textwrap.dedent(
        '''
    <h1>A Test</h1>
    <script></script>
    <p><a href="http://example.com">http://example.com</a></p>
    '''
    ).lstrip()

    assert markdown.render_unsafe(src) == expected


def test_render():
    src = textwrap.dedent(
        '''
        # A Test
        <script></script>
        http://example.com
    '''
    )

    expected = '<h1>A Test</h1> <p><a href="http://example.com">http://example.com</a></p>'

    assert markdown.render(src).strip() == expected


def test_render_simple():
    assert markdown.render('some text').strip() == '<p>some text</p>'
