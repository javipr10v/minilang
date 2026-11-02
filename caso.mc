int a = 10;
string nombre = "UNACH";
{
  int b = a + 2;
  b = nombre;      // error: asigna string a int
}
c = a + b;         // errores: c no declarada; b fuera de ambito
int a = 3;         // error: redeclaracion de a
