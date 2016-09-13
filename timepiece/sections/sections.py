from timepiece.sections.base import a_section, BaseSpec, ssv_spec, section_repr, fieldSpecs_from
from timepiece.sizing import valid_sizes, convert_amount, common_size, Sizes
from timepiece.helpers import memoized_property

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
        from timepiece.sections.final import RepeatSpec
        return RepeatSpec.using(start=DateTimeSpec.contain(datetime.utcnow()).simplify())

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
        if at > start:
            difference = (at - start).seconds
            if size == Sizes.SECOND.value:
                start += timedelta(seconds=int(difference/num) * num)

            elif size == Sizes.MINUTE.value:
                start += timedelta(minutes=int(difference/60/num) * num)

            elif size == Sizes.HOUR.value:
                start += timedelta(hours=int(difference/3600/num) * num)

            elif size == Sizes.DAY.value:
                start += timedelta(days=int(difference/3600*24/num) * num)

        while start < at:
            start += relativedelta(**{"{0}s".format(size): num})

        if start > start and start < end and start > at:
            return start

@a_section("interval")
class IntervalSpec(BaseSpec):
    __repr__ = section_repr
    specifies = ("interval", )
    every = dictobj.Field(lambda: fieldSpecs_from(ISO8601DurationSpec, RangeSpec, AmountSpec), wrapper=sb.required)

    def or_with(self, other):
        if isinstance(other, IntervalSpec):
            return IntervalsSpec.contain(self, other)
        elif isinstance(other, IntervalsSpec):
            return IntervalsSpec.contain(self, *other.intervals)
        return super(IntervalSpec, self).or_with(other)

    def following(self, at, start, end):
        yield from self.every.interval(start, at, end)

class IntervalsSpec(BaseSpec):
    __repr__ = section_repr
    _section_name = "Intervals"
    specifies = ("interval", )
    intervals = dictobj.Field(lambda: sb.listof(fieldSpecs_from(IntervalSpec)))

    @classmethod
    def contain(kls, *intervals):
        return kls.FieldSpec().normalise(EmptyMeta, {"intervals": list(intervals)})

    def or_with(self, other):
        if isinstance(other, IntervalsSpec):
            return IntervalsSpec.contain(*self.intervals, *other.intervals)
        elif isinstance(other, IntervalSpec):
            return IntervalsSpec.contain(*self.intervals, other)
        return super(IntervalSpec, self).or_with(other)

    def following(self, at, start, end):
        repeaters = []
        for interval in self.intervals:
            repeaters.append(interval.following(at, start, end))

        round_count = -1
        while True:
            round_count += 1
            next_round_prep = [next(r) for r in repeaters]
            next_round = [n for n in next_round_prep if n]
            if not next_round:
                break

            mn = min(next_round)
            if mn > at:
                return mn

            if round_count > 100:
                return mn

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
    start = dictobj.Field(lambda: fieldSpecs_from(NowSpec, EpochSpec, DateTimeSpec, DayNameSpec, DayNumberSpec, TimeSpec, SunRiseSpec, SunSetSpec, ISO8601DateOrTimeSpec), wrapper=sb.required)
    end = dictobj.Field(lambda: fieldSpecs_from(NowSpec, EpochSpec, DateTimeSpec, DayNameSpec, DayNumberSpec, TimeSpec, SunRiseSpec, SunSetSpec, ISO8601DateOrTimeSpec), default=None)

    def simplify(self):
        from timepiece.sections.final import RepeatSpec
        return RepeatSpec.using(start=self.start, end=self.end if self.end is not None else Forever.using())

@a_section("day_name")
class DayNameSpec(BaseSpec):
    __repr__ = section_repr
    specifies = ("day", )
    name = dictobj.Field(ssv_spec(["mon", "tues", "wed", "thur", "fri", "sat", "sun"]), wrapper=sb.required)

    def simplify(self):
        from timepiece.sections.final import FilterSpec
        return FilterSpec.using(day_names=self.name)

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

@a_section("epoch")
class EpochSpec(BaseSpec):
    __repr__ = section_repr
    specifies = ("day", "time")
    epoch = dictobj.Field(sb.float_spec, wrapper=sb.required)

    def simplify(self):
        from timepiece.sections.final import RepeatSpec
        return RepeatSpec.using(start=DateTimeSpec.contain(self.datetime))

    @classmethod
    def contain(kls, epoch):
        return DateTimeSpec.contain(epoch)

    @memoized_property
    def datetime(self):
        return datetime.fromtimestamp(self.epoch)

class DateTimeSpec(BaseSpec):
    __repr__ = section_repr
    _section_name = "Datetime"
    specifies = ("day", "time")
    datetime = dictobj.Field(sb.any_spec, wrapper=sb.required)

    @classmethod
    def contain(kls, dt):
        if isinstance(dt, float):
            dt = datetime.fromtimestamp(dt)
        return kls.FieldSpec().normalise(EmptyMeta, {"datetime": dt})

    def following(self, at=None):
        if at is None:
            at = datetime.utcnow()
        return None if at > self.datetime else self.datetime

@a_section("sunrise")
class SunRiseSpec(BaseSpec):
    __repr__ = section_repr
    specifies = ("day", "time")

    def simplify(self):
        return TimeSpec.using(hour=3, minute=0)

@a_section("sunset")
class SunSetSpec(BaseSpec):
    __repr__ = section_repr
    specifies = "time"

    def simplify(self):
        return TimeSpec.using(hour=18, minute=0)

@a_section("iso8601")
class ISO8601Spec(BaseSpec):
    __repr__ = section_repr
    @memoized_property
    def specifies(self):
        if self.type == "repeating_interval":
            return ("interval", )
        elif self.type == "datetime":
            return ("day", "time")
        elif self.type == "date":
            return ("day", )
        else:
            return (self.type, )
    type = dictobj.Field(sb.string_choice_spec(["datetime", "date", "time", "duration", "repeating_interval"]), wrapper=sb.required)
    specification = dictobj.Field(sb.string_spec(), wrapper=sb.required)

    @memoized_property
    def val(self):
        return getattr(aniso8601, "parse_{0}".format(self.type))(self.specification)
    datetime = val
    duration = val
    interval = val

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

class ISO8601DateOrTimeSpec(ISO8601Spec):
    type = dictobj.Field(sb.string_choice_spec(["datetime", "date", "time"]), wrapper=sb.required)
    specification = dictobj.Field(sb.string_spec(), wrapper=sb.required)
    _section_name = "iso8601"

class ISO8601DurationSpec(ISO8601Spec):
    type = dictobj.Field(sb.string_choice_spec(["duration"]), wrapper=sb.required)
    specification = dictobj.Field(sb.string_spec(), wrapper=sb.required)
    _section_name = "iso8601"

class ISO8601IntervalSpec(ISO8601Spec):
    type = dictobj.Field(sb.string_choice_spec(["interval"]), wrapper=sb.required)
    specification = dictobj.Field(sb.string_spec(), wrapper=sb.required)
    _section_name = "iso8601"

