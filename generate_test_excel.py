from config.db import db_pool
from routes.excel import generate_excel
import os
import asyncio

async def main():
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, incident_folio FROM incident LIMIT 5")
            rows = cur.fetchall()
            if rows:
                inc_id = rows[0]['id']
                print(f"Generating excel for incident id {inc_id}...")
                res = generate_excel(inc_id)
                body = b""
                if hasattr(res, "body_iterator"):
                    if hasattr(res.body_iterator, "__aiter__"):
                        async for chunk in res.body_iterator:
                            body += chunk
                    else:
                        for chunk in res.body_iterator:
                            body += chunk
                else:
                    body = res.body
                
                with open("test_output.xlsx", "wb") as f:
                    f.write(body)
                print("Successfully saved to test_output.xlsx!")
            else:
                print("No incidents found in DB.")

if __name__ == "__main__":
    asyncio.run(main())
