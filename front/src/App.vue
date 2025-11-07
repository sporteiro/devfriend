<template>
  <div :class="['app-container', { dark: isDarkMode }]">
    <!-- Botón móvil para abrir/cerrar sidebar -->
    <button
      class="menu-toggle"
      @click="sidebarOpen = !sidebarOpen"
      :aria-label="sidebarOpen ? 'Close menu' : 'Open menu'"
      aria-expanded="sidebarOpen"
    >
      ☰
    </button>

    <AppSidebar
      :sidebarOpen="sidebarOpen"
      :isDarkMode="isDarkMode"
      :currentSection="currentSection"
      :user="user"
      @update:isDarkMode="toggleDarkMode"
      @navigate="navigateToSection"
      @show-login="showLogin"
      @logout="logout"
    />

    <!-- Contenido principal -->
    <main class="content">
      <!-- Header con título y modo oscuro -->
      <div class="content-header">
        <h1 v-if="currentSection === 'notes'">Notes</h1>
        <h1 v-else-if="currentSection === 'emailmodal'">Email</h1>
        <h1 v-else-if="currentSection === 'repository'">Repository</h1>
        <h1 v-else-if="currentSection === 'messages'">Messages</h1>
        <h1 v-else-if="currentSection === 'credentials'">Credentials</h1>

        <button
          @click="toggleDarkMode(!isDarkMode)"
          class="dark-mode-toggle"
          :aria-label="isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'"
          :title="isDarkMode ? 'Light mode' : 'Dark mode'"
        >
          <img
            src="@/assets/darkmode.png"
            alt="Toggle dark mode"
            class="darkmode-icon"
          />
        </button>
      </div>

      <!-- Sección Notes -->
      <div v-if="currentSection === 'notes'">

        <div class="search-container">
          <label for="search-input" class="sr-only">Search in notes</label>
          <input
            id="search-input"
            v-model="searchTerm"
            type="text"
            placeholder="Search in notes..."
            class="search-input"
            aria-describedby="search-results"
          />
          <span v-if="searchTerm" id="search-results" class="search-results" role="status" aria-live="polite">
            {{ filteredNotes.length }} result(s) found
          </span>
          <button
            @click="exportNotes"
            class="export-btn"
            title="Export notes"
            aria-label="Export all notes to JSON file"
          >
            Export
          </button>
          <input type="file" id="import-input" ref="importInput" accept="application/json"
              @change="handleImportNotes"
              style="display: none;"
          />
          <button
            @click="$refs.importInput.click()"
            class="export-btn"
            style="margin-left: 0;"
            title="Import notes from JSON file"
            aria-label="Import notes"
          >
            Import
          </button>
        </div>

        <NoteForm
          :editingNote="editingNote"
          @submit="createNote"
          @update-note="updateNote"
          @cancel-edit="cancelEdit"
        />

        <NoteList
          :notes="filteredNotes"
          :loading="loading"
          :error="error"
          @edit-note="editNote"
          @delete-note="deleteNote"
          role="region"
          aria-label="Lista de notas"
        />
      </div>

      <!-- Sección Email -->
      <!--
      <div v-else-if="currentSection === 'email'">
        <div class="section-placeholder">
          <p>Gmail Integration</p>
          <div class="mock-content">
            <div class="mock-item notification-item">
              <span class="notification-count">3</span>
              <span>unread emails</span>
            </div>
            <div class="mock-item">
              <span>Latest: Meeting tomorrow 10:00</span>
            </div>
            <div class="mock-item">
              <span>New: Delivery reminder</span>
            </div>
          </div>
        </div>
      </div>
      -->

      <div v-else-if="currentSection === 'emailmodal'">
        <EmailModal />
      </div>


      <!-- Sección Repository -->
      <div v-else-if="currentSection === 'repository'">
        <div class="section-placeholder">
          <p>GitHub Integration</p>
          <div class="mock-content">
            <div class="mock-item">
              <span>5 active repositories</span>
            </div>
            <div class="mock-item">
              <span>Last push: 2 hours ago</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Sección Messages -->
      <div v-else-if="currentSection === 'messages'">
        <div class="section-placeholder">
          <p>Slack Integration</p>
          <div class="mock-content">
            <div class="mock-item notification-item">
              <span class="notification-count">12</span>
              <span>unread messages</span>
            </div>
            <div class="mock-item">
              <span>Channel: #development (5 new)</span>
            </div>
            <div class="mock-item">
              <span>Channel: #general (7 new)</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Sección Credentials -->
      <div v-else-if="currentSection === 'credentials'">
        <CredentialsList />
      </div>
    </main>

    <!-- Modal de autenticación -->
    <AuthModal
      :show="showAuthModal"
      @close="hideAuthModal"
      @success="onAuthSuccess"
    />
  </div>
</template>

<script>
import AppSidebar from "./components/AppSidebar.vue";
import NoteForm from "./components/NoteForm.vue";
import NoteList from "./components/NoteList.vue";
import AuthModal from "./components/AuthModal.vue";
import CredentialsList from "./components/CredentialsList.vue";
import EmailModal from "./components/EmailModal.vue";
import { noteService } from "./services/noteService.js";
import "./App.css";

export default {
  name: "App",
  components: {
    AppSidebar,
    NoteForm,
    NoteList,
    AuthModal,
    CredentialsList,
    EmailModal,
  },
  data() {
    return {
      notes: [],
      loading: false,
      error: null,
      isDarkMode: false,
      sidebarOpen: false,
      editingNote: null,
      searchTerm: '',
      currentSection: 'notes',
      showAuthModal: false,
      user: null,
    };
  },
  mounted() {
    const saved = localStorage.getItem("darkMode");
    this.isDarkMode = saved === "true";
    this.checkAuth();
    this.loadNotes();
    this.handleOAuthCallback();
  },
  methods: {
    toggleDarkMode(value) {
      this.isDarkMode = value;
      localStorage.setItem("darkMode", value);
    },
    async loadNotes() {
      this.loading = true;
      this.error = null;
      try {
        this.notes = await noteService.getAllNotes();
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },
    async createNote(content) {
      this.error = null;
      try {
        const title = this.extractTitle(content);
        const newNote = await noteService.createNote(title, content);
        this.notes.unshift(newNote);
      } catch (error) {
        this.error = error.message;
      }
    },
    extractTitle(content) {
      const lines = content.split('\n');
      const firstLine = lines[0] || 'Untitled';
      return firstLine.replace(/^#+ /, '').substring(0, 100);
    },
    editNote(note) {
      this.editingNote = note;
    },
    async updateNote(updatedNote) {
      this.error = null;
      try {
        const title = this.extractTitle(updatedNote.content);
        const updated = await noteService.updateNote(
          updatedNote.id,
          title,
          updatedNote.content
        );
        const index = this.notes.findIndex((n) => n.id === updatedNote.id);
        if (index !== -1) {
          this.notes[index] = updated;
        }
        this.editingNote = null;
      } catch (error) {
        this.error = error.message;
      }
    },
    async deleteNote(note) {
      this.error = null;
      try {
        await noteService.deleteNote(note.id);
        this.notes = this.notes.filter(n => n.id !== note.id);
      } catch (error) {
        this.error = error.message;
      }
    },
    cancelEdit() {
      this.editingNote = null;
    },
    navigateToSection(section) {
      this.currentSection = section;
      this.sidebarOpen = false; // Cerrar sidebar en móvil
    },
    async exportNotes() {
      try {
        const exportData = await noteService.exportNotes();
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `devfriend-notes-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } catch (error) {
        this.error = 'Error exporting notes';
      }
    },
    async handleImportNotes(event) {
      const file = event.target.files && event.target.files[0];
      if (!file) return;
      try {
        const text = await file.text();
        const importData = JSON.parse(text);
        if (!importData.notes || !Array.isArray(importData.notes)) {
          this.$toast.error('Invalid import file: missing notes array');
          return;
        }
        const existingNotes = await this.notes;
        const existingContents = new Set(existingNotes.map(n => n.content));
        let imported = 0;
        let duplicate = 0;
        for (const note of importData.notes) {
          if (note.content && !existingContents.has(note.content)) {
            try {
              await this.createNote(note.content);
              imported++;
            } catch (e) {
              // ignorar notas individuales que fallen
            }
          } else {
            duplicate++;
          }
        }
        if(imported > 0) {
          this.$toast.success(`${imported} notes imported${duplicate > 0 ? ", " + duplicate + " duplicates skipped" : ''}`);
        } else {
          this.$toast.info('No new notes were imported (all duplicates)');
        }
        this.loadNotes(); // refresca
      } catch (err) {
        this.$toast.error('Error importing notes: ' + err.message);
      } finally {
        event.target.value = '';
      }
    },
    async checkAuth() {
      const { authService } = await import('./services/authService');
      const userData = localStorage.getItem('devfriend_user');
      if (userData) {
        this.user = JSON.parse(userData);
      }
      if (authService.isAuthenticated()) {
        await this.loadNotes();
      }
    },
    showLogin() {
      this.showAuthModal = true;
    },
    hideAuthModal() {
      this.showAuthModal = false;
    },
    async onAuthSuccess() {
      await this.checkAuth();
      await this.loadNotes();
      this.hideAuthModal();
    },
    async logout() {
      const { authService } = await import('./services/authService');
      authService.logout();
      localStorage.removeItem('devfriend_user');
      this.user = null;
      this.notes = [];
      await this.loadNotes();
    },
    async loginWithGoogle() {
      try {
        const API_URL = process.env.VUE_APP_API_URL || 'http://localhost:8888';
        const axios = (await import('axios')).default;

        const response = await axios.get(`${API_URL}/auth/google/login`);
        const authUrl = response.data?.auth_url;

        if (authUrl) {
          window.location.href = authUrl;
        } else {
          throw new Error('No auth URL received');
        }
      } catch (error) {
        console.error('Error initiating Google login:', error);
        this.$toast.error('Failed to start Google login');
      }
    },
    async handleOAuthCallback() {
      // Handle OAuth login callback
      const urlParams = new URLSearchParams(window.location.search);
      const oauthLoginSuccess = urlParams.get('oauth_login_success');
      const oauthSuccess = urlParams.get('oauth_success');
      const token = urlParams.get('token');

      // Handle Google login OAuth callback
      if (oauthLoginSuccess === 'true' && token) {
        // Save token first
        localStorage.setItem('devfriend_token', token);

        // Get user info using authService (same way as native login)
        try {
          const { authService } = await import('./services/authService');
          const user = await authService.getCurrentUser();

          if (user) {
            localStorage.setItem(
              'devfriend_user',
              JSON.stringify({
                name: user.email.split('@')[0],
                email: user.email,
                loginTime: new Date().toISOString(),
              })
            );
            this.user = {
              name: user.email.split('@')[0],
              email: user.email,
              loginTime: new Date().toISOString(),
            };

            // Clean URL
            window.history.replaceState({}, document.title, window.location.pathname);

            this.$toast.success('Logged in with Google successfully!');

            // Reload everything to update state
            await this.checkAuth();
            await this.loadNotes();
          } else {
            throw new Error('Failed to get user information');
          }
        } catch (error) {
          console.error('Error getting user info:', error);
          this.$toast.error('Failed to get user information');
          // Clean URL even on error
          window.history.replaceState({}, document.title, window.location.pathname);
        }
      }

      // Handle Gmail OAuth callback (integration successful)
      if (oauthSuccess === 'true') {
        this.$toast.success('Gmail integration connected successfully!');

        // Reload email integrations if we're on that section
        if (this.currentSection === 'emailmodal') {
          // Trigger reload in EmailModal component
          this.$nextTick(() => {
            const emailModal = this.$children.find(child => child.$options.name === 'EmailModal');
            if (emailModal && emailModal.loadEmailIntegrations) {
              emailModal.loadEmailIntegrations();
            }
          });
        }

        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
      }

      // Handle OAuth error
      const oauthError = urlParams.get('oauth_error');
      if (oauthError) {
        this.$toast.error(`OAuth error: ${oauthError}`);
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    },
  },
  computed: {
    filteredNotes() {
      if (!this.searchTerm.trim()) {
        return this.notes;
      }
      const term = this.searchTerm.toLowerCase();
      return this.notes.filter(note =>
        note.content.toLowerCase().includes(term)
      );
    },
  },
};
</script>
