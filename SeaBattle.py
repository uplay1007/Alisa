import random

conf = [(6, 3), (10, 4)]


class CShot:
    def __init__(self):
        self.x = None
        self.y = None


class CUserField:
    def __init__(self, size, max_ship_size):
        self.size = size
        self.max_ship_size = max_ship_size
        self.a_cells = [(x + 1, y + 1) for x in range(self.size) for y in range(self.size)]
        self.cur_sections = []
        self.cur_shot = CShot()
        self.killed_ships = []  # массив убитых судов

    def print_available(self):
        field = [['■' for i in range(1, self.size + 1)] for j in range(1, self.size + 1)]
        for c in self.a_cells:
            field[c[0] - 1][c[1] - 1] = '.'
        for i in field:
            print(*i)

    # Расчёт выстрела
    def calculate_chance(self):
        if not self.cur_sections:
            c = random.choice(self.a_cells)
            self.cur_shot.x, self.cur_shot.y = c[0], c[1]
        elif len(self.cur_sections) == 1:
            pos_shots = []
            if (self.cur_sections[0][0] - 1, self.cur_sections[0][1]) in self.a_cells:
                pos_shots.append((self.cur_sections[0][0] - 1, self.cur_sections[0][1]))
            if (self.cur_sections[0][0], self.cur_sections[0][1] - 1) in self.a_cells:
                pos_shots.append((self.cur_sections[0][0], self.cur_sections[0][1] - 1))
            if (self.cur_sections[0][0] + 1, self.cur_sections[0][1]) in self.a_cells:
                pos_shots.append((self.cur_sections[0][0] + 1, self.cur_sections[0][1]))
            if (self.cur_sections[0][0], self.cur_sections[0][1] + 1) in self.a_cells:
                pos_shots.append((self.cur_sections[0][0], self.cur_sections[0][1] + 1))
            if not pos_shots:
                return -1  # нет ходов, либо пользователь ошибся, либо наврал
            else:
                c = random.choice(pos_shots)
                self.cur_shot.x, self.cur_shot.y = c[0], c[1]
        elif len(self.cur_sections) > self.max_ship_size:
            return -2  # пользователь ошибся, либо наврал
        else:
            pos_shots = []
            if self.cur_sections[0][0] == self.cur_sections[-1][0]:
                y_min = min(list(map(lambda y: y[1], self.cur_sections)))
                y_max = max(list(map(lambda y: y[1], self.cur_sections)))
                if (self.cur_sections[-1][0], y_min - 1) in self.a_cells:
                    pos_shots.append((self.cur_sections[-1][0], y_min - 1))
                if (self.cur_sections[-1][0], y_max + 1) in self.a_cells:
                    pos_shots.append((self.cur_sections[-1][0], y_max + 1))

            else:
                x_min = min(list(map(lambda x: x[0], self.cur_sections)))
                x_max = max(list(map(lambda x: x[0], self.cur_sections)))
                if (x_min - 1, self.cur_sections[-1][1]) in self.a_cells:
                    pos_shots.append((x_min - 1, self.cur_sections[-1][1]))
                if (x_max + 1, self.cur_sections[-1][1]) in self.a_cells:
                    pos_shots.append((x_max + 1, self.cur_sections[-1][1]))
            if not pos_shots:
                return -1  # нет ходов, либо пользователь ошибся, либо наврал
            else:
                c = random.choice(pos_shots)
                self.cur_shot.x, self.cur_shot.y = c[0], c[1]

        return 0

    # Метод проверяет, остались ли корабли или нет
    def has_alive(self):
        s = (1 + self.max_ship_size) * self.max_ship_size / 2
        if len(self.killed_ships) <= s:
            return True
        return False

    # Обработка слов игрока, после хода Алисы
    def response(self, ans):
        # значение ans:
        # 0 - не попал
        # 1 - попал
        # 2 - убил
        if self.cur_shot.x and self.cur_shot.y:
            if ans == 0:
                del self.a_cells[self.a_cells.index((self.cur_shot.x, self.cur_shot.y))]
                self.cur_shot.x, self.cur_shot.y = None, None
                return 0
            elif ans == 1:
                self.cur_sections.append((self.cur_shot.x, self.cur_shot.y))
                del self.a_cells[self.a_cells.index((self.cur_shot.x, self.cur_shot.y))]
                self.cur_shot.x, self.cur_shot.y = None, None
                return 0
            elif ans == 2:
                self.cur_sections.append((self.cur_shot.x, self.cur_shot.y))
                del self.a_cells[self.a_cells.index((self.cur_shot.x, self.cur_shot.y))]
                self.cur_shot.x, self.cur_shot.y = None, None
                x1 = min(list(map(lambda x: x[0], self.cur_sections))) - 1
                y1 = min(list(map(lambda y: y[1], self.cur_sections))) - 1
                x2 = max(list(map(lambda x: x[0], self.cur_sections))) + 1
                y2 = max(list(map(lambda y: y[1], self.cur_sections))) + 1
                for x in range(x1, x2 + 1):
                    for y in range(y1, y2 + 1):
                        if (x, y) in self.a_cells:
                            del self.a_cells[self.a_cells.index((x, y))]
                self.killed_ships.append(len(self.cur_sections))
                self.cur_sections.clear()
                if self.has_alive():
                    return 0  # есть непотопленные корабли
                return -3  # все корабли уничтожены
            else:
                return -1  # некорректный ход
        else:
            return -2  # ход не расчитан


# Поле Алисы
class CField:
    def __init__(self, size):
        self.size = size
        self.ships = []
        self.shots = []
        self.used = []

    # Алиса обрабатывает ход игрока затем говорит, попал он или нет, либо произошла ошибка
    def attack(self, cord):
        # -1 - ошибка (за пределами)
        # -2 - ошибка (выстрел в ту же точку)
        # -3 - ошибка (здесь не может быть корабля, когда он уничтожен)
        # 0 - не попал
        # 1 - попал
        # 2 - убил
        # 3 - все убиты
        if cord[0] < 1 or cord[0] > self.size or cord[1] < 1 or cord[1] > self.size:
            return -1
        elif cord in self.shots:
            return -2
        elif cord in self.used:
            return -3
        else:
            s = self.find_ship(cord)
            self.shots.append(cord)
            if s:
                s.sections[cord] = 0
                if self.has_alive():
                    if any(list(s.sections.values())):
                        return 1
                    else:
                        if s.rot == 0:
                            for x in range(s.x - 1, s.x + s.size + 1):
                                for y in range(s.y - 1, s.y + 2):
                                    self.used.append((x, y))
                        else:
                            for x in range(s.x - 1, s.x + 2):
                                for y in range(s.y - 1, s.y + s.size + 1):
                                    self.used.append((x, y))
                        return 2
                return 3
            else:
                return 0

    # Проверка на наличе кораблей
    def has_alive(self):
        for s in self.ships:
            for v in s.sections.values():
                if v == 1:
                    return True
        return False

    # Метод, с помощью Алиса проверяет, попал ли игрок по кораблю или нет
    def find_ship(self, cord):
        for s in self.ships:
            for k, v in s.sections.items():
                if k[0] == cord[0] and k[1] == cord[1]:
                    return s
        return None

    # Метод для дебага
    def print_field(self):
        field = [['•' for i in range(1, self.size + 1)] for j in range(1, self.size + 1)]
        for s in self.ships:
            for i in range(s.size):
                # print(s.rot, s.x, s.y, i)
                if s.rot == 0:
                    field[s.y - 1][s.x + i - 1] = '■'
                else:
                    field[s.y + i - 1][s.x - 1] = '■'
        for i in field:
            print(*i)


# Класс корабля
class CShip:
    def __init__(self, size, parent):
        self.size = size
        self.parent = parent
        self.x = -1
        self.y = -1
        self.rot = -1
        self.sections = {}
        if self.find_rand_place():
            self.parent.ships.append(self)

    # Постановка корабля
    def set_place(self, x, y, rot):
        self.x, self.y, self.rot = x, y, rot
        if self.rot == 0:
            for i in range(self.x, self.x + self.size):
                self.sections[(i, self.y)] = 1
                # self.sections.append((i, self.y))
        else:
            for j in range(self.y, self.y + self.size):
                self.sections[(self.x, j)] = 1
                # self.sections.append((self.x, j))

    # Метод, который рандомно ставит корабль
    def find_rand_place(self):
        free_cord = [(x + 1, y + 1) for x in range(self.parent.size) for y in
                     range(self.parent.size)]
        while True:
            cord = random.choice(free_cord)
            rot = random.choice([0, 1])  # 0 - горизонатльное; 1 - вертикальное
            if self.check_fits(cord, rot):
                self.set_place(cord[0], cord[1], rot)
                return True
            elif self.check_fits(cord, abs(rot - 1)):
                self.set_place(cord[0], cord[1], abs(rot - 1))
                return True
            else:
                del free_cord[free_cord.index(cord)]
                if not free_cord:
                    return False

    # Проверка на вместимость корабля в поле
    def check_fits(self, cord, rot):
        for i in range(self.size):
            if rot == 0:
                if 1 > cord[0] + i or cord[0] + i > self.parent.size or 1 > cord[1] or cord[1] > self.parent.size:
                    return False
            else:
                if 1 > cord[0] or cord[0] > self.parent.size or 1 > cord[1] + i or cord[1] + i > self.parent.size:
                    return False
        for s in self.parent.ships:
            x1 = s.x - 1
            y1 = s.y - 1
            x2 = s.x + s.size if s.rot == 0 else s.x + 1
            y2 = s.y + s.size if s.rot == 1 else s.y + 1
            for i in range(self.size):
                if rot == 0:
                    if (x1 <= cord[0] + i <= x2 and y1 <= cord[1] <= y2):
                        return False
                else:
                    if (x1 <= cord[0] <= x2 and y1 <= cord[1] + i <= y2):
                        return False
        return True
