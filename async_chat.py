# chat.py
import asyncio
import os
import re

from agentforge.agents.ActionSelectionAgent import ActionSelectionAgent
from agentforge.modules.ActionExecution import Action
from agentforge.utils.function_utils import Functions
from agentforge.utils.functions.Logger import Logger
from agentforge.utils.storage_interface import StorageInterface

from customagents.ChooseAgent import ChooseAgent
from customagents.GenerateAgent import GenerateAgent
from customagents.ReflectAgent import ReflectAgent
from customagents.TheoryAgent import TheoryAgent
from customagents.ThoughtAgent import ThoughtAgent
from modules.discord_client import DiscordClient


class UI:
    def __init__(self, client):
        self.client = client
        self.channel_id_layer_0 = None
        self.channel_id_layer_1 = os.getenv('BRAIN_CHANNEL')

    async def send_message(self, layer, message):
        if layer == 0:
            channel_id = self.channel_id_layer_0
        elif layer == 1:
            channel_id = self.channel_id_layer_1
        else:
            print(f"Invalid layer: {layer}")
            return

        if channel_id:
            await self.client.send_discord(message, channel_id)
        else:
            print(f"Channel ID not set for layer {layer}")

    @staticmethod
    def get_message():
        userinput = input("Message: ")
        print(f"User Input: {userinput}")
        return userinput

    def run(self):
        self.client.run()


class Chatbot:
    storage = StorageInterface().storage_utils
    thou = ThoughtAgent()
    gen = GenerateAgent()
    theo = TheoryAgent()
    ref = ReflectAgent()
    cho = ChooseAgent()
    chat_history = None
    result = None
    parsed_data = None
    memories = None
    chat_response = None
    message = None
    cat = None
    categories = None

    def __init__(self, client):
        self.ui = UI(client)
        self.chat_history = None
        self.choice_parsed = None
        self.messages_formatted = ''
        self.action_execution = Action()
        self.action_selection = ActionSelectionAgent()
        self.selected_action = None
        self.functions = Functions()
        self.reflection = None
        self.theory = None
        self.generate = None
        self.thought = None
        self.message = None
        self.author_name = None
        self.channel = None
        self.formatted_mentions = None
        self.user_history = None
        self.channel_messages = {}
        self.processing_lock = asyncio.Lock()
        self.messages = None

        self.logger = Logger('AsyncChat')

    async def run_batch(self, messages):
        self.logger.log(f"Running Chat Loop...", 'info', 'Trinity')
        async with self.processing_lock:
            self.messages = messages
            self.logger.log(f"Message: {self.message}", 'info', 'Trinity')

            # Run Chat Manager
            for index, each_message in enumerate(self.messages):
                self.messages_formatted += f"\n\n{each_message['author']} said: {each_message['message']}\nTimestamp: {each_message['timestamp']}\nID: {index}"

            key_count = len(self.messages)
            print(self.messages)
            if key_count > 1:
                self.result = self.cho.run(messages=self.messages_formatted)
                try:
                    choice = self.parse_lines()
                    self.choice_parsed = int(choice["message_id"])
                except Exception as e:
                    self.logger.log(f"Choice Agent: Parse error - Exception: {e}\nResponse:{self.result}",
                                    'info', 'Trinity')
            else:
                self.choice_parsed = 0

            self.message = messages[self.choice_parsed]
            print(f"Message variable: {self.message['message']}")

            self.author_name = self.format_string(self.message["author"])
            self.channel = str(self.message["channel"])
            self.ui.channel_id_layer_0 = self.message["channel_id"]
            self.formatted_mentions = self.message["formatted_mentions"]

            history, user_history = await self.chatman(self.message['message'])

            # run thought agent
            await self.thought_agent(self.message['message'], history, user_history)

            # run theory agent
            await self.theory_agent(self.message['message'], history, user_history)

            # run generate agent
            await self.gen_agent(self.message['message'], history, user_history)

            # run reflect agent
            await self.reflect_agent(self.message['message'], history, user_history)

            self.memories = []

    async def thought_agent(self, message, history, user_history):
        self.logger.log(f"Running Thought Agent... Message:{message}", 'info', 'Trinity')
        self.result = self.thou.run(user_message=message,
                                    history=history,
                                    user_history=user_history,
                                    username=self.author_name,
                                    new_messages=self.messages_formatted)
        thought = f"Thought Agent:\n```\n{self.result}\n```\n"
        self.logger.log(f"{thought}", 'info', 'Trinity')

        await self.ui.send_message(1, thought)

        self.thought = self.parse_lines()
        print(f"self.thought: {self.thought}")
        self.categories = self.thought["Categories"].split(",")
        for category in self.categories:
            formatted_category = self.format_string(category)
            print(f"formatted_category: {formatted_category}")
            self.memory_recall(formatted_category, message)

    async def gen_agent(self, message, history, user_history):
        self.logger.log(f"Running Generate Response Agent... Message:{message}", 'info', 'Trinity')
        self.result = self.gen.run(user_message=message,
                                   history=history,
                                   memories=self.memories,
                                   emotion=self.thought["Emotion"],
                                   reason=self.thought["Reason"],
                                   thought=self.thought["Inner Thought"],
                                   username=self.author_name,
                                   what=self.theory["What"],
                                   why=self.theory["Why"],
                                   user_history=user_history,
                                   new_messages=self.messages_formatted)
        response = f"Generate Response Agent:\n=====\n{self.result}\n=====\n"
        self.logger.log(f"{response}", 'info', 'Trinity')
        await self.ui.send_message(1, response)
        self.generate = self.parse_lines()
        self.chat_response = self.result

    async def theory_agent(self, message, history, user_history):
        self.logger.log(f"Running Theory Agent... Message:{message}", 'info', 'Trinity')
        self.result = self.theo.run(user_message=message,
                                    history=history,
                                    username=self.author_name,
                                    user_history=user_history,
                                    new_messages=self.messages_formatted)
        theory = f"Theory Agent:\n```\n{self.result}\n```\n"
        self.logger.log(f"{theory}", 'info', 'Trinity')
        await self.ui.send_message(1, theory)
        try:
            self.theory = self.parse_lines()
        except Exception as e:
            self.logger.parsing_error(self.result, e)

    async def reflect_agent(self, message, history, user_history):
        self.logger.log(f"Running Reflect Agent... Message:{message}", 'info', 'Trinity')
        if "What" not in self.theory:
            self.theory = {"What": "Don't Know.", "Why": "Not enough information."}

        self.result = self.ref.run(user_message=message,
                                   history=history,
                                   memories=self.memories,
                                   emotion=self.thought["Emotion"],
                                   reason=self.thought["Reason"],
                                   thought=self.thought["Inner Thought"],
                                   what=self.theory["What"],
                                   why=self.theory["Why"],
                                   response=self.chat_response,
                                   username=self.author_name,
                                   user_history=user_history,
                                   new_messages=self.messages_formatted)
        reflection = f"Reflect Agent:\n```\n{self.result}\n```\n"
        self.logger.log(f"{reflection}", 'info', 'Trinity')
        await self.ui.send_message(1, reflection)
        self.reflection = self.parse_lines()

        if self.reflection["Choice"] == "respond":
            self.logger.log(f"Generated Response:{self.chat_response}", 'debug', 'Trinity')
            await self.ui.send_message(0, f"{self.chat_response}")
            self.save_memory(self.chat_response)
        elif self.reflection["Choice"] == "nothing":
            self.logger.log(f"Reason for not responding:{self.reflection['Reason']}", 'info', 'Trinity')
            await self.ui.send_message(0, f"...\n")
            self.save_memory(self.reflection["Reason"])
        else:
            new_response = self.gen.run(user_message=message,
                                        history=history,
                                        memories=self.memories,
                                        emotion=self.thought["Emotion"],
                                        reason=self.thought["Reason"],
                                        thought=self.thought["Inner Thought"],
                                        what=self.theory["What"],
                                        why=self.theory["Why"],
                                        feedback=self.reflection["Reason"],
                                        username=self.author_name,
                                        user_history=user_history,
                                        response=self.chat_response,
                                        new_messages=self.messages_formatted)
            self.logger.log(f"Sending Response:{new_response}", 'info', 'Trinity')
            await self.ui.send_message(0, f"{new_response}")
            self.save_memory(new_response)

    def save_memory(self, bot_response):
        # Existing chat history saving logic
        bot_message = f"{bot_response}"
        user_chat = f"{self.message['message']}"

        # New logic for saving to each category collection
        for category in self.categories:
            formatted_category = self.format_string(category)
            # Re-assign the values to params for each iteration
            collection_name = formatted_category
            size = self.storage.count_collection(collection_name)
            data = [str(user_chat)]
            ids = [str(size + 1)]
            metadata = [{
                "id": size + 1,
                "Character Response": bot_message,
                "EmotionalResponse": self.thought["Emotion"],
                "Inner_Thought": self.thought["Inner Thought"],
                "User": self.author_name,
                "Mentions": self.formatted_mentions,
                "Channel": self.channel
            }]
            self.storage.save_memory(collection_name=collection_name, data=data, ids=ids, metadata=metadata)
            print(f"Saved to category collection: {collection_name}")
            print(f"Data: {data}")
            print(f"IDs: {ids}")
            print(f"Metadata: {metadata}")
            print("---")

        # Save to the channel-specific collection
        for index, message in enumerate(self.messages):
            if index == self.choice_parsed:
                size = self.storage.count_collection(f"a{self.channel}-chat_history")
                collection_name = f"a{self.channel}-chat_history"
                data = [str(user_chat)]
                ids = [str(size + 1)]
                metadata = [{
                    "id": size + 1,
                    "Response": bot_message,
                    "EmotionalResponse": self.thought["Emotion"],
                    "Inner_Thought": self.thought["Inner Thought"],
                    "User": self.author_name,
                    "Mentions": self.formatted_mentions,
                    "Channel": self.channel
                }]
                self.storage.save_memory(collection_name=collection_name, data=data, ids=ids, metadata=metadata)
                print(f"Saved to channel-specific collection: {collection_name}")
                print(f"Data: {data}")
                print(f"IDs: {ids}")
                print(f"Metadata: {metadata}")
                print("---")
            else:
                size = self.storage.count_collection(f"a{self.channel}-chat_history")
                collection_name = f"a{self.channel}-chat_history"
                data = [str(user_chat)]
                ids = [str(size + 1)]
                metadata = [{
                    "id": size + 1,
                    "User": self.author_name,
                    "Mentions": self.formatted_mentions,
                    "Channel": self.channel
                }]
                self.storage.save_memory(collection_name=collection_name, data=data, ids=ids, metadata=metadata)
                print(f"Saved to channel-specific collection: {collection_name}")
                print(f"Data: {data}")
                print(f"IDs: {ids}")
                print(f"Metadata: {metadata}")
                print("---")

        # Save bot message response
        size = self.storage.count_collection(f"a{self.channel}-chat_history")
        collection_name = f"a{self.channel}-chat_history"
        data = [str(bot_message)]
        ids = [str(size + 1)]
        metadata = [{
            "id": size + 1,
            "Response": user_chat,
            "EmotionalResponse": self.thought["Emotion"],
            "Inner_Thought": self.thought["Inner Thought"],
            "User": "Trinity",
            "Mentions": self.formatted_mentions,
            "Channel": self.channel
        }]
        self.storage.save_memory(collection_name=collection_name, data=data, ids=ids, metadata=metadata)
        print(f"Saved bot message response to: {collection_name}")
        print(f"Data: {data}")
        print(f"IDs: {ids}")
        print(f"Metadata: {metadata}")
        print("---")

        # User History
        size = self.storage.count_collection(f"a{self.author_name}-chat_history")
        collection_name = f"a{self.author_name}-chat_history"
        data = [str(user_chat)]
        ids = [str(size + 1)]
        metadata = [{
            "id": size + 1,
            "Response": bot_message,
            "EmotionalResponse": self.thought["Emotion"],
            "Inner_Thought": self.thought["Inner Thought"],
            "User": self.author_name,
            "Mentions": self.formatted_mentions,
            "Channel": self.channel
        }]
        self.storage.save_memory(collection_name=collection_name, data=data, ids=ids, metadata=metadata)
        print(f"Saved to user history: {collection_name}")
        print(f"Data: {data}")
        print(f"IDs: {ids}")
        print(f"Metadata: {metadata}")
        print("---")

    async def chatman(self, message):
        # Chat History
        chat_log = ""
        size = self.storage.count_collection(f"a{self.channel}-chat_history")
        qsize = max(size - 20, 1)
        print(f"qsize: {qsize}")
        filters = {"id": {"$gte": qsize}}
        history = self.storage.load_collection(collection_name=f"a{self.channel}-chat_history", where=filters)
        print(f"history: {history}")

        if size == 0:
            chat_log = "No Results!"
        else:
            # Sort the ids list in ascending order
            sorted_ids = sorted(history['ids'], key=int)

            for document_id in sorted_ids:
                document_index = history['ids'].index(document_id)
                if 0 <= document_index < len(history['documents']):
                    document = history['documents'][document_index]
                    metadata_index = history['ids'].index(document_id)
                    if 0 <= metadata_index < len(history['metadatas']):
                        metadata = history['metadatas'][metadata_index]
                        timestamp = metadata['timestamp']
                        user = metadata['User']
                        chat_log += f"History Entry {document_id}: {document}\nTimestamp: {timestamp}\nUser:{user}\n"
                        print(f"\nHistory Entry {document_id}: {document}\nTimestamp: {timestamp}\nUser:{user}\n")
                    else:
                        print(f"Skipping metadata for document with id {document_id} as it is out of range.")
                else:
                    print(f"Skipping document with id {document_id} as it is out of range.")

        # User History
        size = self.storage.count_collection(f"a{self.author_name}-chat_history")
        qsize = max(size - 20, 1)
        user_log = ""
        print(f"qsize: {qsize}")
        user_history = self.storage.query_memory(collection_name=f"a{self.author_name}-chat_history", query=message,
                                                 num_results=qsize)
        print(f"User history: {user_history}")

        if size == 0:
            user_log = "No Results!"
        else:
            if 'metadatas' in user_history and isinstance(user_history['metadatas'], list):
                min_id = min(entry[0]['id'] for entry in user_history['metadatas'] if entry)
                for entry_list in user_history['metadatas']:
                    if entry_list:
                        entry = entry_list[0]
                        timestamp = entry.get('timestamp', '')
                        user = entry.get('User', '')
                        document_index = entry.get('id', 0) - min_id
                        if 'documents' in user_history and isinstance(user_history['documents'],
                                                                      list) and 0 <= document_index < len(
                                user_history['documents']):
                            document = user_history['documents'][document_index][0]
                            user_log += f"{timestamp} - {user} : {document}\n"
                        else:
                            print(f"Skipping document with id {entry.get('id', 0)} as it is out of range or missing.")
            else:
                print("Invalid user history format.")

        print(f"User Message: {message}\n")
        return chat_log, user_log

    def parse_lines(self):
        result_dict = {}
        lines = self.result.strip().split('\n')
        for line in lines:
            parts = line.split(':')
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                result_dict[key] = value
        return result_dict

    def memory_recall(self, categories, message, count=10):

        collection_name = categories
        query = message

        new_memories = self.storage.query_memory(collection_name=collection_name, query=query, num_results=count)
        print(f"New Memories: {new_memories}")

        if not hasattr(self, 'memories') or self.memories is None:
            self.memories = []
        self.memories.extend([new_memories])
        return self.memories

    @staticmethod
    def format_string(input_str):
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

    async def process_channel_messages(self):
        self.logger.log(f"Process Channel Messages Running...", 'debug', 'Trinity')
        while True:
            self.logger.log(f"Process Channel Messages - New Loop!", 'debug', 'Trinity')
            if self.channel_messages:
                for channel_layer_id in sorted(self.channel_messages.keys()):
                    messages = self.channel_messages.pop(channel_layer_id, None)
                    self.logger.log(f"Messages in Channel {channel_layer_id}: {messages}", 'debug', 'Trinity')
                    if messages:
                        # await self.run_batch(**channel_data)
                        await self.run_batch(messages)
                        self.logger.log(f"Run Batch Should Run Here, if i had any", 'debug', 'Trinity')
            else:
                self.logger.log(f"No Messages - Sleep Cycle", 'debug', 'Trinity')
                await asyncio.sleep(5)


async def on_message(content, author_name, channel, formatted_mentions, channel_id, timestamp):
    message_data = {
        "channel": channel,
        "channel_id": channel_id,
        "message": content,
        "author": author_name,
        "formatted_mentions": formatted_mentions,
        "timestamp": timestamp
    }
    bot.logger.log(f"Async on_message: {message_data}", 'debug', 'Trinity')
    if channel_id not in bot.channel_messages:
        bot.channel_messages[channel_id] = []

    bot.channel_messages[channel_id].append(message_data)
    bot.logger.log(f"Async on_message: done!", 'debug', 'Trinity')


if __name__ == '__main__':
    print("Starting")
    discord_client = DiscordClient([], on_message_callback=on_message)
    bot = Chatbot(discord_client)
    discord_client.bot = bot  # Set the Chatbot instance reference
    bot.ui = UI(discord_client)

    # Now, when DiscordClient's on_ready triggers, it will start process_channel_messages
    discord_client.client.run(discord_client.token)
