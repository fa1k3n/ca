class ChangeConfigurationException(Exception):
    def __init__(self, msg):
        super().__init__(msg)

class TriggerMessageException(Exception):
    def __init__(self, msg):
        super().__init__(msg)

class TimeoutException(Exception):
    def __init__(self, msg):
        super().__init__(msg)
    
