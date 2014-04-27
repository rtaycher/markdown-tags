#!/usr/bin/env python
# coding=utf-8
import markdown_tags

look_of_disapproval = "ಠ_ಠ"

smiley_face = "ಠ◡ಠ"

reddiquette_link = markdown_tags.Link("reddiquette", "http://www.reddit.com/wiki/reddiquette")


class Strikethrough(markdown_tags.MarkdownFormattingObject):
    def _tags_to_markdown(self, opt_ctx):
        return "~~" + "".join(c._tags_to_markdown(opt_ctx) for c in self.contents) + "~~"


class Superscript(markdown_tags.MarkdownFormattingObject):
    def _tags_to_markdown(self, opt_ctx):
        return  "^(" + "".join(c._tags_to_markdown(opt_ctx) for c in self.contents) + ")"

    def _check_recursive(self, banned_class_exception_tuples, opt_ctx):
        if any(isinstance(c,markdown_tags.BlockLevel) for c in self.contents):
            raise markdown_tags.IllegalMarkdownFormattingException("No BlockLevel tags allowed in superscipt.")
        if "\n" in "".join(c._tags_to_markdown(opt_ctx) for c in self.contents):
            raise markdown_tags.IllegalMarkdownFormattingException("No spaces allowed in superscipt.")