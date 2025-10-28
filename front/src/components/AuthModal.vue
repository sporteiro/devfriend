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
      // Simular login
      await new Promise(resolve => setTimeout(resolve, 1000));
      if (this.formData.email === 'demo@devfriend.com' && this.formData.password === 'demo123') {
        localStorage.setItem('devfriend_user', JSON.stringify({
          name: 'Demo User',
          email: this.formData.email,
          loginTime: new Date().toISOString(),
        }));
        return;
      }
      throw new Error('Incorrect credentials');
    },
    async register() {
      // Simular registro
      await new Promise(resolve => setTimeout(resolve, 1000));
      if (this.formData.password.length < 6) {
        throw new Error('Password must be at least 6 characters');
      }
      localStorage.setItem('devfriend_user', JSON.stringify({
        name: this.formData.name,
        email: this.formData.email,
        loginTime: new Date().toISOString(),
      }));
    },
    async loginWithGoogle() {
      this.loading = true;
      this.error = null;
      
      try {
        // Simular login con Google
        await new Promise(resolve => setTimeout(resolve, 1000));
        localStorage.setItem('devfriend_user', JSON.stringify({
          name: 'Google User',
          email: 'user@gmail.com',
          loginTime: new Date().toISOString(),
        }));
        this.$emit('success');
        this.closeModal();
      } catch (error) {
        this.error = 'Error signing in with Google';
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped src="./AuthModal.css"></style>
