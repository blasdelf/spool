from google.appengine.ext.webapp import template
from sanitize import quote, unquote
from settings import Settings
import timezone

register = template.create_template_register()

@register.filter
def tz(dt):
  """Treat a naive dt as UTC and cast to site timezone"""
  return timezone.datetime ( dt.year, dt.month, dt.day
                           , dt.hour, dt.minute, dt.second, dt.microsecond
                           , timezone.utc ).astimezone(Settings.tz)

@register.filter
def today(dt):
  """Was this dt in the last 24 hours?"""
  return timezone.datetime.utcnow() - timezone.timedelta(1) < dt

@register.filter
def name(model):
  """Return the key_name of the Model instance"""
  return model.key().name()

@register.filter
def rfc3339(dt):
  """For Atom feeds"""
  off = dt.strftime("%z")
  tz  = "Z" if not off or off == "+0000" else off[0:3]+':'+off[3:5]
  return dt.strftime('%Y-%m-%dT%H:%M:%S')+tz

@register.filter
def urlquote(s, safe='/'):
  return quote(s, safe=safe)

@register.filter
def urlunquote(s):
  return unquote(s)

@register.filter
def attr(s):
  return s.replace('"', '&quot;').replace("'", '&#39')

@register.filter
def hidden(comments):
  return len([c for c in comments if not c.upfront or c.snuffed])

@register.filter
def email(addy):
  return " | ".join(addy.replace(".", " ").split("@"))
