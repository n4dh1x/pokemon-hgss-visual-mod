"""Append owned English text using pinned HGSS msgenc's native bank format."""
import struct


def entries(data):
    if len(data) < 4 or len(data) % 2:
        raise ValueError('Malformed native message bank.')
    count, key = struct.unpack_from('<HH', data)
    if 4 + 8 * count > len(data):
        raise ValueError('Native message table exceeds bank.')
    out = []
    for index in range(count):
        mask = (765 * (index + 1) * key) & 0xFFFF
        mask |= mask << 16
        start, length = [n ^ mask for n in struct.unpack_from('<II', data, 4 + index * 8)]
        if start < 4 + count * 8 or start + length * 2 > len(data) or not length:
            raise ValueError('Native message span exceeds bank.')
        out.append((start, length))
    return key, out


def encode_english(text):
    codes = []
    for char in text:
        if 'A' <= char <= 'Z': code = 299 + ord(char) - ord('A')
        elif 'a' <= char <= 'z': code = 325 + ord(char) - ord('a')
        elif char == ' ': code = 478
        elif char == '.': code = 430
        elif char == '!': code = 427
        elif char == '\n': code = 0xE000
        else: raise ValueError(f'Unsupported owned message character: {char!r}')
        codes.append(code)
    return codes + [0xFFFF]


def append_message(data, text):
    key, old = entries(data)
    if len(old) >= 0xFFFF:
        raise ValueError('Native message count overflow.')
    codes = encode_english(text)
    seed = ((len(old) + 1) * 596947) & 0xFFFF
    encoded = []
    for code in codes:
        encoded.append(code ^ seed)
        seed = (seed + 18749) & 0xFFFF
    spans = [(offset + 8, length) for offset, length in old]
    spans.append((len(data) + 8, len(codes)))
    table = bytearray(struct.pack('<HH', len(spans), key))
    for index, (offset, length) in enumerate(spans, 1):
        mask = (765 * index * key) & 0xFFFF
        mask |= mask << 16
        table.extend(struct.pack('<II', offset ^ mask, length ^ mask))
    result = bytes(table) + data[4 + len(old) * 8:] + struct.pack(f'<{len(encoded)}H', *encoded)
    # Preserve every existing encrypted message and all non-table tail bytes.
    _, new = entries(result)
    if any(data[a:a+n*2] != result[b:b+m*2] or n != m for (a,n),(b,m) in zip(old,new)):
        raise ValueError('Existing native message changed while appending text.')
    return result
