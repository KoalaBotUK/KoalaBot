import time
import csv

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
                 ("j", 1, ["i"], [], 0, 0, False), ("k", 7, ["i"], [], 0, 0, True), ("l", 8, ["i"], [], 0, 0, True),
                 ("m", 1, ["i"], [], 0, 0, True)]

test_teams = [([('a', 10, ['b', 'c'], [], 1, 0, False), ('b', 9, ['c', 'f'], [], 1, 0, False),
                ('e', 6, ['a', 'g'], [], 1, 0, False), ('c', 8, ['a', 'b', 'd'], [], 0, 0, False),
                ('g', 4, ['e', 'f'], [], 1, 0, False)], 7.4, []),
              ([('d', 7, ['h', 'i', 'j'], [], 0, 0, False), ('h', 3, ['b', 'c', 'd'], [], 0, 0, False),
                ('j', 1, ['i'], [], 0, 0, False), ('f', 5, ['e', 'a', 'g'], [], 1, 0, False),
                ('i', 2, ['h', 'j'], [], 0, 0, False)], 3.6, [])]

# All roles in the game, can be altered by whoever starts team making
all_roles_in_game = []#["Support", "DPS", "Tank"]

# Maximum number of a role in a team, optimises team to ensure at least this many players in the team can take on each role.
max_role_in_team = 2

max_team_size = 5

rank_depreciation = 5

# Team list : [[Players in team], Average rank of team, [Subs in team], {Dictionary of roles in team}, [Index location of players]]
# This is taken down to just the [Player in team] at the output.
test_team = [[('a', 10, ['b', 'c'], ["Support", "DPS"], 1, 0, False), ('b', 9, ['c', 'f'], ["Support", "DPS"], 1, 0, False),
            ('e', 6, ['a', 'g'], ["Support", "DPS"], 1, 0, False), ('c', 8, ['a', 'b', 'd'], ["DPS", "Tank"], 0, 0, False),
            ('g', 4, ['e', 'f'], ["DPS", "Tank"], 1, 0, False)], 7.4, [], {"Support": 3, "DPS": 5, "Tank": 2}, [0, 1, 2, 4, 6]]

# If this team is a one-off team. If it is one-off then availability doesn't need to be taken into account.
one_off = False


def main(player_list):
    sub_list = get_subs(player_list)
    players_list = [player for player in player_list if player not in sub_list]
    teams = create_teams(players_list)
    sub_list + unused_players(teams, players_list)
    teams = add_subs(teams, sub_list)
    output_to_csv(teams)


def get_subs(player_list):
    sub_list = []
    for player in player_list:
        if player[6]:
            sub_list.append(player)
    return sub_list


def add_subs(teams, sub_list):
    for sub in sub_list:
        posn = pposn = 0
        team = teams[0]
        for x in teams:
            if abs(sub[1] - x[1]) < abs(sub[1] - team[1]):
                pposn = posn
                team = x
            posn += 1
        teams[pposn][2].append(sub)
    return teams


def update_dictionary(team):
    role_dict = {}
    for x in all_roles_in_game:
        role_dict[x] = 0
    for player in team[0]:
        for role in player[3]:
            role_dict[role] = (role_dict[role] + 1)
    return role_dict


def create_teams(player_list):
    teams = []
    while len(player_list) >= max_team_size:
        team = [[player_list[0]], player_list[0][1], [], {}, [0]]
        while len(team[0]) < max_team_size:
            team[1] = average_rank(team[0])
            team[3] = update_dictionary(team)
            matrix = average_matrix(create_matrix(player_list, team))
            next_player = get_highest_compatible_player(matrix, team, player_list)
            team[0].append(next_player)
            team[4].append(player_list.index(next_player))
        teams.append(team)
        for player in team[0]:
            player_list.remove(player)
    return teams


def average_rank(player_list):
    return (sum([item[1] for item in player_list]))/len(player_list)


def get_highest_compatible_player(matrix, team, player_list):
    check = []
    for posn in team[4]:
        check.append(matrix[posn])
    new_list = [sum(x) for x in zip(*check)]
    for posn in team[4]:
        new_list[posn] = -1
    return player_list[new_list.index(max(new_list))]


def create_matrix(player_list, team):
    matrix = [[int for i in range(len(player_list))] for j in range(len(player_list))]
    for x in range(len(player_list)):
        for y in range(len(player_list)):
            matrix[x][y] = compatibility_value(player_list[x], player_list[y], team)
    return matrix


def average_matrix(matrix):
    for x in range(len(matrix)):
        y = x + 1
        while y < len(matrix):
            matrix[x][y] = matrix[x][y] + matrix[y][x]
            matrix[y][x] = matrix[x][y]
            y += 1
    return matrix


def compatibility_value(player_one, player_two, team):
    if player_one[0] == player_two[0]:
        return -1
    return (5 * check_compatible_role(player_one, player_two, team)) + (4 * want_to_play(player_one, player_two)) + (3 * check_attitude(player_one, player_two)) + (
            2 * rank_difference(player_one, player_two)) + (1 * availability_compatibility(player_one, player_two))


def simulate_change(player, team):
    team.append(player)
    dictionary = update_dictionary(team)
    maximum_value = dictionary.get(max(dictionary, key=lambda key: dictionary[key]))
    diff = 0
    for x in dictionary.keys():
        diff += maximum_value - dictionary[x]
    if diff > 3*len(all_roles_in_game):
        return 0
    return (3*len(all_roles_in_game) - diff) / 3*len(all_roles_in_game)


def check_compatible_role(player_one, player_two, team):
    if not all_roles_in_game:
        return 0
    if (player_one in team[0] & player_two in team[0]) | (player_one not in team[0] & player_two not in team[0]):
        return 0
    if player_one in team[0] & player_two not in team[0]:
        return simulate_change(player_two, team)
    if player_one not in team[0] & player_two in team[0]:
        return simulate_change(player_one, team)


def want_to_play(player_one, player_two):
    if player_two[0] in player_one[2]:
        return 1
    return 0


def check_attitude(player_one, player_two):
    if player_one[4] == player_two[4]:
        return 1
    return 0


def rank_difference(player_one, player_two):
    difference = abs(player_one[1] - player_two[1])
    if difference > rank_depreciation:
        return 0
    return 1 - (difference / rank_depreciation)


def availability_compatibility(player_one, player_two):
    if one_off:
        return 0
    return 0


def unused_players(teams, player_list):
    used_players = []
    for team in teams:
        for player in team[0]:
            used_players.append(player)
    return [x for x in player_list if x not in used_players]


def output_to_csv(teams):
    name = "C:\\Users\\Kieran\\Desktop\\test\\test_output_" + str(round(time.time() * 1000)) + ".csv"
    team_cond = condense_teams(teams)
    with open(name, mode='w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        csv_writer.writerow(["Players", "Substitutes"])
        for x in team_cond:
            csv_writer.writerow(x)


def condense_teams(teams):
    team_cond = []
    for x in teams:
        team_cond.append([x[0], x[2]])
    for n in team_cond:
        n[0] = [i[0] for i in n[0]]
        n[1] = [i[0] for i in n[1]]
    return team_cond


def read_csv(location):
    player_list = []
    with open(location) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line = 0
        for row in csv_reader:
            if line != 0:
                player = (row[0], int(row[1]), parse_empty_list(row[2].split("|")), parse_empty_list(row[3].split("|")),
                          int(row[4]), int(row[5]), parse_bool(row[6]))
                player_list.append((player, (line - 1)))
            line += 1
    return player_list


def parse_bool(input_bool):
    if input_bool == "TRUE":
        return True
    return False


def parse_empty_list(input_list):
    if input_list == ['']:
        return []
    return input_list


def print_matrix(matrix):
    for n in matrix:
        print(n)


if __name__ == '__main__':
    main(matrix_values)
