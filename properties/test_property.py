from properties.property import Property
import logging


class TestProperty(Property):

    def __init__(self, name):
        super(TestProperty, self).__init__(name)

    def start(self, parameter):
        logging.info("Starting property %s with parameters: %s" % (self.name, parameter))
        self.running = True

    def stop(self):
        logging.info("Stopping property %s" % (self.name))
        self.running = False

    def status(self):
        return self.running
