<template>
  <div class="note-list">
    <h2>Mis Notas</h2>
    <div v-if="loading" class="loading">Cargando notas...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="notes.length === 0" class="empty">
      No hay notas aún. ¡Crea tu primera nota!
    </div>
    <div v-else class="notes-grid">
      <div v-for="note in notes" :key="note.id" class="note-card">
        <div class="note-content">{{ note.content }}</div>
        <div class="note-footer">
          <small v-if="note.created_at">
            {{ formatDate(note.created_at) }}
          </small>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NoteList',
  props: {
    notes: {
      type: Array,
      required: true,
    },
    loading: {
      type: Boolean,
      default: false,
    },
    error: {
      type: String,
      default: null,
    },
  },
  methods: {
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    },
  },
};
</script>

<style scoped src="./NoteList.css"></style>

