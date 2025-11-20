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
    { key: 'client_id', label: 'Client ID', secret: false, placeholder: '', },
    { key: 'client_secret', label: 'Client Secret', secret: true, placeholder: '', },
  ],
  gmail: [
    { key: 'client_id', label: 'Client ID', secret: false, placeholder: '', },
    { key: 'client_secret', label: 'Client Secret', secret: true, placeholder: '', },
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
    // Can be extended later for edit mode
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
      // Build the object only with entered values (passwords may be empty if not touched in edit mode)
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

<style scoped src="./CredentialsList.css"></style>
