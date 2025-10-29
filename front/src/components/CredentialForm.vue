<template>
  <div class="cred-form">
    <h3>Add Credential</h3>
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label>Service</label>
        <select v-model="service_type">
          <option :value="''" disabled>Select service...</option>
          <option value="github">GitHub</option>
          <option value="gmail">Gmail</option>
          <option value="slack">Slack</option>
        </select>
      </div>
      <div class="form-group">
        <label for="cred-name">Name</label>
        <input id="cred-name" v-model="name" placeholder="Label for your credential" required />
      </div>
      <template v-for="field in fields" :key="field.key">
        <div class="form-group">
          <label :for="field.key">
            {{ field.label }}
            <span v-if="field.secret">*</span>
          </label>
          <input
            :id="field.key"
            :type="field.secret ? 'password' : 'text'"
            v-model="form[field.key]"
            :placeholder="field.secret ? '*****' : field.placeholder"
            autocomplete="off"
            required
          />
        </div>
      </template>
      <div class="actions">
        <button type="submit">Save</button>
        <button type="button" class="cancel-btn" @click="$emit('cancel')">Cancel</button>
      </div>
    </form>
  </div>
</template>

<script>
import { secretService } from '../services/secretService';

// Esquemas por servicio
const credentialSchemas = {
  github: [
    { key: 'token', label: 'Personal Access Token', secret: true, placeholder: '', },
    { key: 'client_id', label: 'Client ID', secret: false, placeholder: '', },
    { key: 'client_secret', label: 'Client Secret', secret: true, placeholder: '', },
  ],
  gmail: [
    { key: 'client_id', label: 'Client ID', secret: false, placeholder: '', },
    { key: 'client_secret', label: 'Client Secret', secret: true, placeholder: '', },
    { key: 'refresh_token', label: 'Refresh Token', secret: true, placeholder: '', },
    { key: 'redirect_uri', label: 'Redirect URI', secret: false, placeholder: '(optional)' },
  ],
  slack: [
    { key: 'bot_token', label: 'Bot Token', secret: true, placeholder: '', },
    { key: 'app_id', label: 'App ID', secret: false, placeholder: '', },
    { key: 'signing_secret', label: 'Signing Secret', secret: true, placeholder: '', },
  ],
};

export default {
  name: 'CredentialForm',
  props: {
    // se puede extender luego a modo edición
  },
  data() {
    return {
      service_type: '',
      name: '',
      form: {},
    };
  },
  computed: {
    fields() {
      return credentialSchemas[this.service_type] || [];
    },
  },
  methods: {
    async handleSubmit() {
      if (!this.service_type || !this.name) {
        this.$toast.error('Complete all required fields');
        return;
      }
      // Armar el objeto solo con los valores ingresados (los password podrán venir vacíos si no se tocaron en edición)
      const datos_secrets = {};
      for (const field of this.fields) {
        if (this.form[field.key]) {
          datos_secrets[field.key] = this.form[field.key];
        }
      }
      try {
        await secretService.createSecret({ name: this.name, service_type: this.service_type, datos_secrets });
        this.$toast.success('Credential created!');
        this.$emit('created');
        this.name = '';
        this.service_type = '';
        this.form = {};
      } catch (e) {
        this.$toast.error(e.message || 'Error creating credential');
      }
    },
  },
};
</script>

<style scoped>
.cred-form {
  padding: 16px 0;
}
.form-group {
  display: flex;
  flex-direction: column;
  margin-bottom: 14px;
}
.form-group label {
  font-weight: 500;
  margin-bottom: 5px;
}
.form-group input,
.form-group select {
  padding: 8px 10px;
  border-radius: 4px;
  border: 1px solid #aaa;
  font-size: 15px;
}
.actions {
  display: flex;
  gap: 15px;
  margin-top: 15px;
}
button.cancel-btn {
  background: #ccc; color: #222;
}
</style>
