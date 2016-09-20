from timepiece.sections.base import a_section, BaseSpec, ssv_spec, section_repr, fieldSpecs_from
from timepiece.sizing import valid_sizes, convert_amount, common_size, Sizes
from timepiece.helpers import memoized_property
from timepiece.sections import final

from input_algorithms import spec_base as sb
from input_algorithms.dictobj import dictobj
from input_algorithms.meta import Meta

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import datetime as datetime_module
import aniso8601
import random

EmptyMeta = Meta.empty()

class Forever(BaseSpec):
    __repr__ = section_repr

@a_section("now")
class NowSpec(BaseSpec):
    __repr__ = section_repr
    specifies = ("day", "time")

    def simplify(self):
        return final.DateTimeSpec.contain(datetime.utcnow())

@a_section("amount")
class AmountSpec(BaseSpec):
    __repr__ = section_repr
    num = dictobj.Field(sb.integer_spec, wrapper=sb.required)
    size = dictobj.Field(sb.string_choice_spec(valid_sizes), wrapper=sb.required)

    def sized(self, new_size):
        current_index = valid_sizes.index(self.size)
        new_index = valid_sizes.index(new_size)
        if current_index == new_index:
            return self
        return AmountSpec.using(num=convert_amount(self.size, new_size, self.num), size=new_size)

    def interval(self, start, at, end):
        num = self.num
        size = self.size
        nxt = start
        if at > nxt:
            difference = (at - nxt).total_seconds()
            if size == Sizes.SECOND.value:
                nxt += timedelta(seconds=int(difference/num) * num)

            elif size == Sizes.MINUTE.value:
                nxt += timedelta(minutes=int(difference/60/num) * num)

            elif size == Sizes.HOUR.value:
                nxt += timedelta(hours=int(difference/3600/num) * num)

            elif size == Sizes.DAY.value:
                nxt += timedelta(days=int(difference/3600*24/num) * num)

        delta = relativedelta(**{"{0}s".format(size): num})
        while nxt <= at:
            nxt += delta

        while True:
            if nxt > start and nxt.replace(microsecond=0) <= end:
                yield nxt
            else:
                break

            nxt += delta

@a_section("interval")
class IntervalSpec(BaseSpec):
    __repr__ = section_repr
    specifies = ("interval", )
    every = dictobj.Field(lambda: fieldSpecs_from(ISO8601IntervalSpec, ISO8601DurationSpec, AmountSpec), wrapper=sb.required)

    def or_with(self, other):
        if isinstance(other, IntervalSpec):
            return final.IntervalsSpec.contain(self, other)
        elif isinstance(other, final.IntervalsSpec):
            return final.IntervalsSpec.contain(self, *other.intervals)
        return super(IntervalSpec, self).or_with(other)

    def following(self, at, start, end):
        yield from self.every.interval(start, at, end)

@a_section("range")
class RangeSpec(BaseSpec):
    __repr__ = section_repr
    specifies = ("interval", )
    min = dictobj.Field(lambda: fieldSpecs_from(AmountSpec), wrapper=sb.required)
    max = dictobj.Field(lambda: fieldSpecs_from(AmountSpec), wrapper=sb.required)

    def simplify(self):
        common = common_size(self.min.size, self.max.size)
        return AmountSpec.using(num=random.randrange(self.min.sized(common).num, self.max.sized(common).num), size=common)

@a_section("between")
class BetweenSpec(BaseSpec):
    __repr__ = section_repr
    start = dictobj.Field(lambda: fieldSpecs_from(NowSpec, EpochSpec, final.DateTimeSpec, DayNameSpec, DayNumberSpec, TimeSpec, SunRiseSpec, SunSetSpec, ISO8601DateOrTimeSpec), wrapper=sb.required)
    end = dictobj.Field(lambda: fieldSpecs_from(NowSpec, EpochSpec, final.DateTimeSpec, DayNameSpec, DayNumberSpec, TimeSpec, SunRiseSpec, SunSetSpec, ISO8601DateOrTimeSpec), default=None)

    def simplify(self):
        return final.RepeatSpec.using(start=self.start, end=self.end if self.end is not None else Forever.using())

@a_section("day_name")
class DayNameSpec(BaseSpec):
    __repr__ = section_repr
    specifies = ("day", )
    name = dictobj.Field(ssv_spec(["mon", "tues", "wed", "thur", "fri", "sat", "sun"]), wrapper=sb.required)

    def simplify(self):
        return final.FilterSpec.using(day_names=self.name)

@a_section("day_number")
class DayNumberSpec(BaseSpec):
    __repr__ = section_repr
    specifies = ("day", )
    number = dictobj.Field(sb.integer_spec(), wrapper=sb.required)

    def simplify(self):
        from timepiece.sections.final import FilterSpec
        return FilterSpec.using(day_numbers=[str(self.number)])

@a_section("time")
class TimeSpec(BaseSpec):
    __repr__ = section_repr
    specifies = ("time", )
    hour = dictobj.Field(sb.integer_spec, wrapper=sb.required)
    minute = dictobj.Field(sb.integer_spec, wrapper=sb.required)

    @memoized_property
    def time(self):
        ZERO = timedelta(0)
        class UTC(datetime_module.tzinfo):
            def utcoffset(self, dt): return ZERO
            def tzname(self, dt): return "UTC"
            def dst(self, dt): return ZERO
        return datetime_module.time(self.hour, self.minute, tzinfo=UTC())

    def combine_with(self, other):
        date = getattr(other, "date", None)
        if date is not None and getattr(other, "time", None) is None:
            dt = datetime.combine(date, self.time)
            return final.DateTimeSpec.contain(dt)
        else:
            super(TimeSpec, self).or_with(other)

@a_section("epoch")
class EpochSpec(BaseSpec):
    __repr__ = section_repr
    specifies = ("day", "time")
    epoch = dictobj.Field(sb.float_spec, wrapper=sb.required)

    def simplify(self):
        return final.DateTimeSpec.contain(self.datetime)

    @classmethod
    def contain(kls, epoch):
        return final.DateTimeSpec.contain(epoch)

    @memoized_property
    def datetime(self):
        return datetime.fromtimestamp(self.epoch)

@a_section("date")
class Date(BaseSpec):
    __repr__ = section_repr
    specifies = ("day", )
    day = dictobj.Field(sb.integer_spec, wrapper=sb.required)
    month = dictobj.Field(sb.integer_spec, wrapper=sb.required)
    year = dictobj.Field(sb.integer_spec, wrapper=sb.required)

    @memoized_property
    def date(self):
        return datetime_module.date(self.year, self.month, self.day)

    def combine_with(self, other):
        time = getattr(other, "time", None)
        if time is not None and getattr(other, "date", None) is None:
            dt = datetime_module.combine(self.date, time)
            return final.DateTimeSpec.contain(dt)
        else:
            super(TimeSpec, self).or_with(other)

@a_section("sunrise")
class SunRiseSpec(BaseSpec):
    __repr__ = section_repr
    specifies = ("day", "time")

@a_section("sunset")
class SunSetSpec(BaseSpec):
    __repr__ = section_repr
    specifies = "time"

@a_section("iso8601")
class ISO8601Spec(BaseSpec):
    __repr__ = section_repr
    type = dictobj.Field(sb.string_choice_spec(["datetime", "date", "time", "duration", "repeating_interval"]), wrapper=sb.required)
    specification = dictobj.Field(sb.string_spec(), wrapper=sb.required)

    @memoized_property
    def val(self):
        return getattr(aniso8601, "parse_{0}".format(self.type))(self.specification)
    datetime = val
    duration = val
    interval = val

    def simplify(self):
        if self.type == "repeating_interval":
            return ISO8601IntervalSpec.using(type=self.type, specification=self.specification)
        elif self.type == "duration":
            return ISO8601DurationSpec.using(type=self.type, specification=self.specification)
        else:
            return ISO8601DateOrTimeSpec.using(type=self.type, specification=self.specification)

class ISO8601DateOrTimeSpec(ISO8601Spec):
    type = dictobj.Field(sb.string_choice_spec(["datetime", "date", "time"]), wrapper=sb.required)
    specification = dictobj.Field(sb.string_spec(), wrapper=sb.required)
    _section_name = "iso8601"
    def simplify(self): return self
    @memoized_property
    def specifies(self):
        if self.type == "datetime":
            return ("day", "time")
        elif self.type == "date":
            return ("day", )
        else:
            return (self.type, )

    @property
    def day(self):
        if self.type == "time":
            return datetime.utcnow().date()
        elif self.type == "datetime":
            return self.val.date()
        else:
            return self.val

    @property
    def time(self):
        if self.type == "time":
            return self.val
        else:
            return self.val.time()

class ISO8601DurationSpec(ISO8601Spec):
    type = dictobj.Field(sb.string_choice_spec(["duration"]), wrapper=sb.required)
    specification = dictobj.Field(sb.string_spec(), wrapper=sb.required)
    _section_name = "iso8601"
    specifies = ("duration", )
    def simplify(self): return self

class ISO8601IntervalSpec(ISO8601Spec):
    type = dictobj.Field(sb.string_choice_spec(["repeating_interval"]), wrapper=sb.required)
    specification = dictobj.Field(sb.string_spec(), wrapper=sb.required)
    _section_name = "iso8601"
    specifies = ("interval", )
    def simplify(self): return self

