<template>
  <div class="slack-modal">
    <h2>Slack Integration</h2>

    <!-- Informational message about OAuth credentials -->
    <div class="info-message">
      <p>
        <strong>OAuth Credentials:</strong> If you have saved SLACK_CLIENT_ID and SLACK_CLIENT_SECRET in your credentials, those will be used instead of the environment variables.
        <span v-if="redirectUri" class="redirect-uri">
          <strong>Redirect URI:</strong> <code>{{ redirectUri }}</code>
        </span>
      </p>
    </div>

    <!-- Estado de carga -->
    <div v-if="loading" class="loading-state">
      Checking Slack integrations...
    </div>

    <!-- Estado de error -->
    <div v-else-if="error" class="error-state">
      <div class="error-message">
        {{ error }}
      </div>
      <button @click="loadSlackIntegrations" class="retry-btn">
        Try Again
      </button>
    </div>

    <!-- Estado con integración existente -->
    <div v-else-if="slackIntegration && !loading" class="integration-existing">
      <div class="integration-info">
        <h3>Current Integration</h3>
        <div class="integration-details">
          <div class="detail-item">
            <span class="label">Provider:</span>
            <span class="value">{{ slackIntegration.provider || 'slack' }}</span>
          </div>
          <div class="detail-item">
            <span class="label">Status:</span>
            <span :class="['value', `status-${slackIntegration.status || 'unknown'}`]">
              {{ slackIntegration.status || 'unknown' }}
            </span>
          </div>
          <div class="detail-item">
            <span class="label">Workspace:</span>
            <span class="value">{{ slackIntegration.workspace_name || 'N/A' }}</span>
          </div>
          <div class="detail-item">
            <span class="label">Last Sync:</span>
            <span class="value">{{ formatDate(slackIntegration.last_sync) }}</span>
          </div>
        </div>

        <div class="integration-actions">
          <button
            @click="viewMessages"
            class="action-btn primary"
            :disabled="loadingMessages"
          >
            {{ loadingMessages ? 'Loading...' : 'View Messages' }}
          </button>
          <button
            @click="syncSlack"
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

      <!-- Lista de mensajes -->
      <div v-if="showMessagesList" class="messages-list">
        <h3>Recent Messages ({{ messages.length }})</h3>
        <div v-if="loadingMessages" class="loading-messages">
          Loading messages...
        </div>
        <div v-else-if="messages.length === 0" class="no-messages">
          No messages found
        </div>
        <ul v-else class="messages-list-items">
          <li v-for="message in messages" :key="message.id" class="message-item">
            <div class="message-channel">#{{ message.channel || 'general' }}</div>
            <div class="message-content">{{ message.text || '(No content)' }}</div>
            <div class="message-meta">
              <span class="message-user">{{ message.user || 'Unknown user' }}</span>
              <span class="message-date">{{ formatDate(message.timestamp) }}</span>
            </div>
          </li>
        </ul>
        <button @click="showMessagesList = false" class="close-messages-btn">Close</button>
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
        No Slack integration configured yet.
      </div>
      <div class="actions">
        <button @click="connectWithOAuth" class="add-btn connect-btn-full" :disabled="connecting">
          {{ connecting ? 'Connecting...' : '🔗 Connect with Slack' }}
        </button>
        <p class="connect-info-text">
          Connect using Slack OAuth
        </p>
      </div>
    </div>

    <!-- Modal de configuración -->
    <div v-if="showConfigModal" class="config-modal-overlay">
      <div class="config-modal">
        <h3>Configure Slack Integration</h3>

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
                v-for="cred in slackCredentials"
                :key="cred.id"
                :value="cred.id"
              >
                {{ cred.name }} ({{ cred.service_type }})
              </option>
            </select>
            <p v-if="credentials.length === 0" class="no-credentials">
              No Slack credentials found.
              <a href="#credentials">Add credentials first</a>
            </p>
          </div>

          <div class="oauth-option">
            <p>Connect with Slack OAuth:</p>
            <p>
              This will automatically create credentials and integration
            </p>
            <button
              @click="connectWithOAuth"
              class="oauth-btn slack"
              :disabled="connecting"
            >
              {{ connecting ? 'Connecting...' : '🔗 Connect with Slack' }}
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
import { messagesService } from '../services/messagesService';


export default {
  name: 'SlackModal',
  data() {
    return {
      loading: true,
      error: null,
      slackIntegration: null,
      showConfigModal: false,
      selectedCredentialId: '',
      credentials: [],
      connecting: false,
      messages: [],
      showMessagesList: false,
      loadingMessages: false,
      redirectUri: null
    };
  },
  async mounted() {
    await this.loadSlackIntegrations();
    await this.loadCredentials();
    await this.loadRedirectUri();
  },
  computed: {
    slackCredentials() {
      return this.credentials.filter(cred =>
        cred.service_type.toLowerCase().includes('slack')
      );
    }
  },
  methods: {
    async loadSlackIntegrations() {
      this.loading = true;
      this.error = null;

      try {
        const integrations = await messagesService.getIntegrations();
        console.log('Loaded Slack integrations:', integrations);
        this.slackIntegration = integrations.length > 0 ? integrations[0] : null;
      } catch (error) {
        console.error('Error loading Slack integrations:', error);
        if (error.response && error.response.status === 403) {
          this.error = 'Authentication required. Please log in.';
        } else if (error.response && error.response.status === 404) {
          this.slackIntegration = null;
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
        this.redirectUri = response.data.slack;
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

        const newIntegration = await messagesService.createIntegration(integrationData);
        this.slackIntegration = newIntegration;
        this.showConfigModal = false;
        this.$toast.success('Slack integration connected successfully');
      } catch (error) {
        console.error('Error creating Slack integration:', error);
        this.$toast.error('Failed to connect Slack integration');
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

        // This will fail until the backend is created, but the frontend is ready
        const response = await axios.get(`${API_URL}/auth/slack/authorize`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        const authUrl = response.data?.auth_url;
        if (authUrl) {
          window.location.href = authUrl;
        } else {
          throw new Error('No auth URL received from Slack OAuth endpoint');
        }
      } catch (error) {
        console.error('Error initiating Slack OAuth:', error);
        if (error.response?.data?.detail) {
          this.$toast.error(error.response.data.detail);
        } else {
          this.$toast.error('Failed to connect with Slack');
        }
      } finally {
        this.connecting = false;
      }
    },

    async deleteIntegration() {
      if (!confirm('Are you sure you want to remove this Slack integration?')) {
        return;
      }

      try {
        await messagesService.deleteIntegration(this.slackIntegration.id);
        this.slackIntegration = null;
        this.$toast.success('Slack integration removed successfully');
      } catch (error) {
        console.error('Error deleting Slack integration:', error);
        this.$toast.error('Failed to remove Slack integration');
      }
    },

    async syncSlack() {
      try {
        await messagesService.syncMessages(this.slackIntegration.id);
        this.$toast.success('Slack sync completed successfully');
        await this.loadSlackIntegrations();
      } catch (error) {
        console.error('Error syncing Slack:', error);
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to sync Slack';
        this.$toast.error(errorMessage);
      }
    },

    async viewMessages() {
      if (!this.slackIntegration || !this.slackIntegration.id) {
        this.$toast.error('No Slack integration available');
        return;
      }

      this.loadingMessages = true;
      this.showMessagesList = true;

      try {
        const response = await messagesService.getMessages(this.slackIntegration.id, {
          max_results: 10
        });

        this.messages = response || [];

        if (this.messages.length === 0) {
          this.$toast.info('No messages found');
        } else {
          this.$toast.success(`Loaded ${this.messages.length} messages`);
        }
      } catch (error) {
        console.error('Error loading messages:', error);
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to load messages';
        this.$toast.error(errorMessage);
      } finally {
        this.loadingMessages = false;
      }
    },

    formatDate(dateString) {
      if (!dateString) return 'Never';
      return new Date(dateString).toLocaleString();
    }
  }
};
</script>

<style scoped src="./MessagesModal.css"></style>
