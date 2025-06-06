class NonlinearBuckConverter:
  global y_tau_y
  global u_tau_u
  global dados_salvos_antes_do_ataque
  global yk
  global uk
  """
  Classe para criar e gerenciar o modelo não linear de um conversor Buck.

  Parâmetros:
                  name (str): Nome do sistema.
  """

  def __init__(self, name):
    self.name = name
    self.inputs = ('D', 'P_CPL')
    self.outputs = ('iL', 'vC')
    self.states = ('iL', 'vC')
    self.system = ct.NonlinearIOSystem(
        self.update, self.output, name=self.name,
        inputs=self.inputs, outputs=self.outputs, states=self.states
    )

  def update(self, t, x, u, params):
    """
    Função de atualização para a representação em espaço de estados do conversor Buck.

    Parâmetros:
                    t (float): Tempo.
                    x (array): Estados do sistema.
                    u (array): Entradas do sistema.
                    params (dict): Dicionário de parâmetros do sistema.

    Retorna:
                    dx (array): Derivada dos estados do sistema.
    """
    V_IN = params.get('Vin', 0)  # Tensão de entrada
    RL = params.get('rL', 0)     # Resistência (indutor)
    RC = params.get('rC', 0)     # Resistência (capacitor)
    L = params.get('L', 1)       # Indutância
    C = params.get('C', 1)       # Capacitância
    D, P_CPL = u

    IL, VC = x
    diL = (V_IN / L) * D - (RL / L) * IL - VC / L
    dvC = IL / C - VC / (C * RC) - P_CPL / (C * VC)
    dx = np.array([diL, dvC])
    return dx

  
  def output(self, t, x, u, params):
    global y_tau_y
    global u_tau_u
    global dados_salvos_antes_do_ataque
    global yk
    global uk
    global lk_lista_1
    global lk_lista_2
    global i
    lk_lista_1 = []
    lk_lista_2 = []
    i = 0

    """
    Função de saída para a representação em espaço de estados do conversor Buck.

    Parâmetros:
                    t (float): Tempo.
                    x (array): Estados do sistema.
                    u (array): Entradas do sistema.
                    params (dict): Dicionário de parâmetros do sistema.

    Retorna:
                    array: Saída do sistema.
    """
    attack = params.get('atk', 0) # Obtem se o ataque está ativo
    intervalo = params.get('intervalo', 0)
    kf = params.get('kf', 0)
    k0 = intervalo[0][0] # Começo da coleta de dados   
    kr = intervalo[0][1] # Fim da coleta de dados
    #============================ DoS Attack ======================================================================
    
    
    if attack == 1:
      inicio = intervalo[0][0]
      dados_salvos_antes_do_ataque = False
      
      if(t < inicio and not dados_salvos_antes_do_ataque):
        y_tau_y = np.array([  #último valor registrado dos sensores antes do ataque 
          [x[0]],
          [x[1]]
        ])
        #print(y_tau_y)
        u_tau_u = np.array([
          [u[0]]    #duty cycle armazenado antes do ataque 
        ])
        #print(u_tau_u)
        dados_salvos_antes_do_ataque = True
        return x[0:2]
      
      dentro_do_intervalo = False
      for inicio, fim in intervalo:
        
        #if(t < inicio_do_ataque and not dados_salvos_antes_do_ataque):
          #y_tau_y = np.array([  #último valor registrado dos sensores antes do ataque 
          #  [x[0]],
          #  [x[1]]
          #])

          #u_tau_u = np.array([
          #  [u[0]]    #duty cycle armazenado antes do ataque 
          #])
          #print(y_tau_y)
          #dados_salvos_antes_do_ataque = True
          #return x[:2]
      
        if inicio <= t <= fim:
          Ray = np.array([[x[0], x[1]]]) #canal de sensores que o adversário pode tornar indisponíveis, no nosso exemplo são a corrente no indutor IL e a tensão no capacitor VC
          Rau = np.array([[u[0]]])

          Sky = np.array([      #matriz binária que indica se o ataque DoS está sendo performado ou não, varia com o tempo
            [1, 0],
            [0, 1]       #depende de k!!!
          ])

          Sku = np.array([1])  #matriz binária que indica se o ataque DoS está sendo performado ou não, também varia com o tempo 

          Gamma_y = np.array([     #matriz binária que indica se o adversário possui ou não acesso aos sensores
            [1, 0],
            [0, 1]
          ])

          Gamma_u = np.array([   #matriz binária que indica se o adversário possui ou não acesso aos atuadores 
            [1]
          ]) 

          Gamma_y_transposta = Gamma_y.T  #matriz gama y maiúsculo transposta

          Gamma_u_transposta = Gamma_u.T  #matriz gama u maiúsculo transposta

          yk = np.array([  #sinal que deveria chegar ao controlador e detector de anomalias
            [x[0]],
            [x[1]]
          ])
          #print(yk)
        
        
          #uk = np.array([
          #  [u[0]]
          #])
          
          #operações para negação de serviço dos sensores
          subtracaoy = yk - y_tau_y #diferença entre o sinal que deveria ser injetado no controlador e o último sinal medido antes do ataque   
          multiplicacao1 = np.dot(Sky, Gamma_y_transposta)  #multiplicação entre a matriz que indica se o ataque está ocorrendo em determinado tempo k e a matriz que mostra os sensores que o aversário domina
          multiplicacao2 = np.dot(multiplicacao1, subtracaoy)
          byk = multiplicacao2 * -1  #matriz resultante do ataque DoS
          multiplicacao3 = np.dot(Gamma_y , byk)
          y_til_k = yk + multiplicacao3  #Sinal dos sensores negado 
          x = y_til_k

          
          #operações para a negação de serviço dos atuadores
          #subtracaou = uk - u_tau_u 
          #mult1 = np.dot(Sku, Gamma_u_transposta)
          #mult2 = np.dot(mult1, subtracaou)
          #buk = mult2 * -1
          #mult3 = np.dot(Gamma_u, byk)
          #u_til_k = uk + mult3
          #u[0] = u_til_k
          
          dentro_do_intervalo = True
          return x[:2]
      if not dentro_do_intervalo:
        return x[:2]
      
    #============================ Replay Attack ======================================================================
    if attack == 2:
      # Fase_1: coleta de dados 
      if k0 <= t <= kr:

        Upsilon_y = np.array([     #matriz binária que indica se o adversário possui ou não acesso aos dados sensores
            [1, 0],
            [0, 1]
          ])
        
        Upsilon_u = np.array([   #matriz binária que indica se o adversário possui ou não acesso aos dados dos atuadores 
            [1]
          ]) 

        yk = np.array([  #sinal medido pelos sensores iL e Vc
            [x[0]],
            [x[1]]
        ])

        #uk = np.array([
        #  [u[0]]
        #])

        multiplicacao = np.dot(Upsilon_y, yk)
        lk_lista_1.append(multiplicacao[0][0])
        lk_lista_2.append(multiplicacao[1][0])
        return x[:2]
      #Fase_2: Repetição dos dados
      if kr < t <= kf:
        n_elementos_1 = len(lk_lista_1)
        print(n_elementos_1)
        return x[:2]
      else:
        return x[:2]
    else:
      return x[:2]