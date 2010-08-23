#  Copyright 2008-2009 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from robotide.editor.editors import DocumentationEditor, SettingEditor
from robotide import utils
import re


class _SettingController(object):
    editor = SettingEditor

    def __init__(self, parent_controller, data):
        self._parent = parent_controller
        if data.comment:
            data.comment = data.comment.strip()
        self._data = data
        self.label = self._label(self._data)
        self._init(self._data)

    def _label(self, data):
        label = data.setting_name
        if label.startswith('['):
            return label[1:-1]
        return label

    @property
    def value(self):
        value = self._data.as_list()[1:]
        if self._data.comment:
            value.pop()
        return ' | '.join(value)

    @property
    def display_value(self):
        return ' | ' .join(self._data.as_list()[1:])

    @property
    def comment(self):
        return self._data.comment or ''

    @property
    def keyword_name(self):
        return ''

    @property
    def datafile_controller(self):
        return self._parent.datafile_controller

    @property
    def datafile(self):
        return self._parent.datafile

    @property
    def is_set(self):
        return self._data.is_set()

    @property
    def dirty(self):
        return self._parent.dirty

    def set_value(self, value):
        if self._changed(value):
            self._set(value)
            self._mark_dirty()

    def set_comment(self, comment):
        if comment != self.comment:
            self._data.comment = comment
            self._mark_dirty()

    def clear(self):
        self._data.reset()
        self._mark_dirty()

    def _changed(self, value):
        return value != self._data.value

    def _set(self, value):
        self._data.value = value

    def _split_from_separators(self, value):
        return utils.split_value(value)

    def _mark_dirty(self):
        self._parent.mark_dirty()


class DocumentationController(_SettingController):
    editor = DocumentationEditor
    compiled_regexp_rn = re.compile(r'(\\+)r\\n')
    compiled_regexp_n = re.compile(r'(\\+)n')
    compiled_regexp_r = re.compile(r'(\\+)r')

    def _init(self, doc):
        self._doc = doc

    @property
    def value(self):
        return self._doc.value

    def _get_editable_value(self):
        return self._unescape_newlines_and_handle_escaped_backslashes(self._doc.value)

    def _set_editable_value(self, value):
        self.set_value(self._escape_newlines(value))

    editable_value = property(_get_editable_value, _set_editable_value)

    @property
    def visible_value(self):
        return utils.html_escape(utils.unescape(self._doc.value), formatting=True)

    def _unescape_newlines_and_handle_escaped_backslashes(self, input):
        def replacer(match):
            blashes = len(match.group(1))
            if blashes % 2 == 1:
                return '\\'*(blashes-1) + '\n'
            return match.group()
        input = self.compiled_regexp_rn.sub(replacer, input)
        input = self.compiled_regexp_n.sub(replacer, input)
        return self.compiled_regexp_r.sub(replacer, input)

    def _escape_newlines(self, item):
        item = item.replace('\r\n', '\\n')
        item = item.replace('\n', '\\n')
        return item.replace('\r', '\\n')


class FixtureController(_SettingController):

    def _init(self, fixture):
        self._fixture = fixture

    @property
    def keyword_name(self):
        return self._fixture.name

    def _changed(self, value):
        name, args = self._parse(value)
        return self._fixture.name != name or self._fixture.args != args

    def _set(self, value):
        name, args = self._parse(value)
        self._fixture.name = name
        self._fixture.args = args

    def _parse(self, value):
        value = self._split_from_separators(value)
        return value[0] if value else '', value[1:] if value else []


class TagsController(_SettingController):

    def _init(self, tags):
        self._tags = tags

    def _changed(self, value):
        return self._tags.value != self._split_from_separators(value)

    def _set(self, value):
        self._tags.value = self._split_from_separators(value)


class TimeoutController(_SettingController):

    def _init(self, timeout):
        self._timeout = timeout

    def _changed(self, value):
        val, msg = self._parse(value)
        return self._timeout.value != val or self._timeout.message != msg

    def _set(self, value):
        value, message = self._parse(value)
        self._timeout.value = value
        self._timeout.message = message

    def _parse(self, value):
        parts = value.split('|', 1)
        val = parts[0].strip() if parts else ''
        msg = parts[1].strip() if len(parts) == 2 else ''
        return val, msg


class TemplateController(_SettingController):

    def _init(self, template):
        self._template = template

    @property
    def keyword_name(self):
        return self._template.value


class ArgumentsController(_SettingController):

    def _init(self, args):
        self._args = args

    def _changed(self, value):
        return self._args.value != self._split_from_separators(value)

    def _set(self, value):
        self._args.value = self._split_from_separators(value)


class ReturnValueController(_SettingController):

    def _init(self, return_):
        self._return = return_

    def _label(self, data):
        return 'Return Value'

    def _changed(self, value):
        return self._return.value != self._split_from_separators(value)

    def _set(self, value):
        self._return.value = self._split_from_separators(value)


class MetadataController(_SettingController):

    def _init(self, meta):
        self._meta = meta

    @property
    def name(self):
        return self._meta.name

    @property
    def value(self):
        return self._meta.value

    def set_value(self, name, value):
        self._meta.name = name
        self._meta.value = value
        self._parent.mark_dirty()


class VariableController(_SettingController):

    def _init(self, var):
        self._var = var

    def _label(self, data):
        return ''

    @property
    def name(self):
        return self._var.name

    @property
    def value(self):
        return self._var.value

    def set_value(self, name, value):
        value = [value] if isinstance(value, basestring) else value
        self._var.name = name
        self._var.value = value
        self._parent.mark_dirty()


class ImportController(_SettingController):

    def _init(self, import_):
        self._import = import_
        self.type = self._import.type

    def _label(self, data):
        return data.type

    @property
    def name(self):
        return self._import.name

    @property
    def alias(self):
        return self._import.alias or ''

    @property
    def args(self):
        return self._import.args or []

    @property
    def display_value(self):
        value = self.args + (['WITH NAME' , self.alias] if self.alias else [])
        return ' | '.join(value)

    @property
    def dirty(self):
        return self._parent.dirty

    def set_value(self, name, args=[], alias=''):
        self._import.name = name
        self._import.args = utils.split_value(args)
        self._import.alias = alias
        self._parent.mark_dirty()
        if self.label == 'Resource':
            return self._parent.resource_import_modified(self.name)
        return None
