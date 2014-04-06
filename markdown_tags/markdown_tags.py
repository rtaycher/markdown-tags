# !/usr/bin/env python
# 
import collections
import enum


class MarkdownFormats(enum.Enum):
    basic = "basic"
    reddit = "reddit"

class _MDTagsContext(object):
    def __init__(self, recover, format_md, tree_level=1):
        self.recover = recover
        self.format_md = format_md
        self.tree_level = tree_level

    def one_level_down(self):
        copy_changed = _MDTagsContext(self.recover, self.format_md, self.tree_level + 1)
        return copy_changed

def tags_to_markdown(tags, recover=False, format_md=MarkdownFormats.reddit):
    """
    :param MarkdownFormattingObject(s) tags: One or more Markdown Tags
    :returns  str: a valid markdown string representing the tags passed in
    :rtype str
    :raises IllegalMarkdownFormattingException: on failure to transform tags to markdown
    """
    #print "format called with args: " + str(args)
    assert tags, "tags_to_markdown not passed any tag arguments"
    ans = ""

    opt_ctx = _MDTagsContext(recover, format_md, 1)
    if len(tags) == 1:
        ans += tags[0]._tags_to_markdown(recover=recover)

    for arg in tags:
        if isinstance(arg, collections.Iterable):
            for sub_arg in arg:
                try:
                    ans += sub_arg._tags_to_markdown(recover=recover,
                                                     format_md=MarkdownFormats.reddit)
                except AttributeError:
                    ans += str(sub_arg)
        elif isinstance(arg, MarkdownFormattingObject):
            if not recover:
                arg._check_recursive(tuple())
                if format_md == "reddit":
                    print("yo yo yo")
                    arg._check_recursive(Image,)
            ans += arg._tags_to_markdown(recover=recover)

    return ans

class IllegalMarkdownFormattingException(Exception):
    pass


class MarkdownFormattingObject(object):
    def __init__(self, *contents):
        self.contents = contents

    def __repr__(self):
        return repr(type(self)) + "(" + repr(self.contents) + ")"

    def _check_recursive(self, banned_class_exception_tuples, opt_ctx):
        my_type = type(self)
        for item in self.contents:
            possible_match = (t for t in banned_class_exception_tuples if my_type == t[0])
            if possible_match:
                raise possible_match[1](self)
            try:
                if my_type != BlockQuote:
                    item._check_recursive(banned_class_exception_tuples +
                                       (my_type,
                                        lambda s: IllegalMarkdownFormattingException(
                                            "Illegal nested MarkdownFormattingTags class " + str(type(self)) +
                                            ": " + tags_to_markdown(self))))
            except AttributeError:
                pass


class MD(MarkdownFormattingObject):
    def __init__(self, *contents):
        def _tags_to_markdown(self, opt_ctx):
            return "\n\n".join(self.contents)
        self.contents = contents

    def _check_recursive(self, banned_class_exception_tuples, opt_ctx):
        second_level_non_block_elements = [c for c in self.contents if not isinstance(c, BlockLevel)]
        if second_level_non_block_elements:
            raise IllegalMarkdownFormattingException(
                "Only block elements are allowed as second level elements," +
                " not allowed:" + str(second_level_non_block_elements))
        super(MD,self)._check_recursive(banned_class_exception_tuples)

    def tags_to_markdown(self, recover, format_md):
        opt_ctx = _MDTagsContext(recover=recover, format_md=format_md)
        return self._tags_to_markdown(opt_ctx)

    def _tags_to_markdown(self, opt_ctx):
        return "\n\n".join(c._tags_to_markdown(opt_ctx.one_level_down()) for c in self.contents)

class BlockLevel(MarkdownFormattingObject):
    pass
#0
class HorizontalRuleLine(BlockLevel):
    def __init__(self):
        pass
    def __repr__(self):
        return repr(type(self))

    def _tags_to_markdown(self, opt_ctx):
        return "---------------------------"

#list
class Header(BlockLevel):
    def __init__(self, level, *contents):
        assert level in [1,2,3,4,5,6]
        self.level = level
        self.contents = contents
    def __repr__(self):
        return repr(type(self)) + self.level + "(" + repr(self.contents) + ")"

    def _tags_to_markdown(self, opt_ctx):
        return ("#" * self.level) + "".join(c._tags_to_markdown(opt_ctx.one_level_down()) for c in self.contents)
#1
class Italic(MarkdownFormattingObject):
    def _tags_to_markdown(self, opt_ctx):
        return "*" + "\n\n".join(c._tags_to_markdown(opt_ctx.one_level_down()) for c in self.contents) + "*"
#1
class Bold(MarkdownFormattingObject):
    def _tags_to_markdown(self, opt_ctx):
        return "**" + "".join(c._tags_to_markdown(opt_ctx.one_level_down()) for c in self.contents) + "**"
#list
class UnorderedList(MarkdownFormattingObject):
    def _tags_to_markdown(self, opt_ctx):
        if opt_ctx.tree_level != 2:
            return _prepend_to_each_line("    ", "\n".join("+" + " " + c._tags_to_markdown(opt_ctx.one_level_down())
                                                    for c in self.contents))
        else:
            return "\n".join("+" + " " + c._tags_to_markdown(opt_ctx.one_level_down())
                for c in self.contents)

#list
class OrderedList(MarkdownFormattingObject):
    def _tags_to_markdown(self, opt_ctx):
        if opt_ctx.tree_level != 2:
            return _prepend_to_each_line("    ", "\n".join(str(i) + ". " + c._tags_to_markdown(opt_ctx.one_level_down())
                             for (i, c) in enumerate(self.contents, 1)))

        else:
            return "\n".join(str(i) + ". " + c._tags_to_markdown(opt_ctx.one_level_down())
                for (i, c) in enumerate(self.contents, 1))
#1
class BlockQuote(BlockLevel):
    def _tags_to_markdown(self, opt_ctx):
        return "\n".join(">" + line
                    for line in "".join(c._tags_to_markdown(opt_ctx.one_level_down())
                        for c in self.contents).split("\n"))

class Code(BlockLevel):
    def _tags_to_markdown(self, opt_ctx):
        return "\n".join("    " + x for x in
                          tags_to_markdown(self.contents, opt_ctx).split("\n"))
    def _check_recursive(self, banned_class_exception_tuples, opt_ctx):
        if any(isinstance(c, MarkdownFormats) for c in self.contents):
            raise IllegalMarkdownFormattingException("You can't put markdown elements in Code elements, just text.")

class Paragraph(BlockLevel):
    def _tags_to_markdown(self, opt_ctx):
        if opt_ctx.tree_level == 2:
            "".join(c._tags_to_markdown(opt_ctx.one_level_down()) for c in self.contents)
        else:
            return "\n\n".join(c._tags_to_markdown(opt_ctx.one_level_down()) for c in self.contents)

class Strikethrough(MarkdownFormattingObject):
    def _tags_to_markdown(self, opt_ctx):
        return "~~" + "".join(c._tags_to_markdown(opt_ctx.one_level_down()) for c in self.contents) + "~~"

class Superscript(MarkdownFormattingObject):
    def _tags_to_markdown(self, opt_ctx):
        return "^" + "".join(c._tags_to_markdown(opt_ctx.one_level_down()) for c in self.contents) + " "


class Link(MarkdownFormattingObject):
    def __init__(self, url, text, title=""):
        if title:
            self.url = url
            self.title = title
            self.contents = text
        else:
            self.url = url
            self.contents = text
    def _tags_to_markdown(self, opt_ctx):
        if self.title:
            return ("![" + tags_to_markdown(self.contents, opt_ctx) + "]"
                    + "(" + self.url + ' "' + self.title + '")')
        else:
            return ("![" + tags_to_markdown(self.contents, opt_ctx) + "]"
                    + "(" + self.url + ")")


class Image(MarkdownFormattingObject):
    def __init__(self, url, alt, title=""):
        if title:
            self.url = url
            self.contents = alt
            self.title = title
        else:
            self.url = url
            self.contents = alt
            self.title = None
    def _tags_to_markdown(self, opt_ctx):
        if self.title:
            return ("![" + tags_to_markdown(self.contents, opt_ctx) + "]"
                    + "(" + self.url + ' "' + self.title + '")')
        else:
            return ("![" + tags_to_markdown(self.contents, opt_ctx) + "]"
                    + "(" + self.url + ")")

_escaped_characters = list(r"\`*_{}[]()#+-.!")
_replace_map = [(e, "\\" + e) for e in _escaped_characters]

def escape_strings(content):
    if isinstance(content, basestring):
        return escape(content)
    return content

def escape(string):
    for (o,n) in _replace_map:
        string = string.replace(o,n)
    return string

def _prepend_to_each_line(pre, content):
    "\n".join((pre + s for s in content.split("\n")))

#tags_to_markdown(Bold(Italic("col"), Bold("q")))
