from timepiece.sizing import valid_sizes, convert_amount, common_size
from timepiece.helpers import memoized_property

from input_algorithms.errors import BadSpecValue
from input_algorithms import spec_base as sb
from input_algorithms.dictobj import dictobj
from input_algorithms.meta import Meta

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from delfick_error import DelfickError
import aniso8601
import random

EmptyMeta = Meta.empty()

default_available_sections = {}
class a_section(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, kls):
        default_available_sections[self.name] = kls.FieldSpec()
        kls._section_name = self.name.replace("Spec", "")
        return kls

class BaseSpec(dictobj.Spec):

    def simplify(self):
        return self

    def or_with(self, other):
        raise BadSpecValue("Sorry, can't do {0} | {1}".format(self.__class__.__name__, other.__class__.__name__))

    def combine_with(self, other):
        raise BadSpecValue("Sorry, can't do {0} & {1}".format(self.__class__.__name__, other.__class__.__name__))

    @classmethod
    def using(kls, **kwargs):
        return kls.FieldSpec().normalise(EmptyMeta, kwargs)

class ssv_spec(sb.Spec):
    """Semicolon separated values"""
    def setup(self, choices=None, spec=None):
        self.spec = spec
        self.choices = choices

    def normalise_filled(self, meta, val):
        if self.choices is None:
            res = [v.strip() for v in val.split(";")]
        else:
            res = sb.listof(sb.string_choice_spec(self.choices)).normalise(meta, [v.strip() for v in val.split(";")])

        if self.spec is None:
            return res

        return sb.listof(self.spec).normalise(meta, res)

class none_spec(sb.Spec):
    def normalise(self, meta, val):
        if val is None:
            return None
        else:
            raise BadSpecValue("Expected None", got=val, meta=meta)

class JoinerSpec(sb.Spec):
    ErrorKls = DelfickError

    def normalise_filled(self, meta, val):
        section_spec = SectionSpec()
        val = sb.tuple_spec(sb.string_choice_spec(["OR", "AND"]), section_spec, section_spec).normalise(meta, val)
        typ, first, second = val
        try:
            if typ == "OR":
                return first.simplify().or_with(second.simplify())
            else:
                return first.simplify().combine_with(second.simplify())
        except self.ErrorKls as error:
            raise BadSpecValue("Failed to join", error=error)

class SectionSpec(sb.Spec):
    ErrorKls = DelfickError

    def setup(self, available_sections=None):
        if available_sections is None:
            self.available_sections = default_available_sections
        else:
            self.available_sections = available_sections

    def normalise_filled(self, meta, val):
        if isinstance(val, dictobj):
            return val

        if isinstance(val, tuple) and len(val) is 1:
            val = (val[0], {})

        val = sb.tuple_spec(
              sb.string_spec()
            , sb.dictof(
                  sb.string_spec()
                , sb.match_spec(
                      (int, sb.integer_spec())
                    , (str, sb.string_spec())
                    , (tuple, SectionSpec())
                    , (dictobj, sb.any_spec())
                    )
                )
            ).normalise(meta, val)

        if val[0] not in self.available_sections:
            raise BadSpecValue("Unknown section type", meta=meta, wanted=val[0])
        return self.available_sections[val[0]].normalise(meta, val[1])

def section_repr(self):
    return "{0}({1})".format(self.__class__._section_name, {k:v for k, v in self.items() if not k.startswith("_")})

def fieldSpecs_from(*specs):
    if len(specs) is 1:
        return specs[0].FieldSpec()
    else:
        return sb.or_spec(*[fieldSpecs_from(spec) for spec in specs])

@a_section("repeat")
class RepeatSpec(BaseSpec):
    __repr__ = section_repr
    specifies = ("repeat", )
    every = dictobj.Field(lambda: fieldSpecs_from(IntervalsSpec), default=None)
    start = dictobj.Field(lambda: fieldSpecs_from(EpochSpec, DateTimeSpec, SunRiseSpec, SunSetSpec), wrapper=sb.required)
    end = dictobj.Field(lambda: sb.or_spec(none_spec(), fieldSpecs_from(EpochSpec, DateTimeSpec, SunRiseSpec, SunSetSpec)), default=None)

    def following(self, at=None):
        if at is None:
            at = datetime.utcnow()

        if self.end and at > self.end:
            return

        if at < self.start.datetime:
            return self.start.following(at)

        if self.every:
            return self.every.following(at, self.start.datetime, self.end)

@a_section("filter")
class FilterSpec(BaseSpec):
    def __repr__(self):
        return "[{1}]".format({k:v for k, v in self.items() if not k.startswith("_")})
    specifies = ("filter", )
    minutes = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))
    hours = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))
    days = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))
    weeks = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))
    months = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))
    day_names = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))

    def repeat_amount(self):
        data = {"num": 1, "size": "minute"}
        if len(self.minutes) > 1:
            data["size"] = "minute"
        elif self.minutes:
            data["size"] = "hour"
        elif len(self.hours) > 1:
            data["size"] = "hour"
        elif self.hours:
            data["size"] = "day"
        elif len(self.days) > 1 or self.day_names:
            data["size"] = "day"
        elif self.days:
            data["size"] = "week"
        elif len(self.weeks) > 1:
            data["size"] = "week"
        elif self.weeks:
            data["size"] = "year"
        elif len(self.months) > 1:
            data["size"] = "month"
        elif self.months:
            data["size"] = "year"
        return AmountSpec.FieldSpec(data).normalise(EmptyMeta, data)

class RepeatAndFiltersSpec(BaseSpec):
    def __repr__(self):
        return "{0}{1}".format(repr(self.repeat), "".join(repr(f) for f in self.filters))
    specifies = ("repeat", "filter")
    repeat = dictobj.Field(lambda: fieldSpecs_from(RepeatSpec), wrapper=sb.required)
    filters = dictobj.Field(sb.listof(fieldSpecs_from(FilterSpec)))

    def add_filter(self, new):
        self.filters.append(new)

class ManyRepeatAndFiltersSpec(BaseSpec):
    def __repr__(self):
        return " | ".join(repr(rf) for rf in self.specs)
    specifies = ("repeat", "filter")
    specs = dictobj.Field(sb.listof(fieldSpecs_from(RepeatAndFiltersSpec)))

    def add_spec(self, spec):
        self.specs.append(spec)

    def following(self, at=None):
        if at is None:
            at = datetime.utcnow()
        return min([rf.following(at) for rf in self.specs])

@a_section("now")
class NowSpec(BaseSpec):
    __repr__ = section_repr
    specifies = ("day", "time")

    def simplify(self):
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
            if size == "second":
                start += timedelta(seconds=int(difference/num) * num)
            elif size == "minute":
                start += timedelta(minutes=int(difference/60/num) * num)
            elif size == "hour":
                start += timedelta(hours=int(difference/3600/num) * num)
            elif size == "day":
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
    @memoized_property
    def specifies(self):
        return ("duration", )
    start = dictobj.Field(lambda: fieldSpecs_from(NowSpec, EpochSpec, DateTimeSpec, DayNameSpec, DayNumberSpec, TimeSpec, SunRiseSpec, SunSetSpec, ISO8601DateOrTimeSpec), wrapper=sb.required)
    end = dictobj.Field(lambda: fieldSpecs_from(NowSpec, EpochSpec, DateTimeSpec, DayNameSpec, DayNumberSpec, TimeSpec, SunRiseSpec, SunSetSpec, ISO8601DateOrTimeSpec), default=None)

    def duration(self):
        return self.start.datetime(), self.end.datetime() if self.end is not None else self.end

    def combine_with(self, other):
        if isinstance(other, IntervalSpec):
            other = IntervalsSpec.contain(other)

        if isinstance(other, IntervalsSpec):
            return RepeatSpec.using(start=self.start, end=self.end, every=other)

        return super(BetweenSpec, self).combine_with(other)

@a_section("day_name")
class DayNameSpec(BaseSpec):
    __repr__ = section_repr
    specifies = ("day", )
    name = dictobj.Field(ssv_spec(["mon", "tues", "wed", "thur", "fri", "sat", "sun"]), wrapper=sb.required)

@a_section("day_number")
class DayNumberSpec(BaseSpec):
    __repr__ = section_repr
    specifies = ("day", )
    number = dictobj.Field(sb.integer_spec(), wrapper=sb.required)

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
