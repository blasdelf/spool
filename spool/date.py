from settings import Settings
from datetime import datetime
"""This can't be in timezone.py beacause it is imported by settings.py"""

def prevM(year, month):
  return datetime((year if month != 1 else year-1),
               (month-1 if month != 1 else 12), 1, 0,0,0,0, Settings.tz)
def thisM(year, month):
  return datetime(year,month,1, 0,0,0,0, Settings.tz)
def nextM(year, month):
  return datetime((year if month != 12 else year+1),
               (month+1 if month != 12 else 1), 1, 0,0,0,0, Settings.tz)
def thisY(year):
  return datetime(year, 1, 1, 0,0,0,0, Settings.tz)
def nextY(year):
  return datetime((year+1),1, 1, 0,0,0,0, Settings.tz)
