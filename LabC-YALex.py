import graphviz
import tkinter as tk
from tkinter import filedialog

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("YALex Text Editor")
        self.root.geometry("700x600")
        self.text_widget = tk.Text(root, wrap="word", undo=True, autoseparators=True)
        self.text_widget.pack(expand=True, fill="both")

        menu_bar = tk.Menu(root)
        root.config(menu=menu_bar)

        menu_bar.add_command(label="Open", command=self.open_file)
        menu_bar.add_command(label="Save", command=self.save_file)
        menu_bar.add_command(label="Run YALex", command=self.run_yalex)
        menu_bar.add_command(label="Exit", command=root.destroy)

    def open_file(self):
        file_path = filedialog.askopenfilename(title="Open YALex File", filetypes=[("YALex Files", "*.yal")])
        if file_path:
            with open(file_path, 'r') as file:
                content = file.read()
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, content)

    def save_file(self):
        file_path = filedialog.asksaveasfilename(title="Save YALex File", filetypes=[("YALex Files", "*.yal")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.text_widget.get(1.0, tk.END))

    def run_yalex(self):
        yalex_code = self.text_widget.get(1.0, tk.END)
        try:
            estados, transiciones, estado_aceptacion = AFD_yalex(yalex_code)
            self.show_graph(estados, transiciones)
        except Exception as e:
            self.show_error(str(e))

    def show_graph(self, estados, transiciones):
        dot = graphviz.Digraph(format='png')

        estado_aceptacion = max(nodos.keys())
        estados_invertidos = {v: k for k, v in estados.items()}
        for estado, transiciones_estado in transiciones.items():
            for transicion, estado_destino in transiciones_estado.items():
                dot.edge(estado, estado_destino, label=transicion)
            if estado_aceptacion in estados_invertidos[estado]:
                dot.node(estado, shape='doublecircle')

        dot.render('afd_graph_directo', view=True)

    def show_error(self, error_message):
        tk.messagebox.showerror("Error", error_message)

def convert_optional(regex):
    return regex.replace('?', '|E')

def expandir_rango(rango):
    inicio, fin = rango
    return '|'.join([f'({chr(i)})' for i in range(ord(inicio), ord(fin) + 1)])

def expandir_extensiones(expresion):
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
                lista[i] = ''.join(almacen) + '*'
                del lista[i+1]
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

def AFD_yalex(yalex_contenido):
    lineas = yalex_contenido.split('\n')
    expresiones = []
    for linea in lineas:
        if linea.startswith('let'):
            partes = linea.split('=')
            nombre = partes[0].strip().split(' ')[1]
            valor = partes[1].strip()
            expresiones.append((nombre, valor))

    print("Expresiones: ")
    for i in range(len(expresiones)):
        print(expresiones[i])

    expresiones_dict = dict(expresiones)

    def reemplazar_referencias(exp):
        for nombre, valor in expresiones_dict.items():
            exp = exp.replace(nombre, f'({valor})')
        return exp

    expresion_completa = '|'.join([f'({reemplazar_referencias(exp)})' for _, exp in expresiones])
    print("\nExpresion completa: ")
    print(expresion_completa)

    infix = convert_optional(expresion_completa)
    infix = expandir_extensiones(infix)
    infix, alfabeto = convertir_expresion(infix)
    exp_explicita = concatenacion(infix)
    postfix = infix_postfix(exp_explicita)
    print("\nExpresion postfix: ")
    print(postfix)

    exp_aumentada = aumentar_expresion(postfix)
    print("\nExpresion aumentada: ")
    print(exp_aumentada)

    arbol_sintactico = construir_AS(exp_aumentada)
    estados, transiciones, estado_aceptacion = construir_transiciones(arbol_sintactico, exp_aumentada)

    return estados, transiciones, estado_aceptacion

def main():
    root = tk.Tk()
    text_editor = TextEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()