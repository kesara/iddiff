from argparse import ArgumentParser
from difflib import _mdiff as mdiff
from re import compile
from string import whitespace
from sys import stdout

SKIPS = [
    compile(r'^.*\[?[Pp]age [0-9ivx]+\]?[ \t\f]*$'),
    compile(r'^ *Internet.Draft.+[12][0-9][0-9][0-9] *$'),
    compile(r'^ *INTERNET.DRAFT.+[12][0-9][0-9][0-9] *$'),
    compile(r'^ *Draft.+(  +)[12][0-9][0-9][0-9] *$'),
    compile(r'^RFC[ -]?[0-9]+.*(  +).* [12][0-9][0-9][0-9]$'),
    compile(r'^draft-[-a-z0-9_.]+.*[0-9][0-9][0-9][0-9]$')]

HTML = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title></title>
    <style>
      body {{font-family: monospace}}
      td {{
        white-space: pre;
        vertical-align: top;
        font-size: 0.86em;
      }}
      th {{
        text-align: center;
      }}
      .left {{ background-color: #EEE; }}
      .right {{ background-color: #FFF; }}
      .lblock {{ background-color: #BFB; }}
      .rblock {{ background-color: #FF8; }}
      .delete {{ background-color: #ACF; }}
      .insert {{ background-color: #8FF; }}
      .change {{ background-color: gray; }}
    </style>
  </head>
  <body>
    <table cellspacing="0" cellpadding="0">
     {rows}
    </table>
  </body>
</html>"""

UNCHANGED_ROW = """
      <tr>
        <td>&nbsp;</td>
        <td class="left">{lline}</td>
        <td>&nbsp;</td>
        <td class="right">{rline}</td>
      </tr>"""

CHANGED_ROW = """
      <tr>
        <td>&nbsp;</td>
        <td class="lblock">{lline}</td>
        <td>&nbsp;</td>
        <td class="rblock">{rline}</td>
      </tr>"""

CONTEXT_LINE = """
      <tr>
        <td>&nbsp;</td>
        <td class="left">&nbsp;</td>
        <td>&nbsp;</td>
        <td class="right">&nbsp;</td>
      </tr>
      <tr>
        <td></td>
        <th class="change"><small>Skipping</small></th>
        <td></td>
        <th class="change"><small>Skipping</small></th>
      </tr>"""

WHITESPACES = ''.join([
    whitespace,  # python stirng.whitespace
    '\u0009',    # character tabulation
    '\u000A',    # line feed
    '\u000B',    # line tabulation
    '\u000C',    # form feed
    '\u000D',    # carriage return
    '\u0020',    # space
    '\u0085',    # next line
    '\u00A0',    # no-break space
    '\u1680',    # ogham space mark
    '\u2000',    # en quad
    '\u2001',    # em quad
    '\u2002',    # en space
    '\u2003',    # em space
    '\u2004',    # three-per-em space
    '\u2005',    # four-per-em space
    '\u2006',    # six-per-em space
    '\u2007',    # figure space
    '\u2008',    # punctuation space
    '\u2009',    # thin space
    '\u200A',    # hair space
    '\u2028',    # line separator
    '\u2029',    # paragraph separator
    '\u202F',    # narrow no-break space
    '\u205F',    # medium mathematical space
    '\u3000',    # ideographic space
    '\u180E',    # mongolian vowel separator
    '\u200B',    # zero width space
    '\u200C',    # zero width non-joiner
    '\u200D',    # zero width joiner
    '\u2060',    # word joiner
    '\uFEFF'])   # zero width non-breaking space


def cleanup(lines):
    id_lines = []
    previous_blank = False
    for line in lines:
        if len(line.strip(WHITESPACES)) > 0:
            previous_blank = False
            keep = True
            for skip in SKIPS:
                if skip.match(line):
                    keep = False
                    break
            if keep:
                id_lines.append(line)
        elif not previous_blank:
            id_lines.append(line.strip(WHITESPACES))
            previous_blank = True
    return id_lines


def add_span(line, css_class):
    stripped_line = line.strip('\0+-^\1').strip(WHITESPACES)
    if len(stripped_line) == 0:
        return ''
    else:
        return line.replace('\0+', '<span class="{}">'.format(css_class)). \
                    replace('\0-', '<span class="{}">'.format(css_class)). \
                    replace('\0^', '<span class="{}">'.format(css_class)). \
                    replace('\1', '</span>')


def main():
    parser = ArgumentParser(description='ID Diff')
    parser.add_argument('-c', '--context', action='store_true', default=False,
                        help='Produce a context')
    parser.add_argument('-l', '--lines', type=int, default=8,
                        help='Set number of context lines (default 8)')
    parser.add_argument('file1')
    parser.add_argument('file2')
    options = parser.parse_args()

    file1 = options.file1
    file2 = options.file2
    if options.context:
        context_lines = options.lines
    else:
        context_lines = None

    with open(file1, 'r') as file:
        id_a_lines = cleanup(file.readlines())
    with open(file2, 'r') as file:
        id_b_lines = cleanup(file.readlines())

    rows = ''
    diffs = mdiff(id_a_lines, id_b_lines, context=context_lines)
    for lb, rb, different in diffs:
        if not lb or not rb:
            rows += CONTEXT_LINE
        elif not different:
            rows += UNCHANGED_ROW.format(lline=lb[1], rline=rb[1])
        else:
            lline = add_span(lb[1], 'delete')
            rline = add_span(rb[1], 'insert')
            if len(lline) > 0 or len(rline) > 0:
                rows += CHANGED_ROW.format(lline=lline, rline=rline)
    rows.replace('\t', '&nbsp;')
    stdout.writelines(HTML.format(rows=rows))


if __name__ == '__main__':
    main()
