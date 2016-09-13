from timepiece.sections.base import BaseSpec, ssv_spec, none_spec, section_repr, fieldSpecs_from
from timepiece.helpers import memoized_property
from timepiece.sections import sections

from input_algorithms import spec_base as sb
from input_algorithms.dictobj import dictobj
from input_algorithms.meta import Meta

from datetime import datetime

EmptyMeta = Meta.empty()

class RepeatSpec(BaseSpec):
    __repr__ = section_repr
    @memoized_property
    def specifies(self):
        spec = ()
        if self.every is not None:
            spec += ("repeat", )
        if self.end is not None:
            spec += ("duration", )
        if not spec:
            spec = ("once", )
        return spec
    every = dictobj.Field(lambda: fieldSpecs_from(sections.IntervalsSpec), default=None)
    start = dictobj.Field(lambda: fieldSpecs_from(sections.EpochSpec, sections.DateTimeSpec, sections.SunRiseSpec, sections.SunSetSpec), wrapper=sb.required)
    end = dictobj.Field(lambda: sb.or_spec(none_spec(), fieldSpecs_from(sections.Forever, sections.EpochSpec, sections.DateTimeSpec, sections.SunRiseSpec, sections.SunSetSpec)), default=None)

    def following(self, at=None):
        if at is None:
            at = datetime.utcnow()

        if self.end and at > self.end:
            return

        if at < self.start.datetime:
            return self.start.following(at)

        if self.every:
            return self.every.following(at, self.start.datetime, self.end)

    def duration(self):
        return self.start.datetime(), self.end.datetime() if self.end is not None else self.end

    def combine_with(self, other):
        if type(other) is FilterSpec:
            return RepeatAndFiltersSpec.using(repeat=self, filters=[other])
        elif type(other) is sections.IntervalSpec:
            return RepeatSpec.using(start=self.start, end=self.end, every=sections.IntervalsSpec.contain(other))
        elif type(other) is sections.IntervalsSpec:
            return RepeatSpec.using(start=self.start, end=self.end, every=other)
        else:
            super(RepeatSpec, self).or_with(other)

    def or_with(self, other):
        one = RepeatAndFiltersSpec.using(repeat=self)
        if type(other) is RepeatSpec:
            two = RepeatAndFiltersSpec.using(repeat=other)
            return ManyRepeatAndFiltersSpec.using(specs=[one, two])
        elif type(other) is FilterSpec:
            two = RepeatAndFiltersSpec.using(repeat=self, filters=[other])
            return ManyRepeatAndFiltersSpec.using(specs=[one, other])
        elif type(other) is sections.IntervalSpec:
            two = RepeatAndFiltersSpec.using(
                  repeat = RepeatSpec.using(start=self.start, end=self.end, every=sections.IntervalsSpec.contain(other))
                )
            return ManyRepeatAndFiltersSpec.using(specs=[one, two])
        elif type(other) is sections.IntervalsSpec:
            two = RepeatAndFiltersSpec.using(
                  repeat = RepeatSpec.using(start=self.start, end=self.end, every=other)
                )
            return ManyRepeatAndFiltersSpec.using(specs=[one, two])
        else:
            super(RepeatSpec, self).or_with(other)

class FilterSpec(BaseSpec):
    def __repr__(self):
        return "[{1}]".format(section_repr(self))
    specifies = ("filter", )
    minutes = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))
    hours = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))
    days = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))
    weeks = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))
    months = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))
    day_names = dictobj.Field(lambda: ssv_spec(["mon", "tues", "wed", "thur", "fri", "sat", "sun"]))
    day_numbers = dictobj.Field(lambda: ssv_spec(spec=sb.integer_spec()))

    def combine_with(self, other):
        if type(other) is RepeatSpec:
            return RepeatAndFiltersSpec.using(repeat=other, filters=[self]).simplify()
        elif type(other) is FilterSpec:
            kwargs = {}
            for field in self.fields:
                kwargs[field] = getattr(self, field) + getattr(other, field)
            return FilterSpec.using(**kwargs)
        elif type(other) is ManyRepeatAndFiltersSpec:
            new_specs = [RepeatAndFiltersSpec.uing(repeat=s.repeat, filters=s.filters + [self]) for s in other.specs]
            return ManyRepeatAndFiltersSpec(specs=new_specs)
        else:
            super(FilterSpec, self).combine_with(self, other)

    def is_filtered(self, at):
        raise NotImplementedError("Getting there...")

class RepeatAndFiltersSpec(BaseSpec):
    def __repr__(self):
        return "{0}{1}".format(repr(self.repeat), "".join(repr(f) for f in self.filters))
    specifies = ("repeat", "filter")
    repeat = dictobj.Field(lambda: fieldSpecs_from(RepeatSpec), wrapper=sb.required)
    filters = dictobj.Field(sb.listof(fieldSpecs_from(FilterSpec)))

    def following(self, at):
        return self.repeat.following(at)

    def is_filtered(self, at):
        return all(f.is_filtered(at) for f in self.filters)

    def simplify(self):
        return ManyRepeatAndFiltersSpec.using(specs=[self])

class ManyRepeatAndFiltersSpec(BaseSpec):
    def __repr__(self):
        return " | ".join(repr(rf) for rf in self.specs)
    specifies = ("repeat", "filter")
    specs = dictobj.Field(sb.listof(fieldSpecs_from(RepeatAndFiltersSpec)))

    def following(self, at=None):
        if at is None:
            at = datetime.utcnow()
        return min([rf.following(at) for rf in self.specs])

    def is_filtered(self, at):
        return any(rf.is_filtered(at) for rf in self.specs)
