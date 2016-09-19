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

