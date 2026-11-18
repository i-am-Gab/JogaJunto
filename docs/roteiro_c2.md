# Roteiro curto de apresentação — Checkpoint 2

## Preparação

Na pasta do projeto, execute:

```powershell
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py seed_demo
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py runserver
```

Senha inicial de todas as contas demo novas: **JogaJuntoDemo!2026**. Se a carga já existia, as senhas e mudanças anteriores são mantidas. `--password` só define senhas de contas novas.

Se a carga avisar sobre prazo encerrado, entre como `demo_admin` no Admin e ajuste início, término e prazo das atividades usadas abaixo para datas futuras (prazo antes do início; término depois do início). A carga não apaga nem redefine dados. As ações desta apresentação alteram inscrições: confira o estado antes de ensaiar novamente.

Use uma janela normal e outra privada, ou dois perfis de navegador, para manter participante e organizador conectados separadamente. Duas janelas normais do mesmo perfil também compartilham a sessão, assim como as abas.

## Demonstração (7 a 9 minutos)

| Etapa | Conta e tela | Mostrar e falar |
| --- | --- | --- |
| 1. Proposta (30 s) | Sem login, página inicial | “O JogaJunto conecta participantes e organizadores de atividades físicas.” Mostre busca, modalidade e alternância claro/escuro. |
| 2. Detalhe (1 min) | Sem login, Ver detalhes em uma atividade | Mostre descrição completa, local e mapa, horários, preço e vagas. “Pendências e vagas reservadas também contam na ocupação.” Clique em Entrar para participar para mostrar o retorno à atividade após o login. |
| 3. Participante (1 min) | `demo_ana`, [DEMO] Corrida com aprovação | Ana já tem uma solicitação pendente. Mostre o status no detalhe e em Minhas inscrições. Não é necessário criar outra inscrição. |
| 4. Organizador (1 min) | `demo_organizador`, /organizador/ e Solicitações | Mostre indicadores e filtro pela corrida; aprove Ana e salve uma nota interna. “Cada organizador gerencia as próprias atividades.” |
| 5. Retorno ao participante (30 s) | `demo_ana`, notificações e Minhas inscrições | Atualize e mostre a aprovação. As notas do organizador são internas. |
| 6. Lista de espera (1 a 2 min) | `demo_organizador` e depois `demo_carla` | No Admin, abra [DEMO] Futebol com lista de espera, aumente o limite de 2 para 3 e salve. Em Solicitações → Lista de espera, filtre pelo futebol e aprove Carla. Entre como Carla e mostre a confirmação e a notificação. “As vagas novas respeitam a ordem da fila; reservar ainda não é aprovar.” |
| 7. Pagamento e presença (1 a 2 min) | `demo_organizador`, /admin/ | Em Pagamentos, busque Futebol concluído. Ana está PAID/PIX; Bruno, PENDING. Abra Bruno, use PAID, informe a data e salve. Em Presenças, busque o mesmo título; marque Bruno como Presente, informe a entrada e salve. “São controles manuais de pagamento e comparecimento.” |
| 8. Fecho (30 s) | README, diagrama e GitHub | “A aplicação usa três apps Django, banco relacional, perfis com permissões e Admin personalizado. Entregamos o fluxo de inscrição e seus controles, com dados e roteiro reproduzíveis.” Mostre documentação e contribuições. |

Para demonstrar uma nova inscrição automática, entre como `demo_carla` e abra **[DEMO] Longão 10K no Campus UFLA**, onde ela não está inscrita na carga inicial. Clique em Confirmar inscrição e mostre o status na mesma página. Em inscrição manual, o resultado é pendente; em atividade lotada, lista de espera.

### Etapa 6: aumento de vagas e aprovação da fila

Na carga inicial, **[DEMO] Futebol com lista de espera** tem limite de 2 participantes, Ana e Bruno aprovados e Carla na fila, sem reserva. Antes de começar, confirme que a atividade está publicada e que o prazo de confirmação ainda está aberto.

1. Entre como Rafael: **`demo_organizador`**, senha inicial **`JogaJuntoDemo!2026`**.
2. No Admin, abra **Atividades → [DEMO] Futebol com lista de espera**. Mostre o limite de 2 e a inscrição de Carla na lista de espera.
3. Aumente **Limite de Participantes** para **3** e clique em **Salvar**. Diga: “Ao aumentar a capacidade, o sistema reserva as vagas disponíveis por ordem de solicitação e notifica quem foi chamado.”
4. Abra **Solicitações**, selecione a aba **Lista de espera** e filtre pelo futebol. Mostre a mensagem **Vaga reservada por ordem da fila** e o botão **Aprovar inscrição** de Carla. Diga: “Ela ainda está na lista de espera, mas agora tem uma vaga reservada. Essa reserva já conta na ocupação.”
5. Clique em **Aprovar inscrição**. A inscrição passa para **Aprovada**, com registro das datas e notificação. O controle de aprovação também fica disponível nas inscrições dentro da atividade no Admin.
6. Em uma sessão separada, entre como **`demo_carla`**. Atualize **Minhas inscrições** e **Notificações** para mostrar o resultado. Diga: “A aprovação confirma a participação e o sistema confere novamente a capacidade para não exceder o limite.”

**Se o cenário já foi ensaiado:** a carga preserva o limite e as situações. Se o futebol já tem 3 vagas e Carla está com reserva, comece no passo 4, sem aumentar novamente. Se Carla já está aprovada, esse fluxo já foi concluído; use uma das alternativas abaixo ou prepare outra atividade com fila. Não é necessário cancelar inscrições nem reduzir a capacidade apenas para repetir a apresentação.

### Alternativas: cancelamento ou confirmação pelo participante

- **Cancelamento:** se o futebol ainda estiver lotado com limite de 2, Ana aprovada e Carla na fila sem reserva, entre como `demo_ana` e cancele a inscrição antes do início. Carla recebe a oferta da vaga liberada. Mostre a confirmação pela área de Carla ou a aprovação pela área de Rafael. Use este cenário como alternativa ao aumento de capacidade, pois ambos alteram a mesma inscrição.
- **Reserva pronta:** entre como `demo_diego` e abra **[DEMO] Caminhada com vaga reservada**, caso ele ainda esteja na lista de espera com oferta válida. Confirme em Minhas inscrições ou no detalhe da atividade. Essa atividade usa inscrição automática, então a confirmação aprova a participação.
- **Inscrição mediante aprovação:** se o participante aceitar uma reserva em atividade `MANUAL`, a inscrição vai para **Pendente**, aguardando decisão do organizador. Se o próprio organizador aprovar a reserva, a participação já fica confirmada, em ambos os tipos de atividade.

**Se o professor perguntar sobre limites:** só quem tem reserva válida recebe a opção de aprovação da fila. O sistema respeita a ordem de solicitação, o prazo, as permissões e as demais vagas ocupadas ou reservadas. Um aumento do limite não aprova pessoas automaticamente; é preciso a decisão do organizador ou a confirmação do participante, conforme o fluxo acima.

## Contas de apoio

- `demo_admin`: superusuário; gerencia contas e acessa a visão global do dashboard.
- `demo_organizador`: Rafael; corrida com aprovação, futebol com fila e futebol concluído.
- `demo_organizador2`: Mariana; caminhada com vaga reservada, pedal e beach tennis.
- `demo_organizador3`: Lucas; society, vôlei e treino de corrida.
- `demo_organizador4`: Camila; torneio de areia, caminhada, corrida e rascunho.
- `demo_ana`, `demo_bruno`, `demo_carla`, `demo_diego`: participantes; não acessam o Admin.

## Conferência antes de apresentar

- Abra os detalhes pela página inicial e verifique se os prazos dos cenários estão abertos.
- Confira se Ana ainda está pendente na corrida. Para o futebol, verifique o limite atual e se Carla está na fila sem reserva, com reserva ou já aprovada; escolha o ponto de início da etapa 6 conforme esse estado.
- Para as alternativas, confirme se Ana ainda pode cancelar o futebol ou se Diego ainda possui a reserva da caminhada dentro do prazo.
- Confira os exemplos de pagamento/presença no futebol concluído; dados editados no ensaio são preservados.
- Mantenha internet para carregar Bootstrap, ícones, mapas e gráficos. O endereço escrito no detalhe continua útil se o mapa falhar.
- Não descreva o registro de pagamento como cobrança real: não há gateway integrado.
- Confirme o repositório público, as contribuições e a entrega no Campus Virtual.
