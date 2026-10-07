# JogaJunto

Aplicação web desenvolvida com **Django** para criação, divulgação e gerenciamento de atividades físicas coletivas, como corrida, caminhada, ciclismo, futebol, entre outras.

O sistema permite que organizadores cadastrem atividades e controlem inscrições, enquanto participantes podem consultar atividades disponíveis, solicitar participação e acompanhar o status de suas inscrições.

## 👥 Integrantes

- **Gabriel Aguiar Alves e Silva**
- **Ronan Gustavo Carleto**
- **Marco Antonio Maia**

## 🛠️ Tecnologias Utilizadas

<p align="center">
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/python/python-original.svg" alt="Python" title="Python" width="50" height="50" />
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/django/django-plain.svg" alt="Django" title="Django" width="50" height="50" />
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/html5/html5-original.svg" alt="HTML5" title="HTML5" width="50" height="50" />
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/css3/css3-original.svg" alt="CSS3" title="CSS3" width="50" height="50" />
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/javascript/javascript-original.svg" alt="JavaScript" title="JavaScript" width="50" height="50" />
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/bootstrap/bootstrap-original.svg" alt="Bootstrap" title="Bootstrap" width="50" height="50" />
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/sqlite/sqlite-original.svg" alt="SQLite" title="SQLite" width="50" height="50" />
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/git/git-original.svg" alt="Git" title="Git" width="50" height="50" />
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/github/github-original.svg" alt="GitHub" title="GitHub" width="50" height="50" />
</p>

<p align="center">
  <strong>Python • Django • HTML5 • CSS3 • JavaScript • Bootstrap • SQLite • Git • GitHub</strong>
</p>

## 📌 Sobre o Projeto

O projeto tem como objetivo facilitar a organização de atividades físicas em grupo, centralizando em um único ambiente informações sobre eventos, inscrições, participantes, pagamentos e presença.

Cada atividade poderá possuir informações como:

- modalidade;
- local;
- data e horário de início e término;
- limite de participantes;
- valor da atividade;
- prazo para confirmação;
- tipo de inscrição;
- status da atividade.

As inscrições poderão ocorrer de forma **automática** ou **mediante aprovação do organizador**.

Quando necessário, o sistema também permitirá o registro de pagamentos e o controle de presença dos participantes.

## ⚙️ Principais Funcionalidades

### Usuários

- Cadastro e autenticação de usuários;
- Perfis de participante e organizador;
- Controle de acesso de acordo com o tipo de usuário;
- Área administrativa protegida.

### Atividades

- Cadastro de atividades físicas;
- Consulta, edição e exclusão de atividades;
- Associação de modalidade e local;
- Definição de data e horário;
- Definição do limite de participantes;
- Atividades gratuitas ou pagas;
- Prazo para confirmação;
- Inscrição automática ou mediante aprovação;
- Controle do status da atividade.

### Inscrições

- Solicitação de participação em atividades;
- Aprovação ou rejeição de inscrições;
- Lista de espera;
- Cancelamento de inscrição;
- Acompanhamento do status pelo participante;
- Impedimento de inscrições duplicadas na mesma atividade.

### Pagamentos

- Registro de pagamento para atividades pagas;
- Controle do status do pagamento;
- Registro da forma de pagamento;
- Registro da data de pagamento.

### Presença

- Registro de presença do participante;
- Data e horário de check-in;
- Observações relacionadas à participação.

## 🗃️ Modelagem do Banco de Dados

O sistema utiliza um banco de dados relacional composto pelas seguintes entidades principais:

- `User`;
- `Modality`;
- `Location`;
- `Activity`;
- `Registration`;
- `Payment`;
- `Attendance`.

Os principais relacionamentos são:

- um usuário pode organizar várias atividades;
- um usuário pode possuir várias inscrições;
- uma modalidade pode estar associada a várias atividades;
- um local pode receber várias atividades;
- uma atividade pode possuir várias inscrições;
- uma inscrição pode possuir um pagamento;
- uma inscrição pode possuir um registro de presença.

📊 [Visualizar o Diagrama Entidade-Relacionamento](docs/der.md)

## 🧩 Organização dos Apps Django

O projeto está dividido em três aplicações principais:

```
accounts/
activities/
registrations/
```

### `accounts`

Responsável pelo gerenciamento dos usuários e autenticação.

Principais models:

```
User
```

### `activities`

Responsável pelo cadastro e gerenciamento das atividades físicas.

Principais models:

```
Modality
Location
Activity
```

### `registrations`

Responsável pelas inscrições, pagamentos e controle de presença.

Principais models:

```
Registration
Payment
Attendance
```

## 📁 Estrutura do Projeto

A estrutura prevista para o projeto é:

```
.
├── accounts/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── activities/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── registrations/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── docs/
│   └── der.md
│
├── static/
│   ├── css/
│   ├── js/
│   └── img/
│
├── templates/
│
├── manage.py
├── requirements.txt
└── README.md
```

A estrutura poderá sofrer alterações durante o desenvolvimento da aplicação.

## 🔐 Ambiente Administrativo

O projeto possui um ambiente administrativo protegido por autenticação.

O Django Admin será personalizado com um tema administrativo e terá recursos como:

- filtros por status;
- filtros por modalidade;
- filtros por tipo de inscrição;
- filtros por data;
- busca por atividade;
- busca por participante;
- busca por organizador;
- hierarquia de datas;
- gerenciamento de usuários;
- gerenciamento de atividades;
- gerenciamento de inscrições;
- gerenciamento de pagamentos;
- gerenciamento de presença.

## 🌿 Organização do Repositório

O desenvolvimento utiliza Git e GitHub.

As principais branches do projeto são:

```
main
develop
feature
```

Durante o desenvolvimento também poderão ser utilizadas branches específicas, por exemplo:

```
feature/database-models
feature/admin
feature/authentication
feature/activities
feature/registrations
feature/frontend
```

### Fluxo de desenvolvimento

```
feature/*
    ↓
develop
    ↓
main
```

A branch `main` deverá conter versões estáveis do projeto.

A branch `develop` será utilizada para integração das funcionalidades em desenvolvimento.

As branches `feature/*` serão utilizadas para implementação isolada de funcionalidades.

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone [URL_DO_REPOSITORIO]
```

Entre na pasta do projeto:

```bash
cd [NOME_DA_PASTA]
```

### 2. Crie um ambiente virtual

No Windows:

```bash
python -m venv venv
```

Ative o ambiente virtual:

```bash
venv\Scripts\activate
```

No Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute as migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Crie um superusuário

```bash
python manage.py createsuperuser
```

### 6. Execute o servidor

```bash
python manage.py runserver
```

A aplicação estará disponível, por padrão, em:

```
http://127.0.0.1:8000/
```

O ambiente administrativo estará disponível em:

```
http://127.0.0.1:8000/admin/
```

## 🧪 Estado Atual do Desenvolvimento

### Checkpoint 1

- [ ]  Estrutura inicial do projeto Django;
- [ ]  Apps `accounts`, `activities` e `registrations`;
- [ ]  Modelagem completa do banco de dados;
- [ ]  Models implementados;
- [ ]  Migrations criadas e aplicadas;
- [ ]  Diagrama Entidade-Relacionamento;
- [ ]  Ambiente administrativo configurado;
- [ ]  Tema personalizado no Django Admin;
- [ ]  Filtros e mecanismos de busca no Admin;
- [ ]  Repositório público organizado no GitHub;
- [ ]  Branches `main`, `develop` e `feature`.

### Checkpoint 2

- [ ]  Login;
- [ ]  Logout;
- [ ]  Cadastro de usuários;
- [ ]  Área do participante;
- [ ]  Área do organizador;
- [ ]  CRUD das principais entidades;
- [ ]  Interface responsiva;
- [ ]  Tema claro;
- [ ]  Tema escuro;
- [ ]  Integração completa com o banco de dados;
- [ ]  Finalização da documentação.

## 📋 Regras de Negócio

Algumas das principais regras previstas para o sistema são:

1. Um usuário não poderá possuir duas inscrições para a mesma atividade.
2. O limite de participantes de uma atividade deverá ser maior que zero.
3. O valor de uma atividade não poderá ser negativo.
4. O horário de término deverá ser posterior ao horário de início.
5. O prazo de confirmação deverá ocorrer antes do início da atividade.
6. Atividades poderão possuir inscrição automática ou mediante aprovação.
7. Inscrições sujeitas à aprovação poderão assumir os estados pendente, aprovada, rejeitada, cancelada ou lista de espera.
8. Pagamentos serão associados apenas às inscrições que necessitarem desse controle.
9. O organizador será responsável pelo gerenciamento das inscrições de suas atividades.
10. Cada inscrição poderá possuir no máximo um registro de pagamento e um registro de presença.

---

## 📄 Licença

Projeto acadêmico desenvolvido para a disciplina **GAC116 - Programação Web**.

Universidade Federal de Lavras — UFLA.
