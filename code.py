# -'- coding: utf-8 -*-
import sys
import json

import errno
import os
import signal

MC_MAP = {}
MC_DEPTH = 12


class TimeoutException(Exception):
    pass

class timeout:
    seconds = 0
    error_message = ''

    def __init__(self, seconds, error_message=os.strerror(errno.ETIME)):
        self.seconds = seconds
        self.error_message = error_message

    def __enter__(self):
        def _handle_timeout(signum, frame):
            raise TimeoutException(self.error_message)

        signal.signal(signal.SIGALRM, _handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)

def preprocess_map(m, player, opponent):
    mm = []
    if player == 'B':
        for i in range(8):
            for j in range(8):
                mm.append(m[(7 - i) * 8 + (7 - j)])
    else:
        mm.append(m)
    return (''.join(mm)
            .replace(player, 'P')
            .replace(player.lower(), 'x')
            .replace(opponent, 'O')
            .replace(opponent.lower(), 'x')
            + 'x')


def print_map(m):
    for i in range(8):
        print(m[i * 8: i * 8 + 8])


def mark_map(m, pos, mark='x'):
    return m[:pos] + mark + m[pos + 1:]


def player_move(m, action):
    pos = m.find('P')
    return mark_map(m.replace('P', 'x'), action(pos), 'P')


def opposite_move(m, action):
    pos = m.find('O')
    return mark_map(m.replace('O', 'x'), action(pos), 'O')


def distance(m):
    cur = m.find('P')
    pos = m.find('O')

    mm = [False] * 64
    mm.append(True)
    q = [cur]
    while q:
        curr = q.pop()
        if mm[curr]:
            continue
        if curr == pos:
            return True
        mm[curr] = True
        for action in action_choice(m, curr, ('x', 'P')).values():
            q.append(action(curr))
    return False


def find_logest_path(m, player, max_search):
    cur = m.find(player)
    maxx_direction = 'U'
    maxx = 0
    for d, action in action_choice(m, cur).items():
        mm = mark_map(m.replace(player, 'x'), action(cur), player)
        _, v = find_logest_path(mm, player, max_search - 1)
        if v + 1 > maxx:
            maxx_direction = d
            maxx = v + 1
        if maxx > max_search:
            return maxx_direction, maxx
    return maxx_direction, maxx


def up(pos):
    return pos - 8 if pos >= 8 else 64


def down(pos):
    return pos + 8 if pos < 56 else 64


def left(pos):
    return pos - 1 if pos % 8 != 0 else 64


def right(pos):
    return pos + 1 if pos % 8 != 7 else 64


command_to_function_map = {
    'U': up,
    'D': down,
    'R': right,
    'L': left,
}


def action_choice(m, pos, wall=('x', 'P', 'O')):
    ret = {}
    for command, func in command_to_function_map.items():
        if m[func(pos)] not in wall:
            ret[command] = func
    return ret


def mc(m, depth=MC_DEPTH):
    if depth <= 0:
        return 'U', 0
    if m in MC_MAP:
        return MC_MAP[m]
    maxx_d = 'U'
    maxx = -1
    if distance(m):
        for p_d, p_action in action_choice(m, m.find('P')).items():
            mm = player_move(m, p_action)
            ret = 0
            for o_action in action_choice(m, m.find('O')).values():
                if p_action(m.find('P')) == o_action(m.find('O')):
                    ret = -100
                else:
                    ret += 0.2 * mc(opposite_move(mm, o_action), depth - 2)[1]
            if ret > maxx:
                maxx = ret
                maxx_d = p_d
    else:
        p_d, p_l = find_logest_path(m, 'P', 20)
        o_d, o_l = find_logest_path(m, 'O', 20)
        maxx_d = p_d
        if p_l > o_l:
            maxx = 100
        elif p_l == o_l:
            maxx = -100
        else:
            maxx = -10000

    if depth == MC_DEPTH:
        MC_MAP[m] = (maxx_d, maxx)
    return maxx_d, maxx


def create_mc_sets(m, depth):
    if depth <= 0:
        return
    print_map(m)
    mm = mc(m)
    print(mm)
    if mm[1]  > 20:
        return
    p_action = command_to_function_map[mm[0]]
    mm = player_move(m, p_action)
    for o_action in action_choice(mm, m.find('O')).values():
        create_mc_sets(opposite_move(mm, o_action), depth - 1)


def test():
    m1 = preprocess_map("""
    A*******
    ********
    ********
    ********
    ********
    ********
    ********
    *******B
    """.replace('\n', '').replace(' ', ''), 'A', 'B')
    try:
        create_mc_sets(m1, 10)
    except:
        pass
    print(MC_MAP)


def main():
    data = json.loads(sys.argv[1])

    map_string = data['map']
    # opponent_history = data['opponent_history']
    # my_history = data['my_history']
    player = data['me']
    opponent = data['opponent']

    m = preprocess_map(map_string, player, opponent)
    try:
        with timeout(1):
            d = mc(m)[0]
    except TimeoutException:
        d = mc(m, MC_DEPTH - 2)[0]

    if player == 'A':
        print(d)
    else:
        if d == 'U':
            print('D')
        elif d == 'D':
            print('U')
        elif d == 'R':
            print('L')
        elif d == 'L':
            print('R')

test()

