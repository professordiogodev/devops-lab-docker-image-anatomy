#!/usr/bin/env python3
import io, json, os, re, subprocess, sys, tarfile, tempfile, time, urllib.request
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
passed = failed = 0


def check(desc, ok, hint=""):
    global passed, failed
    if ok:
        passed += 1; print("PASS  " + desc, flush=True)
    else:
        failed += 1; print("FAIL  " + desc + (("   -> " + hint) if hint else ""), flush=True)


def sh(*a, timeout=900):
    r = subprocess.run(a, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def finish():
    print()
    print(("ALL CHECKS PASSED (%d/%d)" % (passed, passed)) if failed == 0 else ("%d check(s) failed, %d passed" % (failed, passed)))
    sys.exit(1 if failed else 0)


def size_bytes(s):
    m = re.match(r"([\d.]+)\s*([kMG]?B)", s.strip())
    if not m:
        return 0
    return float(m.group(1)) * {"B": 1, "kB": 1e3, "MB": 1e6, "GB": 1e9}[m.group(2)]


def layer_contains(image, needle):
    """True if the bytes appear in any file of any layer."""
    with tempfile.TemporaryDirectory() as d:
        tarp = os.path.join(d, "img.tar")
        subprocess.run(["docker", "save", image, "-o", tarp], check=True)
        with tarfile.open(tarp) as outer:
            for m in outer.getmembers():
                if not m.isfile():
                    continue
                f = outer.extractfile(m)
                data = f.read()
                if needle in data:
                    return True
                if data[:2] == b"\x1f\x8b" or data[:5] == b"ustar" or m.name.endswith(".tar") or "blobs/" in m.name:
                    try:
                        with tarfile.open(fileobj=io.BytesIO(data)) as inner:
                            for im in inner.getmembers():
                                if im.isfile() and im.size < 5_000_000:
                                    if needle in inner.extractfile(im).read():
                                        return True
                    except Exception:
                        pass
    return False


truth = json.load(open(".lab/.truth.json"))
token = truth["token"].encode()
print("== Your findings about the legacy image ==")
try:
    f = json.load(open("findings.json"))
except Exception as e:
    check("findings.json is valid JSON", False, str(e)); finish()
insp = json.loads(sh("docker", "image", "inspect", "legacy-pollie:1")[1])[0]
check("base_image is python:3.12 (the full, non-slim image)", f.get("base_image", "").strip() in ("python:3.12", "python:3.12 ") or re.fullmatch(r"python:3\.12(\.\d+)?", f.get("base_image", "").strip()) is not None)
check("secret_value is the token that is STILL inside the image", f.get("secret_value", "").strip() == truth["token"], "docker save legacy-pollie:1 | tar -x, then look in the layers")
check("secret_layer_instruction names the COPY of registry.env", "registry.env" in f.get("secret_layer_instruction", "").lower())
hist = sh("docker", "history", "--no-trunc", "--format", "{{.Size}}|{{.CreatedBy}}", "legacy-pollie:1")[1].strip().split("\n")
rows = [(size_bytes(l.split("|", 1)[0]), l.split("|", 1)[1]) for l in hist if "|" in l]
big = max(rows)[1].lower()
kw = "apt-get" if "apt-get" in big else ("pip install" if "pip install" in big else "copy")
check("largest_layer_instruction names the instruction of the largest layer", kw in f.get("largest_layer_instruction", "").lower(), "docker history shows sizes")
check("layer_count equals the number of filesystem layers of the image", f.get("layer_count") == len(insp["RootFS"]["Layers"]), "docker image inspect")
check("runs_as is root", str(f.get("runs_as", "")).strip().lower() in ("root", "0", "uid 0"))
real = insp["Size"] / 1e6
listed = size_bytes(sh("docker", "image", "ls", "legacy-pollie:1", "--format", "{{.Size}}")[1]) / 1e6
check("image_size_mb is within 15%% of the size docker reports (%.0f MB on disk by `docker images`, %.0f MB by `docker image inspect`)" % (listed, real), isinstance(f.get("image_size_mb"), (int, float)) and any(abs(f["image_size_mb"] - v) <= v * 0.15 for v in (real, listed)))
check("the secret really is inside the legacy image (your proof it was not deleted)", layer_contains("legacy-pollie:1", token))

print("== Your rebuilt image ==")
di = open(".dockerignore").read() if os.path.exists(".dockerignore") else ""
check(".dockerignore keeps .git and secrets/ out of the build context", ".git" in di and "secrets" in di)
rc, out, err = sh("docker", "build", "-q", "-f", "Dockerfile.fixed", "-t", "pollie-fixed:1", ".")
check("Dockerfile.fixed builds", rc == 0, err[-200:])
if rc != 0:
    finish()
fi = json.loads(sh("docker", "image", "inspect", "pollie-fixed:1")[1])[0]
mb = fi["Size"] / 1e6
check("the image is under 250 MB (it is %.0f MB; the legacy one is %.0f MB)" % (mb, real), mb < 250)
cfg = fi["Config"]
check("it runs as a non-root numeric user", re.fullmatch(r"[1-9]\d*(:\d+)?", cfg.get("User", "") or "") is not None, "USER 10001")
check("it has a HEALTHCHECK", bool(cfg.get("Healthcheck")))
check("the CMD starts uvicorn for pollie.api.main:app", "uvicorn" in " ".join(cfg.get("Cmd") or []) and "pollie.api.main:app" in " ".join(cfg.get("Cmd") or []))
check("the token is in NO layer, no env and no history of the fixed image", not layer_contains("pollie-fixed:1", token) and token.decode() not in json.dumps(fi) and token.decode() not in sh("docker", "history", "--no-trunc", "pollie-fixed:1")[1])
def inside(cmd):
    return sh("docker", "run", "--rm", "--entrypoint", "sh", "pollie-fixed:1", "-c", cmd)
check("no compiler or git in the final image", inside("command -v gcc || command -v git || command -v make")[0] != 0)
check("no tests, docs or dev tools in the final image", inside("test -d /app/tests || test -d /app/docs || python -m pip show pytest ruff 2>/dev/null | grep -q Name")[0] != 0)
rc, out, err = sh("docker", "run", "--rm", "-e", "DATABASE_URL=postgresql://pollie:x@127.0.0.1:5432/pollie", "-e", "REDIS_URL=redis://127.0.0.1:6379", "--entrypoint", "python", "pollie-fixed:1", "-c",
                  "import pollie.api.main as m, pollie.worker; assert m.app is not None; print('APP_OK', m.app.title)")
check("the application imports and builds inside the image (Pollie insists on DATABASE_URL and REDIS_URL, so the check passes dummy ones)", rc == 0 and "APP_OK" in out, err[-300:])
rc, out, err = sh("docker", "run", "--rm", "--entrypoint", "id", "pollie-fixed:1", "-u")
check("the process really runs as a non-root user inside the container (uid %s)" % out.strip(), rc == 0 and out.strip() not in ("0", ""))
finish()
