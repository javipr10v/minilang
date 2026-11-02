# MiniLang - Verificador semantico minimo

Actividad integradora de Compiladores, UNACH. Lenguaje: Python 3.

## Que hace
Verifica programas MiniLang: tabla de simbolos con pila de ambitos, verificacion de tipos (int, string) y reporte de errores con linea.

## Como ejecutarlo
Requiere Python 3 instalado.

    python minilang.py caso.mc     (analiza un archivo)
    python minilang.py             (modo interactivo, linea vacia para terminar)
    python pruebas.py              (corre los 8 casos de prueba)

## Errores que detecta
E1 variable no declarada, E2 fuera de ambito, E3 redeclaracion, E4 tipos incompatibles, E5 operador invalido, E6 error de sintaxis (con modo panico), E7 simbolo invalido.

## Evidencia
- salida_pruebas.txt: resultado de los 8 casos (3 validos y 5 con error)
- salida_caso.txt: salida del programa caso del PDF

## Declaracion de uso de IA
Se uso Claude (Anthropic) como apoyo para estructurar el codigo y redactar borradores. El equipo reviso, probo y comprendio el resultado.
