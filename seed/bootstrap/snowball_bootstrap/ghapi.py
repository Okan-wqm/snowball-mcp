"""Minimal GitHub REST calls the pull job needs: find and download the latest state artifact, and look at the
newest failed run of this workflow (E13). The job holds `actions: read` and nothing else.

The fence workflow (E532) adds: the copy's open pull requests into `brain/integration`, read with the job's own token
(the copy is public), and, in the gate's posting job alone, the gate App's installation token and its
``snowball-fence`` check runs (Checks write, on the copy only)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


def _api_base() -> str:
    return os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")


def _request(url: str, token: str, accept: str = "application/vnd.github+json") -> urllib.request.Request:
    return urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "snowball-bootstrap",
    })


def latest_artifact(repo: str, name: str, token: str, branch: str = "main") -> dict | None:
    """Newest non-expired artifact with this exact name made by a run on `branch`, or None (E17)."""
    query = urllib.parse.urlencode({"name": name, "per_page": 50})
    with urllib.request.urlopen(_request(f"{_api_base()}/repos/{repo}/actions/artifacts?{query}", token),
                                timeout=60) as resp:
        data = json.load(resp)
    candidates = [a for a in data.get("artifacts", []) if a.get("name") == name and not a.get("expired")
                  and (a.get("workflow_run") or {}).get("head_branch") == branch]
    candidates.sort(key=lambda a: a.get("created_at", ""), reverse=True)
    return candidates[0] if candidates else None


def _get_json(path: str, query: dict, token: str) -> dict:
    url = f"{_api_base()}/repos/{path}?{urllib.parse.urlencode(query)}"
    with urllib.request.urlopen(_request(url, token), timeout=60) as resp:
        data = json.load(resp)
    return data if isinstance(data, dict) else {}


def latest_failed_run(repo: str, token: str, workflow: str = "bootstrap.yml", branch: str = "main") -> dict | None:
    """The newest run of this workflow on `branch` that ended in failure, or None."""
    data = _get_json(f"{repo}/actions/workflows/{workflow}/runs", {"branch": branch, "status": "failure",
                                                                    "per_page": 1}, token)
    runs = [r for r in data.get("workflow_runs", []) if isinstance(r, dict)]
    return runs[0] if runs else None


def run_jobs(repo: str, run_id: int, token: str) -> dict[str, str | None]:
    """Each job of a run by name, with its conclusion."""
    data = _get_json(f"{repo}/actions/runs/{int(run_id)}/jobs", {"per_page": 50}, token)
    return {j.get("name"): j.get("conclusion") for j in data.get("jobs", []) if isinstance(j, dict)}


def run_artifact(repo: str, run_id: int, name: str, token: str) -> dict | None:
    """A run's unexpired artifact of this exact name, or None."""
    data = _get_json(f"{repo}/actions/runs/{int(run_id)}/artifacts", {"name": name, "per_page": 10}, token)
    found = [a for a in data.get("artifacts", []) if isinstance(a, dict) and a.get("name") == name
             and not a.get("expired")]
    return found[0] if found else None


def download_zip(repo: str, artifact_id: int, token: str) -> bytes:
    """Download an artifact; the token is sent to GitHub only, never to the storage redirect."""
    opener = urllib.request.build_opener(_NoRedirect())
    url = f"{_api_base()}/repos/{repo}/actions/artifacts/{int(artifact_id)}/zip"
    try:
        with opener.open(_request(url, token), timeout=60) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code not in (301, 302, 303, 307, 308):
            raise
        location = exc.headers.get("Location")
        if not location or not location.startswith("https://"):
            raise
    with urllib.request.urlopen(urllib.request.Request(location, headers={"User-Agent": "snowball-bootstrap"}),
                                timeout=120) as resp:
        return resp.read()


def _call(method: str, url: str, token: str, body: dict | None = None, scheme: str = "Bearer") -> object:
    """One JSON request to GitHub; the parsed answer (None for an empty one)."""
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"{scheme} {token}", "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "snowball-bootstrap",
        **({"Content-Type": "application/json"} if data is not None else {})})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    return json.loads(raw) if raw.strip() else None


MAX_PULLS = 100  # one page: a head beyond it gets no check this run, and no check is no merge


def open_pulls(repo: str, base: str, token: str) -> list[dict]:
    """The open pull requests of ``repo`` into ``base``, oldest first: ``{number, head_sha}`` each."""
    query = urllib.parse.urlencode({"state": "open", "base": base, "per_page": MAX_PULLS, "sort": "created",
                                    "direction": "asc"})
    data = _call("GET", f"{_api_base()}/repos/{repo}/pulls?{query}", token)
    out = []
    for pull in data if isinstance(data, list) else []:
        head = pull.get("head") if isinstance(pull, dict) else None
        if isinstance(pull.get("number"), int) and isinstance(head, dict) and isinstance(head.get("sha"), str):
            out.append({"number": pull["number"], "head_sha": head["sha"]})
    return out


def installation_token(repo: str, app_jwt: str, permissions: dict[str, str]) -> str:
    """An installation token of the App whose JWT this is, for ``repo`` alone and ``permissions`` alone."""
    found = _call("GET", f"{_api_base()}/repos/{repo}/installation", app_jwt)
    if not isinstance(found, dict) or not isinstance(found.get("id"), int):
        raise ValueError(f"the gate App is not installed on {repo}")
    made = _call("POST", f"{_api_base()}/app/installations/{found['id']}/access_tokens", app_jwt,
                 {"repositories": [repo.split("/", 1)[1]], "permissions": permissions})
    if not isinstance(made, dict) or not isinstance(made.get("token"), str):
        raise ValueError("GitHub gave no installation token")
    return made["token"]


def latest_check(repo: str, sha: str, name: str, app_id: int, token: str) -> dict | None:
    """The newest check run named ``name`` that the App ``app_id`` posted on ``sha``, or None."""
    query = urllib.parse.urlencode({"check_name": name, "app_id": app_id, "filter": "latest", "per_page": 1})
    data = _call("GET", f"{_api_base()}/repos/{repo}/commits/{sha}/check-runs?{query}", token)
    runs = data.get("check_runs") if isinstance(data, dict) else None
    found = [r for r in runs if isinstance(r, dict)] if isinstance(runs, list) else []
    return found[0] if found else None


def post_check(repo: str, sha: str, name: str, conclusion: str, title: str, summary: str, token: str) -> None:
    """A completed check run on ``sha``."""
    _call("POST", f"{_api_base()}/repos/{repo}/check-runs", token,
          {"name": name, "head_sha": sha, "status": "completed", "conclusion": conclusion,
           "output": {"title": title, "summary": summary}})
