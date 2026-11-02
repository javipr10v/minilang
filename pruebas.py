from minilang import verificar

CASOS = [
    ("V1 declaraciones y expresiones", 'int a = 10;\nstring s = "hola";\nint b = a + 2 * 3;', 0),
    ("V2 sombreado en bloque", 'int x = 1;\n{\n  int x = 2;\n  int y = x + 1;\n}\nx = x - 1;', 0),
    ("V3 concatenacion de strings", 'string a = "uno";\nstring b = a + "dos";\n{\n  string c = b + a;\n  b = c;\n}', 0),
    ("E1 programa caso del PDF", 'int a = 10;\nstring nombre = "UNACH";\n{\n  int b = a + 2;\n  b = nombre;\n}\nc = a + b;\nint a = 3;', 4),
    ("E2 declaracion con tipo incorrecto", 'int x = "hola";', 1),
    ("E3 redeclaracion", 'int a = 1;\nint a = 2;', 1),
    ("E4 operador invalido string - int", 'string s = "a";\nint n = s - 1;', 1),
    ("E5 variable fuera de ambito", '{\n  int t = 1;\n}\nt = 2;', 1),
]

ok = 0
print(f"{'CASO':<38}{'ESPERADO':<10}{'OBTENIDO':<10}RESULTADO")
for nombre, codigo, esperado in CASOS:
    errores, _ = verificar(codigo)
    paso = len(errores) == esperado
    ok += paso
    print(f"{nombre:<38}{esperado:<10}{len(errores):<10}{'OK' if paso else 'FALLO'}")
print(f"\n{ok}/{len(CASOS)} casos correctos")
