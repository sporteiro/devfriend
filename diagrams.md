# Diagramas DevFriend

## 1. Diagrama de Clases (Backend)

```mermaid
classDiagram
    class Note {
        +Optional~int~ id
        +str title
        +str content
        +Optional~datetime~ created_at
        +update_content(new_content: str) None
    }

    class NoteRepository {
        <<interface>>
        +save(note: Note) Note
        +find_all() List~Note~
        +find_by_id(note_id: int) Optional~Note~
        +delete(note_id: int) bool
    }

    class SQLiteNoteRepository {
        -str db_path
        -_get_connection() Connection
        -_create_table() None
        +save(note: Note) Note
        +find_all() List~Note~
        +find_by_id(note_id: int) Optional~Note~
        +delete(note_id: int) bool
    }

    class NoteService {
        -NoteRepository note_repository
        +__init__(note_repository: NoteRepository)
        +create_note(title: str, content: str) Note
        +get_all_notes() List~Note~
        +get_note_by_id(note_id: int) Optional~Note~
        +update_note(note_id: int, title: str, content: str) Optional~Note~
        +delete_note(note_id: int) bool
    }

    class NoteController {
        +note_service: NoteService
        +get_notes() List~Note~
        +create_note(note: Note) Note
        +get_note(note_id: int) Note
        +update_note(note_id: int, note: Note) Note
        +delete_note(note_id: int) dict
    }

    NoteRepository <|.. SQLiteNoteRepository : implements
    NoteService --> NoteRepository : uses
    NoteService --> Note : manages
    SQLiteNoteRepository --> Note : persists
    NoteController --> NoteService : uses
    NoteController --> Note : handles
```

## 2. Diagrama de Base de Datos

```mermaid
erDiagram
    NOTES {
        INTEGER id PK "PRIMARY KEY AUTOINCREMENT"
        TEXT title "NOT NULL"
        TEXT content
        DATETIME created_at "DEFAULT CURRENT_TIMESTAMP"
    }
```

## 3. Diagrama de Arquitectura Hexagonal

```mermaid
graph TB
    subgraph "Frontend - Vue.js"
        UI[UI Components]
        NoteForm[NoteForm.vue]
        NoteList[NoteList.vue]
        AppVue[App.vue]
        NoteServiceJS[noteService.js<br/>Adaptador HTTP]
    end

    subgraph "Backend - FastAPI"
        subgraph "Adaptadores Primarios<br/>(Driving/Input)"
            API[note_controller.py<br/>REST API Controller]
        end

        subgraph "Núcleo - Aplicación"
            Service[NoteService<br/>Casos de Uso]
        end

        subgraph "Núcleo - Dominio"
            Domain[Note<br/>Entidad de Dominio]
        end

        subgraph "Puertos"
            Port[NoteRepository<br/>Interface/Puerto]
        end

        subgraph "Adaptadores Secundarios<br/>(Driven/Output)"
            SQLiteAdapter[SQLiteNoteRepository<br/>Adaptador SQLite]
        end

        subgraph "Infraestructura"
            DB[(SQLite DB<br/>devfriend.db)]
        end
    end

    UI --> NoteForm
    UI --> NoteList
    NoteForm --> AppVue
    NoteList --> AppVue
    AppVue --> NoteServiceJS
    NoteServiceJS -->|HTTP REST| API
    API --> Service
    Service --> Domain
    Service --> Port
    Port <-.implements.-> SQLiteAdapter
    SQLiteAdapter --> DB

    style Domain fill:#90EE90
    style Port fill:#FFD700
    style Service fill:#87CEEB
    style API fill:#FFA07A
    style SQLiteAdapter fill:#FFA07A
    style DB fill:#DDA0DD
    style NoteServiceJS fill:#FFA07A
```

## 4. Diagrama de Flujo - Crear Nota

```mermaid
sequenceDiagram
    participant User as Usuario
    participant Form as NoteForm.vue
    participant App as App.vue
    participant HTTP as noteService.js
    participant API as note_controller
    participant Service as NoteService
    participant Repo as SQLiteNoteRepository
    participant DB as SQLite DB

    User->>Form: Escribe contenido
    User->>Form: Click "Guardar"
    Form->>App: emit('submit', content)
    App->>HTTP: createNote(content)
    HTTP->>API: POST /notes {title, content}
    API->>Service: create_note(title, content)
    Service->>Service: new Note(title, content)
    Service->>Repo: save(note)
    Repo->>DB: INSERT INTO notes
    DB-->>Repo: note con id
    Repo-->>Service: note guardada
    Service-->>API: note
    API-->>HTTP: JSON response
    HTTP-->>App: note
    App->>HTTP: getAllNotes()
    HTTP->>API: GET /notes
    API->>Service: get_all_notes()
    Service->>Repo: find_all()
    Repo->>DB: SELECT * FROM notes
    DB-->>Repo: rows
    Repo-->>Service: List[Note]
    Service-->>API: List[Note]
    API-->>HTTP: JSON response
    HTTP-->>App: notes[]
    App-->>Form: Limpia textarea
    App->>User: Muestra notas actualizadas
```

## 5. Capas de la Arquitectura Hexagonal

```mermaid
graph LR
    subgraph "Capa de Presentación"
        A[Vue Components]
    end

    subgraph "Adaptadores de Entrada"
        B[REST API Controller]
    end

    subgraph "Capa de Aplicación"
        C[NoteService<br/>Casos de Uso]
    end

    subgraph "Capa de Dominio"
        D[Note Entity<br/>Lógica de Negocio]
    end

    subgraph "Puertos"
        E[NoteRepository<br/>Interface]
    end

    subgraph "Adaptadores de Salida"
        F[SQLiteNoteRepository<br/>Implementación]
    end

    subgraph "Infraestructura"
        G[SQLite Database]
    end

    A -->|HTTP| B
    B --> C
    C --> D
    C --> E
    E -.->|implements| F
    F --> G

    style D fill:#90EE90
    style E fill:#FFD700
    style C fill:#87CEEB
    style B fill:#FFA07A
    style F fill:#FFA07A
```

---

## Notas sobre la Arquitectura

### Arquitectura Hexagonal (Puertos y Adaptadores)

**Núcleo (Core):**
- **Dominio**: `Note` - Entidad con lógica de negocio
- **Aplicación**: `NoteService` - Casos de uso y orquestación

**Puertos:**
- `NoteRepository` - Interface que define el contrato de persistencia

**Adaptadores Primarios (Driving/Input):**
- `note_controller.py` - Adaptador REST API que recibe peticiones HTTP

**Adaptadores Secundarios (Driven/Output):**
- `SQLiteNoteRepository` - Implementación concreta de persistencia en SQLite
- `noteService.js` - Adaptador HTTP en el frontend

### Beneficios de esta arquitectura:

1. **Independencia del framework**: El core no depende de FastAPI
2. **Testabilidad**: Se puede testear el core sin infraestructura
3. **Flexibilidad**: Fácil cambiar SQLite por PostgreSQL, MongoDB, etc.
4. **Separación de responsabilidades**: Cada capa tiene un propósito claro
5. **Inversión de dependencias**: El core define las interfaces, no la infraestructura

---

## Nuevo diagrama para la memoria:

```mermaid
graph TD
    A[🖥️ Frontend (Vue.js 3 SPA)] -- REST API --> B[⚙️ Backend (FastAPI)]
    B -- SQL --> C[💾 Base de datos (PostgreSQL)]
    B -- Secrets API / OAuth --> D[🔐 External Services (Secrets, Auth APIs, Integrations)]

    subgraph Infraestructura
        C
        D
    end

    %% Estilos para claridad
    classDef frontend fill:#e1f5fe
    classDef backend fill:#bbdefb
    classDef infrastructure fill:#ffcdd2
    class A frontend
    class B backend
    class C,D infrastructure
```

---

# Otros diagramas (de clases, de base de datos, etc.) van debajo...
