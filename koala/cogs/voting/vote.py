class Vote:
    def __init__(self, v_id, title, author_id, guild_id, db_manager):
        """
        An object containing methods and attributes of an active vote
        :param title: title of the vote
        :param author_id: creator of the vote
        :param guild_id: location of the vote
        """
        self.guild = guild_id
        self.id = v_id
        self.author = author_id
        self.title = title
        self.DBManager = db_manager

        self.target_roles = []
        self.chair = None
        self.target_voice_channel = None
        self.end_time = None

        self.options = []

        self.sent_to = {}

    def is_ready(self):
        """
        Check if the vote is ready to be sent out
        :return: True if ready, False otherwise
        """
        return 1 < len(self.options) < 11 and not self.sent_to

    def add_role(self, role_id):
        """
        Adds a target role to send the vote to
        :param role_id: target role
        :return: None
        """
        if self.sent_to:
            return
        self.target_roles.append(role_id)
        in_db = self.DBManager.db_execute_select("SELECT * FROM VoteTargetRoles WHERE vote_id=? AND role_id=?", (self.id, role_id))
        if not in_db:
            self.DBManager.db_execute_commit("INSERT INTO VoteTargetRoles VALUES (?, ?)", (self.id, role_id))

    def remove_role(self, role_id):
        """
        Removes target role from vote targets
        :param role_id: target role
        :return: None
        """
        if self.sent_to:
            return
        self.target_roles.remove(role_id)
        self.DBManager.db_execute_commit("DELETE FROM VoteTargetRoles WHERE vote_id=? AND role_id=?", (self.id, role_id))

    def set_end_time(self, time=None):
        """
        Sets the end time of the vote.
        :param time: time in unix time
        :return:
        """
        self.end_time = time
        self.DBManager.db_execute_commit("UPDATE votes SET end_time=? WHERE vote_id=?", (time, self.id))

    def set_chair(self, chair_id=None):
        """
        Sets the chair of the vote to the given id
        :param chair_id: target chair
        :return: None
        """
        if self.sent_to:
            return
        self.chair = chair_id
        self.DBManager.db_execute_commit("UPDATE Votes SET chair_id=? WHERE vote_id=?", (chair_id, self.id))

    def set_vc(self, channel_id=None):
        """
        Sets the target voice channel to a given channel id
        :param channel_id: target discord voice channel id
        :return: None
        """
        if self.sent_to:
            return
        self.target_voice_channel = channel_id
        self.DBManager.db_execute_commit("UPDATE Votes SET voice_id=? WHERE vote_id=?", (channel_id, self.id))

    def add_option(self, option):
        """
        Adds an option to the vote
        :param option: Option object
        :return: None
        """
        if self.sent_to:
            return
        self.options.append(option)
        in_db = self.DBManager.db_execute_select("SELECT * FROM VoteOptions WHERE opt_id=?", (option.id,))
        if not in_db:
            self.DBManager.db_execute_commit("INSERT INTO VoteOptions VALUES (?, ?, ?, ?)", (self.id, option.id, option.head, option.body))

    def remove_option(self, index):
        """
        Removes an option from the vote
        :param index: the location in the list of options to remove
        :return: None
        """
        if self.sent_to:
            return
        opt = self.options.pop(index-1)
        self.DBManager.db_execute_commit("DELETE FROM VoteOptions WHERE vote_id=? AND opt_id=?", (self.id, opt.id))

    def register_sent(self, user_id, msg_id):
        """
        Marks a user as having been sent a message to vote on
        :param user_id: user who was sent the message
        :param msg_id: the id of the message that was sent
        :return:
        """
        self.sent_to[user_id] = msg_id
        in_db = self.DBManager.db_execute_select("SELECT * FROM VoteSent WHERE vote_receiver_message=?", (msg_id,))
        if not in_db:
            self.DBManager.db_execute_commit("INSERT INTO VoteSent VALUES (?, ?, ?)", (self.id, user_id, msg_id))
