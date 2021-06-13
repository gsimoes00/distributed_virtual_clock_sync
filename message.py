
class Message(object):

    def __init__(self, source, destination, timestamp, message_type, content):
        self.source = source
        self.destination = destination
        self.timestamp = timestamp
        self.message_type = message_type
        self.content = content
