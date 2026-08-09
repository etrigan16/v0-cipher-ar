"""Phishing template variable substitution (design D7).

Pure function: ``render(template_html, context)`` replaces ``{{var}}``
placeholders with per-target values using fixed ``str.replace`` (no template
engine dependency). Target-supplied values are ``html.escape``-d to prevent
HTML injection (spec R4); a variable missing from ``context`` renders empty
(design D7). The fixed variable set is ``nombre``/``empresa``/``link``
(spec R3); any other ``{{var}}`` present in ``context`` is also substituted.
"""

import html

# The fixed variable set every seed template carries (spec R3 / design D7).
TEMPLATE_VARIABLES = ("nombre", "empresa", "link")


def render(template_html: str, context: dict[str, str]) -> str:
    """Substitute ``{{var}}`` placeholders with escaped target values.

    Every key in ``context`` replaces its ``{{key}}`` placeholder (escaped);
    a standard variable missing from ``context`` renders empty. Unknown
    placeholders not present in ``context`` are left untouched (the template
    is trusted tenant HTML, so only known variables are consumed).
    """
    out = template_html
    for key, value in context.items():
        out = out.replace("{{" + key + "}}", html.escape(str(value)))
    for key in TEMPLATE_VARIABLES:
        if key not in context:
            out = out.replace("{{" + key + "}}", "")
    return out
