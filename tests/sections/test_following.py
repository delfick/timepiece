# coding: spec

from tests.helpers import TestCase

from timepiece.sections import sections, final

from datetime import datetime
import mock

describe TestCase, "following functionality":
    describe "RepeatSpec":
        it "defaults at to utcnow":
            dt = datetime(2078, 2, 15)
            dtstart = datetime(2079, 2, 15)

            res = mock.Mock(name="res")

            start = mock.Mock(name="start", datetime=dtstart)
            start.following.return_value = res

            fake_datetime = mock.Mock(name="datetime")
            fake_datetime.utcnow.return_value = dt

            spec = final.RepeatSpec(start=start, end=None, every=None)
            with mock.patch("timepiece.sections.final.datetime", fake_datetime):
                self.assertIs(spec.following(), res)

            fake_datetime.utcnow.assert_called_once_with()

        it "returns nothing if end is less than at":
            at = datetime(2078, 2, 15)
            dtend = datetime(2077, 2, 15)
            dtstart = datetime(2076, 2, 15)

            end = mock.Mock(name="end", datetime=dtend)
            start = mock.Mock(name="start", datetime=dtstart)

            fake_datetime = mock.NonCallableMock(name="datetime")

            spec = final.RepeatSpec(start=start, end=end, every=None)
            with mock.patch("timepiece.sections.final.datetime", fake_datetime):
                self.assertIs(spec.following(at), None)

        it "returns start.following if end is greater than at and start is greater than at":
            at = datetime(2078, 2, 15)
            dtend = datetime(2079, 2, 15)
            dtstart = datetime(2078, 2, 16)

            res = mock.Mock(name="res")

            end = mock.Mock(name="end", datetime=dtend)
            start = mock.Mock(name="start", datetime=dtstart)
            start.following.return_value = res

            fake_datetime = mock.NonCallableMock(name="datetime")

            spec = final.RepeatSpec(start=start, end=end, every=None)
            with mock.patch("timepiece.sections.final.datetime", fake_datetime):
                self.assertIs(spec.following(at), res)

        it "returns start.following if no end and start is greater than at":
            at = datetime(2078, 2, 15)
            dtstart = datetime(2079, 2, 15)

            res = mock.Mock(name="res")

            start = mock.Mock(name="start", datetime=dtstart)
            start.following.return_value = res

            fake_datetime = mock.NonCallableMock(name="datetime")

            spec = final.RepeatSpec(start=start, end=None, every=None)
            with mock.patch("timepiece.sections.final.datetime", fake_datetime):
                self.assertIs(spec.following(at), res)

        it "uses every.following if start is less than at":
            at = datetime(2078, 2, 15)
            dtstart = datetime(2000, 1, 10)

            res = mock.Mock(name="res")

            start = mock.Mock(name="start", datetime=dtstart)
            every = mock.Mock(name="every")
            every.following.return_value = res

            fake_datetime = mock.NonCallableMock(name="datetime")

            spec = final.RepeatSpec(start=start, end=None, every=every)
            with mock.patch("timepiece.sections.final.datetime", fake_datetime):
                self.assertIs(spec.following(at), res)

    describe "ManyRepeatAndFiltersSpec":
        it "defaults at to utcnow":
            res = datetime(2000, 1, 1)
            utcnow = mock.Mock(name="utcnow")

            repeat_spec = mock.Mock(name="repeat_spec")
            repeat_spec.following.return_value = res

            fake_datetime = mock.Mock(name="datetime")
            fake_datetime.utcnow.return_value = utcnow

            spec = final.ManyRepeatAndFiltersSpec(specs=[repeat_spec])
            with mock.patch("timepiece.sections.final.datetime", fake_datetime):
                self.assertIs(spec.following(), res)

            fake_datetime.utcnow.assert_called_once_with()
            repeat_spec.following.assert_called_once_with(utcnow)

        it "returns the min datetime found":
            at = mock.Mock(name="at")
            res = datetime(2000, 1, 1)
            res1 = datetime(1999, 1, 1)
            res2 = datetime(2001, 2, 2)

            repeat_spec = mock.Mock(name="repeat_spec")
            repeat_spec.following.return_value = res

            repeat_spec1 = mock.Mock(name="repeat_spec1")
            repeat_spec1.following.return_value = res1

            repeat_spec2 = mock.Mock(name="repeat_spec2")
            repeat_spec2.following.return_value = res2

            fake_datetime = mock.NonCallableMock(name="datetime")

            spec = final.ManyRepeatAndFiltersSpec(specs=[repeat_spec, repeat_spec1, repeat_spec2])
            with mock.patch("timepiece.sections.final.datetime", fake_datetime):
                self.assertIs(spec.following(at), res1)

            repeat_spec.following.assert_called_once_with(at)
            repeat_spec1.following.assert_called_once_with(at)
            repeat_spec2.following.assert_called_once_with(at)

    describe "DateTimeSpec":
        it "defaults at to utcnow":
            utcnow = datetime(2001, 1, 1, 20, 15, 2)
            res = datetime(2002, 1, 1, 5, 5, 5)

            repeat_spec = mock.Mock(name="repeat_spec")
            repeat_spec.following.return_value = res

            fake_datetime = mock.Mock(name="datetime")
            fake_datetime.utcnow.return_value = utcnow

            spec = final.DateTimeSpec(datetime=res)
            with mock.patch("timepiece.sections.final.datetime", fake_datetime):
                self.assertIs(spec.following(), res)

            fake_datetime.utcnow.assert_called_once_with()

        it "removes microseconds before comparing":
            at = datetime(2001, 1, 1, 20, 15, 2, 200)
            res = datetime(2001, 1, 1, 20, 15, 2)

            repeat_spec = mock.Mock(name="repeat_spec")
            repeat_spec.following.return_value = res

            fake_datetime = mock.NonCallableMock(name="datetime")

            spec = final.DateTimeSpec(datetime=res)
            with mock.patch("timepiece.sections.final.datetime", fake_datetime):
                self.assertIs(spec.following(at), res)

        it "returns None if at is greater than the start time":
            at = datetime(2001, 1, 1, 20, 15, 2, 200)
            res = datetime(2000, 1, 1, 20, 15, 2)

            repeat_spec = mock.Mock(name="repeat_spec")
            repeat_spec.following.return_value = res

            fake_datetime = mock.NonCallableMock(name="datetime")

            spec = final.DateTimeSpec(datetime=res)
            with mock.patch("timepiece.sections.final.datetime", fake_datetime):
                self.assertIs(spec.following(at), None)

