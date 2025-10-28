import axios from 'axios';
import { authService } from './authService';

const API_URL = process.env.VUE_APP_API_URL || 'http://localhost:8888';
const STORAGE_KEY = 'devfriend_notes';

function getAuthHeaders() {
  const token = authService.getToken();
  return token
    ? {
        Authorization: `Bearer ${token}`,
      }
    : {};
}

export const noteService = {
  async getAllNotes() {
    const token = authService.getToken();

    if (!token) {
      return this._getLocalNotes();
    }

    try {
      const response = await axios.get(`${API_URL}/notes`, {
        headers: getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching notes from API:', error);
      return this._getLocalNotes();
    }
  },

  _getLocalNotes() {
    try {
      const notes = localStorage.getItem(STORAGE_KEY);
      const parsedNotes = notes ? JSON.parse(notes) : [];

      if (parsedNotes.length === 0) {
        const exampleNote = {
          id: Date.now().toString(),
          title: 'Welcome to DevFriend',
          content: `# DevFriend - Example Note

This is an **example note** that demonstrates Markdown support in DevFriend.

## Implemented features:

- ✅ **Titles** with different levels
- ✅ **Bold text** and *italic*
- ✅ **Lists** numbered and bulleted
- ✅ \`Inline code\` and code blocks
- ✅ [Links](https://github.com) functional

## Code block:

\`\`\`javascript
function greet() {
  console.log("Hello from DevFriend!");
}
\`\`\`

## Task list:

- [x] Implement Markdown support
- [x] Create example note
- [ ] Add more features
- [ ] Improve interface

> **Note**: This is an example quote showing how quotes look in Markdown.

---

*Automatically created by DevFriend*`,
          created_at: new Date().toISOString(),
        };
        parsedNotes.push(exampleNote);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(parsedNotes));
      }

      return parsedNotes;
    } catch (error) {
      console.error('Error loading notes from localStorage:', error);
      return [];
    }
  },

  async createNote(title, content) {
    const token = authService.getToken();

    if (!token) {
      return this._createLocalNote(title, content);
    }

    try {
      const response = await axios.post(
        `${API_URL}/notes`,
        {
          title,
          content,
        },
        {
          headers: getAuthHeaders(),
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error creating note:', error);
      throw new Error(error.response?.data?.detail || 'Error creating note');
    }
  },

  _createLocalNote(title, content) {
    const notes = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    const newNote = {
      id: Date.now().toString(),
      title,
      content,
      created_at: new Date().toISOString(),
    };
    notes.unshift(newNote);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(notes));
    return newNote;
  },

  async updateNote(noteId, title, content) {
    const token = authService.getToken();

    if (!token) {
      return this._updateLocalNote(noteId, title, content);
    }

    try {
      const response = await axios.put(
        `${API_URL}/notes/${noteId}`,
        {
          title,
          content,
        },
        {
          headers: getAuthHeaders(),
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error updating note:', error);
      throw new Error(error.response?.data?.detail || 'Error updating note');
    }
  },

  _updateLocalNote(noteId, title, content) {
    const notes = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    const index = notes.findIndex((n) => n.id === noteId);
    if (index !== -1) {
      notes[index].title = title;
      notes[index].content = content;
      notes[index].updated_at = new Date().toISOString();
      localStorage.setItem(STORAGE_KEY, JSON.stringify(notes));
      return notes[index];
    }
    return null;
  },

  async deleteNote(noteId) {
    const token = authService.getToken();

    if (!token) {
      return this._deleteLocalNote(noteId);
    }

    try {
      await axios.delete(`${API_URL}/notes/${noteId}`, {
        headers: getAuthHeaders(),
      });
      return true;
    } catch (error) {
      console.error('Error deleting note:', error);
      throw new Error(error.response?.data?.detail || 'Error deleting note');
    }
  },

  _deleteLocalNote(noteId) {
    try {
      const notes = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      const filtered = notes.filter((n) => n.id !== noteId);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
      return true;
    } catch (error) {
      throw new Error('Error deleting note');
    }
  },

  async exportNotes() {
    try {
      const notes = await this.getAllNotes();
      const exportData = {
        notes: notes,
        exported_at: new Date().toISOString(),
        version: '1.0',
      };
      return exportData;
    } catch (error) {
      throw new Error('Error exporting notes');
    }
  },
};
