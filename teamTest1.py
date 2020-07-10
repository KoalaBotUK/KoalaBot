# How many ranks apart players can be without compatibility going to 0.
rank_depreciation = 5


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
    return (rank_depreciation - rank_difference) * calculate_compatibility_factor(first_player, second_player)


# Checks if a player wants to play with another.
def want_to_play(first_player, second_player):
    if second_player[0] in first_player[2]:
        return 2
    return 1


# Check if a player wants to avoid playing with another.
def want_to_avoid(first_player, second_player):
    if second_player[0] in first_player[3]:
        return 0
    return 1


# Calculates the compatibility multiplier.
def calculate_compatibility_factor(first_player, second_player):
    return want_to_play(first_player, second_player) * want_to_avoid(first_player, second_player)


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
            matrix[x][y] = create_value_comp(player_list[x], player_list[y])
    return matrix


# Alters a specific value in the matrix.
def alter_matrix_value(matrix, x_value, y_value, new_value):
    matrix[x_value][y_value] = new_value
    return matrix


# Print out each value row in the matrix.
def print_matrix(matrix):
    for n in matrix:
        print(n)


# Player tuple : (PlayerName, Rank, [Players they want to play with], [Players they don't want to play with])
matrix_values = [("a", 10, ["b", "c"], []), ("b", 9, [], []), ("c", 8, [], []), ("d", 7, [], []), ("e", 6, [], []),
                 ("f", 5, [], []), ("g", 4, [], []), ("h", 3, [], []), ("i", 2, [], []), ("j", 1, [], [])]

print_matrix(create_matrix(matrix_values))
