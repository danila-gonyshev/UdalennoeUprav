import telebot
import subprocess
import cv2
import webbrowser
import os
import pyautogui
from io import BytesIO
import sounddevice as sd
import numpy as np
import wave

TOKEN = 'your bot token'
PASSWORD = 'test12345@' #password

bot = telebot.TeleBot(TOKEN)

programs = {
    'Notepad': 'notepad.exe',
    'Calculator': 'calc.exe',
    'Paint': 'mspaint.exe',
    'Explorer': 'explorer.exe',
}

user_authenticated = {}

def is_authenticated(message):
    return user_authenticated.get(message.chat.id, False)

@bot.message_handler(commands=['start'])
def start_message(message):
    if not is_authenticated(message):
        bot.send_message(message.chat.id, 'Please enter the password to access:')
        bot.register_next_step_handler(message, authenticate_user)
        return

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    actions = ['Open Program', 'Take Photo', 'Open Link', 'Create Object', 'Take Screenshot', 'Record Audio']
    buttons = [telebot.types.KeyboardButton(action) for action in actions]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Choose an action:", reply_markup=markup)

def authenticate_user(message):
    if message.text == PASSWORD:
        user_authenticated[message.chat.id] = True
        bot.send_message(message.chat.id, 'Access granted. Welcome!')
        start_message(message)
    else:
        bot.send_message(message.chat.id, 'Incorrect password. Please try again:')
        bot.register_next_step_handler(message, authenticate_user)

@bot.message_handler(func=lambda message: message.text == 'Back')
def handle_back(message):
    start_message(message)

@bot.message_handler(func=lambda message: message.text == 'Open Program')
def choose_program(message):
    if not is_authenticated(message):
        bot.send_message(message.chat.id, 'Please enter the password to access:')
        bot.register_next_step_handler(message, authenticate_user)
        return

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for program_name in programs:
        markup.add(telebot.types.KeyboardButton(program_name))
    markup.add(telebot.types.KeyboardButton('Back'))
    bot.send_message(message.chat.id, "Choose a program to open:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in programs)
def open_program(message):
    if not is_authenticated(message):
        bot.send_message(message.chat.id, 'Please enter the password to access:')
        bot.register_next_step_handler(message, authenticate_user)
        return

    program_name = message.text
    program_path = programs.get(program_name)
    if program_path:
        try:
            subprocess.Popen(program_path)
            bot.send_message(message.chat.id, f'Program "{program_name}" opened.')
        except Exception:
            pass
    else:
        bot.send_message(message.chat.id, 'Program not found.')

@bot.message_handler(func=lambda message: message.text == 'Take Photo')
def take_photo(message):
    if not is_authenticated(message):
        bot.send_message(message.chat.id, 'Please enter the password to access:')
        bot.register_next_step_handler(message, authenticate_user)
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        bot.send_message(message.chat.id, 'Unable to open the webcam.')
        return

    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        bot.send_message(message.chat.id, 'Failed to take photo.')
        return

    _, img_encoded = cv2.imencode('.jpg', frame)
    img_bytes = img_encoded.tobytes()
    
    bot.send_photo(message.chat.id, photo=BytesIO(img_bytes))

@bot.message_handler(func=lambda message: message.text == 'Open Link')
def ask_for_link(message):
    if not is_authenticated(message):
        bot.send_message(message.chat.id, 'Please enter the password to access:')
        bot.register_next_step_handler(message, authenticate_user)
        return

    bot.send_message(message.chat.id, 'Please send the link to open.')

@bot.message_handler(func=lambda message: message.text.startswith('http'))
def open_link(message):
    if not is_authenticated(message):
        bot.send_message(message.chat.id, 'Please enter the password to access:')
        bot.register_next_step_handler(message, authenticate_user)
        return

    link = message.text
    try:
        webbrowser.open(link)
        bot.send_message(message.chat.id, 'Link opened')
    except Exception:
        pass

@bot.message_handler(func=lambda message: message.text == 'Create Object')
def create_object(message):
    if not is_authenticated(message):
        bot.send_message(message.chat.id, 'Please enter the password to access:')
        bot.register_next_step_handler(message, authenticate_user)
        return

    markup = telebot.types.InlineKeyboardMarkup()
    btn_create_folder = telebot.types.InlineKeyboardButton('Create Folder', callback_data='create_folder')
    btn_create_file = telebot.types.InlineKeyboardButton('Create Text File', callback_data='create_file')
    markup.add(btn_create_folder, btn_create_file)
    bot.send_message(message.chat.id, "Choose an object to create:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['create_folder', 'create_file'])
def handle_create_object_choice(call):
    if call.data == 'create_folder':
        bot.send_message(call.message.chat.id, 'Enter the name of the folder to create:')
        bot.register_next_step_handler(call.message, handle_folder_creation)
    elif call.data == 'create_file':
        bot.send_message(call.message.chat.id, 'Enter the name of the file to create:')
        bot.register_next_step_handler(call.message, handle_file_creation)

def handle_folder_creation(message):
    folder_name = message.text
    try:
        os.makedirs(folder_name)
        bot.send_message(message.chat.id, f'Folder "{folder_name}" created.')
    except Exception:
        pass

def handle_file_creation(message):
    file_name = message.text
    bot.send_message(message.chat.id, 'Enter the file content:')
    bot.register_next_step_handler(message, lambda msg: handle_file_content(msg, file_name))

def handle_file_content(message, file_name):
    file_content = message.text
    try:
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(file_content)
        bot.send_message(message.chat.id, f'File "{file_name}" created and written.')
    except Exception:
        pass

@bot.message_handler(func=lambda message: message.text == 'Take Screenshot')
def take_screenshot(message):
    if not is_authenticated(message):
        bot.send_message(message.chat.id, 'Please enter the password to access:')
        bot.register_next_step_handler(message, authenticate_user)
        return

    screenshot = pyautogui.screenshot()
    with BytesIO() as img_buffer:
        screenshot.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        bot.send_photo(message.chat.id, photo=img_buffer)

@bot.message_handler(func=lambda message: message.text == 'Record Audio')
def choose_recording_duration(message):
    if not is_authenticated(message):
        bot.send_message(message.chat.id, 'Please enter the password to access:')
        bot.register_next_step_handler(message, authenticate_user)
        return

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    durations = ['5 seconds', '10 seconds', '30 seconds', '1 minute']
    buttons = [telebot.types.KeyboardButton(duration) for duration in durations]
    markup.add(*buttons, telebot.types.KeyboardButton('Back'))
    bot.send_message(message.chat.id, 'Choose audio recording duration:', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ['5 seconds', '10 seconds', '30 seconds', '1 minute'])
def record_audio(message):
    if not is_authenticated(message):
        bot.send_message(message.chat.id, 'Please enter the password to access:')
        bot.register_next_step_handler(message, authenticate_user)
        return

    duration_map = {
        '5 seconds': 5,
        '10 seconds': 10,
        '30 seconds': 30,
        '1 minute': 60
    }
    duration = duration_map[message.text]

    bot.send_message(message.chat.id, f'Starting audio recording for {duration} seconds...')

    fs = 44100
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=2, dtype='int16')
    sd.wait()

    filename = 'audio_recording.wav'
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(fs)
        wf.writeframes(recording.tobytes())
    
    with open(filename, 'rb') as audio_file:
        bot.send_audio(message.chat.id, audio_file)
    
    bot.send_message(message.chat.id, 'Recording completed and sent.')
    os.remove(filename)

bot.polling(none_stop=True)
