import enum
from portfolio_data_classes import ResumeInfo

"""
Class definition
"""
class ProfileType(enum.Enum):
    CV = 1
    PORTFOLIO = 2

class InteractionMode(enum.Enum):
    GUIDED = 1
    SCRIBE = 2

class SessionData:
    def __init__(self):
        self.profileType: ProfileType = None
        self.interactionMode: InteractionMode = None

"""
Single-user use
"""
class SingleUserUse:
    def __init__(self):
        self.setUp()

    def setUp(self):
        self.userInfo = ResumeInfo()
        self.sessionData = SessionData()

    def introductoryFlow():
        pass


singleUser = SingleUserUse()
