"""Run from repo root: be/.venv/bin/python -m be.scripts.check_space."""
from be.space import client

if __name__ == '__main__':
    api = client().view_api(return_format='dict',print_info=False)
    endpoints = api.get('named_endpoints',{})
    assert '/embed' in endpoints, 'Space must expose /embed'
    parameters = endpoints['/embed'].get('parameters',[])
    print('Space contract:', {'endpoint':'/embed','inputs':[p.get('parameter_name') for p in parameters]})
    assert len(parameters)==2, 'Expected photo and selected inputs'
    status = client().predict(api_name='/health')
    print('Encoder ready:',status.get('encoder_ready'),'; Reference ready:',status.get('reference_ready'))
