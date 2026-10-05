import os
from python.connectors.social import XConnector, TikTokConnector, YouTubeConnector, LinkedInConnector, public_config


def test_x_pkce_authorization_has_state_and_challenge():
    c=XConnector('client','http://127.0.0.1/callback','tweet.read users.read offline.access')
    url=c.authorization('state123','verifier123')
    assert 'code_challenge=' in url and 'code_challenge_method=S256' in url and 'state=state123' in url


def test_social_public_config_excludes_secrets(tmp_path):
    p=tmp_path/'x.json'
    cfg=public_config(p, {'clientId':'abc','clientSecret':'SECRET','accessToken':'TOKEN','query':'marca lang:es'})
    raw=p.read_text()
    assert cfg['clientId']=='abc' and cfg['query']=='marca lang:es'
    assert 'SECRET' not in raw and 'TOKEN' not in raw


def test_tiktok_authorization_uses_display_scopes():
    c=TikTokConnector('key','http://127.0.0.1/callback','user.info.basic,video.list')
    assert 'video.list' in c.authorization('s') and 'client_key=key' in c.authorization('s')


def test_youtube_authorization_is_read_only():
    c=YouTubeConnector('client','http://127.0.0.1/callback','https://www.googleapis.com/auth/youtube.readonly')
    assert 'youtube.readonly' in c.authorization('s') and 'access_type=offline' in c.authorization('s')


def test_linkedin_versioned_headers_are_configurable():
    c=LinkedInConnector('client','http://127.0.0.1/callback','r_organization_social','202609')
    assert c.version == '202609'


def test_youtube_comments_normalization_shape():
    from python.connection_server import social_to_mentions
    payload={'comments':[{'id':'c1','snippet':{'topLevelComment':{'snippet':{'textDisplay':'Muy buena atención','publishedAt':'2026-10-01T00:00:00Z'}}}}]}
    rows=social_to_mentions('youtube',payload)
    assert rows[0]['fuente']=='youtube' and rows[0]['texto_original']=='Muy buena atención'


def test_tiktok_video_text_normalization_shape():
    from python.connection_server import social_to_mentions
    payload={'data':{'videos':[{'id':'v1','title':'Mi experiencia','video_description':'Excelente servicio','create_time':1760000000}]}}
    rows=social_to_mentions('tiktok',payload)
    assert 'Excelente servicio' in rows[0]['texto_original'] and rows[0]['fuente']=='tiktok'


def test_linkedin_post_and_comment_normalization():
    from python.connection_server import social_to_mentions
    payload={'posts':{'elements':[{'id':'urn:li:share:1','commentary':'Publicación de la empresa'}]},'comments':[{'message':{'text':'Tengo una duda'}}]}
    rows=social_to_mentions('linkedin',payload)
    assert {r['fuente'] for r in rows} == {'linkedin'} and len(rows)==2


def test_linkedin_ids_are_deterministic_for_deduplication():
    from python.connection_server import social_to_mentions
    payload={'posts':{'elements':[{'id':'urn:li:share:1','commentary':'Publicación de la empresa'}]},'comments':[{'id':'comment-1','message':{'text':'Tengo una duda'}}]}
    first=social_to_mentions('linkedin',payload)
    second=social_to_mentions('linkedin',payload)
    assert [x['id_mencion'] for x in first] == [x['id_mencion'] for x in second]
