<template>
  <div class="email-modal">
    <h2>Email Integration</h2>
    
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
    <div v-else-if="emailIntegration" class="integration-existing">
      <div class="integration-info">
        <h3>Current Integration</h3>
        <div class="integration-details">
          <div class="detail-item">
            <span class="label">Provider:</span>
            <span class="value">{{ emailIntegration.provider }}</span>
          </div>
          <div class="detail-item">
            <span class="label">Status:</span>
            <span :class="['value', `status-${emailIntegration.status}`]">
              {{ emailIntegration.status }}
            </span>
          </div>
          <div class="detail-item">
            <span class="label">Email:</span>
            <span class="value">{{ emailIntegration.email_address }}</span>
          </div>
          <div class="detail-item">
            <span class="label">Last Sync:</span>
            <span class="value">{{ formatDate(emailIntegration.last_sync) }}</span>
          </div>
        </div>
        
        <div class="integration-actions">
          <button @click="viewEmails" class="action-btn primary">
            View Emails
          </button>
          <button @click="syncEmails" class="action-btn secondary">
            Sync Now
          </button>
          <button @click="deleteIntegration" class="action-btn danger">
            Remove
          </button>
        </div>
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
        <button @click="showConfigModal = true" class="add-btn">
          + Add Integration
        </button>
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
      connecting: false
    };
  },
  async mounted() {
    await this.loadEmailIntegrations();
    await this.loadCredentials();
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
        // Asumimos que por ahora solo manejamos una integración
        this.emailIntegration = integrations.length > 0 ? integrations[0] : null;
      } catch (error) {
        console.error('Error loading email integrations:', error);
        this.error = 'Could not connect to server. Please try again.';
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
        this.$toast.success('Email sync started');
      } catch (error) {
        console.error('Error syncing emails:', error);
        this.$toast.error('Failed to sync emails');
      }
    },
    
    viewEmails() {
      // TODO: Implementar vista de emails
      this.$toast.info('Email viewer will be implemented soon');
    },
    
    formatDate(dateString) {
      if (!dateString) return 'Never';
      return new Date(dateString).toLocaleString();
    }
  }
};
</script>

<style scoped src="./EmailModal.css"></style>