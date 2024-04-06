import re
from agentforge.utils.functions.Logger import Logger


logger = Logger(__name__)


class MessageParser:

    @staticmethod
    def parse_lines(result):
        """
        Parses a result string into a dictionary of key-value pairs.

        Parameters:
        - result (str): The result string to parse.

        Returns:
        - dict: A dictionary containing the parsed key-value pairs.
        """
        result_dict = {}
        lines = result.strip().split('\n')
        for line in lines:
            parts = line.split(':', 1)  # Only split on the first colon
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                result_dict[key] = value
        return result_dict

    @staticmethod
    def format_string(input_str):
        """
        Formats a string by enforcing specific rules (e.g., replacing certain characters).

        Parameters:
        - input_str (str): The string to format.

        Returns:
        - str: The formatted string.
        """
        # Remove leading and trailing whitespace
        input_str = input_str.strip()

        # Replace non-alphanumeric, non-underscore, non-hyphen characters with underscores
        input_str = re.sub("[^a-zA-Z0-9_-]", "_", input_str)

        # Replace consecutive periods with a single period
        while ".." in input_str:
            input_str = input_str.replace("..", ".")

        # Ensure it's not a valid IPv4 address
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', input_str):
            input_str = "a" + input_str

        # Ensure length is between 3 and 63 characters
        while len(input_str) < 3:
            input_str += input_str
        if len(input_str) > 63:
            input_str = input_str[:63]

        # Ensure it starts and ends with an alphanumeric character
        if not input_str[0].isalnum():
            input_str = "a" + input_str[1:]
        if not input_str[-1].isalnum():
            input_str = input_str[:-1] + "a"

        return input_str

    @staticmethod
    def format_history_entries(history, user_specific=False):
        """
        Formats history entries for display, improved to handle both user-specific and general history.

        Args:
            history (dict): The history dictionary containing 'documents', 'ids', and 'metadatas'.
            user_specific (bool): Flag to indicate if the history is user-specific. Defaults to False.

        Returns:
            str: Formatted history entries.
        """
        formatted_entries = []
        min_id = min(entry.get('id', 0) for entry in history.get('metadatas', [])) if user_specific else 0

        for entry in history.get('metadatas', []):
            document_id = entry.get('id', 0) - min_id
            if 'documents' in history and 0 <= document_id < len(history['documents']):
                document = history['documents'][document_id]
                timestamp = entry.get('timestamp', '')
                user = entry.get('User', '')
                formatted_entries.append(f"{timestamp} - {user}: {document}\n")

        return "\n".join(formatted_entries).strip()

    @staticmethod
    def prepare_message_format(messages: dict) -> str:
        formatted_messages = []
        for index, message in enumerate(messages):
            # Add the formatted message to the list without leading newlines
            formatted_messages.append(f"ID: {index}\n"  
                                      f"Date: {message['timestamp']}\n"  # Check if were formatting the timestamp
                                      f"Author: {message['author']}\n"
                                      f"Message: {message['message']}")
        # Join the messages with two newlines, putting newlines at the end instead of the beginning
        formatted_messages = "\n\n".join(formatted_messages).strip()
        logger.log(f"Formatted Messages:\n{formatted_messages}", 'debug', 'Trinity')
        return formatted_messages
