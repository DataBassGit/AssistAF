from agentforge.agent import Agent
from Utilities.Parsers import MessageParser


class ChooseAgent(Agent):
    parser = MessageParser

    def parse_result(self):
        """
        Placeholder for result parsing. Meant to be overridden by custom agents to implement specific result parsing
        logic.
        """
        self.logger.log(f"Choice Agent Result: {self.result}", 'debug', 'Trinity')
        try:
            self.result = self.parser.parse_lines(self.result)
        except Exception as e:
            self.logger.parsing_error(self.result, e)

    def build_output(self):
        """
        Constructs the output from the result. This method can be overridden by subclasses to customize the output.
        """
        self.output = int(self.result["message_id"])

    def save_result(self):
        pass
