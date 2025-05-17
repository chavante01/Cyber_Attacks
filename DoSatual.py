import os
import py_dss_interface
import numpy as np
import matplotlib.pyplot as plt
import random
#import opendssdirect as dss

# Instância do OpenDSS
dss = py_dss_interface.DSS()

# ========================= CONTROLE SOC COM DEGRADAÇÃO =========================
# Variáveis globais do ataque DoS

dados_salvos_antes_do_ataque = False
x = 0 # variável que atualiza os instantes de tempo
atacando = False
# Variáveis globais do controle
soc_max = 80
soc_min = 20
contador_soc_max = 60
contador_soc_min = 40
taxa_degradacao = 0.5
contador_ciclos = 0
carga_completa = False
descarga_completa = False

soc_lista = []
soc_lista_2 = []
soc_max_lista = []
soc_min_lista = []
passos = []
kW_painel_lista = []
kW_carga_lista = []
kW_bateria_lista = []


# Variáveis globais
estado_anterior = 0  # Começa como 0 para detectar o primeiro 1
y_tau_y = None       # Valor do sensor antes do ataque
dados_salvos_antes_do_ataque = False

def bernoulli(p: float) -> int:
    if not 0 <= p <= 1:
        raise ValueError("O valor de p deve estar entre 0 e 1.")
    return 1 if random.random() < p else 0

def ataque_DoS():
    global estado_anterior
    global dados_salvos_antes_do_ataque
    global y_tau_y
    global soc

    # puxar o valor do soc_2 pra ficar de acordo com o gráfico
    dss.circuit._set_active_element("Storage.Battery")
    soc = float(dss.dssproperties._value_read("23"))

    yk = np.array([  #sinal que deveria chegar ao controlador e detector de anomalias
        [soc]
    ])
    #print(f"yk:{yk}")
    # Gera valor binário (0 ou 1) com Bernoulli
    resultado = bernoulli(0.77)
    Sky = np.array([      #matriz binária que indica se o ataque DoS está sendo performado ou não, varia com o tempo
        [resultado]  #depende do passo de simulação!!!
    ])
    #print(f"Resultado Bernoulli: {resultado}")

    # Detecta transição de 0 → 1
    if resultado == 1 and estado_anterior == 0:
        y_tau_y = np.array([[soc]])  # salva o valor do sensor
        dados_salvos_antes_do_ataque = True
        print(f"Transição detectada: salvando soc = {soc:.3f}")
    else:
        dados_salvos_antes_do_ataque = False

    estado_anterior = resultado  # atualiza para próxima chamada

    # Exibe estado atual
    #print(f"y_tau_y: {y_tau_y}")
    #print(f"dados_salvos_antes_do_ataque: {dados_salvos_antes_do_ataque}\n")

    #Sku = np.array([1])  #matriz binária que indica se o ataque DoS está sendo performado ou não, também varia com o tempo 

    Gamma_y = np.array([     #matriz binária que indica se o adversário possui ou não acesso aos sensores
        [1]
    ])

    Gamma_y_transposta = Gamma_y.T  #matriz gama y maiúsculo transposta

    #operações para negação de serviço dos sensores
    subtracaoy = yk - y_tau_y #diferença entre o sinal que deveria ser injetado no controlador e o último sinal medido antes do ataque   
    multiplicacao1 = np.dot(Sky, Gamma_y_transposta)  #multiplicação entre a matriz que indica se o ataque está ocorrendo em determinado tempo k e a matriz que mostra os sensores que o aversário domina
    multiplicacao2 = np.dot(multiplicacao1, subtracaoy)
    byk = multiplicacao2 * -1  #matriz resultante do ataque DoS
    multiplicacao3 = np.dot(Gamma_y , byk)
    y_til_k = yk + multiplicacao3  #Sinal dos sensores negado 
    soc = y_til_k
    print(f"resultado do ataque{soc}")
        
    return soc
    
def controle_soc_por_ciclo(stepNumber):
    global soc_max, soc_min, soc_2, x
    global contador_ciclos, carga_completa, descarga_completa
    global kW_painel_lista, kW_bateria_lista, kW_carga_lista

    dss.circuit._set_active_element("Storage.Battery")
    soc = float(dss.dssproperties._value_read("23"))
    kW_bateria = float(dss.dssproperties._value_read("5"))
    #descarga = float(dss.dssproperties._value_read("26"))
    #print(descarga)
    #print(soc)
    #print(kW_bateria)

    dss.circuit._set_active_element("Load.634a")
    kW_carga = dss.cktelement._powers()[0]
    #print(kW_carga)

    x = stepNumber 
    #print(stepNumber)
    dss.circuit._set_active_element("PVSystem.PV")
    kW_painel = dss.cktelement._powers()[0] * (-1)
    #print(kW_painel)

    # Salva para gráficos
    soc_lista.append(soc)
    soc_max_lista.append(soc_max)
    soc_min_lista.append(soc_min)
    passos.append(stepNumber)
    kW_carga_lista.append(kW_carga)
    kW_painel_lista.append(kW_painel)
    kW_bateria_lista.append(kW_bateria)

    # Aplicação do controle
    ataque_DoS()
   
    # Aplicação do controle
    if soc > soc_max:
        dss.text("Edit Storage.Battery %Charge=0 dispmode=external %stored=" + str(soc_max))
        #dss.text("Edit Storage.Bateria state=discharging dispmode=external %stored=" + str(soc_max))

    elif soc < soc_min:
        dss.text("Edit Storage.Battery %Discharge=0 dispmode=external %stored=" + str(soc_min))
        #dss.text("Edit Storage.Bateria %Stored={soc_min}")
    else:
        # colocar para a bateria seguir o loadshape aqui
        dss.loadshapes._name()
        dss.text("Edit Storage.Battery %Charge=100 %Discharge=100 dispmode=follow daily=storageShape")
    
    dss.circuit._set_active_element("Storage.Battery")
    soc_2 = float(dss.dssproperties._value_read("23"))
    #print(soc_2)
    # Salva para gráficos
    soc_lista_2.append(soc_2)

def solve_settings():
    dss_file = r"C:\Users\lucas\OneDrive\Desktop\simulacaodss\IEEE13bus.dss"
    dss.text("Clear")
    dss.text(f"Compile [{dss_file}]")
    dss.text("set maxcontroliter=2000")
    dss.text("set maxiterations=1000")
    dss.text("set mode=daily")
    dss.text("set stepsize=1h")
    dss.text("Disable StorageController.*")
    print("Configurações aplicadas.")
    return dss_file



dss_file = solve_settings()
original_steps = 24 # 168 passos = 7 dias
dss.solution._number_write(original_steps)

for step in range(original_steps):
    control_iter = 1
    dss.solution._init_snap()

    while not dss.solution._control_actions_done_read():
        dss.solution._solve_no_control()

        if control_iter == 1:
            controle_soc_por_ciclo(step)
            dss.solution._solve_no_control()

        dss.solution._sample_control_devices()

        if dss.ctrlqueue._queue_size() == 0:
            break

        dss.solution._do_control_actions()

        control_iter += 1
        if control_iter >= dss.solution._max_control_iterations_read():
            print("Número máximo de iterações de controle excedido.")
            break

    dss.solution._finish_time_step()

# ============================= PLOT ==============================

horas = np.linspace(0, 24, original_steps)
plt.figure(figsize=(12, 6))
plt.plot(horas, soc_lista_2, label="SOC (%)", linewidth=1)
plt.title("SOC com Controle e Degradação por Ciclos")
plt.xlabel("Hora do Dia")
plt.ylabel("SOC (%)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()