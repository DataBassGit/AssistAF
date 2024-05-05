from agentforge.utils.storage_interface import StorageInterface
from agentforge.utils.functions.Logger import Logger
from Utilities.Parsers import MessageParser


class Memory:
    def __init__(self):
        self.logger = Logger('Memory')
        self.storage = StorageInterface().storage_utils

        self.persona_file = self.storage.config.data['settings']['system'].get('Persona')
        self.persona = self.storage.config.data['personas'][self.persona_file].get('Name')

        self.parser = MessageParser
        self.response = ''
        self.message_batch = {}
        self.user_message = {}
        self.cognition = {}
        self.chosen_message_index: int = 0
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
            "Channel": str(chat_message["channel"]),
            "Categories": str(self.cognition["thought"]["Categories"])
        }

        if metadata_extra:
            metadata.update(metadata_extra)

        message = [chat_message["message"]]
        self.storage.save_memory(collection_name=collection_name, data=message, ids=memory_id, metadata=[metadata])
        self.logger.log(f"\nSaved to {collection_name}\n"
                        f"Data (Message)={message}\n"
                        f"ID={memory_id}\n"
                        f"Metadata={metadata}",
                        'debug', 'Trinity')

    async def save_category_memory(self):
        categories = self.cognition["thought"]["Categories"].split(",")
        for category in categories:
            collection_name = f"{self.persona}_{category.strip()}"
            category_collection = self.parser.format_string(collection_name)
            self.logger.log(f"Saving Category to: {category_collection}\nMessage:\n{self.user_message}",
                            'debug', 'Memory')
            await self.save_to_collection(category_collection, self.user_message, self.response)

    async def save_channel_memory(self):
        collection_name = f"{self.persona}_{self.user_message['channel']}_chat_history"
        collection_name = self.parser.format_string(collection_name)
        for index, message in enumerate(self.message_batch):
            metadata_extra = {}
            bot_response = self.response
            if index != self.chosen_message_index:
                bot_response = None
                metadata_extra = {
                    "Emotion": None,
                    "InnerThought": None,
                    "Categories": None
                }
            self.logger.log(f"Saving Channel to: {collection_name}\nMessage:\n{message}", 'debug', 'Memory')
            await self.save_to_collection(collection_name, message, bot_response, metadata_extra)

    # this also needs to be reviewed
    async def save_bot_response(self):
        message = self.user_message.copy()
        message['message'] = self.response
        message['author'] = self.persona

        collection_name = f"{self.persona}_{message['channel']}_chat_history"
        collection_name = self.parser.format_string(collection_name)
        self.logger.log(f"Saving Bot Response to: {collection_name}\nMessage:\n{message}", 'debug', 'Memory')
        await self.save_to_collection(collection_name, message, self.user_message['message'])

    async def save_user_history(self):
        collection_name = f"{self.persona}_{self.user_message['author']}_chat_history"
        collection_name = self.parser.format_string(collection_name)
        self.logger.log(f"Saving User History to: {collection_name}\nMessage:\n{self.user_message}", 'debug', 'Memory')
        await self.save_to_collection(collection_name, self.user_message, self.response)

    async def save_all_memory(self):
        await self.save_category_memory()
        await self.save_channel_memory()
        await self.save_bot_response()
        await self.save_user_history()

        # Save Journal would go here, if I had it!

    async def set_memory_info(self,   message_batch: dict, chosen_message_index: int, cognition: dict, response: str):
        self.message_batch = message_batch
        self.user_message = message_batch[chosen_message_index]
        self.cognition = cognition
        self.chosen_message_index = chosen_message_index
        self.response = response

    async def fetch_history(self, collection_name, query=None, is_user_specific=False, query_size: int = 20):
        collection_name = f"{self.persona}_{collection_name}_chat_history"
        collection_name = self.parser.format_string(collection_name)
        self.logger.log(f"Fetch History from: {collection_name}\n", 'debug', 'Memory')

        collection_size = self.storage.count_collection(collection_name)

        if collection_size == 0:
            return "No Results!"

        qsize = max(collection_size - query_size, 0)

        # Adjust the method of fetching history based on whether it's user-specific
        if is_user_specific and query:
            if qsize == 0:
                qsize = 1
            history = self.storage.query_memory(collection_name=collection_name, query=query, num_results=qsize)
            formatted_history = self.parser.format_user_specific_history_entries(history)
        else:
            filters = {"id": {"$gte": qsize}}
            history = self.storage.load_collection(collection_name=collection_name, where=filters)
            formatted_history = self.parser.format_general_history_entries(history)

        self.logger.log(f"Fetched History:\n{history}\n", 'debug', 'Memory')
        return formatted_history

    def get_current_memories(self):
        if self.current_memories:
            memories = str(self.current_memories[0])
            return memories

        return 'No Memories Found.'

    async def recall_categories(self, message, categories, num_memories_per_category: int = 10):
        self.logger.log(f"Recalling {num_memories_per_category} Memories per Category", 'debug', 'Memory')
        categories = categories.split(",")
        for category in categories:
            collection_name = f"{self.persona}_{category.strip()}"
            category_collection = self.parser.format_string(collection_name)
            self.logger.log(f"Fetching Category: {category}", 'debug', 'Memory')
            recalled_memories = self.storage.query_memory(collection_name=category_collection,
                                                          query=message,
                                                          num_results=num_memories_per_category)
            if recalled_memories:
                self.logger.log(f"Recalled Memories:\n{recalled_memories}", 'debug', 'Memory')
                memories = self.parser.format_user_specific_history_entries(recalled_memories)
                # Add recalled memories to current memories
                self.current_memories.append(memories)
                return

            self.logger.log(f"No Memories Recalled For Category: {category}", 'debug', 'Memory')

    def wipe_current_memories(self):
        self.current_memories = []
