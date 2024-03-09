from agentforge.utils.functions.UserInterface import UserInterface


class UI:

    def __init__(self):
        pass

    @staticmethod
    def send_message(layer, message):
        layer = layer
        print(message)
        pass

    @staticmethod
    def get_message():
        userinput = input("Message: ")
        print(f"User Input: {userinput}")
        return userinput
