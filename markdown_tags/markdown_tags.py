#!/usr/bin/env python
#
import collections

import enum


class MarkdownFormats(enum.Enum):
    basic = "basic"
    reddit = "reddit"

class _MDTagsContext(object):
    def __init__(self, recover, format_md):
        self.recover = recover
        self.format_md = format_md


class IllegalMarkdownFormattingException(Exception):
    pass


class MarkdownFormattingObject(object):
    def __init__(self, *contents):
        self.contents = contents
        self._wrap_unwrapped()

    def _wrap_unwrapped(self):
        self.contents = tuple(c if isinstance(c, MarkdownFormattingObject)
                              else MFOWrapper(c)
                              for c in self.contents)

    def __repr__(self):
        return repr(type(self)) + "(" + repr(self.contents) + ")"

    def _check_recursive(self, banned_class_exception_tuples, opt_ctx):
        my_type = type(self)

        if not isinstance(self, _RepeatableBlockLevel):
            possible_match = [t for t in banned_class_exception_tuples if my_type == t[0]]
            if possible_match:
                raise possible_match[0][1](self)
            banned_class_exception_tuples = (banned_class_exception_tuples +
                                             [(my_type, lambda s:
                                             IllegalMarkdownFormattingException(
                                                 "Illegal nested MarkdownFormattingTags class " +
                                                 str(type(self))))])

        for item in self.contents:
            item._check_recursive(banned_class_exception_tuples, opt_ctx)


class MFOWrapper(MarkdownFormattingObject):
    def __init__(self, obj):
        self.contents = obj

    def __repr__(self):
        return repr(self.contents)

    def _check_recursive(self, banned_class_exception_tuples, opt_ctx):
        pass

    def _tags_to_markdown(self, opt_ctx):
        return str(self.contents)


class Blocks(MarkdownFormattingObject):
    def _tags_to_markdown(self, opt_ctx):
        return "\n\n".join(c._tags_to_markdown(opt_ctx) for c in self.contents)

    def _check_recursive(self, banned_class_exception_tuples, opt_ctx):
        second_level_non_block_elements = [c for c in self.contents
                                           if not isinstance(c, BlockLevel)]
        if second_level_non_block_elements:
            raise IllegalMarkdownFormattingException(
                "Only block elements are allowed as second level elements," +
                " not allowed:" + str(second_level_non_block_elements))
        super(Blocks, self)._check_recursive(banned_class_exception_tuples, opt_ctx)


class MD(Blocks):
    def _tags_to_markdown(self, opt_ctx):
        if not opt_ctx.recover:
            self._check_recursive([], opt_ctx)
        return super(MD, self)._tags_to_markdown(opt_ctx)

    def tags_to_markdown(self, recover, format_md):
        opt_ctx = _MDTagsContext(recover=recover, format_md=format_md)
        return self._tags_to_markdown(opt_ctx)


class BlockLevel(MarkdownFormattingObject):
    pass


class _RepeatableBlockLevel(BlockLevel):
    pass


class HorizontalRuleLine(BlockLevel):
    def __init__(self):
        self.contents = tuple()

    def __repr__(self):
        return repr(type(self))

    def _check_recursive(self, banned_class_exception_tuples, opt_ctx):
        pass

    def _tags_to_markdown(self, opt_ctx):
        return "---------------------------"


class Header(BlockLevel):
    def __init__(self, level, *contents):
        assert level in [1, 2, 3, 4, 5, 6]
        self.level = level
        self.contents = contents
        self._wrap_unwrapped()

    def __repr__(self):
        return repr(type(self)) + self.level + "(" + repr(self.contents) + ")"

    def _tags_to_markdown(self, opt_ctx):
        return ("#" * self.level) + "".join(c._tags_to_markdown(opt_ctx) for c in self.contents)


class Italic(MarkdownFormattingObject):
    def _tags_to_markdown(self, opt_ctx):
        return "*" + "".join(c._tags_to_markdown(opt_ctx) for c in self.contents) + "*"


class Bold(MarkdownFormattingObject):
    def _tags_to_markdown(self, opt_ctx):
        return "**" + "".join(c._tags_to_markdown(opt_ctx) for c in self.contents) + "**"

class _List(_RepeatableBlockLevel):
    @classmethod
    def with_title(cls, title, *contents):
        obj = cls(*contents)
        obj.title = title
        return obj
    def __init__(self, *contents):
        self.title = ""
        super(_List, self).__init__(*contents)

class UnorderedList(_List):
    def _tags_to_markdown(self, opt_ctx):
        res = ""
        if self.title:
            res += self.title + "\n\n"

        for list_item in self.contents:
            first_line = True
            for line in list_item._tags_to_markdown(opt_ctx).split("\n"):
                if first_line:
                    if isinstance(list_item, _List) and not list_item.title:
                        res += "\n"
                    res += "+ " + line + "\n"
                    first_line = False
                else:
                    res += "    " + line + "\n"
            res += "\n"
        return res

class OrderedList(_List):
    def _tags_to_markdown(self, opt_ctx):
        res = ""
        if self.title:
            res += self.title + "\n\n"

        for (i, list_item) in enumerate(self.contents, start=1):
            first_line = True
            for line in list_item._tags_to_markdown(opt_ctx).split("\n"):
                if first_line:
                    if isinstance(list_item, _List) and not list_item.title:
                        res += "\n"
                    res += str(i) + ". " + line + "\n"
                    first_line = False
                else:
                    res += "    " + line + "\n"
            res += "\n"
        return res

class BlockQuote(_RepeatableBlockLevel):
    def _tags_to_markdown(self, opt_ctx):
        return "\n".join(">" + line
                         for line in "".join(c._tags_to_markdown(opt_ctx)
                                             for c in self.contents).split("\n"))


class Code(BlockLevel):
    def _tags_to_markdown(self, opt_ctx):
        return "\n".join("    " + x for x in
                         "".join(self.contents, opt_ctx).split("\n"))

    def _check_recursive(self, banned_class_exception_tuples, opt_ctx):
        if any(isinstance(c, MarkdownFormats) for c in self.contents):
            raise IllegalMarkdownFormattingException("You can't put markdown elements in Code elements, just text.")
        super(Code, self)._check_recursive(banned_class_exception_tuples, opt_ctx)


class Paragraph(BlockLevel):
    def _tags_to_markdown(self, opt_ctx):
        return "".join(c._tags_to_markdown(opt_ctx) for c in self.contents)


class Link(MarkdownFormattingObject):
    def __init__(self, url, text, title=""):
        if title:
            self.url = url
            self.contents = text
            self.title = title
        else:
            self.url = url
            self.contents = text
            self.title = None
        self._wrap_unwrapped()

    def _tags_to_markdown(self, opt_ctx):
        if self.title:
            return ("[" + "".join(c._tags_to_markdown(opt_ctx) for c in self.contents) + "]"
                    + "(" + self.url + ' "' + self.title + '")')
        else:
            return ("[" + "".join(c._tags_to_markdown(opt_ctx) for c in self.contents) + "]"
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
        self._wrap_unwrapped()

    def _check_recursive(self, banned_class_exception_tuples, opt_ctx):
        if opt_ctx.format_md == MarkdownFormats.reddit:
            raise IllegalMarkdownFormattingException("Reddit markdown does not allow Images")
        super(Image, self)._check_recursive(banned_class_exception_tuples, opt_ctx)

    def _tags_to_markdown(self, opt_ctx):
        if self.title:
            return ("![" + "".join(c._tags_to_markdown(opt_ctx) for c in self.contents) + "]"
                    + "(" + self.url + ' "' + self.title + '")')
        else:
            return ("![" + "".join(c._tags_to_markdown(opt_ctx) for c in self.contents) + "]"
                    + "(" + self.url + ")")


_escaped_characters = list(r"\`*_{}[]()#+-.!")
_replace_map = [(e, "\\" + e) for e in _escaped_characters]


def escape_strings(content):
    if isinstance(content, basestring):
        return escape(content)
    return content


def escape(string):
    for (o, n) in _replace_map:
        string = string.replace(o, n)
    return string


def _prepend_to_each_line(first_pre, other_pre, content):
    "\n".join((other_pre + s for s in content.split("\n")))

