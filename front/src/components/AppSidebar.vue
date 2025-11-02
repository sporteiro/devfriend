<template>
  <aside :class="['sidebar', { open: sidebarOpen }]">
    <div class="sidebar-header">
      <img src="@/assets/logo.png" alt="DevFriend Logo" class="sidebar-logo" />
      <h2 class="logo_name">DevFriend</h2>
    </div>

    <nav class="menu">
      <a 
        href="#" 
        :class="{ active: currentSection === 'notes' }"
        @click="navigateTo('notes')"
      >
        Notes
      </a>
      <a 
        href="#" 
        :class="{ active: currentSection === 'emailmodal' }"
        @click="navigateTo('emailmodal')"
        class="nav-item"
      >
        Email
        <span class="notification-badge">3</span>
      </a>
      <a 
        href="#" 
        :class="{ active: currentSection === 'repository' }"
        @click="navigateTo('repository')"
      >
        Repository
      </a>
      <a 
        href="#" 
        :class="{ active: currentSection === 'messages' }"
        @click="navigateTo('messages')"
        class="nav-item"
      >
        Messages
        <span class="notification-badge">12</span>
      </a>
      <a 
        href="#" 
        :class="{ active: currentSection === 'credentials' }"
        @click="navigateTo('credentials')"
      >
        Credentials
      </a>
    </nav>

    <div class="user-section" v-if="user">
      <div class="user-info">
        <div class="user-avatar"></div>
        <div class="user-details">
          <div class="user-name">{{ user.name }}</div>
          <div class="user-email">{{ user.email }}</div>
        </div>
      </div>
      <button @click="$emit('logout')" class="logout-btn">
        Sign Out
      </button>
    </div>

    <div class="auth-section" v-else>
      <button @click="$emit('show-login')" class="login-btn">
        Sign In
      </button>
    </div>

  </aside>
</template>

<script>
export default {
  name: "AppSidebar",
  props: {
    sidebarOpen: { type: Boolean, required: true },
    isDarkMode: { type: Boolean, required: true },
    currentSection: { type: String, default: 'notes' },
    user: { type: Object, default: null },
  },
  methods: {
    navigateTo(section) {
      this.$emit('navigate', section);
    },
  },
};
</script>

<style scoped src="./AppSidebar.css"></style>

