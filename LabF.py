import graphviz
import tkinter as tk
from tkinter import filedialog
import os

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("YALex Text Editor")
        self.root.geometry("1000x600")
        
        self.text_widget = tk.Text(root, wrap="word", undo=True, autoseparators=True)
        self.text_widget.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        self.text_widget.config(width=60, height=25)

        self.cadena_text_widget = tk.Text(root, wrap="word", undo=True, autoseparators=True)
        self.cadena_text_widget.grid(row=1, column=0, sticky="nsew", padx=3, pady=3)
        self.cadena_text_widget.config(width=60, height=10)

        self.text_widget1 = tk.Text(root, wrap="word", undo=True, autoseparators=True)
        self.text_widget1.grid(row=0, column=2, sticky="nsew", padx=3, pady=3)
        self.text_widget1.config(width=60, height=25)

        self.resultado_text_widget = tk.Text(root, wrap="word", undo=True, autoseparators=True)
        self.resultado_text_widget.grid(row=1, column=2, sticky="nsew", padx=3, pady=3)
        self.resultado_text_widget.config(width=60, height=10)

        menu_bar = tk.Menu(root)
        root.config(menu=menu_bar)

        menu_bar.add_command(label="Open YALex", command=self.open_YALex)
        menu_bar.add_command(label="Open YAPar", command=self.open_YAPar)
        menu_bar.add_command(label="Run", command=self.run)
        menu_bar.add_command(label="Exit", command=root.destroy)

    def open_YALex(self):
        file_path = filedialog.askopenfilename(title="Open YALex File", filetypes=[("YALex Files", "*.yal")])
        if file_path:
            with open(file_path, 'r') as file:
                content = file.read()
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, content)
    
    def open_YAPar(self):
        file_path = filedialog.askopenfilename(title="Open YAPar File", filetypes=[("YAPar Files", "*.yalp")])
        if file_path:
            with open(file_path, 'r') as file:
                content = file.read()
            self.text_widget1.delete(1.0, tk.END)
            self.text_widget1.insert(tk.END, content)

    def run(self):
        yalex_contenido = self.text_widget.get(1.0, tk.END)
        yapar_contenido = self.text_widget1.get(1.0, tk.END)

        if not self.verificar_tokens():
            return
        
        carpeta_guardado = 'AFD_Graphs'
        for archivo in os.listdir(carpeta_guardado):
            archivo_path = os.path.join(carpeta_guardado, archivo)
            try:
                if os.path.isfile(archivo_path):
                    os.unlink(archivo_path)
            except Exception as e:
                print(f"No se pudo eliminar {archivo_path}. Razón: {e}")

        cadena_input = self.get_cadena_input()
        lista_cadenas = self.convertir_a_lista(cadena_input)

        resultados = AFD_yalex(yalex_contenido, yapar_contenido, lista_cadenas, self.show_error)
        lista_estados, transiciones, estado_aceptacion, primero, siguiente = resultados
        self.mostrar_resultados_primero_y_siguiente(primero, siguiente)

    def mostrar_resultados_primero_y_siguiente(self, primero, siguiente):
        self.resultado_text_widget.delete(1.0, tk.END)

        self.resultado_text_widget.insert(tk.END, "Primeros:\n")
        for no_terminal, primero_set in primero.items():
            self.resultado_text_widget.insert(tk.END, f"primero({no_terminal}): {primero_set}\n")
        
        self.resultado_text_widget.insert(tk.END, "\nSiguientes:\n")
        for no_terminal, siguiente_set in siguiente.items():
            self.resultado_text_widget.insert(tk.END, f"siguiente({no_terminal}): {siguiente_set}\n")

    def get_cadena_input(self):
        cadena_input = self.cadena_text_widget.get(1.0, tk.END)
        return cadena_input

    def convertir_a_lista(self, cadena_input):
        lista_cadenas = cadena_input.split()
        return lista_cadenas
    
    def verificar_tokens(self):
        tokens_yalex = set()
        tokens_yapar = set()
        tokens_no_definidos = []

        en_rule_tokens = False
        for linea in self.text_widget.get("1.0", tk.END).split('\n'):            
            if linea.startswith('rule tokens'):
                en_rule_tokens = True
                continue

            if en_rule_tokens:
                if '|' not in linea:
                    break

                partes = linea.strip().split('|')
                for parte in partes[1:]:
                    if '{' in parte:
                        contenido = parte.split('{')[1].split('}')[0].strip()
                        if "return" in contenido:
                            token = contenido.split("return")[1].strip()
                        elif "print" in contenido:
                            token = contenido.split("Token:")[1].split('\"')[0].strip()
                        else:
                            token = contenido
                        tokens_yalex.add(token)
        print(f"Token YALex: {tokens_yalex}")

        for linea in self.text_widget1.get("1.0", tk.END).split('\n'):
            if linea.strip().startswith("%token"):
                token = linea.strip().split()[1]
                tokens_yapar.add(token)
            if linea.strip().startswith("IGNORE"):
                token = linea.strip().split()[1]
                tokens_yapar.remove(token)
        print(f"Token YAPar: {tokens_yapar}")

        for token in tokens_yapar:
            if token not in tokens_yalex:
                tokens_no_definidos.append(token)

        if tokens_no_definidos:
            tk.messagebox.showwarning("Advertencia", f"Los tokens '{tokens_no_definidos}' definidos en YAPar no está definido en YALex.")
            return False

        return True
    
    def show_error(self, error_message):
        tk.messagebox.showerror("Error", error_message)
    

def convert_optional(regex):
    return regex.replace('?', '|E')

def expandir_rango(rango):
    inicio, fin = rango
    return '|'.join([f'({chr(i)})' for i in range(ord(inicio), ord(fin) + 1)])

def reemplazar_caracteres(expresion):
    expresion = expresion.replace("'\\t'", "'\t'").replace("'\\n'", "'\n'").replace("'\\s'", "'\s'")
    caracteres_reemplazar = {'\t': '替', '\n': '换', '\s': '空'}

    if expresion.find("['+' '-']") != -1:
        expresion = expresion.replace("['+' '-']", "['加' '点']")
    elif expresion.find("['-' '+']") != -1:
        expresion = expresion.replace("['-' '+']", "['点' '加']")
    elif expresion.find("['+']") != -1:
        expresion = expresion.replace("['+']", "['加']")
    elif expresion.find("['-']") != -1:
        expresion = expresion.replace("['-']", "['点']")
    elif expresion.find("(_)") != -1:
        expresion = expresion.replace('(_)', '苦')
    elif expresion.find("(+)") != -1:
        expresion = expresion.replace("(+)", "加")
    elif expresion.find("(-)") != -1:
        expresion = expresion.replace("(-)", "点")
    elif expresion.find("(*)") != -1:
        expresion = expresion.replace("(*)", "阿")
    elif expresion.find("(/)") != -1:
        expresion = expresion.replace("(/)", "贝")
    elif expresion.find("(;)") != -1:
        expresion = expresion.replace("(;)", "色")
    elif expresion.find("(:=)") != -1:
        expresion = expresion.replace("(:=)", "日")
    elif expresion.find("(<)") != -1:
        expresion = expresion.replace("(<)", "伊")
    elif expresion.find("(>)") != -1:
        expresion = expresion.replace("(>)", "鸡")
    elif expresion.find("(=)") != -1:
        expresion = expresion.replace("(=)", "卡")
    elif expresion.find("(LPARENT)") != -1:
        expresion = expresion.replace("(LPARENT)", "丝")
    elif expresion.find("(RPARENT)") != -1:
        expresion = expresion.replace("(RPARENT)", "瓜")

    for caracter, chino in caracteres_reemplazar.items():
        expresion = expresion.replace(caracter, chino)
    return expresion

def revertir_caracteres(expresion):
    caracteres_revertir = {'替': 't', '换': 'n', '空': 's', '加': '+', '点': '-', '苦': '_', '阿': '*', '贝': '/', '色': ';', '日': ':=', '伊': '<', '鸡': '>', '卡': '=', '丝': '(', '瓜': ')'}
    for chino, caracter in caracteres_revertir.items():
        expresion = expresion.replace(chino, caracter)
    return expresion

def convertir_transiciones(transiciones, revertir_caracteres):
    nuevas_transiciones = {}
    for clave, valor in transiciones.items():
        nueva_clave = revertir_caracteres(clave)
        if isinstance(valor, dict):
            nuevo_valor = {revertir_caracteres(k): revertir_caracteres(v) for k, v in valor.items()}
        else:
            nuevo_valor = [revertir_caracteres(v) for v in valor]
        nuevas_transiciones[nueva_clave] = nuevo_valor
    return nuevas_transiciones

def expandir_extensiones(expresion):
    expresion = reemplazar_caracteres(expresion)

    patron_extension = '[^\]]+'
    inicio = expresion.find('[')
    while inicio != -1:
        fin = expresion.find(']', inicio)
        coincidencia = expresion[inicio+1:fin]
        rangos = coincidencia.split(' ')
        expresion_rangos = []
        for rango in rangos:
            if '-' in rango:
                inicio_rango, fin_rango = rango.split('-')
                if len(inicio_rango) == 1 and len(fin_rango) == 1:
                    expresion_rangos.append(expandir_rango((inicio_rango, fin_rango)))
                elif len(inicio_rango) == 3 and inicio_rango[0] == "'" and inicio_rango[2] == "'" and len(fin_rango) == 3 and fin_rango[0] == "'" and fin_rango[2] == "'":
                    expresion_rangos.append(expandir_rango((inicio_rango[1], fin_rango[1])))
            elif rango[0] == "'" and rango[-1] == "'":
                palabra = rango[1:-1]
                expresion_rangos.append(f'({"|".join(palabra)})') 
            else:
                expresion_rangos.append(rango)
        
        expresion = expresion.replace(f'[{coincidencia}]', f'({"|".join(expresion_rangos)})')
        inicio = expresion.find('[', fin)
    
    return expresion

def convertir_expresion(expresion):
    lista = list(expresion)
    alfabeto = []
    operandos = ['+', '.', '*', '|', '(', ')', '[', ']', '{', '}','?']

    for i in lista:
        if i not in operandos:
            if i not in alfabeto:
                alfabeto.append(i)

    alfabeto.append('')
    
    i = 0
    while i < len(lista):
        if lista[i] == '+':
            if i > 0 and lista[i - 1] not in ')]}':
                lista[i - 1] = lista[i - 1] + lista[i - 1] + '*'
                del lista[i]
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
                lista[i] = ''.join(almacen) + ''.join(almacen) + '*'
                del lista[i-len(almacen):i]
        else:
            i += 1

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

class Estado:
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
            nodo = Estado()
            nodo.label = char
            nodo.anulable = True
            nodo.primera_pos = set()
            nodo.ultima_pos = set()
            stack.append(nodo)
        elif char.isalpha() or char == '#' or char.isalnum() and char != 'E':
            nodo = Estado()
            nodo.label = char
            nodo.etiqueta = nodo_etiqueta  
            nodo.anulable = False
            nodo.primera_pos = {nodo_etiqueta}
            nodo.ultima_pos = {nodo_etiqueta}
            nodos[nodo_etiqueta] = nodo
            nodo_etiqueta += 1 
            stack.append(nodo)
        elif char in "|.*":
            nodo = Estado()
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
    estado_aceptacion = max(nodos.keys())
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
    return estados, transiciones_estados, estado_aceptacion

def graficar_afd_directo(estados, transiciones, numero_grafico, carpeta_guardado):
    dot = graphviz.Digraph(format='png')

    estado_aceptacion = max(nodos.keys()) 
    estados_invertidos = {v: k for k, v in estados.items()}
    
    for estado, transiciones_estado in transiciones.items():
        for transicion, estado_destino in transiciones_estado.items():
            dot.edge(estado, estado_destino, label=revertir_caracteres(transicion))
        if estado_aceptacion in estados_invertidos[estado]:
            dot.node(estado, shape='doublecircle')

    filename = f'afd_graph_directo{numero_grafico}'
    filepath = os.path.join(carpeta_guardado, filename)
    dot.render(filepath, view=False)

def unir_afds(lista_estados):
    nuevo_estado_inicial = 's0'
    transiciones_totales = {}
    estados_totales = {nuevo_estado_inicial}

    for i, (estados, transiciones, estado_aceptacion) in enumerate(lista_estados):
        nuevo_estado_inicial_afd = f'q{i+1}_s0'
        if nuevo_estado_inicial in transiciones_totales:
            transiciones_totales[nuevo_estado_inicial].append(nuevo_estado_inicial_afd)
        else:
            transiciones_totales[nuevo_estado_inicial] = [nuevo_estado_inicial_afd]
        estados_totales.add(nuevo_estado_inicial_afd)

        for estado, transiciones_estado in transiciones.items():
            nuevo_estado = f'q{i+1}_{estado}'
            estados_totales.add(nuevo_estado)
            transiciones_totales[nuevo_estado] = {}

            for simbolo, estado_destino in transiciones_estado.items():
                nuevo_estado_destino = f'q{i+1}_{estado_destino}'
                transiciones_totales[nuevo_estado][simbolo] = nuevo_estado_destino

        estados_totales.add(f'q{i+1}_{estado_aceptacion}')

    return estados_totales, transiciones_totales, nuevo_estado_inicial

def graficar_afd_unidos(estados, transiciones, nuevo_estado_inicial):
    dot = graphviz.Digraph(format='png')

    estados_aceptacion = set(e for e in estados if e != nuevo_estado_inicial and 'q' in e)
    nuevo_estado_inicial = str(nuevo_estado_inicial)

    for estado_origen, transiciones_estado in transiciones.items():
        estado_origen = str(estado_origen)
        if isinstance(transiciones_estado, list):
            for estado_destino in transiciones_estado:
                dot.edge(estado_origen, str(estado_destino), label='ε')
        else:
            for simbolo, estado_destino in transiciones_estado.items():
                dot.edge(estado_origen, str(estado_destino), label=revertir_caracteres(simbolo))
        if estado_origen in estados_aceptacion:
            dot.node(estado_origen, shape='doublecircle')

    dot.render('afd_graph_unido', view=False)

class SintaxisError(Exception):
    def __init__(self, message, expresion):
        super().__init__(message)
        self.expresion = expresion

def validar_sintaxis(expresion):
    stack = []
    single_quote_open = False

    for char in expresion:
        if char == "'":
            single_quote_open = not single_quote_open
        elif char in "([{":
            stack.append(char)
        elif char in ")]}":
            if not stack:
                raise SintaxisError(f"Error: Paréntesis o corchete sin coincidencia de apertura en la expresión.", expresion)
            ultimo = stack.pop()
            if (char == ")" and ultimo != "(") or (char == "]" and ultimo != "[") or (char == "}" and ultimo != "{"):
                raise SintaxisError(f"Error: Paréntesis o corchete no coincide con la apertura en la expresión.", expresion)

    if stack:
        raise SintaxisError(f"Error: Paréntesis o corchete sin coincidencia de cierre en la expresión.", expresion)

    if single_quote_open:
        raise SintaxisError(f"Error: Comilla simple sin coincidencia de cierre en la expresión.", expresion)

lista_tokens_validos = []

def simular_cadena(cadena, estados, transiciones, estado_aceptacion, lista_tokens, yalex_contenido):
    tokens = []
    listTokens = []
    estados_invertidos = {item: index for index, item in enumerate(estados)}
    estado_inicial_actual_index = 0
    automata_index = None
    sufijos = ['_s0', '_s1', '_s2', '_s3', '_s4', '_s5', '_s6', '_s7', '_s8', '_s9']

    while cadena:
        estado_actual = transiciones['s0'][estado_inicial_actual_index]
        encontrado = False

        if estado_actual != 's0':
            for simbolo in transiciones[estado_actual]:
                if cadena.startswith(simbolo):
                    estado_actual = transiciones[estado_actual][simbolo]
                    tokens.append((simbolo, estado_actual))
                    cadena = cadena[len(simbolo):]
                    encontrado = True
                    break

        if not encontrado:
            estado_inicial_actual_index += 1
            if estado_inicial_actual_index >= len(transiciones['s0']):
                return tokens, cadena

        for sufijo in sufijos:
            if estado_actual.startswith('q') and estado_actual.endswith(sufijo):
                automata_index = estado_inicial_actual_index
                break

    if automata_index is not None:
        token_name = lista_tokens[automata_index]
        print(f"Token encontrado: {token_name}")

        en_rule_tokens = False
        for linea in yalex_contenido.split('\n'):
            if linea.startswith('rule tokens'):
                en_rule_tokens = True
                continue

            if en_rule_tokens:
                if '|' not in linea:
                    break

                partes = linea.strip().split('|')
                if len(partes) > 1:
                    exp = partes[1].strip()
                    exp = exp.split('{')[0].strip()
                    if exp == token_name:
                        action = partes[1].split('{')[1].split('}')[0].strip()
                        if action.startswith('return'):
                            actionValor = action.split(' ')[1]
                            print(f"Token: {actionValor}")
                            listTokens.append(actionValor)
                            if actionValor != '$':
                                lista_tokens_validos.append(actionValor)
                        else:
                            exec(action) 
                        break

    else:
        print("No se pudo simular completamente la cadena.")

    return tokens, ''

def gramatica(yapar_contenido):
    grammar = {}
    grammar_started = False
    for line in yapar_contenido:
        line = line.strip()
        if line.startswith('%%'):
            grammar_started = True
            continue
        if grammar_started and line:
            if ':' in line:
                production, symbols = line.split(':', 1)
                production = production.strip()
                symbol_list = [symbol.strip().split() for symbol in symbols.split('|')]
                symbol_list = [[symbol[:-1] if symbol.endswith(';') else symbol for symbol in production] for production in symbol_list]
                grammar[production] = symbol_list
            else:
                symbol = line.strip()
                if symbol.endswith(';'):
                    symbol = symbol[:-1].strip()
                grammar[symbol] = []

    #print(f'\nGramatica: {grammar}')
    return grammar

def countGrammar(yapar_contenido):
    grammar = {}
    grammar_started = False
    production_counter = 1 

    for line in yapar_contenido:
        line = line.strip()
        if line.startswith('%%'):
            grammar_started = True
            continue
        if grammar_started and line:
            if ':' in line:
                lhs, rhs = line.split(':', 1)
                lhs = lhs.strip()
                rhs_list = [rhs_part.strip().split() for rhs_part in rhs.split('|')]
                for rhs in rhs_list:
                    if rhs[-1].endswith(';'):
                        rhs[-1] = rhs[-1][:-1]
                    grammar[production_counter] = (lhs, rhs)
                    production_counter += 1
            else:
                symbol = line.strip()
                if symbol.endswith(';'):
                    symbol = symbol[:-1].strip()
                grammar[production_counter] = (lhs, [symbol])
                production_counter += 1

    return grammar

def aumentar_gramatica(grammar):
    produccion_inicial = list(grammar.keys())[0]
    nuevo_simbolo = 'S'
    while nuevo_simbolo in grammar:
        nuevo_simbolo += '0'

    grammar[nuevo_simbolo] = [[produccion_inicial]]

    #print(f'\nGramatica aumentada: {grammar}')
    return grammar

def closure(items, grammar):
    added = True
    while added:
        added = False
        for item in list(items):
            lhs, rhs = item.split(' -> ')
            rhs_symbols = rhs.split(' ')
            if '.' in rhs_symbols:
                dot_index = rhs_symbols.index('.')
                if dot_index < len(rhs_symbols) - 1:
                    next_symbol = rhs_symbols[dot_index + 1]
                    if next_symbol in grammar:
                        new_items = []
                        for production in grammar[next_symbol]:
                            production_str = ' '.join(production)
                            new_item = next_symbol + ' -> . ' + production_str
                            if new_item not in items:
                                new_items.append(new_item)
                                added = True
                        items.update(new_items)
    return items

def goto(items, symbol, grammar):
    new_items = set()

    for item in items:
        lhs, rhs = item.split(' -> ')
        rhs_symbols = rhs.split(' ')
        if '.' in rhs_symbols:
            dot_index = rhs_symbols.index('.')
            if dot_index < len(rhs_symbols) - 1 and rhs_symbols[dot_index + 1] == symbol:
                new_rhs_symbols = rhs_symbols[:dot_index] + [symbol, '.'] + rhs_symbols[dot_index + 2:]
                new_item = lhs + ' -> ' + ' '.join(new_rhs_symbols)
                new_items.add(new_item)

    return closure(new_items, grammar) if new_items else None

def canonical_LR0_collection(grammar, start_symbol):
    start_item = start_symbol + ' -> . ' + ' '.join(grammar[start_symbol][0])
    C = [closure(set([start_item]), grammar)]
    transitions = {}
    added = True
    acceptance_state = None

    while added:
        added = False
        for i, items in enumerate(list(C)):
            for item in items:
                lhs, rhs = item.split(' -> ')
                rhs_symbols = rhs.split(' ')
                if '.' in rhs_symbols:
                    dot_index = rhs_symbols.index('.')
                    if dot_index == len(rhs_symbols) - 1 and lhs != start_symbol:
                        acceptance_state = i
                    if dot_index < len(rhs_symbols) - 1:
                        symbol = rhs_symbols[dot_index + 1]
                        new_set = goto(items, symbol, grammar)
                        if new_set:
                            new_set_index = len(C)
                            for j, existing_set in enumerate(C):
                                if new_set == existing_set:
                                    new_set_index = j
                                    break
                            if new_set_index not in transitions.get(i, []):
                                if i not in transitions:
                                    transitions[i] = {}
                                transitions[i].setdefault(new_set_index, []).append(symbol)
                                added = True
                                if new_set not in C:
                                    C.append(new_set)

    return C, transitions, acceptance_state

def graficar_automata_LR0(collection, transitions):
    dot = graphviz.Digraph(format='png')

    state_names = {f'I{i}': f'I{i}' for i in range(len(collection))}
    for state, item_set in state_names.items():
        label = f'{item_set}:\n' + '\n'.join(collection[int(state[1])])
        dot.node(state, label=label, shape='box')

    for start, end_transitions in transitions.items():
        start_state = state_names[f'I{start}']
        for end, symbols in end_transitions.items():
            end_state = state_names[f'I{end}']
            for symbol in symbols:
                dot.edge(start_state, end_state, label=symbol)

    dot.render('automata_LR0', view=False)

    return dot

def primero_no_terminal(no_terminal, grammar, primero, procesados=None):
    if procesados is None:
        procesados = set()

    if no_terminal in procesados:
        return primero[no_terminal]

    procesados.add(no_terminal)

    primero_set = set()

    for production in grammar[no_terminal]:
        for symbol in production:
            if symbol in grammar:
                if symbol != no_terminal:
                    primero_symbol = primero_no_terminal(symbol, grammar, primero, procesados)
                    primero_set.update(primero_symbol - {'ε'})
                    if 'ε' not in primero_symbol:
                        break
                else:
                    if 'ε' in primero[symbol]:
                        primero_set |= primero[symbol] - {'ε'}
                    else:
                        break
            else:
                primero_set.add(symbol)
                break
        else:
            primero_set.add('ε')

    procesados.remove(no_terminal)
    primero[no_terminal] = primero_set
    return primero_set

def calcular_primero(grammar):
    primero = {}

    for no_terminal in grammar:
        primero[no_terminal] = set()

    for no_terminal in grammar:
        primero_no_terminal(no_terminal, grammar, primero)

    return primero

def calcular_siguiente(grammar, start_symbol, primero):
    follow = {non_terminal: set() for non_terminal in grammar.keys()}
    follow[start_symbol].add('$')

    while True:
        updated = False
        for non_terminal, productions in grammar.items():
            for production in productions:
                for i, symbol in enumerate(production):
                    if symbol in grammar:
                        if i < len(production) - 1:
                            siguiente_symbol = set()
                            for j in range(i + 1, len(production)):
                                next_symbol = production[j]
                                if next_symbol in grammar:
                                    siguiente_symbol |= primero[next_symbol] - {'ε'}
                                    if 'ε' not in primero[next_symbol]:
                                        break
                                else:
                                    siguiente_symbol.add(next_symbol)
                                    break
                            else:
                                siguiente_symbol |= follow[non_terminal]

                            if not follow[symbol].issuperset(siguiente_symbol):
                                follow[symbol] |= siguiente_symbol
                                updated = True
                        else:
                            if not follow[symbol].issuperset(follow[non_terminal]):
                                follow[symbol] |= follow[non_terminal]
                                updated = True

        if not updated:
            break

    return follow

def verificar_gramatica_SLR(tabla_SLR):
    for estado in tabla_SLR:
        acciones = estado.values()
        if len(acciones) != len(set(acciones)):
            return False
    return True

def generar_tabla_SLR(canonical_collection, transitions, acceptance_state, grammar, start_symbol, follow):
    table = [{} for _ in range(len(canonical_collection))]

    production_indices = {}
    production_index = 1
    for lhs, productions in grammar.items():
        for production in productions:
            production_indices[(lhs, tuple(production))] = production_index
            production_index += 1

    for i, item_set in enumerate(canonical_collection):
        for item in item_set:
            lhs, rhs = item.split(' -> ')
            rhs_symbols = rhs.split(' ')
            dot_index = rhs_symbols.index('.')
            if dot_index < len(rhs_symbols) - 1:
                symbol = rhs_symbols[dot_index + 1]
                goto_state = goto(item_set, symbol, grammar)
                if goto_state:
                    goto_state_index = canonical_collection.index(goto_state)
                    if symbol in grammar:
                        table[i][symbol] = f'S{goto_state_index}'
                    else:
                        table[i][symbol] = f'S{goto_state_index}'
            else:
                if lhs != start_symbol:
                    production = (lhs, tuple(rhs_symbols[:-1]))
                    if production in production_indices:
                        prod_index = production_indices[production]
                        for symbol in follow[lhs]:
                            if symbol in table[i] and table[i][symbol] != f'r{prod_index}':
                                return table, False 
                            table[i][symbol] = f'r{prod_index}'
                else:
                    table[i]['$'] = 'aceptar'

    return table, True

def simular_sintactico(cadena_tokens, tabla_SLR, grammar):
    pila = [0] 
    cadena_tokens.append('$') 

    while True:
        estado_actual = pila[-1]
        token_actual = cadena_tokens[0]
        accion = tabla_SLR[estado_actual].get(token_actual)
        
        print(f"Estado actual: {estado_actual}")
        print(f"Token actual: {token_actual}")
        print(f"Acción: {accion}")
        print(f"Pila: {pila}")
        print(f"Cadena: {cadena_tokens}")
        print("-------------")

        if accion is None:
            print(f"Error de sintaxis en el token: {token_actual}")
            return False, f"Error de sintaxis en el token: {token_actual}"
        
        if accion.startswith('S'):
            nuevo_estado = int(accion[1:])
            pila.append(nuevo_estado) 
            cadena_tokens.pop(0)

        elif accion.startswith('r'):
            produccion_index = int(accion[1:])
            if produccion_index in grammar:
                lhs, rhs = grammar[produccion_index]
                for _ in range(len(rhs)):
                    pila.pop() 
                estado_actual = pila[-1]
                transicion = tabla_SLR[estado_actual].get(lhs)
                if transicion and transicion.startswith('S'):
                    pila.append(int(transicion[1:])) 
                else:
                    print(f"Error: No hay transición para {lhs} en el estado {estado_actual}")
                    return False, f"Error: No hay transición para {lhs} en el estado {estado_actual}"
            else:
                print(f"Producción no encontrada para el índice: {produccion_index}")
                return False, f"Producción no encontrada para el índice: {produccion_index}"

        elif accion == 'aceptar':
            print("Cadena aceptada.")
            return True, None
        
        else:
            print(f"Error de sintaxis en el token: {token_actual}")
            return False, f"Error de sintaxis en el token: {token_actual}"

def AFD_yalex(yalex_contenido, yapar_contenido, lista_cadenas, show_error_function):
    lineas = yalex_contenido.split('\n')
    yapar_contenido = yapar_contenido.split('\n')
    expresiones = []
    lista_estados = []
    lista_transiciones_let = []
    lista_tokens = []
    lista_unidos = []
    carpeta_guardado = 'AFD_Graphs'
    error_ocurrido = False
    transiciones = None
    estado_aceptacion = None

    def process_string(input_string):
        if input_string.startswith("'") and input_string.endswith("'"):
            no_quotes = input_string[1:-1]
            result = '.'.join(no_quotes)
            return result
        return input_string

    for linea in lineas:
        if linea.startswith('let'):
            partes = linea.split('=')
            nombre = partes[0].strip().split(' ')[1]
            valor = partes[1].strip()
            valor = process_string(valor)
            expresiones.append((nombre, valor))

    expresiones_dict = dict(expresiones)

    def reemplazar_referencias(exp):
        while True:
            exp_previa = exp
            for nombre, valor in expresiones_dict.items():
                if not (exp.startswith("'") and exp.endswith("'")):
                    index = exp.find(nombre)
                    while index != -1:
                        if (
                            (index == 0 or not exp[index - 1].isalnum()) and
                            (index + len(nombre) == len(exp) or not exp[index + len(nombre)].isalnum())
                        ):
                            exp = exp[:index] + f'({valor})' + exp[index + len(nombre):]
                        index = exp.find(nombre, index + 1)
            if exp == exp_previa:
                break
        return exp

    for _, exp in expresiones:
        try:
            validar_sintaxis(exp)
        except SintaxisError as e:
            show_error_function(f"{str(e)} (Expresión: {e.expresion})")
            error_ocurrido = True
            break

        expresion_completa = reemplazar_referencias(exp)

        infix = convert_optional(expresion_completa)
        infix = expandir_extensiones(infix)
        infix, alfabeto = convertir_expresion(infix)
        exp_explicita = concatenacion(infix)
        postfix = infix_postfix(exp_explicita)

        exp_aumentada = aumentar_expresion(postfix)
        
        arbol_sintactico = construir_AS(exp_aumentada)
        estados, transiciones, estado_aceptacion = construir_transiciones(arbol_sintactico, exp_aumentada)
        lista_transiciones_let.append((estados, transiciones, estado_aceptacion))

    if not error_ocurrido:
        en_rule_tokens = False
        for linea in lineas:
            if linea.startswith('rule tokens'):
                en_rule_tokens = True
                continue

            if en_rule_tokens:
                if '|' not in linea:
                    break

                partes = linea.strip().split('|')
                if len(partes) > 1:
                    exp = partes[1].strip()
                    exp = exp.split('{')[0].strip()
                    lista_tokens.append(exp)
                    exp = reemplazar_referencias(exp)

                try:
                    validar_sintaxis(exp)
                except SintaxisError as e:
                    show_error_function(f"{str(e)} (Expresión: {e.expresion})")
                    error_ocurrido = True
                    break

                if not error_ocurrido:
                    print("Expresion: ", exp)
                    infix = convert_optional(exp)
                    infix = expandir_extensiones(infix)
                    infix, alfabeto = convertir_expresion(infix)
                    exp_explicita = concatenacion(infix)
                    postfix = infix_postfix(exp_explicita)
                    exp_aumentada = aumentar_expresion(postfix)
                    arbol_sintactico = construir_AS(exp_aumentada)
                    estados, transiciones, estado_aceptacion = construir_transiciones(arbol_sintactico, exp_aumentada)
                    lista_estados.append((estados, transiciones, estado_aceptacion))

        if not error_ocurrido:
            estados_totales, transiciones_totales, nuevo_estado_inicial = unir_afds(lista_estados)
            lista_unidos.append((estados_totales, transiciones_totales, estado_aceptacion))
            graficar_afd_unidos(estados_totales, transiciones_totales, nuevo_estado_inicial)

        transiciones_totales = convertir_transiciones(transiciones_totales, revertir_caracteres)
        
        grammar = gramatica(yapar_contenido)
        augmented_grammar = aumentar_gramatica(grammar)
        start_symbol = 'S'
        canonical_collection, transitions, acceptance_state = canonical_LR0_collection(augmented_grammar, start_symbol)

        print("\nCanonical LR(0) Collection:")
        for i, item_set in enumerate(canonical_collection):
            print(f"\nItem set {i}:")
            for item in item_set:
                print(f"{item}")

        graficar_automata_LR0(canonical_collection, transitions)

        primero = calcular_primero(grammar)
        print("\nPrimeros:")
        for no_terminal, primero_set in primero.items():
            print(f"primero({no_terminal}): {primero_set}")
        
        siguiente = calcular_siguiente(grammar, start_symbol, primero)
        print("\nSiguientes:")
        for no_terminal, siguiente_set in siguiente.items():
            print(f"siguiente({no_terminal}): {siguiente_set}")

        table, is_SLR = generar_tabla_SLR(canonical_collection, transitions, acceptance_state, augmented_grammar, start_symbol, siguiente)

        if not is_SLR:
            show_error_function("La gramática no es SLR, modifique la gramática para que sea SLR.")
            return lista_estados, transiciones, estado_aceptacion, primero, siguiente
        else:
            print("\nTabla SLR:")
            for i, row in enumerate(table):
                print(f"Estado {i}:")
                for symbol, action in row.items():
                    print(f"  {symbol}: {action}")
            
            cadenas_entrada = lista_cadenas
            for cadena_entrada in cadenas_entrada:
                print(f"\nSimulando cadena: {cadena_entrada}")
                tokens, resto = simular_cadena(cadena_entrada, estados_totales, transiciones_totales, estado_aceptacion, lista_tokens, yalex_contenido)

            print(f'\ntengo miedo {lista_tokens_validos}')

            countgrammar = countGrammar(yapar_contenido)
            if cadenas_entrada:
                print(f"\nSimulando cadena de tokens: {cadenas_entrada}")
                aceptado, error = simular_sintactico(lista_tokens_validos, table, countgrammar)
                lista_tokens_validos.clear()
                if aceptado == False:
                    show_error_function(error)

    return lista_estados, transiciones, estado_aceptacion, primero, siguiente

def main():
    root = tk.Tk()
    text_editor = TextEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
