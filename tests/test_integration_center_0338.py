from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HTML=(ROOT/'01-HTML/index.html').read_text(); JS=(ROOT/'03-JAVASCRIPT/js/app.js').read_text(); CSS=(ROOT/'02-CSS/css/styles.css').read_text()
EXPECTED=['Meta / Facebook Pages','Instagram','X','TikTok','YouTube','LinkedIn','Google Analytics 4','Cohere','Conector personalizado']
def test_all_integrations_are_catalogued():
    assert all(x in JS for x in EXPECTED)
def test_configuration_has_connection_hub():
    assert 'connection-hub' in HTML and 'open-integrations-center' in HTML
def test_filters_exist():
    assert all(f'data-integration-filter="{x}"' in HTML for x in ['all','Social','Analytics','IA','REST / JSON'])
def test_secrets_not_rendered_as_browser_inputs():
    assert 'type="password"' not in JS and 'secret-box' in JS and 'secrets' in JS
def test_public_config_is_stored_via_integration_store():
    assert 'DB.saveIntegration' in JS and 'values:vals' in JS
def test_responsive_hub_exists():
    assert '@media(max-width:700px)' in CSS
