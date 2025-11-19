<template>
  <div class="repository-modal">
    <h2>GitHub Integration</h2>

    <!-- Informational message about OAuth credentials -->
    <div class="info-message" style="background: #e3f2fd; border-left: 4px solid #2196f3; padding: 12px; margin-bottom: 20px; border-radius: 4px;">
      <p style="margin: 0; font-size: 0.9em; color: #1565c0;">
        <strong>OAuth Credentials:</strong> If you have saved GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in your credentials, those will be used instead of the environment variables.
        <span v-if="redirectUri" style="display: block; margin-top: 8px;">
          <strong>Redirect URI:</strong> <code style="background: white; padding: 2px 6px; border-radius: 3px;">{{ redirectUri }}</code>
        </span>
      </p>
    </div>

    <!-- Estado de carga -->
    <div v-if="loading" class="loading-state">
      Checking GitHub integrations...
    </div>

    <!-- Estado de error -->
    <div v-else-if="error" class="error-state">
      <div class="error-message">
        {{ error }}
      </div>
      <button @click="loadGithubIntegrations" class="retry-btn">
        Try Again
      </button>
    </div>

    <!-- Estado con integración existente -->
    <div v-else-if="githubIntegration && !loading" class="integration-existing">
      <div class="integration-info">
        <h3>Current Integration</h3>
        <div class="integration-details">
          <div class="detail-item">
            <span class="label">Provider:</span>
            <span class="value">{{ githubIntegration.provider || 'github' }}</span>
          </div>
          <div class="detail-item">
            <span class="label">Status:</span>
            <span :class="['value', `status-${githubIntegration.status || 'unknown'}`]">
              {{ githubIntegration.status || 'unknown' }}
            </span>
          </div>
          <div class="detail-item">
            <span class="label">Username:</span>
            <span class="value">{{ githubIntegration.github_username || 'N/A' }}</span>
          </div>
          <div class="detail-item">
            <span class="label">Last Sync:</span>
            <span class="value">{{ formatDate(githubIntegration.last_sync) }}</span>
          </div>
        </div>

        <div class="integration-actions">
          <button
            @click="viewRepos"
            class="action-btn primary"
            :disabled="loadingRepos"
          >
            {{ loadingRepos ? 'Loading...' : 'View Repositories' }}
          </button>
          <button
            @click="syncGithub"
            class="action-btn secondary"
          >
            Sync Now
          </button>
          <button
            @click="deleteIntegration"
            class="action-btn danger"
          >
            Remove
          </button>
        </div>
      </div>

      <!-- Lista de repositorios -->
      <div v-if="showReposList" class="repos-list">
        <h3>Recent Repositories ({{ repos.length }})</h3>
        <div v-if="loadingRepos" class="loading-repos">
          Loading repositories...
        </div>
        <div v-else-if="repos.length === 0" class="no-repos">
          No repositories found
        </div>
        <ul v-else class="repos-list-items">
          <li v-for="repo in repos" :key="repo.id" class="repo-item">
            <div class="repo-title">
              <span class="repo-name">{{ repo.name }}</span>
              <span :class="['repo-visibility', repo.private ? 'private' : 'public']">
                {{ repo.private ? 'Private' : 'Public' }}
              </span>
            </div>
            <div class="repo-meta">
              <span class="repo-language" v-if="repo.language">
                {{ repo.language }}
              </span>
              <span class="repo-stars">
                ⭐ {{ repo.stargazers_count || 0 }}
              </span>
              <span class="repo-forks">
                🍴 {{ repo.forks_count || 0 }}
              </span>
              <span class="repo-updated">
                Updated {{ formatRelativeDate(repo.updated_at) }}
              </span>
            </div>
            <div v-if="repo.description" class="repo-description">
              {{ repo.description }}
            </div>
          </li>
        </ul>
        <button @click="showReposList = false" class="close-repos-btn">Close</button>
      </div>

      <div class="actions">
        <button @click="showConfigModal = true" class="add-btn">
          + Add Another Integration
        </button>
      </div>
    </div>

    <!-- Estado sin integración -->
    <div v-else class="integration-empty">
      <div class="empty-message">
        No GitHub integration configured yet.
      </div>
      <div class="actions">
        <button @click="connectWithOAuth" class="add-btn" :disabled="connecting" style="width: 100%; max-width: 300px; padding: 15px; font-size: 16px;">
          {{ connecting ? 'Connecting...' : '🔗 Connect with GitHub' }}
        </button>
        <p style="margin-top: 15px; font-size: 0.9em; color: var(--text-secondary);">
          Connect using GitHub OAuth
        </p>
      </div>
    </div>

    <!-- Modal de configuración -->
    <div v-if="showConfigModal" class="config-modal-overlay">
      <div class="config-modal">
        <h3>Configure GitHub Integration</h3>

        <div class="connection-config">
          <div class="form-group">
            <label for="credential-select">Select Credential:</label>
            <select
              id="credential-select"
              v-model="selectedCredentialId"
              class="form-select"
              :disabled="credentials.length === 0"
            >
              <option value="">Choose a credential</option>
              <option
                v-for="cred in githubCredentials"
                :key="cred.id"
                :value="cred.id"
              >
                {{ cred.name }} ({{ cred.service_type }})
              </option>
            </select>
            <p v-if="credentials.length === 0" class="no-credentials">
              No GitHub credentials found.
              <a href="#credentials">Add credentials first</a>
            </p>
          </div>

          <div class="oauth-option" style="margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 5px;">
            <p style="margin-bottom: 10px; font-weight: bold;">Connect with GitHub OAuth:</p>
            <p style="margin-bottom: 10px; font-size: 0.9em; color: #666;">
              This will automatically create credentials and integration
            </p>
            <button
              @click="connectWithOAuth"
              class="oauth-btn"
              :disabled="connecting"
              style="width: 100%; padding: 12px; background: #24292e; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500;"
            >
              {{ connecting ? 'Connecting...' : '🔗 Connect with GitHub' }}
            </button>
          </div>
          <div class="pat-option" style="margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 5px;">
            <p style="margin-bottom: 10px; font-weight: bold;">Or use Personal Access Token:</p>
            <p style="margin-bottom: 10px; font-size: 0.9em; color: #666;">
              Create a GitHub PAT with repo and read:user scopes
            </p>
            <button
              @click="connectWithPAT"
              class="pat-btn"
              :disabled="connecting"
              style="width: 100%; padding: 12px; background: #586069; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500;"
            >
              {{ connecting ? 'Connecting...' : 'Use PAT Instead' }}
            </button>
          </div>
        </div>

        <div class="modal-actions">
          <button @click="showConfigModal = false" class="cancel-btn">
            Cancel
          </button>
          <button
            @click="connectIntegration"
            class="connect-btn"
            :disabled="!selectedCredentialId || connecting"
          >
            {{ connecting ? 'Connecting...' : 'Connect' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { secretService } from '../services/secretService';
import { githubService } from '../services/githubService';

export default {
  name: 'RepositoryModal',
  data() {
    return {
      loading: true,
      error: null,
      githubIntegration: null,
      showConfigModal: false,
      selectedCredentialId: '',
      credentials: [],
      connecting: false,
      repos: [],
      showReposList: false,
      loadingRepos: false,
      redirectUri: null
    };
  },
  async mounted() {
    await this.loadGithubIntegrations();
    await this.loadCredentials();
    await this.loadRedirectUri();
  },
  computed: {
    githubCredentials() {
      return this.credentials.filter(cred =>
        cred.service_type.toLowerCase().includes('github')
      );
    }
  },
  methods: {
    async loadGithubIntegrations() {
      this.loading = true;
      this.error = null;

      try {
        const integrations = await githubService.getIntegrations();
        console.log('Loaded GitHub integrations:', integrations);
        this.githubIntegration = integrations.length > 0 ? integrations[0] : null;
        console.log('GitHub integration set to:', this.githubIntegration);
      } catch (error) {
        console.error('Error loading GitHub integrations:', error);
        if (error.response && error.response.status === 403) {
          this.error = 'Authentication required. Please log in.';
        } else if (error.response && error.response.status === 404) {
          this.githubIntegration = null;
        } else {
          this.error = 'Could not connect to server. Please try again.';
        }
      } finally {
        this.loading = false;
      }
    },

    async loadCredentials() {
      try {
        this.credentials = await secretService.listSecrets();
      } catch (error) {
        console.error('Error loading credentials:', error);
      }
    },

    async loadRedirectUri() {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL || 'http://localhost:8888'}/oauth/redirect-uris`);
        this.redirectUri = response.data.github;
      } catch (error) {
        console.error('Error loading redirect URI:', error);
      }
    },

    async connectIntegration() {
      if (!this.selectedCredentialId) {
        this.$toast.error('Please select a credential');
        return;
      }

      this.connecting = true;

      try {
        const integrationData = {
          credential_id: parseInt(this.selectedCredentialId)
        };

        const newIntegration = await githubService.createIntegration(integrationData);
        this.githubIntegration = newIntegration;
        this.showConfigModal = false;
        this.$toast.success('GitHub integration connected successfully');
      } catch (error) {
        console.error('Error creating GitHub integration:', error);
        this.$toast.error('Failed to connect GitHub integration');
      } finally {
        this.connecting = false;
      }
    },

    async connectWithOAuth() {
      this.connecting = true;
      try {
        const token = localStorage.getItem('devfriend_token');
        if (!token) {
          this.$toast.error('Please log in first');
          this.connecting = false;
          return;
        }

        const API_URL = process.env.VUE_APP_API_URL || 'http://localhost:8888';
        const axios = (await import('axios')).default;

        const response = await axios.get(`${API_URL}/auth/github/authorize`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        const authUrl = response.data?.auth_url;
        if (authUrl) {
          window.location.href = authUrl;
        } else {
          throw new Error('No auth URL received from GitHub OAuth endpoint');
        }
      } catch (error) {
        console.error('Error initiating GitHub OAuth:', error);
        if (error.response?.data?.detail) {
          this.$toast.error(error.response.data.detail);
        } else {
          this.$toast.error('Failed to connect with GitHub');
        }
      } finally {
        this.connecting = false;
      }
    },

    async connectWithPAT() {
      this.connecting = true;
      try {
        // Redirect to credentials page to add GitHub PAT
        this.$emit('navigate', 'credentials');
      } catch (error) {
        console.error('Error connecting with PAT:', error);
        this.$toast.error(error.message || 'Failed to connect with GitHub');
      } finally {
        this.connecting = false;
      }
    },

    async deleteIntegration() {
      if (!confirm('Are you sure you want to remove this GitHub integration?')) {
        return;
      }

      try {
        await githubService.deleteIntegration(this.githubIntegration.id);
        this.githubIntegration = null;
        this.$toast.success('GitHub integration removed successfully');
      } catch (error) {
        console.error('Error deleting GitHub integration:', error);
        this.$toast.error('Failed to remove GitHub integration');
      }
    },

    async syncGithub() {
      try {
        await githubService.syncGithub(this.githubIntegration.id);
        this.$toast.success('GitHub sync completed successfully');
        await this.loadGithubIntegrations();
      } catch (error) {
        console.error('Error syncing GitHub:', error);
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to sync GitHub';
        this.$toast.error(errorMessage);
      }
    },

    async viewRepos() {
      if (!this.githubIntegration || !this.githubIntegration.id) {
        this.$toast.error('No GitHub integration available');
        return;
      }

      this.loadingRepos = true;
      this.showReposList = true;

      try {
        const response = await githubService.getRepos(this.githubIntegration.id, {
          max_results: 10,
          visibility: 'all'
        });

        this.repos = response || [];

        if (this.repos.length === 0) {
          this.$toast.info('No repositories found');
        } else {
          this.$toast.success(`Loaded ${this.repos.length} repositories`);
        }
      } catch (error) {
        console.error('Error loading repositories:', error);
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to load repositories';
        this.$toast.error(errorMessage);
      } finally {
        this.loadingRepos = false;
      }
    },

    formatDate(dateString) {
      if (!dateString) return 'Never';
      return new Date(dateString).toLocaleString();
    },

    formatRelativeDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      const now = new Date();
      const diffTime = Math.abs(now - date);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

      if (diffDays === 1) return 'today';
      if (diffDays < 7) return `${diffDays} days ago`;
      if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
      return `${Math.floor(diffDays / 30)} months ago`;
    }
  }
};
</script>

<style scoped src="./RepositoryModal.css"></style>
