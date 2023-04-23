from flask import Flask, request
import logging
import json

import SeaBattle
from SeaBattle import *

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    print(user_id)
    if req['session']['new']:
        res['response']['text'] = random.choice(['Привет! Назови своё имя!',
                                                 'Привет! Как тебя зовут?', 'Привет! Я Алиса, а тебя как зовут?'])
        sessionStorage[user_id] = {
            'first_name': None,  # здесь будет храниться имя
            'game_started': False,
            'new session': 'true',
            'field': None,
            'u_field': None,
            'turn': 0  # Игрок ходит первым

            # здесь информация о том, что пользователь начал игру. По умолчанию False
        }
        return
    # Если игрокзахочет сразу закончить игру
    if 'выход' in req['request']['nlu']['tokens']:
        res['response']['text'] = f'Конец игры'
        end_session(res, user_id)
        return

    if sessionStorage[user_id]['first_name'] is None:
        # Знакомство
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = random.choice(['Это не имя! Представься заново, капитан!',
                                                     'Я таких имен не знаю! Признавайся кто ты!',
                                                     'Мы тут не шутим капитан! Представься!'])
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response']['text'] = f'Приятно познакомиться, {first_name}!' \
                                      f'Начнем нашу игру сначала. Тебе понадобится ручка и листочек в клеточку,' \
                                      f'Мы можем сыграть на маленьком поле 6 на 6, или на стандартном 10 на 10. ' \
                                      f'Выбери размер поля.'
            res['response']['buttons'] = [
                {'title': '6 на 6'}, {'title': '10 на 10'}
            ]

    else:
        # У нас уже есть имя, и теперь мы ожидаем ответ на предложение сыграть.
        # В sessionStorage[user_id]['game_started'] хранится True или False в зависимости от того,
        # начал пользователь игру или нет.
        if not sessionStorage[user_id]['game_started']:
            m = None
            n = None
            if '6' in req['request']['nlu']['tokens']:
                m, n = conf[0]
                sessionStorage[user_id]['game_started'] = True
            elif '10' in req['request']['nlu']['tokens']:
                m, n = conf[1]
                sessionStorage[user_id]['game_started'] = True
            else:
                res['response']['text'] = 'Не поняла ответа! Повтори ещё раз.'
                return
            # Алиса создает своё поле и поле игрока. Если Алиса за 100 попыток не сможет сгенерировать поле,
            # то она предложит сыграть в другой раз и закончит игру
            sessionStorage[user_id]['field'] = CField(m)
            sum_ships = (1 + n) * n / 2
            for i in range(100):
                num = 0
                for i in range(n, 0, -1):
                    for j in range(n - i + 1):
                        ship = CShip(i, sessionStorage[user_id]['field'])
                        num += 1
                if num != sum_ships:
                    for i in range(num, -1, -1):
                        del sessionStorage[user_id]['field'].ships[i]
                    sessionStorage[user_id]['field'].ships = []
                else:
                    break
            if not sessionStorage[user_id]['field'].ships:
                res['response'][
                    'text'] = 'Я не смогла расставить корабли. Давай сыграем в другой раз'
                end_session(res, req['session']['user_id'])
            # sessionStorage[user_id]['field'].print_field()
            sessionStorage[user_id]['u_field'] = CUserField(m, n)
            # Правила
            if m == 10:
                res['response'][
                    'text'] = f'Итак, играем на поле 10 на 10. Нарисуй свое поле и подпиши оси (руссике буквы сверху, цифры сбоку, как на шахматной доске). ' \
                              f'расставь корабли (4 однопалубных корабля, 3 двухпалубных, 2 трёхпалубных и один четырехпалубный). Ты ходишь первым.'
            elif m == 6:
                res['response'][
                    'text'] = f'Итак, играем на поле 6 на 6. Нарисуй свое поле и подпиши оси (руссике буквы сверху, цифры сбоку, как на шахматной доске). ' \
                              f'расставь корабли (3 однопалубных корабля, 2 двухпалубных и один трёхпалубных). Ты ходишь первым.'
        else:
            play_game(res, req)


# конец сессии
def end_session(res, user_id):
    sessionStorage[user_id]['game_started'] = False
    sessionStorage[user_id]['first_name'] = None
    res['response']['end_session'] = True


def play_game(res, req):
    user_id = req['session']['user_id']
    field = sessionStorage[user_id]['field']
    u_field = sessionStorage[user_id]['u_field']
    turn = sessionStorage[user_id]['turn']

    if 'выход' in req['request']['nlu']['tokens']:
        res['response']['text'] = f'Конец игры'
        end_session(res, user_id)

        return

    if turn == 0:  # ход игрока
        r = s2d(req['request']['original_utterance'], field.size)

        if r:

            result = field.attack(r)

            # Алиса говорит, что игрок попал
            if result == 1:
                res['response']['text'] = random.choice(['Попал, стреляй снова!',
                                                         'Меткий выстрел! Стреляй ещё раз!',
                                                         'Удача сегодня на твоей стороне! Проверь её еще раз!',
                                                         'Точно в цель, стреляй еще раз!'])
            # Алиса говорит, что игрок уничтожил корабль
            elif result == 2:
                res['response']['text'] = random.choice(['Убил, стреляй снова!',
                                                         'Корабль потерпел крушение! Стреляй ещё раз!',
                                                         'Удачным выстрелом ты потопил судно! Попробуй повтори!',
                                                         'Судно утонуло, стреляй еще раз!'])
            # Алиса говорит, что игрок победил
            elif result == 3:
                res['response'][
                    'text'] = random.choice(['Убил. Это был последний корабль. Поздравляю с победой капитан!',
                                             'Корабль потерпел крушение! Неплохой был бой, капитан!',
                                             'Удачным выстрелом ты потопил судно! Удача не подвела тебя сегодня, капитан!',
                                             'Судно утонуло, а вместе с ним и мой флот. Молодец, капитан!'])
                end_session(res, user_id)
            # Алиса говорит, что игрок не попал
            elif result == 0:
                if u_field.calculate_chance() == 0:
                    # {d2s(u_field.cur_shot.x, u_field.size).upper()}{u_field.cur_shot.y}
                    res['response'][
                        'text'] = random.choice(
                        [f'Не попал. Стреляю {d2s(u_field.cur_shot.x, u_field.size).upper()}{u_field.cur_shot.y}.',
                         f'Мимо! Проверим {d2s(u_field.cur_shot.x, u_field.size).upper()}{u_field.cur_shot.y}.',
                         f'Неудачный выстрел. Проверим мою удачу выстрелом в {d2s(u_field.cur_shot.x, u_field.size).upper()}{u_field.cur_shot.y}.'])
                else:
                    # Алиса не может скалькулировать ход
                    res['response'][
                        'text'] = f'Врунишка! Я с такими не играю'
                    end_session(res, user_id)
                sessionStorage[user_id]['turn'] = abs(sessionStorage[user_id]['turn'] - 1)
            # Выстрел игрока за пределы поля
            elif result == -1:
                res['response']['text'] = random.choice(['Сюда даже я бы не выстрелила. Стреляй ещё раз!',
                                                         'Выстрел за пределы поля! Попробуй ещё раз!',
                                                         'Неудачный выстрел за поле! Давай ещё раз!'])
            # Встрел игрока в ту точку, куда он уже стрелял
            elif result == -2:
                res['response']['text'] = random.choice(['Ты уже стрелял сюда. Стреляй ещё раз!',
                                                         'Молния два раза в одно место не бьет, как и ты два раза в одно место не стреляешь! Давай ещё раз!'])
            # Выстрел игрока в ту точку, где потоплен корабль
            elif result == -3:
                res['response']['text'] = random.choice(['Ты решил добить мои корабли? Стреляй ещё раз!',
                                                         'Твоё судно уже потонуло здесь. Поробуй ещё раз!'])

        #  Игрок ввел  некорректное значение
        else:
            res['response']['text'] = f'Ты будешь стрелять или нет?'
    else:  # ход Алисы
        if 'попал' in req['request']['original_utterance']:
            result = u_field.response(1)
            if result == 0:
                if u_field.calculate_chance() == 0:
                    # {d2s(u_field.cur_shot.x, u_field.size).upper()}{u_field.cur_shot.y}
                    res['response'][
                        'text'] = random.choice(
                        [f'Стреляю еще раз в {d2s(u_field.cur_shot.x, u_field.size).upper()}{u_field.cur_shot.y}.',
                         f'Проверим {d2s(u_field.cur_shot.x, u_field.size).upper()}{u_field.cur_shot.y}.',
                         f'Удача не подвела меня. Проверим её выстрелом в {d2s(u_field.cur_shot.x, u_field.size).upper()}{u_field.cur_shot.y}.'])
                else:
                    # Алиса поняла, что игрок либо обманул, либо ошибся
                    res['response'][
                        'text'] = f'Врунишка! Я с такими не играю'
                    end_session(res, user_id)
            else:
                # Алиса поняла, что игрок либо обманул, либо ошибся
                res['response']['text'] = f'Врунишка! Я с такими не играю'
                end_session(res, user_id)
        elif 'убил' in req['request']['original_utterance']:
            result = u_field.response(2)
            if result == 0:
                if u_field.calculate_chance() == 0:
                    res['response'][
                        'text'] = random.choice([
                        f'Отлично, давай еще что нибудь потопим. Как насчёт {d2s(u_field.cur_shot.x, u_field.size).upper()}{u_field.cur_shot.y}?',
                        f'Удача явно на моей стороне. Она поможет мне с {d2s(u_field.cur_shot.x, u_field.size).upper()}{u_field.cur_shot.y}?',
                        f'Как и ожидалось от лучшего капитана среди ИИ! Проивела расчёт на {d2s(u_field.cur_shot.x, u_field.size).upper()}{u_field.cur_shot.y}?'])
                else:
                    # Алиса поняла, что игрок либо обманул, либо ошибся
                    res['response'][
                        'text'] = f'Врунишка! Я с такими не играю'
                    end_session(res, user_id)

            elif result == -3:
                res['response']['text'] = random.choice(['Кажется я победила!',
                                                         'Уадча всегда на моей сторону, как и моя победа!',
                                                         'Это была легкая победа.'])
            else:
                # Алиса поняла, что игрок либо обманул, либо ошибся
                res['response']['text'] = f'Врунишка! Я с такими не играю'
                end_session(res, user_id)
        elif 'мимо' in req['request']['original_utterance']:
            result = u_field.response(0)
            res['response']['text'] = f'Хорошо, твой ход.'
            sessionStorage[user_id]['turn'] = abs(sessionStorage[user_id]['turn'] - 1)
        else:
            # Игрок сказал некорректное значение
            if u_field.cur_shot.x and u_field.cur_shot.y:
                res['response'][
                    'text'] = f'Я стреляла {d2s(u_field.cur_shot.x, field.size).upper()}{u_field.cur_shot.y}. Скажи попал, убил или мимо'
            else:
                # Алиса поняла, что игрок либо обманул, либо ошибся
                res['response'][
                    'text'] = f'Врунишка! Я с такими не играю'
                end_session(res, user_id)


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name',
            # то возвращаем ее значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


# Перевод клетки в координаты - х у
def s2d(s, n):
    alph = 'абвгдежзиклм'[:n]
    s1 = s.replace(' ', '').lower()
    ltr = s1[0]
    if ltr in alph:
        dig = s1[1:]
        if dig.isnumeric():
            d = int(dig)
            if 0 < d <= n:
                return (alph.find(ltr) + 1, d)
    return None


# Функция для Алисы - превращает координаты х в букву
def d2s(d, n):
    alph = 'абвгдежзиклм'[:n]
    if 0 < d <= n:
        return alph[d - 1]
    return None


if __name__ == '__main__':
    app.run(debug=True)
