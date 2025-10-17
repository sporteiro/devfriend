<template>
  <aside :class="['sidebar', { open: sidebarOpen }]">
    <h2 class="title">DevFriend</h2>

    <nav class="menu">
      <a href="#">Inicio</a>
      <a href="#">Perfil</a>
      <a href="#">Configuración</a>
    </nav>

    <div class="mode-toggle">
      <label>
        <input
          type="checkbox"
          :checked="isDarkMode"
          @change="$emit('update:isDarkMode', $event.target.checked)"
        />
        Modo oscuro
      </label>
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

<style scoped>
.sidebar {
  width: 220px;
  background-color: #adadad;
  color: #333;
  padding: 20px;
  flex-shrink: 0;
  transition: transform 0.3s ease-in-out;
}

.title {
  font-size: 1.5em;
  margin-bottom: 20px;
}

.menu a {
  display: block;
  color: #333;  /* negro */
  text-decoration: none;
  margin: 10px 0;
  font-weight: bold;
}

.menu a:hover {
  text-decoration: underline;
}

.mode-toggle {
  margin-top: 20px;
  font-size: 0.9em;
}

/* Responsividad */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100%;
    transform: translateX(-100%);
    z-index: 999;
  }

  .sidebar.open {
    transform: translateX(0);
  }
}
</style>

