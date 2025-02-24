import aiosqlite

DB_NAME = 'quiz_bot.db'

async def create_table():
    # Создаем соединение с базой данных (если она не существует, то она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Выполняем SQL-запрос к базе данных
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, username TEXT, question_index INTEGER DEFAULT 0, stats INTEGER DEFAULT 0)''')
        # Сохраняем изменения
        await db.commit()

async def update_quiz(user_id, username, index, stats):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, username, question_index, stats) VALUES (?, ?, ?, ?)', (user_id, username, index, stats))
        # Сохраняем изменения
        await db.commit()


async def get_quiz_index(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0

async def get_user_stats(user_id):
    # Получаем текущую статистику пользователя
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT stats FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0

async def load_stats():
    # Загружаем статистику 10 лучших игроков
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT user_id, username, stats FROM quiz_state ORDER BY stats DESC LIMIT 10') as cursor:
            results = await cursor.fetchall()
            return results
           