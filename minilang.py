import re
import sys

KW = {"int", "string"}

TOKEN_RE = re.compile(r"""
    (?P<WS>[ \t\r]+)
  | (?P<COMENT>//[^\n]*)
  | (?P<NL>\n)
  | (?P<STR>"[^"\n]*")
  | (?P<NUM>\d+)
  | (?P<ID>[A-Za-z_]\w*)
  | (?P<OP>[+\-*/=(){};])
  | (?P<MAL>.)
""", re.X)


# ---------------- LEXICO ----------------
def tokenizar(texto):
    toks, errs, linea = [], [], 1
    for m in TOKEN_RE.finditer(texto):
        k, v = m.lastgroup, m.group()
        if k == "NL":
            linea += 1
        elif k in ("WS", "COMENT"):
            pass
        elif k == "MAL":
            errs.append(f"Linea {linea}: [E7 simbolo invalido] '{v}'")
        elif k == "ID":
            toks.append(("KW" if v in KW else "ID", v, linea))
        else:
            toks.append((k, v, linea))
    toks.append(("EOF", "", linea))
    return toks, errs


# ---------------- PARSER ----------------
class SynErr(Exception):
    pass


class Parser:
    def __init__(self, toks):
        self.t = toks
        self.i = 0
        self.errores = []

    def peek(self):
        return self.t[self.i]

    def eat(self, val):
        k = self.peek()
        if k[0] == "OP" and k[1] == val:
            self.i += 1
            return k
        enc = "fin de archivo" if k[0] == "EOF" else f"'{k[1]}'"
        ln = self.t[self.i - 1][2] if val == ";" and self.i > 0 else k[2]
        raise SynErr(f"Linea {ln}: [E6 error de sintaxis] se esperaba '{val}' pero se encontro {enc}")

    def programa(self):
        return self.sentencias(False)

    def sentencias(self, en_bloque):
        out = []
        while True:
            k = self.peek()
            if k[0] == "EOF":
                break
            if k[0] == "OP" and k[1] == "}":
                if en_bloque:
                    break
                self.errores.append(f"Linea {k[2]}: [E6 error de sintaxis] '}}' sin '{{' que abrir")
                self.i += 1
                continue
            try:
                out.append(self.sentencia())
            except SynErr as e:
                self.errores.append(str(e))
                self.sync()
        return out

    def sync(self):
        # modo panico: avanzar hasta pasar un ';' o llegar a un '}'
        while self.peek()[0] != "EOF":
            k = self.peek()
            if k[0] == "OP" and k[1] == ";":
                self.i += 1
                return
            if k[0] == "OP" and k[1] == "}":
                return
            self.i += 1

    def sentencia(self):
        k = self.peek()
        if k[0] == "OP" and k[1] == "{":
            self.i += 1
            cuerpo = self.sentencias(True)
            self.eat("}")
            return ("block", cuerpo)
        if k[0] == "KW":
            self.i += 1
            nom = self.peek()
            if nom[0] != "ID":
                raise SynErr(f"Linea {nom[2]}: [E6 error de sintaxis] se esperaba un identificador despues de '{k[1]}'")
            self.i += 1
            self.eat("=")
            e = self.expr()
            self.eat(";")
            return ("decl", k[1], nom[1], e, k[2])
        if k[0] == "ID":
            self.i += 1
            self.eat("=")
            e = self.expr()
            self.eat(";")
            return ("assign", k[1], e, k[2])
        raise SynErr(f"Linea {k[2]}: [E6 error de sintaxis] sentencia invalida, se encontro '{k[1]}'")

    def expr(self):
        izq = self.term()
        while self.peek()[0] == "OP" and self.peek()[1] in ("+", "-"):
            op = self.peek()
            self.i += 1
            izq = ("bin", op[1], izq, self.term(), op[2])
        return izq

    def term(self):
        izq = self.factor()
        while self.peek()[0] == "OP" and self.peek()[1] in ("*", "/"):
            op = self.peek()
            self.i += 1
            izq = ("bin", op[1], izq, self.factor(), op[2])
        return izq

    def factor(self):
        k = self.peek()
        if k[0] == "NUM":
            self.i += 1
            return ("num", k[1], k[2])
        if k[0] == "STR":
            self.i += 1
            return ("str", k[1], k[2])
        if k[0] == "ID":
            self.i += 1
            return ("var", k[1], k[2])
        if k[0] == "OP" and k[1] == "(":
            self.i += 1
            e = self.expr()
            self.eat(")")
            return e
        enc = "fin de archivo" if k[0] == "EOF" else f"'{k[1]}'"
        raise SynErr(f"Linea {k[2]}: [E6 error de sintaxis] se esperaba una expresion pero se encontro {enc}")


# ---------------- TABLA DE SIMBOLOS ----------------
class Tabla:
    def __init__(self):
        self.pila = [{}]          # pila de ambitos; el 0 es el global
        self.cerrados = set()     # nombres de ambitos ya cerrados
        self.historial = []       # (nombre, tipo, nivel, linea) para imprimir

    def entrar(self):
        self.pila.append({})

    def salir(self):
        self.cerrados |= set(self.pila[-1])
        self.pila.pop()

    def insertar(self, nombre, tipo, linea):
        if nombre in self.pila[-1]:
            return False
        self.pila[-1][nombre] = (tipo, linea)
        self.historial.append((nombre, tipo, len(self.pila) - 1, linea))
        return True

    def buscar(self, nombre):
        for amb in reversed(self.pila):
            if nombre in amb:
                return amb[nombre][0]
        return None


# ---------------- VERIFICADOR SEMANTICO ----------------
class Verificador:
    def __init__(self):
        self.tabla = Tabla()
        self.errores = []

    def err(self, linea, msg):
        self.errores.append(f"Linea {linea}: {msg}")

    def no_declarada(self, nombre, linea):
        if nombre in self.tabla.cerrados:
            self.err(linea, f"[E2 fuera de ambito] '{nombre}' solo existe dentro de un bloque ya cerrado")
        else:
            self.err(linea, f"[E1 no declarada] la variable '{nombre}' no esta declarada")

    def tipo_de(self, e):
        k = e[0]
        if k == "num":
            return "int"
        if k == "str":
            return "string"
        if k == "var":
            t = self.tabla.buscar(e[1])
            if t is None:
                self.no_declarada(e[1], e[2])
                return "error"
            return t
        _, op, izq, der, ln = e
        tl, tr = self.tipo_de(izq), self.tipo_de(der)
        if "error" in (tl, tr):
            return "error"
        if tl == tr == "int":
            return "int"
        if tl == tr == "string" and op == "+":
            return "string"
        self.err(ln, f"[E5 operador invalido] '{op}' no se puede aplicar entre {tl} y {tr}")
        return "error"

    def sentencias(self, lista):
        for s in lista:
            if s[0] == "block":
                self.tabla.entrar()
                self.sentencias(s[1])
                self.tabla.salir()
            elif s[0] == "decl":
                _, tipo, nombre, expr, ln = s
                te = self.tipo_de(expr)
                if not self.tabla.insertar(nombre, tipo, ln):
                    self.err(ln, f"[E3 redeclaracion] '{nombre}' ya fue declarada en este ambito")
                if te not in (tipo, "error"):
                    self.err(ln, f"[E4 tipos incompatibles] no se puede asignar {te} a '{nombre}' de tipo {tipo}")
            else:
                _, nombre, expr, ln = s
                t = self.tabla.buscar(nombre)
                if t is None:
                    self.no_declarada(nombre, ln)
                te = self.tipo_de(expr)
                if t is not None and te not in (t, "error"):
                    self.err(ln, f"[E4 tipos incompatibles] no se puede asignar {te} a '{nombre}' de tipo {t}")


def verificar(codigo):
    toks, errs_lex = tokenizar(codigo)
    p = Parser(toks)
    ast = p.programa()
    v = Verificador()
    v.sentencias(ast)
    return errs_lex + p.errores + v.errores, v.tabla.historial


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8-sig") as f:
            codigo = f.read()
    else:
        print("Escribe tu programa MiniLang. Linea vacia para terminar:")
        lineas = []
        while True:
            try:
                l = input()
            except EOFError:
                break
            if l.strip() == "":
                break
            lineas.append(l)
        codigo = "\n".join(lineas)

    errores, tabla = verificar(codigo)
    print("\nTABLA DE SIMBOLOS")
    print(f"{'NOMBRE':<12}{'TIPO':<9}{'AMBITO':<10}LINEA")
    for nom, tipo, nivel, ln in tabla:
        amb = "global" if nivel == 0 else f"bloque {nivel}"
        print(f"{nom:<12}{tipo:<9}{amb:<10}{ln}")
    print(f"\nERRORES ({len(errores)})")
    if not errores:
        print("Sin errores. El programa es semanticamente correcto.")
    for e in errores:
        print(" -", e)


if __name__ == "__main__":
    main()
