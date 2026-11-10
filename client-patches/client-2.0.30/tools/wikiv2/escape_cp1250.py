# -*- coding: utf-8 -*-
# MT2009_PLUS_WIKI_V1 - writes a client root module from its UTF-8 source with every non-ASCII letter of its string
# literals as a CP1250 escape (the client's Python 2.7 reads the texts as CP1250 bytes; root files stay ASCII -
# tools/uicheck/verify_root_encoding.py). Comments must be ASCII already.
#   python3 escape_cp1250.py <source.py (UTF-8)> <root/module.py>
import io
import sys
import tokenize


def escape(src):
	out = []
	last = (1, 0)
	lines = src.splitlines(True)
	toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
	for tok in toks:
		if tok.type == tokenize.STRING and any(ord(c) > 127 for c in tok.string):
			text = ''.join(c if ord(c) < 128 else ''.join('\\x%02x' % b for b in c.encode('cp1250')) for c in tok.string)
			out.append((tok.start, tok.end, text))
		elif tok.type == tokenize.COMMENT and any(ord(c) > 127 for c in tok.string):
			raise SystemExit('non-ASCII comment at line %d' % tok.start[0])
	if not out:
		return src
	# rebuild with the replaced tokens
	res = []
	row, col = 1, 0
	def take(to_row, to_col):
		nonlocal row, col
		while row < to_row:
			res.append(lines[row - 1][col:])
			row += 1
			col = 0
		res.append(lines[row - 1][col:to_col])
		col = to_col
	for (sr, sc), (er, ec), text in out:
		take(sr, sc)
		res.append(text)
		row, col = er, ec
	take(len(lines), len(lines[-1]))
	return ''.join(res)


def main():
	src = open(sys.argv[1], encoding='utf-8').read()
	dst = escape(src)
	dst.encode('ascii')
	open(sys.argv[2], 'w', encoding='ascii', newline='\n').write(dst)


if __name__ == '__main__':
	main()
