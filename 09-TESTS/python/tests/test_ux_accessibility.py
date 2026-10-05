from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = (ROOT / 'index.html').read_text(encoding='utf-8')
CSS = (ROOT / 'css' / 'styles.css').read_text(encoding='utf-8')
APP = (ROOT / 'js' / 'app.js').read_text(encoding='utf-8')


def test_navigation_has_current_state_and_real_buttons():
    assert '<nav aria-label="Secciones de Sentia">' in INDEX
    assert INDEX.count('class="nav-item') >= 8
    assert 'aria-current="page"' in INDEX
    assert 'aria-current="false"' in INDEX
    assert 'type="button"' in INDEX


def test_local_bridge_is_allowed_by_csp_without_wildcard_connect_src():
    assert "connect-src 'self' http://127.0.0.1:8787 http://localhost:8787;" in INDEX
    assert "connect-src *" not in INDEX


def test_keyboard_navigation_and_modal_focus_support_are_present():
    assert 'document.querySelector("main")?.focus({preventScroll:true})' in APP
    assert 'event.key==="Escape"' in APP
    assert 'event.key!=="Tab"' in APP
    assert 'modal.querySelector("#connection-close").focus()' in APP


def test_reduced_motion_and_visible_focus_styles_exist():
    assert 'prefers-reduced-motion: reduce' in CSS
    assert 'button:focus-visible' in CSS
    assert '.nav-item:focus-visible' in CSS
    assert '.skip-link:focus' in CSS


def test_mobile_navigation_and_filters_have_responsive_rules():
    assert '@media(max-width:760px)' in CSS
    assert '.sidebar nav{grid-template-columns:repeat(2,minmax(0,1fr))}' in CSS
    assert '.filters{display:grid;grid-template-columns:1fr}' in CSS
