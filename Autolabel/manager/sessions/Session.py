

class Session():
    def __init__(self, *args, **kwargs):
        #check if user_id is present in kwargs
        if 'user_id' in kwargs:
            self.user_id = kwargs['user_id']
        else:
            self.user_id = None
        