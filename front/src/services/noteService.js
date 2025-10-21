// Adaptador para comunicación con el backend (puerto en arquitectura hexagonal)
const API_URL = 'http://localhost:8888';

export const noteService = {
  async getAllNotes() {
    const response = await fetch(`${API_URL}/notes`);
    if (!response.ok) {
      throw new Error('Error al obtener las notas');
    }
    return await response.json();
  },

  async createNote(content) {
    const response = await fetch(`${API_URL}/notes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: '',
        content: content,
      }),
    });
    if (!response.ok) {
      throw new Error('Error al crear la nota');
    }
    return await response.json();
  },
};

