import asyncio
from database import get_supabase_admin
from services.vc_tagger import detect_company_type

def tag_visa_and_relocation(job: dict) -> dict:
    title = str(job.get("title", "")).lower()
    description = str(job.get("description", "")).lower()
    
    text = title + " " + description
    
    # Enhanced patterns for visa and relocation
    if any(p in text for p in ["visa sponsor", "sponsorship available", "sponsor visa", "h1b", "h-1b", "visa support"]):
        job["visa_sponsorship"] = True
        
    if any(p in text for p in ["relocation support", "relocation assistance", "relocation package", "offer relocation", "relocation provided", "willing to relocate"]):
        job["relocation_support"] = True
        
    return job

async def backfill_tags():
    db = get_supabase_admin()
    print("Fetching all jobs...")
    res = db.table("jobs").select("*").execute()
    jobs = res.data
    
    print(f"Found {len(jobs)} jobs. Updating tags...")
    
    updated_count = 0
    for job in jobs:
        needs_update = False
        updates = {}
        
        # 1. Visa and Relocation
        title = str(job.get("title", "")).lower()
        description = str(job.get("description", "")).lower()
        text = title + " " + description
        
        if not job.get("visa_sponsorship"):
            if any(p in text for p in ["visa sponsor", "sponsorship available", "sponsor visa", "h1b", "h-1b", "visa support"]):
                updates["visa_sponsorship"] = True
                needs_update = True
                
        if not job.get("relocation_support"):
            if any(p in text for p in ["relocation support", "relocation assistance", "relocation package", "offer relocation", "relocation provided"]):
                updates["relocation_support"] = True
                needs_update = True
                
        # 2. Company Type
        info = detect_company_type(job.get("company_name", ""))
        if info["company_type"] != "other" and job.get("company_type") != info["company_type"]:
            updates["company_type"] = info["company_type"]
            updates["is_stealth"] = info["is_stealth"]
            if info["vc_backer"]:
                updates["vc_backer"] = info["vc_backer"]
            needs_update = True
            
        if needs_update:
            db.table("jobs").update(updates).eq("id", job["id"]).execute()
            updated_count += 1
            
    print(f"Successfully backfilled tags for {updated_count} jobs.")

if __name__ == "__main__":
    asyncio.run(backfill_tags())
