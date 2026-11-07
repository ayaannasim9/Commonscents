from .models import Persona, Preferences, TrustedPerson

MARGARET = Persona(
    id="MRG-4471",
    name="Margaret",
    age=81,
    bank="NatWest",  # plan 0.8: CLAUDE.md says Lloyds, changed by decision
    hub_day="Tuesday",
    trusted_person=TrustedPerson(name="Sarah", relation="daughter", level="alerts_only"),
    preferences=Preferences(large_print=True, language="en"),
)

# Demo "current month" (plan 0.11): letter dated 1 Dec 2026, last full month November 2026.
DEMO_END = (2026, 11)
