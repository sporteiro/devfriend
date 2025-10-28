<template>
  <div v-if="show" class="auth-modal-overlay" @click="closeModal">
    <div class="auth-modal" @click.stop>
      <div class="auth-header">
        <h2>{{ isLogin ? 'Sign In' : 'Sign Up' }}</h2>
        <button @click="closeModal" class="close-btn">×</button>
      </div>
      
      <div class="auth-tabs">
        <button 
          :class="{ active: isLogin }" 
          @click="isLogin = true"
        >
          Sign In
        </button>
        <button 
          :class="{ active: !isLogin }" 
          @click="isLogin = false"
        >
          Sign Up
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="auth-form">
        <div v-if="!isLogin" class="form-group">
          <label for="name">Full name</label>
          <input 
            v-model="formData.name"
            type="text" 
            id="name" 
            required
            placeholder="Your full name"
          />
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input 
            v-model="formData.email"
            type="email" 
            id="email" 
            required
            placeholder="your@email.com"
          />
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input 
            v-model="formData.password"
            type="password" 
            id="password" 
            required
            placeholder="Minimum 6 characters"
          />
        </div>

        <button type="submit" :disabled="loading" class="submit-btn">
          {{ loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Sign Up') }}
        </button>

        <div class="divider">
          <span>or</span>
        </div>

        <button type="button" @click="loginWithGoogle" class="google-btn">
          Continue with Google
        </button>

        <p v-if="error" class="error">{{ error }}</p>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AuthModal',
  props: {
    show: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      isLogin: true,
      loading: false,
      error: null,
      formData: {
        name: '',
        email: '',
        password: '',
      },
    };
  },
  methods: {
    closeModal() {
      this.$emit('close');
      this.resetForm();
    },
    resetForm() {
      this.formData = {
        name: '',
        email: '',
        password: '',
      };
      this.error = null;
      this.loading = false;
    },
    async handleSubmit() {
      this.loading = true;
      this.error = null;
      
      try {
        if (this.isLogin) {
          await this.login();
        } else {
          await this.register();
        }
        this.$emit('success');
        this.closeModal();
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },
    async login() {
      const { authService } = await import('../services/authService');
      await authService.login(this.formData.email, this.formData.password);
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
      }
    },
    async register() {
      if (this.formData.password.length < 6) {
        throw new Error('Password must be at least 6 characters');
      }
      const { authService } = await import('../services/authService');
      await authService.register(this.formData.email, this.formData.password);
      await this.login();
    },
    async loginWithGoogle() {
      this.loading = true;
      this.error = null;

      try {
        this.error = 'Google OAuth not yet implemented. Use email/password for now.';
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped src="./AuthModal.css"></style>
