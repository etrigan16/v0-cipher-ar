"""Renderer unit tests (Phishing Simulator — Phase 2, PR 2).

Covers templates spec R4 + design D7: ``render(template_html, context)``
replaces ``{{nombre}}``/``{{empresa}}``/``{{link}}`` (and any other key in
context), HTML-escapes target values, and renders missing variables empty.

Selective run: ``pytest tests/test_phishing_render.py -q``
"""

from app.services.phishing.render import render


def test_render_substitutes_all_three_variables():
    """R4/All-vars: every variable is replaced with the target's value."""
    template = (
        "<p>Hola {{nombre}}, tu cuenta de {{empresa}}.</p>"
        '<p><a href="{{link}}">Verificar</a></p>'
    )
    out = render(
        template,
        {"nombre": "Ana", "empresa": "Banco Test", "link": "https://x.test/v"},
    )
    assert "Hola Ana" in out
    assert "tu cuenta de Banco Test" in out
    assert 'href="https://x.test/v"' in out
    assert "{{" not in out


def test_render_extra_context_key_is_substituted():
    """R4/Extra: a non-standard {{var}} present in context is also replaced."""
    out = render("<p>{{nombre}} pidio {{monto}}</p>", {"nombre": "Ana", "monto": "$50"})
    assert out == "<p>Ana pidio $50</p>"


def test_render_missing_variable_renders_empty():
    """R4/Missing: a variable the target lacks renders empty, no error."""
    out = render("<p>{{nombre}} @ {{empresa}}</p>", {"nombre": "Ana"})
    assert out == "<p>Ana @ </p>"


def test_render_escapes_html_in_values():
    """R4/Escape: target-supplied markup is escaped, never executed."""
    out = render("<p>{{nombre}}</p>", {"nombre": "<script>alert(1)</script>"})
    assert "<script>" not in out
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in out


def test_render_escapes_quotes_for_attribute_context():
    """R4/Escape: quotes in values are escaped for href attribute safety."""
    out = render('<a href="{{link}}">x</a>', {"link": 'https://x.test/" onclick="evil'})
    assert '" onclick="' not in out
    assert "&quot; onclick=&quot;" in out


def test_render_replaces_repeated_occurrences():
    """R4/Triangulate: the same variable appearing twice is replaced twice."""
    out = render("{{nombre}} y {{nombre}}", {"nombre": "Ana"})
    assert out == "Ana y Ana"


def test_render_missing_all_variables_returns_body_with_empty_placeholders():
    """R4/Missing-all: empty context renders a body without placeholders."""
    out = render("<p>{{nombre}} {{empresa}} {{link}}</p>", {})
    assert out == "<p>  </p>"
