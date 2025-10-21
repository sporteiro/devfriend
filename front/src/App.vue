<template>
  <div :class="['app-container', { dark: isDarkMode }]">
    <!-- Botón móvil para abrir/cerrar sidebar -->
    <button class="menu-toggle" @click="sidebarOpen = !sidebarOpen">☰</button>

    <AppSidebar
      :sidebarOpen="sidebarOpen"
      :isDarkMode="isDarkMode"
      @update:isDarkMode="toggleDarkMode"
    />

    <!-- Contenido principal -->
    <main class="content">
      <h1>DevFriend - Gestor de Notas</h1>
      
      <NoteForm @submit="createNote" />
      
      <NoteList 
        :notes="notes" 
        :loading="loading" 
        :error="error" 
      />
    </main>
  </div>
</template>

<script>
import AppSidebar from "./components/AppSidebar.vue";
import NoteForm from "./components/NoteForm.vue";
import NoteList from "./components/NoteList.vue";
import { noteService } from "./services/noteService.js";
import "./App.css";

export default {
  name: "App",
  components: { 
    AppSidebar,
    NoteForm,
    NoteList,
  },
  data() {
    return {
      notes: [],
      loading: false,
      error: null,
      isDarkMode: false,
      sidebarOpen: false,
    };
  },
  mounted() {
    const saved = localStorage.getItem("darkMode");
    this.isDarkMode = saved === "true";
    this.loadNotes();
  },
  methods: {
    toggleDarkMode(value) {
      this.isDarkMode = value;
      localStorage.setItem("darkMode", value);
    },
    async loadNotes() {
      this.loading = true;
      this.error = null;
      try {
        this.notes = await noteService.getAllNotes();
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },
    async createNote(content) {
      this.error = null;
      try {
        await noteService.createNote(content);
        await this.loadNotes();
      } catch (error) {
        this.error = error.message;
      }
    },
  },
};
</script>

