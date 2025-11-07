<template>
  <div class="note-list">
    <h2>Notes</h2>
    <div v-if="loading" class="loading" role="status" aria-live="polite">Loading notes...</div>
    <div v-else-if="error" class="error" role="alert" aria-live="assertive">{{ error }}</div>
    <div v-else-if="notes.length === 0" class="empty" role="status">
      No notes yet
    </div>
    <div v-else class="notes-grid" role="list" aria-label="Notes list">
      <div v-for="note in notes" :key="note.id" class="note-card" role="listitem">
        <div class="note-content" v-html="renderMarkdown(note.content)"></div>
        <div class="note-footer">
          <small v-if="note.created_at">
            {{ formatDate(note.created_at) }}
          </small>
          <div class="note-actions">
            <button
              @click="editNote(note)"
              class="edit-btn"
              :aria-label="`Edit note: ${note.content.substring(0, 50)}...`"
            >
              Edit
            </button>
            <button
              @click="deleteNote(note)"
              class="delete-btn"
              :aria-label="`Delete note: ${note.content.substring(0, 50)}...`"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { marked } from 'marked';

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
    renderMarkdown(content) {
      if (!content) return '';
      return marked(content);
    },
    editNote(note) {
      this.$emit('edit-note', note);
    },
    deleteNote(note) {
      if (confirm('Are you sure you want to delete this note?')) {
        this.$emit('delete-note', note);
      }
    },
  },
};
</script>

<style scoped src="./NoteList.css"></style>
