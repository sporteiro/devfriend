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

<style scoped>
.note-list {
  margin-top: 20px;
}

h2 {
  margin-bottom: 20px;
  color: #333;
}

.dark h2 {
  color: #eee;
}

.loading,
.empty {
  text-align: center;
  padding: 40px;
  color: #666;
  font-style: italic;
}

.dark .loading,
.dark .empty {
  color: #999;
}

.error {
  color: #ff4444;
  padding: 20px;
  background-color: #fee;
  border-radius: 4px;
  text-align: center;
}

.dark .error {
  background-color: #4a1f1f;
}

.notes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.note-card {
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.dark .note-card {
  background-color: #2a2a2a;
  border-color: #444;
}

.note-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.note-content {
  margin-bottom: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  color: #333;
  line-height: 1.5;
}

.dark .note-content {
  color: #eee;
}

.note-footer {
  border-top: 1px solid #eee;
  padding-top: 8px;
  text-align: right;
}

.dark .note-footer {
  border-top-color: #444;
}

.note-footer small {
  color: #999;
  font-size: 12px;
}

.dark .note-footer small {
  color: #666;
}
</style>

