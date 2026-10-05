from python.connection_server import _origin_allowed


def test_origin_policy_allows_local_and_github_pages():
    assert _origin_allowed("http://localhost:8080")
    assert _origin_allowed("http://127.0.0.1:8787")
    assert _origin_allowed("https://example.github.io")


def test_origin_policy_rejects_untrusted_web_origin():
    assert not _origin_allowed("https://evil.example")
    assert not _origin_allowed("https://github.io")


def test_origin_policy_allows_non_browser_requests():
    assert _origin_allowed("")


def test_oauth_html_escapes_untrusted_provider_message():
    from python.connection_server import Handler
    import html
    assert html.escape('<script>alert(1)</script>', quote=True) == '&lt;script&gt;alert(1)&lt;/script&gt;'
