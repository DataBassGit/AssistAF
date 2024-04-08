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
        logger.log(f"Formatting string:\n{input_str}", 'debug', 'Formatting')
        """
        Formats a string by enforcing specific rules (e.g., replacing certain characters).

        Parameters:
        - input_str (str): The string to format.

        Returns:
        - str: The formatted string.
        """
        # Remove leading and trailing whitespace
        input_str = input_str.strip()
        logger.log(f"Remove leading and trailing whitespace:\n{input_str}", 'debug', 'Formatting')

        # Replace non-alphanumeric, non-underscore, non-hyphen characters with underscores
        input_str = re.sub("[^a-zA-Z0-9_-]", "_", input_str)
        logger.log(f"Replacing non-alphanumeric:\n{input_str}", 'debug', 'Formatting')

        # Replace consecutive periods with a single period
        while ".." in input_str:
            input_str = input_str.replace("..", ".")
            logger.log(f"Replacing consecutive periods:\n{input_str}", 'debug', 'Formatting')

        # Ensure it's not a valid IPv4 address
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', input_str):
            input_str = "a" + input_str
            logger.log(f"Ensuring not a valid IPv4:\n{input_str}", 'debug', 'Formatting')

        # Ensure it starts and ends with an alphanumeric character
        if not input_str[0].isalnum():
            input_str = "a" + input_str[1:]
            logger.log(f"Ensure it starts with an alphanumeric character:\n{input_str}", 'debug', 'Formatting')
        if not input_str[-1].isalnum():
            input_str = input_str[:-1] + "a"
            logger.log(f"Ensure it ends with an alphanumeric character:\n{input_str}", 'debug', 'Formatting')

        # Ensure length is between 3 and 64 characters
        while len(input_str) < 3:
            input_str += input_str
            logger.log(f"Ensure length is at least 3 characters:\n{input_str}", 'debug', 'Formatting')
        if len(input_str) > 63:
            input_str = input_str[:63]
            logger.log(f"Ensure length is not more than 64 characters:\n{input_str}", 'debug', 'Formatting')

        input_str = input_str.lower()
        logger.log(f"Lower casing string:\n{input_str}", 'debug', 'Formatting')

        return input_str

    @staticmethod
    def format_messages(messages):
        formatted_messages = []

        for message in messages:
            timestamp = message.get('timestamp', 'N/A')
            author = message.get('author', 'N/A')
            channel_name = message['channel'].name if 'channel' in message and hasattr(message['channel'],
                                                                                       'name') else 'N/A'
            channel_id = message.get('channel_id', 'N/A')
            message_text = message.get('message', 'N/A')

            formatted_message = (
                f"Timestamp: {timestamp}\n"
                f"Author: {author}\n"
                f"Channel: {channel_name}\n"
                f"Channel ID: {channel_id}\n"
                f"Message: \"{message_text}\"\n"
            )
            formatted_messages.append(formatted_message)

        return "\n=====\n".join(formatted_messages)

    @staticmethod
    def format_user_specific_history_entries(history):
        """
        Formats user-specific history entries for display with a dynamic format
        based on the available attributes in each entry.

        Args:
            history (dict): The history dictionary containing 'documents', 'ids', and 'metadatas'.

        Returns:
            str: Formatted user-specific history entries.
        """
        formatted_entries = []
        # Assuming metadatas is a nested list structure; adjust if it's different.
        min_id = min(entry.get('id', 0) for entry in history.get('metadatas', [[]])[0])

        for entry in history.get('metadatas', [[]])[0]:
            entry_id = entry.get('id', 0)
            document_id = entry_id - min_id
            document = ""
            if 'documents' in history and 0 <= document_id < len(history['documents'][0]):
                document = history['documents'][0][document_id]

            entry_details = []
            for key, value in entry.items():
                if key.lower() != "id":  # Optionally skip 'id'
                    entry_details.append(f"{key.capitalize()}: {value}")

            if document:
                entry_details.append(f"Message: {document}")

            formatted_entry = "\n".join(entry_details)
            formatted_entries.append(formatted_entry + "\n")

        return "=====\n".join(formatted_entries).strip()

    @staticmethod
    def format_general_history_entries(history):
        """
        Formats general history entries for display with a dynamic format based on the
        available attributes in each entry.

        Args:
            history (dict): The history dictionary containing 'documents', 'ids', and 'metadatas'.

        Returns:
            str: Formatted general history entries.
        """
        formatted_entries = []
        # Assuming metadatas is directly a list of dicts; adjust based on actual structure.
        for entry in history.get('metadatas', []):
            document_id = entry.get('id', 0) - 1  # Assuming 'id' starts from 1
            document = ""
            if 'documents' in history and 0 <= document_id < len(history['documents']):
                document = history['documents'][document_id]

            entry_details = []
            for key, value in entry.items():
                if key.lower() not in ("id", "response", "reason", "emotion", "innerthought"):
                    entry_details.append(f"{key.capitalize()}: {value}")

            if document:
                entry_details.append(f"Message: {document}")

            formatted_entry = "\n".join(entry_details)
            formatted_entries.append(formatted_entry + "\n")

        return "=====\n".join(formatted_entries).strip()

    # @staticmethod
    # def format_history_entries(history, user_specific=False):
    #     """
    #     Formats history entries for display, improved to handle both user-specific and general history
    #     with a dynamic format based on the available attributes in each entry.
    #
    #     Args:
    #         history (dict): The history dictionary containing 'documents', 'ids', and 'metadatas'.
    #         user_specific (bool): Flag to indicate if the history is user-specific. Defaults to False.
    #
    #     Returns:
    #         str: Formatted history entries.
    #     """
    #     formatted_entries = []
    #     min_id = min(entry.get('id', 0) for entry in history.get('metadatas', [])) if user_specific else None
    #
    #     for entry in history.get('metadatas', []):
    #         entry_id = entry.get('id', 0)
    #         document_id = entry_id - min_id if min_id is not None else entry_id - 1
    #         document = ""
    #         if 'documents' in history and 0 <= document_id < len(history['documents']):
    #             document = history['documents'][document_id]
    #
    #         entry_details = []
    #         for key, value in entry.items():
    #             if key.lower() != "id":  # Optionally skip 'id'
    #                 entry_details.append(f"{key.capitalize()}: {value}")
    #
    #         # Append the document as "Message"
    #         if document:
    #             entry_details.append(f"Message: {document}")
    #
    #         formatted_entry = "\n".join(entry_details)
    #         formatted_entries.append(formatted_entry + "\n")
    #
    #     return "=====\n".join(formatted_entries).strip()

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
