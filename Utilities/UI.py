import os


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
