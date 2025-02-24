from aiogram.filters.command import Command
from aiogram.types import URLInputFile
from aiogram.filters.callback_data import CallbackData
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from db import update_quiz, get_quiz_index, load_stats, get_user_stats
import json

router = Router()

quiz_data = []
with open('quiz_data.json', encoding='utf-8') as file:
    quiz_data = json.load(file)

# Хэндлер на команду /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем сборщика клавиатур типа Reply
    builder = ReplyKeyboardBuilder()
   # Добавляем в сборщик одну кнопку
    builder.add(types.KeyboardButton(text="Начать квиз"))
    builder.add(types.KeyboardButton(text="Статистика"))
    # Прикрепляем кнопки к сообщению
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))

@router.message(F.text=="Начать квиз")
@router.message(Command('quiz'))
async def quiz_start(message: types.Message):
    # Начинаем квиз
    await message.answer('Начинаем квиз!')
    await new_quiz(message)

@router.message(F.text=="Статистика")
@router.message(Command('stats'))
async def quiz_start(message: types.Message):
    # Показать статистику
    stats = await load_stats()

    text = ''
    for i in range(len(stats)):
        for row in stats:
            row = list(row)
            text += f'{i+1}.  [ {row[1]} ] набрал  [ {row[2]} ]  правильных ответов!'

    await message.answer(f'{text}')


async def new_quiz(message):
    # получаем id пользователя, отправившего сообщение
    user_id = message.from_user.id

    # получаем username пользователя, отправившего сообщение
    username = message.from_user.username

    # сбрасываем значение текущего индекса вопроса квиза в 0
    current_question_index = 0
    stats = 0
    
    await update_quiz(user_id, username, current_question_index, stats)

    # запрашиваем новый вопрос для квиза
    await get_question(message, user_id)

# Создадим класс и опишем структуру нашей фабрики колбэков
class AnswerCallbackFactory(CallbackData, prefix="answers"):
    index: int
    is_right: bool

async def get_question(message, user_id):
    # Запрашиваем из базы текущий индекс для вопроса
    current_question_index = await get_quiz_index(user_id)
    # Получаем индекс правильного ответа для текущего вопроса
    correct_index = quiz_data[current_question_index]['correct_option']
    # Получаем URL картинки для текущего вопроса
    img_url = quiz_data[current_question_index]['url']
    # Получаем список вариантов ответа для текущего вопроса
    opts = quiz_data[current_question_index]['options']

    # Отправка файла по ссылке
    image_from_url = URLInputFile(img_url)

    # Функция генерации кнопок для текущего вопроса квиза
    # В качестве аргументов передаем варианты ответов и значение правильного ответа (не индекс!)
    kb = generate_options_keyboard(opts, opts[correct_index])
    # Отправляем в чат сообщение с вопросом, прикрепляем сгенерированные кнопки
    await message.answer_photo(image_from_url)
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)

def generate_options_keyboard(answer_options, right_answer):
  # Создаем сборщика клавиатур типа Inline
    builder = InlineKeyboardBuilder()

    # В цикле создаем 3 Inline кнопки, а точнее Callback-кнопки
    for i, option in enumerate(answer_options):
        print(option)
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data=AnswerCallbackFactory(index = i, is_right = True if option == right_answer else False).pack())
        )

    # Выводим по одной кнопке в столбик
    builder.adjust(1)
    return builder.as_markup()

@router.callback_query(AnswerCallbackFactory.filter())
async def my_callback_foo(callback: types.CallbackQuery, callback_data: AnswerCallbackFactory):
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Получаем username пользователя, отправившего сообщение
    username = callback.from_user.username

    # Получение текущей статистики для данного пользователя
    current_stats = await get_user_stats(callback.from_user.id)
        
    # Получение текущего вопроса для данного пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)

    correct_index = quiz_data[current_question_index]['correct_option']
    correct_option = quiz_data[current_question_index]['options'][correct_index]
    selected_option = quiz_data[current_question_index]['options'][callback_data.index]

    if callback_data.is_right:
        # Отправляем в чат сообщение, что ответ верный
        await callback.message.reply(f'Верно! это {correct_option}!' )
        current_stats += 1
    else:
        # Отправляем в чат сообщение об ошибке с указанием верного ответа
        await callback.message.reply(f"Ответ {selected_option} не верный! \n Правильный ответ: {correct_option}")

    # Обновление номера текущего вопроса и статистику в базе данных
    current_question_index += 1
    await update_quiz(callback.from_user.id, username, current_question_index, current_stats)

    # Проверяем достигнут ли конец квиза
    if current_question_index < len(quiz_data):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id)
    else:
        # Уведомление об окончании квиза
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")
        stats = await get_user_stats(callback.from_user.id)
        await callback.message.answer(f'Правильных ответов: {stats} из {len(quiz_data)}')

