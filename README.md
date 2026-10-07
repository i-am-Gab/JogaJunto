# JogaJunto
Sistema web para criação, divulgação e gerenciamento de atividades físicas coletivas. Permite cadastrar modalidades, definir data, horário, local, limite de participantes, valor e tipo de inscrição. Usuários podem visualizar atividades, solicitar participação e acompanhar o status de suas inscrições.

<script src="https://mermaid.live/embed.js" async></script>
<mermaid-embed src="https://mermaid.live/embed?theme=default&look=classic&mode=light" height="480">
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
        bigint registration_id FK,UK
        decimal amount
        varchar status
        varchar method
        datetime paid_at
        datetime created_at
    }

    ATTENDANCE {
        bigint id PK
        bigint registration_id FK,UK
        boolean attended
        datetime check_in_at
        text notes
    }
</mermaid-embed>
