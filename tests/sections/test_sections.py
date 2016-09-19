# coding: spec

from tests.helpers import TestCase

from timepiece.sections import sections, final
from timepiece.spec import make_timepiece

from noseOfYeti.tokeniser.support import noy_sup_setUp
from input_algorithms.errors import BadSpecValue
from datetime import datetime, timedelta
from delfick_error import DelfickError
import mock
import uuid

describe TestCase, "Sections":
    describe "parsing into single objects":
        before_each:
            # Make our ErrorKls
            class ErrorKls(DelfickError):
                desc = "Something went wrong lol"
            self.ErrorKls = ErrorKls
            self.parser = make_timepiece(ErrorKls)

        describe "epoch":
            it "simplifies into a DateTimeSpec":
                epoch = datetime.utcnow() + timedelta(hours=1)
                obj = self.parser.time_spec_to_object("epoch(epoch: {0})".format(epoch.strftime("%s.%f")))

                self.assertIs(type(obj), final.DateTimeSpec)
                self.assertEqual(obj.datetime, epoch)

        describe "now":
            it "simplifies into a DateTimeSpec":
                now = datetime.utcnow() + timedelta(hours=1)
                fake_datetime = mock.Mock(name="datetime")
                fake_datetime.utcnow.return_value = now

                with mock.patch("timepiece.sections.sections.datetime", fake_datetime):
                    obj = self.parser.time_spec_to_object("now()")

                self.assertIs(type(obj), final.DateTimeSpec)
                self.assertIs(obj.datetime, now)

        describe "amount":
            it "can only be used as a parameter":
                with self.fuzzyAssertRaisesError(self.ErrorKls, "Sorry, object can only be used as a parameter", got=sections.AmountSpec(num=1, size="minute")):
                    self.parser.time_spec_to_object("amount(num:1, size: minute)")

        describe "interval":
            it "does not provide enough on it's own":
                with self.fuzzyAssertRaisesError(self.ErrorKls, "Time spec is invalid, .+", got=("interval", )):
                    self.parser.time_spec_to_object("interval(every: amount(num:1, size:minute))")

            it "combines with something providing a start time":
                obj = self.parser.time_spec_to_object("between(start: now()) & interval(every: amount(num:1, size:minute))")
                self.assertEqual(len(obj.every.intervals), 1)
                self.assertEqual(obj.every.intervals[0].every.num, 1)
                self.assertEqual(obj.every.intervals[0].every.size, "minute")

            it "can or with other intervals":
                obj = self.parser.time_spec_to_object("between(start: now()) & interval(every: amount(num:1, size:minute)) | interval(every: amount(num:2, size: second))")
                self.assertEqual(len(obj.every.intervals), 2)
                self.assertEqual(obj.every.intervals[0].every.num, 1)
                self.assertEqual(obj.every.intervals[0].every.size, "minute")
                self.assertEqual(obj.every.intervals[1].every.num, 2)
                self.assertEqual(obj.every.intervals[1].every.size, "second")

            it "can or with other groups of intervals":
                obj = self.parser.time_spec_to_object("between(start: now()) & interval(every: amount(num:1, size:minute)) | interval(every: amount(num:2, size: second)) | interval(every: amount(num:3, size: hour))")
                self.assertEqual(len(obj.every.intervals), 3)
                self.assertEqual(obj.every.intervals[0].every.num, 1)
                self.assertEqual(obj.every.intervals[0].every.size, "minute")
                self.assertEqual(obj.every.intervals[1].every.num, 2)
                self.assertEqual(obj.every.intervals[1].every.size, "second")
                self.assertEqual(obj.every.intervals[2].every.num, 3)
                self.assertEqual(obj.every.intervals[2].every.size, "hour")

            it "can or with wrapped intervals":
                obj = self.parser.time_spec_to_object("between(start: now()) & interval(every: amount(num:1, size:minute)) | ( interval(every: amount(num:2, size: second)) | interval(every: amount(num:3, size: hour)))")
                self.assertEqual(len(obj.every.intervals), 3)
                self.assertEqual(obj.every.intervals[0].every.num, 1)
                self.assertEqual(obj.every.intervals[0].every.size, "minute")
                self.assertEqual(obj.every.intervals[1].every.num, 2)
                self.assertEqual(obj.every.intervals[1].every.size, "second")
                self.assertEqual(obj.every.intervals[2].every.num, 3)
                self.assertEqual(obj.every.intervals[2].every.size, "hour")

                obj = self.parser.time_spec_to_object("between(start: now()) & ( interval(every: amount(num:1, size:minute)) | interval(every: amount(num:2, size: second))) | interval(every: amount(num:3, size: hour))")
                self.assertEqual(len(obj.every.intervals), 3)
                self.assertEqual(obj.every.intervals[0].every.num, 1)
                self.assertEqual(obj.every.intervals[0].every.size, "minute")
                self.assertEqual(obj.every.intervals[1].every.num, 2)
                self.assertEqual(obj.every.intervals[1].every.size, "second")
                self.assertEqual(obj.every.intervals[2].every.num, 3)
                self.assertEqual(obj.every.intervals[2].every.size, "hour")

        describe "range":
            it "consolidate the min and max into a common size and then finds a random amount in that range into an AmountSpec":
                randrange = mock.Mock(name="randrange", return_value=42)
                with mock.patch("timepiece.sections.sections.random.randrange", randrange):
                    obj = self.parser.time_spec_to_object("range(min: amount(num:1, size: second), max: amount(num:2, size:hour))", validate=False)
                self.assertEqual(type(obj), sections.AmountSpec)
                self.assertEqual(obj.num, 42)
                self.assertEqual(obj.size, "second")
                randrange.assert_called_once_with(1, 7200)

        describe "between":
            it "does not provide enough on it's own":
                with self.fuzzyAssertRaisesError(self.ErrorKls, "Time spec is invalid, .+", got=("duration", )):
                    self.parser.time_spec_to_object("between(start: sunset())")

            it "combines with intervals":
                obj = self.parser.time_spec_to_object("between(start: sunset()) & interval(every: amount(num: 1, size: minute))")
                self.assertEqual(type(obj), final.RepeatSpec)
                self.assertEqual(type(obj.every), sections.IntervalsSpec)
                self.assertEqual(len(obj.every.intervals), 1)

            it "combines with multiple intervals":
                obj = self.parser.time_spec_to_object("between(start: sunset()) & (interval(every: amount(num: 1, size: minute)) | interval(every: amount(num:2, size: hour)))")
                self.assertEqual(type(obj), final.RepeatSpec)
                self.assertEqual(type(obj.every), sections.IntervalsSpec)
                self.assertEqual(len(obj.every.intervals), 2)

        describe "day_name":
            it "does not provide enough on it's own":
                with self.fuzzyAssertRaisesError(self.ErrorKls, "Time spec is invalid, .+", got=("filter", )):
                    self.parser.time_spec_to_object("day_name(name: mon;tues)")

            it "provides a list of names":
                obj = self.parser.time_spec_to_object("day_name(name: mon;tues)", validate=False)
                self.assertEqual(obj.day_names, ["mon", "tues"])

                obj = self.parser.time_spec_to_object("day_name(name: wed)", validate=False)
                self.assertEqual(obj.day_names, ["wed"])

        describe "day_number":
            it "does not provide enough on it's own":
                with self.fuzzyAssertRaisesError(self.ErrorKls, "Time spec is invalid, .+", got=("filter", )):
                    self.parser.time_spec_to_object("day_number(number: 20)")

        describe "time":
            it "does not provide enough on it's own":
                with self.fuzzyAssertRaisesError(self.ErrorKls, "Time spec is invalid, .+", got=("time", )):
                    self.parser.time_spec_to_object("time(hour: 16, minute:20)")

            it "can combine with a date":
                res = self.parser.time_spec_to_object("time(hour: 16, minute:20) & date(month:3, day:10, year:1980)")
                self.assertEqual(type(res), final.DateTimeSpec)
                self.assertEqual(res.datetime.strftime("%s"), "321517200")

        describe "sunrise":
            it "does not simplify":
                obj = self.parser.time_spec_to_object("sunrise()", validate=False)
                self.assertIs(type(obj), sections.SunRiseSpec)

        describe "sunset":
            it "does not simplify":
                obj = self.parser.time_spec_to_object("sunset()", validate=False)
                self.assertIs(type(obj), sections.SunSetSpec)

        describe "iso8601":
            it "can represent repeating intervals":
                spec = str(uuid.uuid1())
                obj = self.parser.time_spec_to_object("iso8601(type: repeating_interval, specification: {0})".format(spec), validate=False)
                self.assertIs(type(obj), sections.ISO8601Spec)
                self.assertEqual(obj.specifies, ("interval", ))

                res = mock.Mock(name="res")
                fake_iso8601 = mock.Mock(name='iso8601')
                fake_iso8601.parse_repeating_interval.return_value = res

                with mock.patch("timepiece.sections.sections.aniso8601", fake_iso8601):
                    self.assertIs(obj.interval, res)

                fake_iso8601.parse_repeating_interval.assert_called_once_with(spec)

            it "can represent a datetime":
                spec = str(uuid.uuid1())
                obj = self.parser.time_spec_to_object("iso8601(type: datetime, specification: {0})".format(spec), validate=False)
                self.assertIs(type(obj), sections.ISO8601Spec)
                self.assertEqual(obj.specifies, ("day", "time"))

                day = mock.Mock(name="day")
                tme = mock.Mock(name="time")
                res = mock.Mock(name="res")
                res.date.return_value = day
                res.time.return_value = tme

                fake_iso8601 = mock.Mock(name='iso8601')
                fake_iso8601.parse_datetime.return_value = res

                with mock.patch("timepiece.sections.sections.aniso8601", fake_iso8601):
                    self.assertIs(obj.datetime, res)

                fake_iso8601.parse_datetime.assert_called_once_with(spec)

                self.assertIs(obj.time, tme)
                self.assertIs(obj.day, day)

            it 'can represent a date':
                spec = str(uuid.uuid1())
                obj = self.parser.time_spec_to_object("iso8601(type: date, specification: {0})".format(spec), validate=False)
                self.assertIs(type(obj), sections.ISO8601Spec)
                self.assertEqual(obj.specifies, ("day", ))

                res = mock.Mock(name="res")
                fake_iso8601 = mock.Mock(name='iso8601')
                fake_iso8601.parse_date.return_value = res

                with mock.patch("timepiece.sections.sections.aniso8601", fake_iso8601):
                    self.assertIs(obj.day, res)

                fake_iso8601.parse_date.assert_called_once_with(spec)

            it 'can represent a time':
                spec = str(uuid.uuid1())
                obj = self.parser.time_spec_to_object("iso8601(type: time, specification: {0})".format(spec), validate=False)
                self.assertIs(type(obj), sections.ISO8601Spec)
                self.assertEqual(obj.specifies, ("time", ))

                res = mock.Mock(name="res")
                fake_iso8601 = mock.Mock(name='iso8601')
                fake_iso8601.parse_time.return_value = res

                with mock.patch("timepiece.sections.sections.aniso8601", fake_iso8601):
                    self.assertIs(obj.time, res)

                fake_iso8601.parse_time.assert_called_once_with(spec)

            it 'cannot represent arbitrary types':
                spec = str(uuid.uuid1())
                error = BadSpecValue("Expected one of the available choices", got="arbitrary", available=['datetime', 'date', 'time', 'duration', 'repeating_interval'], meta=mock.ANY)
                with self.fuzzyAssertRaisesError(BadSpecValue, _errors=[error]):
                     self.parser.time_spec_to_object("iso8601(type: arbitrary, specification: {0})".format(spec), validate=False)

