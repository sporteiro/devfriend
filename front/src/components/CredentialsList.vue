<template>
  <div class="credentials-list">
    <h2>Your Credentials</h2>
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

<style scoped>
.credentials-list {
  max-width: 600px;
  margin: 0 auto;
}
.cred-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
  background: #fff;
  border: none;
  color: #333;
}
.dark .cred-table {
  background: #23272b;
  color: #eee;
}
.cred-table th,
.cred-table td {
  border: none !important;
  padding: 10px 8px;
  text-align: left;
}
.dark .cred-table th, .dark .cred-table td {
  color: #eee;
}
.add-btn {
  margin-bottom: 16px;
  background: #095633;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 8px 14px;
  cursor: pointer;
  font-weight: 500;
}
.dark .add-btn {
  background: #11896c;
  color: #fff;
}
.delete-btn {
  color: #fff;
  background: #c0392b;
  border: none;
  border-radius: 4px;
  padding: 6px 12px;
  cursor: pointer;
}
.dark .delete-btn {
  background: #a43c2d;
  color: #fff;
}
.cred-empty,
.cred-empty-error {
  margin-top: 30px;
  font-style: italic;
  color: #888;
  text-align: center;
}
.dark .cred-empty,
.dark .cred-empty-error {
  color: #b4b8be;
}
/* Inputs formulario (por si hay inputs directos en la vista) */
input, select {
  background: #fff;
  color: #222;
  border: 1px solid #aaa;
  padding: 8px 10px;
  border-radius: 4px;
  font-size: 15px;
}
.dark input, .dark select {
  background: #26292e;
  color: #f5f5f5;
  border: 1px solid #444;
}
</style>
