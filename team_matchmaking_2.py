import time
import csv

matrix_values = [("a", 10, ["b", "c"], [], 1, 0, False), ("b", 9, ["c", "f"], [], 1, 0, False),
                 ("c", 8, ["a", "b", "d"], [], 0, 0, False),
                 ("d", 7, ["h", "i", "j"], [], 0, 0, False), ("e", 6, ["a", "g"], [], 1, 0, False),
                 ("f", 5, ["e", "a", "g"], [], 1, 0, False),
                 ("g", 4, ["e", "f"], [], 1, 0, False), ("h", 3, ["b", "c", "d"], [], 0, 0, False),
                 ("i", 2, ["h", "j"], [], 0, 0, False),
                 ("j", 1, ["i"], [], 0, 0, False), ("k", 7, ["i"], [], 0, 0, True), ("l", 8, ["i"], [], 0, 0, True),
                 ("m", 1, ["i"], [], 0, 0, True)]

test_teams = [([('a', 10, ['b', 'c'], [], 1, 0, False), ('b', 9, ['c', 'f'], [], 1, 0, False),
                ('e', 6, ['a', 'g'], [], 1, 0, False), ('c', 8, ['a', 'b', 'd'], [], 0, 0, False),
                ('g', 4, ['e', 'f'], [], 1, 0, False)], 7.4, []),
              ([('d', 7, ['h', 'i', 'j'], [], 0, 0, False), ('h', 3, ['b', 'c', 'd'], [], 0, 0, False),
                ('j', 1, ['i'], [], 0, 0, False), ('f', 5, ['e', 'a', 'g'], [], 1, 0, False),
                ('i', 2, ['h', 'j'], [], 0, 0, False)], 3.6, [])]


def main(player_list):
    sub_list = get_subs(player_list)
    teams = create_teams(player for player in player_list if player not in sub_list)
    sub_list.append(unused_players(teams, player_list))
    # teams = add_subs(teams, sub_list)
    output_to_csv(teams)


def get_subs(player_list):
    sub_list = []
    for x in player_list:
        if x[6]:
            sub_list.append(x)
    return sub_list


def create_teams(player_list):
    return "NO"


def unused_players(teams, player_list):
    unused_players_list = []
    for x in player_list:
        for y in teams:
            if x not in y[0]:
                unused_players_list.append(x)
                print("YEYEYE")
    return unused_players_list


print(unused_players(test_teams, matrix_values))


def output_to_csv(teams):
    name = "C:\\Users\\Kieran\\Desktop\\test\\test_output_" + str(round(time.time() * 1000)) + ".csv"
    with open(name, mode='w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        for x in teams:
            csv_writer.writerow(x)
