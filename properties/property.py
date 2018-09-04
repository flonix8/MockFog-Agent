

class Property(object):

    def __init__(self, name):
        self.name = name
        self.running = False

    def start(self, parameter):
        raise NotImplementedError("Abstract")

    def stop(self):
        raise NotImplementedError("Abstract")

    def status(self):
        raise NotImplementedError("Abstract")

    def update(self, parameter):
        raise NotImplementedError("Abstract")

    def __str__(self):
        return self.name

