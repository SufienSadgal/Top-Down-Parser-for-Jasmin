import re
import sys

# Definizione dei token (Terminali della grammatica Jasmin)
TOKEN_TYPES = [
    # 1. Letterali e Identificatori Complessi
    ('STRING',        r'"[^"\\]*(?:\\.[^"\\]*)*"'), # Stringhe racchiuse tra ""
    ('INT',           r'0[xX][0-9a-fA-F]+|\d+'),    # Interi (esadecimali o decimali)
    
    # 2. Parole Chiave (Keywords) - Ordinate per lunghezza decrescente
    ('UNALIGNED',     r'\bunaligned\b'),
    ('NAMESPACE',     r'\bnamespace\b'),
    ('CONSTANT',      r'\bconstant\b'),
    ('ARRAYINIT',     r'\barrayinit\b'),
    ('DOWNTO',        r'\bdownto\b'),
    ('REQUIRE',       r'\brequire\b'),
    ('ALIGNED',       r'\baligned\b'),
    ('ASSERT',        r'\bassert\b'),
    ('MUTABLE',       r'\bmutable\b'),
    ('POINTER',       r'\bptr\b'),
    ('EXPORT',        r'\bexport\b'),
    ('INLINE',        r'\binline\b'),
    ('RETURN',        r'\breturn\b'),
    ('GLOBAL',        r'\bglobal\b'),
    ('STACK',         r'\bstack\b'),
    ('WHILE',         r'\bwhile\b'),
    ('FALSE',         r'\bfalse\b'),
    ('PARAM',         r'\bparam\b'),
    ('TRUE',          r'\btrue\b'),
    ('ELSE',          r'\belse\b'),
    ('TYPE',          r'\btype\b'),
    ('FROM',          r'\bfrom\b'),
    ('REG',           r'\breg\b'),
    ('FOR',           r'\bfor\b'),
    ('FN',            r'\bfn\b'),
    ('IF',            r'\bif\b'),
    ('TO',            r'\bto\b'),                  # Parola chiave per cicli FOR

    # 3. Tipi Primitivi e Cast (Jasmin specific)
    ('T_BOOL',        r'\bbool\b'),
    ('T_INT',         r'\bint\b'),
    ('T_W',           r'\bu(8|16|32|64|128|256)\b'), # Parola macchina (es: u64)
    ('SWSIZE',        r'\bs(8|16|32|64|128|256)\b'), # Dimensione segno
    ('SVSIZE',        r'\bv(8|16|32|64|128|256)\b'), # Dimensione vettore
    
    # Identificatore generico (NID) - Deve stare DOPO le parole chiave
    ('NID',           r'[a-zA-Z_][a-zA-Z0-9_]*'),

    # 4. Operatori Composti e Specifici Jasmin
    ('SHARPLBRACKET', r'#\['),
    ('COLONCOLON',    r'::'),
    ('PIPEPIPE',      r'\|\|'),
    ('AMPAMP',        r'&&'),
    ('BANGEQ',        r'!='),
    ('EQEQ',          r'=='),
    ('RARROW',        r'->'),
    ('LTLT',          r'<<r|<<'),
    ('GTGT',          r'>>r|>>'),
    ('LE',            r'<='),
    ('GE',            r'>='),
    ('XOREQ',         r'\^='),                     # Assegnamento bitwise XOR (^=)

    # 5. Operatori Singoli e Punteggiatura
    ('LBRACKET',      r'\['),
    ('RBRACKET',      r'\]'),
    ('LBRACE',        r'\{'),
    ('RBRACE',        r'\}'),
    ('LPAREN',        r'\('),
    ('RPAREN',        r'\)'),
    ('SHARP',         r'#'),
    ('AMP',           r'&'),
    ('BANG',          r'!'),
    ('COLON',         r':'),
    ('COMMA',         r','),
    ('DOT',           r'\.'),
    ('EQ',            r'='),
    ('HAT',           r'\^'),
    ('LT',            r'<'),
    ('GT',            r'>'),
    ('MINUS',         r'-'),
    ('PLUS',          r'\+'),
    ('STAR',          r'\*'),
    ('SLASH',         r'/'),
    ('PERCENT',       r'%'),
    ('PIPE',          r'\|'),
    ('QUESTIONMARK',  r'\?'),
    ('SEMICOLON',     r';'),
    ('UNDERSCORE',    r'_'),
]

class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, '{self.value}', Line:{self.line}, Col:{self.column})"

class Lexer:
    def __init__(self, source_code):
        self.source_code = source_code
        self.tokens = []
        self.line = 1
        self.line_start = 0

    def tokenize(self):
        pos = 0
        length = len(self.source_code)
        
        # Compiliamo le regex per efficienza
        compiled_rules = [(type, re.compile(pattern)) for type, pattern in TOKEN_TYPES]
        
        # Regex per spazi bianchi, nuove linee e commenti
        whitespace_re = re.compile(r'[ \t]+')
        newline_re = re.compile(r'\n')
        comment_single_re = re.compile(r'//[^\n]*')
        comment_multi_re = re.compile(r'/\*.*?\*/', re.DOTALL)

        while pos < length:
            # 1. Spazi bianchi
            match = whitespace_re.match(self.source_code, pos)
            if match:
                pos = match.end()
                continue

            # 2. Nuove Linee
            match = newline_re.match(self.source_code, pos)
            if match:
                self.line += 1
                pos = match.end()
                self.line_start = pos
                continue

            # 3. Commenti Singoli (//)
            match = comment_single_re.match(self.source_code, pos)
            if match:
                pos = match.end()
                continue

            # 4. Commenti Multilinea (/* ... */)
            match = comment_multi_re.match(self.source_code, pos)
            if match:
                self.line += match.group(0).count('\n')
                pos = match.end()
                if '\n' in match.group(0):
                    self.line_start = self.source_code.rfind('\n', 0, pos) + 1
                continue

            # 5. Matching Token Grammatica
            match_found = False
            for token_type, regex in compiled_rules:
                match = regex.match(self.source_code, pos)
                if match:
                    value = match.group(0)
                    column = (pos - self.line_start) + 1
                    
                    token = Token(token_type, value, self.line, column)
                    self.tokens.append(token)
                    
                    pos = match.end()
                    match_found = True
                    break

            if not match_found:
                column = (pos - self.line_start) + 1
                print(f"Errore Lessicale: Carattere non valido '{self.source_code[pos]}' alla riga {self.line}, colonna {column}", file=sys.stderr)
                sys.exit(1)

        # Fine file (EOF)
        column = (pos - self.line_start) + 1
        self.tokens.append(Token('EOF', 'EOF', self.line, column))
        return self.tokens