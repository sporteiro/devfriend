// Adaptador para comunicación con el backend (puerto en arquitectura hexagonal)
// Detecta automáticamente si estamos en local o en producción
const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_URL = isLocalhost 
  ? 'http://localhost:8888' 
  : 'https://devfriend-back.onrender.com';

export const noteService = {
  async getAllNotes() {
    const response = await fetch(`${API_URL}/notes`);
    if (!response.ok) {
      throw new Error('Error getting notes');
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
      throw new Error('Error creating note');
    }
    return await response.json();
  },
};

