<template>
  <div class="credentials-list">
    <h2>Your Credentials</h2>

    <!-- Informational message about OAuth credentials -->
    <div class="info-message-warning">
      <p>
        <strong>OAuth Credentials Priority:</strong> When connecting to Gmail, GitHub, or Slack, if you have saved the corresponding CLIENT_ID and CLIENT_SECRET credentials (GOOGLE_CLIENT_ID/SECRET, GITHUB_CLIENT_ID/SECRET, or SLACK_CLIENT_ID/SECRET), those will be used instead of the environment variables. This allows you to use your own OAuth applications.
      </p>
    </div>
    <button v-if="authError === false" @click="showForm = !showForm" class="add-btn">
      {{ showForm ? 'Cancel' : 'Add Credential' }}
    </button>
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
          <th>Name</th>
          <th>Service</th>
          <th>Created</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="cred in credentials" :key="cred.id">
          <td>{{ cred.name }}</td>
          <td>{{ cred.service_type }}</td>
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
      showForm: false,
      authError: false,
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
