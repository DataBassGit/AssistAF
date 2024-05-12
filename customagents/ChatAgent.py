from agentforge.agent import Agent
from Utilities.Parsers import MessageParser


class ChatAgent(Agent):
    parser = MessageParser

    def load_additional_data(self):
        chosen_index = self.data['chosen_msg_index']
        chat_message = self.data['messages'][chosen_index]
        self.data['new_messages'] = self.parser.format_messages(self.data['messages'])
        # self.data['chat_history'] = chat_history
        # self.data['user_history'] = user_history
        self.data['chat_message'] = chat_message['message']
        self.data['username'] = chat_message['author']
        self.data['formatted_mentions'] = chat_message['formatted_mentions']

        # self.data['memories'] = memories

        self.data['emotion'] = self.data['cognition']['thought'].get('Emotion')
        self.data['reason'] = self.data['cognition']['thought'].get('Reason')
        self.data['thought'] = self.data['cognition']['thought'].get('InnerThought')
        self.data['what'] = self.data['cognition']['theory'].get("What", "Unknown.")
        self.data['why'] = self.data['cognition']['theory'].get("Why", "Not enough information.")
        self.data['response'] = self.data['cognition']['generate']
        self.data['response_commentary'] = self.data['cognition']['generate'].get('OptionalReflection')
        self.data['choice'] = self.data['cognition']['reflect'].get("Choice")
        self.data['reflection_reason'] = self.data['cognition']['reflect'].get("Reason")
        self.data['feedback'] = self.data['cognition']['reflect'].get("Feedback")

    def parse_result(self):
        self.logger.log(f"{self.agent_name} Results:\n{self.result}", 'debug', 'Trinity')
        try:
            result = str(self.result)
            self.result = self.parser.parse_lines(result)
            self.result['result'] = result
        except Exception as e:
            self.logger.parsing_error(self.result, e)

    def save_result(self):
        pass
