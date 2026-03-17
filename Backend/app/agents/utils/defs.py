from enum import Enum, auto

# ==================== General Definitions ==================== #

class BaseLevelTasks(Enum):
    CONVERSATION = "the user is talking to the agent in a general way."
    SCHEDULE = "When the user wants to schedule a reminder for an event/meeting/appointment/daily task, etc."
    QUERY = "When the user needs to query or aggregate data from the knowledge base for specific information."
    UPDATE = "When the user wants to update or delete an existing event/meeting/task in the knowledge base."

    def __str__(self):
        return self.name.lower()


# ==================== State (Short-term Memmory) ==================== #
class SubtaskStatus(Enum):
    """States of subtask throughout the execution"""
    NEW = auto()                # newely added
    RUNNING = auto()            # in-progress 
    WAITING = auto()            # waiting for HIL interaction
    DONE = auto()               # done successfully
    CANCELED = auto()

    def __str__(self):
        return self.name.lower()