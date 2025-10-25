graph TD
    subgraph "🖥️ Frontend - Vue.js"
        A1[📊 UI Components]
        A2[🔗 HTTP Client]
    end

    subgraph "⚙️ Backend - FastAPI"
        B1[🎮 REST API Controllers]
        B2[🔐 Auth Endpoints]
    end

    A2 -- "API Calls" --> B1
    B1 -- "uses" --> B2
    B1 -- "behind" --> F5
    B1 -- "connects to" --> F1
    B2 -- "uses" --> F4

    subgraph "🟥 Infraestructura & External Services"
        F1[💾 Database]
        F2[🗝️ Security Secrets]
        F3[🔑 Database Credentials]
        F4[🌐 External Auth API]
        F5[🚪 API Gateway]
    end

    %% Styling
    classDef frontend fill:#e1f5fe
    classDef backend fill:#bbdefb
    classDef infrastructure fill:#ffcdd2

    class A1,A2 frontend
    class B1,B2 backend
    class F1,F2,F3,F4,F5 infrastructure
