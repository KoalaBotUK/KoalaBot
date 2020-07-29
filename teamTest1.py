import csv
import time

# How many ranks apart players can be without compatibility going to 0.
rank_depreciation = 5

# Player name:  Discord tag input by player, String
# Rank:         List input by creator, [Int]
# Friends:      People player wants to play with input by player, discord tag must be input, [String]
# Role:         Role a person plays in the team, can be turned of by creator, [String]
# Attitude:     Whether they want to play casually or competitively, Int
# Availability: When they can play, no idea for now
# Substitute:   If the player is acting as a substitute instead of a full time player, Bool

# Player tuple : (PlayerName, Rank, [Players they want to play with], [in-game role], attitude, availability, Substitute)

matrix_values = [("a", 10, ["b", "c"], [], 1, 0, False), ("b", 9, ["c", "f"], [], 1, 0, False),
                 ("c", 8, ["a", "b", "d"], [], 0, 0, False),
                 ("d", 7, ["h", "i", "j"], [], 0, 0, False), ("e", 6, ["a", "g"], [], 1, 0, False),
                 ("f", 5, ["e", "a", "g"], [], 1, 0, False),
                 ("g", 4, ["e", "f"], [], 1, 0, False), ("h", 3, ["b", "c", "d"], [], 0, 0, False),
                 ("i", 2, ["h", "j"], [], 0, 0, False),
                 ("j", 1, ["i"], [], 0, 0, False), ("k", 1, ["i"], [], 0, 0, True), ("l", 1, ["i"], [], 0, 0, True),
                 ("m", 1, ["i"], [], 0, 0, True)]

subs_list = [("k", 7, ["i"], [], 0, 0, True), ("l", 8, ["i"], [], 0, 0, True), ("m", 1, ["i"], [], 3, 0, True)]

team_size = 5

test_teams = [(['Team1', ('a', 10, ['b', 'c'], [], 1, 0, False), ('b', 9, ['c', 'f'], [], 1, 0, False),
                ('e', 6, ['a', 'g'], [], 1, 0, False), ('c', 8, ['a', 'b', 'd'], [], 0, 0, False),
                ('g', 4, ['e', 'f'], [], 1, 0, False)], 7.4, []),
              (['Team2', ('d', 7, ['h', 'i', 'j'], [], 0, 0, False), ('h', 3, ['b', 'c', 'd'], [], 0, 0, False),
                ('j', 1, ['i'], [], 0, 0, False), ('f', 5, ['e', 'a', 'g'], [], 1, 0, False),
                ('i', 2, ['h', 'j'], [], 0, 0, False)], 3.6, [])]


# Compatibility value based purely on ranks.
def create_value(first_player, second_player):
    if first_player[0] == second_player[0]:
        return -1
    rank_difference = calculate_rank_difference(first_player[1], second_player[1])
    if rank_difference == 0:
        return 0
    return rank_depreciation - rank_difference


# Compatibility value w/ "I want to team with person x and I don't want to play with y" taken into account.
def create_value_comp(first_player, second_player):
    if first_player[0] == second_player[0]:
        return -1
    rank_difference = calculate_rank_difference(first_player[1], second_player[1])
    if rank_difference == 0:
        return 0
    return (rank_depreciation - rank_difference) * want_to_play(first_player, second_player)


def create_value_attitude(first_player, second_player):
    if first_player[0] == second_player[0]:
        return -1
    # rank_difference = calculate_rank_difference(first_player[1], second_player[1])
    rank_difference = 1 - (calculate_rank_difference(first_player[1], second_player[1]) / rank_depreciation)
    if rank_difference == 0:
        return 0
    if second_player[6]:
        return -1
    return (4 * want_to_play(first_player, second_player)) + (3 * check_attitude(first_player, second_player)) + (
            2 * rank_difference)


# Checks if a player wants to play with another.
def want_to_play(first_player, second_player):
    if second_player[0] in first_player[2]:
        return 2
    return 1


# Checks if two players have a similar attitude to playing
def check_attitude(first_player, second_player):
    if second_player[4] == first_player[4]:
        return 1
    return 0


# Calculates the rank difference between two players, if difference > depreciation returns 0.
def calculate_rank_difference(rank_one, rank_two):
    rank_difference = abs(rank_one - rank_two)
    if rank_difference > rank_depreciation:
        return 0
    return rank_difference


# Creates an |A| * |A| matrix and populates it with compatibility values.
def create_matrix(player_list):
    matrix = [[int for i in range(len(player_list))] for j in range(len(player_list))]
    for x in range(len(player_list)):
        for y in range(len(player_list)):
            matrix[x][y] = create_value_attitude(player_list[x], player_list[y])
    return average_matrix(matrix)


# Alters a specific value in the matrix.
def alter_matrix_value(matrix, x_value, y_value, new_value):
    matrix[x_value][y_value] = new_value
    return matrix


# Print out each value row in the matrix.
def print_matrix(matrix):
    for n in matrix:
        print(n)


def get_highest_player(player_list):
    player = ("", 0, [], [])
    for p in player_list:
        if p[1] > player[1]:
            player = p
    return player


def highest_player_position(player_list, player):
    return player_list.index(player)


def pick_teams_rank_only(player_list):
    team = []
    matrix = create_matrix(player_list)
    highest_player = get_highest_player(player_list)
    team.append(highest_player[0])
    while len(team) < team_size:
        highest_player_compa_list = matrix[highest_player_position(player_list, highest_player)]
        next_player = get_next_player(highest_player_compa_list, player_list)
        team.append(next_player[0])
        player_list = remove_player(player_list, next_player)
    player_list.remove(highest_player)
    print(team)
    if len(player_list) >= team_size:
        pick_teams_rank_only(player_list)


# TODO sort this fuck ugly method out
def pick_teams_compa_list(player_list, input_teams):
    team = []
    teams = input_teams
    team.append("Team" + str(len(teams) + 1))
    highest_player = get_highest_player(player_list)
    team.append(highest_player)
    while len(team) < (team_size + 1):
        matrix = create_matrix(player_list)
        highest_player_compat_list = matrix[highest_player_position(player_list, highest_player)]
        next_player = get_next_player(highest_player_compat_list, player_list)
        team.append(next_player)
        player_list = remove_player(player_list, next_player)
    player_list.remove(highest_player)
    teams.append(team)
    if len(player_list) >= team_size:
        pick_teams_compa_list(player_list, teams)
    return teams


def get_highest(compat_list):
    return max(compat_list)


def get_next_player(compa_list, player_list):
    next_player = player_list[compa_list.index(max(compa_list))]
    return next_player


def remove_player(player_list, player):
    player_list.remove(player)
    return player_list


def average_matrix(matrix):
    for x in range(len(matrix)):
        y = x + 1
        while y < len(matrix):
            matrix[x][y] = matrix[x][y] + matrix[y][x]
            matrix[y][x] = matrix[x][y]
            y += 1
    return matrix


def get_sub_list(player_list):
    sub_list = []
    for x in player_list:
        if x[6]:
            sub_list.append(x)
    return sub_list


def remove_subs(player_list, sub_list):
    return [player for player in player_list if player not in sub_list]


def read_csv(location):
    player_list = []
    with open(location) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line = 0
        for row in csv_reader:
            if line != 0:
                player = (row[0], int(row[1]), parse_empty_list(row[2].split("|")), parse_empty_list(row[3].split("|")),
                          int(row[4]), int(row[5]), parse_bool(row[6]))
                player_list.append(player)
            line += 1
    return player_list


def write_csv(teams):
    name = "C:\\Users\\Kieran\\Desktop\\test\\test_output_" + str(current_time()) + ".csv"
    with open(name, mode='w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        for x in teams:
            csv_writer.writerow(x)


def parse_bool(input_bool):
    if input_bool == "TRUE":
        return True
    return False


def parse_empty_list(input_list):
    if input_list == ['']:
        return []
    return input_list


def current_time():
    return int(round(time.time() * 1000))


def convert_teams(teams):
    team_sub_list = []
    for x in teams:
        team_sub_list.append((x, team_rank_average(x), []))
    return team_sub_list


def team_rank_average(team):
    rank_total = 0
    for x in team:
        if x[1] != "e":
            rank_total += x[1]
    return rank_total / (len(team) - 1)


def assign_subs(teams, sub_list):
    av_ranks = team_av_rank_list(teams)
    for x in sub_list:
        teams[get_team_from_rank(take_closest(x[1], av_ranks), teams)][2].append(x)
    return teams


def take_closest(num, collection):
    return min(collection, key=lambda x: abs(x - num))


def team_av_rank_list(teams):
    av_ranks = []
    for x in teams:
        av_ranks.append(x[1])
    return av_ranks


def get_team_from_rank(rank, teams):
    for x in teams:
        if rank == x[1]:
            return teams.index(x)


# print(get_team_from_rank(take_closest(7, team_av_rank_list(test_teams)), test_teams))
# print(assign_subs(test_teams, subs_list))

print(pick_teams_compa_list(matrix_values, []))
