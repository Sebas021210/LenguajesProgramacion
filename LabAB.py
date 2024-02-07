import graphviz

def convert_optional(regex):
    return regex.replace('?', '|E')


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
    if '+' in lista:
        lista.remove('+')
    return ''.join(lista), alfabeto


def convertir_explicito(exp: str) -> str:
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
    label = None
    transicion1 = None 
    transicion2 = None 
    id = None


class afn:
    inicial, accept = None, None

    def __init__(self, inicial, accept):
        self.inicial, self.accept = inicial, accept

    def get_all_transitions(self):
        transitions = []
        estados = 0 
        transiciones = []

        def visit(estado):
            nonlocal transitions
            nonlocal estados 
            nonlocal transiciones
            estados += 1
            if estado.transicion1 is not None:
                transition = (estado, estado.label, estado.transicion1)
                transiciones.append((estados,estado.label, estado.transicion1))
                if transition not in transitions:
                    transitions.append(transition)
                    visit(estado.transicion1)
            if estado.transicion2 is not None:
                transition = (estado, estado.label, estado.transicion2)
                transiciones.append((estados,estado.label, estado.transicion2))
                if transition not in transitions:
                    transitions.append(transition)
                    visit(estado.transicion2)
        visit(self.inicial)
        self.transitions = transitions
        self.transiciones = transiciones
        return transiciones
   

def postfix_afn(exp_postfix):
    afnstack = []
    epsilon = 'E'

    for c in exp_postfix:
        if c == '*':
            afn1 = afnstack.pop()
            inicial, accept = estado(), estado()
            inicial.transicion1, inicial.transicion2 = afn1.inicial, accept
            afn1.accept.transicion1, afn1.accept.transicion2 = afn1.inicial, accept
            afnstack.append(afn(inicial, accept))
        elif c == '.':
            afn2, afn1 = afnstack.pop(), afnstack.pop()
            afn1.accept.transicion1 = afn2.inicial
            afnstack.append(afn(afn1.inicial, afn2.accept))
        elif c == '|':
            afn2, afn1 = afnstack.pop(), afnstack.pop()
            inicial = estado()
            inicial.transicion1, inicial.transicion2 = afn1.inicial, afn2.inicial
            accept = estado()
            afn1.accept.transicion1, afn2.accept.transicion1 = accept, accept
            afnstack.append(afn(inicial, accept))
        elif c == 'E':
            accept, inicial = estado(), estado()
            inicial.transicion1 = accept
            afnstack.append(afn(inicial, accept))
        else:
            accept, inicial = estado(), estado()
            inicial.label, inicial.transicion1 = c, accept
            afnstack.append(afn(inicial, accept))

    return afnstack.pop()


def graficar_afn(afn):
    dot = graphviz.Digraph(format='png')
    estados = 0  

    def add_estados_edges(node, visited):
        nonlocal estados
        if node in visited:
            return
        visited.add(node)
        estados += 1

        dot.node(str(id(node)), label=f'q{estados}')

        if node.transicion1:
            label = node.transicion1.label if node.transicion1.label else 'ε'
            dot.edge(str(id(node)), str(id(node.transicion1)), label=label)
            add_estados_edges(node.transicion1, visited)
        if node.transicion2:
            label = node.transicion2.label if node.transicion2.label else 'ε'
            dot.edge(str(id(node)), str(id(node.transicion2)), label=label)
            add_estados_edges(node.transicion2, visited)

    add_estados_edges(afn.inicial, set())

    dot.render('afn_graph', view=True)


def seguimiento(estado):
    estados = set()
    estados.add(estado)

    if estado.label is None:
        if estado.transicion1 is not None:
            estados |= seguimiento(estado.transicion1)
        if estado.transicion2 is not None:
            estados |= seguimiento(estado.transicion2)
    return estados


class AFD:
    def __init__(self):
        self.estados = set()
        self.transitions = {}
        self.inicial = None
        self.accept = set()


def afn_to_afd(afn, alphabet):
    afd = AFD()
    estado_inicial = frozenset(seguimiento(afn.inicial))
    afd.inicial = estado_inicial
    afd.estados.add(estado_inicial)
    stack = [estado_inicial]

    while stack:
        actual_estado = stack.pop()
        for char in alphabet:
            next_estados = set()
            for afn_estado in actual_estado:
                if afn_estado.label == char:
                    next_estados |= seguimiento(afn_estado.transicion1)
            next_estado = frozenset(next_estados)
            if next_estado:
                afd.transitions[(actual_estado, char)] = next_estado
                if next_estado not in afd.estados:
                    afd.estados.add(next_estado)
                    stack.append(next_estado)
    
    for estado in afd.estados:
        if afn.accept in estado:
            afd.accept.add(estado)
    
    return afd


def label_estados(estados):
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    estado_labels = {}

    for i, estado in enumerate(estados):
        if i < len(alphabet):
            estado_labels[estado] = alphabet[i]
        else:
            estado_labels[estado] = str(i)

    return estado_labels


def graficar_afd(afd):
    dot = graphviz.Digraph(format='png')
    estado_labels = label_estados(afd.estados)  
  
    for estado in afd.estados:
        label = estado_labels[estado]
        if estado in afd.accept:
            dot.node(label, shape='doublecircle')
        else:
            dot.node(label)

    inicial_label = estado_labels[afd.inicial]
    dot.node('inicial', shape='none')
    dot.edge('inicial', inicial_label)

    for (estado1, char), estado2 in afd.transitions.items():
        dot.edge(estado_labels[estado1], estado_labels[estado2], label=char)

    return dot

def min_afd(afd):
    alfabeto = set([simbolo for _, simbolo in afd.transitions.keys()])
    P = [afd.accept, afd.estados - afd.accept]
    W = [set(y) for y in P]

    while W:
        A = W.pop()
        for c in alfabeto:
            X = set([s for s in afd.estados if afd.transitions.get((s, c)) in A])
            for Y in P:
                if X.intersection(Y) and (Y - X):
                    P.remove(Y)
                    P.extend([Y.intersection(X), Y - X])
                    if Y in W:
                        W.remove(Y)
                        W.extend([Y.intersection(X), Y - X])
                    else:
                        if len(Y.intersection(X)) < len(Y - X):
                            W.append(Y.intersection(X))
                        else:
                            W.append(Y - X)

    estados_minimizados = [list(y) for y in P]
    estado_inicial_minimizado = [s for s in estados_minimizados if afd.inicial in s][0]
    estados_aceptacion_minimizados = [s for s in estados_minimizados if set(s).intersection(afd.accept)]
    transiciones_minimizadas = {}

    for estado in estados_minimizados:
        for c in alfabeto:
            transicion = afd.transitions.get((estado[0], c))
            if transicion:
                for s in estados_minimizados:
                    if transicion in s:
                        transiciones_minimizadas[(str(estado), c)] = str(s)

    afd_minimizado = AFD()
    afd_minimizado.estados = set([str(estado) for estado in estados_minimizados])
    afd_minimizado.transitions = transiciones_minimizadas
    afd_minimizado.inicial = str(estado_inicial_minimizado)
    afd_minimizado.accept = set([str(s) for s in estados_aceptacion_minimizados])

    return afd_minimizado


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
        if char.isalpha() or char == '#':
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
        elif char == 'ε':
            nodo = estado()
            nodo.label = char
            nodo.anulable = True
            nodo.primera_pos = set()
            stack.append(nodo)
        i += 1

    return stack.pop()

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
infix,alfabeto = convertir_expresion(infix)
exp_explicita = convertir_explicito(infix)
postfix = infix_postfix(exp_explicita)
print('Expresión regular en notación postfix:', postfix)

afn = postfix_afn(postfix)
#graficar_afn(afn)
afd = afn_to_afd(afn, alfabeto)
estado_labels = label_estados(afd.estados)
#graficar_afd(afd).render('afd_graph', view=True)
afd_min = min_afd(afd)
#graficar_afd(afd_min).render('afd_minimizado_graph', view=True)

exp_aumentada = aumentar_expresion(postfix)
print('Expresión regular aumentada:', exp_aumentada)
arbol_sintactico = construir_AS(exp_aumentada)
graficar_AS(arbol_sintactico)
