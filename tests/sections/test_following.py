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

    describe "IntervalsSpec":
        it "keeps going till a round is empty":
            at = datetime(2001, 1, 1)
            start = datetime(1999, 1, 1)
            end = datetime(2002, 1, 1)

            called = []

            def interval1_gen(a, s, e):
                self.assertIs(a, at)
                self.assertIs(s, start)
                self.assertIs(e, end)

                yield datetime(2000, 1, 2)
                called.append([])
                called[-1].append(1)

                yield datetime(2000, 1, 4)
                called.append([])
                called[-1].append(1)

            def interval2_gen(a, s, e):
                self.assertIs(a, at)
                self.assertIs(s, start)
                self.assertIs(e, end)

                yield datetime(2000, 1, 3)
                called[-1].append(2)

                yield datetime(2000, 1, 5)
                called[-1].append(2)

            interval1 = mock.Mock(name="interval1")
            interval1.following.side_effect = interval1_gen

            interval2 = mock.Mock(name="interval2")
            interval2.following.side_effect = interval2_gen

            spec = final.IntervalsSpec(intervals=[interval1, interval2])
            self.assertEqual(spec.following(at, start, end), None)

            self.assertEqual(called, [[1, 2], [1, 2]])

        it "keeps going till we've reached over 100 rounds":
            at = datetime(2001, 1, 1)
            start = datetime(1999, 1, 1)
            end = datetime(2002, 1, 1)

            called = []

            def interval1_gen(a, s, e):
                self.assertIs(a, at)
                self.assertIs(s, start)
                self.assertIs(e, end)

                while True:
                    yield datetime(1998, 1, 2)
                    called.append([])
                    called[-1].append(1)

            def interval2_gen(a, s, e):
                self.assertIs(a, at)
                self.assertIs(s, start)
                self.assertIs(e, end)

                while True:
                    yield datetime(1998, 1, 3)
                    called[-1].append(2)

            interval1 = mock.Mock(name="interval1")
            interval1.following.side_effect = interval1_gen

            interval2 = mock.Mock(name="interval2")
            interval2.following.side_effect = interval2_gen

            spec = final.IntervalsSpec(intervals=[interval1, interval2])
            self.assertEqual(spec.following(at, start, end), None)

            self.assertEqual(len(called), 101)

        it "drops repeaters that give values greater than end":
            at = datetime(2001, 1, 1)
            start = datetime(1999, 1, 1)
            end = datetime(2002, 1, 1)

            called = []

            def interval1_gen(a, s, e):
                self.assertIs(a, at)
                self.assertIs(s, start)
                self.assertIs(e, end)

                called.append([])
                called[-1].append(1)
                yield datetime(1998, 1, 2)

                called.append([])
                called[-1].append(1)
                yield datetime(1998, 1, 3)

                called.append([])
                called[-1].append(1)
                yield datetime(2001, 1, 4)

            def interval2_gen(a, s, e):
                self.assertIs(a, at)
                self.assertIs(s, start)
                self.assertIs(e, end)

                while True:
                    called[-1].append(2)
                    yield datetime(2003, 1, 3)

            interval1 = mock.Mock(name="interval1")
            interval1.following.side_effect = interval1_gen

            interval2 = mock.Mock(name="interval2")
            interval2.following.side_effect = interval2_gen

            spec = final.IntervalsSpec(intervals=[interval1, interval2])
            self.assertEqual(spec.following(at, start, end), datetime(2001, 1, 4))

            self.assertEqual(called, [[1, 2], [1], [1]])

        it "drops repeaters that finish":
            at = datetime(2001, 1, 1)
            start = datetime(1999, 1, 1)
            end = datetime(2002, 1, 1)

            called = []

            def interval1_gen(a, s, e):
                self.assertIs(a, at)
                self.assertIs(s, start)
                self.assertIs(e, end)

                called.append([])
                called[-1].append(1)
                yield datetime(1998, 1, 2)

                called.append([])
                called[-1].append(1)
                yield datetime(1998, 1, 3)

                called.append([])
                called[-1].append(1)
                yield datetime(2001, 1, 4)

            def interval2_gen(a, s, e):
                self.assertIs(a, at)
                self.assertIs(s, start)
                self.assertIs(e, end)

                called[-1].append(2)
                if False:
                    yield None

            interval1 = mock.Mock(name="interval1")
            interval1.following.side_effect = interval1_gen

            interval2 = mock.Mock(name="interval2")
            interval2.following.side_effect = interval2_gen

            spec = final.IntervalsSpec(intervals=[interval1, interval2])
            self.assertEqual(spec.following(at, start, end), datetime(2001, 1, 4))

            self.assertEqual(called, [[1, 2], [1], [1]])

        it "chooses the minimum after at and after start":
            at = datetime(2001, 1, 1)
            start = datetime(1999, 1, 1)
            end = datetime(2002, 1, 1)

            def interval1_gen(a, s, e):
                self.assertIs(a, at)
                self.assertIs(s, start)
                self.assertIs(e, end)

                # Both before start
                yield datetime(1998, 1, 3)

                # Both before at but after start
                yield datetime(2000, 1, 3)

                # this after start, but before at
                yield datetime(2000, 12, 3)

            def interval2_gen(a, s, e):
                self.assertIs(a, at)
                self.assertIs(s, start)
                self.assertIs(e, end)

                # Both before start
                yield datetime(1998, 1, 4)

                # Both before at but after start
                yield datetime(2000, 1, 4)

                # this after at
                yield datetime(2001, 1, 4)

            interval1 = mock.Mock(name="interval1")
            interval1.following.side_effect = interval1_gen

            interval2 = mock.Mock(name="interval2")
            interval2.following.side_effect = interval2_gen

            spec = final.IntervalsSpec(intervals=[interval1, interval2])
            self.assertEqual(spec.following(at, start, end), datetime(2001, 1, 4))

    describe "IntervalSpec":
        it "yields from the every attribute":
            res1 = mock.Mock(name='res1')
            res2 = mock.Mock(name='res2')
            res3 = mock.Mock(name='res3')

            def gen(s, a, e):
                yield res1
                yield res2
                yield res3
            every = mock.Mock(name="every")
            every.interval.side_effect = gen

            spec = sections.IntervalSpec(every=every)
            s = mock.Mock(name='s')
            a = mock.Mock(name='a')
            e = mock.Mock(name="e")
            self.assertEqual(list(spec.following(s, a, e)), [res1, res2, res3])

            every.interval.assert_called_once_with(a, s, e)

