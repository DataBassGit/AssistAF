from agentforge.agent import Agent
from Utilities.Parsers import MessageParser


class ChatAgent(Agent):
    parser = MessageParser

    def load_additional_data(self, chat_message, chat_history, user_history, memories, cognition):
        self.data['chat_message'] = chat_message['message']
        self.data['chat_history'] = chat_history
        self.data['user_history'] = user_history
        self.data['username'] = chat_message['author']
        self.data['formatted_mentions'] = chat_message['formatted_mentions']
        self.data['memories'] = memories
        self.data['response'] = cognition['generate'].get('result')
        self.data['emotion'] = cognition['thought'].get('Emotion')
        self.data['reason'] = cognition['thought'].get('Reason')
        self.data['thought'] = cognition['thought'].get('InnerThought')
        self.data['what'] = cognition['theory'].get("What", "Unknown.")
        self.data['why'] = cognition['theory'].get("Why", "Not enough information.")
        # add new messages here | message batch

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