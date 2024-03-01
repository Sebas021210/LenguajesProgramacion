import graphviz
import re

def convert_optional(regex):
    return regex.replace('?', '|E')


def expandir_rango(rango):
    inicio, fin = rango
    return '|'.join([f'({chr(i)})' for i in range(ord(inicio), ord(fin) + 1)])


def expandir_extensiones(expresion):
    patron_extension = re.compile(r'\[([^\]]+)\]')
    coincidencias = patron_extension.findall(expresion)

    for coincidencia in coincidencias:
        rango = coincidencia.split('-')
        if len(rango) == 2 and len(rango[0]) == 1 and len(rango[1]) == 1:
            expresion = expresion.replace(f'[{coincidencia}]', f'({expandir_rango(rango)})')
    
    return expresion


def convertir_expresion(expresion):
    lista = list(expresion)
    alfabeto = []
    operandos = ['+','.','*','|','(',')','[',']','{','}','?']

    for i in lista:
        if i not in operandos:
            if i not in alfabeto:
                alfabeto.append(i)

    alfabeto.append('')
    
    for i in range(len(lista)):
        if i > 0:
            before = lista[i - 1]
            if lista[i] == '+':
                if before not in ')]}':
                    lista[i - 1] = lista[i - 1] + lista[i - 1] + '*'
                else:
                    almacen = []
                    aperturas = 0
                    for j in range(i - 1, -1, -1):
                        if lista[j] in ')]}':
                            aperturas += 1
                            almacen.append(lista[j])
                        elif lista[j] in '([{':
                            aperturas -= 1
                            almacen.append(lista[j])
                        else:
                            almacen.append(lista[j])
                        if aperturas == 0:
                            break
                    almacen.reverse()
                    lista[i] = ''.join(almacen) + '*'
    while '+' in lista:
        lista.remove('+')
    return ''.join(lista), alfabeto


def concatenacion(exp: str) -> str:
    nueva_exp = ''
    for i in range(len(exp) - 1):
        if exp[i] not in ['(', '|', '.'] and exp[i + 1] not in [')', '|', '*', '.']:
            nueva_exp += exp[i] + '.'
        else:
            nueva_exp += exp[i] 

    nueva_exp += exp[-1] 

    return nueva_exp


def infix_postfix(infix):
    caracteres_especiales = {'*': 60, '.': 40, '|': 20}
    exp_postfix, stack = "", ""  

    for c in infix:        
        if c == '(':
            stack = stack + c 
        elif c == ')':
            while stack[-1] != '(':  
                exp_postfix = exp_postfix + stack[-1]  
                stack = stack[:-1]  
            stack = stack[:-1]  
        elif c in caracteres_especiales:
            while stack and caracteres_especiales.get(c, 0) <= caracteres_especiales.get(stack[-1], 0):
                exp_postfix, stack = exp_postfix + stack[-1], stack[:-1]
            stack = stack + c
        else:
            exp_postfix = exp_postfix + c

    while stack:
        exp_postfix, stack = exp_postfix + stack[-1], stack[:-1]

    return exp_postfix


class estado:
    def __init__(self):
        self.label = None
        self.transicion1 = None
        self.transicion2 = None
        self.etiqueta = None
        self.anulable = None
        self.primera_pos = None
        self.ultima_pos = None
        self.siguiente_pos = set()

nodo_etiqueta = 1
nodos = {}

def aumentar_expresion(expresion):
    return f"{expresion}#."


def construir_AS(exp_aumentada):
    global nodo_etiqueta 
    global nodos
    stack = []
    i = 0
    while i < len(exp_aumentada):
        char = exp_aumentada[i]
        if char == 'E':
            nodo = estado()
            nodo.label = char
            nodo.anulable = True
            nodo.primera_pos = set()
            nodo.ultima_pos = set()
            stack.append(nodo)
        elif char.isalpha() or char == '#' or char.isalnum() and char != 'E':
            nodo = estado()
            nodo.label = char
            nodo.etiqueta = nodo_etiqueta  
            nodo.anulable = False
            nodo.primera_pos = {nodo_etiqueta}
            nodo.ultima_pos = {nodo_etiqueta}
            nodos[nodo_etiqueta] = nodo
            nodo_etiqueta += 1 
            stack.append(nodo)
        elif char in "|.*":
            nodo = estado()
            nodo.label = char
            if char == '*':
                c1 = stack.pop()
                nodo.transicion1 = c1
                nodo.anulable = True 
                nodo.primera_pos = c1.primera_pos
                nodo.ultima_pos = c1.ultima_pos
                for pos in c1.ultima_pos:
                    nodos[pos].siguiente_pos.update(c1.primera_pos)
            else:
                c2 = stack.pop()
                c1 = stack.pop()
                if char == '|':
                    nodo.anulable = c1.anulable or c2.anulable
                    nodo.primera_pos = c1.primera_pos.union(c2.primera_pos)
                    nodo.ultima_pos = c1.ultima_pos.union(c2.ultima_pos)
                else: 
                    nodo.anulable = c1.anulable and c2.anulable 
                    if c1.anulable:
                        nodo.primera_pos = c1.primera_pos.union(c2.primera_pos)
                    else:
                        nodo.primera_pos = c1.primera_pos
                    if c2.anulable:
                        nodo.ultima_pos = c1.ultima_pos.union(c2.ultima_pos)
                    else:
                        nodo.ultima_pos = c2.ultima_pos
                    for pos in c1.ultima_pos:
                        nodos[pos].siguiente_pos.update(c2.primera_pos)
                nodo.transicion2 = c2
                nodo.transicion1 = c1
            stack.append(nodo)
        i += 1

    return stack.pop()


def construir_transiciones(arbol, expresion):
    transiciones = set(expresion) - set(['|', '*', '(', ')', '#', 'ε'])
    estados = {frozenset(arbol.primera_pos): 's0'}
    transiciones_estados = {'s0': {}}
    pendientes = [arbol.primera_pos]
    while pendientes:
        actual = pendientes.pop()
        estado_actual = estados[frozenset(actual)]
        for transicion in transiciones:
            nuevo = set()
            for pos in actual:
                nodo = nodos[pos]
                if nodo.label == transicion:
                    nuevo.update(nodo.siguiente_pos)
            if nuevo:
                estado_nuevo = estados.get(frozenset(nuevo))
                if estado_nuevo is None:
                    estado_nuevo = f's{len(estados)}'
                    estados[frozenset(nuevo)] = estado_nuevo
                    pendientes.append(nuevo)
                if estado_actual not in transiciones_estados:
                    transiciones_estados[estado_actual] = {}
                transiciones_estados[estado_actual][transicion] = estado_nuevo
    return estados, transiciones_estados


def graficar_AS(arbol):
    dot = graphviz.Digraph(format='png')

    def agregar_nodos(nodo, parent_id=None):
        nonlocal dot
        if nodo is None:
            return

        current_id = str(id(nodo))
        
        if nodo.etiqueta is not None:
            label = f"{nodo.label} ({nodo.etiqueta}) \nAnulable: {nodo.anulable} \nPrimeraPos: {nodo.primera_pos} \nUltimaPos: {nodo.ultima_pos} \nSiguientePos: {nodo.siguiente_pos}" if nodo.label else 'ε'
        else:
            label = f"{nodo.label} \nAnulable: {nodo.anulable} \nPrimeraPos: {nodo.primera_pos} \nUltimaPos: {nodo.ultima_pos} \nSiguientePos: {nodo.siguiente_pos}" if nodo.label else 'ε'
        
        dot.node(current_id, label=label)

        if parent_id is not None:
            dot.edge(parent_id, current_id)

        agregar_nodos(nodo.transicion1, current_id)
        agregar_nodos(nodo.transicion2, current_id)

    agregar_nodos(arbol)
    dot.render('arbol_sintactico_graph', view=True)


def graficar_afd_directo(estados, transiciones):
    dot = graphviz.Digraph(format='png')

    estado_aceptacion = max(nodos.keys()) 
    estados_invertidos = {v: k for k, v in estados.items()}
    for estado, transiciones_estado in transiciones.items():
        for transicion, estado_destino in transiciones_estado.items():
            dot.edge(estado, estado_destino, label=transicion)
        if estado_aceptacion in estados_invertidos[estado]:
            dot.node(estado, shape='doublecircle')

    dot.render('afd_graph_directo', view=True)


def simulacion_afd_directo(estados, transiciones, cadena):
    estado_actual = 's0'

    for char in cadena:
        if estado_actual in transiciones and char in transiciones[estado_actual]:
            estado_actual = transiciones[estado_actual][char]
        else:
            return False

    return estado_actual in estados.values()


def leer_expresion_y_cadena(nombre_archivo):
    with open(nombre_archivo, 'r') as archivo:
        lineas = archivo.readlines()
        expresion = lineas[0].strip()
        cadena = lineas[1].strip()
    return expresion, cadena


nombre_archivo = 'expresiones_cadena.txt'
expresion, cadena = leer_expresion_y_cadena(nombre_archivo)

infix = convert_optional(expresion)
print('Expresión regular:', infix)
infix = expandir_extensiones(infix)
infix,alfabeto = convertir_expresion(infix)
exp_explicita = concatenacion(infix)
postfix = infix_postfix(exp_explicita)
print('Expresión regular en notación postfix:', postfix)

exp_aumentada = aumentar_expresion(postfix)
print('Expresión regular aumentada:', exp_aumentada)
arbol_sintactico = construir_AS(exp_aumentada)
graficar_AS(arbol_sintactico)

estados, transiciones = construir_transiciones(arbol_sintactico, exp_aumentada)
estados_str = {str(list(k)): v for k, v in estados.items()}
print('\nEstados:')
for estado, nombre in estados_str.items(): print(f'{nombre}: {estado}')
print('\nTransiciones')
for estado, transiciones_estado in transiciones.items(): print(f'{estado}: {transiciones_estado}')

graficar_afd_directo(estados, transiciones)
print('El resultado de la simulación del AFD directo es:', simulacion_afd_directo(estados_str, transiciones, cadena))
