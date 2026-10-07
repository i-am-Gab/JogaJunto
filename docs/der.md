# Diagrama Entidade-Relacionamento

Este diagrama representa a modelagem relacional do sistema de gerenciamento de atividades físicas coletivas.

```mermaid
erDiagram

    USER ||--o{ ACTIVITY : organizes
    USER ||--o{ REGISTRATION : makes

    MODALITY ||--o{ ACTIVITY : classifies
    LOCATION ||--o{ ACTIVITY : hosts

    ACTIVITY ||--o{ REGISTRATION : receives

    REGISTRATION ||--o| PAYMENT : generates
    REGISTRATION ||--o| ATTENDANCE : records

    USER {
        bigint id PK
        varchar username
        varchar email UK
        varchar password
        varchar first_name
        varchar last_name
        varchar phone
        varchar role
        boolean is_active
        boolean is_staff
        datetime date_joined
    }

    MODALITY {
        bigint id PK
        varchar name UK
        text description
        boolean is_active
    }

    LOCATION {
        bigint id PK
        varchar name
        varchar street
        varchar number
        varchar neighborhood
        varchar city
        varchar state
        varchar zip_code
        varchar complement
        varchar reference_point
    }

    ACTIVITY {
        bigint id PK
        bigint organizer_id FK
        bigint modality_id FK
        bigint location_id FK
        varchar title
        text description
        datetime starts_at
        datetime ends_at
        int max_participants
        decimal price
        datetime confirmation_deadline
        varchar registration_type
        varchar status
        datetime created_at
        datetime updated_at
    }

    REGISTRATION {
        bigint id PK
        bigint activity_id FK
        bigint participant_id FK
        varchar status
        datetime requested_at
        datetime decided_at
        datetime confirmed_at
        datetime cancelled_at
        text organizer_notes
    }

    PAYMENT {
        bigint id PK
        bigint registration_id FK
        decimal amount
        varchar status
        varchar method
        datetime paid_at
        datetime created_at
    }

    ATTENDANCE {
        bigint id PK
        bigint registration_id FK
        boolean attended
        datetime check_in_at
        text notes
    }
```

## Relacionamentos principais

- Um usuário pode organizar várias atividades.
- Um usuário pode possuir várias inscrições.
- Uma modalidade pode estar associada a várias atividades.
- Um local pode receber várias atividades.
- Uma atividade pode possuir várias inscrições.
- Uma inscrição pode possuir no máximo um pagamento.
- Uma inscrição pode possuir no máximo um registro de presença.

## Restrições principais

- Um participante não pode possuir mais de uma inscrição para a mesma atividade.
- O limite de participantes deve ser maior que zero.
- O valor da atividade não pode ser negativo.
- O horário de término deve ser posterior ao horário de início.
- O prazo de confirmação deve ocorrer antes do início da atividade.