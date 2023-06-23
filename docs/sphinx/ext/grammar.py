from timepiece.grammar import TimeSpecVisitor

from docutils.statemachine import ViewList
from docutils.parsers.rst import Directive
from textwrap import dedent
from docutils import nodes

class GrammarDirective(Directive):
    """Directive for outputting the timepiece grammar"""
    def run(self):
        sect = nodes.section()
        sect['ids'].append("the_grammar")
        title = nodes.title()
        title += nodes.Text("EBNF grammar")
        sect += title

        grammar = TimeSpecVisitor().grammar_string

        viewlist = ViewList()
        viewlist.append(".. code-block:: text", "")
        viewlist.append("", "")

        for line in dedent(grammar).strip().split("\n"):
            viewlist.append("    {0}".format(line), "")
        self.state.nested_parse(viewlist, self.content_offset, sect)
        return [sect]

def setup(app):
    """Setup the show_specs directive"""
    app.add_directive('the_grammar', GrammarDirective)
