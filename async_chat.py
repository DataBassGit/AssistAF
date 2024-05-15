import asyncio

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
from Utilities.Memory import Memory
from Utilities.UI import UI


class Chatbot:

    def __init__(self, client):
        self.logger = Logger(self.__class__.__name__)
        self.ui = UI(client)
        self.memory = Memory()
        self.functions = Functions()
        self.storage = StorageInterface().storage_utils
        self.processing_lock = asyncio.Lock()
        self.parser = MessageParser

        self.channel_messages = {}
        self.chosen_msg_index: int = 0
        self.formatted_messages: str = ''
        self.messages: dict = {}
        self.message: dict = {}
        self.chat_history = None
        self.user_history = None
        self.response: str = ''

        # Grouping agent-related instances into a dictionary
        self.agents = {
            "choose": ChooseAgent(),
            "thought": ThoughtAgent(),
            "theory": TheoryAgent(),
            "generate": GenerateAgent(),
            "reflect": ReflectAgent(),
        }

        self.cognition = {
            "choose": {},
            "thought": {},
            "theory": {},
            "generate": {},
            "reflect": {},
        }

    async def run_batch(self, messages):
        self.logger.log(f"Running Batch Loop...", 'info', 'Trinity')
        async with self.processing_lock:
            self.messages = messages
            self.formatted_messages = self.parser.prepare_message_format(messages=self.messages)
            self.choose_message()
            await self.process_chosen_message()

    def choose_message(self):
        key_count = len(self.messages)
        if key_count > 1:
            try:
                self.chosen_msg_index = self.agents["choose"].run(messages=self.formatted_messages)
            except Exception as e:
                self.logger.log(f"Choice Agent Error: {e}", 'error', 'Trinity')
                self.chosen_msg_index = 0
                # Default to first message if error occurs
        else:
            self.chosen_msg_index = 0

        self.message = self.messages[self.chosen_msg_index]
        self.logger.log(f"Choice Agent Selection: {self.message['message']}", 'info', 'Trinity')

    async def process_chosen_message(self):
        self.ui.channel_id_layer_0 = self.message["channel_id"]

        self.chat_history, self.user_history = await self.chat_manager()

        # Run Agents
        await self.run_agent('thought')
        await self.memory.recall_journal_entry(self.message['message'], self.cognition['thought']["Categories"], 3)
        await self.memory.recall_categories(self.message['message'], self.cognition['thought']["Categories"], 3)
        await self.run_agent('theory')
        await self.run_agent('generate')
        await self.run_agent('reflect')

        await self.handle_reflect_agent_decision()

        await self.save_memories()
        # write journal
        journal = await self.memory.check_journal()
        if journal:
            await self.ui.send_message(1, journal)

    async def run_agent(self, agent_name):
        self.logger.log(f"Running {agent_name.capitalize()} Agent... Message:{self.message['message']}", 'info',
                        'Trinity')

        memories = self.memory.get_current_memories()
        journals = self.memory.get_current_journals()
        agent = self.agents[agent_name]
        # agent.load_additional_data(self.messages, self.chosen_msg_index, self.chat_history,
        #                            self.user_history, memories, self.cognition)
        agent_vars = {'messages': self.messages,  # batch_messages
                      'chosen_msg_index': self.chosen_msg_index,  # selected_message
                      'chat_history': self.chat_history,  # chat_history
                      'user_history': self.user_history,  # user_history
                      'memories': memories,  # memories
                      'journals': journals,  # journals
                      'cognition': self.cognition}  # cognition
        self.cognition[agent_name] = agent.run(**agent_vars)

<<<<<<< HEAD
        # User History
        #User history is cutting off some messages due to the if/else logic at line 402.
        size = self.storage.count_collection(f"a{self.author_name}-chat_history")
        qsize = max(size - (size - 5), 1)
        user_log = ""
        print(f"qsize: {qsize}")
        user_history = self.storage.query_memory(collection_name=f"a{self.author_name}-chat_history", query=message,
                                                 num_results=qsize)
        print(f"User history: {user_history}")

        if size == 0:
            user_log = "No Results!"
        else:
            if 'metadatas' in user_history and isinstance(user_history['metadatas'], list):
                min_id = min(entry['id'] for entry in user_history['metadatas'] if entry)
                for entry_list in user_history['metadatas']:
                    if entry_list:
                        entry = entry_list
                        timestamp = entry.get('timestamp', '')
                        user = entry.get('User', '')
                        document_index = entry.get('id', 0) - min_id
                        if ('documents' in user_history and isinstance(user_history['documents'], list)
                                and 0 <= document_index < len(user_history['documents'])):
                            document = user_history['documents'][document_index]
                            user_log += f"{timestamp} - {user} : {document}\n"
                        else:
                            print(f"Skipping document with id {entry.get('id', 0)} as it is out of range or missing.")
            else:
                print("Invalid user history format.")
=======
        # Send result to Brain Channel
        result_message = f"{agent_name.capitalize()} Agent:\n```{str(self.cognition[agent_name]['result'])}```"
        await self.ui.send_message(1, result_message)

    async def handle_reflect_agent_decision(self):
        max_iterations = 2
        iteration_count = 0
>>>>>>> dev

        while True:
            iteration_count += 1
            if iteration_count > max_iterations:
                self.logger.log("Maximum iteration count reached, forcing response", 'warning', 'Trinity')
                self.cognition['reflect']['Choice'] = 'respond'

            reflection = self.cognition['reflect']
            self.response = self.cognition['generate'].get('result')
            self.logger.log(f"Handle Reflection:{reflection}", 'debug', 'Trinity')

            if "Choice" in reflection:
                if reflection["Choice"] == "respond":
                    response_log = f"Generated Response:\n{self.response}\n"
                    self.logger.log(response_log, 'debug', 'Trinity')
                    await self.ui.send_message(0, self.response)
                    break

                elif reflection["Choice"] == "nothing":
                    self.logger.log(f"Reason for not responding:\n{reflection['Reason']}\n", 'info', 'Trinity')
                    self.response = f"... (Did not respond to {self.message['author']} because {reflection['Reason']})"
                    await self.ui.send_message(0, f"...")
                    return

                elif reflection["Choice"] == "change":
                    self.logger.log(f"Changing Response:\n{self.response}\n Due To:\n{reflection['Reason']}",
                                    'info', 'Trinity')
                    await self.run_agent('generate')
                    await self.run_agent('reflect')
                    continue
            self.logger.log(f"No Choice in Reflection Response:\n{reflection}", 'error', 'Trinity')
            break

    async def save_memories(self):
        await self.memory.set_memory_info(self.messages, self.chosen_msg_index, self.cognition, self.response)
        await self.memory.save_all_memory()
        self.memory.wipe_current_memories()

    async def chat_manager(self):
        chat_log = await self.memory.fetch_history(self.message['channel'])
        user_log = await self.memory.fetch_history(self.message['author'],
                                                   query=self.message['message'],
                                                   is_user_specific=True)

        self.logger.log(f"User Message: {self.message['message']}\n", 'Info', 'Trinity')
        return chat_log, user_log

    async def process_channel_messages(self):
        self.logger.log(f"Process Channel Messages Running...", 'debug', 'Trinity')
        while True:
            # self.logger.log(f"Process Channel Messages - New Loop!", 'debug', 'Trinity')
            if self.channel_messages:
                for channel_layer_id in sorted(self.channel_messages.keys()):
                    messages = self.channel_messages.pop(channel_layer_id, None)
                    self.logger.log(f"Messages in Channel {channel_layer_id}: {messages}", 'debug', 'Trinity')
                    if messages:
                        await self.run_batch(messages)
            else:
                # self.logger.log(f"No Messages - Sleep Cycle", 'debug', 'Trinity')
                await asyncio.sleep(5)


async def on_message(content, author_name, channel, formatted_mentions, channel_id, timestamp):
    if formatted_mentions == '':
        formatted_mentions = 'No Mentions.'

    message_data = {
        "channel": str(channel),
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
