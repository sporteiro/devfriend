<template>
  <div :class="['app-container', { dark: isDarkMode }]">
    <!-- Botón móvil para abrir/cerrar sidebar -->
    <button class="menu-toggle" @click="sidebarOpen = !sidebarOpen">☰</button>

    <AppSidebar
      :sidebarOpen="sidebarOpen"
      :isDarkMode="isDarkMode"
      @update:isDarkMode="isDarkMode = $event"
    />

    <!-- Contenido principal -->
    <main class="content">
      <h1>Frontend con Vue y FastAPI</h1>
      <button @click="fetchData">Obtener datos del Backend</button>

      <div v-if="response">
        <p><strong>Mensaje desde FastAPI:</strong> {{ response.message }}</p>
      </div>
      <div v-if="error" style="color: red;">
        <p><strong>Error:</strong> {{ error }}</p>
      </div>
    </main>
  </div>
</template>

<script>
import AppSidebar from "./components/AppSidebar.vue";
import "./App.css";

export default {
  name: "App",
  components: { AppSidebar },
  data() {
    return {
      response: null,
      error: null,
      isDarkMode: false,
      sidebarOpen: false,
    };
  },
  mounted() {
    const saved = localStorage.getItem("darkMode");
    this.isDarkMode = saved === "true";
  },
  methods: {
    async fetchData() {
      this.error = null;
      try {
        const res = await fetch("http://localhost:8888/");
        if (!res.ok) throw new Error("Error al obtener datos");
        this.response = await res.json();
      } catch (error) {
        this.error = error.message;
      }
    },
  },
};
</script>

