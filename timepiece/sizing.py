from input_algorithms.errors import BadSpecValue

from dateutil.relativedelta import relativedelta
from datetime import datetime

valid_sizes = ("second", "minute", "hour", "day", "week", "month", "year")

def common_size(min_size, max_size):
    if min_size not in valid_sizes or max_size not in valid_sizes:
        raise BadSpecValue("Size must be one of the valid units", first=min_size, second=max_size, valid=valid_sizes)
    return valid_sizes[min([valid_sizes.index(min_size), valid_sizes.index(max_size)])]

def convert_amount(old_size, new_size, old_num):
    now = datetime.utcnow()
    later = now + relativedelta(**{"{0}s".format(old_size): old_num})
    diff = later - now
    return getattr(diff, "{0}s".format(new_size))

