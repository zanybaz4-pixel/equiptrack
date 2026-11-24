"""Check actual Render nginx limits in disposable Docker networks (WSL Engine)."""
import json
from pathlib import Path
import subprocess
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def main():
    prefix = "equiptrack-limit-check-" + uuid4().hex[:8]
    networks, containers = [], []

    def docker(*args, check=True):
        return subprocess.run(["wsl", "-d", "Ubuntu-24.04", "--", "env", "DOCKER_HOST=unix:///var/run/docker.sock", "docker", *args], capture_output=True, text=True, check=check)

    def probe(network, address, headers, count=1):
        code = f"""import json, urllib.request, urllib.error
results=[]
for i in range({count}):
    r=urllib.request.Request('http://{address}:10000/api/auth/login',data=b'{{}}',headers={headers!r})
    try: response=urllib.request.urlopen(r,timeout=5)
    except urllib.error.HTTPError as error: response=error
    results.append(response.status)
print(json.dumps(results))
"""
        return json.loads(docker("run", "--rm", "--network", network, "--entrypoint", "python", "equiptrack-render:verification", "-c", code).stdout)

    try:
        for label, subnet in (("trusted", None), ("untrusted", "198.19.212.0/24")):
            name = prefix + "-" + label
            docker("network", "create", *(["--subnet", subnet] if subnet else []), name)
            networks.append(name)
        source = ROOT / "infra/render/nginx.conf.template"
        mount = "/mnt/" + source.drive[0].lower() + source.as_posix()[2:]
        server = """from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import subprocess
class Stub(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b'{}')
    def log_message(self,*args): pass
for part in ('client','proxy','fastcgi','uwsgi','scgi'): Path('/tmp/nginx',part).mkdir(parents=True,exist_ok=True)
Path('/tmp/check-nginx.conf').write_text(Path('/tmp/source-nginx.conf').read_text().replace(chr(36)+'{PORT}','10000'))
subprocess.run(['nginx','-t','-c','/tmp/check-nginx.conf'],check=True)
subprocess.Popen(['nginx','-c','/tmp/check-nginx.conf','-g','daemon off;'])
HTTPServer(('127.0.0.1',8000),Stub).serve_forever()
"""
        name = prefix + "-server"
        docker("run", "-d", "--name", name, "--network", networks[0], "--mount", f"type=bind,source={mount},target=/tmp/source-nginx.conf,readonly", "--entrypoint", "python", "equiptrack-render:verification", "-c", server)
        containers.append(name)
        docker("network", "connect", networks[1], name)
        info = json.loads(docker("inspect", name).stdout)[0]["NetworkSettings"]["Networks"]
        time.sleep(1)
        trusted_ip = info[networks[0]]["IPAddress"]
        assert trusted_ip, docker("logs", name, check=False).stderr
        # Keep burst/isolation/spoof probes in one process, before bucket refill.
        code = f"""import urllib.request,urllib.error,json
def request(path,headers):
    request=urllib.request.Request('http://{trusted_ip}:10000'+path,data=b'{{}}',headers=headers)
    try: response=urllib.request.urlopen(request,timeout=5)
    except urllib.error.HTTPError as error: response=error
    return response.status
result={{}}
for path,count in (('/api/auth/login',11),('/api/auth/forgot-password',8)):
    burst=[request(path,{{'CF-Connecting-IP':'203.0.113.10'}}) for i in range(count)]
    other=request(path,{{'CF-Connecting-IP':'203.0.113.11'}})
    spoof=request(path,{{'CF-Connecting-IP':'203.0.113.10','X-Forwarded-For':'203.0.113.99'}})
    result[path]={{'burst':burst,'other':other,'spoof':spoof}}
result['reset_shares_recovery_limit']=request('/api/auth/reset-password',{{'CF-Connecting-IP':'203.0.113.10'}})
print(json.dumps(result))
"""
        trusted = json.loads(docker("run", "--rm", "--network", networks[0], "--entrypoint", "python", "equiptrack-render:verification", "-c", code).stdout)
        for path in ("/api/auth/login", "/api/auth/forgot-password"):
            assert 200 in trusted[path]["burst"] and 429 in trusted[path]["burst"], "Repeated attempts must still be throttled"
            assert trusted[path]["other"] == 200, "A separate visitor must not inherit the first visitor's quota"
            assert trusted[path]["spoof"] == 429, "Spoofed XFF must not bypass a visitor's quota"
        assert trusted["reset_shares_recovery_limit"] == 429
        untrusted_ip = info[networks[1]]["IPAddress"]
        untrusted = probe(networks[1], untrusted_ip, {"CF-Connecting-IP": "203.0.113.20"}, 11)
        # Reuse the same client container's address so only its header changes.
        code = f"""import urllib.request,urllib.error,json
result=[]
for i in range(11):
    request=urllib.request.Request('http://{untrusted_ip}:10000/api/auth/login',data=b'{{}}',headers={{'CF-Connecting-IP':f'203.0.113.{{50+i}}'}})
    try: response=urllib.request.urlopen(request,timeout=5)
    except urllib.error.HTTPError as error: response=error
    result.append(response.status)
print(json.dumps(result))
"""
        changing = json.loads(docker("run", "--rm", "--network", networks[1], "--entrypoint", "python", "equiptrack-render:verification", "-c", code).stdout)
        assert 429 in untrusted and 429 in changing, "Untrusted direct clients must not choose their limiter identity"
        print(json.dumps({"login_visitor_isolation": True, "recovery_visitor_isolation": True, "burst_throttling": True, "spoofed_xff_ignored": True, "untrusted_cf_header_ignored": True, "reset_shares_recovery_limit": True}, indent=2))
    finally:
        for name in containers: docker("rm", "-f", name, check=False)
        for name in reversed(networks): docker("network", "rm", name, check=False)


if __name__ == "__main__":
    main()
