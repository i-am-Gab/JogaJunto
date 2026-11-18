# Usuários para testes — JogaJunto

Contas de demonstração criadas pelo comando `seed_demo`. Entre usando o **nome de usuário**, não o e-mail.

## Senha inicial

A senha inicial padrão das nove contas de demonstração é **`JogaJuntoDemo!2026`**.

## Logins e cenários

| Nome | Usuário | Perfil | O que testar |
| --- | --- | --- | --- |
| Admin | `demo_admin` | Superusuário | Gerenciar usuários e perfis, acessar todos os registros do Admin e visualizar o dashboard global. |
| Rafael | `demo_organizador` | Organizador | Aprovar a corrida, aumentar vagas e aprovar a fila do futebol; editar pagamentos e presenças do Futebol concluído. |
| Mariana | `demo_organizador2` | Organizadora | Gerenciar caminhada com vaga reservada, pedal e beach tennis. |
| Lucas | `demo_organizador3` | Organizador | Gerenciar society, vôlei e treino de corrida. |
| Camila | `demo_organizador4` | Organizadora | Gerenciar torneio de areia, caminhada, corrida e atividade em rascunho. |
| Ana | `demo_ana` | Participante | Acompanhar a aprovação na corrida, cancelar a inscrição no futebol e consultar notificações. |
| Bruno | `demo_bruno` | Participante | Consultar inscrições e notificações. Seu registro no Futebol concluído possui pagamento pendente e presença desmarcada na carga inicial. |
| Carla | `demo_carla` | Participante | Testar a lista de espera do futebol, receber a reserva e acompanhar a aprovação. Fazer nova inscrição no Longão 10K. |
| Diego | `demo_diego` | Participante | Confirmar a vaga reservada na caminhada e acompanhar inscrições e notificações. |

Os cenários da tabela correspondem à carga inicial. Alterações feitas nos ensaios são preservadas; confira o estado de cada inscrição antes de repetir.

## Onde entrar

- [Login do site](http://127.0.0.1:8000/login/): todas as contas.
- [Solicitações de inscrição](http://127.0.0.1:8000/organizador/inscricoes/): organizadores e superusuário.
- [Admin](http://127.0.0.1:8000/admin/): organizadores e superusuário, conforme suas permissões.
- [Pagamentos](http://127.0.0.1:8000/admin/registrations/payment/) e [presenças](http://127.0.0.1:8000/admin/registrations/attendance/): entre como Rafael e pesquise **Futebol concluído**.

Os participantes acessam suas inscrições e notificações pelo site, sem acesso ao Admin.

## Preparar as contas

Na pasta do projeto, com as dependências instaladas:

```powershell
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py seed_demo
.\venv\Scripts\python.exe manage.py runserver
```

A senha acima vale para contas criadas com a configuração padrão de `seed_demo`. Se a carga inicial usou `--password`, utilize a senha escolhida naquela execução. Senhas alteradas posteriormente também continuam valendo: repetir a carga preserva as senhas das contas existentes.

Para testar participante e organizador ao mesmo tempo, use uma janela normal e uma privada ou perfis distintos de navegador. Abas e janelas normais do mesmo perfil compartilham a sessão.

[Consultar o roteiro da apresentação do C2](roteiro_c2.md).
