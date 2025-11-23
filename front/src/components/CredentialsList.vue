<template>
  <div class="credentials-list">
    <h2>Your Credentials</h2>

    <!-- Informational message about OAuth credentials -->
    <div class="info-message-warning">
      <p>
        <strong>OAuth Credentials Priority:</strong> When connecting to Gmail, GitHub, or Slack, if you have saved the corresponding CLIENT_ID and CLIENT_SECRET credentials (GOOGLE_CLIENT_ID/SECRET, GITHUB_CLIENT_ID/SECRET, or SLACK_CLIENT_ID/SECRET), those will be used instead of the environment variables. This allows you to use your own OAuth applications.
      </p>
    </div>

    <!-- Informational message about custom keys decryption -->
    <div class="info-message">
      <p>
        <strong>Custom Keys Decryption:</strong> The "Show values of custom keys" button will decrypt and display
        the actual values <strong>only for credentials with "custom" service type</strong>.
        For other service types (OAuth credentials like Gmail, GitHub, Slack), values remain hidden for security.
      </p>
    </div>

    <div class="buttons-container">
      <button v-if="authError === false" @click="showForm = !showForm" class="add-btn">
        {{ showForm ? 'Cancel' : 'Add Credential' }}
      </button>
      <button v-if="authError === false && credentials.length" @click="toggleSecretValues" class="add-btn margin-left">
        {{ showDecryptedValues ? '🔒 Hide values' : '🔓 Show values of custom keys' }}
      </button>
    </div>

    <CredentialForm
      v-if="showForm"
      @cancel="showForm = false"
      @created="onCreated"
    />
    <div v-if="authError" class="cred-empty-error">
      Please log in to manage your credentials.
    </div>
    <table v-if="credentials.length && !authError" class="cred-table">
      <thead>
        <tr>
          <th>Service</th>
          <th>Name</th>
          <th>Value</th>
          <th>Created</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="cred in credentials" :key="cred.id">
          <td>{{ cred.service_type }}</td>
          <td>{{ cred.name }}</td>
          <td>{{ getSecretValue(cred) }}</td>
          <td>{{ formatDate(cred.created_at) }}</td>
          <td>
            <button @click="deleteSecret(cred.id)" class="delete-btn">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else-if="!credentials.length && !authError" class="cred-empty">You have no credentials saved yet.</div>
  </div>
</template>

<script>
import { secretService } from '../services/secretService';
import CredentialForm from './CredentialForm.vue';

export default {
  name: 'CredentialsList',
  components: { CredentialForm },
  data() {
    return {
      credentials: [],
      decryptedSecrets: [],
      showForm: false,
      authError: false,
      showDecryptedValues: false,
    };
  },
  async mounted() {
    await this.loadCredentials();
  },
  methods: {
    async loadCredentials() {
      try {
        this.credentials = await secretService.listSecrets();
        this.authError = false;
      } catch (e) {
        if (e.response && e.response.status === 403) {
          this.authError = true;
        }
      }
    },
    async deleteSecret(id) {
      if (confirm('Delete this credential?')) {
        await secretService.deleteSecret(id);
        this.$toast.success('Deleted successfully');
        await this.loadCredentials();
      }
    },
    async toggleSecretValues() {
      if (this.showDecryptedValues) {
        // Hide values
        this.showDecryptedValues = false;
        this.decryptedSecrets = [];
      } else {
        // Show values - get decrypted secrets
        try {
          this.decryptedSecrets = await secretService.getDecryptableSecrets();
          this.showDecryptedValues = true;
          this.$toast.success('Showing decrypted values');
        } catch (error) {
          console.error('Error getting decrypted secrets:', error);
          this.$toast.error('Error loading decrypted values');
        }
      }
    },
    getSecretValue(cred) {
      if (!this.showDecryptedValues) {
        return '*****';
      }

      // Find decrypted secret by ID
      const decryptedCred = this.decryptedSecrets.find(d => d.id === cred.id);

      if (decryptedCred && decryptedCred.encrypted_value) {
        try {
          // Parse JSON and extract the first value
          const parsedValue = JSON.parse(decryptedCred.encrypted_value);

          // Get the first value from the object, regardless of the key
          const firstKey = Object.keys(parsedValue)[0];
          return parsedValue[firstKey];
        } catch {
          // If not JSON, show the string directly
          return decryptedCred.encrypted_value;
        }
      }

      return '*****';
    },
    onCreated() {
      this.showForm = false;
      this.loadCredentials();
    },
    formatDate(ts) {
      if (!ts) return '';
      return new Date(ts).toLocaleString();
    },
  },
};
</script>

<style scoped src="./CredentialsList.css"></style>
