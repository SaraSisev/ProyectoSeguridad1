import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cifrado import SF4, SF5
from analizador import SF20

ALFABETO = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"

FRASES = [
    "LA FAMILIA COME EN LA COCINA TODOS LOS DIAS",
    "EL PERRO CORRE POR EL PARQUE TODAS LAS TARDES",
    "MI ABUELA PREPARA UN DESAYUNO DELICIOSO CADA MAÑANA",
    "LOS ESTUDIANTES ENTREGAN SUS TAREAS ANTES DEL VIERNES",
    "EL CIELO SE PINTA DE COLORES DURANTE EL ATARDECER",
    "NUESTRO EQUIPO GANO EL PARTIDO DE FUTBOL EL DOMINGO",
    "LA TECNOLOGIA HA CAMBIADO LA FORMA EN QUE VIVIMOS",
    "ELLA ESTUDIA MEDICINA EN LA UNIVERSIDAD DESDE HACE TRES AÑOS",
    "EL TREN LLEGA A LA ESTACION CENTRAL A LAS OCHO",
    "LOS NIÑOS JUEGAN EN EL JARDIN DESPUES DE LA ESCUELA",
    "EL CAFE RECIEN HECHO LLENA LA CASA DE UN AROMA AGRADABLE",
    "LA CIUDAD SE ILUMINA CON MILES DE LUCES POR LA NOCHE",
    "MIS AMIGOS Y YO VIAJAMOS AL SUR DURANTE LAS VACACIONES",
    "EL MEDICO RECOMENDO DESCANSAR Y BEBER MUCHA AGUA",
    "LA ORQUESTA TOCO UNA HERMOSA MELODIA EN EL TEATRO",
    "EL AGRICULTOR SEMBRO MAIZ Y FRIJOL EN SU TERRENO",
    "LOS BOMBEROS APAGARON EL INCENDIO EN POCAS HORAS",
    "LA BIBLIOTECA PERMANECE ABIERTA HASTA LAS NUEVE DE LA NOCHE",
    "EL AVION ATERRIZO SIN PROBLEMAS A PESAR DE LA TORMENTA",
    "MI HERMANO MENOR APRENDIO A NADAR ESTE VERANO",
    "LA EMPRESA CONTRATO A DIEZ NUEVOS EMPLEADOS ESTE MES",
    "EL RIO CRECIO DESPUES DE LAS FUERTES LLUVIAS DE AYER",
    "LOS VECINOS ORGANIZARON UNA FIESTA PARA CELEBRAR EL ANIVERSARIO",
    "EL PROFESOR EXPLICO LA LECCION CON MUCHA PACIENCIA",
    "LA PANADERIA VENDE PAN FRESCO DESDE TEMPRANO POR LA MAÑANA",
    "EL ARTISTA PINTO UN MURAL ENORME EN LA PLAZA PRINCIPAL",
    "NUESTROS PADRES CELEBRARON SU ANIVERSARIO EN UN RESTAURANTE",
    "EL CIENTIFICO PUBLICO SUS RESULTADOS EN UNA REVISTA IMPORTANTE",
    "LA LLUVIA NO DETUVO EL PARTIDO DE BALONCESTO AYER",
    "EL CARPINTERO CONSTRUYO UNA MESA DE MADERA MUY RESISTENTE",
    "LOS TURISTAS VISITARON EL MUSEO DURANTE TODA LA MAÑANA",
    "EL GRANJERO ORDEÑA LAS VACAS ANTES DEL AMANECER",
    "LA ENFERMERA CUIDO AL PACIENTE DURANTE TODA LA NOCHE",
    "EL ESCRITOR TERMINO SU NOVELA DESPUES DE DOS AÑOS",
    "LOS ALPINISTAS ALCANZARON LA CIMA DE LA MONTAÑA AL MEDIODIA",
    "LA PANADERA HORNEA GALLETAS DULCES TODOS LOS SABADOS",
    "EL MECANICO REPARO EL MOTOR DEL AUTOMOVIL EN UNA HORA",
    "LOS PESCADORES SALIERON AL MAR ANTES DE QUE SALIERA EL SOL",
    "LA MAESTRA ORGANIZO UNA EXCURSION AL ZOOLOGICO ESTE MES",
    "EL JARDINERO REGO LAS PLANTAS TEMPRANO POR LA MAÑANA",
]

PALABRAS_CORTAS = [
    "HOLA", "NO", "SI", "MEXICO", "CASA", "AMOR", "PERRO", "GATO", "AGUA",
    "SOL", "LUNA", "PAZ", "VIDA", "BIEN", "MAL", "HOY", "AQUI", "ADIOS",
    "GRACIAS", "FAMILIA", "MESA", "LIBRO", "NOCHE", "DIA", "CIELO",
    "TIERRA", "FUEGO", "AIRE", "MAR", "RIO", "FLOR", "ARBOL", "NIÑO",
    "NIÑA", "HOMBRE", "MUJER", "TIEMPO", "AMIGO", "ESCUELA", "TRABAJO",
]

SHIFTS_DE_MUESTRA = [1, 4, 9, 13, 18, 22]


def evaluar_banco(nombre_banco, textos, shifts):
    aciertos = 0
    fallos = 0
    detalle_fallos = []

    for texto in textos:
        for shift in shifts:
            cifrado = SF4(texto, ALFABETO, shift)
            resultado = SF20(cifrado, ALFABETO)
            ok = resultado["metodo"] == "CESAR" and resultado["desplazamiento"] == shift and resultado["texto"] == texto
            if ok:
                aciertos += 1
            else:
                fallos += 1
                detalle_fallos.append((texto, shift, resultado["metodo"], resultado["desplazamiento"], resultado["texto"]))

        cifrado_atbash = SF5(texto, ALFABETO)
        resultado_atbash = SF20(cifrado_atbash, ALFABETO)
        ok = resultado_atbash["metodo"] == "ATBASH" and resultado_atbash["texto"] == texto
        if ok:
            aciertos += 1
        else:
            fallos += 1
            detalle_fallos.append((texto, "ATBASH", resultado_atbash["metodo"], resultado_atbash["desplazamiento"], resultado_atbash["texto"]))

    total = aciertos + fallos
    print(f"\n== {nombre_banco} ==")
    print(f"Total de casos: {total}")
    print(f"Aciertos: {aciertos}")
    print(f"Fallos: {fallos}")
    print(f"Precision: {aciertos / total * 100:.2f}%")
    if detalle_fallos:
        print("Ejemplos de fallos (hasta 15):")
        for texto, clave, metodo_detectado, shift_detectado, resultado_texto in detalle_fallos[:15]:
            print(f"  texto={texto!r} clave_usada={clave!r} -> detecto {metodo_detectado} shift={shift_detectado} resultado={resultado_texto!r}")

    return total, aciertos, fallos


if __name__ == "__main__":
    evaluar_banco("Banco de frases completas (multiples palabras)", FRASES, SHIFTS_DE_MUESTRA)
    evaluar_banco("Banco de palabras sueltas / muy cortas", PALABRAS_CORTAS, SHIFTS_DE_MUESTRA)
