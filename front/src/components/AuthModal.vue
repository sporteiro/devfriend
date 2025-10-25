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

<style scoped>
.auth-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.auth-modal {
  background-color: #fff;
  border-radius: 8px;
  width: 90%;
  max-width: 400px;
  max-height: 90vh;
  overflow-y: unset;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.dark .auth-modal {
  background-color: #2a2a2a;
  color: #eee;
}

.auth-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.dark .auth-header {
  border-bottom-color: #444;
}

.auth-header h2 {
  margin: 0;
  font-size: 20px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dark .close-btn {
  color: #999;
}

.auth-tabs {
  display: flex;
  border-bottom: 1px solid #eee;
}

.dark .auth-tabs {
  border-bottom-color: #444;
}

.auth-tabs button {
  flex: 1;
  padding: 15px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  color: #666;
  border-bottom: 2px solid transparent;
}

.dark .auth-tabs button {
  color: #999;
}

.auth-tabs button.active {
  color: #095633;
  border-bottom-color: #095633;
}

.auth-form {
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #333;
}

.dark .form-group label {
  color: #eee;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background-color: #fff;
  color: #333;
}

.dark .form-group input {
  background-color: #1e1e1e;
  color: #eee;
  border-color: #444;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background-color: #095633;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  margin-bottom: 15px;
  transition: background-color 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background-color: #359268;
}

.submit-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.divider {
  text-align: center;
  margin: 15px 0;
  position: relative;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background-color: #eee;
}

.dark .divider::before {
  background-color: #444;
}

.divider span {
  background-color: #fff;
  padding: 0 15px;
  color: #666;
  font-size: 14px;
}

.dark .divider span {
  background-color: #2a2a2a;
  color: #999;
}

.google-btn {
  width: 100%;
  padding: 12px;
  background-color: #fff;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: background-color 0.2s;
}

.dark .google-btn {
  background-color: #1e1e1e;
  color: #eee;
  border-color: #444;
}

.google-btn:hover {
  background-color: #f8f9fa;
}

.dark .google-btn:hover {
  background-color: #333;
}

.google-icon {
  font-size: 16px;
}

.error {
  color: #ff4444;
  font-size: 14px;
  margin-top: 10px;
  text-align: center;
}
</style>
