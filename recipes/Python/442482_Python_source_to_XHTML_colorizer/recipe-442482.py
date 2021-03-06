# -*- coding: utf-8 -*-
"""
    Colorize - Python source formatter that outputs Python code in XHTML.
    This script is based on MoinMoin - The Python Source Parser.

    Usage:
    colorize.py [source file name] [optional author name]
"""

# Imports
import cgi
import string
import sys
import cStringIO
import keyword
import token
import tokenize
import re
import os

#Filepath of source file from command line parameter.  
sourcefile = sys.argv[1]

#Get file name of source file.  
filename = os.path.split(sourcefile)[1]

#Get optional author name parameter (it is added to the DC metadata)
if len(sys.argv)> 2:
    authorname = sys.argv[2]
else:
    authorname = "Unknown"

#Set up basic values.  
_KEYWORD = token.NT_OFFSET + 1
_TEXT    = token.NT_OFFSET + 2

_classes = {
    token.NUMBER:       'token_number',
    token.OP:           'token_op',
    token.STRING:       'token_string',
    tokenize.COMMENT:   'token_comment',
    token.NAME:         'token_name',
    token.ERRORTOKEN:   'token_error',
    _KEYWORD:           'keyword',
    _TEXT:              'text',
}

_DEFAULTENCODING = "utf-8"

#Define start of XHtml document.  
docstart = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
    <head>"""


#Add css from file to output document.  
docstart += """\n\t<style type="text/css">\n"""
cssfile = open("colorize.css", "r")
docstart += cssfile.read()
docstart += """\n\t</style>\n"""

#Close Xhtml document.  
docend = "\n\t</body>\n</html>"

#Set default encoding for output document.  
docencoding = _DEFAULTENCODING


def getEncodingOfFile(sourcefile):
    """Get encoding of source file. If no encoding found, returns _DEFAULTENCODING."""
    myfile = file(sourcefile)
    line = myfile.readline()

    #try line 1
    encoding = parseEncoding(line)

    #encoding found?
    if encoding != "":
        return encoding

    #if not - try line two
    line = myfile.readline()
    encoding = parseEncoding(line)

    #encoding found?
    if encoding != "":
        return encoding

    #if not - try BOM
    if myfile.encoding != None:
        return myfile.encoding

    #if not - return default encoding
    return _DEFAULTENCODING



def parseEncoding(textline):
    """Parse encoding from textline."""
    #Check line for encoding match
    regex = re.compile("coding[=:]\s*([-\w.]+)")
    match = regex.search(textline, 1)

    if match != None:
        #Return found encoding
        return match.group(1)
    else:
        #return default
        return ""



class Parser:
    """ Send colored python source.
    """

    def __init__(self, raw, out = sys.stdout):
        """ Store the source text.
        """
        self.raw = string.strip(string.expandtabs(raw))
        self.out = out

    def format(self, formatter, form):
        """ Parse and send the colored source.
        """
        # store line offsets in self.lines
        self.lines = [0, 0]
        pos = 0
        while 1:
            pos = string.find(self.raw, '\n', pos) + 1
            if not pos: break
            self.lines.append(pos)
        self.lines.append(len(self.raw))

        # parse the source and write it
        self.out.write(docstart)

        # write metadata
        self.out.write("\n<title>" + filename + "</title>\n")
        self.out.write('<link rel="schema.DC" href="http://purl.org/DC/elements/1.0/" />\n')
        self.out.write('<meta name="DC.Language" content="en" />\n')
        self.out.write('<meta name="DC.Format" content="text/html" />\n')
        self.out.write('<meta name="DC.Type" content="Software" />\n')
        self.out.write('<meta name="DC.Title" content="Python source of %s" />\n' % filename)
        self.out.write('<meta name="DC.Creator" content="%s" />\n' % authorname)

        #encoding
        self.out.write('<meta http-equiv="Content-Type" content="text/html; charset=%s" />\n' % docencoding)

        #Close head and begin body.  
        self.out.write("\n\t</head>\n<body>")

        self.pos = 0
        text = cStringIO.StringIO(self.raw)
        self.out.write('<pre><code>')
        try:
            tokenize.tokenize(text.readline, self)
        except tokenize.TokenError, ex:
            msg = ex[0]
            line = ex[1][0]
            self.out.write("<h3>ERROR: %s</h3>%s\n" % (
                msg, self.raw[self.lines[line]:]))
        self.out.write('</code></pre>\n')

        self.out.write(docend)

    def __call__(self, toktype, toktext, (srow,scol), (erow,ecol), line):
        """ Token handler.
        """
        if 0:
            print "type", toktype, token.tok_name[toktype], "text", toktext,
            print "start", srow, scol, "end", erow, ecol, "<br />"

        # calculate new positions
        oldpos = self.pos
        newpos = self.lines[srow] + scol
        self.pos = newpos + len(toktext)

        # handle newlines
        if toktype in [token.NEWLINE, tokenize.NL]:
            self.out.write('\n')
            return

        # send the original whitespace, if needed
        if newpos > oldpos:
            self.out.write(self.raw[oldpos:newpos])

        # skip indenting tokens
        if toktype in [token.INDENT, token.DEDENT]:
            self.pos = newpos
            return

        # map token type to a color/class group
        if token.LPAR <= toktype and toktype <= token.OP:
            toktype = token.OP
        elif toktype == token.NAME and keyword.iskeyword(toktext):
            toktype = _KEYWORD
        classval = _classes.get(toktype, _classes[_TEXT])

        style = ''
        if toktype == token.ERRORTOKEN:
            style = ' style="border: solid 1.5pt #FF0000;"'

        # send text
        self.out.write('<span class="%s"%s>' % (classval, style))
        self.out.write(cgi.escape(toktext))
        self.out.write('</span>')


if __name__ == "__main__":
    import os, sys
    print "Formatting " + sourcefile

    #Set up encoding
    docencoding = getEncodingOfFile(sourcefile)

    # open own source
    source = open(sourcefile).read()

    # write colorized version to "[filename].py.html"
    Parser(source, open(sourcefile + '.html', 'wt')).format(None, None)

    # done!
    print "Done! Wrote result file " + sourcefile + ".html"
