# coding: spec

from tests.helpers import TestCase

from timepiece.helpers import memoized_property

describe TestCase, "memoized_property":
    it "stores the cached value on the instance":
        class Thing(object):
            @memoized_property
            def a_property(self):
                return 42

        thing = Thing()
        self.assertEqual(hasattr(thing, "_a_property"), False)

        self.assertEqual(thing.a_property, 42)
        self.assertEqual(thing._a_property, 42)

        thing._a_property = "changed"
        self.assertEqual(thing.a_property, "changed")

    it "supports setting new values":
        class Thing(object):
            @memoized_property
            def a_property(self):
                return 42

        thing = Thing()
        self.assertEqual(hasattr(thing, "_a_property"), False)

        self.assertEqual(thing.a_property, 42)
        self.assertEqual(thing._a_property, 42)

        thing.a_property = "set a new"
        self.assertEqual(thing.a_property, "set a new")
        self.assertEqual(thing._a_property, "set a new")

    it "supports deleting the cache":
        info = {"called": 0}
        class Thing(object):
            @memoized_property
            def a_property(self):
                info["called"] += 1
                return 42

        thing = Thing()
        self.assertEqual(info, {"called": 0})
        self.assertEqual(hasattr(thing, "_a_property"), False)

        self.assertEqual(thing.a_property, 42)
        self.assertEqual(info, {"called": 1})
        self.assertEqual(thing._a_property, 42)

        self.assertEqual(thing.a_property, 42)
        self.assertEqual(info, {"called": 1})

        del thing.a_property
        self.assertEqual(hasattr(thing, "_a_property"), False)

        self.assertEqual(thing.a_property, 42)
        self.assertEqual(info, {"called": 2})

    it "memoizes the value":
        info = {"called": 0}
        class Thing(object):
            @memoized_property
            def a_property(self):
                info["called"] += 1
                return 42

        thing = Thing()
        self.assertEqual(info, {"called": 0})
        self.assertEqual(hasattr(thing, "_a_property"), False)

        self.assertEqual(thing.a_property, 42)
        self.assertEqual(info, {"called": 1})

        self.assertEqual(thing.a_property, 42)
        self.assertEqual(info, {"called": 1})

        self.assertEqual(thing.a_property, 42)
        self.assertEqual(info, {"called": 1})

