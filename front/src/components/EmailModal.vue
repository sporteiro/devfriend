<template>
  <div class="email-modal">
    <h2>Email Integration</h2>

    <!-- Informational message about OAuth credentials -->
    <div class="info-message">
      <p>
        <strong>OAuth Credentials:</strong> If you have saved GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your credentials, those will be used instead of the environment variables.
        <span v-if="redirectUri" class="redirect-uri">
          <strong>Redirect URI:</strong> <code>{{ redirectUri }}</code>
        </span>
      </p>
    </div>

    <!-- Estado de carga -->
    <div v-if="loading" class="loading-state">
      Checking email integrations...
    </div>

    <!-- Estado de error -->
    <div v-else-if="error" class="error-state">
      <div class="error-message">
        {{ error }}
      </div>
      <button @click="loadEmailIntegrations" class="retry-btn">
        Try Again
      </button>
    </div>

    <!-- Estado con integración existente -->
    <div v-else-if="emailIntegration && !loading" class="integration-existing">
      <div class="integration-info">
        <h3>Current Integration</h3>
        <div class="integration-details">
          <div class="detail-item">
            <span class="label">Provider:</span>
            <span class="value">{{ emailIntegration.provider || 'gmail' }}</span>
          </div>
          <div class="detail-item">
            <span class="label">Status:</span>
            <span :class="['value', `status-${emailIntegration.status || 'unknown'}`]">
              {{ emailIntegration.status || 'unknown' }}
            </span>
          </div>
          <div class="detail-item">
            <span class="label">Email:</span>
            <span class="value">{{ emailIntegration.email_address || 'N/A' }}</span>
          </div>
          <div class="detail-item">
            <span class="label">Last Sync:</span>
            <span class="value">{{ formatDate(emailIntegration.last_sync) }}</span>
          </div>
        </div>

        <div class="integration-actions">
          <button
            @click="viewEmails"
            class="action-btn primary"
            :disabled="loadingEmails"
          >
            {{ loadingEmails ? 'Loading...' : 'View Emails' }}
          </button>
          <button
            @click="syncEmails"
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

      <!-- Lista de emails -->
      <div v-if="showEmailsList" class="emails-list">
        <h3>Recent Emails ({{ emails.length }})</h3>
        <div v-if="loadingEmails" class="loading-emails">
          Loading emails...
        </div>
        <div v-else-if="emails.length === 0" class="no-emails">
          No emails found
        </div>
        <ul v-else class="emails-list-items">
          <li v-for="email in emails" :key="email.id" class="email-item">
            <div class="email-title">{{ email.subject || '(No subject)' }}</div>
            <div class="email-meta">
              <span class="email-from">{{ email.sender || email.from || 'Unknown sender' }}</span>
              <span class="email-date">{{ formatDate(email.date) }}</span>
              <span v-if="!email.read" class="email-unread-badge">Unread</span>
            </div>
            <div v-if="email.snippet || email.preview" class="email-snippet">
              {{ email.snippet || email.preview }}
            </div>
          </li>
        </ul>
        <button @click="showEmailsList = false" class="close-emails-btn">Close</button>
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
        No email integration configured yet.
      </div>
      <div class="actions">
        <button @click="connectWithOAuth" class="add-btn connect-btn-full" :disabled="connecting">
          {{ connecting ? 'Connecting...' : '🔗 Connect with Google' }}
        </button>
        <p class="connect-info-text">
          This will automatically create credentials and integration with refresh token.
        </p>
      </div>
    </div>

    <!-- Modal de configuración -->
    <div v-if="showConfigModal" class="config-modal-overlay">
      <div class="config-modal">
        <h3>Configure Email Integration</h3>

        <div class="connection-config">
          <div class="form-group">
            <label for="provider-select">Email Provider:</label>
            <select id="provider-select" v-model="selectedProvider" class="form-select">
              <option value="gmail">Gmail</option>
            </select>
          </div>

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
                v-for="cred in gmailCredentials"
                :key="cred.id"
                :value="cred.id"
              >
                {{ cred.name }} ({{ cred.service_type }})
              </option>
            </select>
            <p v-if="credentials.length === 0" class="no-credentials">
              No Gmail credentials found.
              <a href="#credentials">Add credentials first</a>
            </p>
          </div>

          <div class="oauth-option">
            <p>Connect with Google OAuth:</p>
            <p>
              This will automatically create credentials and integration with refresh token.
            </p>
            <button
              @click="connectWithOAuth"
              class="oauth-btn google"
              :disabled="connecting"
            >
              {{ connecting ? 'Connecting...' : '🔗 Connect with Google' }}
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
import { emailService } from '../services/emailService';

export default {
  name: 'EmailModal',
  data() {
    return {
      loading: true,
      error: null,
      emailIntegration: null,
      showConfigModal: false,
      selectedProvider: 'gmail',
      selectedCredentialId: '',
      credentials: [],
      connecting: false,
      emails: [],
      showEmailsList: false,
      loadingEmails: false,
      redirectUri: null
    };
  },
  async mounted() {
    await this.loadEmailIntegrations();
    await this.loadCredentials();
    await this.loadRedirectUri();

    // Check if we just came back from OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    const oauthSuccess = urlParams.get('oauth_success');
    const integrationId = urlParams.get('integration_id');

    if (oauthSuccess === 'true') {
      console.log('OAuth success detected, reloading integrations...');
      // Reload integrations after OAuth success
      await this.loadEmailIntegrations();
      await this.loadCredentials();

      if (integrationId) {
        this.$toast.success('Gmail integration connected successfully!');
      } else {
        this.$toast.info('OAuth completed, please check your integrations');
      }

      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  },
  computed: {
    gmailCredentials() {
      return this.credentials.filter(cred =>
        cred.service_type.toLowerCase().includes('gmail') ||
        cred.service_type.toLowerCase().includes('email')
      );
    }
  },
  methods: {
    async loadEmailIntegrations() {
      this.loading = true;
      this.error = null;

      try {
        const integrations = await emailService.getIntegrations();
        console.log('Loaded integrations:', integrations);
        // For now, we only handle one integration
        this.emailIntegration = integrations.length > 0 ? integrations[0] : null;
        console.log('Email integration set to:', this.emailIntegration);
      } catch (error) {
        console.error('Error loading email integrations:', error);
        if (error.response && error.response.status === 403) {
          this.error = 'Authentication required. Please log in.';
        } else if (error.response && error.response.status === 404) {
          // No integrations found, that's OK
          this.emailIntegration = null;
        } else {
          this.error = 'Could not connect to server. Please try again.';
        }
      } finally {
        this.loading = false;
        console.log('Loading finished. emailIntegration:', this.emailIntegration, 'loading:', this.loading);
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
        this.redirectUri = response.data.google;
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
          provider: this.selectedProvider,
          credential_id: parseInt(this.selectedCredentialId)
        };

        const newIntegration = await emailService.createIntegration(integrationData);
        this.emailIntegration = newIntegration;
        this.showConfigModal = false;
        this.$toast.success('Email integration connected successfully');
      } catch (error) {
        console.error('Error creating email integration:', error);
        this.$toast.error('Failed to connect email integration');
      } finally {
        this.connecting = false;
      }
    },

    async connectWithOAuth() {
      this.connecting = true;
      try {
        // Get auth token
        const token = localStorage.getItem('devfriend_token');
        if (!token) {
          this.$toast.error('Please log in first');
          this.connecting = false;
          return;
        }

        console.log('Initiating OAuth flow for Gmail integration...');

        // Use axios to get OAuth URL (simplified - no secret_id needed)
        const API_URL = process.env.VUE_APP_API_URL || 'http://localhost:8888';
        const axios = (await import('axios')).default;

        try {
          // Make request to get OAuth URL (uses env vars automatically)
          const url = `${API_URL}/auth/google/authorize`;
          console.log('Calling OAuth authorize endpoint:', url);

          const response = await axios.get(url, {
            headers: {
              'Authorization': `Bearer ${token}`,
            }
          });

          console.log('OAuth response:', response.data);

          // Get the auth_url from response
          const authUrl = response.data?.auth_url;
          if (authUrl) {
            console.log('Redirecting to Google OAuth:', authUrl);
            // Redirect to Google OAuth
            window.location.href = authUrl;
          } else {
            throw new Error('No auth URL received from OAuth endpoint');
          }
        } catch (error) {
          console.error('OAuth request error:', error);
          if (error.response) {
            console.error('Error response:', error.response.status, error.response.data);
            if (error.response.status === 401 || error.response.status === 403) {
              this.$toast.error('Authentication failed. Please log in again.');
              this.connecting = false;
              return;
            } else if (error.response.data?.detail) {
              throw new Error(error.response.data.detail);
            }
          }
          throw error;
        }
      } catch (error) {
        console.error('Error initiating OAuth:', error);
        this.$toast.error(error.message || 'Failed to start OAuth flow');
        this.connecting = false;
      }
    },

    async deleteIntegration() {
      if (!confirm('Are you sure you want to remove this email integration?')) {
        return;
      }

      try {
        await emailService.deleteIntegration(this.emailIntegration.id);
        this.emailIntegration = null;
        this.$toast.success('Email integration removed successfully');
      } catch (error) {
        console.error('Error deleting email integration:', error);
        this.$toast.error('Failed to remove email integration');
      }
    },

    async syncEmails() {
      try {
        await emailService.syncEmails(this.emailIntegration.id);
        this.$toast.success('Email sync completed successfully');
        // Reload integrations to get updated status and secret_id
        await this.loadEmailIntegrations();
      } catch (error) {
        console.error('Error syncing emails:', error);
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to sync emails';

        // Check if it's a refresh_token error
        if (errorMessage.includes('refresh_token') || errorMessage.includes('OAuth') || errorMessage.includes('authorize')) {
          this.$toast.error('Missing OAuth authorization. Please connect with Google OAuth first.', {
            duration: 5000
          });
          // Reload to get updated secret_id after auto-fix
          await this.loadEmailIntegrations();
          // Show config modal with OAuth option
          this.showConfigModal = true;
        } else {
          this.$toast.error(errorMessage);
        }
      }
    },

    async viewEmails() {
      if (!this.emailIntegration || !this.emailIntegration.id) {
        this.$toast.error('No email integration available');
        return;
      }

      this.loadingEmails = true;
      this.showEmailsList = true;

      try {
        // Get 10 most recent emails
        const response = await emailService.getEmails(this.emailIntegration.id, {
          max_results: 10
        });

        // Backend returns array with subject, sender, date, snippet, etc.
        this.emails = response || [];

        if (this.emails.length === 0) {
          this.$toast.info('No emails found');
        } else {
          this.$toast.success(`Loaded ${this.emails.length} emails`);
        }
      } catch (error) {
        console.error('Error loading emails:', error);
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to load emails';

        // Show error message with duration if it's about Gmail API not enabled
        if (errorMessage.includes('Gmail API is not enabled')) {
          this.$toast.error(errorMessage, {
            duration: 8000
          });
        } else {
          this.$toast.error(errorMessage);
        }

        if (errorMessage.includes('refresh_token') || errorMessage.includes('OAuth')) {
          this.showConfigModal = true;
        }
      } finally {
        this.loadingEmails = false;
      }
    },

    formatDate(dateString) {
      if (!dateString) return 'Never';
      return new Date(dateString).toLocaleString();
    }
  }
};
</script>

<style scoped src="./EmailModal.css"></style>
