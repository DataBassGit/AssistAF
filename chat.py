# chat.py

from customagents.GenerateAgent import GenerateAgent
from customagents.ReflectAgent import ReflectAgent
from customagents.TheoryAgent import TheoryAgent
from customagents.ThoughtAgent import ThoughtAgent
from agentforge.utils.storage_interface import StorageInterface
from agentforge.modules.ActionExecution import Action
from agentforge.agents.ActionSelectionAgent import ActionSelectionAgent
from agentforge.utils.function_utils import Functions
from modules.discord_client import DiscordClient
import re

CHANNEL_IDS = {
    0: 1216272137552400435,  # Output channel
    1: 1216272272990666813   # Brain channel
}


class UI:
    def __init__(self, client):
        self.client = client
        self.channel_ids = CHANNEL_IDS

    async def send_message(self, layer, message):
        channel_id = self.channel_ids.get(layer)
        if channel_id:
            await self.client.send_discord(message, channel_id)
        else:
            print(f"Invalid layer: {layer}")

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
        self.chat_history = self.storage.select_collection("chat_history")
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


    async def run(self, message, author_name, channel, formatted_mentions):
        print(message)
        self.message = message
        self.author_name = self.format_string(author_name)
        self.channel = channel
        self.formatted_mentions = formatted_mentions

        # save message to chat history
        history = await self.chatman(message)

        # run thought agent
        await self.thought_agent(message, history)

        # run generate agent
        await self.gen_agent(message, history)

        # run theory agent
        await self.theory_agent(message, history)

        # run reflect agent
        await self.reflect_agent(message, history)
        self.memories = []

    async def thought_agent(self, message, history):
        self.result = self.thou.run(user_message=message,
                                    history=history["documents"],
                                    username=self.author_name)
        await self.ui.send_message(1, f"Thought Agent:\n=====\n{self.result}\n=====\n")
        self.thought = self.parse_lines()
        print(f"self.thought: {self.thought}")
        self.categories = self.thought["Categories"].split(",")
        for category in self.categories:
            formatted_category = self.format_string(category)
            print(f"formatted_category: {formatted_category}")
            self.memory_recall(formatted_category, message)

    async def gen_agent(self, message, history):
        self.result = self.gen.run(user_message=message,
                                   history=history["documents"],
                                   memories=self.memories,
                                   emotion=self.thought["Emotion"],
                                   reason=self.thought["Reason"],
                                   thought=self.thought["Inner Thought"],
                                   username=self.author_name)
        await self.ui.send_message(1, f"Generate Agent:\n=====\n{self.result}\n=====\n")
        self.generate = self.parse_lines()
        print(f"self.thought: {self.generate}")
        self.chat_response = self.result

    async def theory_agent(self, message, history):
        self.result = self.theo.run(user_message=message,
                                    history=history["documents"],
                                    username=self.author_name)
        await self.ui.send_message(1, f"Theory Agent:\n=====\n{self.result}\n=====\n")
        self.theory = self.parse_lines()
        print(f"self.thought: {self.theory}")

    async def reflect_agent(self, message, history):
        if "What" not in self.theory:
            self.theory = {"What": "Don't Know.", "Why": "Not enough information."}

        self.result = self.ref.run(user_message=message,
                                   history=history["documents"],
                                   memories=self.memories,
                                   emotion=self.thought["Emotion"],
                                   reason=self.thought["Reason"],
                                   thought=self.thought["Inner Thought"],
                                   what=self.theory["What"],
                                   why=self.theory["Why"],
                                   response=self.chat_response,
                                   username=self.author_name)
        await self.ui.send_message(1, f"Reflect Agent:\n=====\n{self.result}\n=====\n")
        self.reflection = self.parse_lines()
        print(f"self.thought: {self.reflection}")

        if self.reflection["Choice"] == "respond":
            await self.ui.send_message(0, f"Chatbot: {self.chat_response}\n")
            self.save_memory(self.chat_response)
        elif self.reflection["Choice"] == "nothing":
            await self.ui.send_message(0, f"Chatbot: ...\n")
        else:
            new_response = self.gen.run(user_message=message,
                                        history=history["documents"],
                                        memories=self.memories,
                                        emotion=self.thought["Emotion"],
                                        reason=self.thought["Reason"],
                                        thought=self.thought["Inner Thought"],
                                        what=self.theory["What"],
                                        why=self.theory["Why"],
                                        feedback=self.reflection["Reason"],
                                        response=self.chat_response)
            await self.ui.send_message(0, f"Chatbot: {new_response}\n")
            self.save_memory(new_response)

    def save_memory(self, bot_response):
        # Existing chat history saving logic
        bot_message = f"Chatbot: {bot_response}"
        user_chat = f"User: {self.message}"

        # New logic for saving to each category collection
        for category in self.categories:
            formatted_category = self.format_string(category)
            # Re-assign the values to params for each iteration
            collection_name = formatted_category
            size = self.storage.count_collection(collection_name)
            data = [user_chat]
            ids = [str(size + 1)]
            metadata = [{
                "id": size + 1,
                "Character Response": bot_message,
                "EmotionalResponse": self.thought["Emotion"],
                "Inner_Thought": self.thought["Inner Thought"],
                "User": self.author_name,
                "Mentions": self.formatted_mentions
            }]
            self.storage.save_memory(collection_name=collection_name, data=data, ids=ids, metadata=metadata)
            print(f"Saved to category collection: {collection_name}")
            print(f"Data: {data}")
            print(f"IDs: {ids}")
            print(f"Metadata: {metadata}")
            print("---")

        # Save to the category-specific collection
        size = self.storage.count_collection(f"a{self.channel}-chat_history")
        collection_name = f"{self.channel}-chat_history"
        data = [user_chat]
        ids = [str(size + 1)]
        metadata = [{
            "id": size + 1,
            "Response": bot_message,
            "EmotionalResponse": self.thought["Emotion"],
            "Inner_Thought": self.thought["Inner Thought"],
            "User": self.author_name,
            "Mentions": self.formatted_mentions
        }]
        self.storage.save_memory(collection_name=collection_name, data=data, ids=ids, metadata=metadata)
        print(f"Saved to channel-specific collection: {collection_name}")
        print(f"Data: {data}")
        print(f"IDs: {ids}")
        print(f"Metadata: {metadata}")
        print("---")

        # Save bot message response
        collection_name = f"a{self.channel}-chat_history"
        data = [bot_message]
        ids = [str(size + 2)]
        metadata = [{
            "id": size + 1,
            "Response": user_chat,
            "EmotionalResponse": self.thought["Emotion"],
            "Inner_Thought": self.thought["Inner Thought"],
            "User": self.author_name,
            "Mentions": self.formatted_mentions
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
        data = [user_chat]
        ids = [str(size + 1)]
        metadata = [{
            "id": size + 1,
            "Response": bot_message,
            "EmotionalResponse": self.thought["Emotion"],
            "Inner_Thought": self.thought["Inner Thought"],
            "User": self.author_name,
            "Mentions": self.formatted_mentions
        }]
        self.storage.save_memory(collection_name=collection_name, data=data, ids=ids, metadata=metadata)
        print(f"Saved to user history: {collection_name}")
        print(f"Data: {data}")
        print(f"IDs: {ids}")
        print(f"Metadata: {metadata}")
        print("---")

    async def chatman(self, message):
        size = self.storage.count_collection(f"a{self.channel}-chat_history")
        qsize = max(size - 20, 1)
        print(f"qsize: {qsize}")
        filters = {"id": {"$gte": qsize}}
        history = self.storage.load_collection(collection_name=f"a{self.channel}-chat_history",where=filters)
        user_message = f"User: {message}"
        print(f"history: {history}")

        data = [user_message]
        ids = [str(size + 1)]
        metadata = [{"id": size + 1}]

        if size == 0:
            history["documents"].append("No Results!")
        # self.storage.save_memory(collection_name="chat_history", data=data, ids=ids, metadata=metadata)
        # await self.ui.send_message(0, f"User: {message}\n")
        print(f"User: {message}\n")
        return history

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

    def check_for_actions(self):
        self.select_action()

        if self.selected_action:
            self.execute_action()
        else:
            pass

    def execute_action(self):
        action_results = self.action_execution.run(action=self.selected_action, context=self.message)
        self.functions.printing.print_result(action_results, 'Action Results')

    def select_action(self):
        self.selected_action = None
        self.selected_action = self.action_selection.run(feedback=self.message)

        if self.selected_action:
            result = f"{self.selected_action['Name']}: {self.selected_action['Description']}"
            self.functions.printing.print_result(result, 'Action Selected')

    @staticmethod
    def format_action_results(action_results):
        formatted_strings = []
        for key, value in action_results.items():
            formatted_string = f"{key}: {value}\n\n---\n"
            formatted_strings.append(formatted_string)

        return "\n".join(formatted_strings).strip('---\n')


async def on_message(content, author_name, channel, formatted_mentions):
    await bot.run(content, author_name, channel, formatted_mentions)

if __name__ == '__main__':
    print("Starting")
    # Create an instance of the DiscordClient once and pass it to the UI
    discord_client = DiscordClient(CHANNEL_IDS.values(), on_message_callback=on_message)
    bot = Chatbot(discord_client)
    bot.ui = UI(discord_client)  # Pass the discord_client to the UI
    # Now, start the Discord client
    discord_client.run()