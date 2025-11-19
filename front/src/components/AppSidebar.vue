<template>
  <aside :class="['sidebar', { open: sidebarOpen }]">
    <!-- X solo si sidebarOpen y en móvil -->
    <button
      v-if="sidebarOpen"
      class="sidebar-close"
      @click="$emit('close-sidebar')"
      aria-label="Close menu"
    >
      ×
    </button>
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
      <span v-if="emailUnreadCount > 0" class="notification-badge">{{ emailUnreadCount }}</span>
    </a>
    <a
      href="#"
      :class="{ active: currentSection === 'repositorymodal' }"
      @click="navigateTo('repositorymodal')"
      class="nav-item"
    >
      Repository
      <span v-if="githubNotificationCount > 0" class="notification-badge">{{ githubNotificationCount }}</span>
    </a>
    <a
      href="#"
      :class="{ active: currentSection === 'messagesmodal' }"
      @click="navigateTo('messagesmodal')"
      class="nav-item"
    >
      Messages
      <span v-if="slackUnreadCount > 0" class="notification-badge">{{ slackUnreadCount }}</span>
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
    emailUnreadCount: { type: Number, default: 0 },
    slackUnreadCount: { type: Number, default: 0 },
    githubNotificationCount: { type: Number, default: 0 },
  },
  methods: {
    navigateTo(section) {
      this.$emit('navigate', section);
    },
  },
};
</script>

<style scoped src="./AppSidebar.css"></style>
