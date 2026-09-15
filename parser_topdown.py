import sys
from lexer import Lexer
# lexer prende le stringhe e le trasforma in una sequenza di token
# parser prende la sequenza di token e prova (usando le regole di derivazione disponibili) a trasformarla in un albero sintattico 

# =====================================================================
# 1. NODI SYNTAX TREE
# =====================================================================

class ASTNode:
    def print_tree(self, level=0):
        raise NotImplementedError
# nodo genitore, tutti i nodi figli devono implementare il metodo print_tree che stampa un pezzo di albero in base alla regola usata

class ProgramNode(ASTNode):
 # rappresenta la regola di derivazione dell'intero programma, può essere espansa con una lista qualsiasi di 
 # require (per files) e definizioni di funzioni e variabili globali
    def __init__(self, requires, functions_and_globals):
        self.requires = requires
        self.functions_and_globals = functions_and_globals

    def print_tree(self, level=0):
        print("  " * level + "└── Program")
        for req in self.requires:
            req.print_tree(level + 1)
        for fg in self.functions_and_globals:
            fg.print_tree(level + 1)

class RequireNode(ASTNode):
# nel caso di import di un file salva il percorso di tale file
    def __init__(self, path):
        self.path = path

    def print_tree(self, level=0):
        print("  " * level + f"└── Require: {self.path}")

class ParamDeclNode(ASTNode):
# riconosce la definizione di costanti 
    def __init__(self, type_name, name, expr):
        self.type_name = type_name
        self.name = name
        self.expr = expr

    def print_tree(self, level=0):
        print("  " * level + f"└── ParamDecl: {self.type_name} {self.name}")
        self.expr.print_tree(level + 1)

class FunctionNode(ASTNode):
# Rappresenta una funzione del tipo " fn name(...) -> ... { ... } "
    def __init__(self, annotation, call_conv, name, args, ret_types, body):
        self.annotation = annotation
        self.call_conv = call_conv
        self.name = name
        self.args = args
        self.ret_types = ret_types
        self.body = body

    def print_tree(self, level=0):
        annot_str = f" [{self.annotation}]" if self.annotation else ""
        cc_str = f" ({self.call_conv})" if self.call_conv else ""
        print("  " * level + f"└── Function: {self.name}{annot_str}{cc_str}")
        print("  " * (level + 1) + "├── Args")
        for arg in self.args:
            print("  " * (level + 2) + f"└── {arg['storage']} {arg['type']} {arg['name']}")
        if self.ret_types:
            types_str = ", ".join(self.ret_types)
            print("  " * (level + 1) + f"├── Returns: ({types_str})")
        self.body.print_tree(level + 1)

class BlockNode(ASTNode):
# Rappresenta un blocco di codice delimitato da parentesi graffe { ... }. 
# Contiene una lista di istruzioni (statements) e un'eventuale istruzione di ritorno finale (return_stmt).
    def __init__(self, statements, return_stmt=None):
        self.statements = statements
        self.return_stmt = return_stmt

    def print_tree(self, level=0):
        print("  " * level + "└── Block")
        for stmt in self.statements:
            stmt.print_tree(level + 1)
        if self.return_stmt:
            self.return_stmt.print_tree(level + 1)

class VarDeclNode(ASTNode):
# dichiarazione di una o più variabili
    def __init__(self, storage, type_name, var_names):
        self.storage = storage
        self.type_name = type_name
        self.var_names = var_names if isinstance(var_names, list) else [var_names]

    def print_tree(self, level=0):
        names_str = ", ".join(self.var_names)
        print("  " * level + f"└── Decl: {self.storage} {self.type_name} [{names_str}]")

class AssignNode(ASTNode):
# Rappresenta un assegnamento (es. x = y + 1; o x += 2;).

    def __init__(self, left, op, right, annotation=None):
        self.left = left if isinstance(left, list) else [left]
        # Nota che self.left è una lista, perché Jasmin supporta assegnamenti multipli (es. x, y = foo();).
        self.op = op
        self.right = right
        self.annotation = annotation

    def print_tree(self, level=0):
        annot_str = f" [{self.annotation}]" if self.annotation else ""
        print("  " * level + f"└── Assign{annot_str} ({self.op})")
        print("  " * (level + 1) + "├── Targets")
        for t in self.left:
            if isinstance(t, ASTNode):
                t.print_tree(level + 2)
            else:
                print("  " * (level + 2) + f"└── {t}")
        print("  " * (level + 1) + "└── Value")
        self.right.print_tree(level + 2)

class FlagNode(ASTNode):
# Modella i flag della CPU di x86/assembly (es. cf, zf) o il flag jolly/ignorato 
    def __init__(self, name):
        self.name = name

    def print_tree(self, level=0):
        print("  " * level + f"└── Flag: {self.name}")

class ForNode(ASTNode):
# ciclo for
    def __init__(self, var_name, start_expr, direction, end_expr, step_expr, body):
        self.var_name = var_name
        self.start_expr = start_expr
        self.direction = direction
        self.end_expr = end_expr
        self.step_expr = step_expr
        self.body = body

    def print_tree(self, level=0):
        print("  " * level + f"└── ForLoop: {self.var_name} ({self.direction})")
        print("  " * (level + 1) + "├── Start")
        self.start_expr.print_tree(level + 2)
        print("  " * (level + 1) + "├── End")
        self.end_expr.print_tree(level + 2)
        if self.step_expr:
            print("  " * (level + 1) + "├── Step")
            self.step_expr.print_tree(level + 2)
        print("  " * (level + 1) + "└── Body")
        self.body.print_tree(level + 2)

class IfNode(ASTNode):
# costrutto condizionale if
    def __init__(self, cond, then_body, else_body=None):
        self.cond = cond
        self.then_body = then_body
        self.else_body = else_body

    def print_tree(self, level=0):
        print("  " * level + "└── IfStmt")
        print("  " * (level + 1) + "├── Cond")
        self.cond.print_tree(level + 2)
        print("  " * (level + 1) + "├── Then")
        self.then_body.print_tree(level + 2)
        if self.else_body:
            print("  " * (level + 1) + "└── Else")
            self.else_body.print_tree(level + 2)

class WhileNode(ASTNode):
# ciclo whiel
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

    def print_tree(self, level=0):
        print("  " * level + "└── WhileLoop")
        print("  " * (level + 1) + "├── Cond")
        self.cond.print_tree(level + 2)
        print("  " * (level + 1) + "└── Body")
        self.body.print_tree(level + 2)

class DoWhileNode(ASTNode):
# ciclo do - while
    def __init__(self, body, cond):
        self.body = body
        self.cond = cond

    def print_tree(self, level=0):
        print("  " * level + "└── DoWhileLoop")
        print("  " * (level + 1) + "├── Body")
        self.body.print_tree(level + 2)
        print("  " * (level + 1) + "└── Cond")
        self.cond.print_tree(level + 2)

class BreakNode(ASTNode):
# key word break nei cicli
    def print_tree(self, level=0):
        print("  " * level + "└── Break")

class ContinueNode(ASTNode):
# key word continue nei cicli
    def print_tree(self, level=0):
        print("  " * level + "└── Continue")

class ArrayAccessNode(ASTNode):
# per accedere a un elemento di un array usando l'indice 
    def __init__(self, array_target, indices):
        self.array_target = array_target
        self.indices = indices if isinstance(indices, list) else [indices]

    def print_tree(self, level=0):
        print("  " * level + "└── ArrayAccess")
        if isinstance(self.array_target, ASTNode):
            self.array_target.print_tree(level + 1)
        else:
            print("  " * (level + 1) + f"└── Target: {self.array_target}")
        print("  " * (level + 1) + "└── Indices")
        for idx in self.indices:
            idx.print_tree(level + 2)

class SliceAccessNode(ASTNode):
# estrazione di una porzione di array (per esempio dal terzo al quinto elemento)
    def __init__(self, array_target, slice_type, start_expr, length_or_end_expr):
        self.array_target = array_target
        self.slice_type = slice_type
        self.start_expr = start_expr
        self.length_or_end_expr = length_or_end_expr

    def print_tree(self, level=0):
        print("  " * level + f"└── SliceAccess ({self.slice_type})")
        if isinstance(self.array_target, ASTNode):
            self.array_target.print_tree(level + 1)
        else:
            print("  " * (level + 1) + f"└── Target: {self.array_target}")
        print("  " * (level + 1) + "├── Start/Base")
        self.start_expr.print_tree(level + 2)
        print("  " * (level + 1) + "└── End/Length")
        self.length_or_end_expr.print_tree(level + 2)

class MemAccessNode(ASTNode):
# accesso alla memoria mediante indirizzo esplicito
    def __init__(self, addr_expr, type_name=None, base_var=None):
        self.type_name = type_name
        self.addr_expr = addr_expr
        self.base_var = base_var

    def print_tree(self, level=0):
        t_str = f":{self.type_name}" if self.type_name else ""
        b_str = f" on {self.base_var}" if self.base_var else ""
        print("  " * level + f"└── MemAccess[{t_str}]{b_str}")
        self.addr_expr.print_tree(level + 1)

class TypeCastNode(ASTNode):
# cast esplicito di una variabile
    def __init__(self, target_type, expr):
        self.target_type = target_type
        self.expr = expr

    def print_tree(self, level=0):
        print("  " * level + f"└── TypeCast: ({self.target_type})")
        self.expr.print_tree(level + 1)

class CallNode(ASTNode):
# chiamata a funzione
    def __init__(self, func_name, args, annotation=None):
        self.func_name = func_name
        self.args = args
        self.annotation = annotation

    def print_tree(self, level=0):
        annot_str = f" [{self.annotation}]" if self.annotation else ""
        print("  " * level + f"└── Call: {self.func_name}{annot_str}")
        for arg in self.args:
            arg.print_tree(level + 1)

class ReturnNode(ASTNode):
# key word return seguita da una lista di elementi restituiti da una funzione
    def __init__(self, expressions):
        self.expressions = expressions if isinstance(expressions, list) else ([expressions] if expressions else [])

    def print_tree(self, level=0):
        print("  " * level + "└── Return")
        for expr in self.expressions:
            expr.print_tree(level + 1)

class VarNode(ASTNode):
# variabile in un'espressione
    def __init__(self, name):
        self.name = name

    def print_tree(self, level=0):
        print("  " * level + f"└── Var: {self.name}")

class LiteralNode(ASTNode):
# valore costante
    def __init__(self, value, type_lbl):
        self.value = value
        self.type_lbl = type_lbl

    def print_tree(self, level=0):
        print("  " * level + f"└── {self.type_lbl}: {self.value}")

class BinOpNode(ASTNode):
# operazione binaria
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def print_tree(self, level=0):
        print("  " * level + f"└── BinOp: {self.op}")
        self.left.print_tree(level + 1)
        self.right.print_tree(level + 1)

class UnaryOpNode(ASTNode):
# operazione unaria
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

    def print_tree(self, level=0):
        print("  " * level + f"└── UnaryOp: {self.op}")
        self.operand.print_tree(level + 1)

class TernaryNode(ASTNode):
# costrutto condizionale del tipo " cond ? expr1 : expr2 "
    def __init__(self, cond, then_expr, else_expr):
        self.cond = cond
        self.then_expr = then_expr
        self.else_expr = else_expr

    def print_tree(self, level=0):
        print("  " * level + "└── TernaryOp (?:)")
        print("  " * (level + 1) + "├── Cond")
        self.cond.print_tree(level + 2)
        print("  " * (level + 1) + "├── Then")
        self.then_expr.print_tree(level + 2)
        print("  " * (level + 1) + "└── Else")
        self.else_expr.print_tree(level + 2)

class VectorInitNode(ASTNode):
# inizializzazione di array mediante graffe
    def __init__(self, elements):
        self.elements = elements

    def print_tree(self, level=0):
        print("  " * level + "└── VectorInit")
        for elem in self.elements:
            elem.print_tree(level + 1)

class ArrayInitNode(ASTNode):
# inizializzazione di array mediante quadre
    def __init__(self, elements):
        self.elements = elements

    def print_tree(self, level=0):
        print("  " * level + "└── ArrayInit")
        for elem in self.elements:
            elem.print_tree(level + 1)

class VectorPackNode(ASTNode):
# operazioni SIMD specializzate come pack o unpack.
    def __init__(self, op_type, args):
        self.op_type = op_type
        self.args = args

    def print_tree(self, level=0):
        print("  " * level + f"└── SIMD_{self.op_type.upper()}")
        for arg in self.args:
            arg.print_tree(level + 1)

# =====================================================================
# 2. PARSER
# =====================================================================

class Parser:
    CPU_FLAGS = {"cf", "zf", "sf", "of", "pf"}
    PRIMITIVE_TYPES = {
        "u8", "u16", "u32", "u64", "u128", "u256",
        "i8", "i16", "i32", "i64", "i128", "i256",
        "int", "bool"
    }

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0 # indice intero che punta al token corrente nell'array self.tokens.

    def peek(self, k=0):
        if self.pos + k >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos + k]

    def match(self, token_type):
    # Verifica che il token corrente sia del tipo o valore atteso. Se sì, avanza di un passo (self.pos += 1) e lo restituisce. 
    # Se no, ferma l'esecuzione invocando error().
        current = self.peek()
        if current.type == token_type or current.value == token_type:
            self.pos += 1
            return current
        self.error(
            f"Atteso token '{token_type}', trovato '{current.type}' con valore '{current.value}'"
        )
    

    def error(self, message):
        token = self.peek()
        print(
            f"Errore Sintattico alla riga {token.line}, colonna {token.column}: {message}",
            file=sys.stderr,
        )
        sys.exit(1)

    def parse_full_type(self):
        type_name = self.peek().value
        self.pos += 1

        while self.peek().type == "LBRACKET":
            self.match("LBRACKET")
            size_expr = self.parse_expr()
            self.match("RBRACKET")
            if isinstance(size_expr, LiteralNode):
                type_name += f"[{size_expr.value}]"
            else:
                type_name += f"[expr]"
        return type_name

    def parse_module(self):
        requires = []
        globals_and_funcs = []

        while self.peek().type != "EOF":
            tok = self.peek()

            if tok.type == "REQUIRE" or tok.value == "require":
                self.pos += 1
                path = self.peek().value
                self.pos += 1
                if self.peek().type == "SEMICOLON":
                    self.match("SEMICOLON")
                requires.append(RequireNode(path))

            elif tok.type == "PARAM" or tok.value == "param":
                globals_and_funcs.append(self.parse_param_decl())

            elif tok.type in ["T_W", "T_INT", "T_BOOL"] or tok.value in self.PRIMITIVE_TYPES:
                type_name = self.parse_full_type()
                var_name = self.match("NID").value

                if self.peek().type == "EQ":
                    self.match("EQ")
                    init_expr = self.parse_expr()
                    self.match("SEMICOLON")
                    globals_and_funcs.append(
                        AssignNode([VarNode(var_name)], "=", init_expr)
                    )
                else:
                    self.match("SEMICOLON")
                    globals_and_funcs.append(
                        VarDeclNode("global", type_name, [var_name])
                    )
            else:
                globals_and_funcs.append(self.parse_pfundef())

        self.match("EOF")
        return ProgramNode(requires, globals_and_funcs)

    def parse_param_decl(self):
        self.pos += 1
        type_name = self.peek().value
        self.pos += 1
        param_name = self.match("NID").value
        self.match("EQ")
        val_expr = self.parse_expr()
        self.match("SEMICOLON")
        return ParamDeclNode(type_name, param_name, val_expr)

    def parse_pfundef(self):
        annotation = None
        call_conv = None

        if self.peek().type == "SHARPLBRACKET":
            self.match("SHARPLBRACKET")
            annotation = self.peek().value
            self.pos += 1
            self.match("RBRACKET")

        if self.peek().type in ["EXPORT", "INLINE"] or self.peek().value in ["export", "inline"]:
            call_conv = self.peek().value
            self.pos += 1

        self.match("FN")
        func_name = self.match("NID").value

        self.match("LPAREN")
        args = self.parse_param_list()
        self.match("RPAREN")

        ret_types = []
        if self.peek().type == "RARROW" or self.peek().value == "->":
            self.pos += 1
            if self.peek().type == "LPAREN":
                self.match("LPAREN")
                ret_types.append(self.parse_single_type())
                while self.peek().type == "COMMA":
                    self.match("COMMA")
                    ret_types.append(self.parse_single_type())
                self.match("RPAREN")
            else:
                ret_types.append(self.parse_single_type())
                while self.peek().type == "COMMA":
                    self.match("COMMA")
                    ret_types.append(self.parse_single_type())

        body = self.parse_pfunbody()
        return FunctionNode(annotation, call_conv, func_name, args, ret_types, body)

    def parse_param_list(self):
        args = []
        while self.peek().type in ["REG", "STACK", "INLINE", "GLOBAL"] or self.peek().value in ["reg", "stack", "inline", "global"]:
            storage = self.peek().value
            self.pos += 1

            type_name = self.parse_full_type()

            while self.peek().type == "NID":
                var_name = self.match("NID").value
                args.append({"storage": storage, "type": type_name, "name": var_name})

            if self.peek().type == "COMMA":
                self.match("COMMA")
        return args

    def parse_single_type(self):
        if self.peek().type in ["REG", "STACK", "INLINE", "GLOBAL"] or self.peek().value in ["reg", "stack", "inline", "global"]:
            self.pos += 1

        return self.parse_full_type()

    def parse_pfunbody(self):
        self.match("LBRACE")
        statements = []
        return_stmt = None

        while self.peek().type != "RBRACE":
            if self.peek().type in ["RETURN", "T_RETURN"] or self.peek().value == "return":
                self.pos += 1
                exprs = []
                if self.peek().type != "SEMICOLON":
                    if self.peek().type == "LPAREN":
                        self.match("LPAREN")
                        exprs.append(self.parse_expr())
                        while self.peek().type == "COMMA":
                            self.match("COMMA")
                            exprs.append(self.parse_expr())
                        self.match("RPAREN")
                    else:
                        exprs.append(self.parse_expr())
                        while self.peek().type == "COMMA":
                            self.match("COMMA")
                            exprs.append(self.parse_expr())
                self.match("SEMICOLON")
                return_stmt = ReturnNode(exprs)
                break
            else:
                statements.append(self.parse_statement())

        self.match("RBRACE")
        return BlockNode(statements, return_stmt)

    def parse_statement(self):
        curr = self.peek(0)

        if curr.type == "PARAM" or curr.value == "param":
            return self.parse_param_decl()

        if curr.type == "IF" or curr.value == "if":
            self.pos += 1
            self.match("LPAREN")
            cond = self.parse_expr()
            self.match("RPAREN")
            then_body = self.parse_pfunbody()
            
            else_body = None
            if self.peek().type == "ELSE" or self.peek().value == "else":
                self.pos += 1
                if self.peek().type == "IF" or self.peek().value == "if":
                    else_body = self.parse_statement()
                else:
                    else_body = self.parse_pfunbody()
            return IfNode(cond, then_body, else_body)

        if curr.type == "WHILE" or curr.value == "while":
            self.pos += 1
            self.match("LPAREN")
            cond = self.parse_expr()
            self.match("RPAREN")
            body = self.parse_pfunbody()
            return WhileNode(cond, body)

        if curr.type == "DO" or curr.value == "do":
            self.pos += 1
            body = self.parse_pfunbody()
            if self.peek().type == "WHILE" or self.peek().value == "while":
                self.pos += 1
            else:
                self.match("WHILE")
            self.match("LPAREN")
            cond = self.parse_expr()
            self.match("RPAREN")
            self.match("SEMICOLON")
            return DoWhileNode(body, cond)

        if curr.type == "BREAK" or curr.value == "break":
            self.pos += 1
            self.match("SEMICOLON")
            return BreakNode()

        if curr.type == "CONTINUE" or curr.value == "continue":
            self.pos += 1
            self.match("SEMICOLON")
            return ContinueNode()

        if curr.type in ["FOR", "T_FOR"] or curr.value == "for":
            self.pos += 1
            var_name = self.match("NID").value
            self.match("EQ")
            start_expr = self.parse_expr()
            
            direction = "to"
            if self.peek().value in ["to", "downto"]:
                direction = self.peek().value
                self.pos += 1
            else:
                self.error("Atteso 'to' o 'downto' nel ciclo for")

            end_expr = self.parse_expr()

            step_expr = None
            if self.peek().value == "step":
                self.pos += 1
                step_expr = self.parse_expr()

            body = self.parse_pfunbody()
            return ForNode(var_name, start_expr, direction, end_expr, step_expr, body)

        is_storage = curr.type in ["REG", "STACK", "INLINE", "GLOBAL"] or curr.value in ["reg", "stack", "inline", "global"]
        if is_storage:
            storage = curr.value
            self.pos += 1
            type_name = self.parse_full_type()

            var_decls = []
            statements = []

            while True:
                var_name = self.match("NID").value
                var_decls.append(var_name)

                if self.peek().type == "EQ":
                    self.match("EQ")
                    right = self.parse_expr()
                    statements.append(AssignNode([VarNode(var_name)], "=", right))

                if self.peek().type == "COMMA":
                    self.match("COMMA")
                else:
                    break

            self.match("SEMICOLON")
            if statements:
                decl_node = VarDeclNode(storage, type_name, var_decls)
                return BlockNode([decl_node] + statements)
            return VarDeclNode(storage, type_name, var_decls)

        annotation = None
        if self.peek().type == "SHARPLBRACKET":
            self.match("SHARPLBRACKET")
            annotation = self.peek().value
            self.pos += 1
            self.match("RBRACKET")

        if (self.peek().type in ["NID", "ASSERT"] or self.peek().value in ["assert"]) and self.peek(1).type == "LPAREN":
            func_name = self.peek().value
            self.pos += 1
            self.match("LPAREN")
            args = []
            if self.peek().type != "RPAREN":
                args.append(self.parse_expr())
                while self.peek().type == "COMMA":
                    self.match("COMMA")
                    args.append(self.parse_expr())
            self.match("RPAREN")
            self.match("SEMICOLON")
            return CallNode(func_name, args, annotation=annotation)

        targets = [self.parse_lhs_target()]

        while self.peek().type == "COMMA":
            self.match("COMMA")
            targets.append(self.parse_lhs_target())

        assign_ops = ["=", "^=", "+=", "-=", "<<=", ">>=", "&=", "|=", "*=", "/=", "%=", "<<r=", ">>r="]

        curr_tok = self.peek()
        curr_val = curr_tok.value
        next_val = self.peek(1).value

        if curr_val in ["<<r", ">>r"] and next_val == "=":
            op = curr_val + "="
            self.pos += 2
        elif curr_val in ["+", "-", "*", "/", "%", "^", "&", "|", "<<", ">>"] and next_val == "=":
            op = curr_val + "="
            self.pos += 2
        elif curr_val in assign_ops or curr_tok.type in ["EQ", "XOREQ", "PLUSEQ", "MINUSEQ"]:
            op = curr_val
            self.pos += 1
        else:
            self.error(f"Operatore di assegnamento non valido dopo LHS: '{curr_val}'")

        right = self.parse_expr()
        self.match("SEMICOLON")
        return AssignNode(targets, op, right, annotation=annotation)

    def parse_lhs_target(self):
        if self.peek().type == "QUESTIONMARK" or self.peek().value == "?":
            self.pos += 1
            if self.peek().type == "LBRACE":
                self.match("LBRACE")
                self.match("RBRACE")
            return FlagNode("?")

        if self.peek().type == "LPAREN":
            saved_pos = self.pos
            self.match("LPAREN")

            cast_type_str = ""
            while self.peek().type not in ["RPAREN", "EOF"]:
                cast_type_str += str(self.peek().value)
                self.pos += 1

            if self.peek().type == "RPAREN":
                self.match("RPAREN")
                if self.peek().type in ["LBRACKET", "NID", "LPAREN"]:
                    sub_target = self.parse_lhs_target()
                    return TypeCastNode(cast_type_str, sub_target)

            self.pos = saved_pos

        if self.peek().type == "LBRACKET":
            self.match("LBRACKET")
            type_name = None
            if self.peek().type == "COLON" or self.peek().value == ":":
                self.pos += 1
                type_name = self.peek().value
                self.pos += 1

            addr_expr = self.parse_expr()
            self.match("RBRACKET")
            return MemAccessNode(addr_expr, type_name)

        token_val = self.peek().value
        if token_val in self.CPU_FLAGS:
            self.pos += 1
            return FlagNode(token_val)

        var_name = self.match("NID").value
        target = VarNode(var_name)

        while self.peek().type == "LBRACKET":
            self.match("LBRACKET")
            
            type_name = None
            if self.peek().type == "COLON" or self.peek().value == ":":
                self.pos += 1
                type_name = self.peek().value
                self.pos += 1

            start_expr = self.parse_expr()

            if self.peek().value == ".." or self.peek().type == "DOTDOT":
                self.pos += 1
                end_expr = self.parse_expr()
                self.match("RBRACKET")
                target = SliceAccessNode(target, "range", start_expr, end_expr)
            elif self.peek().value in ["+:", "+"] and self.peek(1).type == "COLON":
                self.pos += 2
                len_expr = self.parse_expr()
                self.match("RBRACKET")
                target = SliceAccessNode(target, "plus_width", start_expr, len_expr)
            elif self.peek().value in ["-:", "-"] and self.peek(1).type == "COLON":
                self.pos += 2
                len_expr = self.parse_expr()
                self.match("RBRACKET")
                target = SliceAccessNode(target, "minus_width", start_expr, len_expr)
            else:
                self.match("RBRACKET")
                if type_name:
                    target = MemAccessNode(start_expr, type_name, base_var=var_name)
                else:
                    if isinstance(target, ArrayAccessNode):
                        target.indices.append(start_expr)
                    else:
                        target = ArrayAccessNode(target, [start_expr])

        return target

    # -----------------------------------------------------------------
    # ESPRESSIONI
    # -----------------------------------------------------------------
    def parse_expr(self):
        cond = self.parse_logic_or()
        if self.peek().type == "QUESTIONMARK" or self.peek().value == "?":
            self.pos += 1
            then_expr = self.parse_expr()
            self.match("COLON")
            else_expr = self.parse_expr()
            return TernaryNode(cond, then_expr, else_expr)
        return cond

    def parse_logic_or(self):
        left = self.parse_logic_and()
        while self.peek().value == "||" or self.peek().type == "OROR":
            op = self.peek().value
            self.pos += 1
            right = self.parse_logic_and()
            left = BinOpNode(left, op, right)
        return left

    def parse_logic_and(self):
        left = self.parse_bitwise_or()
        while self.peek().value == "&&" or self.peek().type == "ANDAND":
            op = self.peek().value
            self.pos += 1
            right = self.parse_bitwise_or()
            left = BinOpNode(left, op, right)
        return left

    def parse_bitwise_or(self):
        left = self.parse_bitwise_xor()
        while self.peek().type == "PIPE" or self.peek().value == "|":
            op = self.peek().value
            self.pos += 1
            right = self.parse_bitwise_xor()
            left = BinOpNode(left, op, right)
        return left

    def parse_bitwise_xor(self):
        left = self.parse_bitwise_and()
        while self.peek().type == "HAT" or self.peek().value == "^":
            op = self.peek().value
            self.pos += 1
            right = self.parse_bitwise_and()
            left = BinOpNode(left, op, right)
        return left

    def parse_bitwise_and(self):
        left = self.parse_equality()
        while self.peek().type == "AMP" or self.peek().value == "&":
            op = self.peek().value
            self.pos += 1
            right = self.parse_equality()
            left = BinOpNode(left, op, right)
        return left

    def parse_equality(self):
        left = self.parse_relational()
        while self.peek().value in ["==", "!="] or self.peek().type in ["EQEQ", "NEQ"]:
            op = self.peek().value
            self.pos += 1
            right = self.parse_relational()
            left = BinOpNode(left, op, right)
        return left

    def parse_relational(self):
        left = self.parse_shift()
        while self.peek().value in ["<", "<=", ">", ">="] or self.peek().type in ["LT", "LE", "GT", "GE"]:
            op = self.peek().value
            self.pos += 1
            right = self.parse_shift()
            left = BinOpNode(left, op, right)
        return left

    def parse_shift(self):
        left = self.parse_additive()
        while self.peek().value in ["<<", ">>", "<<r", ">>r"] or self.peek().type in ["LTLT", "GTGT"]:
            op = self.peek().value
            self.pos += 1
            right = self.parse_additive()
            left = BinOpNode(left, op, right)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.peek().type in ["PLUS", "MINUS"] or self.peek().value in ["+", "-"]:
            op = self.peek().value
            self.pos += 1
            right = self.parse_multiplicative()
            left = BinOpNode(left, op, right)
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self.peek().type in ["STAR", "SLASH", "PERCENT"] or self.peek().value in ["*", "/", "%"]:
            op = self.peek().value
            self.pos += 1
            right = self.parse_unary()
            left = BinOpNode(left, op, right)
        return left

    def parse_unary(self):
        if self.peek().value in ["!", "~", "-", "+"] or self.peek().type in ["NOT", "TILDE", "MINUS", "PLUS"]:
            op = self.peek().value
            self.pos += 1
            operand = self.parse_unary()
            return UnaryOpNode(op, operand)
        return self.parse_primary()

    def parse_primary(self):
        token = self.peek()

        if token.value in self.CPU_FLAGS:
            self.pos += 1
            return FlagNode(token.value)

        if token.type == "HASH" or token.value == "#":
            self.pos += 1
            name = "#" + self.peek().value
            self.pos += 1
            self.match("LPAREN")
            args = []
            if self.peek().type != "RPAREN":
                args.append(self.parse_expr())
                while self.peek().type == "COMMA":
                    self.match("COMMA")
                    args.append(self.parse_expr())
            self.match("RPAREN")
            return CallNode(name, args)

        if token.type == "LBRACE":
            self.match("LBRACE")
            elems = []
            if self.peek().type != "RBRACE":
                elems.append(self.parse_expr())
                while self.peek().type == "COMMA":
                    self.match("COMMA")
                    elems.append(self.parse_expr())
            self.match("RBRACE")
            return VectorInitNode(elems)

        # FIX: Supporto agli array/vettori con [elem1, elem2, ...]
        if token.type == "LBRACKET":
            self.match("LBRACKET")
            type_name = None
            if self.peek().type == "COLON" or self.peek().value == ":":
                self.pos += 1
                type_name = self.peek().value
                self.pos += 1
            
            first_expr = self.parse_expr()

            if self.peek().type == "COMMA":
                elems = [first_expr]
                while self.peek().type == "COMMA":
                    self.match("COMMA")
                    if self.peek().type == "RBRACKET":
                        break  # Gestisce virgole finali facoltative
                    elems.append(self.parse_expr())
                self.match("RBRACKET")
                return ArrayInitNode(elems)
            else:
                self.match("RBRACKET")
                return MemAccessNode(first_expr, type_name)

        if token.type == "LPAREN":
            saved_pos = self.pos
            self.match("LPAREN")

            cast_type_str = ""
            while self.peek().type not in ["RPAREN", "EOF"]:
                cast_type_str += str(self.peek().value)
                self.pos += 1

            if self.peek().type == "RPAREN":
                self.match("RPAREN")
                if self.peek().type in ["LBRACKET", "LBRACE", "NID", "INT", "HEX"]:
                    expr = self.parse_primary()
                    return TypeCastNode(cast_type_str, expr)

            self.pos = saved_pos
            self.match("LPAREN")
            expr = self.parse_expr()
            self.match("RPAREN")
            return expr

        if token.value in ["pack", "unpack", "simd_pack", "simd_unpack"]:
            op_type = token.value
            self.pos += 1
            self.match("LPAREN")
            args = []
            if self.peek().type != "RPAREN":
                args.append(self.parse_expr())
                while self.peek().type == "COMMA":
                    self.match("COMMA")
                    args.append(self.parse_expr())
            self.match("RPAREN")
            return VectorPackNode(op_type, args)

        if token.type in ["NID", "IDENTIFIER"] or token.type == "ASSERT" or token.value in ["assert"]:
            name = token.value
            self.pos += 1

            if self.peek().type == "LPAREN":
                self.match("LPAREN")
                args = []
                if self.peek().type != "RPAREN":
                    args.append(self.parse_expr())
                    while self.peek().type == "COMMA":
                        self.match("COMMA")
                        args.append(self.parse_expr())
                self.match("RPAREN")
                return CallNode(name, args)

            target = VarNode(name)
            while self.peek().type == "LBRACKET":
                self.match("LBRACKET")
                type_name = None
                if self.peek().type == "COLON" or self.peek().value == ":":
                    self.pos += 1
                    type_name = self.peek().value
                    self.pos += 1

                start_expr = self.parse_expr()

                if self.peek().value == ".." or self.peek().type == "DOTDOT":
                    self.pos += 1
                    end_expr = self.parse_expr()
                    self.match("RBRACKET")
                    target = SliceAccessNode(target, "range", start_expr, end_expr)
                elif self.peek().value in ["+:", "+"] and self.peek(1).type == "COLON":
                    self.pos += 2
                    len_expr = self.parse_expr()
                    self.match("RBRACKET")
                    target = SliceAccessNode(target, "plus_width", start_expr, len_expr)
                elif self.peek().value in ["-:", "-"] and self.peek(1).type == "COLON":
                    self.pos += 2
                    len_expr = self.parse_expr()
                    self.match("RBRACKET")
                    target = SliceAccessNode(target, "minus_width", start_expr, len_expr)
                else:
                    self.match("RBRACKET")
                    if type_name:
                        target = MemAccessNode(start_expr, type_name, base_var=name)
                    else:
                        if isinstance(target, ArrayAccessNode):
                            target.indices.append(start_expr)
                        else:
                            target = ArrayAccessNode(target, [start_expr])
            return target

        if token.type in ["INT", "FLOAT", "HEX", "BOOL", "STRING"]:
            self.pos += 1
            return LiteralNode(token.value, token.type)

        self.error(f"Espressione primario non valida: '{token.value}'")












# =====================================================================
# 3. TEST 
# =====================================================================
if __name__ == "__main__":
    test_jasmin_code1 = """
fn f() -> (reg u32, reg u32) {
  reg u32 b, c;
  b = 5;
  c = b;
  c += 1;
  return (b,c);
}

inline fn ft() -> reg u32[2] {
  reg u32[2] t;

  t[0] = 1;
  t[1] = 15;
  
  return t;
}

inline fn mem() -> reg u64 {
  reg u64 r;
  reg u64 p;

  p = 0x1000;

  [ p + 0] = 255;
  r = [ p + 0];

  return r;
}

inline fn mem1() -> reg u32 {
  reg u32 r;
  reg u64 p;

  p = 0x1000;

  [ p + 8 ] = 255;
  r = [ p + 8];

  return r;
}

inline fn test_assert(reg bool x) {
  assert("label", x);
}
"""

    test_jasmin_code2 = """
require "../pending/x86-64/cmoveptr.jazz"

inline
fn zero() -> reg u8 {
  reg u8 r;
  #[inline] r = test(42);
  return r;
}

inline
fn one() -> reg u8 {
  reg u8 r;
  #[inline] r = test(-42);
  return r;
}
"""

    test_jasmin_code3 = """
require "../success/x86-64/eval_for.jazz"

inline
fn test_param() -> inline int {
  inline int i;
  i = n;
  return i;
}
"""

    test_jasmin_code4 = """
require "../success/x86-64/inline_call_to_export.jazz"

/* Inline call to an export function from an inline function. */
inline
fn test() -> reg u64 {
  reg u64 a;
  #[inline] a = sum(42, 24);
  return a;
}
"""

    test_jasmin_code5 = """
require "../success/x86-64/eval_poly1305_u32.jazz"

u256 key = 0x1bf54941aff6bf4afdb20dfb8a800301a806d542fe52447f336d555778bed685;

inline
fn test_poly1305() -> reg u8[16] {
reg u64 in, out, inlen, k, tmp;
reg u8[16] result;
inline int i;

out = 0x1200;
k = 0x1100;
in = 0x1000;

[:u256 k + 0] = key;

[:u8 in + 0] = 0x43;
[:u8 in + 1] = 0x72;
[:u8 in + 2] = 0x79;
[:u8 in + 3] = 0x70;
[:u8 in + 4] = 0x74;
[:u8 in + 5] = 0x6f;
[:u8 in + 6] = 0x67;
[:u8 in + 7] = 0x72;
[:u8 in + 8] = 0x61;
[:u8 in + 9] = 0x70;
[:u8 in + 10] = 0x68;
[:u8 in + 11] = 0x69;
[:u8 in + 12] = 0x63;
[:u8 in + 13] = 0x20;
[:u8 in + 14] = 0x46;
[:u8 in + 15] = 0x6f;
[:u8 in + 16] = 0x72;
[:u8 in + 17] = 0x75;
[:u8 in + 18] = 0x6d;
[:u8 in + 19] = 0x20;
[:u8 in + 20] = 0x52;
[:u8 in + 21] = 0x65;
[:u8 in + 22] = 0x73;
[:u8 in + 23] = 0x65;
[:u8 in + 24] = 0x61;
[:u8 in + 25] = 0x72;
[:u8 in + 26] = 0x63;
[:u8 in + 27] = 0x68;
[:u8 in + 28] = 0x20;
[:u8 in + 29] = 0x47;
[:u8 in + 30] = 0x72;
[:u8 in + 31] = 0x6f;
[:u8 in + 32] = 0x75;
[:u8 in + 33] = 0x70;

inlen = 34;

#[inline] tmp = poly1305(out, in, inlen, k);

for i = 0 to 16 {
  result[i] = [:u8 out + i];
}

return result;
}
"""

    test_jasmin_code6 = """
inline
fn f() -> reg u64 {
  reg u64 x;
  return x;
}
"""

    
    test_jasmin_code7 = """
fn vpsllv_4u32(reg u128 x y) -> reg u128 {
  reg u128 z;
  z = #VPSLLV_4u32(x, y);
  return z;
}

fn vpsllv_8u32(reg u256 x y) -> reg u256 {
  reg u256 z;
  z = #VPSLLV_8u32(x, y);
  return z;
}

fn vpsllv_4u64(reg u256 x y) -> reg u256 {
  reg u256 z;
  z = #VPSLLV_4u64(x, y);
  return z;
}

fn shrd_16(reg u16 x y, reg u8 c) -> reg u16 {
  ?{}, x = #SHRD_16(x, y, c);
  return x;
}

fn divu64() -> reg u64, reg u64 {
  reg u64 x = 1 << 63, y = -1, z = x / y, r = x % y;
  return z, r;
}

u16[1] g = { 0xabcd };
fn global_u16() -> reg u8, reg u8 {
  reg u8 lo = g[:u8 0], hi = g[:u8 1];
  return hi, lo;
}

fn wide_shift(reg u128 x) -> reg u128 {
  reg u128 y = x, z = y;
  x = #VPSLL_2u64(x, x);
  y = #VPSRL_2u64(y, y);
  z = #VPSRA_4u32(z, z);
  x ^= y;
  x += z;
  return x;
}
"""

    test_jasmin_code8 = """
require "../success/x86-64/vpsxldq.jazz"

inline
fn etest() -> reg u256[2] {
global u128 g;
reg u64 p;
reg u256[2] r;
p = 0x480;

g = 0x12345678901234567890123456789012;
[:u128 p + 0] = g;

#[inline] test(p);

r[0] = [:u256 p + 0];
r[1] = [:u256 p + 32];

return r;
}
"""

    test_jasmin_code = """
inline
fn main() -> reg u128[4] {
  reg u256 p = (32u8)[
    0x03, 0x24, 0x3f, 0x6a, 0x88, 0x85, 0xa3, 0x08,
    0xd3, 0x13, 0x19, 0x8a, 0x2e, 0x03, 0x70, 0x73,
    0x44, 0xa4, 0x09, 0x38, 0x22, 0x29, 0x9f, 0x31,
    0xd0, 0x08, 0x2e, 0xfa, 0x98, 0xec, 0x4e, 0x6c ];
  reg u128[4] t;
  p <<r= 4;
  t[0] = p;
  p >>r= 132;
  t[1] = p;
  t[2] = t[1] <<r 7;
  t[3] = t[2] >>r 31;
  return t;
}
"""




    lexer = Lexer(test_jasmin_code)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    ast_root = parser.parse_module()
    print("Parsing completato con successo!\n")
    ast_root.print_tree()