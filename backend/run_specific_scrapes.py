import asyncio
from services.scheduler import scrape_all_sources
from database import get_supabase_admin

async def main():
    queries = [
        ("Google software engineer", "United States"),
        ("Meta frontend engineer", "Remote"),
        ("Stripe backend engineer", "United States"),
        ("Airbnb full stack", "Remote"),
        ("stealth startup engineer", "San Francisco"),
        ("undisclosed startup software engineer", "Remote"),
        ("visa sponsorship software engineer", "India")
    ]
    
    for q, loc in queries:
        print(f"Scraping for query: '{q}', location: '{loc}'")
        await scrape_all_sources(query=q, location=loc)
        print(f"Finished scraping for {q} - {loc}")

    # After scraping, run the backfill logic again
    import backfill_tags
    await backfill_tags.backfill_tags()

if __name__ == "__main__":
    asyncio.run(main())
