from timepiece.sections.base import JoinerSpec, SectionSpec
from timepiece.grammar import TimeSpecGrammar, TimeSpecVisitor

from delfick_error import DelfickError

def make_timepiece(ErrorKls=DelfickError, JoinerSpec=JoinerSpec, SectionSpec=SectionSpec, sections=None):
	Joiner = type("Joiner", (JoinerSpec, ), {"ErrorKls": ErrorKls})
	Section = type("Section", (SectionSpec, ), {"ErrorKlss": ErrorKls})
	Visitor = type("Visitor", (TimeSpecVisitor, ), {"ErrorKls": ErrorKls, "Joiner": Joiner, "Section": Section})
	return type("Grammar", (TimeSpecGrammar, ), {"Visitor": Visitor})(sections)

