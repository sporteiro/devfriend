<template>
  <div class="note-form">
    <h3 v-if="editingNote">Editing note</h3>
    <h3 v-else>New</h3>
    <label for="note-content" class="sr-only">Note content</label>
    <textarea
      id="note-content"
      v-model="content"
      placeholder="Write your note here... (supports Markdown)"
      rows="6"
      aria-describedby="note-help"
    ></textarea>
    <div id="note-help" class="markdown-help">
      💡 <strong>Markdown Support:</strong> Use # for titles, **bold**, *italic*, `code`, [links](url), lists with -, and more.
    </div>
    <div class="form-actions">
      <button 
        @click="handleSubmit" 
        :disabled="!content.trim()"
        :aria-label="editingNote ? 'Update note' : 'Save new note'"
      >
        {{ editingNote ? 'Update' : 'Save' }}
      </button>
      <button 
        v-if="editingNote" 
        @click="cancelEdit" 
        class="cancel-btn"
        aria-label="Cancel note editing"
      >
        Cancel
      </button>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script>
export default {
  name: 'NoteForm',
  props: {
    editingNote: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      content: '',
      error: null,
    };
  },
  watch: {
    editingNote: {
      handler(newNote) {
        if (newNote) {
          this.content = newNote.content;
        } else {
          this.content = '';
        }
      },
      immediate: true,
    },
  },
  methods: {
    handleSubmit() {
      if (!this.content.trim()) {
        this.error = 'El contenido no puede estar vacío';
        return;
      }
      if (this.editingNote) {
        this.$emit('update-note', { ...this.editingNote, content: this.content });
      } else {
        this.$emit('submit', this.content);
      }
      this.content = '';
      this.error = null;
    },
    cancelEdit() {
      this.$emit('cancel-edit');
      this.content = '';
      this.error = null;
    },
  },
};
</script>

<style scoped src="./NoteForm.css"></style>

