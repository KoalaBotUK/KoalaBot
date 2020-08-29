import time
import csv
import asyncio
from tkinter.filedialog import askopenfilename
import discord
from discord import Client
from discord.ext import commands
from discord.ext.commands import bot
from dotenv import load_dotenv
import requests

import KoalaBot
from KoalaBot import KOALA_GREEN
import utils.KoalaUtils

# Player tuple : (PlayerName, Rank, [Players they want to play with], [in-game role], attitude, availability, Substitute)


matrix_values = [("a", 10, ["b", "c"], [], 1, 0, False), ("b", 9, ["c", "f"], [], 1, 0, False),
                 ("c", 8, ["a", "b", "d"], [], 0, 0, False),
                 ("d", 7, ["h", "i", "j"], [], 0, 0, False), ("e", 6, ["a", "g"], [], 1, 0, False),
                 ("f", 5, ["e", "a", "g"], [], 1, 0, False),
                 ("g", 4, ["e", "f"], [], 1, 0, False), ("h", 3, ["b", "c", "d"], [], 0, 0, False),
                 ("i", 2, ["h", "j"], [], 0, 0, False),
                 ("j", 1, ["i"], [], 0, 0, False), ("k", 7, ["i"], [], 0, 0, True), ("l", 8, ["i"], [], 0, 0, True),
                 ("m", 1, ["i"], [], 0, 0, True)]


def get_subs(player_list):
    """
    Returns players that want to be subs from the player list.
    :param player_list: List of all players including those that want to be substitutes.
    :return: New list of subs
    """
    sub_list = []
    for player in player_list:
        if player[6]:
            sub_list.append(player)
    return sub_list


def add_subs(teams, sub_list):
    """
    Adds subs to teams, uses the team with the closest average rank to the substitute.
    :param teams: List of team tuples
    :param sub_list: List of players that indicated they wanted to be substitutes.
    :return: The teams list with substitutes added back in.
    """
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


def update_dictionary(team, all_roles_in_game):
    """
    Updates the dictionary of the sum of team roles. Doesn't add a player to the team so player needs to be added beforehand.
    e.g. if player with roles ["a"] joins a team with dictionary {"a": 3, "b": 5, "c": 2} it will then return {"a": 4, "b": 5, "c": 2}
    :param all_roles_in_game:
    :param team: The team that needs its dictionary updated.
    :return: Updated dictionary
    """
    role_dict = {}
    for x in all_roles_in_game:
        role_dict[x] = 0
    for player in team[0]:
        for role in player[3]:
            role_dict[role] = (role_dict[role] + 1)
    return role_dict


def create_teams(player_list, max_team_size, all_roles_in_game, rank_depreciation):
    """
    Main method for creating teams, will take in all non-substitute players and will create as many teams as possible with those players
    :param rank_depreciation:
    :param max_team_size:
    :param all_roles_in_game:
    :param player_list: List of all players excluding those that want to be substitutes.
    :return: List of team tuples without substitutes.
    """
    teams = []
    while len(player_list) >= max_team_size:
        team = [[player_list[0]], player_list[0][1], [], {}, [0]]
        while len(team[0]) < max_team_size:
            team[1] = average_rank(team[0])
            team[3] = update_dictionary(team, all_roles_in_game)
            matrix = average_matrix(create_matrix(player_list, team, all_roles_in_game, rank_depreciation))
            next_player = get_highest_compatible_player(matrix, team, player_list)
            team[0].append(next_player)
            team[4].append(player_list.index(next_player))
        teams.append(team)
        for player in team[0]:
            player_list.remove(player)
    return teams


def average_rank(player_list):
    """
    Takes in a team and calculates the average rank of the team, used for find the most suitable team for substitutes.
    :param player_list: List of all players in a team.
    :return: The average rank of a team.
    """
    return (sum([item[1] for item in player_list])) / len(player_list)


def get_highest_compatible_player(matrix, team, player_list):
    """
    Picks the player with the highest compatibility factor with all players in the team form the list of players not currently in the team.
    This way a player won't be picked because they are compatible with one player but are compatible with the entire team.
    :param matrix: The compatibility matrix created by the players.
    :param team: The team that you want to check compatibility against.
    :param player_list: List of all players including those that want to be substitutes.
    :return: Player to be added to the team.
    """
    check = []
    for posn in team[4]:
        check.append(matrix[posn])
    new_list = [sum(x) for x in zip(*check)]
    for posn in team[4]:
        new_list[posn] = -1
    return player_list[new_list.index(max(new_list))]


def create_matrix(player_list, team, all_roles_in_game, rank_depreciation):
    """
    Creates a matrix of compatibility values between all players.
    e.g. The value matrix[i][j] is the compatibility value between player i and j.
    :param rank_depreciation:
    :param all_roles_in_game:
    :param player_list: List of all players including those that want to be substitutes.
    :param team: Team that is currently in the process of having a player added, this is so roles can be taken into account.
    :return: Compatibility matrix
    """
    matrix = [[int for i in range(len(player_list))] for j in range(len(player_list))]
    for x in range(len(player_list)):
        for y in range(len(player_list)):
            matrix[x][y] = compatibility_value(player_list[x], player_list[y], team, all_roles_in_game, rank_depreciation)
    return matrix


def average_matrix(matrix):
    """
    Averages the values in the matrix across the y=-x plane. Doesn't fully average only adds values [i][j] and [j][i] as you don't need to divide all values by two as all values would be divided by two.
    This is because matrix[i][j] and matrix[j][i] talk about the same two players however there can be differences between [i][j] and [j][i]
    :param matrix: The matrix you want to average the values of.
    :return: Matrix with values [i][j] and [j][i] added together.
    """
    for x in range(len(matrix)):
        y = x + 1
        while y < len(matrix):
            matrix[x][y] = matrix[x][y] + matrix[y][x]
            matrix[y][x] = matrix[x][y]
            y += 1
    return matrix


def compatibility_value(player_one, player_two, team, all_roles_in_game, rank_depreciation):
    """
    Calculates the compatibility between two players, uses other functions to get individual values so more values can be added easily and weightings can be changed.
    :param rank_depreciation:
    :param all_roles_in_game:
    :param player_one: First player you want to check
    :param player_two: Second player you want to check
    :param team: Team that is currently in the process of having a player added, this is so roles can be taken into account.
    :return: Compatibility value between player one and player two.
    """
    if player_one[0] == player_two[0]:
        return -1
    return (5 * check_compatible_role(player_one, player_two, team, all_roles_in_game)) + (
            4 * want_to_play(player_one, player_two)) + (3 * check_attitude(player_one, player_two)) + (
                   2 * rank_difference_compatibility(player_one, player_two, rank_depreciation)) + (
                   1 * availability_compatibility(player_one, player_two, False))


def simulate_change(player, team, all_roles_in_game):
    """
    Simulates how the role dictionary will change if player is added to team. This aims to equalise roles in the team role dictionary.
    e.g. For dictionary {"a": 1, "b": 2, "c": 1}, player roles ["a", "c"] > ["a"] | ["c"] > ["a", "b"] | ["b", "c"] etc. so ideally in the end the dictionary would be even.
    :param all_roles_in_game:
    :param player: Player you want to simulate adding to the team
    :param team: Team you want to simulate adding to.
    :return: Value difference adding a player will make to the dictionary.
    e.g. For dictionary {"a": 1, "b": 2, "c": 1}, if player with roles ["a"] joins it will result with dictionary {"a": 2, "b": 2, "c": 1}.
    Since maximum value = 2, the diff will be (2 - 2) + (2 - 2) + (2 - 1) = 1 so it will return 9-1/9 = 8/9.
    (Number of roles is 3 as dictionary will always show all roles even if no one has them in the team.)
    For dictionary {"a": 1, "b": 2, "c": 1}, if player with roles ["a", "c"] joins it will result with dictionary {"a": 2, "b": 2, "c": 2}.
    Since maximum value = 2, the diff will be (2 - 2) + (2 - 2) + (2 - 2) = 2 so it will return 9-0/9 = 1.
    So players that can better even out the dictionary will be more valuable and have a higher compatibility.
    """
    team.append(player)
    dictionary = update_dictionary(team, all_roles_in_game)
    maximum_value = dictionary.get(max(dictionary, key=lambda key: dictionary[key]))
    diff = 0
    for x in dictionary.keys():
        diff += maximum_value - dictionary[x]
    if diff > 3 * len(all_roles_in_game):
        return 0
    return (3 * len(all_roles_in_game) - diff) / 3 * len(all_roles_in_game)


def check_compatible_role(player_one, player_two, team, all_roles_in_game):
    """
    Checks to see compatibility of roles between two players. If there are no roles or both are either in or not in the team then return 0 as only one can join at a time.
    :param all_roles_in_game:
    :param player_one: First player you want to check
    :param player_two: Second player you want to check
    :param team: Team that one person could potentially join.
    :return: Compatibility based on the roles of two players. Float {0 <= x <= 1}
    """
    if not all_roles_in_game:
        return 0
    if (player_one in team[0]) & (player_two in team[0]):
        return 0
    if (player_one not in team[0]) & (player_two not in team[0]):
        return 0
    if (player_one in team[0]) & (player_two not in team[0]):
        return simulate_change(player_two, team, all_roles_in_game)
    if (player_one not in team[0]) & (player_two in team[0]):
        return simulate_change(player_one, team, all_roles_in_game)


def want_to_play(player_one, player_two):
    """
    Checks if player_one wants to play with player_two
    :param player_one: First player you want to check
    :param player_two: Second player you want to check
    :return: Compatibility based on whether a player wants to play with another.
    """
    if player_two[0] in player_one[2]:
        return 1
    return 0


def check_attitude(player_one, player_two):
    """
    Gets compatibility based on how two players want to play, if 0 a player wants to take it more relaxed, if 1 then they want to take it seriously.
    :param player_one: First player you want to check
    :param player_two: Second player you want to check
    :return: Compatibility based on attitude to playing.
    """
    if player_one[4] == player_two[4]:
        return 1
    return 0


def rank_difference_compatibility(player_one, player_two, rank_depreciation):
    """
    Gets compatibility based on the difference in rank between two players. This is on a depreciating factor which can be altered by changing rank_depreciation.
    :param rank_depreciation:
    :param player_one: First player you want to check
    :param player_two: Second player you want to check
    :return: Compatibility based on rank difference between two players.
    """
    difference = abs(player_one[1] - player_two[1])
    if difference > rank_depreciation:
        return 0
    return 1 - (difference / rank_depreciation)


def availability_compatibility(player_one, player_two, one_off):
    """
    Gets compatibility based on what the players want to play, so one player might only be able to play weekends whilst another might only be able to play weekdays so there will not be compatible at all.
    :param player_one: First player you want to check
    :param player_two: Second player you want to check
    :param one_off: Boolean to see if team is a one off team so will only play a single game.
    :return: Compatibility based on availability.
    """
    return 0


def unused_players(teams, player_list):
    """
    Gets a list of players that weren't used in creating teams as there's a good chance that not all players can be fit into teams. Such as teams of 5 but 16 players apply.
    :param teams: List of all full teams without subs.
    :param player_list: List of all players including those that want to be substitutes.
    :return: List of players not used in creating teams that didn't want to be substitutes.
    """
    used_players = []
    for team in teams:
        for player in team[0]:
            used_players.append(player)
    return [x for x in player_list if x not in used_players]


def output_to_csv(teams):
    """
    Outputs the finished teams and subs to a CSV file. Currently outputs to the same location as this python file.
    :param teams: List of all teams
    :return:
    """
    name = "test_output_" + str(round(time.time() * 1000)) + ".csv"
    team_cond = condense_teams(teams)
    with open(name, mode='w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        csv_writer.writerow(["Players", "Substitutes"])
        for x in team_cond:
            csv_writer.writerow(x)


def condense_teams(teams):
    """
    Takes away data in team tuple only used for creating team so out put is only the players and the subs.
    :param teams: List of all complete team tuples.
    :return: List of team tuples of just the player names of the players and substitutes.
    """
    team_cond = []
    for x in teams:
        team_cond.append([x[0], x[2]])
    for n in team_cond:
        n[0] = [i[0] for i in n[0]]
        n[1] = [i[0] for i in n[1]]
    return team_cond


def read_csv():
    """
    Reads a CSV of players.
    :return: List of player tuples.
    """
    filename = askopenfilename()
    player_list = []
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line = 0
        for row in csv_reader:
            if line != 0:
                player = (
                    row[0], int(row[1]), parse_empty_list(row[2].split("|")), parse_empty_list(row[3].split("|")),
                    int(row[4]), int(row[5]), parse_bool(row[6]))
                player_list.append((player, (line - 1)))
            line += 1
    return player_list


def parse_bool(input_bool):
    """
    Parses string boolean into Boolean.
    :param input_bool: String of either "True" or "False"
    :return: Returns Boolean
    """
    return input_bool == "True"


def parse_empty_list(input_list):
    """
    Parses an "empty list" as read from the CSV into an actual empty list. When reading an empty list it returns [''] instead of just [].
    :param input_list: A list that could be empty.
    :return: [] if the list should be empty otherwise input_list.
    """
    if input_list == ['']:
        return []
    return input_list


def print_matrix(matrix):
    """
    Prints the compatibility matrix, used more for testing.
    :param matrix: Matrix you want to print.
    :return:
    """
    for n in matrix:
        print(n)


def wait_for_message(bot: discord.Client, ctx: commands.Context) -> discord.Message:
    try:
        response = bot.wait_for('message', check=lambda message: message.author == ctx.author)
        return response
    except Exception:
        response = None
        return response


def start_team_making(game_role, team_size, role_list, is_one_off, deadline):
    print(game_role.content)
    print(team_size.content)
    print(role_list.content)
    print(is_one_off.content)
    print(deadline.content)


class TeamMaking(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def create_team(self):
        sub_list = get_subs(self.player_list)
        players_list = [player for player in self.player_list if player not in sub_list]
        teams = create_teams(players_list, self.all_roles_in_game, self.rank_depreciation)
        sub_list + unused_players(teams, players_list)
        teams = add_subs(teams, sub_list)
        output_to_csv(teams)

    def main(self):
        self.old_main()

    @commands.command(name="startTeamMaking", aliases=["start_team_making_command"])
    @commands.check(KoalaBot.is_admin)
    async def start_team_making_command(self, ctx):

        try:
            await ctx.channel.send("What game do you want to make teams for?")
            game_role = await wait_for_message(self.bot, ctx)

            await ctx.channel.send("How large are each teams?")
            team_size = await wait_for_message(self.bot, ctx)

            await ctx.channel.send("What roles are in the game? (can be none)")
            role_list = await wait_for_message(self.bot, ctx)

            await ctx.channel.send("Is this a one off set of teams?")
            is_one_off = await wait_for_message(self.bot, ctx)

            await ctx.channel.send("When do you want the deadline to be for?")
            deadline = await wait_for_message(self.bot, ctx)

            await IndividualGameTeamMaking(self.bot, game_role, team_size, role_list, is_one_off, deadline).start_making()

        except asyncio.TimeoutError:
            return await ctx.channel.send("Timeout has occurred, please restart")


class IndividualGameTeamMaking:

    def __init__(self, bot, game_role, team_size, role_list, is_one_off, deadline):
        self.bot = bot
        self.game_role = game_role
        self.team_size = team_size
        self.role_list = role_list
        self.is_one_off = is_one_off
        self.deadline = deadline

    async def start_making(self):
        await self.hi(self, self.game_role.guild)

    @KoalaBot.client.command()
    async def hi(self, ctx):
        role_list = ctx.roles
        for i in role_list:
            if i.name == "Founder":
                n = i.members[0]
                await n.send("This is a test")
                thing = await self.bot.wait_for('message')
                print(thing)


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(TeamMaking(bot))
