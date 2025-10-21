<template>
  <aside :class="['sidebar', { open: sidebarOpen }]">
    <div class="sidebar-header">
      <img src="@/assets/logo.png" alt="DevFriend Logo" class="sidebar-logo" />
    </div>

    <nav class="menu">
      <a href="#">Notes</a>
      <a href="#">Email</a>
      <a href="#">Repository</a>
      <a href="#">Messages</a>
      <a href="#">Credentials</a>
    </nav>

    <div class="mode-toggle">
      <img 
        src="@/assets/darkmode.png" 
        alt="Toggle dark mode" 
        class="darkmode-icon"
        @click="$emit('update:isDarkMode', !isDarkMode)"
      />
    </div>
  </aside>
</template>

<script>
export default {
  name: "AppSidebar",
  props: {
    sidebarOpen: { type: Boolean, required: true },
    isDarkMode: { type: Boolean, required: true },
  },
};
</script>

<style scoped src="./AppSidebar.css"></style>

