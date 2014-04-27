#!/usr/bin/env python
from markdown_tags import *


class Spoiler(MarkdownFormattingObject):
    def __init__(self, visible, spoiler):
        self.contents = (visible, spoiler)
        self.visible = visible
        self.spoiler = spoiler
        self._wrap_unwrapped()

    def _tags_to_markdown(self, opt_ctx):
        return '[' + self.visible + '](#s "' + self.spoiler + '")'

