class AnnounceMessage:
    """
    A class consisting the information about a announcement message
    """

    def __init__(self, title, message, thumbnail):
        """
        Initiate the message with default thumbnail, title and description
        :param title: The title of the announcement
        :param message: The message included in the announcement
        :param thumbnail: The logo of the server
        """
        self.title = title
        self.description = message
        self.thumbnail = thumbnail

    def set_title(self, title):
        """
        Changing the title of the announcement
        :param title: A string consisting the title
        :return:
        """
        self.title = title

    def set_description(self, message):
        """
        Changing the message in the announcement
        :param message: A string consisting the message
        :return:
        """
        self.description = message
