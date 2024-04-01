# modules/discord_client.py
import discord
import os
import asyncio
import spacy
import time
from agentforge.utils.functions.Logger import Logger


class DiscordClient:
    # def __init__(self, channel_ids, on_message_callback):
    #     self.token = str(os.getenv('DISCORD_TOKEN'))
    #     self.intents = discord.Intents.default()
    #     self.intents.message_content = True
    #     self.client = discord.Client(intents=self.intents, max_concurrency=100)
    #     self.channels = {}
    #     self.channel_ids = channel_ids
    #     self.on_message_callback = on_message_callback
    #     self.logger = Logger('DiscordClient')
    #
    #     @self.client.event
    #     async def on_ready():
    #         print(f'\n{self.client.user} is connected.')
    #         for channel_id in channel_ids:
    #             channel = self.client.get_channel(channel_id)
    #             if channel:
    #                 self.channels[channel_id] = channel
    #             else:
    #                 print(f"Channel not found: {channel_id}")

    def __init__(self, channel_ids, on_message_callback):
        self.token = str(os.getenv('DISCORD_TOKEN'))
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.client = discord.Client(intents=self.intents, max_concurrency=100)
        self.channels = {}
        self.channel_ids = channel_ids
        self.on_message_callback = on_message_callback
        self.bot = None  # Placeholder for the Chatbot instance
        self.logger = Logger('DiscordClient')

        @self.client.event
        async def on_ready():
            self.logger.log(f'\n{self.client.user} is connected.', 'info', 'Trinity')
            for channel_id in channel_ids:
                channel = await self.client.fetch_channel(channel_id)
                if channel:
                    self.channels[channel_id] = channel
                else:
                    print(f"Channel not found: {channel_id}")

            # Now that the bot is connected, start process_channel_messages
            if self.bot:
                asyncio.create_task(self.bot.process_channel_messages())

        @self.client.event
        async def on_message(message: discord.Message):
            self.logger.log(f"On Message: {message}", 'debug', 'Trinity')
            author = message.author
            content = message.content
            channel = message.channel
            channel_id = channel.id
            timestamp = time.time()

            # Get the author's display name
            author_name = author.display_name

            # Find all user mentions in the message
            mentions = []
            for user in message.mentions:
                # Get the mentioned user's display name
                mention_name = user.display_name
                mentions.append(mention_name)
                # Replace the mention ID with the display name in the content string
                content = content.replace(f'<@!{user.id}>', f'@{mention_name}')

            # Format the mentions
            formatted_mentions = ", ".join(mentions)

            self.logger.log(f"{author_name} said: {content} in {channel}. Channel ID: {channel_id}", 'info', 'Trinity')
            self.logger.log(f"Mentions: {formatted_mentions}", 'debug', 'Trinity')
            # print(f"{author_name} said: {content} in {channel}. Channel ID: {channel_id}")
            # print(f"Mentions: {formatted_mentions}")

            if author != self.client.user:
                await self.on_message_callback(content, author_name, channel, formatted_mentions, channel_id, timestamp)

    def run(self):
        self.client.run(token=self.token)

    async def send_discord(self, message_text, channel_id):
        channel = self.channels.get(channel_id)
        if not channel:
            print(f"Channel not found: {channel_id}, updating channel reference.")
            channel = await self.client.fetch_channel(channel_id)  # Fetch and update the channel
            if channel:
                self.channels[channel_id] = channel
            else:
                print(f"Failed to fetch channel: {channel_id}")
                return

        try:
            message_chunks = self.intelligent_chunk(message_text, 0)
            for chunk in message_chunks:
                if len(chunk) > 0:  # Check if the chunk is not empty
                    await channel.send(chunk)
        except Exception as e:
            print(f"Send Error: {e}")
            await channel.send(f"Send Error: {e}")

    def intelligent_chunk(self, text, chunk_size):
        # Define the number of sentences per chunk based on the chunk_size
        sentences_per_chunk = {
            0: 5,
            1: 13,
            2: 34,
            3: 55
        }

        # Load the spacy model (you can use a different model if you prefer)
        # nlp = StorageInterface().storage_utils.return_embedding(str(text))
        # Increase the max_length limit to accommodate large texts
        nlp = spacy.blank('en')
        nlp.add_pipe('sentencizer', config={"punct_chars": None})
        nlp.max_length = 3000000

        # Tokenize the text into sentences using spacy
        doc = nlp(str(text))
        sentences = [sent.text for sent in doc.sents]

        # Determine the number of sentences per chunk based on the input chunk_size
        num_sentences = sentences_per_chunk.get(chunk_size)

        # Group the sentences into chunks with a 2-sentence overlap
        chunks = []
        i = 0
        for i in range(0, len(sentences), num_sentences):
            # while i < len(sentences):
            chunk = ' '.join(sentences[i:i + num_sentences])
            chunks.append(chunk)
            # i += num_sentences - 2  # Move the index forward by (num_sentences - 2) to create the overlap
        # print(f"Chunks: {chunks}")
        return chunks
