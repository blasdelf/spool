import timezone

class Settings(object):
  tz = timezone.Pacific
  title  = "Our Spool"
  subtitle = "a chatty sort of thing"
  footer = "Does anyone look down here?"
  prefix = "spool"
  header = "spoolage"
  debug  = True
  domain = "your-app-name.appspot.com"
  urlbase = "/spool/"
  minFP = 4 #have at least this many threads on the front page
  maxFP = 8 #keep appending the prev month's until there at least this many
  atomlimit = 25    #limit on the number of threads in the atom feed
  atomfresh = False #should the atom feed be generated from recent comments?
                    #it is generated from recent threads otherwise, which is faster.
  analytics = None
