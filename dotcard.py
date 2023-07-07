#!/usr/bin/python310

from PIL import Image, PngImagePlugin
from datetime import datetime
from functools import wraps
import argparse
import base64
import json
import os
import re
import sys
import typeguard


TOOL_NAME = '.card'
TOOL_VERSION = '0.2.0'


def get_metadata():
    return {
        'modified': round(datetime.utcnow().timestamp() * 1000),
        'tool': {
            'name': TOOL_NAME,
            'version': TOOL_VERSION,
        }
    }


def re_replace(string, substring, replacement):
    assert substring not in replacement

    while substring in string:
        string = string.replace(substring, replacement)

    return string


def save_image(card, img_path, dst, max_size):
    TEXT_CHUNK_ID = b'tEXt'

    # Encode char data
    encoded = b'chara\0' + base64.b64encode(
        bytes(json.dumps(card, default=vars), 'utf-8'))

    info = PngImagePlugin.PngInfo()
    info.add(TEXT_CHUNK_ID, encoded, after_idat=True)

    # Fit image to max_size maintaining aspect ratio
    im = Image.open(img_path)
    size = list(im.size)
    for i in (0, 1):
        j = 1 - i
        if max_size[i] > 0 and size[i] > max_size[i]:
            size[i] = max_size[i]
            size[j] = size[i] * (im.size[j] / im.size[i])
    im = im.resize(tuple(map(int, size)))

    # Save final image
    im.save(dst, 'PNG', pnginfo=info)


def deep_strip(text):
    return re_replace(text.strip(), '\n\n\n', '\n\n')


def minify_content(text):
    PLACEHOLDERS = ['{{' + p + '}}' for p in ['user', 'char']]

    final = []
    for i, code in enumerate(text.split('<!>')):
        if i % 2 != 0:
            final.append(code)
            continue

        for j, p in enumerate(PLACEHOLDERS):
            code = re.sub(p, chr(j), code, flags=re.I)

        for a, b in [
            # Remove duplicate spaces
            ('  ', ' '),
            (' \n', '\n'),
            ('\n ', '\n'),

            # Only type of line feed that is relevant
            ('}\n', '}; '),

            # Remove additional line feeds
            ('\n', ' '),
            ('  ', ' '),

            # Remove duplicate semicolons
            ('; }', ' }'),
            (';;', ';'),
            ('; ;', ';'),

            # Clamp repeated closing brackets
            ('}; }', '}}'),
            ('};}', '}}'),
            ('} }', '}}'),
        ]:
            code = re_replace(code, a, b).strip()

        for j, p in enumerate(PLACEHOLDERS):
            code = code.replace(chr(j), p)

        final.append(code)

    return deep_strip('\n'.join(final))


def parse_class(key_mark, const_mark, default_key='name'):
    def decorator(cls):
        original_init = cls.__init__

        @wraps(original_init)
        def inner(self, text, **kwargs):
            data = parse(text, key_mark, const_mark, default_key)

            def warn(text):
                if not kwargs.get('_silent'):
                    print(f'Warning: {text}', file=sys.stderr)

            for key, value in kwargs.items():
                if key.startswith('_'):
                    continue
                if key in data:
                    warn(f'Duplicate data key: {key}, overwriting')
                data[key] = value

            entries = {}

            for key in vars(cls).keys():
                if key.startswith('__') or key not in dir(cls):
                    continue
                entries[key] = getattr(cls, key)
                setattr(self, key, entries[key](data))

            remaining = ', '.join(list(data.keys()))
            if remaining:
                warn(f'Unknown entries will be ignored: {remaining}')

            # Check type correctness
            for key, method in entries.items():
                for constraint in method.__annotations__.values():
                    value = getattr(self, key)
                    try:
                        typeguard.check_type(value, constraint)
                    except typeguard.TypeCheckError:
                        warn(f'{key} does not match {constraint}')

                    if value is None:
                        delattr(self, key)

            original_init(self)

        cls.__init__ = inner
        return cls
    return decorator


def extract(data, key):
    value = data[key]
    del data[key]
    return value


def extract_raw(data, key, req_in=False, def_out=None):
    if key not in data:
        assert not req_in, f'Missing required entry: {key}'
        return def_out
    return extract(data, key)


def extract_str(data, key, stripped=True, req_in=False, def_out=None,
                non_empty=False):
    value = extract_raw(data, key, req_in=req_in, def_out=None)
    if value is None:
        return def_out
    value = deep_strip(value) if stripped else value
    assert not non_empty or value != '', f'{key} must not be empty'
    return value


def extract_tags(data, key, req_in=False, def_out=None):
    value = extract_raw(data, key, req_in=req_in, def_out=None)
    if value is None:
        return def_out

    if isinstance(value, str):
        value = value.replace('\n', ',').split(',')

    return list(tag for tag in
                dict.fromkeys(tag.strip() for tag in value)
                if tag != '')


def extract_type(data, key, t, req_in=False, def_out=None):
    value = extract_raw(data, key, req_in=req_in, def_out=None)
    return def_out if value is None else t(value)


def extract_bool(data, key, req_in=False, def_out=None):
    return extract_type(data, key, bool, req_in=req_in, def_out=def_out)


def extract_int(data, key, req_in=False, def_out=None):
    return extract_type(data, key, int, req_in=req_in, def_out=def_out)


def extract_json(data, key, req_in=False, def_out=None):
    return extract_type(data, key, json.loads, req_in=req_in, def_out=def_out)


@parse_class('|', None)
class CharacterBookEntry:
    def keys(data) -> list[str]:
        return extract_tags(data, 'keys', def_out=[])

    def content(data) -> str:
        return minify_content(extract_str(data, 'content', def_out=''))

    def enabled(data) -> bool:
        return extract_bool(data, 'enabled', def_out=True)

    def insertion_order(data) -> int:
        return extract_int(data, 'insertion_order', def_out=0)

    def case_sensitive(data) -> bool|None:
        return extract_bool(data, 'case_sensitive', def_out=None)

    def name(data) -> str|None:
        return extract_str(data, 'name', def_out=None)

    def priority(data) -> int|None:
        return extract_int(data, 'priority', def_out=None)

    def id(data) -> int|None:
        return extract_int(data, 'id', def_out=None)

    def comment(data) -> str|None:
        return extract_str(data, 'comment', def_out=None)

    def selective(data) -> bool|None:
        return extract_bool(data, 'selective', def_out=None)

    def secondary_keys(data) -> list[str]|None:
        return extract_tags(data, 'secondary_keys', def_out=None)

    def constant(data) -> bool|None:
        return extract_bool(data, 'constant', def_out=None)

    def position(data) -> str|None:
        VALUES = ('before_char', 'after_char')
        value = extract_str(data, 'position', def_out=None)
        if value is None:
            return None
        value = value.lower()
        assert value in VALUES, ('If defined, position must be one of: ' +
                                 ', '.join(VALUES))
        return value

    def extensions(data) -> dict:
        return extract_json(data, 'extensions', def_out={})


@parse_class('|', None)
class CharacterBook:
    def name(data) -> str|None:
        return extract_str(data, 'name', def_out=None)

    def description(data) -> str|None:
        return extract_str(data, 'description', def_out=None)

    def scan_depth(data) -> int|None:
        return extract_int(data, 'scan_depth', def_out=None)

    def token_budget(data) -> int|None:
        return extract_int(data, 'token_budget', def_out=None)

    def recursive_scanning(data) -> bool|None:
        return extract_bool(data, 'recursive_scanning', def_out=None)

    def entries(data) -> list[CharacterBookEntry]:
        value = extract_raw(data, 'entries', def_out=[])
        assert isinstance(value, list), f'entries must be a list'
        return list(CharacterBookEntry(x) for x in value)

    def extensions(data) -> dict:
        return extract_json(data, 'extensions', def_out={})


@parse_class('@', '$')
class CardV2:
    def __init__(self):
        data = self.__dict__
        self.__dict__ = {}
        self.spec = 'chara_card_v2'
        self.spec_version = '2.0'
        self.data = data
        self.metadata = get_metadata()

    def name(data) -> str:
        return extract_str(data, 'name', req_in=True, non_empty=True)

    def description(data) -> str:
        return minify_content(extract_str(data, 'description', def_out=''))

    def personality(data) -> str:
        return extract_str(data, 'personality', def_out='')

    def scenario(data) -> str:
        return extract_str(data, 'scenario', def_out='')

    def first_mes(data) -> str:
        # If first_mes isn't defined but there is at least
        # one alternate greeting...
        if 'first_mes' not in data \
           and 'alternate_greetings' in data \
           and isinstance(data['alternate_greetings'], list) \
           and data['alternate_greetings']:
            # Take the first alternate greeting as first_mes
            data['first_mes'] = extract(data['alternate_greetings'], 0)

        return extract_str(data, 'first_mes', req_in=False, def_out='')

    def mes_example(data) -> str:
        return extract_str(data, 'mes_example', def_out='')

    def creator_notes(data) -> str:
        return extract_str(data, 'creator_notes', def_out='')

    def system_prompt(data) -> str:
        return extract_str(data, 'system_prompt', def_out='')

    def post_history_instructions(data) -> str:
        return extract_str(data, 'post_history_instructions', def_out='')

    def alternate_greetings(data) -> list[str]:
        value = extract_raw(data, 'alternate_greetings', def_out=[])
        assert isinstance(value, list), 'alternate_greetings must be a list'
        return list(x for x in (deep_strip(x) for x in value) if x != '')

    def tags(data) -> list[str]:
        return extract_tags(data, 'tags', def_out=[])

    def creator(data) -> str:
        return extract_str(data, 'creator', def_out='')

    def character_version(data) -> str:
        return extract_str(data, 'character_version', def_out='')

    def extensions(data) -> dict:
        return extract_json(data, 'extensions', def_out={})

    def character_book(data) -> CharacterBook|None:
        cb = CharacterBook(extract_raw(data, 'character_book', def_out=''),
                           entries=extract_raw(data, 'entries', def_out=[]))
        return None if cb.__dict__ == {'entries': [], 'extensions': {}} else cb


@parse_class('@', '$')
class CardV1:
    def __init__(self):
        self.metadata = get_metadata()

    def name(data) -> str:
        return extract_str(data, 'name', req_in=True, non_empty=True)

    def description(data) -> str:
        return minify_content(extract_str(data, 'description', def_out=''))

    def personality(data) -> str:
        return extract_str(data, 'personality', def_out='')

    def scenario(data) -> str:
        return extract_str(data, 'scenario', def_out='')

    def first_mes(data) -> str:
        return extract_str(data, 'first_mes', req_in=False, def_out='')

    def mes_example(data) -> str:
        return extract_str(data, 'mes_example', def_out='')


@parse_class('@', '$')
class Formatted:
    def description(data) -> str:
        return minify_content(extract_str(data, 'description', def_out=''))


def parse(raw, key_mark, const_mark, default_key, silent=False):
    data = {}
    consts = {}
    key = None

    def warn(text):
        if not silent:
            print(f'Warning: {text}', file=sys.stderr)

    for line in raw.split('\n'):
        line = line.strip() + '\n'

        if line.startswith('#'):
            continue

        if const_mark is not None and line.startswith(const_mark):
            const = (line[len(const_mark):] + ' ').split(' ')
            name = const[0].strip().lower()
            if name == '':
                warn(f'Unnamed constant, ignoring')
                continue
            if not name[0].isalpha():
                warn(f'Constant names doesn\'t start with a letter: {name}, ignoring')
                continue
            if not name.replace('_', '').isalnum():
                warn(f'Constant names must be alphanumeric: {name}, ignoring')
                continue
            if name in consts:
                warn(f'Duplicate const name: {name}, overwriting')
            consts[name] = ' '.join(const[1:]).strip()
            continue

        if line.startswith(key_mark):
            line = line[len(key_mark):]
            parts = line.split(' ')

            if not parts or parts[0] == '':
                warn(f'Empty data key, ignoring')
                continue

            key = parts[0].strip()
            value = ' '.join(parts[1:])

            if key[-1] == '+':
                # Adding to list
                bkey = key[:-1]
                if bkey in data and not isinstance(data[bkey], list):
                    warn(f'Duplicate data key: {bkey}, overwriting')
                    del data[bkey]
                if bkey not in data:
                    data[bkey] = []
                data[bkey].append('')
            else:
                # Defining string
                if key in data:
                    warn(f'Duplicate data key: {key}, overwriting')
                data[key] = ''
        else:
            value = line

        if key is None:
            if default_key not in data and value.strip() != '':
                key = default_key
                data[key] = ''
            else:
                continue

        if key[-1] == '+':
            data[key[:-1]][-1] += value
        else:
            data[key] += value

    for name, value in consts.items():
        for key in data:
            if isinstance(data[key], list):
                continue
            data[key] = re.sub('{{\$' + name + '}}', value, data[key], flags=re.I)

    return data


def main():
    CARD_EXT = '.card'
    IMAGE_EXT = '.png'
    sys.stdout.reconfigure(encoding='utf-16')

    def only_one(*args):
        val = False
        for arg in args:
            if val and arg:
                return False
            val ^= arg
        return val

    def has_card_ext(fname):
        return fname.lower().endswith(CARD_EXT.lower())

    def get_base_name(fname):
        if has_card_ext(fname):
            return fname[:-len(CARD_EXT)]
        return fname

    def get_image_name(fname):
        return get_base_name(fname) + IMAGE_EXT

    def load_file(src, cls, **kwargs):
        with open(src, encoding='utf-8') as f:
            return cls(f.read(), **kwargs)

    DEFAULT_WIDTH = 400
    DEFAULT_HEIGHT = 600

    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str,
                        help='.card file or directory with .card files')

    parser.add_argument('output', nargs='?', type=str,
                        help='output file name or directory')

    parser.add_argument('--width', nargs='?', type=int,
                        const=DEFAULT_WIDTH, default=DEFAULT_WIDTH,
                        help='max output image width, 0 for no limit '
                            f'(default {DEFAULT_WIDTH})')

    parser.add_argument('--height', nargs='?', type=int,
                        const=DEFAULT_HEIGHT, default=DEFAULT_HEIGHT,
                        help='max output image height, 0 for no limit '
                            f'(default {DEFAULT_HEIGHT})')

    parser.add_argument('--fullres', action='store_true',
                        help='don\'t resize output image')

    parser.add_argument('-d', '--description', action='store_true',
                        help='only parse description')

    parser.add_argument('-j', '--json', action='store_true',
                        help='only print resulting json to stdout')

    parser.add_argument('--v1', action='store_true',
                        help='export Character Card V1 (legacy)')

    args = parser.parse_args()

    assert only_one(args.description, args.json, bool(args.output)), \
            'Must only define one of: description, json, output'

    isFile = os.path.isfile(args.input)

    assert isFile or not args.json, \
            'If json is set, input must be a file'

    assert isFile or not args.description, \
            'If description is set, input must be a file'

    assert not args.description or not args.json, \
            'description and json can not both be set'

    assert isFile or os.path.isdir(args.input), \
            'Input must be an existing file or directory'

    assert isFile or not os.path.isfile(args.output), \
            'If input is a directory, output must not be a file'

    assert not isFile \
            or not bool(args.output) \
            or not os.path.isdir(args.output), \
            'If input is a file, output must not be a directory'

    cls = CardV1 if args.v1 else CardV2

    if args.description:
        print(load_file(args.input, Formatted, _silent=True).description)
        return

    if args.json:
        print(json.dumps(load_file(args.input, cls), default=vars, indent=2))
        return

    if args.fullres:
        args.width = args.height = 0

    if isFile:
        save_image(load_file(args.input, cls),
                   get_image_name(args.input),
                   args.output,
                   (args.width, args.height))
    else:
        targets = []
        for file in os.listdir(args.input):
            card_path = os.path.join(args.input, file)

            if not has_card_ext(file) or not os.path.isfile(card_path):
                continue
            if not os.path.isdir(args.output):
                os.mkdir(args.output)

            pairs = []
            target = (card_path, pairs)

            i = 0
            file_base = get_base_name(file)
            while True:
                image_name = (file_base +
                              ('' if i == 0 else f'-{i}') +
                              IMAGE_EXT)
                image_path = os.path.join(args.input, image_name)
                if not os.path.isfile(image_path):
                    break;
                pairs.append((image_path,
                              os.path.join(args.output, image_name)))
                i += 1

            targets.append(target)

        for src, pairs in targets:
            for img, dst in pairs:
                save_image(load_file(src, cls), img, dst,
                           (args.width, args.height))

if __name__ == '__main__':
    main()
