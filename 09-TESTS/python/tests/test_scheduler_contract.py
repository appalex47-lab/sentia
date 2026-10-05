from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def test_scheduler_is_indexeddb_persistent_and_not_localstorage():
    db=(ROOT/"js/db.js").read_text()
    app=(ROOT/"js/app.js").read_text()
    assert 'sync_scheduler' in db
    assert 'saveSyncScheduler' in app
    assert 'sentia-auto-sync' not in app

def test_scheduler_has_configurable_intervals():
    html=(ROOT/"index.html").read_text()
    for value in ("15","30","60","180","360"):
        assert f'value="{value}"' in html

def test_scheduler_disclaims_background_service():
    html=(ROOT/"index.html").read_text()
    assert 'mientras la app esté abierta' in html
