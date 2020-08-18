import abc
import sqlite3


class TwitchAlertUtils:
    pass


class TwitchAlertDBInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'load_data_source') and
                callable(subclass.load_data_source) and
                hasattr(subclass, 'extract_text') and
                callable(subclass.extract_text) or
                NotImplemented)

    @abc.abstractmethod
    def load_data_source(self, path: str, file_name: str):
        """Load in the data set"""
        raise NotImplementedError

    @abc.abstractmethod
    def extract_text(self, full_file_path: str):
        """Extract text from the data set"""
        raise NotImplementedError

    @abc.abstractmethod
    def update_alert_default_message(self, new_default_message: str):
        """Extract text from the data set"""
        raise NotImplementedError

    @abc.abstractmethod
    def update_alert_default_message(self, new_default_message: str):
        """Extract text from the data set"""
        raise NotImplementedError
