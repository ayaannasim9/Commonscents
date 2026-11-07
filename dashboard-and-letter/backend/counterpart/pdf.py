"""Portable PDF rendering of the same escaped HTML blocks used by the letter preview."""
from html.parser import HTMLParser
from html import escape
from io import BytesIO


class LetterBlocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_body = False
        self.tag = None
        self.parts = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.in_body = True
        if self.in_body and tag in ('h1', 'h2', 'p', 'li'):
            self.tag = tag
            self.parts = []

    def handle_data(self, data):
        if self.in_body and self.tag:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == self.tag:
            self.blocks.append((tag, ''.join(self.parts)))
            self.tag = None
        if tag == 'body':
            self.in_body = False


def render_pdf(html: str) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    parser = LetterBlocks()
    parser.feed(html)
    stream = BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=18*mm, bottomMargin=18*mm, title='Your monthly letter')
    styles = {
        'h1': ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=22, leading=28, spaceAfter=12),
        'h2': ParagraphStyle('Section', fontName='Helvetica-Bold', fontSize=16, leading=22, spaceBefore=14, spaceAfter=6, keepWithNext=True),
        'p': ParagraphStyle('Body', fontName='Helvetica', fontSize=14, leading=21, spaceAfter=7),
        'li': ParagraphStyle('Slip', fontName='Helvetica', fontSize=14, leading=21, spaceAfter=4),
    }
    story = []
    for tag, text in parser.blocks:
        text = text.replace('□', '[ ]')
        style = styles[tag]
        style.textColor = colors.HexColor('#2B0D3E')
        story.append(Paragraph(escape(text), style))
    if not story:
        raise ValueError('Letter HTML has no printable blocks')
    story.append(Spacer(1, 4*mm))
    doc.build(story)
    return stream.getvalue()
