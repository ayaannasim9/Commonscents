"""The letter is the dashboard's sections laid out as paper plus the tear-off slip (C4, P9).
No logo, no links, no QR code, no phone numbers (P6): scammers will copy the format."""
from __future__ import annotations

from html import escape

from .models import Facts

SLIP_OPTIONS = ["I am worried about something", "Someone has asked me for money", "A bill looks wrong",
                "Can I afford something?", "Something else"]  # same list as ticks (C5)

CSS = """
@page { size: A4; margin: 18mm; }
body { font-family: Overpass, system-ui, sans-serif; font-size: 14pt; line-height: 1.5; color: #2B0D3E; max-width: 170mm; margin: 0 auto; }
h1 { font-size: 22pt; margin: 0 0 4mm; } h2 { font-size: 16pt; margin: 6mm 0 2mm; } p { margin: 0; }
.ref { font-size: 11pt; margin-bottom: 6mm; }
.slip { border-top: 2px dashed #2B0D3E; margin-top: 10mm; padding-top: 4mm; } .slip ul { list-style: none; padding: 0; } .slip li { margin: 2mm 0; }
"""


def render_letter(facts: Facts, sections: list[dict]) -> str:
    d = facts.as_of
    when = f"{d.day} {d.strftime('%B %Y')}"
    body = []
    for s in sections:
        if s["id"] == "ask":
            ticks = "".join(f"<li>&#9633; {escape(o)}</li>" for o in SLIP_OPTIONS)
            body.append(f'<section class="slip"><h2>{escape(s["title"])}</h2><p>{escape(s["text"])}</p>'
                        f'<ul>{ticks}</ul><p>Write your question here: ______________________________</p></section>')
        else:
            body.append(f'<section><h2>{escape(s["title"])}</h2><p>{escape(s["text"])}</p></section>')
    return (f'<!doctype html>\n<html lang="en-GB"><head><meta charset="utf-8">'
            f'<title>Your monthly letter, {d.strftime("%B %Y")}</title><style>{CSS}</style></head><body>\n'
            f'<h1>Dear {escape(facts.customer.name)}</h1>\n'
            f'<p class="ref">Your letter for {when}. Your reference: {escape(facts.customer.reference)}</p>\n'
            + "\n".join(body) + "\n</body></html>\n")
