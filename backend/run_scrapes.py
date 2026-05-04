import asyncio
from services.scheduler import scrape_all_sources
from database import get_supabase_admin

async def main():
    queries = [
        ("software engineer", "India"),
        ("software engineer visa sponsorship", ""),
        ("software engineer relocation support", ""),
        ("data scientist", "India"),
        ("full stack developer visa sponsorship", "Europe"),
        ("backend developer relocation", "United States"),
        ("frontend developer", "India")
    ]
    
    for q, loc in queries:
        print(f"Scraping for query: '{q}', location: '{loc}'")
        await scrape_all_sources(query=q, location=loc)
        print(f"Finished scraping for {q} - {loc}")

if __name__ == "__main__":
    asyncio.run(main())
