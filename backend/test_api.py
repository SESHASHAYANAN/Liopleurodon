import httpx
r = httpx.get("http://127.0.0.1:8000/api/jobs?per_page=5")
d = r.json()
print(f"Total: {d['total']}, Jobs returned: {len(d['jobs'])}")
for j in d["jobs"][:5]:
    title = j["title"][:50]
    company = j["company_name"][:20]
    feat = j.get("is_featured", "?")
    _feat = j.get("_is_featured", "?")
    _new = j.get("_is_new", "?")
    src = j.get("source_platforms", [])
    print(f"  {title} @ {company} | featured={feat} | _featured={_feat} | _new={_new} | src={src}")
