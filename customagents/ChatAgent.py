from agentforge.agent import Agent
from Utilities.Parsers import MessageParser


class ChatAgent(Agent):
    parser = MessageParser

    def load_additional_data(self, batch_messages, selected_message, chat_history, user_history, memories, cognition):
        chat_message = batch_messages[selected_message]
        self.data['new_messages'] = self.parser.format_messages(batch_messages)
        self.data['chat_history'] = chat_history
        self.data['user_history'] = user_history
        self.data['chat_message'] = chat_message['message']
        self.data['username'] = chat_message['author']
        self.data['formatted_mentions'] = chat_message['formatted_mentions']

        self.data['memories'] = memories

        self.data['emotion'] = cognition['thought'].get('Emotion')
        self.data['reason'] = cognition['thought'].get('Reason')
        self.data['thought'] = cognition['thought'].get('InnerThought')
        self.data['what'] = cognition['theory'].get("What", "Unknown.")
        self.data['why'] = cognition['theory'].get("Why", "Not enough information.")
        self.data['response'] = cognition['generate'].get('DirectResponse')
        self.data['response_commentary'] = cognition['generate'].get('OptionalReflection')
        self.data['choice'] = cognition['reflect'].get("Choice")
        self.data['reflection_reason'] = cognition['reflect'].get("Reason")
        self.data['feedback'] = cognition['reflect'].get("Feedback")

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
