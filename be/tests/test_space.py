import json
import httpx
import pytest
from be import space


@pytest.mark.parametrize(('http_status','body','state','reason'),[
    (200,{'stage':'RUNNING'},'running','ready'),
    (200,{'stage':'SLEEPING'},'waking','starting'),
    (200,{'stage':'RUNTIME_ERROR'},'down','space_unavailable'),
    (401,{'error':'unauthorized'},'down','access_denied'),
    (403,{'error':'forbidden'},'down','access_denied'),
    (404,{'error':'not found'},'down','space_not_found_or_private'),
    (429,{'error':'rate limited'},'down','rate_limited'),
    (503,{'error':'unavailable'},'down','hf_http_error'),
])
def test_runtime_diagnostic_distinguishes_failures_without_leaking_token(monkeypatch,http_status,body,state,reason):
    token='hf_private_test_marker'
    monkeypatch.setattr(space.config,'TOKEN',token)
    def get(url,headers,timeout):
        assert headers['Authorization']=='Bearer '+token
        return httpx.Response(http_status,json=body)
    monkeypatch.setattr(space.httpx,'get',get)
    result=space.runtime_status()
    assert result['state']==state and result['reason']==reason
    assert result['hf_http_status']==http_status
    assert result['token_configured'] is True
    assert token not in json.dumps(result)


def test_runtime_network_timeout_is_separate_from_missing_access(monkeypatch):
    def timeout(*args,**kwargs):raise httpx.ReadTimeout('do not disclose raw exception text')
    monkeypatch.setattr(space.httpx,'get',timeout)
    result=space.runtime_status()
    assert result['state']=='down' and result['reason']=='network_timeout'
    assert 'do not disclose' not in json.dumps(result)


def test_runtime_reports_absent_token_without_sending_an_auth_header(monkeypatch):
    monkeypatch.setattr(space.config,'TOKEN',None)
    def get(url,headers,timeout):
        assert headers=={}
        return httpx.Response(401,json={'error':'unauthorized'})
    monkeypatch.setattr(space.httpx,'get',get)
    result=space.runtime_status()
    assert result['token_configured'] is False
    assert result['reason']=='access_denied'


def test_runtime_rejects_unexpected_json_shape(monkeypatch):
    monkeypatch.setattr(space.httpx,'get',lambda *args,**kwargs:httpx.Response(200,json=[]))
    result=space.runtime_status()
    assert result['state']=='down'
    assert result['reason']=='invalid_runtime_response'
