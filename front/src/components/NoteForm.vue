<template>
  <div class="note-form">
    <textarea
      v-model="content"
      placeholder="Write here"
      rows="6"
    ></textarea>
    <button @click="handleSubmit" :disabled="!content.trim()">
      Save
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

<style scoped src="./NoteForm.css"></style>

