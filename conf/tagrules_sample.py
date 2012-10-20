

# message data from mu
#
# {'date': [20265, 23151, 0],
#  'docid': 23,
# 'flags': ['seen'],
# 'from': [('Abdó Roig-Maranges', 'abdo.roig@upc.edu')],
# 'maildir': '/All Mail',
# 'message-id': '87vcnq7es0.fsf@gmail.com',
# 'path': '/home/abdo/Projects/offlineimap-gmail/mail/All Mail/cur/1350601752_0.15371.grothendieck,U=25,FMD5=883ba13d52aa35908bd3344dc0604026:2,S',
# 'priority': 'normal',
# 'size': 1961,
# 'subject': 'Test 8',
# 'to': [(None, 'abdo.roig2@gmail.com')]}

# The class name is always TagRules
class TagRules(object):

  def __init__(self):
    super().__init__()
    # Here you can load as much external data as you want

  def get_tags(self, msg):
    # This function uses the data in msg to compute a new set of tags.
    # Can use any data prepared in __init__
    pass
