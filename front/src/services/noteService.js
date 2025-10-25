// Servicio de notas con almacenamiento local (simulando versión Cloud)
const STORAGE_KEY = 'devfriend_notes';

export const noteService = {
  async getAllNotes() {
    try {
      const notes = localStorage.getItem(STORAGE_KEY);
      const parsedNotes = notes ? JSON.parse(notes) : [];
      
      // Si no hay notas, crear una nota de ejemplo con Markdown
      if (parsedNotes.length === 0) {
        const exampleNote = {
          id: Date.now().toString(),
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
          updated_at: new Date().toISOString(),
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

  async createNote(content) {
    try {
      const notes = await this.getAllNotes();
      const newNote = {
        id: Date.now().toString(),
        content: content,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      notes.unshift(newNote); // Agregar al inicio
      localStorage.setItem(STORAGE_KEY, JSON.stringify(notes));
      return newNote;
    } catch (error) {
      throw new Error('Error creating note');
    }
  },

  async updateNote(noteId, content) {
    try {
      const notes = await this.getAllNotes();
      const index = notes.findIndex(n => n.id === noteId);
      if (index !== -1) {
        notes[index] = {
          ...notes[index],
          content: content,
          updated_at: new Date().toISOString(),
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(notes));
        return notes[index];
      }
      throw new Error('Note not found');
    } catch (error) {
      throw new Error('Error updating note');
    }
  },

  async deleteNote(noteId) {
    try {
      const notes = await this.getAllNotes();
      const filteredNotes = notes.filter(n => n.id !== noteId);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(filteredNotes));
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

