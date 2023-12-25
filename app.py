import os
import re
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from gtts import gTTS
import random
from openai import OpenAI

app = Flask(__name__)

api_keys = ['sk-xxxxxx']


def generate_random_number_string(length=2):
    # random.random()
    # num=random.choices('0123456789', k=length)
    return ''.join(str(random.randint(0, 70)))


def text_to_speech(text, lang='fr'):
    filename = 'static/audio_' + str(uuid.uuid4()) + '.mp3'
    tts = gTTS(text, lang=lang)
    tts.save(filename)
    return filename


def access_gpt():
    client = OpenAI(
        api_key=api_keys[0],
        base_url="https://api.openai.com/"
    )

    prompt = ("1.我现在在学习法语，请给我生成20个包含70以内数字的法语句子，并且数字用阿拉伯数字表示。 "
              "2.这20句话里出现的数字分布要发散一点，不要出现重复的数字。 "
              "3.记住是70以内的数字。并且一句话里只能出现一个数字。"
              "4.直接输出20个句子就可以，不要出现其他多余的句子。"
              "5.不要出现包含时间的句子")

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    result = completion.choices[0].message.content
    global sentences
    sentences = [sentence.split(". ", 1)[1] for sentence in result.split("\n")]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_sentences')
def get_sentences():
    try:
        access_gpt()
        # 存储生成的音频文件名
        global audio_files
        audio_files = {i: "" for i in range(len(sentences))}
    except:
    		return "failure"
    return "success"

@app.route('/get_sentence_info')
def get_sentence_info():
    return jsonify({
        'total_sentences': len(sentences)
    })

@app.route('/get_sentence/<int:index>')
def get_sentence(index):
    if index < 0 or index >= len(sentences):
        return jsonify({'error': 'Invalid index'}), 400
    # 我们假设有一个函数来处理句子并替换数字
    sentence_with_blanks = replace_numbers_with_underscores(sentences[index])
    return jsonify({
        'sentence_with_blanks': sentence_with_blanks
    })


def replace_numbers_with_underscores(sentence):
    # 使用正则表达式匹配数字并替换为下划线
    return re.sub(r'\d+', '___', sentence)


@app.route('/generate_sentence_audio/<int:index>')
def generate_sentence_audio(index):
    # 确保索引有效
    if index < 0 or index >= len(sentences):
        return jsonify({'error': 'Invalid index'}), 400

    sentence = sentences[index]
    # 使用 UUID 生成唯一的文件名，确保每次请求都生成新的文件
    unique_filename = f"audio_sentence_{uuid.uuid4().hex}.mp3"
    tts = gTTS(text=sentence, lang='fr')
    tts.save(f'static/{unique_filename}')

    return jsonify({
        'audio_file': unique_filename,
        'sentence': sentence,
        'index': index
    })


@app.route('/generate_audio', methods=['POST'])
def generate_audio():
    # 删除旧的音频文件
    # for filename in os.listdir('static'):
    #     if filename.startswith('audio_'):
    #         os.remove(os.path.join('static', filename))

    data = request.get_json()
    length = int(data.get('length', 10)) if data else 10
    number_string = generate_random_number_string(length)
    audio_file = text_to_speech(number_string)
    return jsonify({'audio_file': audio_file, 'number': number_string})


@app.route('/audio/<filename>')
def audio(filename):
    return send_from_directory('static', filename)


if __name__ == '__main__':
    for filename in os.listdir('static'):
        if filename.startswith('audio_'):
            os.remove(os.path.join('static', filename))
    try:
        get_sentences()
    except:
    	   get_sentences()

    app.run()
