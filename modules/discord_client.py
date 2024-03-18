# discord_client.py

import discord
import os
# from agentforge.tools.IntelligentChunk import intelligent_chunk
import spacy


class DiscordClient:
    def __init__(self, channel_ids, on_message_callback):
        self.token = str(os.getenv('DISCORD_TOKEN'))
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.client = discord.Client(intents=self.intents)

        @self.client.event
        async def on_ready():
            print(f'\n{self.client.user} is connected.')
            for channel_id in channel_ids:
                channel = self.client.get_channel(channel_id)
                if channel:
                    self.channels[channel_id] = channel
                else:
                    print(f"Channel not found: {channel_id}")

        @self.client.event
        async def on_message(message):
            if message.author != self.client.user:
                await on_message_callback(message)

        self.channels = {}
        self.channel_ids = channel_ids

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
            message_text2 = self.intelligent_chunk(message_text, 0)
            for message in message_text2:
                await channel.send(message)
        except Exception as e:
            print(f"Send Error: {e}")
            await channel.send(f"Send Error: {e}")

    async def on_ready(self):
        print(f'\n{self.client.user} is connected.')
        for channel_id in self.channel_ids:
            channel = self.client.get_channel(channel_id)
            if channel:
                self.channels[channel_id] = channel
            else:
                print(f"Channel not found: {channel_id}")

    async def on_message(self, message: discord.Message):
        author = message.author
        content = message.content
        channel = message.channel
        print(f"{author} said: {content} in {channel}")
        if author != self.client.user:
            return content

    def run(self):
        self.client.run(token=self.token)

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
            chunk = '\n'.join(sentences[i:i + num_sentences])
            chunks.append(chunk)
            # i += num_sentences - 2  # Move the index forward by (num_sentences - 2) to create the overlap
        # print(f"Chunks: {chunks}")
        return chunks
