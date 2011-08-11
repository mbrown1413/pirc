

class BaseInterface(object):

    def __init__(self, client):
        self.client = client

    def initialize(self):
        raise NotImplementedError("This subclass must be implemented")

    def uninitialize(self):
        raise NotImplementedError("This subclass must be implemented")

    def put_text(self, text):
        raise NotImplementedError("This subclass must be implemented")

    def set_style(self, style):
        pass
