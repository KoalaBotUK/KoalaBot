class Option:
    def __init__(self, head, body, opt_id):
        """
        Object holding information about an option
        :param head: the title of the option
        :param body: the description of the option
        """
        self.id = opt_id
        self.head = head
        self.body = body
