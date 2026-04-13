import datetime
from django.db import transaction
from .models import Event
from core.models import Notification
from core.models import User
from decouple import config
