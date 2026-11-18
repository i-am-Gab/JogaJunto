# JogaJunto

Aplicação web para criação, divulgação e gerenciamento de atividades físicas coletivas, desenvolvida para a disciplina **GAC116 - Programação Web**, da Universidade Federal de Lavras (UFLA).

Organizadores cadastram atividades e gerenciam inscrições. Participantes consultam atividades publicadas, solicitam participação e acompanham inscrições e notificações.

## Integrantes

- Gabriel Aguiar Alves e Silva
- Ronan Gustavo Carleto
- Marco Antonio Maia

## Tecnologias

- Python e Django 6.1.2, com arquitetura MVT (models, views e templates).
- SQLite como banco de dados relacional e migrations do Django para evolução do esquema.
- HTML, CSS, JavaScript e Bootstrap 5.3.2 na interface.
- Django Admin com Jazzmin 3.0.5 e CSS personalizado.
- python-dotenv para leitura de variáveis de ambiente.
- Git e GitHub para versionamento.
- Chart.js (via CDN) para visualização de gráficos estatísticos no dashboard.
- Google Maps (embed e links diretos) para pré-visualização geográfica dos locais das atividades.

## Funcionalidades implementadas

### Autenticação e perfis

- Cadastro público de participantes, login por usuário e senha e logout.
- Cadastro público não permite escolher privilégios de organizador ou administrador.
- Participante: acessa suas inscrições e notificações nas telas do site; não acessa o Admin.
- Organizador: cria atividades e gerencia suas atividades, inscrições, pagamentos e presenças no Admin; possui dashboard com indicadores e tela de análise de inscrições.
- Superusuário: acesso administrativo geral, incluindo gerenciamento de usuários e perfis, além de visão consolidada da plataforma no dashboard.
- Grupos e permissões sincronizados conforme o perfil do usuário.
- O dashboard e a análise de solicitações ficam restritos a organizadores; participante recebe negação de acesso.

### Atividades

- Listagem pública de atividades publicadas, com modalidade, local, horário, valor, barra de progresso de ocupação e indicador de inscrição (imediata ou mediante aprovação).
- Barra de busca instantânea (por título, local ou cidade) e filtros rápidos por modalidade na página inicial.
- Mini-mapa interativo (Google Maps) nos cards de atividades, priorizando coordenadas geográficas (`latitude` e `longitude`) com fallback automático para endereço completo, além de atalho para abrir a rota no Google Maps.
- Criação de atividades pela tela do organizador; nessa tela, a atividade é publicada diretamente.
- Dashboard do organizador (`/organizador/`) com totais de atividades, pendências, confirmadas, lista de espera e vagas ocupadas, gráficos de pizza por modalidade (visão individual do organizador e visão global da plataforma para superusuários) e lista das atividades do próprio usuário.
- Atalhos do dashboard para criar atividade e abrir a análise de solicitações, inclusive filtrada por atividade.
- Cadastro, consulta, edição e exclusão de atividades pelo Admin, respeitando as permissões.
- Modalidades e locais gerenciados pelo Admin. Organizadores podem cadastrar esses registros; sua edição e exclusão ficam restritas ao superusuário.
- Atividades gratuitas ou pagas, com limite de vagas, prazo de confirmação e inscrição automática ou mediante aprovação.
- Estados: rascunho, publicada, cancelada e finalizada.

### Inscrições, lista de espera e notificações

- Inscrição autenticada, automática ou sujeita à aprovação do organizador.
- Área “Minhas inscrições” com filtros por situação, contagens e paginação.
- Aprovação, rejeição e notas do organizador na tela de análise de inscrições.
- Cancelamento pelo participante antes do início de uma atividade publicada e nova solicitação para inscrições canceladas, enquanto o prazo permitir.
- Lista de espera quando as vagas estão ocupadas, com oferta de vaga por ordem de solicitação e confirmação pelo participante.
- Notificações internas sobre inscrições e oferta de vagas, com marcação individual ou conjunta como lidas.
- Estados da inscrição: pendente, aprovada, rejeitada, lista de espera e cancelada.

### Pagamentos e presença

- Registro administrativo do valor, situação, método e data de pagamento.
- Registro administrativo de presença, horário de entrada e observações.
- Cada inscrição admite no máximo um pagamento e um registro de presença.
- O pagamento é um registro de controle; não há integração implementada com gateway de cobrança.

### Interface

- Bootstrap, layouts adaptáveis e regras CSS para telas menores.
- Alternância entre tema claro e escuro no site, com preferência armazenada no navegador.
- Menus conforme o usuário autenticado e seu perfil.

## Modelagem do banco de dados

| App | Entidades |
| --- | --- |
| `accounts` | `User` |
| `activities` | `Modality`, `Location`, `Activity` |
| `registrations` | `Registration`, `Payment`, `Attendance`, `Notification` |

Um usuário organiza atividades e realiza inscrições. Cada atividade pertence a uma modalidade e a um local. A inscrição relaciona participante e atividade, podendo ter pagamento, presença e várias notificações. Cada notificação tem um destinatário; a referência à inscrição pode ser nula.

[Consultar o diagrama entidade-relacionamento e as restrições](docs/der.md).

### Regras implementadas

- A combinação de atividade e participante é única no banco.
- O limite de vagas deve ser positivo e o valor da atividade não pode ser negativo.
- O término deve ser posterior ao início e o prazo de confirmação deve anteceder o início.
- Novas inscrições exigem atividade publicada, ainda não iniciada e com prazo de confirmação aberto.
- O organizador não pode se inscrever na própria atividade pelo fluxo do site.
- Inscrições pendentes, aprovadas e ofertas de vaga da lista de espera ocupam vagas no fluxo de inscrição.
- A aceitação de uma vaga da fila gera aprovação automática ou solicitação pendente, conforme o tipo da atividade.
- Organizadores consultam e gerenciam os registros das próprias atividades; o superusuário possui acesso geral.

## Ambiente administrativo

A rota `/admin/` exige autenticação, usuário ativo, acesso de equipe e perfil de organizador ou superusuário. O painel utiliza Jazzmin, identidade visual JogaJunto, ícones, CSS personalizado, seções nos formulários e controles de inscrições dentro da atividade.

As sete entidades principais (`User`, `Modality`, `Location`, `Activity`, `Registration`, `Payment` e `Attendance`) estão registradas no Admin. Notificações são consultadas nas telas do usuário.

| Cadastro | Filtros disponíveis |
| --- | --- |
| Usuários | Perfil, equipe, superusuário, grupos e ativo |
| Modalidades | Ativa |
| Locais | Estado e cidade |
| Atividades | Status, tipo de inscrição, modalidade, organizador, cidade, gratuito/pago e início |
| Inscrições | Status, data de solicitação, status da atividade e modalidade |
| Pagamentos | Status e método |
| Presenças | Presente |

Também existem buscas textuais e hierarquia de datas em atividades, inscrições e pagamentos.

## Estrutura do projeto

Estrutura resumida dos arquivos existentes; as rotas estão centralizadas em `config/urls.py`.

```text
JogaJunto/
├── accounts/
│   ├── management/commands/
│   │   ├── seed_demo.py
│   │   └── sync_access.py
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── permissions.py
│   ├── signals.py
│   ├── tests.py
│   └── views.py
├── activities/
│   ├── migrations/
│   ├── templates/widgets/date_time.html
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── registrations/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── context_processors.py
│   ├── models.py
│   ├── signals.py
│   ├── tests.py
│   ├── test_waitlist.py
│   ├── views.py
│   └── waitlist.py
├── config/
│   ├── admin_site.py
│   ├── admin_widgets.py
│   ├── settings.py
│   ├── test_admin_widgets.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── docs/der.md
├── static/css/
│   ├── admin.css
│   └── site.css
├── templates/
│   ├── activities/
│   │   └── dashboard.html
│   ├── admin/
│   ├── includes/
│   ├── registration/
│   ├── registrations/
│   ├── activity_form.html
│   ├── base.html
│   ├── home.html
│   └── notifications.html
├── manage.py
├── requirements.txt
└── README.md
```

## Instalação e execução local

Os comandos abaixo usam PowerShell e Python 3.13, utilizado no ambiente local do projeto. Não é necessário ativar o ambiente: o executável é chamado diretamente, inclusive para executar o pip.

```powershell
git clone https://github.com/i-am-Gab/JogaJunto.git
cd JogaJunto
py -3.13 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py sync_access
.\venv\Scripts\python.exe manage.py createsuperuser

No Linux/macOS, crie o ambiente com `python3.13 -m venv venv` e substitua `.\venv\Scripts\python.exe` por `./venv/bin/python` nos comandos seguintes.

- Site: <http://127.0.0.1:8000/>
- Admin: <http://127.0.0.1:8000/admin/>
- Login: <http://127.0.0.1:8000/login/>
- Cadastro: <http://127.0.0.1:8000/cadastro/>
- Minhas inscrições: <http://127.0.0.1:8000/minhas-inscricoes/>
- Dashboard do organizador: <http://127.0.0.1:8000/organizador/>
- Análise do organizador: <http://127.0.0.1:8000/organizador/inscricoes/>
- Notificações: <http://127.0.0.1:8000/notificacoes/>

Encerre o servidor com `Ctrl+C`. Nas execuções seguintes, basta entrar na pasta e executar `runserver` pelo Python do ambiente virtual. Não é necessário gerar novas migrations para instalar o projeto: as migrations existentes são aplicadas por `migrate`.

### Configuração e primeiros cadastros

O banco SQLite `db.sqlite3` é criado por `migrate`. Para cadastrar dados manualmente, siga os passos abaixo. Para carregar exemplos prontos, use o comando `seed_demo` descrito a seguir.

1. Entre no Admin com o superusuário criado.
2. Cadastre modalidades e locais (opcionalmente informando latitude e longitude para posicionamento exato no mapa).3. Crie usuários ou utilize o cadastro público. Para conceder acesso de organizador, edite o perfil do usuário pelo Admin com o superusuário.
4. Cadastre atividades e use uma conta de participante para testar inscrições.

A aplicação lê `SECRET_KEY` das variáveis de ambiente ou de um arquivo `.env` na pasta do projeto. Sem essa configuração, usa uma chave padrão de desenvolvimento. `DEBUG=True` e SQLite estão configurados para execução local. O fuso horário é `America/Sao_Paulo`.

Bootstrap, Chart.js e Google Maps utilizam recursos externos; mantenha conexão com a internet durante a demonstração para carregá-los corretamente.

### Dados de demonstração (`seed_demo`)

Depois de aplicar as migrations, execute na pasta do projeto:

```powershell
python manage.py seed_demo
```

O comando cria **9 usuários, 6 modalidades, 9 locais com coordenadas geográficas reais (em Lavras, Nepomuceno, Varginha, Perdões e Belo Horizonte), 14 atividades e inscrições variadas**, além de notificações. Modalidades, locais e atividades usam o prefixo `[DEMO]`.

| Conta | Perfil |
| --- | --- |
| `demo_admin` | Superusuário (acesso Admin e visão global no dashboard) |
| `demo_organizador` | Organizador Rafael |
| `demo_organizador2` | Organizadora Mariana |
| `demo_organizador3` | Organizador Lucas |
| `demo_organizador4` | Organizadora Camila |
| `demo_ana`, `demo_bruno`, `demo_carla`, `demo_diego` | Participantes |

A senha inicial das contas novas é **`JogaJuntoDemo!2026`**. Entre com o nome de usuário. Você pode escolher outra senha na primeira carga:

```powershell
python manage.py seed_demo --password "SuaSenhaDeDemonstracao!2026"
```

Os exemplos incluem atividades gratuitas e pagas, inscrição pendente, aprovada, rejeitada, cancelada e em lista de espera, atividade lotada com fila, vaga reservada aguardando confirmação, inscrição automática e por aprovação, além de atividade em rascunho. Entre com qualquer um dos 4 organizadores (`demo_organizador` a `demo_organizador4`) para visualizar seus respectivos gráficos e solicitações, ou com `demo_admin` para visualizar o gráfico agregado de toda a plataforma. Entre com `demo_diego` para testar a confirmação de vaga reservada, ou use `demo_ana` para cancelar a inscrição no futebol e liberar vaga para `demo_carla`..

As atividades abertas são criadas com datas futuras em relação à primeira execução, no fuso do projeto. A atividade finalizada usa datas passadas.

Repetir o comando preserva registros existentes, senhas, permissões, datas e situações. Ele não apaga dados, não redefine contas e não repõe inscrições de atividades já existentes, inclusive se foram removidas ou alteradas durante os testes. As datas dos exemplos existentes também não são deslocadas para o futuro. Não são geradas notificações duplicadas. Se um dos nomes de usuário já pertencer a uma conta com outro e-mail, a carga é interrompida sem gravar alterações.

Os cadastros são feitos em uma única transação. A carga não dispara as rotinas normais de sincronização de grupos ou redistribuição de vagas; as permissões das contas novas e as notificações dos exemplos são configuradas explicitamente.

### Verificações e testes

```powershell
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py test
```

Existem testes de cadastro, permissões, atividades, dashboard do organizador, inscrições, lista de espera e widgets administrativos. Para sincronizar novamente os grupos e permissões dos usuários existentes:

```powershell
.\venv\Scripts\python.exe manage.py sync_access
```

## Versionamento e checkpoints

Repositório: <https://github.com/i-am-Gab/JogaJunto>

As referências Git locais incluem `main`, `origin/develop` e `origin/feature`. A visibilidade pública, os colaboradores e a entrega do link no Campus Virtual devem ser conferidos no GitHub e no ambiente da disciplina.

Para o Checkpoint 1, o projeto possui models e migrations, diagrama relacional, Admin com Jazzmin, filtros, buscas, grupos de acesso e separação em três apps. Para a etapa final, já há autenticação, cadastro, áreas por perfil, dashboard do organizador com gráficos por modalidade, pré-visualização com Google Maps, filtros dinâmicos na página inicial, inscrições, lista de espera, notificações, interface Bootstrap e temas claro/escuro.
