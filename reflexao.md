# Reflexão — Transparência em Sistemas Distribuídos

## Questões para reflexão — Tarefa 1 (Acesso)
- Execute com CONFIG_BACKEND=local e depois com CONFIG_BACKEND=http (vai falhar com ConnectionError — esperado). O código cliente precisou mudar entre as duas execuções?
  - Não, o código cliente permanece igual. Só muda a configuração do ambiente, mostrando a transparência de acesso.
- Identifique os papéis de ConfigRepository, LocalConfig e get_repo_from_env() no padrão Strategy.
  - ConfigRepository é a interface/contrato, LocalConfig é uma implementação concreta, e get_repo_from_env() é a fábrica que seleciona a estratégia conforme o ambiente.

## Questões para reflexão — Tarefa 2 (Localização)
- O ServiceLocator faz resolução estática (na inicialização). O que precisaria mudar para que a resolução fosse dinâmica — refletindo instâncias que sobem e caem em tempo real?
  - Seria necessário consultar um serviço de registro dinâmico, como Consul, etcd ou DNS, a cada chamada, em vez de usar um dicionário fixo.
- Cite duas tecnologias de produção utilizadas como service registry (além do Consul).
  - etcd e Eureka (Netflix OSS).

## Questões para reflexão — Tarefa 3 (Migração)
- A sessão persistiu entre dois processos Python completamente separados. O que isso demonstra sobre o princípio de separação entre estado e lógica computacional (stateless application + stateful store)?
  - Demonstra que o estado do usuário não depende da instância, permitindo migração transparente e alta disponibilidade.
- Por que uma variável global em memória (session_store = {}) não resolve o problema mesmo com as duas instâncias na mesma máquina física, em um cenário com múltiplas réplicas da aplicação?
  - Porque cada processo tem seu próprio espaço de memória; apenas um store externo como Redis garante persistência e compartilhamento entre réplicas.

## Questões para reflexão — Tarefa 4 (Relocação)
- Qual é a diferença prática entre migração (Tarefa 3) e relocação (esta tarefa)? Por que relocação é tecnicamente mais difícil?
  - Migração ocorre quando o serviço é movido entre instâncias, mas não há uso ativo. Relocação ocorre durante uso ativo, exigindo continuidade sem perda de dados ou interrupção.
- O buffer interno (_message_buffer) garante semântica de entrega exactly-once? O que poderia causar entrega duplicada ou perda de mensagem mesmo com o buffer?
  - Não garante exactly-once. Falhas de rede, reconexão ou bugs podem causar duplicidade ou perda.
- A mudança de estado MIGRATING -> RECONNECTING -> CONNECTED é uma máquina de estados. Por que modelar estados explicitamente em vez de uma flag booleana is_relocating?
  - Permite maior controle e clareza sobre o ciclo de vida da conexão, facilitando manutenção e extensibilidade.
- Cite um sistema real em que transparência de relocação é requisito.
  - Live migration de VMs (ex: VMware vMotion) e rescheduling de Pods no Kubernetes.

## Questões para reflexão — Tarefa 5 (Replicação)
- O código acima implementa consistência read-your-writes? O que precisaria mudar para garantir essa propriedade?
  - Não, pois leituras podem ir para réplicas desatualizadas. Para garantir read-your-writes, o pool deveria direcionar leituras para o master após uma escrita ou usar sincronização entre réplicas.
- Uma versão anterior deste código usava recursão no fallback (return self.query(sql, write=True)). Por que isso é perigoso? Como a versão atual resolve o problema?
  - Recursão pode causar loop infinito em caso de falha persistente. A versão atual faz fallback direto e evita recursão.

## Questões para reflexão — Tarefa 6 (Concorrência)
- Por que esta tarefa usa multiprocessing em vez de threading? O que é o GIL e por que ele interfere na demonstração de race conditions?
  - Multiprocessing cria processos independentes, cada um com seu próprio GIL. O GIL impede concorrência real entre threads, tornando race conditions menos evidentes.
- O distributed_lock usa o Redis Cloud — um servidor externo aos dois processos. Por que isso é fundamentalmente diferente de um threading.Lock() local, que só funciona dentro de um único processo?
  - O lock distribuído funciona entre processos e máquinas diferentes, enquanto threading.Lock é restrito ao processo local.
- O que acontece se o Processo-A travar dentro da seção crítica (antes do finally)? Como o parâmetro ex (TTL) mitiga esse risco? Existe algum risco residual mesmo com o TTL?
  - O lock expira automaticamente após o TTL, evitando deadlock. Riscos residuais incluem operações não-atômicas ou TTL insuficiente.

## Questões para reflexão — Tarefa 7 (Falha e Circuit Breaker)
- Qual das oito falácias da computação distribuída de Peter Deutsch (1994) o anti_pattern.py viola diretamente? Enuncie a falácia.
  - "A rede é confiável". O código assume que chamadas remotas sempre funcionam como locais, ignorando latência e falhas.
- Por que async/await é uma forma deliberada de quebrar a transparência — e por que isso é, neste contexto, a decisão correta de design?
  - Porque explicita que a operação pode ser suspensa, ter latência ou falhar, forçando o desenvolvedor a tratar esses casos.

## Questões para reflexão — Circuit Breaker (Parte B)
- O Circuit Breaker executável funcionou conforme esperado: após três falhas consecutivas, o estado mudou para OPEN e as chamadas passaram a falhar rapidamente, evitando sobrecarga e espera desnecessária. Quando o tempo de recuperação passa, o estado vai para HALF_OPEN e testa se o serviço voltou. Isso demonstra resiliência e proteção contra cascata de falhas.

---

## Bloco de Reflexão (obrigatório)

## 1. Síntese
A transparência de concorrência é a mais difícil de implementar corretamente em sistemas reais. O output do roteiro mostra que, mesmo usando Redis para lock distribuído, ainda há risco de race condition se o lock não for adquirido por todos os processos, como ocorreu no erro "Recurso 'conta:saldo' em uso — tente novamente". Garantir exclusão mútua entre processos distribuídos exige coordenação precisa e tolerância a falhas, pois o lock pode expirar ou não ser liberado corretamente. O uso de mecanismos como Redis Cloud é fundamental, mas ainda assim há desafios técnicos, como deadlocks e falhas de rede.

## 2. Trade-offs
Em sistemas como jogos online ou apps de mensagens, esconder completamente a distribuição pode prejudicar a resiliência. Por exemplo, se o sistema mascarar falhas de servidores e não informar o usuário, ele pode perder progresso ou mensagens sem saber. O output do Circuit Breaker mostra que, após várias falhas, o sistema "abre" e rejeita chamadas rapidamente, evitando que o usuário fique esperando indefinidamente. Transparência excessiva pode ocultar problemas reais e dificultar a recuperação do usuário.

## 3. Conexão com Labs anteriores
O uso de `async/await` (visto no Lab 02 e na Tarefa 7) é uma forma de quebrar a transparência conscientemente. O output do exemplo "bom_pattern.py" mostra que o contrato explícito (async, timeout, Optional[dict]) força o chamador a lidar com falhas e latência, tornando o comportamento distribuído visível. Isso é importante para evitar que o usuário ou desenvolvedor assuma que todas as operações são locais e instantâneas, o que não é verdade em sistemas distribuídos.

## 4. GIL e multiprocessing
A Tarefa 6 usa `multiprocessing` porque o GIL (Global Interpreter Lock) do CPython impede que threads executem bytecode Python simultaneamente, tornando difícil reproduzir race conditions reais. O output mostra que, com processos separados, o saldo final no Redis pode ser incorreto devido à concorrência, evidenciando a necessidade de mecanismos distribuídos de exclusão mútua. O GIL interfere apenas em threads dentro do mesmo processo, não entre processos distintos.

## 5. Desafio técnico
O provisionamento do Redis Cloud foi tranquilo, mas o exercício mais interessante foi observar a persistência de sessão entre instâncias na Tarefa 3. O output mostra que a sessão salva por "instancia_a.py" foi recuperada por "instancia_b.py", demonstrando o princípio de separação entre lógica e estado. Isso evidencia como sistemas distribuídos podem garantir continuidade para o usuário mesmo após migração de servidores, desde que o estado esteja em um store externo como Redis Cloud.