from mysql.connector.aio import connect
import config

async def create_db():
    async with await connect(host=config.HOST, user=config.USER, password=config.PASSWORD, database=config.DB) as db_connector:
        async with await db_connector.cursor() as db_cursor:
            await db_cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INT PRIMARY KEY,
                    name VARCHAR(255),
                    phone VARCHAR(20) NOT NULL
                );
                '''
            )

            await db_cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS requests (
                    request_id INT PRIMARY KEY,
                    contact_id INT NOT NULL,
                    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
                );
                '''
            )

            await db_cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    direct ENUM('designer', 'manager') NOT NULL,
                    message VARCHAR(255),
                    contact_id INT NOT NULL,
                    pil_id INT NULL,
                    FOREIGN KEY (pil_id) REFERENCES requests(request_id) ON DELETE CASCADE,
                    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
                );
                '''
            )

            await db_cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT NOT NULL,
                    pil_size INT NOT NULL,
                    pil_count INT NOT NULL,
                    status ENUM('confirmed', 'not confirmed', 'requires confirmation') NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES requests(request_id) ON DELETE CASCADE
                );
                '''
            )

        await db_connector.commit()