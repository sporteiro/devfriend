<template>
  <div class="note-form">
    <textarea
      v-model="content"
      placeholder="Escribe tu nota aquí..."
      rows="6"
    ></textarea>
    <button @click="handleSubmit" :disabled="!content.trim()">
      Guardar Nota
    </button>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script>
export default {
  name: 'NoteForm',
  data() {
    return {
      content: '',
      error: null,
    };
  },
  methods: {
    handleSubmit() {
      if (!this.content.trim()) {
        this.error = 'El contenido no puede estar vacío';
        return;
      }
      this.$emit('submit', this.content);
      this.content = '';
      this.error = null;
    },
  },
};
</script>

<style scoped>
.note-form {
  margin-bottom: 30px;
  padding: 20px;
  background-color: #f5f5f5;
  border-radius: 8px;
}

.dark .note-form {
  background-color: #1e1e1e;
}

textarea {
  width: 100%;
  padding: 12px;
  font-size: 14px;
  border: 1px solid #ccc;
  border-radius: 4px;
  resize: vertical;
  font-family: inherit;
}

.dark textarea {
  background-color: #2a2a2a;
  color: #eee;
  border-color: #444;
}

button {
  margin-top: 10px;
  padding: 10px 20px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
}

button:hover:not(:disabled) {
  background-color: #359268;
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.error {
  color: #ff4444;
  margin-top: 10px;
  font-size: 14px;
}
</style>

