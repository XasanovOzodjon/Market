from . import errors
from .users import start, help, echo
from .admins import aprove
from . import groups
from . import channels

def register_handlers(dp):
    # Admin handlerlar birinchi — callback query uchun
    aprove.register_handlers(dp)

    start.register_handlers(dp)
    help.register_handlers(dp)
    echo.register_handlers(dp)
