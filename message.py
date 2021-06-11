
class Message(object):

    def __init__(self, source, destination, message_type, content):
        self.source = source
        self.destination = destination
        self.message_type = message_type
        self.content = content
