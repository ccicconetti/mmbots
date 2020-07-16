"""Simple class holding a slash command Mattermost request"""

class MattermostRequest(object):
    """
    This is what we get from Mattermost
    """
    def __init__(self, mmdata):
        """Initialize the MM request with the data from the server.

        Parameters
        ---------
            mmdata : dict
                Dictionary representing the MM fields as read from the JSON in the POST.
        """

        self.response_url = None
        self.text = None
        self.token = None
        self.channel_id = None
        self.team_id = None
        self.command = None
        self.team_domain = None
        self.user_name = None
        self.channel_name = None

        for key, value in mmdata.items():
            if key == 'response_url':
                self.response_url = value
            elif key == 'text':
                self.text = value
            elif key == 'token':
                self.token = value
            elif key == 'channel_id':
                self.channel_id = value
            elif key == 'team_id':
                self.team_id = value
            elif key == 'command':
                self.command = value
            elif key == 'team_domain':
                self.team_domain = value
            elif key == 'user_name':
                self.user_name = value
            elif key == 'channel_name':
                self.channel_name = value
