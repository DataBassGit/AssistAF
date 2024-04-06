import asyncio

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
from Utilities.Parsers import MessageParser
from Utilities.UI import UI


class Chatbot:
    parsed_data = None
    memories = None
    chat_response = None
    cat = None
    categories = None

    def __init__(self, client):
        self.ui = UI(client)
        # self.memory = Memory()
        self.storage = StorageInterface().storage_utils
        self.parser = MessageParser
        self.chat_history = None
        self.choice_parsed = None
        self.formatted_messages = ''
        self.functions = Functions()
        self.memories = []
        self.logger = Logger('AsyncChat')
        self.processing_lock = asyncio.Lock()
        self.channel_messages = {}
        self.user_history = None
        self.result = None

        # Grouping agent-related instances into a dictionary
        self.agents = {
            "choose": ChooseAgent(),
            "reflection": ReflectAgent(),
            "theory": TheoryAgent(),
            "generate": GenerateAgent(),
            "thought": ThoughtAgent()
        }

        self.cognition = {
            "choose": dict,
            "reflection": dict,
            "theory": dict,
            "generate": str,
            "thought": dict
        }

        self.messages = None
        self.message: dict = {}

    async def run_batch(self, messages):
        self.logger.log(f"Running Batch Loop...", 'info', 'Trinity')
        async with self.processing_lock:
            self.messages = messages
            self.prepare_message_format(self.messages)
            chosen_message = self.choose_message()
            await self.process_chosen_message(chosen_message)

    def prepare_message_format(self, messages):
        formatted_messages = []
        for index, message in enumerate(messages):
            # Add the formatted message to the list without leading newlines
            formatted_messages.append(f"ID: {index}\n"  
                                      f"Date: {message['timestamp']}\n"  # Check if were formatting the timestamp
                                      f"Author: {message['author']}\n"
                                      f"Message: {message['message']}")
        # Join the messages with two newlines, putting newlines at the end instead of the beginning
        self.formatted_messages = "\n\n".join(formatted_messages).strip()
        self.logger.log(f"Formatted Messages:\n{self.formatted_messages}", 'info', 'Trinity')

    def choose_message(self):
        key_count = len(self.messages)
        if key_count > 1:
            self.result = self.agents["choose"].run(messages=self.formatted_messages)
            try:
                choice = self.parser.parse_lines(self.result)
                self.choice_parsed = int(choice["message_id"])
            except Exception as e:
                self.logger.log(f"Choice Agent - Parse error: {e}\nResponse:{self.result}", 'info', 'Trinity')
                self.choice_parsed = 0  # Default to first message if error occurs
        else:
            self.choice_parsed = 0

        selected_message = self.messages[self.choice_parsed]
        self.logger.log(f"Choice Agent Selection: {selected_message}", 'info', 'Trinity')
        return selected_message

    async def process_chosen_message(self, message):

        self.ui.channel_id_layer_0 = self.message["channel_id"]

        history, user_history = await self.chat_manager(self.message['message'])

        # Run thought agent
        await self.interact_with_agent('thought', self.message['message'], history, user_history)

        # Run theory agent
        await self.interact_with_agent('theory', self.message['message'], history, user_history)

        # Run generate agent
        await self.interact_with_agent('generate', self.message['message'], history, user_history)

        # Run reflection agent
        await self.interact_with_agent('reflection', self.message['message'], history, user_history)

        await self.handle_reflect_agent_decision()

        self.memories = []

    async def interact_with_agent(self, agent_key, message, history, user_history, additional_params=None):
        self.logger.log(f"Running {agent_key.capitalize()} Agent... Message:{message}", 'info', 'Trinity')

        def get_value_or_none(value):
            # If the value is a non-empty string, return it as is
            if isinstance(value, str) and value.strip():
                return value
            # Check for other non-empty values (including False as a meaningful boolean value)
            elif value or value is False:
                return value
            # Return None for empty strings, None values, empty lists, and empty dicts
            return None

        agent_params = {
            "user_message": get_value_or_none(message),
            "history": get_value_or_none(history),
            "user_history": get_value_or_none(user_history),
            "username": get_value_or_none(self.message.get("author")),
            "new_messages": get_value_or_none(self.formatted_messages),
            "memories": get_value_or_none(self.memories),
            # Safeguarded access to nested dict values with get_value_or_none for each nested property
            "emotion": get_value_or_none(self.cognition["thought"].get("Emotion")) if isinstance(
                self.cognition.get("thought"), dict) else None,
            "reason": get_value_or_none(self.cognition["thought"].get("Reason")) if isinstance(
                self.cognition.get("thought"), dict) else None,
            "thought": get_value_or_none(self.cognition["thought"].get("Inner Thought")) if isinstance(
                self.cognition.get("thought"), dict) else None,
            "what": get_value_or_none(self.cognition["theory"].get("What")) if isinstance(self.cognition.get("theory"),
                                                                                          dict) else None,
            "why": get_value_or_none(self.cognition["theory"].get("Why")) if isinstance(self.cognition.get("theory"),
                                                                                        dict) else None,
            "response": get_value_or_none(self.result),
        }

        if additional_params:
            agent_params.update(additional_params)

        self.logger.log(f"{agent_key.capitalize()} Agent Parameters:{agent_params}", 'debug', 'Trinity')

        self.result = self.agents[agent_key].run(**agent_params)
        if agent_key == 'thought':
            self.categories = self.parser.parse_lines(self.result)["Categories"].split(",")

        response_log = f"{agent_key.capitalize()} Agent:\n```{self.result}```\n"
        self.logger.log(response_log, 'info', 'Trinity')
        await self.ui.send_message(1, response_log)

        try:
            if agent_key == 'generate':
                self.cognition[agent_key] = self.result
                return

            self.cognition[agent_key] = self.parser.parse_lines(self.result)
        except Exception as e:
            self.logger.parsing_error(self.result, e)
            # return None

    async def handle_reflect_agent_decision(self):
        cognition = self.cognition['reflection']
        response = self.cognition['generate']
        self.logger.log(f"Handle Reflection:{cognition}", 'debug', 'Trinity')
        if self.cognition['reflection'] and "Choice" in self.cognition['reflection']:
            if cognition["Choice"] == "respond":
                # Log the decision to respond and send the generated response
                response_log = f"Generated Response:\n{response}\n"
                self.logger.log(response_log, 'debug', 'Trinity')
                await self.ui.send_message(0, response)
                # Save the response for memory
                self.save_memory(response)
            elif cognition["Choice"] == "nothing":
                # Log the decision to not respond and the reason
                self.logger.log(f"Reason for not responding:\n{cognition['Reason']}\n", 'info', 'Trinity')
                await self.ui.send_message(0, f"...\n")
                # Save the reason for not responding for memory
                self.save_memory(cognition["Reason"])
            else:
                # Handle other cases, such as possibly generating a new response based on feedback
                new_response_params = {
                    "memories": self.memories,
                    "emotion": cognition.get("Emotion", ""),
                    "reason": cognition.get("Reason", ""),
                    "thought": cognition.get("InnerThought", ""),
                    "what": cognition.get("What", ""),
                    "why": cognition.get("Why", ""),
                    "feedback": cognition.get("Reason", ""),  # Assuming feedback is based on the reason
                }
                new_response = self.agents["generate"].run(
                    user_message=self.message['message'],
                    history=cognition.get("history", ""),  # Assuming we need to pass some history
                    user_history=cognition.get("user_history", ""),  # And user history
                    response=response,
                    new_messages=self.formatted_messages,
                    **new_response_params
                )
                self.logger.log(f"Sending New Response: {new_response}", 'info', 'Trinity')
                await self.ui.send_message(0, f"{new_response}")
                self.save_memory(new_response)

    def save_to_collection(self, collection_name, response_message, chat_message, metadata_extra=None):
        data = [str(chat_message)]
        size = self.storage.count_collection(collection_name)
        ids = [str(size + 1)]
        metadata = {
            "id": size + 1,
            "Response": response_message | None,
            "Emotion": self.cognition["thought"]["Emotion"] | None,
            "InnerThought": self.cognition["thought"]["InnerThought"] | None,
            "User": self.message["author"],
            "Mentions": self.message["formatted_mentions"],
            "Channel": self.message["channel"]
        }
        if metadata_extra:
            metadata.update(metadata_extra)

        self.storage.save_memory(collection_name=collection_name, data=data, ids=ids, metadata=[metadata])
        self.logger.log(f"Saved to {collection_name}:\nData={data}\nIDs={ids}\nMetadata={metadata}", 'debug',
                        'Trinity')

    def save_category_memory(self, bot_response, user_chat):
        categories = self.cognition["thought"]["Categories"].split(",")
        for category in categories:
            formatted_category = self.parser.format_string(category)
            collection_name = formatted_category
            # Example updated call to save_to_collection
            self.save_to_collection(collection_name, bot_response, user_chat)

    # this logic needs revision - Check self messages as it might be a list of dicts
    def save_channel_memory(self, bot_response):
        collection_name = f"a{self.message['channel']}-chat_history"
        for index, message in enumerate(self.messages):
            metadata_extra = {}
            if index != self.choice_parsed:
                bot_response = None
                metadata_extra = {
                    "EmotionalResponse": None,
                    "Inner_Thought": None
                }
            # Note: Assuming user_chat is the content of the current message in self.messages being iterated
            current_user_message = str(message['message'])
            self.save_to_collection(collection_name, bot_response, current_user_message, metadata_extra)

    # this also needs to be reviewed
    def save_bot_response(self, bot_response, user_message):
        collection_name = f"a{self.message['channel']}-chat_history"
        metadata_extra = {"User": "Trinity"}
        # Example updated call to save_to_collection
        self.save_to_collection(collection_name, user_message, bot_response, metadata_extra)

    def save_user_history(self, bot_response, user_chat):
        collection_name = f"a{self.message['author']}-chat_history"
        self.save_to_collection(collection_name, bot_response, user_chat)

    def save_memory(self, bot_response):
        user_message = self.message['message']

        # Save memory to each category collection
        self.save_category_memory(bot_response, user_message)

        # Save to the channel-specific collection
        self.save_channel_memory(bot_response)

        # Save bot message response
        self.save_bot_response(bot_response, user_message)

        # Save to user history
        self.save_user_history(bot_response, user_message)

        # Save Journal would go here, if I had it!

    def fetch_history(self, collection_name, query=None, is_user_specific=False):
        """
        Fetches and formats history (either chat or user) from the storage.

        Args:
            collection_name (str): The name of the collection to fetch the history from.
            query (str, optional): The query to filter user-specific history. Defaults to None.
            is_user_specific (bool, optional): Flag to indicate if the history is user-specific. Defaults to False.

        Returns:
            str: Formatted history.
        """
        collection_name = f"a{collection_name}-chat_history"
        size = self.storage.count_collection(collection_name)
        qsize = max(size - 20, 0)

        if size == 0:
            return "No Results!"

        # Adjust the method of fetching history based on whether it's user-specific
        if is_user_specific and query:
            history = self.storage.query_memory(collection_name=collection_name, query=query, num_results=qsize)
        else:
            filters = {"id": {"$gte": qsize}}
            history = self.storage.load_collection(collection_name=collection_name, where=filters)

        return self.parser.format_history_entries(history, user_specific=is_user_specific)

    async def chat_manager(self, message):
        chat_log = self.fetch_history(message['channel'])
        user_log = self.fetch_history(message['author'], query=message['message'], is_user_specific=True)

        print(f"User Message: {message}\n")
        return chat_log, user_log

    def memory_recall(self, categories, message, count=10):
        collection_name = categories
        query = message

        new_memories = self.storage.query_memory(collection_name=collection_name, query=query, num_results=count)
        self.logger.log(f"New Memories: {new_memories}", 'debug', 'Trinity')

        # Directly extend self.memories with new_memories assuming new_memories is a list
        self.memories.extend(new_memories)

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
