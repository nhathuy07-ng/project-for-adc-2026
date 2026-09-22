import enum

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

class Experience:
    def __init__(self):
        self.orgName = ""
        self.address = ""
        self.jobTitle = ""
        self.highlightContribution = ""
        self.contributions = []
        self.startTime = ""
        self.endTime = ""

class UserInfo:
    def __init__(self):
        self.fullName: str = None
        self.location: str = None
        self.contacts: list[str] = []
        self.targetJobTitle: str = None
        self.profileURL: str = ""
        self.professionalSummary: str = "" # basic HTML tags allowed
        self.experience: list[Experience] = []
        self.skillsAndTools: list[str] = [] # one item per line, basic HTML tags allowed


"""
Single-user use
"""

class SingleUserUse:
    def __init__(self):
        self.setUp()

    def setUp(self):
        self.userInfo = UserInfo()
        self.sessionData = SessionData()

    def introductoryFlow():
        pass