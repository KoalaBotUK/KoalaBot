class TwoWay(dict):
    """Class to because a friend was bored and wanted a better way to make a two way dict than the way I had before
    """
    def __init__(self, dict_in=None):
        super(TwoWay, self).__init__()
        if dict_in is not None:
            self.update(dict_in)

    def __delitem__(self, key):
        self.pop(self.pop(key))

    def __setitem__(self, key, value):
        # essentially this assert prevents updates to the dict if values are already set
        # which for a 1-1 mapping is reasonable imo, but you could also call __delitem__
        # if you wanted overwriting behaviour to work correctly (but it might be surprising)
        assert key not in self or self[key] == value
        super(TwoWay, self).__setitem__(key, value)
        super(TwoWay, self).__setitem__(value, key)

    def update(self, e, **f):
        for key, value in e.items():
            assert key not in self or self[key]==value
            self[key] = value

emote_reference = TwoWay({0: "1️⃣", 1: "2️⃣", 2: "3️⃣",
                               3: "4️⃣", 4: "5️⃣", 5: "6️⃣",
                               6: "7️⃣", 7: "8️⃣", 8: "9️⃣", 9: "🔟"})

class Option:
    def __init__(self, head, body):
        """
        Object holding information about an option
        :param head: the title of the option
        :param body: the description of the option
        """
        self.head = head
        self.body = body


class VoteManager:
    def __init__(self):
        """
        Manages votes for the bot
        """
        self.active_votes = {}

    def get_vote(self, ctx):
        """
        Returns a vote from a given discord context
        :param ctx: discord.Context object from a command
        :return: Relevant vote object
        """
        return self.active_votes[ctx.author.id]

    def has_active_vote(self, author_id):
        """
        Checks if a user already has an active vote somewhere
        :param author_id: the user id of the person trying to create a vote
        :return: True if they have an existing vote, otherwise False
        """
        return author_id in self.active_votes.keys()

    def create_vote(self, ctx, title):
        """
        Creates a vote object and assigns it to a users ID
        :param ctx: discord.Context object from the command
        :param title: title of the vote
        :return: the newly created Vote object
        """
        vote = Vote(title, ctx.author.id, ctx.guild.id)
        self.active_votes[ctx.author.id] = vote
        return vote

    def cancel_vote(self, author_id):
        """
        Removed a vote from the list of active votes
        :param author_id: the user who created the vote
        :return: None
        """
        self.active_votes.pop(author_id)

    def was_sent_to(self, msg_id):
        """
        Checks if a given message was sent by the bot for a vote, so it knows if it should listen for reactions on it.
        :param msg_id: the message that has been reacted on
        :return: the relevant vote for the message, if there is one
        """
        for vote in self.active_votes.values():
            if msg_id in vote.sent_to.values():
                return vote
        return None


class Vote:
    def __init__(self, title, author_id, guild_id):
        """
        An object containing methods and attributes of an active vote
        :param title: title of the vote
        :param author_id: creator of the vote
        :param guild_id: location of the vote
        """
        self.guild = guild_id
        self.id = author_id
        self.title = title

        self.target_roles = []
        self.chair = author_id
        self.target_voice_channel = None

        self.options = []

        self.sent_to = {}

    def is_ready(self):
        """
        Check if the vote is ready to be sent out
        :return: True if ready, False otherwise
        """
        return 1 < len(self.options) < 11

    def add_role(self, role_id):
        """
        Adds a target role to send the vote to
        :param role_id: target role
        :return: None
        """
        self.target_roles.append(role_id)

    def remove_role(self, role_id):
        """
        Removes target role from vote targets
        :param role_id: target role
        :return: None
        """
        self.target_roles.remove(role_id)

    def set_chair(self, chair_id):
        """
        Sets the chair of the vote to the given id
        :param chair_id: target chair
        :return: None
        """
        self.chair = chair_id

    def set_vc(self, channel_id=None):
        """
        Sets the target voice channel to a given channel id
        :param channel_id: target discord voice channel id
        :return: None
        """
        self.target_voice_channel = channel_id

    def add_option(self, option):
        """
        Adds an option to the vote
        :param option: Option object
        :return: None
        """
        self.options.append(option)

    def remove_option(self, index):
        """
        Removes an option from the vote
        :param index: the location in the list of options to remove
        :return: None
        """
        del self.options[index-1]

    def register_sent(self, user_id, msg_id):
        """
        Marks a user as having been sent a message to vote on
        :param user_id: user who was sent the message
        :param msg_id: the id of the message that was sent
        :return:
        """
        self.sent_to[user_id] = msg_id
