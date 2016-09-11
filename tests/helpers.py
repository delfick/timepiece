from unittest import TestCase as UnitTestTestCase
from delfick_error import DelfickErrorTestMixin

class TestCase(UnitTestTestCase, DelfickErrorTestMixin):
    pass
