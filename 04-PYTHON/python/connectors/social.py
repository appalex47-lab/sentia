"""Read-only OAuth connectors for X, TikTok, YouTube and LinkedIn."""
from __future__ import annotations
import base64, hashlib, json, os, secrets, urllib.parse, urllib.request
from dataclasses import dataclass

class SocialConnectorError(RuntimeError):
    def __init__(self, code, message=""):
        self.code=code; super().__init__(message or code)

def _request(url, method="GET", headers=None, data=None, timeout=30):
    req=urllib.request.Request(url, method=method, headers=headers or {})
    if data is not None:
        req.data=json.dumps(data).encode() if isinstance(data,(dict,list)) else data
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw=r.read().decode('utf-8')
            return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw=e.read().decode('utf-8', errors='replace')
        try: body=json.loads(raw)
        except Exception: body={"raw":raw}
        raise SocialConnectorError(f"HTTP_{e.code}", json.dumps(body, ensure_ascii=False))
    except urllib.error.URLError as e:
        raise SocialConnectorError("NETWORK_ERROR", str(e))

def _form(url, data, auth=None):
    body=urllib.parse.urlencode(data).encode()
    headers={"Content-Type":"application/x-www-form-urlencoded","Accept":"application/json"}
    if auth: headers["Authorization"]="Basic "+base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    return _request(url,"POST",headers,body)

@dataclass
class XConnector:
    client_id:str; redirect_uri:str; scopes:str
    auth_url:str="https://x.com/i/oauth2/authorize"
    token_url:str="https://api.x.com/2/oauth2/token"
    api_url:str="https://api.x.com/2"
    def authorization(self,state,verifier):
        challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
        q={"response_type":"code","client_id":self.client_id,"redirect_uri":self.redirect_uri,"scope":self.scopes or "tweet.read users.read offline.access","state":state,"code_challenge":challenge,"code_challenge_method":"S256"}
        return self.auth_url+"?"+urllib.parse.urlencode(q)
    def exchange(self,code,verifier,client_secret=""):
        data={"code":code,"grant_type":"authorization_code","redirect_uri":self.redirect_uri,"code_verifier":verifier,"client_id":self.client_id}
        if client_secret: return _form(self.token_url,data,(self.client_id,client_secret))[1]
        return _form(self.token_url,data)[1]
    def refresh(self,refresh_token,client_secret=""):
        data={"refresh_token":refresh_token,"grant_type":"refresh_token","client_id":self.client_id}
        if client_secret: return _form(self.token_url,data,(self.client_id,client_secret))[1]
        return _form(self.token_url,data)[1]
    def me(self,token): return _request(self.api_url+"/users/me?user.fields=id,name,username",headers={"Authorization":"Bearer "+token})[1]
    def recent(self,token,query,max_results=100):
        q={"query":query,"max_results":max(10,min(100,int(max_results))),"tweet.fields":"id,text,created_at,author_id,lang,public_metrics","expansions":"author_id","user.fields":"id,name,username"}
        return _request(self.api_url+"/tweets/search/recent?"+urllib.parse.urlencode(q),headers={"Authorization":"Bearer "+token})[1]

@dataclass
class TikTokConnector:
    client_key:str; redirect_uri:str; scopes:str
    def authorization(self,state):
        q={"client_key":self.client_key,"response_type":"code","scope":self.scopes or "user.info.basic,video.list","redirect_uri":self.redirect_uri,"state":state}
        return "https://www.tiktok.com/v2/auth/authorize/?"+urllib.parse.urlencode(q)
    def exchange(self,code,client_secret):
        return _form("https://open.tiktokapis.com/v2/oauth/token/",{"client_key":self.client_key,"client_secret":client_secret,"code":code,"grant_type":"authorization_code","redirect_uri":self.redirect_uri})[1]
    def refresh(self,refresh_token,client_secret):
        return _form("https://open.tiktokapis.com/v2/oauth/token/",{"client_key":self.client_key,"client_secret":client_secret,"grant_type":"refresh_token","refresh_token":refresh_token})[1]
    def profile(self,token): return _request("https://open.tiktokapis.com/v2/user/info/?fields=open_id,display_name,username,profile_deep_link",headers={"Authorization":"Bearer "+token})[1]
    def videos(self,token,max_count=20):
        fields="id,title,video_description,duration,create_time,share_url,embed_link"
        return _request("https://open.tiktokapis.com/v2/video/list/?fields="+urllib.parse.quote(fields),"POST",{"Authorization":"Bearer "+token,"Content-Type":"application/json"},{"max_count":max(1,min(20,int(max_count)))})[1]

@dataclass
class YouTubeConnector:
    client_id:str; redirect_uri:str; scopes:str
    def authorization(self,state):
        q={"client_id":self.client_id,"redirect_uri":self.redirect_uri,"response_type":"code","access_type":"offline","prompt":"consent","scope":self.scopes or "https://www.googleapis.com/auth/youtube.readonly","state":state}
        return "https://accounts.google.com/o/oauth2/v2/auth?"+urllib.parse.urlencode(q)
    def exchange(self,code,client_secret):
        return _form("https://oauth2.googleapis.com/token",{"code":code,"client_id":self.client_id,"client_secret":client_secret,"redirect_uri":self.redirect_uri,"grant_type":"authorization_code"})[1]
    def refresh(self,refresh_token,client_secret):
        return _form("https://oauth2.googleapis.com/token",{"refresh_token":refresh_token,"client_id":self.client_id,"client_secret":client_secret,"grant_type":"refresh_token"})[1]
    def _get(self,token,path,params):
        q=dict(params); q["access_token"]=token
        return _request("https://www.googleapis.com/youtube/v3/"+path+"?"+urllib.parse.urlencode(q))[1]
    def channel(self,token,channel_id): return self._get(token,"channels",{"part":"snippet,contentDetails,statistics","id":channel_id})
    def videos(self,token,channel_id,limit=20,api_key=""):
        channels=self._get(token,"channels",{"part":"contentDetails","id":channel_id}) if token else _request("https://www.googleapis.com/youtube/v3/channels?"+urllib.parse.urlencode({"part":"contentDetails","id":channel_id,"key":api_key}))[1]
        items=channels.get("items",[])
        if not items: return {"items":[]}
        uploads=items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
        params={"part":"snippet","playlistId":uploads,"maxResults":min(50,int(limit))}
        if api_key: params["key"]=api_key
        elif token: params["access_token"]=token
        return _request("https://www.googleapis.com/youtube/v3/playlistItems?"+urllib.parse.urlencode(params))[1]
    def comments(self,token,video_id,limit=100,api_key=""):
        p={"part":"snippet","videoId":video_id,"maxResults":min(100,int(limit)),"textFormat":"plainText"}
        if api_key:p["key"]=api_key
        elif token:p["access_token"]=token
        return _request("https://www.googleapis.com/youtube/v3/commentThreads?"+urllib.parse.urlencode(p))[1]

@dataclass
class LinkedInConnector:
    client_id:str; redirect_uri:str; scopes:str; version:str="202609"
    def authorization(self,state):
        q={"response_type":"code","client_id":self.client_id,"redirect_uri":self.redirect_uri,"state":state,"scope":self.scopes or "openid profile email r_organization_social"}
        return "https://www.linkedin.com/oauth/v2/authorization?"+urllib.parse.urlencode(q)
    def exchange(self,code,client_secret):
        return _form("https://www.linkedin.com/oauth/v2/accessToken",{"grant_type":"authorization_code","code":code,"redirect_uri":self.redirect_uri,"client_id":self.client_id,"client_secret":client_secret})[1]
    def refresh(self,refresh_token,client_secret):
        return _form("https://www.linkedin.com/oauth/v2/accessToken",{"grant_type":"refresh_token","refresh_token":refresh_token,"client_id":self.client_id,"client_secret":client_secret})[1]
    def posts(self,token,organization_id,count=100):
        author="urn:li:organization:"+str(organization_id)
        q={"q":"author","author":author,"count":min(100,int(count))}
        return _request("https://api.linkedin.com/rest/posts?"+urllib.parse.urlencode(q),headers={"Authorization":"Bearer "+token,"LinkedIn-Version":self.version,"X-Restli-Protocol-Version":"2.0.0"})[1]
    def comments(self,token,urn,count=100):
        q={"count":min(100,int(count))}
        return _request("https://api.linkedin.com/rest/socialActions/"+urllib.parse.quote(urn,safe="")+"/comments?"+urllib.parse.urlencode(q),headers={"Authorization":"Bearer "+token,"LinkedIn-Version":self.version,"X-Restli-Protocol-Version":"2.0.0"})[1]

def public_config(path, values):
    path.parent.mkdir(parents=True,exist_ok=True)
    safe={k:str(values.get(k,"" )).strip() for k in values if k not in {"clientSecret","apiKey","accessToken","refreshToken"}}
    path.write_text(json.dumps(safe,ensure_ascii=False,indent=2),encoding="utf-8")
    try: os.chmod(path,0o600)
    except OSError: pass
    return safe
