from mysql.connector.aio import connect
import config

async def select_contact(contact_id):
    async with await connect(host=config.HOST, user=config.USER, password=config.PASSWORD, database=config.DB) as db_connector:
        async with await db_connector.cursor() as db_cursor:
            await db_cursor.execute("SELECT name, phone FROM contacts WHERE id = %s LIMIT 1",
                (
                    contact_id,
                )
            )
            contact = await db_cursor.fetchone()
            return contact