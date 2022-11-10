import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from config import API_TOKEN

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

chooses = {}


def get_pair(current_index, options):
    arr = []
    for i in range(len(options)):
        for j in range(i + 1, len(options)):
            arr.append((i, j))

    if current_index < len(arr):
        return arr[current_index]

    return None


class ChooseState(StatesGroup):
    options = State()
    choosing = State()
    waiting_choose = State()


# Simple bot command
@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


# command /choose ask for options each one in new line
@dp.message_handler(commands=['choose'])
async def choose(message: types.Message):
    await message.reply("Enter options in new lines")
    chooses[message.from_user.id] = {
        "options": [],
        "scores": {},
        "current": -1
    }
    # set state to wait for options
    await ChooseState.options.set()


# if user press button
@dp.message_handler(lambda message: message.text == "Finish", state=ChooseState.options)
async def choose_options_first(message: types.Message, state: FSMContext):
    # show next question
    await next_question(message, state)


# wait for options in new lines
@dp.message_handler(state=ChooseState.options)
async def choose_options(message: types.Message):
    # explode options by new line
    options = message.text.splitlines()
    # add options to choose
    chooses[message.from_user.id]['options'].extend(options)
    # set scores to 0
    for i in range(0, len(chooses[message.from_user.id]['options'])):
        chooses[message.from_user.id]['scores'][i] = 0
    # show options length and button to finish or ask for more options
    await message.reply(f"Options count: {len(chooses[message.from_user.id]['options'])}\n"
                        f"Enter more options or press button to finish",
                        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
                        .add(types.KeyboardButton("Finish")))
    # wait for button or new options
    await ChooseState.options.set()


async def next_question(message: types.Message, state: FSMContext):
    # check if user has options
    if message.from_user.id in chooses:
        # check if user has more than 1 option
        if len(chooses[message.from_user.id]['options']) > 1:
            # increase current option index
            chooses[message.from_user.id]['current'] += 1

            pair = get_pair(chooses[message.from_user.id]['current'], chooses[message.from_user.id]['options'])

            if pair is not None:
                # set state to wait for choose
                await ChooseState.waiting_choose.set()
                # show question
                return await message.reply(f"Which one is better?\n"
                                           f"{chooses[message.from_user.id]['options'][pair[0]]}\n"
                                           f"or\n"
                                           f"{chooses[message.from_user.id]['options'][pair[1]]}",
                                           reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
                                           .add(types.KeyboardButton("First"))
                                           .add(types.KeyboardButton("Second")))
            else:
                # remove state
                await state.finish()
                # show result
                text = "Result:\n"

                # result_array is array of tuples (option, score)
                result_array = []
                for key, value in chooses[message.from_user.id]['scores'].items():
                    result_array.append((chooses[message.from_user.id]['options'][key], value))

                # sort result array by score
                result_array.sort(key=lambda x: x[1], reverse=True)

                # show result
                for item in result_array:
                    text += f"{item[0]} ({item[1]})\n"

                return await message.reply(text)

    # if user has no options or only one option show message
    return await message.reply(text="You have no options")


# if user press button
@dp.message_handler(lambda message: message.text == "First", state=ChooseState.waiting_choose)
async def choose_first(message: types.Message, state: FSMContext):
    # add score to first option
    option = get_pair(chooses[message.from_user.id]['current'], chooses[message.from_user.id]['options'])[0]
    chooses[message.from_user.id]['scores'][option] += 1
    # show next question
    await next_question(message, state)


# if user press button
@dp.message_handler(lambda message: message.text == "Second", state=ChooseState.waiting_choose)
async def choose_second(message: types.Message, state: FSMContext):
    # add score to second option
    option = get_pair(chooses[message.from_user.id]['current'], chooses[message.from_user.id]['options'])[1]
    chooses[message.from_user.id]['scores'][option] += 1
    # show next question
    await next_question(message, state)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
