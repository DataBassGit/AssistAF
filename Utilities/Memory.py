from agentforge.utils.storage_interface import StorageInterface
from agentforge.utils.functions.Logger import Logger
from Utilities.Parsers import MessageParser


class Memory:
    def __init__(self):
        self.logger = Logger(__name__)
        self.storage = StorageInterface().storage_utils
        self.parser = MessageParser
        self.message_batch = {}
        self.user_message = {}
        self.cognition = {}
        self.chosen_message_index: int = 0
        self.bot_response = ''

    def save_to_collection(self, collection_name: str, chat_message: dict, response_message: str, metadata_extra=None):
        collection_size = self.storage.count_collection(collection_name)
        memory_id = [str(collection_size + 1)]

        metadata = {
            "id": collection_size + 1,
            "Response": response_message,
            "Emotion": self.cognition["thought"]["Emotion"],
            "InnerThought": self.cognition["thought"]["InnerThought"],
            "User": chat_message["author"],
            "Mentions": chat_message["formatted_mentions"],
            "Channel": chat_message["channel"]
        }

        if metadata_extra:
            metadata.update(metadata_extra)

        message = [chat_message["message"]]
        self.storage.save_memory(collection_name=collection_name, data=message, ids=memory_id, metadata=[metadata])
        self.logger.log(f"Saved to {collection_name}\n"
                        f"Data (Message)={message}\n"
                        f"ID={memory_id}\n"
                        f"Metadata={metadata}",
                        'debug', 'Trinity')

    def save_category_memory(self):
        categories = self.cognition["thought"]["Categories"].split(",")
        for category in categories:
            formatted_category = self.parser.format_string(category)
            collection_name = formatted_category
            # Example updated call to save_to_collection
            self.save_to_collection(collection_name, self.user_message, self.bot_response)

    def save_channel_memory(self):
        collection_name = f"a{self.user_message['channel']}-chat_history"
        for index, message in enumerate(self.message_batch):
            metadata_extra = {}
            bot_response = self.bot_response
            if index != self.chosen_message_index:
                bot_response = None
                metadata_extra = {
                    "Emotion": None,
                    "InnerThought": None
                }
            self.save_to_collection(collection_name, message, bot_response, metadata_extra)

    # this also needs to be reviewed
    def save_bot_response(self):
        message = self.user_message
        message['message'] = self.bot_response
        message['author'] = "Trinity"  # Should be replaced with Persona name

        collection_name = f"a{message['channel']}-chat_history"
        self.save_to_collection(collection_name, message, self.user_message['message'])

    def save_user_history(self):
        collection_name = f"a{self.user_message['author']}-chat_history"
        self.save_to_collection(collection_name, self.user_message, self.bot_response)

    def save_all_memory(self):
        # Save memory to each category collection
        self.save_category_memory()

        # Save to the channel-specific collection
        self.save_channel_memory()

        # Save bot message response
        self.save_bot_response()

        # Save to user history
        self.save_user_history()

        # Save Journal would go here, if I had it!

    def set_memory_info(self, message_batch: dict, chosen_message_index: int, cognition: dict, bot_response: str):
        self.message_batch = message_batch
        self.user_message = message_batch[chosen_message_index]
        self.cognition = cognition
        self.chosen_message_index = chosen_message_index
        self.bot_response = bot_response

    # Needs to be separated into fetch channel history and fetch user history
    def fetch_history(self, collection_name, query=None, is_user_specific=False, query_size: int = 20):
        collection_name = f"a{collection_name}-chat_history"
        collection_size = self.storage.count_collection(collection_name)

        if collection_size == 0:
            return "No Results!"

        qsize = max(collection_size - query_size, 0)

        # Adjust the method of fetching history based on whether it's user-specific
        if is_user_specific and query:
            history = self.storage.query_memory(collection_name=collection_name, query=query, num_results=qsize)
        else:
            filters = {"id": {"$gte": qsize}}
            history = self.storage.load_collection(collection_name=collection_name, where=filters)

        return self.parser.format_history_entries(history, user_specific=is_user_specific)

    # Need to be reworked along with the agents
    def memory_recall(self, categories, message, count=10):
        collection_name = categories
        query = message

        new_memories = self.storage.query_memory(collection_name=collection_name, query=query, num_results=count)
        self.logger.log(f"New Memories: {new_memories}", 'debug', 'Trinity')

        # Directly extend self.memories with new_memories assuming new_memories is a list
        self.memories.extend(new_memories)
