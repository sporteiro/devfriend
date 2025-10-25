classDiagram
    %% Entidades del dominio principal
    class User {
        +id: String
        +email: String
        +passwordHash: String
        +createdAt: DateTime
        +updatedAt: DateTime
        +isActive: Boolean
        +login()
        +register()
        +updateProfile()
    }
    class Note {
        +id: String
        +title: String
        +content: String
        +userId: String
        +createdAt: DateTime
        +updatedAt: DateTime
        +isArchived: Boolean
        +save()
        +update()
        +delete()
        +search()
        +archive()
    }
    class Secret {
        +id: String
        +name: String
        +encryptedValue: String
        +serviceType: String
        +userId: String
        +createdAt: DateTime
        +updatedAt: DateTime
        +encrypt()
        +decrypt()
        +validate()
    }
    class Integration {
        +id: String
        +serviceType: String
        +secretId: String
        +userId: String
        +config: JSON
        +createdAt: DateTime
        +updatedAt: DateTime
        +isActive: Boolean
        +connect()
        +disconnect()
        +testConnection()
        +fetchData()
    }
    class APIToken {
        +token: String
        +expiresAt: DateTime
        +isValid: Boolean
        +refresh()
        +validate()
    }
    class OAuthConfig {
        +clientId: String
        +clientSecret: String
        +redirectUri: String
        +provider: String
        +getAuthUrl()
        +exchangeCode()
    }
    User "1" -- "*" Note : creates
    User "1" -- "*" Secret : owns
    User "1" -- "*" Integration : configures
    Secret "1" -- "*" Integration : providesCredentials
    User "1" -- "*" APIToken : has
    OAuthConfig "1" -- "*" Integration : configures

    %% Servicios y repositorios como interfaces y sus implementaciones
    class INoteService {
        <<interface>>
        +createNote()
        +getUserNotes()
        +updateNote()
        +deleteNote()
        +searchNotes()
        +archiveNote()
    }
    class NoteService
    INoteService <|.. NoteService

    class IIntegrationService {
        <<interface>>
        +createIntegration()
        +testIntegration()
        +deleteIntegration()
        +getIntegrationData()
    }
    class IntegrationService
    IIntegrationService <|.. IntegrationService

    class ISecretService {
        <<interface>>
        +encryptSecret()
        +decryptSecret()
        +validateSecret()
        +rotateSecrets()
    }
    class SecretService
    ISecretService <|.. SecretService

    class IAuthService {
        <<interface>>
        +registerUser()
        +loginUser()
        +logoutUser()
        +validateToken()
        +oauthLogin()
    }
    class AuthService
    IAuthService <|.. AuthService

    class IUserRepository {
        <<interface>>
        +findById()
        +findByEmail()
        +save()
        +update()
    }
    class UserRepository
    IUserRepository <|.. UserRepository

    class INoteRepository {
        <<interface>>
        +findById()
        +findByUser()
        +save()
        +update()
        +delete()
        +searchByContent()
    }
    class NoteRepository
    INoteRepository <|.. NoteRepository

    class ISecretRepository {
        <<interface>>
        +findById()
        +findByUser()
        +save()
        +update()
        +delete()
    }
    class SecretRepository
    ISecretRepository <|.. SecretRepository

    class IIntegrationRepository {
        <<interface>>
        +findById()
        +findByUser()
        +findByService()
        +save()
        +update()
        +delete()
    }
    class IntegrationRepository
    IIntegrationRepository <|.. IntegrationRepository

    %% Relaciones de uso (dependencias)
    NoteService --> INoteRepository
    IntegrationService --> IIntegrationRepository
    SecretService --> ISecretRepository
    AuthService --> IUserRepository
    IntegrationService --> ISecretService
