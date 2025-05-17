
  # A def abaixo deve ser utilizada no primeiro e segundo ataque  
  def output(self, t, x, u, params, inicio_do_ataque = 0.02, intervalos = [(0.02, 0.05)], #define os intervalos de ataque DoS e o tempo de captura da matriz lk" 
    replay = [(0.03, 0.10)]):

    
    global valor_maximo_de_corrente
    global valor_minimo_de_corrente
    global valor_maximo_de_tensao
    global valor_minimo_de_tensao
    global intervalo
    
    #yk = float
    #y_tau_y = float
    
    valor_maximo_de_corrente = 30
    valor_minimo_de_corrente = 0
    valor_maximo_de_tensao = 60
    valor_minimo_de_tensao = 0
   
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
    
    """
    "Injeção de Dados Falsos"

    if( t<= 10.0):

      yk = np.array([   #sinal limpo
        [x[0]],
        [x[1]]
      ])

      gamma_y = np.array([
        [1, 0],
        [0, 1]
      ])

      gamma_u = 0

      bku = 0

      bky = np.array([
        [random.uniform(valor_maximo_de_corrente, valor_minimo_de_corrente)],
        [random.uniform(valor_maximo_de_tensao, valor_minimo_de_tensao)]
      ])

      y_til_k = yk + (np.dot(gamma_y, bky))

      x = y_til_k

      
      return x[:2]

    return x[:2]
    """

    
    
    "Denial-of-service attack"

    global y_tau_y
    global u_tau_u
    global dados_salvos_antes_do_ataque
    global yk
    #global uk
    dados_salvos_antes_do_ataque = False
    

    
    
    if(t < inicio_do_ataque and not dados_salvos_antes_do_ataque):
      y_tau_y = np.array([  #último valor registrado dos sensores antes do ataque 
        [x[0]],
        [x[1]]
      ])

      u_tau_u = np.array([
        [u[0]]    #duty cycle armazenado antes do ataque 
      ])
      #print(u_tau_u)
      dados_salvos_antes_do_ataque = True
      return x[:2]
    
    
    dentro_do_intervalo = False
    for inicio, fim in intervalos:
        
    
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



    else:
      return x[:2]