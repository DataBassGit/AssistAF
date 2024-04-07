from agentforge.utils.storage_interface import StorageInterface
from agentforge.utils.functions.Logger import Logger
from Utilities.Parsers import MessageParser


class Memory:
    def __init__(self):
        self.logger = Logger('Memory')
        self.storage = StorageInterface().storage_utils
        self.parser = MessageParser
        self.message_batch = {}
        self.user_message = {}
        self.cognition = {}
        self.chosen_message_index: int = 0
        self.response = ''
        self.current_memories: list = []

    async def save_to_collection(self, collection_name: str, chat_message: dict, response_message: str,
                                 metadata_extra=None):
        collection_size = self.storage.count_collection(collection_name)
        memory_id = [str(collection_size + 1)]

        metadata = {
            "id": collection_size + 1,
            "Response": response_message,
            "Emotion": self.cognition["thought"].get("Emotion"),
            "InnerThought": self.cognition["thought"].get("InnerThought"),
            "Reason": self.cognition["reflect"].get("Reason"),
            "User": chat_message["author"],
            "Mentions": chat_message["formatted_mentions"],
            "Channel": str(chat_message["channel"])
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

    async def save_category_memory(self):
        categories = self.cognition["thought"]["Categories"].split(",")
        for category in categories:
            formatted_category = self.parser.format_string(category)
            await self.save_to_collection(formatted_category, self.user_message, self.response)

    async def save_channel_memory(self):
        collection_name = f"a{self.user_message['channel']}-chat_history"
        for index, message in enumerate(self.message_batch):
            metadata_extra = {}
            bot_response = self.response
            if index != self.chosen_message_index:
                bot_response = None
                metadata_extra = {
                    "Emotion": None,
                    "InnerThought": None
                }
            await self.save_to_collection(collection_name, message, bot_response, metadata_extra)

    # this also needs to be reviewed
    async def save_bot_response(self):
        message = self.user_message
        message['message'] = self.response
        message['author'] = "Trinity"  # Should be replaced with Persona name

        collection_name = f"a{message['channel']}-chat_history"
        await self.save_to_collection(collection_name, message, self.user_message['message'])

    async def save_user_history(self):
        collection_name = f"a{self.user_message['author']}-chat_history"
        await self.save_to_collection(collection_name, self.user_message, self.response)

    async def save_all_memory(self):
        await self.save_category_memory()
        await self.save_channel_memory()
        await self.save_bot_response()
        await self.save_user_history()

        # Save Journal would go here, if I had it!

    async def set_memory_info(self, message_batch: dict, chosen_message_index: int, cognition: dict, response: str):
        self.message_batch = message_batch
        self.user_message = message_batch[chosen_message_index]
        self.cognition = cognition
        self.chosen_message_index = chosen_message_index
        self.response = response

    # Needs to be separated into fetch channel history and fetch user history
    async def fetch_history(self, collection_name, query=None, is_user_specific=False, query_size: int = 20):
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

    def get_current_memories(self):
        if self.current_memories:
            return self.current_memories

        return 'No Memories Found.'

    async def recall_categories(self, message, categories, num_memories_per_category: int = 10):
        self.logger.log(f"Recalling {num_memories_per_category} Memories per Category", 'debug', 'Trinity')
        categories = categories.split(",")
        for category in categories:
            formatted_category = self.parser.format_string(category)
            self.logger.log(f"Fetching Category: {category}", 'debug', 'Trinity')
            recalled_memories = self.storage.query_memory(collection_name=formatted_category,
                                                          query=message,
                                                          num_results=num_memories_per_category)
            if recalled_memories:
                self.logger.log(f"Recalled Memories:\n{recalled_memories}", 'debug', 'Trinity')

                # Add recalled memories to current memories
                self.current_memories.extend(recalled_memories)
                return

            self.logger.log(f"No Memories Recalled For Category: {category}", 'debug', 'Trinity')

    def wipe_current_memories(self):
        self.current_memories = []
