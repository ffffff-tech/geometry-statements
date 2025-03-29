from flask import Flask, render_template, request, redirect, url_for, session
import random
import os
import json
import pickle
from base64 import b64encode, b64decode

# Импортируем утверждения и языковые настройки
from statements import russian_statements
from language import russian

app = Flask(__name__)
app.secret_key = "geometry_test_secret_key"  # Фиксированный ключ для сессий

# Глобальные переменные для хранения данных теста (вместо сессии)
test_in_progress = False
current_statements = []
current_question = 0
correct_answers = 0
user_answers = []

# Установка Flask для работы с библиотекой
try:
    import flask
except ImportError:
    pass  # Игнорируем ошибку, если flask не установлен (для IDE)
    
# Настройка CORS для работы в Miro
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('X-Frame-Options', 'ALLOWALL')
    response.headers.add('Content-Security-Policy', "frame-ancestors 'self' https://miro.com https://*.miro.com")
    return response

@app.route('/')
def index():
    global test_in_progress
    
    # Получаем словарь с текстами интерфейса
    lang = russian
    
    # Сбрасываем флаг теста при возврате на главную
    test_in_progress = False
    
    return render_template('index.html', lang=lang)

@app.route('/start_test', methods=['POST'])
def start_test():
    global test_in_progress, current_statements, current_question, correct_answers, user_answers
    
    # Фиксированное количество вопросов - 6
    num_questions = 6
    
    # Используем русские утверждения
    statements = russian_statements
    
    # Генерируем тест с случайными утверждениями
    current_statements = random.sample(statements, min(num_questions, len(statements)))
    current_question = 0
    correct_answers = 0
    user_answers = []
    test_in_progress = True
    
    return redirect(url_for('question'))

@app.route('/question')
def question():
    global test_in_progress, current_statements, current_question
    
    # Отладочная информация
    print("Question - Глобальные переменные: ", 
          "test_in_progress=", test_in_progress,
          "current_question=", current_question,
          "current_statements=", current_statements)
    
    # Если тест не начат, вернуться на главную
    if not test_in_progress:
        print("Тест не начат!")
        return redirect(url_for('index'))
    
    try:
        # Получаем словарь с текстами интерфейса
        lang = russian
        
        # Получаем информацию о текущем вопросе
        question_text = current_statements[current_question][0]
        question_number = current_question + 1
        total_questions = len(current_statements)
        
        return render_template(
            'question.html', 
            lang=lang, 
            question_text=question_text, 
            question_number=question_number, 
            total_questions=total_questions
        )
    except Exception as e:
        # В случае ошибки выводим информацию и возвращаемся на главную
        print("Ошибка в question:", str(e))
        return redirect(url_for('index'))

@app.route('/answer', methods=['POST'])
def answer():
    global test_in_progress, current_statements, current_question, correct_answers, user_answers
    
    try:
        # Отладочная информация
        print("Answer - Глобальные переменные: ", 
              "test_in_progress=", test_in_progress,
              "current_question=", current_question,
              "current_statements=", current_statements)
        
        # Если тест не начат, вернуться на главную
        if not test_in_progress:
            print("Тест не начат (в answer)!")
            return redirect(url_for('index'))
        
        # Получаем ответ пользователя
        user_answer = request.form.get('answer')
        
        # Приведем ответ к формату на русском языке
        user_answer = "верно" if user_answer == "true" else "неверно"
        
        # Получаем правильный ответ для текущего вопроса
        _, correct_answer = current_statements[current_question]
        
        # Проверяем ответ
        if user_answer == correct_answer:
            correct_answers += 1
        
        # Сохраняем ответ пользователя
        user_answers.append(user_answer)
        
        # Переходим к следующему вопросу
        current_question += 1
        
        # Если вопросы закончились, показываем результаты
        if current_question >= len(current_statements):
            test_in_progress = False
            return redirect(url_for('results'))
        
        # Если есть еще вопросы, показываем следующий
        return redirect(url_for('question'))
    except Exception as e:
        # В случае ошибки выводим информацию и возвращаемся на главную
        print("Ошибка в answer:", str(e))
        return redirect(url_for('index'))

@app.route('/results')
def results():
    global test_in_progress, current_statements, current_question, correct_answers, user_answers
    
    try:
        # Отладочная информация
        print("Results - Глобальные переменные: ", 
              "test_in_progress=", test_in_progress,
              "current_question=", current_question,
              "correct_answers=", correct_answers,
              "total_questions=", len(current_statements) if current_statements else 0)
        
        # Получаем словарь с текстами интерфейса
        lang = russian
        
        # Вычисляем результаты
        total_questions = len(current_statements)
        
        # Вычисляем оценку на основе количества правильных ответов
        grade = 2  # По умолчанию - неудовлетворительно
        if correct_answers >= 6:
            grade = 5  # Отлично
        elif correct_answers >= 4:
            grade = 4  # Хорошо
        elif correct_answers >= 2:
            grade = 3  # Удовлетворительно
        
        return render_template(
            'results.html', 
            lang=lang, 
            correct_answers=correct_answers, 
            total_questions=total_questions, 
            grade=grade,  # Передаем оценку вместо процента
            questions=current_statements,  # Передаем список вопросов
            user_answers=user_answers      # Передаем ответы пользователя
        )
    except Exception as e:
        # В случае ошибки выводим информацию и возвращаемся на главную
        print("Ошибка в results:", str(e))
        return redirect(url_for('index'))

@app.route('/retry')
def retry():
    global test_in_progress, current_statements, current_question, correct_answers, user_answers
    
    # Сбрасываем все глобальные переменные теста
    test_in_progress = False
    current_statements = []
    current_question = 0
    correct_answers = 0
    user_answers = []
    
    return redirect(url_for('index'))

@app.route('/miro')
def miro():
    """Специальный маршрут для интеграции с Miro"""
    return render_template('miro.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
# Для совместимости с Vercel
app.debug = False