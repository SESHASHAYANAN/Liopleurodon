import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client
db = create_client(
    os.environ.get("SUPABASE_URL", "https://ayovlmoyyckxtftbnxmg.supabase.co"),
    os.environ.get("SUPABASE_SERVICE_KEY", "")
)
r = db.table('jobs').select('id', count='exact').eq('is_active', True).execute()
print(f'Total active jobs: {r.count}')

r2 = db.table('jobs').select('title, company_name, source_platforms, apply_url').eq('is_active', True).order('created_at', desc=True).limit(10).execute()
print('\nNewest 10 jobs (verified links):')
for j in r2.data:
    t = j['title'][:50]
    c = j['company_name'][:30]
    s = j['source_platforms']
    print(f'  - {t} @ {c} | {s}')

# Check no IndiaAI-Curated remain
r3 = db.table('jobs').select('id', count='exact').contains('source_platforms', ['IndiaAI-Curated']).execute()
print(f'\nIndiaAI-Curated jobs remaining: {r3.count}')
